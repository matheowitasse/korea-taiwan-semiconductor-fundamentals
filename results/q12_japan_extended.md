# Q12 — Japan with five years of history

Follows `docs/q12_japan_extended_preregistration.md` (committed before the data was downloaded).

Financials 2021-09-21 → 2026-09-18, 276 companies, median 23 statements each.

## All windows (only the first is decisive)

```
                               window    factor  months  mean_bp     t  p_one_sided  placebo_p  long_only_bp              span
  decisive (unseen) 2021-10 → 2024-06 composite      21  162.032 1.802        0.036      0.008        88.066 2022-10 → 2024-06
  decisive (unseen) 2021-10 → 2024-06   quality      21  104.484 1.156        0.124      0.018        27.770 2022-10 → 2024-06
  decisive (unseen) 2021-10 → 2024-06  earn_mom      18  104.982 1.206        0.114      0.050       100.783 2023-01 → 2024-06
  decisive (unseen) 2021-10 → 2024-06     value      29  263.422 3.925        0.000      0.000       120.962 2022-02 → 2024-06
already seen in Q9: 2024-07 → 2026-06 composite      24  199.747 2.647        0.004      0.002        93.638 2024-07 → 2026-06
already seen in Q9: 2024-07 → 2026-06   quality      24   81.284 0.893        0.186      0.074        28.951 2024-07 → 2026-06
already seen in Q9: 2024-07 → 2026-06  earn_mom      24   98.333 1.065        0.143      0.048        62.133 2024-07 → 2026-06
already seen in Q9: 2024-07 → 2026-06     value      24  130.636 1.119        0.132      0.086        57.394 2024-07 → 2026-06
                  full sample (mixed) composite      47  184.151 3.095        0.001      0.000        95.506 2022-10 → 2026-09
                  full sample (mixed)   quality      47   82.966 1.270        0.102      0.016        25.257 2022-10 → 2026-09
                  full sample (mixed)  earn_mom      44  104.584 1.664        0.048      0.010        82.808 2023-01 → 2026-09
                  full sample (mixed)     value      55  208.453 3.134        0.001      0.000        95.919 2022-02 → 2026-09
```

**Decisive test — composite, unseen window: NOT CONFIRMED** (mean 162 bp/month, t 1.80, placebo p 0.008, 21 months)

## Risk adjustment on the unseen window (index + momentum spread, HAC 3 lags)

```
months               21.000
alpha_bp            150.171
alpha_t               1.551
alpha_p_one_sided     0.060
beta_index            0.132
beta_momentum        -0.135
r2                    0.026
```
