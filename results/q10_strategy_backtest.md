# Q10 — long-only 20-stock strategy backtest

Rules fixed in `docs/q10_strategy_spec.md` before running. Long only, equal weight, monthly rebalance,
net of costs (Korea 0.30%, Japan 0.10%, Taiwan 0.60% per unit of turnover). Signal: quality + earnings/revenue
momentum (value dropped: it failed in Korea and had the wrong sign in Taiwan).

**This reuses the data that produced the signals — it is a cost-and-implementation study, not new evidence.**

## Strategy vs local index

```
market  months  ann_return_%  ann_vol_%  sharpe  max_drawdown_%  hit_rate_%  best_%  worst_%  bench_ann_%  excess_ann_%  tracking_error_%  avg_turnover  avg_holdings
 Korea      44         49.23      47.19    1.04          -37.99       59.09   50.07   -26.62        32.03         17.19             30.53          0.22         20.00
 Japan      17        113.96      40.01    2.85          -15.26       70.59   28.13   -15.26        49.84         64.12             17.96          0.27         20.00
Taiwan      44         45.36      38.04    1.19          -32.55       59.09   39.72   -18.16        34.98         10.38             26.65          0.49         20.00
```

## Year by year (net of costs)

```
market  year  months  strategy_%  index_%  excess_%
 Korea  2023      12       69.95     2.97     66.98
 Korea  2024      12      -17.27     0.81    -18.09
 Korea  2025      12      114.46   107.53      6.93
 Korea  2026       8       43.92    28.59     15.33
 Japan  2025       9       76.94    47.93     29.01
 Japan  2026       8       66.02    19.88     46.14
Taiwan  2023      12       80.54    17.19     63.35
Taiwan  2024      12       -7.62    31.50    -39.12
Taiwan  2025      12       51.28    36.29     14.98
Taiwan  2026       8       56.20    42.99     13.21
```

## Sensitivity (reported, not used to choose)

```
market                        variant  months  ann_return_%  ann_vol_%  sharpe  max_drawdown_%  hit_rate_%  best_%  worst_%
 Korea                         top 10      44         45.95      46.85    0.98          -37.97       59.09   47.02   -28.40
 Korea                         top 20      44         49.23      47.19    1.04          -37.99       59.09   50.07   -26.62
 Korea                         top 30      44         46.31      42.68    1.09          -38.06       56.82   41.58   -23.96
 Korea            quarterly rebalance      44         36.11      45.79    0.79          -38.15       56.82   47.27   -27.46
 Korea best months replaced by median      44         34.37      40.33    0.85          -37.99       59.09   30.08   -26.62
 Japan                         top 10      17        158.42      44.26    3.58          -15.75       82.35   34.65   -15.75
 Japan                         top 20      17        113.96      40.01    2.85          -15.26       70.59   28.13   -15.26
 Japan                         top 30      17        107.22      37.60    2.85          -15.38       76.47   28.62   -15.38
 Japan            quarterly rebalance      17         94.15      39.13    2.41          -18.11       70.59   23.05   -18.11
 Japan best months replaced by median      17         90.99      35.46    2.57          -15.26       70.59   22.45   -15.26
Taiwan                         top 10      44         38.55      46.97    0.82          -38.85       50.00   54.26   -18.81
Taiwan                         top 20      44         45.36      38.04    1.19          -32.55       59.09   39.72   -18.16
Taiwan                         top 30      44         50.58      34.94    1.45          -24.64       61.36   31.66   -18.80
Taiwan            quarterly rebalance      44         56.27      36.15    1.56          -22.86       63.64   39.60   -16.32
Taiwan best months replaced by median      44         33.43      32.81    1.02          -32.55       59.09   28.59   -18.16
```
