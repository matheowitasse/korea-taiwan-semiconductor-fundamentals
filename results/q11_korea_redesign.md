# Q11 — Korea implementation redesign

Follows `docs/q11_korea_redesign_spec.md` (committed before running). Decisive number: alpha after controlling
for the KOSPI, a size spread and a momentum spread (HAC 3 lags), one-sided positive, Holm over the two designs.
Implementation study on data already used — not new evidence.

## Decisive: the two new designs

```
             design  months  alpha_bp  alpha_t  alpha_p_one_sided  beta_index  beta_size  beta_momentum   r2  ann_%  vol_%  sharpe  max_dd_%  tracking_error_%  hit_%  avg_holdings  turnover  p_holm  pass
       D1_avoidance      44     71.92     0.77               0.22        0.57      -0.18           0.09 0.54  29.55  37.26    0.79    -35.54             27.01  63.64        115.00      0.11    0.23 False
D2_momentum_neutral      44    147.78     1.21               0.11        0.60      -0.36          -0.08 0.58  46.51  38.60    1.20    -40.48             26.44  65.91         21.00      0.35    0.23 False
```

**Pass: neither design**

## Reference portfolios (not decisive)

```
               design  months  alpha_bp  alpha_t  alpha_p_one_sided  beta_index  beta_size  beta_momentum   r2  ann_%  vol_%  sharpe  max_dd_%  tracking_error_%  hit_%  avg_holdings  turnover
                top20      44    153.87     1.37               0.09        0.62      -0.46           0.06 0.63  49.23  47.19    1.04    -37.99             30.53  59.09         20.00      0.22
universe_equal_weight      44      2.32     0.03               0.49        0.56      -0.07           0.12 0.48  17.00  35.63    0.48    -38.45             28.05  54.55        190.90      0.04
```

## Year by year

```
               design  year  strategy_%  index_%
         D1_avoidance  2023       34.99     2.97
         D1_avoidance  2024      -16.12     0.81
         D1_avoidance  2025       94.07   107.53
         D1_avoidance  2026       17.60    28.59
  D2_momentum_neutral  2023       45.09     2.97
  D2_momentum_neutral  2024      -20.90     0.81
  D2_momentum_neutral  2025      123.99   107.53
  D2_momentum_neutral  2026       57.79    28.59
                top20  2023       69.95     2.97
                top20  2024      -17.27     0.81
                top20  2025      114.46   107.53
                top20  2026       43.92    28.59
universe_equal_weight  2023       25.91     2.97
universe_equal_weight  2024      -20.09     0.81
universe_equal_weight  2025       68.78   107.53
universe_equal_weight  2026        4.72    28.59
```
