# Q1 holdout test — AI-era "sell the news"

Follows `docs/q1_holdout_preregistration.md` (committed before any post-2025-06 data was loaded). Run once.

- Holdout releases used: 28 (2025-07-11 → 2026-08-21)
- In-sample AI-era S2 tercile cut-offs: bottom ≤ -3.1 pp, top ≥ 7.0 pp

## Releases

```
    posted  type  semis_yoy_text      S2 tercile  NVDA_r5  SOXX_r5
2025-07-11 10day          12.800  -7.567  bottom    0.057    0.006
2025-07-21 20day          16.500  -2.367  middle    0.004   -0.024
2025-08-11 10day          12.000  -5.033  bottom   -0.009    0.019
2025-08-21 20day          29.500  15.733     top    0.039    0.037
2025-09-11 10day          28.400   9.067     top   -0.052    0.017
2025-09-22 20day          27.000   3.700  middle    0.016    0.008
2025-10-13 10day          47.000  18.700     top   -0.025    0.019
2025-10-22 20day          20.200 -13.933  bottom    0.110    0.057
2025-11-11 10day          17.700 -13.700  bottom   -0.044   -0.052
2025-11-21 20day          26.500  -1.800  middle   -0.023    0.106
2025-12-11 10day          45.900  24.433     top   -0.052   -0.087
2025-12-22 20day          41.800  11.767     top    0.023   -0.005
2026-01-12 10day          45.600   7.533     top    0.016    0.051
2026-01-22 20day          70.200  25.767     top    0.037    0.017
2026-02-12 10day         137.600  85.067     top   -0.027   -0.021
2026-02-23 20day         134.100  49.633     top   -0.074   -0.015
2026-03-11 10day         175.900  61.933     top   -0.021   -0.000
2026-03-23 20day         163.900  14.700     top   -0.055   -0.049
2026-04-13 10day         152.500  -5.467  bottom    0.084    0.080
2026-04-21 20day         182.500  18.400     top    0.072    0.083
2026-05-11 10day         149.800 -16.500  bottom    0.053   -0.030
2026-05-27 20day         202.100  40.500     top    0.041    0.035
2026-06-11 10day         205.800  27.667     top    0.016    0.080
2026-06-22 20day         188.400   2.500  middle   -0.089   -0.098
2026-07-13 10day         193.000  -5.767  bottom   -0.027   -0.074
2026-07-21 20day         180.600 -15.133  bottom   -0.053   -0.060
2026-08-11 10day         155.400 -31.933  bottom    0.013    0.039
2026-08-21 20day         198.800  22.467     top    0.044   -0.005
```

## Primary test: NVDA 5-day return on S2 (one-sided, slope < 0)

```
n = 28, slope per 1 pp of S2 = -0.0398% , HAC t = -1.40, placebo p (one-sided) = 0.149
mean NVDA r5: top tercile -0.13% (n=15), bottom tercile 2.03% (n=9)
```

1. HAC t < -1.7: **FAIL**
2. placebo p < 0.05: **FAIL**
3. top-tercile mean < bottom-tercile mean: **PASS**

**Result: NOT CONFIRMED**

## Alongside (not decisive): SOXX and MU

```
asset  n  slope_pct_per_pp      t  placebo_p_one_sided
 SOXX 28            -0.003 -0.081                0.478
   MU 28             0.029  0.459                0.653
```
