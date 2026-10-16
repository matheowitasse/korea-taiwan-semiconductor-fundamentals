# Q10 risk adjustment — is the strategy just market, size and momentum?

Monthly strategy return regressed on the local index, a size spread (small − big) and a 12-1 momentum spread,
both built inside the same universe. HAC standard errors (3 lags). `alpha` is the unexplained part.

```
market  months  alpha_bp_month  alpha_t  alpha_p    r2  beta_index  t_index  beta_momentum  t_momentum  beta_size_small_minus_big  t_size_small_minus_big
 Korea      44         153.869    1.365    0.172 0.628       0.622    3.295          0.064       0.225                     -0.463                  -2.320
 Japan      17         302.856    3.816    0.000 0.900       0.964    9.662          0.430       6.704                        NaN                     NaN
Taiwan      44          14.851    0.223    0.824 0.638       0.943    3.922          0.606       2.937                        NaN                     NaN
```
