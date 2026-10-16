# Q7b pre-registration — post-earnings drift in the recent Korean market (second look) + regime comparison

Written and committed **2026-09-18, before the Q7b script is written or run.** Requested by the author.

## Why, and how it must be read

Q7 T1 (60-day post-earnings drift, list A) narrowly failed discovery on 2023-01 → 2025-06: +5.6 %, clustered t 1.63,
p 0.103, placebo p 0.082. By the Q7 rules validation was not run, so **events from 2025-07-01 onward are untouched** for
post-earnings drift.

The author's argument: the Korean market changed strongly in 2025–26 (memory-chip rally, KOSPI above 6,000, record foreign
selling), so the recent period is the market that matters. Pooling 2023–2026 after seeing the Q7 result is **not** allowed
(result-driven). Instead:

- **Part 1 (decisive)** tests T1 on the recent period alone. It is a **follow-up chosen after a near-miss**, so a pass is
  weaker evidence than a pass of the original Q7 sequence, and it is reported that way.
- **Part 2 (descriptive)** documents whether the market changed, with a fixed list of measures and a fixed break date.

## Part 1 — T1 on 2025-07-01 → last complete 60-day window (decisive)

- Everything exactly as Q7 (`docs/q7_pead_preregistration.md`, `src/q7_pead_test.py`): list A, same events, exclusions,
  EAR, CAR60, ranks within calendar quarter, OLS with standard errors clustered by month of D0, 5,000 within-month
  placebo shuffles, seed 42.
- Period: D0 from 2025-07-01 to the last D0 with a complete 60-day window (2026-06-16 in the Q7 run).
- **One-sided, H1: coefficient > 0** (drift). Justified by prior research on Korea and fixed now; the Q7 discovery sign was
  also positive.
- **Pass = one-sided clustered p < 0.05 and one-sided placebo p < 0.05** (placebo p = share of draws with coefficient ≥ observed).
- Reported, not decisive: lists B, C, B ∪ C (same sign?); T3 (SUE) on the same period; the Q7 strategy illustration
  (long top EAR quintile, 60 days, vs market, with and without 0.30% cost); the coefficient difference recent − discovery.

## Part 2 — did the market change? (descriptive only, not a formal break test)

Break date fixed at **2025-07-01** (the project's validation split, set before any Q7 result). No other break dates will
be searched. "Before" = 2023-01-01 → 2025-06-30, "after" = 2025-07-01 → 2026-09-16.

| Measure | Data |
|---|---|
| Market return and annualised daily volatility, KOSPI and KOSDAQ | Yahoo ^KS11, ^KQ11 |
| List-A median stock: annualised daily volatility; median daily turnover (close × volume / quarter-end market cap) | Q7 prices, KRX snapshots |
| List-A median share of trading that is retail net buying, \|individual net value\| / (close × volume) | Naver flows |
| KOSPI foreign net buying per month (trn KRW) | KRX hand downloads |
| Earnings reactions: cross-sectional std and mean \|EAR\| of list-A events | Q7 events |
| Q7 T1 coefficient before vs after (from part 1 and Q7) | Q7 |

For each measure: before, after, and ratio after/before. For the per-event and per-stock measures also a simple two-sample
comparison (Welch t or Mann-Whitney), clearly labelled descriptive.

Earlier project findings that are relevant and will be cited (not re-tested): Q2 (Korea copies more of the US overnight move
in the AI era, SK Hynix gap beta 0.54 → 0.77, break at 2023), Q4b (US sell-off nights in 2025-07+ far more volatile than in
2023–25), Q5 (KOSPI foreign net buying 2023 +11.3, 2024 +1.3, 2025 −4.7, 2026 to 09-16 −179 trn KRW).

## Known weaknesses (accepted in advance)

- ~12 event months in the recent period → clustered standard errors with few clusters are unreliable; the placebo test is
  the more robust of the two criteria, and both must pass.
- Follow-up after a near-miss (see above); one period, one regime, ~1 year: even a pass needs confirmation on future quarters.
- Part 2 can show that conditions differed, not that they caused any difference in drift.
- The break date is the project's split, not an estimated break; the real change may have happened at another time.
