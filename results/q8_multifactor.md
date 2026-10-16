# Q8 — multi-factor cross-section in Korean chip stocks

Follows `docs/q8_multifactor_preregistration.md` (committed before this script was written).

Universe B ∪ C: 262 companies (list A: 118). Month-ends with prices: 141 (2015-01 → 2026-09).
Statistic: mean monthly long-short (top − bottom quintile) return in basis points, Newey–West t (3 lags).

## Discovery 2023-01 → 2025-06 (decisive)

```
   factor  months  mean_bp      t     p  placebo_p  long_only_bp  long_only_t  avg_stocks  p_holm  pass
composite      30  147.226  2.692 0.007      0.020        78.128        3.365     227.667   0.043  True
    value      30  121.493  2.153 0.031      0.036        56.739        1.824     236.367   0.094  True
  quality      30  189.751  2.366 0.018      0.004        86.371        1.884     225.300   0.072  True
 earn_mom      30  156.428  2.562 0.010      0.036        85.466        2.317     204.800   0.052  True
price_mom      30 -105.938 -1.199 0.231      0.092       -48.888       -0.989     224.867   0.461 False
     size      30  -53.008 -0.841 0.400      0.368       -26.185       -0.465     238.133   0.461 False
```

Survivors: composite, value, quality, earn_mom

## Validation 2025-07 → today (survivors only)

```
   factor  months  mean_bp     t     p  placebo_p  long_only_bp  long_only_t  avg_stocks  p_holm  edge
composite      14  426.560 2.034 0.021      0.002       148.013        1.201     244.571   0.042  True
    value      14  198.145 1.385 0.083      0.070       -15.738       -0.164     249.929   0.083 False
  quality      14  600.463 4.434 0.000      0.000       238.717        3.132     242.500   0.000  True
 earn_mom      14  604.379 3.340 0.000      0.000       330.889        2.435     221.286   0.001  True
```

**Edges confirmed: composite, quality, earn_mom**

## Robustness (not decisive)

```
   factor               list  months  mean_bp      t     p
composite                  A      30   94.951  1.262 0.207
    value                  A      30  105.316  1.157 0.247
  quality                  A      30  108.014  1.184 0.236
 earn_mom                  A      30  158.349  1.849 0.065
price_mom                  A      30  -98.389 -0.627 0.531
     size                  A      30  -29.176 -0.431 0.666
composite B∪C value-weighted      30   66.705  0.552 0.581
    value B∪C value-weighted      30  194.594  1.326 0.185
  quality B∪C value-weighted      30  189.118  1.130 0.259
 earn_mom B∪C value-weighted      30  -60.884 -0.502 0.615
price_mom B∪C value-weighted      30  206.589  1.139 0.255
     size B∪C value-weighted      30 -150.852 -1.563 0.118
composite    2023-01→2024-01      13  211.390  2.272 0.023
    value    2023-01→2024-01      13   23.543  0.310 0.756
  quality    2023-01→2024-01      13  301.834  2.419 0.016
 earn_mom    2023-01→2024-01      13  134.407  1.895 0.058
price_mom    2023-01→2024-01      13   62.232  0.467 0.641
     size    2023-01→2024-01      13  -55.011 -0.754 0.451
composite    2024-02→2025-06      17   98.160  1.596 0.111
    value    2024-02→2025-06      17  196.396  3.286 0.001
  quality    2024-02→2025-06      17  104.040  1.323 0.186
 earn_mom    2024-02→2025-06      17  173.268  1.881 0.060
price_mom    2024-02→2025-06      17 -234.538 -2.993 0.003
     size    2024-02→2025-06      17  -51.477 -0.494 0.621
```
