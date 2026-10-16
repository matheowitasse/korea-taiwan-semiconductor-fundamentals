"""Q7: import KRX [12001] all-issues price snapshots (quarter-end market caps) from ~/Downloads.

KRX snapshot files contain no date column, so each file's date is identified by matching the closing prices of the 10
stocks in data/raw/naver_flows/ (Naver closes are unadjusted, like KRX). A file is accepted only if exactly one trading
day matches all available stocks AND that day is one of the expected quarter-ends.
Moves originals to data/raw/krx_snapshots/snapshot_<YYYYMMDD>.csv and writes data/interim/krx_marketcap_quarterly.parquet.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"
NAVER = ROOT / "data" / "raw" / "naver_flows"
RAW = ROOT / "data" / "raw" / "krx_snapshots"
OUT = ROOT / "data" / "interim" / "krx_marketcap_quarterly.parquet"
HEADER = "Issue code,Issue name,Market type,Company category,Close"
EXPECTED = ["2022-06-30", "2022-09-30", "2022-12-29", "2023-03-31", "2023-06-30", "2023-09-27", "2023-12-28", "2024-03-29",
            "2024-06-28", "2024-09-30", "2024-12-30", "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-30", "2026-03-31",
            "2026-06-30"]


def naver_closes() -> pd.DataFrame:
    return pd.concat({p.stem: pd.read_parquet(p)["close"] for p in NAVER.glob("[0-9]*.parquet")}, axis=1, sort=True)


def identify(snap: pd.DataFrame, closes: pd.DataFrame) -> list[pd.Timestamp]:
    snap_close = snap.set_index("Issue code")["Close"]
    codes = [c for c in closes.columns if c in snap_close.index]
    match = pd.Series(True, index=closes.index)
    for c in codes:
        match &= closes[c] == float(snap_close[c])
    return list(closes.index[match])


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    closes = naver_closes()
    frames, found = [], {}
    for f in sorted(DOWNLOADS.glob("data_*.csv")):
        if not f.read_text(encoding="utf-8", errors="replace").startswith(HEADER):
            continue
        snap = pd.read_csv(f, dtype={"Issue code": str}, encoding_errors="replace")
        dates = identify(snap, closes)
        ok = len(dates) == 1 and dates[0].strftime("%Y-%m-%d") in EXPECTED
        label = dates[0].strftime("%Y-%m-%d") if len(dates) == 1 else f"{len(dates)} matches"
        print(f"{f.name}: {len(snap)} rows -> {label} {'OK' if ok else 'NOT ACCEPTED'}")
        if not ok:
            continue
        d = dates[0]
        if d in found:
            print(f"  duplicate of {found[d]} -> removed")
            f.unlink()
            continue
        target = RAW / f"snapshot_{d:%Y%m%d}.csv"
        f.replace(target)
        found[d] = f.name
        frames.append(snap.assign(date=d))

    for p in RAW.glob("snapshot_*.csv"):  # include snapshots imported in earlier runs
        d = pd.Timestamp(p.stem.split("_")[1])
        if d not in found:
            frames.append(pd.read_csv(p, dtype={"Issue code": str}, encoding_errors="replace").assign(date=d))
            found[d] = p.name
    allsnap = pd.concat(frames, ignore_index=True).rename(columns={
        "Issue code": "stock_code", "Issue name": "name", "Market type": "market", "Market cap.": "market_cap",
        "No.of listed shares": "shares"})
    allsnap[["date", "stock_code", "name", "market", "Close", "market_cap", "shares"]].to_parquet(OUT)
    missing = [e for e in EXPECTED if pd.Timestamp(e) not in found]
    print(f"\nquarter-ends imported: {len(found)}/17; missing: {missing or 'none'} -> {OUT}")


if __name__ == "__main__":
    main()
