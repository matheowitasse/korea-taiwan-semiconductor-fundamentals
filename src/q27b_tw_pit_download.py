"""Q27b data: a point-in-time Taiwanese universe, including companies that later delisted.

Two sources, both archived by month:
  (a) MOPS monthly revenue files, re-parsed with their industry section headers (產業別：半導體業 / 電子零組件業),
      so the chip universe is the one that existed in that month;
  (b) month-end all-issues closing prices from TWSE (MI_INDEX) and TPEx (afterTrading/otc), which include names that
      have since been delisted. These prices are NOT adjusted for dividends — that is the trade-off of this version.

Outputs: data/raw/taiwan_pit/universe_<YYYY>_<M>_<market>.csv and data/raw/taiwan_pit/prices_<YYYYMM>.csv
No returns are computed here.
"""

import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "taiwan_pit"
UA = {"User-Agent": "Mozilla/5.0 (academic research; korea-chip-loop)"}
START, END = pd.Timestamp("2016-01-01"), pd.Timestamp.today()
SLEEP = 3.0
SEMI, PARTS = "半導體業", "電子零組件業"   # 半導體業 / 電子零組件業
NUM = lambda s: pd.to_numeric(str(s).replace(",", "").strip(), errors="coerce")


def get_with_retry(url: str, params: dict, tries: int = 5):
    """Both exchanges reset connections under sustained scraping; back off and retry."""
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=60)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        if attempt < tries:
            time.sleep(10 * attempt)
    return None


def month_ends() -> list[pd.Timestamp]:
    cal = pd.read_parquet(ROOT / "data" / "raw" / "full_IDX_TWII.parquet").index
    cal = cal[(cal >= START) & (cal <= END)]
    return list(pd.Series(cal, index=cal).groupby([cal.year, cal.month]).max())


def fetch_universe(year: int, month: int, market: str) -> pd.DataFrame | None:
    """Monthly revenue file, keeping the industry section each company sits under."""
    url = f"https://mopsov.twse.com.tw/nas/t21/{market}/t21sc03_{year - 1911}_{month}.html"
    r = get_with_retry(url, {})
    if r is None:
        return None
    html = r.content.decode("big5", errors="replace")
    rows = []
    for block in re.split(r"產業別：", html)[1:]:          # split on 產業別：
        industry = re.match(r"([^<\s]+)", block).group(1)
        if industry not in (SEMI, PARTS):
            continue
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", block, flags=re.S):
            cells = [re.sub(r"<[^>]+>|&nbsp;", " ", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)]
            if len(cells) >= 5 and re.fullmatch(r"\d{4}", cells[0] or ""):
                rows.append({"code": cells[0], "name": cells[1], "industry": industry,
                             "revenue_current": NUM(cells[2]), "revenue_prev_month": NUM(cells[3]),
                             "revenue_year_ago": NUM(cells[4])})
    return pd.DataFrame(rows).assign(year=year, month=month, market=market) if rows else None


def fetch_prices(d: pd.Timestamp) -> pd.DataFrame | None:
    """Month-end closing price for every issue on both markets (unadjusted)."""
    out = []
    r = get_with_retry("https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX",
                       {"date": f"{d:%Y%m%d}", "type": "ALLBUT0999", "response": "json"})
    if r is not None and r.text.strip().startswith("{"):
        tables = r.json().get("tables", [])
        if tables:
            t = max(tables, key=lambda x: len(x.get("data", [])))
            for row in t.get("data", []):
                if re.fullmatch(r"\d{4}", str(row[0]).strip()):
                    out.append({"code": row[0].strip(), "close": NUM(row[8]), "market": "TWSE"})
    time.sleep(SLEEP)
    r = get_with_retry("https://www.tpex.org.tw/www/zh-tw/afterTrading/otc",
                       {"date": f"{d:%Y/%m/%d}", "type": "EW", "response": "json"})
    if r is not None and r.text.strip().startswith("{"):
        tables = r.json().get("tables", [])
        if tables:
            for row in tables[0].get("data", []):
                if re.fullmatch(r"\d{4}", str(row[0]).strip()):
                    out.append({"code": row[0].strip(), "close": NUM(row[2]), "market": "TPEx"})
    return pd.DataFrame(out).assign(date=d.date()) if out else None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    periods = pd.period_range(START.to_period("M"), (END - pd.Timedelta(days=40)).to_period("M"), freq="M")
    for p in periods:
        for market in ["sii", "otc"]:
            path = OUT / f"universe_{p.year}_{p.month}_{market}.csv"
            if path.exists():
                continue
            df = fetch_universe(p.year, p.month, market)
            if df is None:
                print(f"  universe {p} {market}: no data")
            else:
                df.to_csv(path, index=False, encoding="utf-8-sig")
                print(f"  universe {p} {market}: {len(df)} chip companies")
            time.sleep(SLEEP)

    for d in month_ends():
        path = OUT / f"prices_{d:%Y%m}.csv"
        if path.exists():
            continue
        df = fetch_prices(d)
        if df is None:
            print(f"  prices {d.date()}: no data")
        else:
            df.to_csv(path, index=False, encoding="utf-8-sig")
            print(f"  prices {d.date()}: {len(df)} issues ({df['market'].value_counts().to_dict()})")
        time.sleep(SLEEP)

    print(f"universe files: {len(list(OUT.glob('universe_*.csv')))} | price files: {len(list(OUT.glob('prices_*.csv')))}")


if __name__ == "__main__":
    main()
