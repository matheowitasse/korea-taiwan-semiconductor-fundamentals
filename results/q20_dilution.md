# Q20 — Do dilution filings predict returns in Korean chip stocks?

Follows `docs/q20_dilution_events_preregistration.md` (committed before this script was written).
Direction fixed in advance: **negative** (dilution, hedge selling, refixing). Returns start at the close of
D0+1, so the announcement-day reaction and its documented leakage are excluded.

## Events

- **T1** (CB, 21 trading days): 148 events, 83 companies, 45 months, KOSDAQ 143 / KOSPI 5; excluded — no_price_or_not_listed 4, zero_volume 1, move_gt_31pct 2, short_history 1, window_incomplete 1
- **T2** (CB, 61 trading days): 141 events, 82 companies, 43 months, KOSDAQ 136 / KOSPI 5; excluded — no_price_or_not_listed 4, zero_volume 1, move_gt_31pct 4, short_history 1, window_incomplete 6
- **T3** (CB, 121 trading days): 124 events, 77 companies, 39 months, KOSDAQ 119 / KOSPI 5; excluded — no_price_or_not_listed 4, zero_volume 1, move_gt_31pct 6, short_history 1, window_incomplete 21
- **T4** (RIGHTS, 21 trading days): 120 events, 70 companies, 41 months, KOSDAQ 108 / KOSPI 12; excluded — no_price_or_not_listed 12, zero_volume 18, move_gt_31pct 2, short_history 0, window_incomplete 8
- **T5** (RIGHTS, 61 trading days): 113 events, 69 companies, 40 months, KOSDAQ 103 / KOSPI 10; excluded — no_price_or_not_listed 12, zero_volume 18, move_gt_31pct 4, short_history 0, window_incomplete 13

## Tests (one-sided, H1: mean < 0; Holm across the family)

```
test  event  days   n  months  mean_%  median_%      t  p_one_sided  placebo_p  announcement_window_%  shortable_%  p_holm  pass
  T1     CB    21 148      45   0.720    -4.172  0.210        0.583      0.481                  3.399        8.108   1.000 False
  T2     CB    61 141      43   6.481    -9.669  0.733        0.768      0.806                  3.571        7.801   1.000 False
  T3     CB   121 124      39  13.135   -14.765  0.948        0.828      0.803                  3.701        8.065   1.000 False
  T4 RIGHTS    21 120      41   5.165    -2.765  2.407        0.992      0.951                  0.434        9.167   1.000 False
  T5 RIGHTS    61 113      40  -3.427   -10.547 -1.047        0.148      0.033                  0.524        8.850   0.738 False
```

**Passed: none**

`announcement_window_%` is the market-adjusted return from close(D0−2) to close(D0+1), reported only to check
whether the positive announcement effect documented in the Korean literature appears in our sample.
`shortable_%` is the share of event stocks inside the KOSPI 200 / KOSDAQ 150 proxy — the fraction of any
negative result that could be traded at all. Cost reference: 30 bp round trip.

### Reported, not decisive: split at 2025-07 (regime break used elsewhere)

```
test  group  n  mean_%      t
  T1  after 51   4.390  0.493
  T1 before 97  -1.210 -0.459
  T2  after 44  30.050  1.075
  T2 before 97  -4.210 -1.302
  T3  after 28  80.459  1.460
  T3 before 96  -6.501 -1.539
  T4  after 44   7.653  1.985
  T4 before 76   3.724  1.439
  T5  after 37  -4.577 -0.572
  T5 before 76  -2.867 -0.928
```

### Reported, not decisive: by market

```
test  group   n  mean_%      t
  T1 KOSDAQ 143   0.761  0.215
  T2 KOSDAQ 136   7.068  0.771
  T3 KOSDAQ 119  14.638  1.017
  T4 KOSDAQ 108   5.439  2.460
  T5 KOSDAQ 103  -4.107 -1.196
```
