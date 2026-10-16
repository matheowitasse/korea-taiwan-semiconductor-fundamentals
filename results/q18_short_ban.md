# Q18 — The Korean short-selling ban, and a short leg you could actually trade

Follows `docs/q18_short_ban_and_implementable_preregistration.md` (committed before this script was written).
Implementation / mechanism work on the frozen finding: it changes no verdict of Q8/Q9.

Ban: 2023-11-06 → 2025-03-30. Taiwan had no ban (control).

## Part A — leg returns by sub-period

```
market        leg   period  months  mean_bp     t  alpha_bp  alpha_t  alpha_p_one_sided
 Korea   long_leg  pre-ban      10   213.70  2.05       NaN      NaN                NaN
 Korea   long_leg      ban      16    22.87  0.41     10.82     0.31               0.38
 Korea   long_leg post-ban      18   339.77  3.33    208.99     2.75               0.00
 Korea  short_leg  pre-ban      10   139.42  1.71       NaN      NaN                NaN
 Korea  short_leg      ban      16    90.61  1.58     99.69     2.38               0.01
 Korea  short_leg post-ban      18   286.28  4.07    199.36     3.57               0.00
 Korea long_short  pre-ban      10   353.12  1.93       NaN      NaN                NaN
 Korea long_short      ban      16   113.48  1.08    110.51     1.53               0.06
 Korea long_short post-ban      18   626.05  3.71    408.36     3.22               0.00
Taiwan   long_leg  pre-ban      10   192.62  4.19       NaN      NaN                NaN
Taiwan   long_leg      ban      16   -19.09 -0.59    -19.89    -0.58               0.72
Taiwan   long_leg post-ban      18   148.39  2.25    107.08     2.01               0.02
Taiwan  short_leg  pre-ban      10   185.93  8.66       NaN      NaN                NaN
Taiwan  short_leg      ban      16    35.05  2.11     38.64     1.76               0.04
Taiwan  short_leg post-ban      18   260.79  3.31    123.43     1.86               0.03
Taiwan long_short  pre-ban      10   378.55  7.95       NaN      NaN                NaN
Taiwan long_short      ban      16    15.96  0.40     18.75     0.39               0.35
Taiwan long_short post-ban      18   409.18  5.16    230.51     3.32               0.00
```

### Ban months vs all other months (Welch, two-sided)

```
market       leg  ban_mean_bp  other_mean_bp  difference_bp  welch_t  p_two_sided  n_ban  n_other
 Korea short_leg        90.61         233.83        -143.23    -1.75         0.09     16       28
 Korea  long_leg        22.87         294.74        -271.87    -2.43         0.02     16       28
Taiwan short_leg        35.05         234.05        -199.00    -3.01         0.00     16       28
Taiwan  long_leg       -19.09         164.19        -183.28    -2.99         0.00     16       28
```

## Part B — Korea: short leg restricted to shortable names (KOSPI 200 / KOSDAQ 150 proxy)

Bottom-quintile names shortable per month: median 4 of 47 (8 %); months skipped for fewer than 5 shortable names: 18.

```
                                  portfolio  months  mean_bp    t  alpha_bp  alpha_t  alpha_p_one_sided
          short leg, all names (all months)      44   181.75 3.75    143.96     4.20               0.00
      short leg, all names (allowed months)      28   233.83 3.82    176.12     3.87               0.00
 short leg, SHORTABLE only (allowed months)      10   159.53 0.98       NaN      NaN                NaN
                  long leg (allowed months)      28   294.74 3.67    203.59     3.86               0.00
long + implementable short (allowed months)      10   413.67 2.29       NaN      NaN                NaN
```

**Implementable short leg does NOT survive the pre-registered bar (alpha t > 2, same sign).**

Borrow cost reference: 1% a year ≈ 8 bp a month on the short leg.
