"""Q15: out-of-sample tests of the profit-surprise (SUE) drift — as pre-registered in
docs/q15_sue_out_of_sample_preregistration.md.

  S1  D0 2022-07-01 → 2022-12-31, CAR60  (never used: the Q7 study started 2023-01)
  S2  D0 2026-07-01 → 2026-08-31, CAR20  (60-day windows not complete yet)
  S3  the same events as S2, CAR60       (only when every window is complete, ≈ 2026-11-20)

Decisive: one-sided placebo p < 0.05 (SUE shuffled within calendar month, 5,000 draws, seed 42).
Reported: HC3 t, quintiles, trimmed slope.

Usage:
  python src/q15_sue_out_of_sample.py --check      # counts only
  python src/q15_sue_out_of_sample.py S1 S2        # run the tests whose windows are complete
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q7_pead_test as q7  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
N_DRAWS = 5000
SPECS = {  # id: (period, outcome, trading days that must be complete)
    "S1": (("2022-07-01", "2022-12-31"), "car60", 61),
    "S2": (("2026-07-01", "2026-08-31"), "car20", 21),
    "S3": (("2026-07-01", "2026-08-31"), "car60", 61),
}


def events_for(test_id: str) -> pd.DataFrame:
    period, outcome, days = SPECS[test_id]
    ev, _ = q7.build_events(require_days=days)
    d = q7.prepare(ev, "A", period)
    d = d[d["sue"].notna() & d[outcome].notna()].copy()
    d["r_sue"] = q7.centered_rank(d["sue"].values, d["quarter_key"].values)
    return d.dropna(subset=["r_sue"]).reset_index(drop=True)


def slope(y: np.ndarray, x: np.ndarray) -> float:
    return np.linalg.lstsq(np.column_stack([np.ones(len(x)), x]), y, rcond=None)[0][1]


def run(test_id: str) -> dict:
    period, outcome, _ = SPECS[test_id]
    d = events_for(test_id)
    y, x = d[outcome].values, d["r_sue"].values
    fit = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HC3")
    obs = fit.params[1]

    rng = np.random.default_rng(42)
    months = d["month_key"].values
    groups = [np.where(months == m)[0] for m in np.unique(months)]
    quarters = d["quarter_key"].values
    sue = d["sue"].values
    draws = np.empty(N_DRAWS)
    for j in range(N_DRAWS):
        s = sue.copy()
        for g in groups:
            s[g] = sue[rng.permutation(g)]
        draws[j] = slope(y, q7.centered_rank(s, quarters))

    lo, hi = np.quantile(y, [0.025, 0.975])
    keep = (y >= lo) & (y <= hi)
    q = pd.qcut(pd.Series(x), 5, labels=False, duplicates="drop")
    top, bot = y[q == q.max()], y[q == q.min()]
    return {"test": test_id, "period": f"{period[0]} → {period[1]}", "outcome": outcome, "n": len(d),
            "months": len(groups), "slope_%": obs * 100, "t_HC3": fit.tvalues[1],
            "placebo_p_one_sided": float((draws >= obs).mean()),
            "pass": bool((draws >= obs).mean() < 0.05),
            "trimmed_slope_%": slope(y[keep], x[keep]) * 100,
            "top_q_mean_%": top.mean() * 100, "top_q_median_%": np.median(top) * 100,
            "bottom_q_mean_%": bot.mean() * 100, "bottom_q_median_%": np.median(bot) * 100}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tests", nargs="*", default=["S1", "S2"])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if a.check:
        for t in SPECS:
            d = events_for(t)
            print(f"{t}: {len(d)} events with SUE and outcome, {d['month_key'].nunique()} months, "
                  f"months {sorted(d['month_key'].unique())}")
        return

    rows = [run(t) for t in a.tests]
    df = pd.DataFrame(rows)
    L = ["# Q15 — Out-of-sample tests of the profit-surprise (SUE) drift", "",
         "Follows `docs/q15_sue_out_of_sample_preregistration.md` (committed before this script was written).",
         "Decisive: one-sided placebo p < 0.05. One earnings season per test → HC3 t and quintiles are reported, not decisive.", "",
         "```", df.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", ""]
    for r in rows:
        L.append(f"**{r['test']} ({r['period']}, {r['outcome']}): {'PASSED' if r['pass'] else 'FAILED'}** — "
                 f"slope {r['slope_%']:.1f} %, placebo p {r['placebo_p_one_sided']:.3f}, n {r['n']}")
    L += ["", "Reference (already-seen data, not a test): Q7b recent period CAR60 slope +31.3 %; "
          "Q7 discovery 2023-01 → 2025-06 slope +5.9 % (trimmed +2.1 %).", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "q15_sue_out_of_sample.md"
    prev = out.read_text(encoding="utf-8") if out.exists() else ""
    out.write_text((prev + "\n" if prev else "") + "\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
