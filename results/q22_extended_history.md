# Q22 — Does the effect exist before the AI era? (Korea, extended history)

Follows `docs/q22_extended_history_preregistration.md` (committed before this script was written).
One-sided (positive); the decisive test is E1.

Universe: 285 codes (282 with prices). DART's multi-account API returns only annual figures for
2015, so trailing-four-quarter signals begin later: the first month with at least 25 signals is
**2016-11-30**, which sets the start of the decisive window (a data constraint, not a chosen window).

## E1 and E3

```
                test   start     end  months  median_names  spread_bp    t  p_one_sided  placebo_p
E1 pre-AI (decisive) 2016-11 2022-12      74        188.00     158.11 2.69         0.00       0.00
     E3 full history 2016-11 2026-08     118        207.00     220.37 4.06         0.00       0.00
```

**E1 PASSES** (needs t > 2 and one-sided placebo p < 0.05).

## E2 — alpha after controls

Market caps start at the 2022-06 KRX snapshot, so the size control is unavailable before 2023 and these
regressions use the index and momentum controls only.

```
window  months  alpha_bp  alpha_t  beta_index  beta_momentum
pre-AI      74    120.52     2.73        0.32           0.59
  full     118    168.85     4.26        0.24           0.41
```

## Sub-periods (descriptive, no significance tests)

```
               period  months  spread_bp    t
            2017–2019      36     195.62 2.28
2018–2019 memory bust      24     146.24 1.66
            2020–2022      36     119.24 1.40
    2023–2026 (known)      44     325.08 3.30
```
