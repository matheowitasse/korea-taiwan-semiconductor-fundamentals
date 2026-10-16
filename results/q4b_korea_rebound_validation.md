# Q4b — Korean supplier rebound after big US chip sell-offs: narrowed validation

Follows `docs/q4b_korea_supplier_rebound_validation_preregistration.md` (committed before this script).
Korea was chosen after Q4 showed it as the best of three markets → a pass is weaker evidence than a full validation.

## Decisive test (2025-07-01 → 2026-09-16, one-sided mean > 0)

```
id  n_nights  mean_bp  all_days_mean_bp  hit_rate_%      t  p_one_sided  placebo_p  pass
KR        34  -31.324            16.217      50.000 -0.520        0.697      0.798 False
```

**Statistical pass: NO** (needs p < 0.05 and placebo p < 0.05)

**Tradable after 30 bp round-trip cost: NO** (one-sided p of mean > 30 bp < 0.05)

## Discovery vs validation (reported, not decisive)

```
                 period  nights  mean_bp  median_bp  hit_rate_%  mean_excl_best_bp  p_mean_gt_cost  big_names_mean_bp
2023-01-01 → 2025-06-30      56   52.370     34.135      55.357             39.425           0.249              7.908
2025-07-01 → 2026-09-16      34  -31.324    -11.801      50.000            -51.033           0.842             34.469
```

## Every validation night

```
            soxx_pct  suppliers_bp  big_bp
2025-08-01      -2.0        -359.2  -243.0
2025-10-10      -2.0          58.3    44.8
2025-10-13      -6.5         574.0   226.7
2025-11-07      -2.5        -197.0   103.8
2025-11-14      -2.2         -75.7  -255.0
2025-11-21      -7.2         -36.0   -12.9
2025-12-15      -3.6          21.0   153.8
2025-12-18      -4.1        -143.5   186.5
2026-02-02      -2.7        -500.9  -400.1
2026-02-04      -2.9          91.7   261.8
2026-02-05      -3.4         -93.2  -136.2
2026-02-13      -3.3         157.2    -3.3
2026-02-27      -2.6         619.0   207.1
2026-03-13      -2.1         194.1   203.8
2026-03-23      -2.1        -142.9  -210.0
2026-03-27      -3.1         279.8   474.0
2026-03-31      -5.2        -164.3  -143.6
2026-05-08      -2.1         302.7   462.0
2026-05-19      -4.3        -493.5  -101.0
2026-05-28      -3.5        -518.4   138.3
2026-06-08      -6.6        -266.7   190.8
2026-06-10      -4.0          12.4  -344.9
2026-06-17      -5.2        -102.7   616.7
2026-07-02      -2.8        -808.4  -417.8
2026-07-03      -5.8         218.6   882.8
2026-07-15      -2.2         472.4  -160.2
2026-07-16      -3.5        -485.4  -337.3
2026-07-27      -3.2          76.9   -52.9
2026-07-28      -3.1        -642.8  -724.8
2026-07-30      -4.8         -88.5  -306.8
2026-08-03      -4.2          35.5  -399.8
2026-08-11      -3.0         602.4   289.0
2026-08-20      -3.1          22.8   514.2
2026-08-31      -2.4         315.4   465.2
```
