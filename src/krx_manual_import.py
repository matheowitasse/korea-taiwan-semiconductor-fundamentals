"""Import hand-downloaded KRX investor files ([12009] Trading by investor (individual issue), daily, trading value,
net buying, details ticked) from ~/Downloads into data/raw/krx_manual/.

KRX files are named data_XXXX_<date>.csv and do not contain the stock name, so each file is identified by matching its
daily foreign + individual net buying value against Naver flows (shares x close) for every stock in
data/raw/naver_flows/. The best match must have correlation >= 0.95 (this is also the Q5 cross-check gate).

Usage:
  python src/krx_manual_import.py            # dry run: show what each file is
  python src/krx_manual_import.py --move     # move + rename matched files
  python src/krx_manual_import.py --check    # re-check every file already in data/raw/krx_manual/
"""

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from naver_download_flows import STOCKS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "data" / "raw" / "krx_manual"
NAVER = ROOT / "data" / "raw" / "naver_flows"
DOWNLOADS = Path.home() / "Downloads"

# The header "Government pension funds, etc." contains an unquoted comma, so names are given explicitly.
DETAILED = ["Date", "Financial investment", "Insurance", "Investment trust", "Private placement", "Bank",
            "Other finances", "Government pension funds", "Other corporations", "Individuals", "Foreigners",
            "Other foreigners", "Total"]
MIN_CORR = 0.95


def read_krx(path: Path) -> pd.DataFrame | None:
    header = path.read_text(errors="replace").splitlines()[0]
    if not header.startswith("Date,Financial investment"):
        return None  # not a detailed daily investor file
    df = pd.read_csv(path, skiprows=1, names=DETAILED)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y/%m/%d")
    return df.set_index("Date").sort_index()


def identify(krx: pd.DataFrame) -> tuple[str, float, float, int]:
    """Best-matching stock code, correlation (foreigners), correlation (individuals), overlapping days."""
    best = ("", -1.0, -1.0, 0)
    for code in STOCKS:
        n = pd.read_parquet(NAVER / f"{code}.parquet")
        j = krx.join(n, how="inner")
        if len(j) < 20:
            continue
        cf = j["Foreigners"].corr(j["foreign_net_shares"] * j["close"])
        ci = j["Individuals"].corr(j["individual_net_shares"] * j["close"])
        if cf > best[1]:
            best = (code, cf, ci, len(j))
    return best


def target_name(code: str, krx: pd.DataFrame) -> str:
    return f"{code}_{krx.index.min():%Y%m%d}_{krx.index.max():%Y%m%d}_value_detailed.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--move", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    MANUAL.mkdir(parents=True, exist_ok=True)
    files = sorted(MANUAL.glob("*.csv")) if a.check else sorted(DOWNLOADS.glob("data_*.csv"), key=lambda p: p.stat().st_mtime)
    for f in files:
        krx = read_krx(f)
        if krx is None:
            print(f"{f.name}: not a detailed daily investor file -> skipped")
            continue
        sums_ok = (krx.drop(columns="Total").sum(axis=1).abs() < 10).mean()
        code, cf, ci, n = identify(krx)
        ok = cf >= MIN_CORR and ci >= MIN_CORR and sums_ok == 1.0
        status = "OK " if ok else "BAD"
        print(f"{status} {f.name}: {code} {STOCKS.get(code, '?'):12s} {krx.index.min().date()} -> {krx.index.max().date()} "
              f"({len(krx)} days, {n} matched) corr foreign {cf:.4f} indiv {ci:.4f} rows-sum-zero {sums_ok:.0%}")
        if a.move and ok and not a.check:
            dest = MANUAL / target_name(code, krx)
            if dest.exists():
                print(f"    {dest.name} already exists -> left in Downloads")
            else:
                shutil.move(str(f), dest)
                print(f"    moved -> {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
