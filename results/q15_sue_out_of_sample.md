# Q15 — Out-of-sample tests of the profit-surprise (SUE) drift

Follows `docs/q15_sue_out_of_sample_preregistration.md` (committed before this script was written).
Decisive: one-sided placebo p < 0.05. One earnings season per test → HC3 t and quintiles are reported, not decisive.

```
test                  period outcome  n  months  slope_%  t_HC3  placebo_p_one_sided  pass  trimmed_slope_%  top_q_mean_%  top_q_median_%  bottom_q_mean_%  bottom_q_median_%
  S1 2022-07-01 → 2022-12-31   car60 86       2    2.501  0.632                0.315 False            0.854        -2.632          -6.279           -3.763             -3.578
  S2 2026-07-01 → 2026-08-31   car20 99       2   -8.683 -1.612                0.926 False           -4.754        -6.257          -6.029           -1.622             -6.531
```

**S1 (2022-07-01 → 2022-12-31, car60): FAILED** — slope 2.5 %, placebo p 0.315, n 86
**S2 (2026-07-01 → 2026-08-31, car20): FAILED** — slope -8.7 %, placebo p 0.926, n 99

Reference (already-seen data, not a test): Q7b recent period CAR60 slope +31.3 %; Q7 discovery 2023-01 → 2025-06 slope +5.9 % (trimmed +2.1 %).
