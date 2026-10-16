# Q14 — market-hedged implementation

Follows `docs/q14_hedged_spec.md` (committed before running). Long top quintile, short the index
(H1: beta from the previous 24 months only; H2: 1:1). Costs: 0.30% per unit of stock turnover, 0.02%/month futures.
Implementation study on data already used; it cannot change the frozen finding.

## Decisive: Korea

```
market            rule  months  mean_bp    t  p_one_sided  ann_%  vol_%  max_dd_%  hit_%  alpha_vs_size_mom_bp  alpha_t  p_holm  pass
 Korea H1_rolling_beta      20    17.73 0.13         0.45  -3.43  34.14    -31.77  40.00                 44.77     0.29    0.45 False
 Korea         H2_full      44   101.21 0.96         0.17   8.79  27.31    -34.48  50.00                 88.45     0.83    0.34 False
```

**Pass: **

## Reported only (Taiwan, and the unhedged portfolios)

```
market               rule  months  mean_bp    t    p  ann_%  vol_%  p_one_sided  max_dd_%  hit_%  alpha_vs_size_mom_bp  alpha_t
 Korea unhedged long-only      44   385.75 2.07 0.04  45.67  41.92          NaN       NaN    NaN                   NaN      NaN
Taiwan    H1_rolling_beta      20    89.84 0.93  NaN   8.47  23.37         0.18    -20.65  55.00                -61.18    -0.89
Taiwan            H2_full      44    80.46 1.14  NaN   8.20  18.83         0.13    -24.46  54.55                 -4.31    -0.07
Taiwan unhedged long-only      44   352.94 2.92 0.00  45.12  30.86          NaN       NaN    NaN                   NaN      NaN
```

## Year by year

```
market            rule  year  return_%
 Korea H1_rolling_beta  2025     -5.13
 Korea H1_rolling_beta  2026     -0.55
 Korea         H2_full  2023     51.09
 Korea         H2_full  2024    -19.97
 Korea         H2_full  2025      9.48
 Korea         H2_full  2026      2.89
Taiwan H1_rolling_beta  2025     12.25
Taiwan H1_rolling_beta  2026      2.00
Taiwan         H2_full  2023     42.92
Taiwan         H2_full  2024    -20.93
Taiwan         H2_full  2025     16.71
Taiwan         H2_full  2026      1.21
```
