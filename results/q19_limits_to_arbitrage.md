# Q19 — Does the effect live where it cannot be shorted?

Follows `docs/q19_limits_to_arbitrage_preregistration.md` (committed before this script was written).
Mechanism test: it cannot change the Q8/Q9 finding, only whether the limits-to-arbitrage explanation holds.

Korean universe, 44 months, 10,169 stock-months. Proxy-shortable share of the universe: median 18.0% (min 16.2%, max 21.2%).

## T1 (primary) — rank × shortable interaction, month fixed effects, clustered by month

```
 coef_bp      t  p_one_sided  n_obs  b_rank_bp  with_size_controls  placebo_p  pass
 -46.761 -0.213        0.416  10169    422.438               False      0.447 False
-240.068 -0.889        0.187  10168    458.276                True        NaN   NaN
```

**T1 FAILS** (needs one-sided p < 0.05 and placebo p < 0.05 for b3 < 0).
Per the pre-registration: if the interaction loses significance once size is controlled, the size version is
the main answer.

## T2 — quintile spreads computed inside each group

```
              group  months  median_names  spread_bp     t
unshortable (proxy)      44       189.000    330.867 3.479
  shortable (proxy)      44        42.000    219.726 1.261
```

## T3 — among proxy-shortable names: ban months vs other months

```
                  group  months  median_names  spread_bp      t
  shortable, ban months      16        46.000     -4.530 -0.033
shortable, other months      28        41.000    347.872  1.418
```
