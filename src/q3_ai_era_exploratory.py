"""Q3 exploratory run: the same 8 tests (A-E) on the AI era only. NOT a confirmatory test.

See the project's research log (2026-09-16, "Deviation") for why and for the rules fixed before running.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q1_test_signal import build_signals  # noqa: E402
from q3_edge_search import EXTRACTED, KOSPI, RESULTS, TESTS, daily_series, load_full, run_tests  # noqa: E402

AI_ERA = ("2023-01-01", "2026-09-16")
HALVES = {"2023-2024": ("2023-01-01", "2024-12-31"), "2025-2026": ("2025-01-01", "2026-09-16")}


def main() -> None:
    rng = np.random.default_rng(2023)
    cal = load_full(KOSPI).index
    series, hynix_close = daily_series(cal)
    rel = build_signals(pd.read_csv(EXTRACTED))
    pos = cal.searchsorted(rel["D"])
    rel = rel[pos < len(cal)].copy()
    pos = pos[pos < len(cal)]
    rel["D_kr"], rel["Dm1"] = cal[pos], cal[pos - 1]

    full = run_tests(list(TESTS), AI_ERA, series, hynix_close, rel, cal, rng)
    full["p_holm"] = multipletests(full["t_or_welch_p"], method="holm")[1]

    halves = {}
    for name, period in HALVES.items():
        h = run_tests(list(TESTS), period, series, hynix_close, rel, cal, rng).set_index("id")
        halves[name] = h
        full[f"effect_bp {name}"] = full["id"].map(h["effect_bp"])
        full[f"p {name}"] = full["id"].map(h["t_or_welch_p"])
    same_sign = np.sign(full["effect_bp 2023-2024"]) == np.sign(full["effect_bp 2025-2026"])
    full["lead"] = (full["p_holm"] < 0.10) & (full["placebo_p"] < 0.05) & same_sign

    cols = ["id", "test", "n", "effect_bp", "t_or_welch_p", "p_holm", "placebo_p",
            "effect_bp 2023-2024", "p 2023-2024", "effect_bp 2025-2026", "p 2025-2026", "lead"]
    L = ["# Q3 exploratory — A–E on the AI era (2023-01 → 2026-09)", "",
         "**Exploratory, not confirmatory.** Deviation from the pre-registration, logged in the project's research log before running.", "",
         "Effects: A/B = event-day minus non-event-day mean return (bp); C/D/E = bp per +10 pp of S2. p = two-sided.", "",
         "```", full[cols].to_string(index=False, float_format=lambda v: f"{v:.4f}"), "```", "",
         f"**Leads worth forward-testing: {', '.join(full.loc[full['lead'], 'id']) or 'none'}**", ""]
    (RESULTS / "q3_ai_era_exploratory.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
