# Q7 — Post-earnings drift in Korean chip stocks

Follows `docs/q7_pead_preregistration.md` (approved and committed before this script was written).

Discovery 2023-01-01 → 2025-06-30; validation 2025-07-01 → 2026-06-16.
Coefficients in % of market-adjusted return, top-minus-bottom surprise rank (T1–T3) or the interaction (T4–T5).

## Events

Exclusion counts (all lists B ∪ C, all dates):

```
raw                       4912
no_price_or_not_listed     228
zero_volume                122
move_gt_31pct               15
short_history              249
window_incomplete          249
```

- list A, discovery: 1227 events, 114 companies, KOSDAQ 1091 / KOSPI 136, with SUE 1023, with market cap 1227, with retail flows 1227, delisted in window 0
- list A, validation: 517 events, 113 companies, KOSDAQ 472 / KOSPI 45, with SUE 439, with market cap 517, with retail flows 517, delisted in window 0
- list B, discovery: 1287 events, 119 companies, KOSDAQ 1133 / KOSPI 154, with SUE 1083, with market cap 1287, with retail flows 1287, delisted in window 0
- list B, validation: 543 events, 118 companies, KOSDAQ 491 / KOSPI 52, with SUE 465, with market cap 543, with retail flows 543, delisted in window 0
- list C, discovery: 2653 events, 245 companies, KOSDAQ 2225 / KOSPI 428, with SUE 2304, with market cap 2653, with retail flows 2653, delisted in window 0
- list C, validation: 1108 events, 244 companies, KOSDAQ 947 / KOSPI 161, with SUE 977, with market cap 1108, with retail flows 1108, delisted in window 0
- list BC, discovery: 2703 events, 249 companies, KOSDAQ 2257 / KOSPI 446, with SUE 2354, with market cap 2703, with retail flows 2703, delisted in window 0
- list BC, validation: 1129 events, 248 companies, KOSDAQ 961 / KOSPI 168, with SUE 998, with market cap 1129, with retail flows 1129, delisted in window 0

List A discovery events per quarter:

```
quarter_key
2023Q1    159
2023Q2     93
2023Q3     99
2023Q4    101
2024Q1    176
2024Q2    103
2024Q3    107
2024Q4    109
2025Q1    170
2025Q2    110
```

## Discovery — step 1: T1 alone (decisive)

```
test    n  months  coef_pct      t      p  placebo_p  pass
  T1 1227      23    5.5974 1.6317 0.1027     0.0816 False
```

**T1 FAILED discovery** (needs p < 0.10 and placebo p < 0.05)

## Discovery — step 2: T2–T5 (descriptive only, because T1 failed)

```
test    n  months  coef_pct      t      p  placebo_p  p_holm                         pass
  T2 1227      23    1.7549 0.7905 0.4292     0.3146  0.8584 descriptive only (T1 failed)
  T3 1023      23    5.9088 2.0079 0.0447     0.1010  0.1786 descriptive only (T1 failed)
  T4 1227      23    7.9325 1.1941 0.2325     0.6586  0.6974 descriptive only (T1 failed)
  T5 1227      23    2.8823 0.5025 0.6153     0.6636  0.8584 descriptive only (T1 failed)
```

**T1 failed → by the fixed-sequence rule nothing else can pass and validation is not run. No edge found.**
