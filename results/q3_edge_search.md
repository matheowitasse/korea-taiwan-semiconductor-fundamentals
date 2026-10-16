# Q3 edge search A–E

Follows `docs/q3_edge_search_preregistration.md` (committed before running).

Discovery 2016-08-01 → 2022-12-31; validation 2023-01-01 → 2026-09-16.
Effects: A/B = event-day minus non-event-day mean return (bp); C/D/E = bp of return per +10 pp of S2.

## Discovery (all 8 tests)

```
id                                 test   n  effect_bp  t_or_welch_p  placebo_p      t  p_holm  pass
A1       Pre-release drift, Big2 on D-1 133   -15.0023        0.3294     0.2896    NaN  1.0000 False
A2  Pre-release drift, Suppliers on D-1 135    -3.2527        0.8654     0.8484    NaN  1.0000 False
B1       Release-day premium, Big2 on D 135    -9.9080        0.5864     0.4890    NaN  1.0000 False
B2  Release-day premium, Suppliers on D 134    -2.2994        0.9074     0.8924    NaN  1.0000 False
B3      Release-day premium, KOSPI on D 137   -12.2869        0.2358     0.1624    NaN  1.0000 False
 C     Suppliers open->close on D vs S2 132     5.6762        0.3314     0.5224 0.9712  1.0000 False
 D    SK Hynix minus Samsung on D vs S2 131    11.6407        0.2288     0.2434 1.2035  1.0000 False
 E SK Hynix close(D)->close(D+20) vs S2 129    69.2786        0.1834     0.1974 1.3303  1.0000 False
```

**No test passed discovery → no edge found among A–E. Validation not run (as pre-registered).**
