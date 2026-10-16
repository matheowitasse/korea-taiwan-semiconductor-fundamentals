"""Q25 step 1: import KRX short-position / short-selling files (pages 33001 and 32001) from ~/Downloads.

The exports carry no date column and the filename holds the download timestamp, so each file's as-of date is
identified by implied price (market capitalisation / listed shares) matched against unadjusted daily closes from the
Naver price files — the same trick used for the quarter-end snapshots in `q7_import_krx_snapshots.py`.

Usage: python src/q25_import_short_positions.py
Output: data/raw/krx_short/<market>_<date>_<kind>.csv and a summary of what was imported.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "krx_short"
DOWNLOADS = Path.home() / "Downloads"
ENCODINGS = ("utf-8-sig", "cp949", "euc-kr", "latin-1")


def read_csv(path: Path) -> pd.DataFrame | None:
    for enc in ENCODINGS:
        try:
            df = pd.read_csv(path, dtype=str, encoding=enc)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
        df.columns = [c.strip() for c in df.columns]
        if "Issue code" in df.columns:
            return df
        return None
    return None


def raw_prices() -> pd.DataFrame:
    """Unadjusted Naver closes where available, plus Yahoo closes, which run a few days later.

    Naver stops earlier than Yahoo, and a snapshot dated after the last Naver day would otherwise be matched to the
    closest day it knows (that mislabelled two files as 2026-09-16 when they were 2026-09-17).
    """
    cols = {}
    for f in (ROOT / "data" / "raw" / "naver_flows").glob("*.parquet"):
        if f.stem.startswith("index_"):
            continue
        d = pd.read_parquet(f)
        if "close" in d.columns:
            cols[f.stem] = d["close"]
    naver = pd.DataFrame(cols)
    ycols = {}
    for f in (ROOT / "data" / "raw" / "q7_yahoo").glob("*.parquet"):
        d = pd.read_parquet(f)
        d.columns = [c if isinstance(c, str) else c[0] for c in d.columns]
        ycols[f.stem] = d["Close"]
    yahoo = pd.DataFrame(ycols)
    return naver.combine_first(yahoo) if len(naver) else yahoo


def traded_volumes() -> pd.DataFrame:
    """Daily share volume per stock (Naver where available, Yahoo otherwise) — used to date the 32001 exports,
    which carry trading volume but no market capitalisation."""
    cols = {}
    for f in (ROOT / "data" / "raw" / "naver_flows").glob("*.parquet"):
        if f.stem.startswith("index_"):
            continue
        d = pd.read_parquet(f)
        if "volume" in d.columns:
            cols[f.stem] = d["volume"]
    naver = pd.DataFrame(cols)
    ycols = {}
    for f in (ROOT / "data" / "raw" / "q7_yahoo").glob("*.parquet"):
        d = pd.read_parquet(f)
        d.columns = [c if isinstance(c, str) else c[0] for c in d.columns]
        ycols[f.stem] = d["Volume"]
    yahoo = pd.DataFrame(ycols)
    return naver.combine_first(yahoo) if len(naver) else yahoo


def identify_by_volume(df: pd.DataFrame, vol: pd.DataFrame) -> tuple[pd.Timestamp | None, float]:
    v = pd.to_numeric(df.get("Quantity_Trading volume"), errors="coerce")
    if v is None:
        return None, np.nan
    codes = df["Issue code"].str.zfill(6).values
    keep = [(c, x) for c, x in zip(codes, v.values) if c in vol.columns and np.isfinite(x) and x > 0]
    if len(keep) < 10:
        return None, np.nan
    sub_codes = [c for c, _ in keep]
    sub_vol = np.array([x for _, x in keep])
    best, best_err = None, np.inf
    for d in vol.index[vol.index >= "2025-01-01"]:
        row = vol.loc[d, sub_codes].astype(float).values
        with np.errstate(divide="ignore", invalid="ignore"):
            err = float(np.nanmedian(np.abs(sub_vol / row - 1)))
        if np.isfinite(err) and err < best_err:
            best, best_err = d, err
    return best, best_err


def identify(df: pd.DataFrame, px: pd.DataFrame) -> tuple[pd.Timestamp | None, float]:
    cap = pd.to_numeric(df.get("Amount_Market cap."), errors="coerce")
    sh = pd.to_numeric(df.get("Quantity_No. of listed shares"), errors="coerce")
    if cap is None or sh is None:
        return None, np.nan
    implied = (cap / sh).values
    codes = df["Issue code"].str.zfill(6).values
    common = [i for i, c in enumerate(codes) if c in px.columns]
    if len(common) < 10:
        return None, np.nan
    sub_codes = [codes[i] for i in common]
    sub_implied = implied[common]
    best, best_err = None, np.inf
    for d in px.index[px.index >= "2025-01-01"]:
        row = px.loc[d, sub_codes].astype(float).values
        err = float(np.nanmedian(np.abs(sub_implied / row - 1)))
        if np.isfinite(err) and err < best_err:
            best, best_err = d, err
    return best, best_err


def main() -> None:
    px, px_vol = raw_prices(), traded_volumes()
    RAW.mkdir(parents=True, exist_ok=True)
    files = sorted(DOWNLOADS.glob("data_*.csv"), key=lambda p: p.stat().st_mtime)
    rows = []
    for f in files:
        df = read_csv(f)
        if df is None or "Issue code" not in df.columns:
            continue
        cols = " ".join(df.columns).lower()
        kind = ("position" if "net short position" in cols else
                "transaction" if "short-selling volume" in cols else None)
        if kind is None:
            continue
        date, err = identify(df, px) if kind == "position" else identify_by_volume(df, px_vol)
        if date is None:
            print(f"{f.name}: could not identify the date — skipped")
            continue
        market = "KOSPI" if len(df) < 1200 else "KOSDAQ"
        dest = RAW / f"{market}_{date:%Y%m%d}_{kind}.csv"
        df.to_csv(dest, index=False, encoding="utf-8-sig")
        rows.append({"file": f.name, "market": market, "date": date.date(), "kind": kind, "issues": len(df),
                     "price_match_error_%": round(err * 100, 2), "saved_as": dest.name})
    if not rows:
        sys.exit("no KRX short-selling exports found in ~/Downloads")
    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    print(f"\nimported {len(out)} files -> {RAW.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
