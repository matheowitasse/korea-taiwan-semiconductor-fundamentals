"""Q8 step 2: extend the Yahoo price history of the chip universe back to 2015.

The Q7 cache starts 2022-06-01, which is not enough for 12-month price momentum at the start of the test period
(2023-01). Re-downloads each listed company from 2015-01-01 into data/raw/q7_yahoo/ (same files, longer history).
Only prices are downloaded; no returns are computed here.
"""

import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "raw" / "q7_yahoo"
START = "2015-01-01"


def main() -> None:
    comp = pd.read_csv(ROOT / "data" / "interim" / "dart_companies.csv", dtype=str)
    codes = pd.read_csv(ROOT / "data" / "interim" / "q7_universe_codes.csv", dtype=str)["stock_code"]
    u = comp[comp["stock_code"].isin(codes) & comp["corp_cls"].isin(["Y", "K"])].copy()
    u["yahoo"] = u["stock_code"] + u["corp_cls"].map({"Y": ".KS", "K": ".KQ"})
    tickers = sorted(u["yahoo"].unique())
    end = str(date.today() + timedelta(days=1))
    extended = 0
    for i in range(0, len(tickers), 40):
        batch = tickers[i:i + 40]
        data = yf.download(batch, start=START, end=end, auto_adjust=True, group_by="ticker", threads=True, progress=False)
        for t in batch:
            code = t.split(".")[0]
            try:
                df = data[t].dropna(how="all")
            except KeyError:
                continue
            if not len(df):
                continue
            df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
            df = df[["Open", "High", "Low", "Close", "Volume"]]
            path = CACHE / f"{code}.parquet"
            if path.exists() and pd.read_parquet(path).index.min() <= df.index.min():
                continue
            df.to_parquet(path)
            extended += 1
        print(f"  {min(i + 40, len(tickers))}/{len(tickers)} ({extended} files extended)")
        time.sleep(2)

    spans = {p.stem: pd.read_parquet(p).index.min() for p in CACHE.glob("*.parquet")}
    s = pd.Series(spans)
    print(f"\nfiles: {len(s)} | starting 2015: {(s <= '2015-01-05').sum()} | starting after 2021-12: {(s > '2021-12-31').sum()}")


if __name__ == "__main__":
    main()
