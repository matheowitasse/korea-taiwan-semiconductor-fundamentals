# Q6 — Broad edge sweep (14 tests, one Holm family)

Follows `docs/q6_edge_sweep_preregistration.md` (committed before this script was written).

Discovery 2023-01-01 → 2025-06-30; validation 2025-07-01 → 2026-09-16. Two-sided. size_bp = top − bottom signal quintile (A/B/H), mean spread (C), event − other (E/F). Costs: 0.30% round trip (C: ~0.60% per period).

## Discovery (decisive)

```
id                                         test   n    effect                    effect_unit      t     p  placebo_p  size_bp  p_holm  pass
A1              KR_BIG cc → SOXX oc (same date) 585  -218.988                bp per 1.0 of x -0.451 0.652      0.659   -9.005   1.000 False
A2                KR_BIG cc → MU oc (same date) 585   177.526                bp per 1.0 of x  0.314 0.754      0.774    9.640   1.000 False
A3              TW_BIG cc → SOXX oc (same date) 567  -810.492                bp per 1.0 of x -1.307 0.191      0.188  -34.267   1.000 False
A4              JP_BIG cc → SOXX oc (same date) 587  -544.968                bp per 1.0 of x -1.193 0.233      0.197  -24.249   1.000 False
B1                          KR_BIG past 5d → h5 607  -732.270                bp per 1.0 of x -1.157 0.247      0.420  -69.865   1.000 False
B2                          KR_SUP past 5d → h5 607 -1000.710                bp per 1.0 of x -1.426 0.154      0.197 -206.017   1.000 False
B3                          TW_SUP past 5d → h5 593  -541.005                bp per 1.0 of x -0.801 0.423      0.398  -28.087   1.000 False
B4                          JP_SUP past 5d → h5 610  -252.740                bp per 1.0 of x -0.318 0.751      0.856   27.149   1.000 False
C1  39 names weekly reversal (losers − winners) 126    19.285 bp losers − winners per period  0.684 0.495      0.404   19.285   1.000 False
C2 39 names monthly reversal (losers − winners)  30  -196.552 bp losers − winners per period -1.523 0.139      0.057 -196.552   1.000 False
E1         KR_BIG oc on KOSPI200 options expiry  30    -6.577               bp event − other -0.251 0.803      0.803   -6.577   1.000 False
E2                    KOSPI cc on turn of month 120    -8.296               bp event − other -0.583 0.561      0.484   -8.296   1.000 False
F1 KR_BIG h5 after 5-day foreign selling streak  12  -113.683               bp event − other -0.787 0.447      0.344 -113.683   1.000 False
H1            MU/NVDA earnings: KR_BIG gap → oc  20  -817.578                bp per 1.0 of x -0.910 0.375      0.432  -50.538   1.000 False
```

**No test passed discovery → validation not run (as pre-registered). No edge found.**
