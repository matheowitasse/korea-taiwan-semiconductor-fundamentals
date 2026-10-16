# Q9 Taiwan — value and monthly-revenue momentum in chip-sector stocks

Follows `docs/q9_cross_market_preregistration.md`. One-sided (positive), Holm across the 3 Taiwanese tests.

Universe: 416 companies (sector codes 24 semiconductors + 28 electronic components); price files 416. Value uses the TWSE valuation file, so TPEx names have no value score.

```
   factor  months  mean_bp      t     p  placebo_p  long_only_bp            window  p_holm  confirmed
    value      44 -146.173 -2.088 0.982      0.998       -58.621 2023-01 → 2026-08   0.982      False
  rev_mom      44  259.231  4.082 0.000      0.000        97.541 2023-01 → 2026-08   0.000       True
composite      38  135.976  2.067 0.019      0.004        21.866 2023-01 → 2026-06   0.039       True
```

**Confirmed in Taiwan: rev_mom, composite**
