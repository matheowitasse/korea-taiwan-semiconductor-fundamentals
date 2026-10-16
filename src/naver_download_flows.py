"""Download daily investor flows (foreign / institution / individual net buying) from Naver's public stock API.

Why Naver: pykrx's KRX login does not accept English-site (foreign member) accounts, so KRX data is downloaded by hand
into data/raw/krx_manual/ and used to cross-check this source. No login or credentials needed here.

Two endpoints (found 2026-09-16, undocumented, may change):
  - stock: m.stock.naver.com/api/stock/<code>/trend?pageSize=60&bizdate=YYYYMMDD
      -> up to 60 trading days strictly before bizdate; net buying in SHARES (foreign, institution, individual),
         foreign holding ratio, close, volume.
  - index: m.stock.naver.com/api/index/<KOSPI|KOSDAQ>/trend?bizdate=YYYYMMDD
      -> one day; net buying VALUE in 100 million KRW (억원) for individual, foreign, institution.

Usage (from the project folder):
  python src/naver_download_flows.py stocks            # Samsung, SK Hynix, 8 suppliers
  python src/naver_download_flows.py index             # KOSPI + KOSDAQ market-wide (one request per day, slow)
  python src/naver_download_flows.py all --start 2016-01-01

Output: data/raw/naver_flows/<code>.parquet and index_<KOSPI|KOSDAQ>.parquet (resumable: existing dates are skipped).
"""

import argparse
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "naver_flows"
CALENDAR = ROOT / "data" / "raw" / "full_IDX_KS11.parquet"  # KOSPI trading days (Yahoo)

STOCKS = {
    "005930": "Samsung", "000660": "SK Hynix",
    "042700": "Hanmi Semi", "000990": "DB HiTek", "058470": "Leeno", "095340": "ISC",
    "240810": "Wonik IPS", "036930": "Jusung Eng", "084370": "Eugene Tech", "403870": "HPSP",
}
INDICES = ["KOSPI", "KOSDAQ"]

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131 Safari/537.36"}
PAUSE = 0.4  # seconds between requests


def get_json(url, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=20)
            if r.status_code == 200 and r.text.strip():
                time.sleep(PAUSE)
                return r.json()
        except (requests.RequestException, ValueError):
            pass
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"failed after {tries} tries: {url}")


def num(s):
    """'+1,234' / '-5' / '50.17%' -> float."""
    s = "" if s is None else str(s).replace(",", "").replace("%", "").replace("+", "").strip()
    try:
        return float(s)
    except ValueError:  # Naver uses "-" / "" for missing
        return float("nan")


def download_stock(code, start):
    path = OUT / f"{code}.parquet"
    old = pd.read_parquet(path) if path.exists() else None
    rows, bizdate = [], (pd.Timestamp.today().normalize() + pd.Timedelta(days=1)).strftime("%Y%m%d")
    while True:
        page = get_json(f"https://m.stock.naver.com/api/stock/{code}/trend?pageSize=60&bizdate={bizdate}")
        if not page:
            break
        for x in page:
            rows.append({
                "date": pd.Timestamp(x["bizdate"]),
                "foreign_net_shares": num(x["foreignerPureBuyQuant"]),
                "institution_net_shares": num(x["organPureBuyQuant"]),
                "individual_net_shares": num(x["individualPureBuyQuant"]),
                "foreign_hold_pct": num(x["foreignerHoldRatio"]),
                "close": num(x["closePrice"]),
                "volume": num(x["accumulatedTradingVolume"]),
            })
        last = page[-1]["bizdate"]
        if last >= bizdate or pd.Timestamp(last) < start:
            break
        # stop early once we reach dates already saved (older rows never change... re-fetch the last 60 days anyway)
        if old is not None and pd.Timestamp(last) < old.index.max() - pd.Timedelta(days=90):
            break
        bizdate = last
    new = pd.DataFrame(rows).drop_duplicates("date").set_index("date").sort_index()
    new = new[new["close"].notna()]  # the current day comes back provisional (flows but no close) -> skip it
    new = new[new.index >= start]  # --start limits what is fetched now; history already saved is never cut
    df = new if old is None else pd.concat([old[~old.index.isin(new.index)], new]).sort_index()
    df.to_parquet(path)
    print(f"{code} {STOCKS.get(code, '')}: {len(df)} days, {df.index.min().date()} -> {df.index.max().date()}")


def download_index(name, start):
    path = OUT / f"index_{name}.parquet"
    old = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    days = pd.read_parquet(CALENDAR).index
    days = [d for d in days if d >= start and d not in old.index]
    rows = []
    for i, d in enumerate(days, 1):
        x = get_json(f"https://m.stock.naver.com/api/index/{name}/trend?bizdate={d:%Y%m%d}")
        if x and x.get("bizdate") == f"{d:%Y%m%d}":
            rows.append({"date": d, "individual_net_100m_krw": num(x["personalValue"]),
                         "foreign_net_100m_krw": num(x["foreignValue"]),
                         "institution_net_100m_krw": num(x["institutionalValue"])})
        else:
            print(f"  {name} {d.date()}: no data / date mismatch ({x})")
        if i % 200 == 0 or i == len(days):
            part = pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame()
            pd.concat([old, part]).sort_index().to_parquet(path)
            print(f"  {name}: {i}/{len(days)} days")
    df = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    if len(df):
        print(f"index {name}: {len(df)} days, {df.index.min().date()} -> {df.index.max().date()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["stocks", "index", "all"])
    ap.add_argument("--start", default="2016-01-01")
    ap.add_argument("--only", nargs="*", help="limit to these stock codes / index names")
    ap.add_argument("--codes-file", help="CSV with a stock_code column: download these stocks instead of the default 10")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp(a.start)
    if a.what in ("stocks", "all"):
        if a.codes_file:
            codes = pd.read_csv(a.codes_file, dtype={"stock_code": str})["stock_code"].dropna().unique()
            for code in codes:
                try:
                    download_stock(code, start)
                except Exception as e:  # e.g. delisted stocks Naver no longer serves
                    print(f"{code}: skipped ({type(e).__name__}: {e})")
        else:
            for code in a.only or STOCKS:
                if code in STOCKS:
                    download_stock(code, start)
    if a.what in ("index", "all"):
        for name in a.only or INDICES:
            if name in INDICES:
                download_index(name, start)


if __name__ == "__main__":
    main()
