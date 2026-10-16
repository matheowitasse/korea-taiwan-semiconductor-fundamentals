# Q15 pre-registration — is the profit-surprise drift real? Three tests on data nobody has looked at

Written and committed **2026-09-18, before the Q15 script is written or run**, and before any of the three event sets
below has had its outcome computed.

## Background (what is being tested, and why it is not yet a claim)

Q7b reported, as a side result (not a decisive test), that in 2025-07 → 2026-06 Korean chip companies with the largest
year-over-year operating-profit surprises (SUE) beat those with the smallest by **+31 %** over the next 60 trading days
(t 5.8, placebo p < 0.001). The Q7 T3 audit found: no data leak; robust to trimming the extreme 5 % (+27 %); present in
all five big event months; not explained by pre-announcement price momentum. In 2023-01 → 2025-06 the same measure was
weak (+5.9 % raw, +2.1 % trimmed, t 1.0).

This is an **exploratory finding in data already looked at**. The direction (positive: high surprise → higher return) is
fixed here in advance, and matches both the exploratory result and the long-standing earnings-momentum literature
(Bernard & Thomas; Chan, Jegadeesh & Lakonishok), so all tests below are **one-sided**.

## Common definitions (identical to Q7 / `src/q7_pead_test.py`, unchanged)

Universe list A; events, D0, exclusions, SUE, market adjustment, ranks within calendar quarter scaled to [−0.5, +0.5],
CAR60 = close(D0+1) → close(D0+61) minus market, CAR20 = close(D0+1) → close(D0+21) minus market.
The "> 31 % move" exclusion is applied over D0−2 → the end of that test's holding window.

**Inference.** Each event set covers one or two earnings seasons, so standard errors clustered by month are not usable
(1–2 clusters). Therefore:

- **Decisive:** the **placebo test** — SUE values shuffled among the events of the same calendar month, 5,000 draws,
  seed 42; one-sided p = share of draws with coefficient ≥ observed. **Pass = placebo p < 0.05.**
- Reported, not decisive: OLS slope with heteroskedasticity-robust (HC3) t, quintile means and medians, the slope after
  trimming the extreme 5 % of the outcome, and the number of events.

## The three tests

| ID | Events (D0) | Outcome | Run when | n (before outcome exclusions) |
|---|---|---|---|---|
| **S1** | 2022-07-01 → 2022-12-31 (never used: the Q7 study started 2023-01) | CAR60 | now | 96 events, 86 with SUE, almost all 2022-11 |
| **S2** | 2026-07-01 → 2026-08-31 (60-day windows not yet complete) | **CAR20** | now | ~123 events, those with a complete 21-day window |
| **S3** | 2026-07-01 → 2026-08-31 (the same events as S2) | CAR60 | when every window is complete (≈ 2026-11-20) | same events as S2 |

- S1 falls in the 2022 memory **downturn**; S2/S3 in the 2026 **boom**. This is deliberate: it tests whether the effect
  is general or boom-specific.
- S2 and S3 use the same events but different outcomes, both fixed here in advance.

## What may be claimed afterwards

- **S3 passes** → "confirmed out of sample at the same horizon as the original finding" (the strongest claim available
  this year). S1 and S2 are supporting evidence only.
- **S1 passes** → the effect is not boom-specific.
- **S1 fails, S2/S3 pass** → the effect is present in the boom and absent in the downturn; the claim is restricted to
  boom conditions and must say so.
- **All fail** → the Q7b +31 % stands as an in-sample observation only, and is reported as such in the write-up.
- No test may be re-run, re-specified or re-weighted after the fact. Whatever the outcome, all three results are reported.

## Known weaknesses (accepted in advance)

- S1: one earnings season (2022-11), 86 events, small caps in a downturn → low power; a fail is not proof of absence.
- S2: 20 days is a shorter horizon than the original 60-day finding; a fail does not refute S3.
- S2/S3: one earnings season each; both in the same regime.
- Korean chip small caps are volatile (median annualised volatility 87 % in 2025–26), so single events can dominate;
  this is why trimmed slopes and medians are reported.
- The strategy view (long the top surprise quintile) is long-only feasible; the short leg is not borrowable in practice
  for a retail account. Costs are not part of the pass rule (an edge is an edge for whoever can trade it).
