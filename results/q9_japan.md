# Q9 Japan — do the Korean factors work in Japanese chip-sector stocks?

Follows `docs/q9_cross_market_preregistration.md`. One-sided (positive), Holm across the 4 Japanese tests.

Universe: 280 companies in 電気機器 + 精密機器; price files 278.

```
   factor  months  mean_bp     t     p  placebo_p  long_only_bp            window  p_holm  confirmed
  quality      16  143.827 1.356 0.088      0.020        67.710 2025-05 → 2026-09   0.175      False
    value      25  136.114 1.187 0.118      0.080        68.556 2024-08 → 2026-09   0.175      False
 earn_mom      13  212.864 1.860 0.031      0.012       148.248 2025-08 → 2026-09   0.094      False
composite      16  291.968 3.544 0.000      0.000       154.222 2025-05 → 2026-09   0.001       True
```

**Confirmed in Japan: composite**
