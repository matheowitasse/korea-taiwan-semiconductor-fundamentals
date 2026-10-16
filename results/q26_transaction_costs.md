# Q26 — Transaction costs

Follows `docs/q26_transaction_costs_spec.md` (committed before this script was written).
Korea, 2023-01-31 → 2026-09-16. Half-spread from Corwin–Schultz, commission 5 bp
each way, sell tax 20 bp, Amihud linear impact, borrow fee on the short leg only.

Monthly turnover: long leg 18%, short leg 15%. Median half-spread among held names: long 32 bp, short 36 bp.

## Cost build-up (USD 10m fund, 3% borrow)

```
                     step  net_bp    t
                    gross  377.63 3.30
            + half spread  355.79 3.13
             + commission  352.56 3.10
               + sell tax  346.08 3.04
              + borrow 3%  321.08 2.82
+ market impact (USD 10m)  249.75 2.24
```

## Net performance by fund size and borrow fee

```
 fund_usd_m  borrow_%  cost_long_bp  cost_short_bp  net_long_short_bp     t  alpha_bp  alpha_t  net_long_leg_bp  long_leg_alpha_t
       1.00      1.00         20.58          28.89             330.62  2.91    233.88     3.07           176.00              2.49
       1.00      3.00         20.58          45.55             313.95  2.77    217.21     2.85           176.00              2.49
       1.00      5.00         20.58          62.22             297.28  2.62    200.54     2.63           176.00              2.49
      10.00      1.00         48.61          67.81             266.42  2.39    171.93     2.38           147.93              2.01
      10.00      3.00         48.61          84.48             249.75  2.24    155.26     2.15           147.93              2.01
      10.00      5.00         48.61         101.14             233.09  2.09    138.60     1.91           147.93              2.01
      50.00      1.00        173.16         240.79             -18.90 -0.17   -103.39    -1.60            23.20             -0.63
      50.00      3.00        173.16         257.46             -35.56 -0.33   -120.06    -1.86            23.20             -0.63
      50.00      5.00        173.16         274.13             -52.23 -0.48   -136.72    -2.12            23.20             -0.63
     200.00      1.00        640.25         889.48           -1088.83 -6.39  -1135.84    -7.67          -444.53             -6.57
     200.00      3.00        640.25         906.15           -1105.50 -6.49  -1152.51    -7.79          -444.53             -6.57
     200.00      5.00        640.25         922.82           -1122.17 -6.59  -1169.18    -7.90          -444.53             -6.57
```

## Break-even fund size (net monthly return crosses zero)

```
 borrow_%  long_short_breakeven_usd_m  long_leg_breakeven_usd_m
     1.00                       47.35                     57.44
     3.00                       45.01                     57.44
     5.00                       42.68                     57.44
```

Impact is linear in fund size in this model, so these are interpolations between the rows above, not a
separate estimate. Capacity in the real market is also limited by borrow availability: Q25 measured typical
net short positions of about 0.55% of market capitalisation in these names.
