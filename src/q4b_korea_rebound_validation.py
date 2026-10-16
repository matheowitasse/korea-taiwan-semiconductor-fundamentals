"""Q4b: Korea-only supplier rebound after SOXX overnight < -2%, narrowed validation on 2025-07 -> 2026-09-16 —
as pre-registered in docs/q4b_korea_supplier_rebound_validation_preregistration.md. Reuses Q4's build() and test().
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q4_supplier_rebound import DISCOVERY, THRESHOLD, build, fmt, test  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
VALIDATION = ("2025-07-01", "2026-09-16")
COST_BP = 30


def details(kr: pd.DataFrame, period: tuple[str, str]) -> dict:
    d = kr[(kr.index >= period[0]) & (kr.index <= period[1])]
    ev = d.loc[d["signal"] < THRESHOLD]
    sup = ev["suppliers"].dropna()
    net = stats.ttest_1samp(sup.values - COST_BP / 1e4, 0.0, alternative="greater")
    return {"period": f"{period[0]} → {period[1]}", "nights": len(sup), "mean_bp": sup.mean() * 1e4,
            "median_bp": sup.median() * 1e4, "hit_rate_%": (sup > 0).mean() * 100,
            "mean_excl_best_bp": sup.drop(sup.idxmax()).mean() * 1e4,
            "p_mean_gt_cost": net.pvalue, "big_names_mean_bp": ev["big"].dropna().mean() * 1e4}


def main() -> None:
    data = build()
    kr = data["KR"]

    val = test(data, "KR", VALIDATION, np.random.default_rng(42))
    val["pass"] = (val["p_one_sided"] < 0.05) and (val["placebo_p"] < 0.05)
    side = pd.DataFrame([details(kr, DISCOVERY), details(kr, VALIDATION)])
    tradable = side.iloc[1]["p_mean_gt_cost"] < 0.05

    nights = kr[(kr.index >= VALIDATION[0]) & (kr.index <= VALIDATION[1]) & (kr["signal"] < THRESHOLD)]
    nights = nights.assign(soxx_pct=nights["signal"] * 100, suppliers_bp=nights["suppliers"] * 1e4,
                           big_bp=nights["big"] * 1e4)[["soxx_pct", "suppliers_bp", "big_bp"]]

    L = ["# Q4b — Korean supplier rebound after big US chip sell-offs: narrowed validation", "",
         "Follows `docs/q4b_korea_supplier_rebound_validation_preregistration.md` (committed before this script).",
         "Korea was chosen after Q4 showed it as the best of three markets → a pass is weaker evidence than a full validation.", "",
         "## Decisive test (2025-07-01 → 2026-09-16, one-sided mean > 0)", "", fmt(pd.DataFrame([val])), "",
         f"**Statistical pass: {'YES' if val['pass'] else 'NO'}** (needs p < 0.05 and placebo p < 0.05)", "",
         f"**Tradable after {COST_BP} bp round-trip cost: {'YES' if tradable else 'NO'}** (one-sided p of mean > {COST_BP} bp < 0.05)", "",
         "## Discovery vs validation (reported, not decisive)", "", fmt(side), "",
         "## Every validation night", "", "```", nights.round(1).to_string(), "```", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q4b_korea_rebound_validation.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
