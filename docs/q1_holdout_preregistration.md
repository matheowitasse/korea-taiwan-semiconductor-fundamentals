# Q1 holdout pre-registration — "sell the news" in the AI era

Written and committed **2026-09-16, before any price or return data after 2025-06-30 was loaded.**
This hypothesis was **not** in the original plan (`q1_preregistration.md`). It came from looking at in-sample results
(`results/q1_first_test.md`, S2 by regime), so it can only be confirmed on data that was never used. The holdout is used
**once** for this test; whatever the result, it is reported.

## 1. Hypothesis

In the AI era, a Korean chip export release showing **faster growth than the recent trend** is followed by
**lower** US chip stock returns over the next week ("sell the news").

In-sample evidence that motivated it (2023-01 → 2025-05, n = 58): NVDA r5 ~ S2 slope t = −3.36; SOXX r5 ~ S2 t = −2.01.
In 2016–2022 the sign was the opposite (positive, not significant).

## 2. Data

- Releases posted **on or after 2025-07-01** whose 5-day return window is complete in the price data available on the test date.
- Signal **S2** exactly as in `q1_preregistration.md`: `semis_yoy(t)` − mean(`semis_yoy` of the previous 3 releases).
  No working-day adjustment, so the 2025H2 format change (working days not yet extracted) does not affect it.
  The previous 3 releases may be pre-holdout releases (signal only; no pre-holdout returns are used).
- Returns: `r5` = open of first US trading day with date ≥ release date → close 4 trading days later (same as before).
- Prices: Yahoo Finance daily adjusted, downloaded fresh into a separate cache.

## 3. Primary test (one test)

OLS of **NVDA r5 on S2**, HAC standard errors (2 lags). **One-sided: slope < 0.**

"Confirmed" requires all three:
1. HAC t-stat < −1.70 (one-sided ~5%);
2. placebo p < 0.05, one-sided (S2 shuffled across holdout releases, 5,000 permutations; share of shuffles with slope ≤ observed);
3. mean NVDA r5 after **top-tercile** S2 releases is lower than after **bottom-tercile** releases, with tercile cut-offs taken
   from the **in-sample AI-era S2 values (2023-01 → 2025-05)**, not from the holdout itself.

Anything else → "not confirmed".

## 4. Reported alongside (not decisive)

- SOXX r5 and MU r5 on S2 (same one-sided direction).
- Number of holdout releases and their date range.
- Power warning: with ~25–30 releases, even a real effect of the in-sample size may fail to reach significance.
  "Not confirmed" therefore means "no evidence", not "proven absent".

## 5. What happens next

- Confirmed → the effect goes into the paper as a pre-registered out-of-sample result; a strategy study may follow, but
  there is no untouched data left, so any strategy would need live paper-trading from now on before real money.
- Not confirmed → Q1 is written up as a negative result, with this test included.
