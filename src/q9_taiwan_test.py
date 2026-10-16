"""Q9 Taiwan: value and monthly-revenue momentum in Taiwanese chip-sector stocks.
Exactly as pre-registered in docs/q9_cross_market_preregistration.md. One-sided (positive), no discovery/validation split.
"""

import sys
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q8_multifactor import nw_stats, quintile_returns, zscores
from q9_japan_test import one_sided

ROOT = Path(__file__).resolve().parents[1]
RAW, RESULTS = ROOT / "data" / "raw", ROOT / "results"
TW = RAW / "taiwan"
PRICES = RAW / "q9_tw_prices"
SECTOR_CODES = {"24", "28"}  # semiconductors, electronic components
MIN_STOCKS = 30


def universe() -> pd.DataFrame:
    tw = pd.read_csv(TW / "companies_twse.csv", dtype=str)
    tw = tw.rename(columns={"公司代號": "code", "公司簡稱": "name", "產業別": "sector"})[["code", "name", "sector"]]
    tw["market"] = "TWSE"
    tp = pd.read_csv(TW / "companies_tpex.csv", dtype=str)
    tp = tp.rename(columns={"SecuritiesCompanyCode": "code", "CompanyAbbreviation": "name",
                            "SecuritiesIndustryCode": "sector"})[["code", "name", "sector"]]
    tp["market"] = "TPEx"
    u = pd.concat([tw, tp], ignore_index=True)
    u["sector"] = u["sector"].str.strip().str.zfill(2)
    u = u[u["sector"].isin(SECTOR_CODES) & u["code"].str.fullmatch(r"\d{4}")]
    u["ticker"] = u["code"] + np.where(u["market"] == "TWSE", ".TW", ".TWO")
    return u.drop_duplicates("code").reset_index(drop=True)


def download_prices(u: pd.DataFrame) -> None:
    PRICES.mkdir(parents=True, exist_ok=True)
    todo = [t for t in u["ticker"] if not (PRICES / f"{t.split('.')[0]}.parquet").exists()]
    end = str(date.today() + timedelta(days=1))
    for i in range(0, len(todo), 40):
        batch = todo[i:i + 40]
        data = yf.download(batch, start="2021-06-01", end=end, auto_adjust=True, group_by="ticker",
                           threads=True, progress=False)
        for t in batch:
            try:
                df = data[t].dropna(how="all") if len(batch) > 1 else data.dropna(how="all")
            except KeyError:
                continue
            if len(df):
                df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
                df[["Close"]].to_parquet(PRICES / f"{t.split('.')[0]}.parquet")
        print(f"  prices {min(i + 40, len(todo))}/{len(todo)}")
        time.sleep(2)


def monthly_prices(codes: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    cal = pd.read_parquet(RAW / "full_IDX_TWII.parquet").index
    month_ends = pd.DatetimeIndex(pd.Series(cal, index=cal).groupby([cal.year, cal.month]).max().values)
    px = {}
    for c in codes:
        p = PRICES / f"{c}.parquet"
        if p.exists():
            px[c] = pd.read_parquet(p)["Close"].reindex(cal).ffill().reindex(month_ends)
    px = pd.DataFrame(px)
    return px, px.shift(-1) / px - 1


def value_factor(px: pd.DataFrame) -> pd.DataFrame:
    """1 / price-to-book from the TWSE month-end valuation files (listed market only)."""
    out = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    for f in sorted(TW.glob("pbr_*.csv")):
        d = pd.read_csv(f, dtype={"code": str})
        month = pd.Timestamp(f.stem.split("_")[1] + "01")
        hits = [t for t in px.index if t.year == month.year and t.month == month.month]
        if not hits:
            continue
        pb = d.set_index("code")["pb"]
        pb = pb[(pb > 0) & pb.notna()]
        common = [c for c in px.columns if c in pb.index]
        out.loc[hits[0], common] = (1 / pb[common]).values
    return out


def revenue_factor(px: pd.DataFrame) -> pd.DataFrame:
    """Latest published monthly revenue vs the same month a year earlier (%), known by the 10th of the next month."""
    rows = []
    for f in sorted(TW.glob("revenue_*.csv")):
        d = pd.read_csv(f, dtype={"code": str})
        d["yoy"] = np.where(d["revenue_year_ago"] > 0, 100 * (d["revenue_current"] / d["revenue_year_ago"] - 1), np.nan)
        rows.append(d[["code", "year", "month", "yoy"]])
    rev = pd.concat(rows, ignore_index=True).dropna(subset=["yoy"])
    rev["period"] = pd.PeriodIndex.from_fields(year=rev["year"], month=rev["month"], freq="M")
    out = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    for t in px.index:
        # at month end t the latest published figure is for the previous month
        prev = (t.to_period("M") - 1)
        d = rev[rev["period"] == prev].set_index("code")["yoy"]
        common = [c for c in px.columns if c in d.index]
        out.loc[t, common] = d[common].values
    return out


def main() -> None:
    rng = np.random.default_rng(97)
    u = universe()
    print(f"universe: {len(u)} companies ({u['market'].value_counts().to_dict()})")
    download_prices(u)
    px, ret = monthly_prices(list(u["code"]))
    factors = {"value": value_factor(px), "rev_mom": revenue_factor(px)}
    zs = pd.concat([zscores(factors["value"]), zscores(factors["rev_mom"])], axis=0, keys=["value", "rev_mom"])
    factors["composite"] = zs.groupby(level=1).mean().where(zs.groupby(level=1).count() >= 2)

    rows = []
    for k, f in factors.items():
        usable = f.index[(f.notna().sum(axis=1) >= MIN_STOCKS)]
        usable = usable[(usable >= "2023-01-01") & (usable <= "2026-08-31")]
        if len(usable) < 6:
            rows.append({"factor": k, "months": len(usable), "mean_bp": np.nan, "t": np.nan, "p": np.nan,
                         "placebo_p": np.nan, "long_only_bp": np.nan, "window": "too few months"})
            continue
        st = one_sided(f.loc[usable], ret, rng)
        rows.append({"factor": k, "months": st["months_used"], "mean_bp": st["mean_bp"], "t": st["t"], "p": st["p"],
                     "placebo_p": st["placebo_p"], "long_only_bp": st["long_only_bp"],
                     "window": f"{usable.min():%Y-%m} → {usable.max():%Y-%m}"})
    df = pd.DataFrame(rows)
    ok = df["p"].notna()
    df.loc[ok, "p_holm"] = multipletests(df.loc[ok, "p"], method="holm")[1]
    df["confirmed"] = (df["p_holm"] < 0.05) & (df["placebo_p"] < 0.05)

    L = ["# Q9 Taiwan — value and monthly-revenue momentum in chip-sector stocks", "",
         "Follows `docs/q9_cross_market_preregistration.md`. One-sided (positive), Holm across the 3 Taiwanese tests.", "",
         f"Universe: {len(u)} companies (sector codes 24 semiconductors + 28 electronic components); "
         f"price files {px.shape[1]}. Value uses the TWSE valuation file, so TPEx names have no value score.", "",
         "```", df.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", "",
         f"**Confirmed in Taiwan: {', '.join(df.loc[df['confirmed'], 'factor']) or 'none'}**", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q9_taiwan.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
