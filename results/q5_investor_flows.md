# Q5 — Do investor flows predict Korean chip stock returns?

Follows `docs/q5_investor_flows_preregistration.md` (committed before this script was written).

Discovery 2023-01-01 → 2025-06-30; validation 2025-07-01 → 2026-09-16. Signal = 60-day z-score of day-D net buying (KRX); return starts at the open of D+1. Slope in bp of return per 1 z. Two-sided. Costs ignored (0.30% round trip for reference).

Data coverage 2023-01 → 2026-09 (% of KOSPI trading days with a value):

```
BIG2_foreign        99.9
BIG2_individual     99.9
BIG2_h1             99.8
BIG2_h5             99.2
SUP_foreign         99.9
SUP_individual      99.9
SUP_h1              99.8
SUP_h5              99.2
KOSPI_foreign      100.0
KOSPI_h1            99.7
KOSPI_h5            99.0
```

## Discovery (decisive)

```
id            signal return  sell-off days only   n  slope_bp_per_z      t     p  placebo_p  top_q_bp  bottom_q_bp  top_minus_bottom_bp  p_holm  pass
T1    BIG2 foreign z     h1               False 607          -7.694 -1.178 0.239      0.239   -29.971       -3.646              -26.325   1.000 False
T2    BIG2 foreign z     h5               False 607          -6.134 -0.263 0.792      0.844    13.230       45.563              -32.333   1.000 False
T3     SUP foreign z     h1               False 607           1.876  0.114 0.909      0.923    13.902       -6.884               20.786   1.000 False
T4     SUP foreign z     h5               False 607         -51.551 -1.231 0.218      0.256    75.050       44.787               30.263   1.000 False
T5 BIG2 individual z     h5               False 607           2.928  0.138 0.890      0.930    38.054       12.379               25.675   1.000 False
T6  SUP individual z     h5               False 607          13.315  0.320 0.749      0.748   140.494       45.651               94.844   1.000 False
T7    BIG2 foreign z     h5                True  56          52.565  0.716 0.477      0.453    57.419     -131.833              189.252   1.000 False
T8   KOSPI foreign z     h5               False 605          -4.734 -0.519 0.604      0.605    21.908       22.847               -0.939   1.000 False
```

**No test passed discovery → validation not run (as pre-registered). No edge found.**
