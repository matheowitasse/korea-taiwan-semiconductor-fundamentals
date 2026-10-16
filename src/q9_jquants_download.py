"""Q9 step 1: Japanese chip-sector data from J-Quants V2 (financials) and Yahoo (prices).

J-Quants V2 authenticates with an API key in the `x-api-key` header; the key is read from the environment variable
JQUANTS_API_KEY (or JQUANTS_TOKEN) and never printed. Free plan covers roughly the last 2 years with a 12-week delay.

Universe: sectors 電気機器 (electric appliances) and 精密機器 (precision instruments) — the Japanese analogue of the
Korean chip-supply-chain list (list B ∪ C).

Outputs (no returns computed here):
  data/raw/jquants/master.csv          listed companies with sector codes
  data/raw/jquants/fins_summary.csv    quarterly statements (disclosure date + time, sales, OP, assets, equity)
  data/raw/q9_jp_prices/<code>.parquet Yahoo daily prices for the universe
"""

import os
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "jquants"
PRICES = ROOT / "data" / "raw" / "q9_jp_prices"
BASE = "https://api.jquants.com/v2"
SECTORS = ["電気機器", "精密機器"]
PRICE_START = "2015-01-01"


def headers() -> dict:
    key = os.environ.get("JQUANTS_API_KEY") or os.environ.get("JQUANTS_TOKEN")
    if not key:
        raise SystemExit("set JQUANTS_API_KEY (or JQUANTS_TOKEN) in the environment")
    return {"x-api-key": key}


def get(path: str, params: dict | None = None) -> list[dict]:
    rows, cursor = [], None
    while True:
        p = dict(params or {})
        if cursor:
            p["pagination_key"] = cursor
        for attempt in range(4):
            r = requests.get(f"{BASE}{path}", headers=headers(), params=p, timeout=60)
            if r.status_code == 200:
                break
            if r.status_code == 400 and "subscription covers" in r.text:
                return rows  # asked for dates outside the plan
            time.sleep(3 * (attempt + 1))
        else:
            raise RuntimeError(f"{path} failed: {r.status_code} {r.text[:200]}")
        j = r.json()
        rows += j.get("data", [])
        cursor = j.get("pagination_key")
        if not cursor:
            return rows


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    master = pd.DataFrame(get("/equities/master"))
    master.to_csv(RAW / "master.csv", index=False, encoding="utf-8-sig")
    uni = master[master["S33Nm"].isin(SECTORS)].copy()
    print(f"universe: {len(uni)} companies in {' + '.join(SECTORS)} (of {len(master)} listed)")

    fins_path = RAW / "fins_summary.csv"
    done = pd.read_csv(fins_path, dtype=str) if fins_path.exists() else pd.DataFrame()
    have = set(done["Code"]) if len(done) else set()
    rows = []
    for i, code in enumerate(uni["Code"], 1):
        if code in have:
            continue
        rows += get("/fins/summary", {"code": code})
        if i % 25 == 0:
            print(f"  financials {i}/{len(uni)}")
            pd.concat([done, pd.DataFrame(rows)]).to_csv(fins_path, index=False, encoding="utf-8-sig")
        time.sleep(0.2)
    fins = pd.concat([done, pd.DataFrame(rows)], ignore_index=True) if rows else done
    fins.to_csv(fins_path, index=False, encoding="utf-8-sig")
    print(f"financial rows: {len(fins)} for {fins['Code'].nunique()} companies "
          f"({fins['DiscDate'].min()} → {fins['DiscDate'].max()})")

    PRICES.mkdir(parents=True, exist_ok=True)
    tickers = [f"{c[:4]}.T" for c in uni["Code"]]
    end = str(date.today() + timedelta(days=1))
    for i in range(0, len(tickers), 40):
        batch = [t for t in tickers[i:i + 40] if not (PRICES / f"{t.split('.')[0]}.parquet").exists()]
        if not batch:
            continue
        data = yf.download(batch, start=PRICE_START, end=end, auto_adjust=True, group_by="ticker",
                           threads=True, progress=False)
        for t in batch:
            try:
                df = data[t].dropna(how="all") if len(batch) > 1 else data.dropna(how="all")
            except KeyError:
                continue
            if len(df):
                df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
                df[["Open", "High", "Low", "Close", "Volume"]].to_parquet(PRICES / f"{t.split('.')[0]}.parquet")
        print(f"  prices {min(i + 40, len(tickers))}/{len(tickers)}")
        time.sleep(2)
    print(f"price files: {len(list(PRICES.glob('*.parquet')))}")


if __name__ == "__main__":
    main()
