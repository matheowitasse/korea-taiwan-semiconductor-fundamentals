
# Q22 pre-registration — does the effect exist before the AI era? (Korea, 2015–2022)

Written and committed **2026-09-21, before the Q22 script is written and before any pre-2023 monthly return of this
universe has been computed.** This is a genuine out-of-sample test in time: every decisive result in the project so far
uses 2023-01 onward, and the 2015–2022 period has never been touched for this signal.

## 1. Why

The frozen finding (tag `finding-v1`) rests on 44 months inside a single semiconductor upcycle, in Korea and Taiwan.
The most serious objection is that the effect is a property of that boom rather than of these markets. Japan's unseen
window — the only one containing a downturn — did not confirm (t 1.80). Eight years of Korean history, including the
2018–19 memory bust and the 2020–21 recovery, can answer the question directly.

**This test can go against us, and we run it anyway.** If the signal is absent before 2023, the paper's claim narrows to
a regime-specific effect and the abstract must say so.

## 2. Hypothesis and direction

The signal used in the backtests — the equal-weight average of z-scored **quality** (operating profit over the trailing
four quarters ÷ total assets) and **earnings momentum** (standardised unexpected earnings) — predicts next-month
cross-sectional returns **positively** in Korean chip-supply-chain stocks over 2015-01 → 2022-12.

Direction is fixed from the existing result; all tests are **one-sided (positive)**.

## 3. Data

- **Universe (285 codes, `data/interim/q22_universe_codes.csv`)**: the 262 current chip-supply-chain companies plus the
  23 companies in the same industry codes that were delisted between 2015-01 and 2022-06, recovered from the KIND
  delisting register (716 delistings, 34 of them chip companies). Two of the 23 (103650, 158300) have no price history
  available and are unavoidably absent; this is reported.
- **Prices**: Yahoo from 2015-01 for listed names (already cached back to 2015-01-02); Naver daily closes for the
  delisted names, which run to each company's last trading day.
- **Fundamentals**: DART key accounts extended to 2014–2019 (needed for trailing-four-quarter figures from 2015).
- **Point-in-time rule.** The filing-date calendar only covers 2022-07 onward. For earlier quarters we therefore use the
  **statutory deadline**: quarterly and half-year figures become usable 45 days after quarter end, annual figures 90 days
  after year end. This is more conservative than actual filing dates (most firms file earlier) and is fixed here in
  advance.

## 4. Tests

| ID | Period | Statistic |
|---|---|---|
| **E1 (primary)** | 2015-01 → 2022-12 (96 months) | mean monthly long–short spread (top − bottom quintile), equal weight |
| E2 | same | alpha after the market, size and momentum controls used in `src/q10_risk_adjustment.py` |
| E3 | 2015-01 → 2026-08 (full history) | spread, reported for completeness |

- Newey–West standard errors (3 lags); placebo = signal shuffled across stocks within each month, 5,000 draws,
  one-sided.
- **Pass (E1, decisive): t > 2 and one-sided placebo p < 0.05.** E2 and E3 are reported whatever E1 does.
- Sub-period means (2015–2017, 2018–2019 memory bust, 2020–2022) are reported without significance tests: they are
  descriptive, and we will not re-cut the sample to find a window that works.

## 5. How the result will be read, fixed now

- **E1 passes** → the effect is not boom-specific; the paper reports a 140-month Korean sample and the claim strengthens
  substantially.
- **E1 fails but E2's alpha is positive with t > 2** → mixed; report both and describe the effect as present but weaker
  outside the boom.
- **E1 fails** → the effect is regime-specific. The abstract, conclusion are amended to say the
  result holds in the 2023–2026 upcycle and not in the preceding eight years.

## 6. Known weaknesses (accepted in advance)

- **Classification look-ahead:** universe membership uses today's DART industry codes, so a company that became a chip
  supplier in 2019 is treated as one in 2015. We cannot reconstruct historical codes from the available data.
- **Survivorship is improved but not complete:** delistings are recovered from 2015, two of them without prices, and
  companies that delisted before 2015 are absent.
- Financial statements are current (restated) values, as elsewhere in the project.
- Naver closes for delisted names are unadjusted for corporate actions; the >31% daily-move screen used elsewhere is
  applied to them as well.
- 2015–2022 contains two regimes (the 2018–19 bust and the 2020–21 recovery); a single mean over 96 months averages them.
