"""Q21: is the cross-sectional effect just illiquidity? — as specified in docs/q21_liquidity_robustness_spec.md.

R1 spread inside Amihud terciles · R2 alpha after adding an illiquidity factor · R3 excluding the smallest 20%
R4 excluding sub-KRW 1,000 stocks · R5 value-weighted, for comparison.

Robustness on data already used: it cannot change the Q8/Q9 verdicts, only which reading of them the data supports.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402
import q8_multifactor as kr  # noqa: E402
from q8_multifactor import nw_stats, quintile_returns  # noqa: E402
from q13_leg_decomposition import adjust  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"
START = pd.Timestamp("2023-01-01")
MIN_DAYS = 120
MIN_NAMES = 25
PENNY_KRW = 1000


def daily_close_volume(code: str) -> pd.DataFrame | None:
    y, k = RAW / "q7_yahoo" / f"{code}.parquet", RAW / "krx_prices" / f"{code}.parquet"
    if y.exists():
        d = pd.read_parquet(y)
        d.columns = [c if isinstance(c, str) else c[0] for c in d.columns]
        return d[["Close", "Volume"]].astype(float)
    if k.exists():
        d = pd.read_parquet(k)
        return d.rename(columns={"Trading volume": "Volume"})[["Close", "Volume"]].astype(float)
    return None


def controls_frame(sig: pd.DataFrame, px: pd.DataFrame, ret: pd.DataFrame, mcap, index_close) -> pd.DataFrame:
    """Index, momentum and size controls, built exactly as in src/q10_risk_adjustment.py."""
    idx_m = index_close.resample("ME").last()
    bench = (idx_m.shift(-1) / idx_m - 1)
    bench.index = [min([d for d in px.index if d.to_period("M") == p.to_period("M")], default=pd.NaT)
                   for p in bench.index]
    bench = bench[bench.index.notna()]
    c = pd.DataFrame({"index": bench.reindex(sig.index),
                      "momentum": quintile_returns(px.shift(1) / px.shift(12) - 1, ret)["ls"].reindex(sig.index)})
    if mcap is not None:
        c["size_small_minus_big"] = quintile_returns(-np.log(mcap.where(mcap > 0)), ret)["ls"].reindex(sig.index)
    return c


def amihud_panel(codes, month_ends: pd.DatetimeIndex, loader) -> pd.DataFrame:
    """Trailing 12-month Amihud illiquidity per stock-month (mean |return| / traded value, scaled)."""
    out = pd.DataFrame(index=month_ends, columns=list(codes), dtype=float)
    for code in codes:
        d = loader(code)
        if d is None or len(d) < MIN_DAYS:
            continue
        d = d[(d["Volume"] > 0) & (d["Close"] > 0)]
        illiq = (d["Close"].pct_change().abs() / (d["Close"] * d["Volume"])) * 1e6
        illiq = illiq.replace([np.inf, -np.inf], np.nan).dropna()
        if len(illiq) < MIN_DAYS:
            continue
        roll = illiq.rolling("365D").mean()
        cnt = illiq.rolling("365D").count()
        s = roll.where(cnt >= MIN_DAYS)
        out[code] = s.reindex(month_ends, method="ffill")
    return out


def spread_in_group(sig: pd.DataFrame, ret: pd.DataFrame, mask: pd.DataFrame, label: str) -> dict:
    s = sig.where(mask)
    keep = s.notna().sum(axis=1) >= MIN_NAMES
    if keep.sum() < 12:
        return {"group": label, "months": int(keep.sum()), "median_names": np.nan, "spread_bp": np.nan, "t": np.nan}
    q = quintile_returns(s[keep], ret.reindex(s[keep].index))
    st = nw_stats(q["ls"])
    return {"group": label, "months": st["months"], "median_names": float(s[keep].notna().sum(axis=1).median()),
            "spread_bp": st["mean_bp"], "t": st["t"]}


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.2f}") + "\n```"


def main() -> None:
    rows_r1, rows_r2, rows_other = [], [], []

    for market, loader in (("Korea", daily_close_volume),):   # Taiwan: cached prices have no volume (see spec note)
        sig, px, ret, mcap, index_close = bt.korea()
        sig = sig.loc[sig.index >= START]
        ret = ret.reindex(sig.index)
        illiq = amihud_panel(px.columns, sig.index, loader)
        cover = illiq.notna().sum(axis=1).median()
        print(f"{market}: Amihud coverage, median {cover:.0f} of {px.shape[1]} names per month", file=sys.stderr)

        # R1 — inside Amihud terciles
        rank = illiq.rank(axis=1, pct=True)
        for label, lo, hi in (("most liquid", 0.0, 1 / 3), ("middle", 1 / 3, 2 / 3), ("least liquid", 2 / 3, 1.0)):
            mask = (rank > lo) & (rank <= hi)
            rows_r1.append({"market": market, **spread_in_group(sig, ret, mask, label)})
        rows_r1.append({"market": market, **spread_in_group(sig, ret, illiq.notna(), "all (Amihud available)")})

        # R2 — add an illiquidity factor to the existing controls
        base = quintile_returns(sig, ret)["ls"]
        illiq_factor = quintile_returns(illiq, ret)["ls"]          # long illiquid − short liquid
        ctrl = controls_frame(sig, px, ret, mcap, index_close)
        for name, c in (("existing controls", ctrl),
                        ("+ illiquidity factor", ctrl.join(illiq_factor.rename("illiquidity"), how="left"))):
            a = adjust(base, c)
            rows_r2.append({"market": market, "controls": name, **{k: round(v, 3) for k, v in a.items()}})

        # R3/R4/R5 — Korea only (needs market caps and KRW prices)
        if market == "Korea":
            cap_rank = mcap.rank(axis=1, pct=True)
            rows_other.append({"market": market, **spread_in_group(sig, ret, cap_rank > 0.20, "excl. smallest 20% by market cap")})
            rows_other.append({"market": market, **spread_in_group(sig, ret, px.reindex(sig.index) >= PENNY_KRW,
                                                                   f"excl. price < KRW {PENNY_KRW:,}")})
            vw = quintile_returns(sig, ret, weights=mcap.reindex(sig.index))
            st = nw_stats(vw["ls"])
            rows_other.append({"market": market, "group": "value-weighted (known)", "months": st["months"],
                               "median_names": np.nan, "spread_bp": st["mean_bp"], "t": st["t"]})

    r1, r2, other = pd.DataFrame(rows_r1), pd.DataFrame(rows_r2), pd.DataFrame(rows_other)
    liquid_ok = r1[(r1["group"] == "most liquid")]
    illiq_ok = r2[r2["controls"] == "+ illiquidity factor"]
    verdict = []
    for m in ("Korea",):
        a = liquid_ok.loc[liquid_ok["market"] == m, "t"]
        b = illiq_ok.loc[illiq_ok["market"] == m, "alpha_t"]
        ok = bool(len(a) and len(b) and a.iloc[0] > 2 and b.iloc[0] > 2)
        verdict.append(f"- **{m}: {'survives' if ok else 'does NOT survive'}** the pre-specified reading "
                       f"(most-liquid tercile t = {a.iloc[0]:.2f}; alpha t with illiquidity factor = {b.iloc[0]:.2f}).")

    L = ["# Q21 — Is the effect just illiquidity?", "",
         "Follows `docs/q21_liquidity_robustness_spec.md` (committed before this script was written).",
         "Robustness on data already used: it cannot change the Q8/Q9 verdicts, only which reading they support.", "",
         "## R1 — long–short spread inside Amihud illiquidity terciles", "", fmt(r1), "",
         "## R2 — alpha before and after adding an illiquidity factor", "", fmt(r2), "",
         "## R3–R5 — size and price screens (Korea)", "", fmt(other), "",
         "Taiwan is not covered by R1/R2: the cached Taiwanese price files hold closing prices only, so Amihud cannot be",
         "computed without re-downloading volume series (noted in the spec before running).", "",
         "## Reading", ""] + verdict + [""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q21_liquidity_robustness.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
