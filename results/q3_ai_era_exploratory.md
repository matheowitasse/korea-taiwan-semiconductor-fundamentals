# Q3 exploratory — A–E on the AI era (2023-01 → 2026-09)

**Exploratory, not confirmatory.** Deviation from the pre-registration, logged in the project's research log before running.

Effects: A/B = event-day minus non-event-day mean return (bp); C/D/E = bp per +10 pp of S2. p = two-sided.

```
id                                 test  n  effect_bp  t_or_welch_p  p_holm  placebo_p  effect_bp 2023-2024  p 2023-2024  effect_bp 2025-2026  p 2025-2026  lead
A1       Pre-release drift, Big2 on D-1 88    46.5129        0.1353  0.9472     0.1514              20.0316       0.4644              78.7190       0.1869 False
A2  Pre-release drift, Suppliers on D-1 88    50.1996        0.1681  1.0000     0.1440              28.8653       0.4946              75.9642       0.2237 False
B1       Release-day premium, Big2 on D 88     8.1767        0.8020  1.0000     0.8046               9.8022       0.7021               6.6546       0.9187 False
B2  Release-day premium, Suppliers on D 88     7.7369        0.8328  1.0000     0.8286              -2.4653       0.9491              20.1429       0.7621 False
B3      Release-day premium, KOSPI on D 89     8.5272        0.6638  1.0000     0.6854              20.4776       0.1413              -5.5442       0.8891 False
 C     Suppliers open->close on D vs S2 89   -22.0354        0.1784  1.0000     0.1538              -7.9515       0.7383             -31.2443       0.0963 False
 D    SK Hynix minus Samsung on D vs S2 88     6.9271        0.6508  1.0000     0.5906              25.0222       0.2908               4.6388       0.7849 False
 E SK Hynix close(D)->close(D+20) vs S2 87   167.2163        0.0884  0.7071     0.1536            -102.7019       0.6131             209.4717       0.1591 False
```

**Leads worth forward-testing: none**
