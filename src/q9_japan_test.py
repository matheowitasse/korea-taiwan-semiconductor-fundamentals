"""Q9 Japan: does the Korean factor result appear in Japanese chip-sector stocks?
Exactly as pre-registered in docs/q9_cross_market_preregistration.md. One-sided (positive), no discovery/validation split.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q8_multifactor import nw_stats, quintile_returns, zscores

ROOT = Path(__file__).resolve().parents[1]
RAW, RESULTS = ROOT / "data" / "raw", ROOT / "results"
SECTORS = ["電気機器", "精密機器"]
MIN_STOCKS, N_PERM, LATE_HOUR = 30, 500, 15


def quarterly_profits(fins: pd.DataFrame) -> pd.DataFrame:
    """Cumulative Japanese statements -> single-quarter operating profit, with the date it became public."""
    f = fins.copy()
    f["OP"] = pd.to_numeric(f["OP"], errors="coerce")
    f["TA"] = pd.to_numeric(f["TA"], errors="coerce")
    f["BPS"] = pd.to_numeric(f["BPS"], errors="coerce")
    f = f[f["CurPerType"].isin(["1Q", "2Q", "3Q", "FY"])].dropna(subset=["OP"])
    f["disc"] = pd.to_datetime(f["DiscDate"])
    late = pd.to_datetime(f["DiscTime"], format="%H:%M:%S", errors="coerce").dt.hour >= LATE_HOUR
    f["avail"] = f["disc"] + pd.to_timedelta(late.fillna(True).astype(int), unit="D")  # known next day if late
    order = {"1Q": 1, "2Q": 2, "3Q": 3, "FY": 4}
    f["q"] = f["CurPerType"].map(order)
    f = f.sort_values(["Code", "CurFYEn", "q"]).drop_duplicates(["Code", "CurFYEn", "q"], keep="last")
    f["op_q"] = f.groupby(["Code", "CurFYEn"])["OP"].diff().fillna(f["OP"].where(f["q"] == 1))
    f["period_end"] = pd.to_datetime(f["CurPerEn"])
    return f.dropna(subset=["op_q"]).sort_values(["Code", "period_end"])


def build(fq: pd.DataFrame, px: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Factor values at each month end, using only statements already public then."""
    idx, cols = px.index, px.columns
    out = {k: pd.DataFrame(index=idx, columns=cols, dtype=float) for k in ["quality", "value", "earn_mom"]}
    for code, g in fq.groupby("Code"):
        col = code[:4]
        if col not in cols:
            continue
        g = g.sort_values("period_end")
        g["op_ttm"] = g["op_q"].rolling(4, min_periods=4).sum()
        g["op_yoy"] = np.where(g["op_q"].shift(4) > 0, 100 * (g["op_q"] / g["op_q"].shift(4) - 1), np.nan)
        for t in idx:
            known = g[g["avail"] <= t]
            if not len(known):
                continue
            r = known.iloc[-1]
            price = px.at[t, col]
            if np.isfinite(r["op_ttm"]) and np.isfinite(r["TA"]) and r["TA"] > 0:
                out["quality"].at[t, col] = r["op_ttm"] / r["TA"]
            if np.isfinite(r["BPS"]) and np.isfinite(price) and price > 0:
                out["value"].at[t, col] = r["BPS"] / price
            if np.isfinite(r["op_yoy"]):
                out["earn_mom"].at[t, col] = r["op_yoy"]
    zs = [zscores(out[k]) for k in ["quality", "value", "earn_mom"]]
    stack = pd.concat(zs, axis=0, keys=["quality", "value", "earn_mom"])
    out["composite"] = stack.groupby(level=1).mean().where(stack.groupby(level=1).count() >= 2)
    return out


def monthly(px_dir: Path, cal: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    month_ends = pd.DatetimeIndex(pd.Series(cal, index=cal).groupby([cal.year, cal.month]).max().values)
    px = {}
    for p in px_dir.glob("*.parquet"):
        s = pd.read_parquet(p)["Close"].reindex(cal).ffill()
        px[p.stem] = s.reindex(month_ends)
    px = pd.DataFrame(px)
    return px, px.shift(-1) / px - 1


def one_sided(sig: pd.DataFrame, ret: pd.DataFrame, rng: np.random.Generator) -> dict:
    port = quintile_returns(sig, ret.reindex(sig.index))
    st = nw_stats(port["ls"])
    if not np.isfinite(st.get("t", np.nan)):
        return {**st, "placebo_p": np.nan, "long_only_bp": np.nan, "months_used": 0}
    st["p"] = stats.norm.sf(st["t"])
    draws = []
    for _ in range(N_PERM):
        sh = sig.apply(lambda row: pd.Series(rng.permutation(row.values), index=row.index), axis=1)
        draws.append(quintile_returns(sh, ret.reindex(sh.index))["ls"].mean())
    st["placebo_p"] = float((np.array(draws) >= port["ls"].mean()).mean())
    st["long_only_bp"] = nw_stats(port["long_only"])["mean_bp"]
    st["months_used"] = len(port)
    return st


def main() -> None:
    rng = np.random.default_rng(99)
    master = pd.read_csv(RAW / "jquants" / "master.csv", dtype={"Code": str})
    uni = set(master.loc[master["S33Nm"].isin(SECTORS), "Code"])
    fins = pd.read_csv(RAW / "jquants" / "fins_summary.csv", dtype={"Code": str})
    fins = fins[fins["Code"].isin(uni)]
    cal = pd.read_parquet(RAW / "full_IDX_N225.parquet").index
    px, ret = monthly(RAW / "q9_jp_prices", cal)
    factors = build(quarterly_profits(fins), px)

    rows = []
    for k, f in factors.items():
        usable = f.index[f.notna().sum(axis=1) >= MIN_STOCKS]
        if len(usable) < 6:
            rows.append({"factor": k, "months": len(usable), "mean_bp": np.nan, "t": np.nan, "p": np.nan,
                         "placebo_p": np.nan, "long_only_bp": np.nan, "window": "too few months"})
            continue
        sig = f.loc[usable]
        st = one_sided(sig, ret, rng)
        rows.append({"factor": k, "months": st["months_used"], "mean_bp": st["mean_bp"], "t": st["t"], "p": st["p"],
                     "placebo_p": st["placebo_p"], "long_only_bp": st["long_only_bp"],
                     "window": f"{usable.min():%Y-%m} → {usable.max():%Y-%m}"})
    df = pd.DataFrame(rows)
    ok = df["p"].notna()
    df.loc[ok, "p_holm"] = multipletests(df.loc[ok, "p"], method="holm")[1]
    df["confirmed"] = (df["p_holm"] < 0.05) & (df["placebo_p"] < 0.05)

    L = ["# Q9 Japan — do the Korean factors work in Japanese chip-sector stocks?", "",
         "Follows `docs/q9_cross_market_preregistration.md`. One-sided (positive), Holm across the 4 Japanese tests.", "",
         f"Universe: {len(uni)} companies in {' + '.join(SECTORS)}; price files {px.shape[1]}.", "",
         "```", df.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", "",
         f"**Confirmed in Japan: {', '.join(df.loc[df['confirmed'], 'factor']) or 'none'}**", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q9_japan.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
