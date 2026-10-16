"""Q27: does the Taiwanese revenue-momentum effect exist before the AI era?
Exactly as pre-registered in docs/q27_taiwan_pre_ai_preregistration.md. One decisive test, run once.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q9_taiwan_test as tw
from q8_multifactor import nw_stats, quintile_returns
from q9_japan_test import one_sided

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DECISIVE = ("2016-01-01", "2022-12-31")
SEEN = ("2023-01-01", "2026-08-31")
FULL = ("2016-01-01", "2026-08-31")
MIN_STOCKS = 30


def window(f: pd.DataFrame, period) -> pd.DatetimeIndex:
    idx = f.index[(f.notna().sum(axis=1) >= MIN_STOCKS)]
    return idx[(idx >= period[0]) & (idx <= period[1])]


def main() -> None:
    rng = np.random.default_rng(27)
    u = tw.universe()
    px, ret = tw.monthly_prices(list(u["code"]))
    rev = tw.revenue_factor(px)
    val = tw.value_factor(px)

    rows = []
    for name, period in [("DECISIVE 2016-01 → 2022-12 (unseen)", DECISIVE),
                         ("already seen 2023-01 → 2026-08", SEEN),
                         ("full sample (mixed)", FULL)]:
        for label, f in [("revenue momentum", rev), ("value", val)]:
            use = window(f, period)
            if len(use) < 6:
                rows.append({"window": name, "factor": label, "months": len(use)})
                continue
            st = one_sided(f.loc[use], ret, rng)
            rows.append({"window": name, "factor": label, "months": st["months_used"], "mean_bp": st["mean_bp"],
                         "t": st["t"], "p_one_sided": st["p"], "placebo_p": st["placebo_p"],
                         "long_only_bp": st["long_only_bp"], "median_names": int(f.loc[use].notna().sum(axis=1).median()),
                         "span": f"{use.min():%Y-%m} → {use.max():%Y-%m}"})
    df = pd.DataFrame(rows)

    # risk adjustment on the decisive window
    use = window(rev, DECISIVE)
    ls = quintile_returns(rev.loc[use], ret.reindex(use))["ls"]
    mom = quintile_returns((px.shift(1) / px.shift(12) - 1).reindex(use), ret.reindex(use))["ls"]
    idx = pd.read_parquet(ROOT / "data" / "raw" / "full_IDX_TWII.parquet")["Close"].resample("ME").last()
    idx = (idx.shift(-1) / idx - 1)
    idx.index = [min([d for d in px.index if d.to_period("M") == p.to_period("M")], default=pd.NaT) for p in idx.index]
    idx = idx[idx.index.notna()]
    d = pd.concat([ls.rename("ls"), idx.reindex(ls.index).rename("index"),
                   mom.reindex(ls.index).rename("momentum")], axis=1).dropna()
    adj = {}
    if len(d) > 12:
        m = sm.OLS(d["ls"], sm.add_constant(d.drop(columns="ls"))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        adj = {"months": len(d), "alpha_bp": 1e4 * m.params["const"], "alpha_t": m.tvalues["const"],
               "alpha_p_one_sided": float(stats.norm.sf(m.tvalues["const"])),
               "beta_index": m.params["index"], "beta_momentum": m.params["momentum"], "r2": m.rsquared}

    dec = df[(df["window"].str.startswith("DECISIVE")) & (df["factor"] == "revenue momentum")].iloc[0]
    passed = bool(dec.get("t", 0) > 2 and dec.get("placebo_p", 1) < 0.05)

    L = ["# Q27 — Taiwan before the AI era", "",
         "Follows `docs/q27_taiwan_pre_ai_preregistration.md` (committed before any pre-2022-06 Taiwanese data was",
         "downloaded). One decisive test: revenue momentum over 2016-01 → 2022-12, one-sided positive.", "",
         "```", df.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", "",
         f"**DECISIVE TEST: {'PASSES' if passed else 'FAILS'}** "
         f"(mean {dec.get('mean_bp', float('nan')):.0f} bp/month, t {dec.get('t', float('nan')):.2f}, "
         f"placebo p {dec.get('placebo_p', float('nan')):.3f}, {int(dec.get('months', 0))} months)", "",
         "## Risk adjustment on the decisive window (index + momentum spread, HAC 3 lags)", "",
         "```", pd.Series(adj).to_string(float_format=lambda v: f"{v:.3f}") if adj else "not enough months", "```", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q27_taiwan_pre_ai.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
