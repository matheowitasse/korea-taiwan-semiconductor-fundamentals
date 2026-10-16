"""Q17b: how much of the Q17 scan survives a proper correction for having searched 264 combinations?

Two corrections, both on the NEW regime (2025-07-01 -> 2026-09-16), using only data we already have:

1. **Benjamini-Hochberg FDR** over the 264 two-sided HAC p-values.
2. **Westfall-Young max-t** (the honest version for correlated tests): every signal series is shifted by the SAME random
   number of trading days, which breaks the link between signals and outcomes while keeping the correlation structure
   among signals and among outcomes; the whole 264-test scan is re-run; the distribution of the LARGEST |t| across the
   scan is the null for "the best thing a scan like this finds when nothing is there".
   p_scan(test) = share of draws whose max |t| >= that test's observed |t|.

Still exploratory: a small p_scan says the scan found more than chance explains, not that a specific rule is tradable.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q17_exploratory_scan as q17  # noqa: E402

RESULTS = Path(__file__).resolve().parents[1] / "results"
NEW = q17.PERIODS["NEW"]
N_DRAWS = 500
MIN_SHIFT = 20


def prepare(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        frame = pd.DataFrame({"x": r["x"], "y": r["y"]})[r["mask"].fillna(False)]
        frame = frame[(frame.index >= NEW[0]) & (frame.index <= NEW[1])]
        if frame.dropna().shape[0] >= q17.MIN_N:
            out.append({**{k: r[k] for k in ("asset", "signal", "outcome", "condition")},
                        "x_full": r["x"], "y_full": r["y"], "mask": r["mask"]})
    return out


def run_scan(rows: list[dict], shift: int = 0) -> np.ndarray:
    ts = np.empty(len(rows))
    for i, r in enumerate(rows):
        x = r["x_full"]
        if shift:
            x = pd.Series(np.roll(x.values, shift), index=x.index)
        frame = pd.DataFrame({"x": x, "y": r["y_full"]})[r["mask"].fillna(False)]
        frame = frame[(frame.index >= NEW[0]) & (frame.index <= NEW[1])].dropna()
        if len(frame) < q17.MIN_N:
            ts[i] = 0.0
            continue
        ts[i] = q17.tstat(frame["y"].values, frame["x"].values)[1]
    return ts


def main() -> None:
    d = q17.build()
    rows = prepare(q17.grid(d))
    obs_t = run_scan(rows)
    n_obs = len(d)

    from scipy import stats as st
    p_raw = 2 * (1 - st.norm.cdf(np.abs(obs_t)))
    bh = multipletests(p_raw, method="fdr_bh")[1]

    rng = np.random.default_rng(42)
    max_null = np.empty(N_DRAWS)
    for j in range(N_DRAWS):
        shift = int(rng.integers(MIN_SHIFT, n_obs - MIN_SHIFT))
        max_null[j] = np.abs(run_scan(rows, shift)).max()
        if (j + 1) % 50 == 0:
            print(f"  draw {j + 1}/{N_DRAWS}", file=sys.stderr, flush=True)

    res = pd.DataFrame([{k: r[k] for k in ("asset", "signal", "outcome", "condition")} for r in rows])
    res["t_NEW"] = obs_t
    res["p_raw"] = p_raw
    res["p_BH_fdr"] = bh
    res["p_scan_maxt"] = [float((max_null >= abs(t)).mean()) for t in obs_t]
    res = res.reindex(res["t_NEW"].abs().sort_values(ascending=False).index)

    L = ["# Q17b — Correcting the exploratory scan for having searched 264 combinations", "",
         "Both corrections use only existing data (new regime 2025-07-01 → 2026-09-16). Exploratory: a small p means the",
         "scan found more than chance explains, not that a specific rule is tradable.", "",
         f"- Tests in the scan: {len(rows)}", f"- Max |t| observed: {np.abs(obs_t).max():.2f}",
         f"- Max |t| from {N_DRAWS} scans of shifted signals (null): median {np.median(max_null):.2f}, "
         f"90th pct {np.quantile(max_null, 0.9):.2f}, max {max_null.max():.2f}",
         f"- **Share of null scans whose best test beats our best test: {float((max_null >= np.abs(obs_t).max()).mean()):.3f}**",
         f"- Tests with BH-FDR q < 0.10: {int((res['p_BH_fdr'] < 0.10).sum())}; q < 0.05: {int((res['p_BH_fdr'] < 0.05).sum())}",
         f"- Tests that survive the max-t correction (p_scan < 0.05): {int((res['p_scan_maxt'] < 0.05).sum())}", "",
         "## Top 20 by |t| in the new regime", "", "```",
         res.head(20).to_string(index=False, float_format=lambda v: f"{v:.4f}"), "```", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q17b_multiple_testing.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
