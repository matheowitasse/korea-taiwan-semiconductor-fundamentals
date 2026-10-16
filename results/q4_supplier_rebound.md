# Q4 — Asian chip suppliers after big US chip sell-offs (SOXX overnight < −2%)

Follows `docs/q4_supplier_rebound_preregistration.md` (committed before running).

Discovery 2023-01-01 → 2025-06-30; validation 2025-07-01 → 2026-09-16. Returns = open→close on the Asian session after the US night. Costs ignored.

## Discovery — supplier baskets (decisive)

```
  id  n_nights  mean_bp  all_days_mean_bp  hit_rate_%      t  p_one_sided  placebo_p  p_holm  pass
  KR        56   52.370             1.370      55.357  1.600        0.058      0.033   0.231 False
  TW        52   16.082           -12.257      48.077  0.504        0.308      0.086   0.652 False
  JP        55   -1.275             8.789      43.636 -0.042        0.516      0.669   0.652 False
POOL        65   18.626            -0.412      55.385  0.786        0.217      0.115   0.652 False
```

Contrast, not decisive — large names (Samsung/SK Hynix, TSMC/MediaTek, Tokyo Electron/Advantest):

```
  id  n_nights  mean_bp  all_days_mean_bp  hit_rate_%     t  p_one_sided  placebo_p
  KR        56    7.908            -3.084      48.214 0.372        0.356      0.277
  TW        52   26.910            -2.013      51.923 1.149        0.128      0.042
  JP        55   13.247             5.804      45.455 0.382        0.352      0.373
POOL        65   13.327            -0.593      52.308 0.650        0.259      0.153
```

**No test passed discovery → validation not run (as pre-registered). No edge found.**
