"""Q27: extend Taiwanese Yahoo price history back to 2013 for the pre-AI test (prices only, no returns computed)."""

import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q9_taiwan_test import PRICES, universe

START = "2013-01-01"


def main() -> None:
    u = universe()
    PRICES.mkdir(parents=True, exist_ok=True)
    end = str(date.today() + timedelta(days=1))
    todo = []
    for t in u["ticker"]:
        p = PRICES / f"{t.split('.')[0]}.parquet"
        if not p.exists() or pd.read_parquet(p).index.min() > pd.Timestamp("2013-06-30"):
            todo.append(t)
    print(f"{len(todo)} of {len(u)} tickers need a longer history")
    for i in range(0, len(todo), 40):
        batch = todo[i:i + 40]
        data = yf.download(batch, start=START, end=end, auto_adjust=True, group_by="ticker",
                           threads=True, progress=False)
        for t in batch:
            try:
                df = data[t].dropna(how="all") if len(batch) > 1 else data.dropna(how="all")
            except KeyError:
                continue
            if len(df):
                df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
                df[["Close"]].to_parquet(PRICES / f"{t.split('.')[0]}.parquet")
        print(f"  {min(i + 40, len(todo))}/{len(todo)}")
        time.sleep(2)
    starts = pd.Series([pd.read_parquet(p).index.min() for p in PRICES.glob("*.parquet")])
    print(f"price files {len(starts)} | starting 2013: {(starts <= '2013-12-31').sum()} | "
          f"starting after 2016: {(starts > '2016-01-31').sum()}")


if __name__ == "__main__":
    main()
