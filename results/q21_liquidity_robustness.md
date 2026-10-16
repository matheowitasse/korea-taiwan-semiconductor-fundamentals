# Q21 — Is the effect just illiquidity?

Follows `docs/q21_liquidity_robustness_spec.md` (committed before this script was written).
Robustness on data already used: it cannot change the Q8/Q9 verdicts, only which reading they support.

## R1 — long–short spread inside Amihud illiquidity terciles

```
market                  group  months  median_names  spread_bp    t
 Korea            most liquid      44         76.00     310.02 2.24
 Korea                 middle      44         78.00     408.84 2.96
 Korea           least liquid      44         78.00     302.86 2.40
 Korea all (Amihud available)      44        230.00     362.39 3.11
```

## R2 — alpha before and after adding an illiquidity factor

```
market             controls  alpha_bp  alpha_t  alpha_p_one_sided
 Korea    existing controls    281.06     3.60               0.00
 Korea + illiquidity factor    252.23     3.69               0.00
```

## R3–R5 — size and price screens (Korea)

```
market                            group  months  median_names  spread_bp    t
 Korea excl. smallest 20% by market cap      44        186.00     385.07 3.08
 Korea          excl. price < KRW 1,000      44        226.00     364.81 3.26
 Korea           value-weighted (known)      44           NaN     517.00 1.91
```

Taiwan is not covered by R1/R2: the cached Taiwanese price files hold closing prices only, so Amihud cannot be
computed without re-downloading volume series (noted in the spec before running).

## Reading

- **Korea: survives** the pre-specified reading (most-liquid tercile t = 2.24; alpha t with illiquidity factor = 3.69).
