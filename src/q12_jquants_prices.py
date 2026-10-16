"""Pull official J-Quants daily prices for the Japanese universe (verification data for the Yahoo prices).

Run while a paid subscription is active; the data is then kept locally regardless of the plan.
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q9_jquants_download import SECTORS, get

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "jquants_prices"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(ROOT / "data" / "raw" / "jquants" / "master.csv", dtype={"Code": str})
    codes = master.loc[master["S33Nm"].isin(SECTORS), "Code"].unique()
    done = 0
    for i, code in enumerate(codes, 1):
        path = OUT / f"{code}.parquet"
        if path.exists():
            continue
        rows = get("/equities/bars/daily", {"code": code})
        if rows:
            df = pd.DataFrame(rows)
            df["Date"] = pd.to_datetime(df["Date"])
            keep = [c for c in ["Date", "AdjO", "AdjH", "AdjL", "AdjC", "Vo", "AdjFactor"] if c in df.columns]
            df[keep].set_index("Date").sort_index().to_parquet(path)
            done += 1
        if i % 40 == 0:
            print(f"  {i}/{len(codes)} ({done} saved)")
        time.sleep(0.15)
    files = list(OUT.glob("*.parquet"))
    if files:
        sample = pd.read_parquet(files[0])
        print(f"price files: {len(files)} | sample span {sample.index.min().date()} → {sample.index.max().date()}")


if __name__ == "__main__":
    main()
