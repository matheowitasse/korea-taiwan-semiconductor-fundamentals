# Q4b pre-registration — Korea-only supplier rebound on untouched data (narrowed validation)

Written and committed **2026-09-17, before running any rebound test on data after 2025-06-30.**

## Why this test, and why it is labelled "narrowed"

Q4 (`docs/q4_supplier_rebound_preregistration.md`) tested the supplier rebound in Korea, Taiwan and Japan. Korea was the
best of the three (+52 bp, t 1.60, placebo p 0.033) but failed Holm correction across the three markets (p 0.23), so by the
Q4 rules validation was not run. **Choosing Korea after seeing it was the best market is a selection step**, so a pass here
is weaker evidence than a pass in the original Q4 design. Any result is reported as "narrowed validation".

What has been seen after 2025-06-30 in the data used here: Yahoo Korean prices were loaded for Q5 (coverage counts only;
no open→close returns on SOXX sell-off nights were computed or looked at).

## Hypothesis (unchanged from Q4)

After a night where US semiconductors fall sharply (SOXX overnight < −2%), the Korean chip **supplier basket** rises
from the open to the close of the next Korean session.

## Data and definitions — identical to Q4, Korea only

- Yahoo daily adjusted OHLCV, same cleaning (zero volume or O=H=L=C → missing), KOSPI (^KS11) calendar.
- US signal for Korean day D: SOXX open→close compounded over US sessions dated in [previous Korean day, D).
- Big-down night: signal < −2%.
- Basket: equal-weight open→close of Hanmi Semi 042700.KS, DB HiTek 000990.KS, Leeno 058470.KQ, ISC 095340.KQ,
  Wonik IPS 240810.KQ, Jusung Eng 036930.KQ, Eugene Tech 084370.KQ, HPSP 403870.KQ.
- Code: the Q4 functions `build()` and `test()` in `src/q4_supplier_rebound.py`, unchanged.

## Test and decision rule (one test, no multiple-testing correction needed)

- Period: D from **2025-07-01 to 2026-09-16**.
- One-sample t-test on the basket's open→close return on big-down nights, **one-sided, H1: mean > 0**.
- Placebo (5,000 draws, seed 42): same number of days drawn at random from all Korean trading days in the period;
  p = share of draws with mean ≥ observed.
- **Pass (statistical) = t-test p < 0.05 and placebo p < 0.05.**
- **Tradable after costs (reported, stricter)** = one-sided t-test of (mean − 30 bp) > 0 with p < 0.05,
  using the project's 0.30% round-trip cost assumption.

## Reported, not decisive

- Number of nights, mean, median, hit rate, mean excluding the single best night.
- Large names (Samsung, SK Hynix) on the same nights, for contrast.
- Discovery (2023-01 → 2025-06) and validation side by side.

## Known weaknesses (accepted in advance)

- **Low power.** Q4 discovery implies a per-night standard deviation of roughly 2.4%. With ~30–45 big-down nights,
  the standard error is about 35–45 bp, so a true +52 bp effect would pass the 5% test only around 40–50% of the time.
  A fail is "no evidence", not proof there is nothing.
- Selection of Korea after Q4 (see above); supplier list chosen in 2026 with hindsight.
- 2026 is an extreme regime (memory rally, very large foreign selling), which may not resemble other years.
- Yahoo open prices unverified.
