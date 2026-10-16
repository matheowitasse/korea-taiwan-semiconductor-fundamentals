# Q12 pre-registration — Japan with five years of history

Written and committed **before** the longer Japanese history is downloaded (2026-09-21). Q9 tested Japan on the free
plan's window (2024-07 → 2026-06) and found the composite confirmed (+292 bp/month, t 3.54) with the single factors
positive but not individually significant. A J-Quants Light subscription extends the history to about 5 years.

## 1. Why this needs care

The 2024-07 → 2026-06 window **has already been seen**. Re-running the same test on a longer sample that contains it
would mix seen and unseen data and could turn into "run it again until it works".

**Split, fixed now:**

| Window | Status | Role |
|---|---|---|
| 2021-10 → 2024-06 (about 33 months) | never seen | **decisive new evidence** |
| 2024-07 → 2026-06 | already seen in Q9 | reported separately, not counted as confirmation |
| Full sample | mixed | reported for completeness only |

## 2. Hypothesis (unchanged from Q9)

In Japanese chip-sector stocks, ranking on the improvement composite (quality = operating profit over the last four
quarters / total assets; earnings momentum = latest quarter's operating profit vs the same quarter a year earlier)
predicts next-month cross-sectional returns. **One-sided positive**, because the direction is set by the Korean and
Taiwanese results.

## 3. Definitions (unchanged)

- Universe: J-Quants sectors 電気機器 and 精密機器, companies listed in the month concerned.
- Quarterly figures are cumulative within the fiscal year → single-quarter amounts by differencing; each statement is
  usable from the next trading day after disclosure (same day if disclosed before 15:00).
- Value (BPS / price) is **reported but not decisive**: it failed in Korean validation and was negative in Taiwan.
- Month-end equal-weight quintiles, held one month; statistic = mean long-short (top − bottom) return,
  Newey–West t (3 lags); placebo = factor values shuffled within each month, 500 shuffles.
- A month enters only with at least 30 scored stocks and a next-month return.

## 4. Decisive test and rule

**One test:** the composite long-short return over **2021-10 → 2024-06**, one-sided positive.
(Boundary set by the subscription, which starts 2021-09-21; fixed before any Japanese return outside the
already-seen window was computed.)
**Confirmed if** t > 2 (one-sided p < 0.05) **and** placebo p < 0.05.

Reported alongside, not decisive: quality, earnings momentum and value over the same unseen window; all four over the
already-seen window; all four over the full sample; and the risk-adjusted alpha (index, size and momentum spreads)
over the unseen window.

## 5. What each outcome means

- **Confirmed:** the effect holds in Japan outside the AI boom window as well, in a period that includes the 2022–23
  semiconductor downturn. Japan then joins Korea and Taiwan in the paper's main claim.
- **Not confirmed:** Japan is reported as a market where the effect could not be demonstrated outside the boom, and the
  main claim stays Korea + Taiwan. The Q9 Japanese result is then treated as a boom-period observation only.

## 6. Known weaknesses

- The J-Quants universe contains currently listed companies, so Japanese delisted firms are still missing.
- Japanese fiscal years vary by company; the differencing depends on the fiscal-year fields being correct.
- Five years still spans only one full semiconductor cycle.
