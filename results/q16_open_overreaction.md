# Q16 — Has the Korean open overreaction come back in the new regime?

Follows `docs/q16_open_overreaction_new_regime_preregistration.md` (committed before this script was written).
beta < 0 = the open overshot the US move and partly reversed during the Korean session. Two-sided, HAC(1), 5,000 circular-shift placebo draws. Single-period test (no validation split possible).

## Decisive: 2025-07-01 → 2026-09-16

```
        test   n    beta       t      p  fitted_move_on_-2%_night_bp  mean_after_down_1%_bp  mean_after_down_2%_bp  n_down_2%  placebo_p  p_holm  pass
    R1 KOSPI 297  0.0453  0.5169 0.6052                      -9.0635               -21.1557               -39.5595         34     0.5836  1.0000 False
  R2 Samsung 297 -0.1725 -1.7801 0.0751                      34.4980                19.1966                27.8061         34     0.1006  0.3002 False
 R3 SK Hynix 297 -0.1949 -1.7113 0.0870                      38.9847                12.9346                41.1324         34     0.1018  0.3002 False
R4 Suppliers 297  0.0269  0.2577 0.7967                      -5.3891                15.8402               -31.3243         34     0.8054  1.0000 False
```

**Passed: none** (needs Holm p < 0.10 and placebo p < 0.05)

Cost reference: a round trip costs 30 bp; the fitted reversal after a −2 % US night is in the table.

## Comparison periods (already seen in Q2, not decisive)

**pre-AI 2016 → 2022**

```
        test    n    beta       t      p  fitted_move_on_-2%_night_bp  mean_after_down_1%_bp  mean_after_down_2%_bp  n_down_2%
    R1 KOSPI 1716 -0.0377 -1.9112 0.0560                       7.5311                 1.4355                14.2838        152
  R2 Samsung 1699 -0.0672 -2.8732 0.0041                      13.4371                13.4851                26.9468        149
 R3 SK Hynix 1700 -0.1450 -4.2228 0.0000                      29.0077                17.2151                45.7709        150
R4 Suppliers 1707 -0.0588 -1.6025 0.1090                      11.7651                 9.9557                36.5560        151
```

**AI era 2023 → 2025H1**

```
        test   n    beta       t      p  fitted_move_on_-2%_night_bp  mean_after_down_1%_bp  mean_after_down_2%_bp  n_down_2%
    R1 KOSPI 606  0.0128  0.5045 0.6139                      -2.5671                -6.3367                 1.1509         56
  R2 Samsung 607 -0.0314 -1.1381 0.2551                       6.2758                -0.2574                 3.2177         56
 R3 SK Hynix 607 -0.0165 -0.3311 0.7406                       3.3045               -11.2155                12.5974         56
R4 Suppliers 607 -0.0720 -1.4507 0.1469                      14.3941                28.2296                52.3703         56
```
