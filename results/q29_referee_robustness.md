# Q29 — standard-methods robustness (referee checks)

Follows `docs/q29_referee_robustness_preregistration.md`, committed before this script. All data here had been
examined before; these are new estimators on known data, reported as run.

## Decisive tests (one-sided, bar t > 2; Holm across the four)

```
test     t  p_one_sided  p_holm  pass (t > 2)
  F1 4.082        0.000   0.000          True
  F2 6.423        0.000   0.000          True
  A1 4.660        0.000   0.000          True
  U1 4.008        0.000   0.000          True
```

## Fama–MacBeth (F1–F4): monthly cross-sectional OLS, Newey–West on the coefficient series

Coefficients are bp of next-month return per one cross-sectional standard deviation of the regressor.

```
                       test regressor  months  coef_bp_per_sd     t  median_names  avg_r2
                   F1 Korea    signal     118           73.44  4.08        206.50    0.05
                   F1 Korea  mom_12_1     118          -19.55 -0.73        206.50    0.05
                   F1 Korea    rev_1m     118          -22.74 -0.80        206.50    0.05
                  F2 Taiwan    signal     127           79.75  6.42        366.00    0.04
                  F2 Taiwan  mom_12_1     127          -13.79 -0.64        366.00    0.04
                  F2 Taiwan    rev_1m     127            2.60  0.12        366.00    0.04
       F3 Korea + size, B/M    signal      50           98.72  3.17        231.50    0.07
       F3 Korea + size, B/M  mom_12_1      50          -23.76 -0.56        231.50    0.07
       F3 Korea + size, B/M    rev_1m      50            4.19  0.06        231.50    0.07
       F3 Korea + size, B/M  log_size      50           44.77  1.23        231.50    0.07
       F3 Korea + size, B/M        bm      50          124.07  2.61        231.50    0.07
F4 Taiwan + B/M (TWSE only)        bm      84           -9.00 -0.33        171.50    0.08
F4 Taiwan + B/M (TWSE only)  mom_12_1      92           -5.89 -0.17        171.50    0.08
F4 Taiwan + B/M (TWSE only)    rev_1m      92           51.87  1.59        171.50    0.08
F4 Taiwan + B/M (TWSE only)    signal      92           62.84  3.34        171.50    0.08
```

## Extended factor alpha (A1), Korea

Market-wide factors built from all listed Korean companies **excluding the chip universe** (median 1640 companies with asset growth per month).

```
                                       test  months  alpha_bp  alpha_t   r2  beta_index  t_index  beta_momentum  t_momentum  beta_rmw_ex_chip  t_rmw_ex_chip  beta_cma_ex_chip  t_cma_ex_chip  beta_umd_ex_chip  t_umd_ex_chip
A0 index + in-universe momentum (reference)     117    168.30     4.21 0.45        0.24     3.00           0.41        4.48               NaN            NaN               NaN            NaN               NaN            NaN
   A1 + market-wide RMW, CMA, UMD (ex chip)     113    178.70     4.66 0.52        0.24     3.04           0.39        3.63              0.35           2.48             -0.31          -1.48             -0.17          -1.22
```

Market-wide factor premia over the same window:

```
     factor  months  mean_bp     t    p
rmw_ex_chip     117   -12.12 -0.42 0.67
cma_ex_chip     113    47.80  2.35 0.02
umd_ex_chip     117   -35.98 -0.96 0.34
```

## Rule-only universe (U1), Korea

Universe defined only by DART industry codes 261, 29271, 262: 281 of 285 codes. Dropped (added by name, not by rule): 005930, 036930, 095340, 240810. Leeno (058470) qualifies by rule (code 2629) and stays.

```
            universe  months  mean_bp    t    p
paper (rule + named)     118   220.37 4.06 0.00
           rule only     118   218.27 4.01 0.00
```

## Skip a month (S1)

```
market  months  mean_bp    t    p
 Korea     117   182.40 3.57 0.00
Taiwan     126   207.32 4.93 0.00
```

## Performance (D1)

```
market  months  ann_mean_%  ann_vol_%  sharpe  skew  max_drawdown_%  positive_months_%
 Korea     118       26.44      21.44    1.23  0.08          -25.50              63.56
Taiwan     127       25.45      13.01    1.96  0.53          -11.49              68.50
```

Calendar years (mean monthly spread, bp):

```
 date  Korea_bp  Taiwan_bp  Korea_months  Taiwan_months
 2016       182        174             2             11
 2017       294        287            12             12
 2018        34         96            12             12
 2019       258        178            12             12
 2020       255        266            12             12
 2021       191        224            12             12
 2022       -88         82            12             12
 2023       309        312            12             12
 2024        34         60            12             12
 2025       476        329            12             12
 2026       559        375             8              8
```

## Summary statistics (D2)

```
                               variable  names_per_month_median  min  max    p10  median      p90
Korea quality (TTM op. profit / assets)                 205.000  162  273 -0.115   0.024    0.136
          Korea earnings momentum (SUE)                 185.000    0  254 -1.548  -0.011    1.573
                Korea next-month return                 224.000  178  282 -0.155   0.000    0.186
Korea market cap (KRW bn, from 2022-07)                 248.000  221  261 33.920 171.510 1199.393
   Taiwan revenue growth (YoY, z-score)                 378.500    0  416 -0.603  -0.099    0.547
               Taiwan next-month return                 375.000  342  416 -0.116   0.003    0.172
```

Median monthly cross-sectional correlation between the quality and SUE z-scores: 0.20.

## Coverage note found while building D2 (descriptive split, not a registered test)

SUE needs eight prior quarters and DART data begin in 2015, so **no Korean stock has an earnings-momentum score
before 2018-08**. In the first 21 pre-AI months (2016-11 → 2018-07) the fundamentals-improvement signal is quality
alone. This was true of Q22 as well and was not recorded there. Splitting the Korean series at that point:

```
segment                         window              months   mean_bp     t
quality only (no SUE yet)       2016-11 .. 2018-07      21       123   0.91
both components, pre-AI         2018-08 .. 2022-12      53       172   2.69
both components, all            2018-08 .. 2026-08      97       241   4.08
```

The combined signal clears the pre-AI bar on the 53 months where it is fully defined; the quality-only stretch is
positive but not significant on its own. The paper states this in the pre-AI section.
