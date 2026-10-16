# Q27 — Taiwan before the AI era

Follows `docs/q27_taiwan_pre_ai_preregistration.md` (committed before any pre-2022-06 Taiwanese data was
downloaded). One decisive test: revenue momentum over 2016-01 → 2022-12, one-sided positive.

```
                             window           factor  months  mean_bp      t  p_one_sided  placebo_p  long_only_bp  median_names              span
DECISIVE 2016-01 → 2022-12 (unseen) revenue momentum      83  187.037  4.937        0.000      0.000        90.653           367 2016-02 → 2022-12
DECISIVE 2016-01 → 2022-12 (unseen)            value      84    0.730  0.026        0.490      0.752       -11.270           164 2016-01 → 2022-12
     already seen 2023-01 → 2026-08 revenue momentum      44  259.314  4.084        0.000      0.000        97.969           410 2023-01 → 2026-08
     already seen 2023-01 → 2026-08            value      44 -146.173 -2.088        0.982      0.998       -58.621           187 2023-01 → 2026-08
                full sample (mixed) revenue momentum     127  212.078  6.301        0.000      0.000        93.188           379 2016-02 → 2026-08
                full sample (mixed)            value     128  -49.768 -1.516        0.935      0.980       -27.547           168 2016-01 → 2026-08
```

**DECISIVE TEST: PASSES** (mean 187 bp/month, t 4.94, placebo p 0.000, 83 months)

## Risk adjustment on the decisive window (index + momentum spread, HAC 3 lags)

```
months               83.000
alpha_bp            182.569
alpha_t               6.603
alpha_p_one_sided     0.000
beta_index            0.152
beta_momentum         0.372
r2                    0.358
```
