# Q13 (diagnostic) — winners or losers: where does the edge come from?

long leg = top quintile − universe average · short leg = universe average − bottom quintile.
`alpha` columns control for the local index, a momentum spread (and a size spread in Korea), HAC 3 lags.
Diagnostic on data already used: it changes no verdict, it locates the effect.

```
market        leg  months  mean_bp    t  share_of_spread_%  hit_%  alpha_bp  alpha_t  alpha_p_one_sided
 Korea   long_leg      44   195.88 2.85              51.87  61.36    137.10     2.86               0.00
 Korea  short_leg      44   181.75 3.75              48.13  77.27    143.96     4.20               0.00
 Korea long_short      44   377.63 3.30             100.00  75.00    281.07     3.60               0.00
Taiwan   long_leg      44    97.54 2.60              37.63  70.45     63.82     2.27               0.01
Taiwan  short_leg      44   161.69 3.57              62.37  77.27     98.02     3.59               0.00
Taiwan long_short      44   259.23 4.08             100.00  70.45    161.85     3.62               0.00
```

## Year by year (monthly averages, basis points)

```
market  year  long_leg_bp  short_leg_bp  universe_bp
 Korea  2023        181.7         109.4        215.2
 Korea  2024         25.7          74.2       -153.0
 Korea  2025        245.7         253.5        406.9
 Korea  2026        397.6         344.0        223.4
Taiwan  2023        161.9         149.9        300.5
Taiwan  2024          1.0          59.3         64.7
Taiwan  2025        184.8         144.0        238.0
Taiwan  2026         15.0         359.6        584.6
```
