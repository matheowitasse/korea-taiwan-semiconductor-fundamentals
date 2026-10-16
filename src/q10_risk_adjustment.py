"""Q10 risk adjustment: is the strategy's excess return just market, size and momentum exposure?

Regresses the monthly strategy return on (a) the local index, (b) a size spread built inside the same universe
(small minus big), and (c) a 12-1 momentum spread inside the same universe. The intercept is the part the known
exposures do not explain.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt
from q8_multifactor import quintile_returns

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def spread(sig: pd.DataFrame, ret: pd.DataFrame) -> pd.Series:
    """Top-minus-bottom quintile return of a characteristic, inside the same universe."""
    port = quintile_returns(sig, ret)
    return port["ls"]


def main() -> None:
    rows = []
    for name, fn in [("Korea", bt.korea), ("Japan", bt.japan), ("Taiwan", bt.taiwan)]:
        sig, px, ret, mcap, index_close = fn()
        r, _ = bt.backtest(name, sig, px, ret, mcap)
        idx_m = index_close.resample("ME").last()
        bench = (idx_m.shift(-1) / idx_m - 1)
        bench.index = [min([d for d in px.index if d.to_period("M") == p.to_period("M")], default=pd.NaT)
                       for p in bench.index]
        bench = bench[bench.index.notna()]

        mom = spread(px.shift(1) / px.shift(12) - 1, ret)
        size = spread(-np.log(mcap.where(mcap > 0)), ret) if mcap is not None else None

        X = pd.DataFrame({"index": bench.reindex(r.index)})
        X["momentum"] = mom.reindex(r.index)
        if size is not None:
            X["size_small_minus_big"] = size.reindex(r.index)
        d = pd.concat([r.rename("strategy"), X], axis=1).dropna()
        if len(d) < 10:
            rows.append({"market": name, "months": len(d), "note": "too few months"})
            continue
        m = sm.OLS(d["strategy"], sm.add_constant(d.drop(columns="strategy"))).fit(
            cov_type="HAC", cov_kwds={"maxlags": 3})
        row = {"market": name, "months": len(d), "alpha_bp_month": 1e4 * m.params["const"],
               "alpha_t": m.tvalues["const"], "alpha_p": m.pvalues["const"], "r2": m.rsquared}
        for k in ["index", "momentum", "size_small_minus_big"]:
            if k in m.params:
                row[f"beta_{k}"] = m.params[k]
                row[f"t_{k}"] = m.tvalues[k]
        rows.append(row)

    df = pd.DataFrame(rows)
    L = ["# Q10 risk adjustment — is the strategy just market, size and momentum?", "",
         "Monthly strategy return regressed on the local index, a size spread (small − big) and a 12-1 momentum spread,",
         "both built inside the same universe. HAC standard errors (3 lags). `alpha` is the unexplained part.", "",
         "```", df.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q10_risk_adjustment.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
