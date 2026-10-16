"""Q13 (diagnostic): does the edge come from picking winners or from avoiding losers?

Splits the long-short spread into two legs, per month:
    long leg  = top quintile − universe average      ("does picking winners add value?")
    short leg = universe average − bottom quintile   ("does avoiding losers add value?")
Each leg is also risk-adjusted (local index, momentum spread, and size spread where market caps exist).

Diagnostic only: it decomposes results already obtained on data already seen. It changes no verdict; it tells us which
part of the effect a long-only investor could ever capture.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt
from q8_multifactor import nw_stats, quintile_returns

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
START = pd.Timestamp("2023-01-01")


def legs(sig: pd.DataFrame, ret: pd.DataFrame) -> pd.DataFrame:
    sig = sig.loc[sig.index >= START]
    p = quintile_returns(sig, ret.reindex(sig.index))
    return pd.DataFrame({"long_leg": p["top"] - p["universe"], "short_leg": p["universe"] - p["bottom"],
                         "long_short": p["top"] - p["bottom"], "universe": p["universe"]})


def adjust(y: pd.Series, controls: pd.DataFrame) -> dict:
    d = pd.concat([y.rename("y"), controls.reindex(y.index)], axis=1).dropna()
    if len(d) < 12:
        return {}
    m = sm.OLS(d["y"], sm.add_constant(d.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    return {"alpha_bp": 1e4 * m.params["const"], "alpha_t": m.tvalues["const"],
            "alpha_p_one_sided": float(stats.norm.sf(m.tvalues["const"]))}


def main() -> None:
    rows, yearly = [], []
    for name, fn in [("Korea", bt.korea), ("Taiwan", bt.taiwan)]:
        sig, px, ret, mcap, index_close = fn()
        L = legs(sig, ret)
        idx = index_close.resample("ME").last()
        idx = (idx.shift(-1) / idx - 1)
        idx.index = [min([d for d in px.index if d.to_period("M") == p.to_period("M")], default=pd.NaT) for p in idx.index]
        idx = idx[idx.index.notna()]
        controls = pd.DataFrame({"index": idx,
                                 "momentum": quintile_returns(px.shift(1) / px.shift(12) - 1, ret)["ls"]})
        if mcap is not None:
            controls["size"] = quintile_returns(-np.log(mcap.where(mcap > 0)), ret)["ls"]
        for leg in ["long_leg", "short_leg", "long_short"]:
            st = nw_stats(L[leg])
            rows.append({"market": name, "leg": leg, "months": st["months"], "mean_bp": st["mean_bp"], "t": st["t"],
                         "share_of_spread_%": 100 * L[leg].mean() / L["long_short"].mean() if leg != "long_short" else 100.0,
                         "hit_%": 100 * (L[leg] > 0).mean(), **adjust(L[leg], controls)})
        for y, g in L.groupby(L.index.year):
            yearly.append({"market": name, "year": y, "long_leg_bp": 1e4 * g["long_leg"].mean(),
                           "short_leg_bp": 1e4 * g["short_leg"].mean(), "universe_bp": 1e4 * g["universe"].mean()})

    df, yr = pd.DataFrame(rows), pd.DataFrame(yearly)
    out = ["# Q13 (diagnostic) — winners or losers: where does the edge come from?", "",
           "long leg = top quintile − universe average · short leg = universe average − bottom quintile.",
           "`alpha` columns control for the local index, a momentum spread (and a size spread in Korea), HAC 3 lags.",
           "Diagnostic on data already used: it changes no verdict, it locates the effect.", "",
           "```", df.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", "",
           "## Year by year (monthly averages, basis points)", "",
           "```", yr.to_string(index=False, float_format=lambda v: f"{v:.1f}"), "```", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q13_leg_decomposition.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
