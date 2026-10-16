"""Q7: import hand-downloaded KRX daily price files (individual / delisted issue price trend) from ~/Downloads.

KRX files are named data_XXXX_<date>.csv. Each contains Issue code + Issue name, so files are identified by content.
Moves the originals to data/raw/krx_prices_manual/<code>_<first>_<last>.csv (exact duplicates are dropped) and writes one
merged file per stock: data/raw/krx_prices/<code>.parquet (UNADJUSTED prices, as published by KRX).
"""

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"
ORIGINALS = ROOT / "data" / "raw" / "krx_prices_manual"
MERGED = ROOT / "data" / "raw" / "krx_prices"
HEADER = "Date,Issue code,Issue name,Market type,Securities type,Close,Change,%Change,Open,High,Low,Trading volume"


def read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"Issue code": str})
    df["Date"] = pd.to_datetime(df["Date"], format="%Y/%m/%d")
    return df


def main() -> None:
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    MERGED.mkdir(parents=True, exist_ok=True)
    seen = {hashlib.sha256(p.read_bytes()).hexdigest() for p in ORIGINALS.glob("*.csv")}
    for f in sorted(DOWNLOADS.glob("data_*.csv")):
        if not f.read_text(encoding="utf-8", errors="replace").startswith(HEADER):
            print(f"skip (not a KRX price file): {f.name}")
            continue
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if digest in seen:
            f.unlink()
            print(f"duplicate removed: {f.name}")
            continue
        df = read(f)
        code = df["Issue code"].iloc[0]
        target = ORIGINALS / f"{code}_{df['Date'].min():%Y%m%d}_{df['Date'].max():%Y%m%d}.csv"
        f.replace(target)
        seen.add(digest)
        print(f"{f.name} -> {target.name} ({df['Issue name'].iloc[0]}, {len(df)} rows)")

    for code in sorted({p.name.split("_")[0] for p in ORIGINALS.glob("*.csv")}):
        df = pd.concat([read(p) for p in ORIGINALS.glob(f"{code}_*.csv")]).drop_duplicates("Date").sort_values("Date")
        df = df.set_index("Date")
        df.to_parquet(MERGED / f"{code}.parquet")
        halted = ((df["Trading volume"] == 0)).sum()
        names = " / ".join(dict.fromkeys(df["Issue name"]))
        print(f"{code} {names}: {df.index.min().date()} -> {df.index.max().date()}, {len(df)} days, {halted} zero-volume days")


if __name__ == "__main__":
    main()
