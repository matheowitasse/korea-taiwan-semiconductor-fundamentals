# Q7b — Post-earnings drift in the recent Korean market + did the market change?

Follows `docs/q7b_pead_recent_market_preregistration.md` (committed before this script was written).
**Follow-up chosen after the Q7 near-miss** → a pass is weaker evidence than a pass of the original Q7 sequence.

Recent period (part 1): D0 2025-07-01 → 2026-06-16, list A, 517 events, 9 event months.

## Part 1 — T1 on the recent market (decisive, one-sided: drift > 0)

```
test   n  months  coef_pct      t     p  placebo_p  pass
  T1 517       9    -4.427 -0.415 0.661      0.715 False
```

**T1 FAILED** (needs one-sided p < 0.05 and one-sided placebo p < 0.05)

Reported, not decisive (one-sided, same period):

```
           what test    n  months  coef_pct      t     p  placebo_p
      T1 list B   T1  543       9    -5.244 -0.446 0.672      0.741
      T1 list C   T1 1108      10     2.969  0.379 0.353      0.263
     T1 list BC   T1 1129      10     2.550  0.313 0.377      0.290
T3 (SUE) list A   T3  439       9    31.337  5.777 0.000      0.000
```

T1 coefficient: discovery 2023-01 → 2025-06 = 5.60 %, recent = -4.43 %, difference = -10.02 pp

## Strategy illustration (not decisive): long top EAR quintile, 60 days, vs market

```
    period  positions  mean_car60_%  after_0.30%_cost_%  hit_rate_%  worst_%  from_delisted_%
 discovery        247        3.0853              2.7853     41.7004 -63.4475           0.0000
validation        104        8.3285              8.0285     50.9615 -82.5408           0.0000
```

## Part 2 — did the market change? (descriptive only; break date fixed at 2025-07-01)

Before = 2023-01-01 → 2025-06-30, after = 2025-07-01 → 2026-09-16. p-values are descriptive, not a break test.

```
period                           before  after  ratio_after/before
measure                                                           
KOSDAQ return, annualised %        5.99   3.72                0.62
KOSDAQ volatility, annualised %   23.75  44.22                1.86
KOSPI return, annualised %        14.08  93.82                6.66
KOSPI volatility, annualised %    18.34  49.67                2.71
```

```
                                            measure  before   after  ratio_after/before  n_before  n_after                   test  p_descriptive
         list-A stock vol_ann_% (per-stock medians)  60.241  86.847               1.442       112      112 Mann-Whitney (medians)          0.000
  list-A stock turnover_daily_% (per-stock medians)   0.612   0.799               1.305       112      112 Mann-Whitney (medians)          0.037
list-A stock retail_net_share_% (per-stock medians)   9.594  10.859               1.132       112      112 Mann-Whitney (medians)          0.000
        KOSPI foreign net buying per month, trn KRW   0.026 -11.516            -438.621        30       14          Welch (means)          0.043
                          list-A |EAR| %, per event   2.966   3.583               1.208      1227      517 Mann-Whitney (medians)          0.000
```

```
                         measure  before  after  ratio_after/before
list-A EAR cross-sectional std %   6.081  9.262               1.523
```

Earlier findings (cited, not re-tested): Q2 SK Hynix overnight gap beta 0.54 → 0.77 (break 2023); Q4b 2025-07+ US sell-off nights far more volatile; Q5 KOSPI foreign net buying 2023 +11.3, 2024 +1.3, 2025 −4.7, 2026 (to 09-16) −179 trn KRW.
