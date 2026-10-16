"""Q16: has the Korean open overreaction come back in the 2025-07+ regime? — as pre-registered in
docs/q16_open_overreaction_new_regime_preregistration.md.

Decisive: 2025-07-01 → 2026-09-16, 4 assets, Holm over 4, two-sided, HAC(1), circular-shift placebo.
Reported for comparison (already seen in Q2): 2016-01 → 2022-12 and 2023-01 → 2025-06.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q3_edge_search import load_full  # noqa: E402
from q4_supplier_rebound import MARKETS, us_signal  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
NEW = ("2025-07-01", "2026-09-16")
COMPARE = {"pre-AI 2016 → 2022": ("2016-01-01", "2022-12-31"), "AI era 2023 → 2025H1": ("2023-01-01", "2025-06-30")}
N_DRAWS = 5000
MIN_SHIFT = 20
COST = 0.003

ASSETS = {"R1 KOSPI": ["^KS11"], "R2 Samsung": ["005930.KS"], "R3 SK Hynix": ["000660.KS"],
          "R4 Suppliers": MARKETS["KR"]["suppliers"]}


def clean(ticker: str, cal: pd.DatetimeIndex) -> pd.DataFrame:
    df = load_full(ticker)
    flat = (df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"])
    no_vol = (df["Volume"] == 0) if not ticker.startswith("^") else False
    return df.mask(flat | no_vol | (df["Open"] <= 0)).reindex(cal)


def panel() -> pd.DataFrame:
    cal = load_full("^KS11").index
    cal = cal[cal >= "2016-01-01"]
    cols = {"signal": us_signal(cal, load_full("SOXX")).reindex(cal)}
    for name, tickers in ASSETS.items():
        oc = [clean(t, cal)["Close"] / clean(t, cal)["Open"] - 1 for t in tickers]
        cols[name] = pd.concat(oc, axis=1).mean(axis=1)
    return pd.DataFrame(cols, index=cal)


def regress(d: pd.DataFrame, name: str, rng, placebo: bool) -> dict:
    x, y = d["signal"].values, d[name].values
    fit = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    b, t, p = fit.params[1], fit.tvalues[1], fit.pvalues[1]
    out = {"test": name, "n": len(d), "beta": b, "t": t, "p": p,
           "fitted_move_on_-2%_night_bp": b * -0.02 * 1e4,
           "mean_after_down_1%_bp": d.loc[d["signal"] < -0.01, name].mean() * 1e4,
           "mean_after_down_2%_bp": d.loc[d["signal"] < -0.02, name].mean() * 1e4,
           "n_down_2%": int((d["signal"] < -0.02).sum())}
    if placebo:
        draws = np.array([sm.OLS(y, sm.add_constant(np.roll(x, rng.integers(MIN_SHIFT, len(x) - MIN_SHIFT))))
                          .fit(cov_type="HAC", cov_kwds={"maxlags": 1}).tvalues[1] for _ in range(N_DRAWS)])
        out["placebo_p"] = float((np.abs(draws) >= abs(t)).mean())
    return out


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.4f}") + "\n```"


def main() -> None:
    rng = np.random.default_rng(42)
    data = panel()

    def window(period):
        d = data[(data.index >= period[0]) & (data.index <= period[1])]
        return d

    new = pd.DataFrame([regress(window(NEW)[["signal", k]].dropna(), k, rng, True) for k in ASSETS])
    new["p_holm"] = multipletests(new["p"], method="holm")[1]
    new["pass"] = (new["p_holm"] < 0.10) & (new["placebo_p"] < 0.05)

    L = ["# Q16 — Has the Korean open overreaction come back in the new regime?", "",
         "Follows `docs/q16_open_overreaction_new_regime_preregistration.md` (committed before this script was written).",
         "beta < 0 = the open overshot the US move and partly reversed during the Korean session. Two-sided, HAC(1), "
         "5,000 circular-shift placebo draws. Single-period test (no validation split possible).", "",
         f"## Decisive: {NEW[0]} → {NEW[1]}", "", fmt(new), "",
         f"**Passed: {', '.join(new.loc[new['pass'], 'test']) or 'none'}** (needs Holm p < 0.10 and placebo p < 0.05)", "",
         f"Cost reference: a round trip costs {COST * 1e4:.0f} bp; the fitted reversal after a −2 % US night is in the table.", ""]

    L += ["## Comparison periods (already seen in Q2, not decisive)", ""]
    for label, per in COMPARE.items():
        old = pd.DataFrame([regress(window(per)[["signal", k]].dropna(), k, rng, False) for k in ASSETS])
        L += [f"**{label}**", "", fmt(old), ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q16_open_overreaction.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
