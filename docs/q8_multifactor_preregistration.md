# Q8 pre-registration — multi-factor cross-section in Korean chip stocks

Finalised 2026-09-21 and committed **before** the test script is written and before any Korean chip-stock
return of this study is computed. Q1–Q7 tested single signals and events and found nothing at daily frequency; Q8 asks a
different question: do **combined stock characteristics**, rebalanced monthly, separate winners from losers?

## 1. Hypothesis

At each month end, ranking Korean chip-supply-chain stocks on a combined score (value, quality, earnings momentum, price
momentum, size) separates next-month returns: the top quintile outperforms the bottom quintile.

## 2. Universe and data

- **Primary: list B ∪ C** (~250 companies: DART industry codes 261, 29271 and 262, plus Samsung Electronics, Leeno, ISC,
  Wonik IPS, Jusung Engineering), **including delisted companies** until their last trading day
  (`data/interim/q7_universe_codes.csv`, `data/interim/kind_delisted.csv`).
  **List A (~120 pure chip names) is reported as robustness.**
- Prices: Yahoo adjusted (`data/raw/q7_yahoo/`), KRX for delisted (`data/raw/krx_prices/`).
- Financials: DART key accounts (`data/interim/dart_financials.csv`), consolidated preferred; SUE (`data/interim/dart_sue.csv`).
- Market cap: shares outstanding from the latest KRX quarter-end snapshot × price at the month end.
- **Point-in-time rule:** a quarter's financials may be used only from the day after that company's first earnings
  disclosure for that quarter (`data/interim/dart_earnings_disclosures.csv`); if that is missing, from the statutory
  deadline (45 days after quarter end, 90 days for the annual report).

## 3. Factors (ranked cross-sectionally within the universe each month end)

| Factor | Definition |
|---|---|
| **Value** | book equity (자본총계) / market cap |
| **Quality** | operating profit over the last 4 quarters / total assets |
| **Earnings momentum** | SUE of the most recent reported quarter |
| **Price momentum** | return from 12 months before to 1 month before (latest month skipped) |
| **Size** | −log(market cap) |
| **Composite** | mean of available factor z-scores (winsorised at ±3); at least 3 of the 5 required |

A stock enters a month's ranking only if it has a price at that month end and a next-month return (or a delisting return).

## 4. Portfolios and statistics

- Equal-weight **quintiles**, held one month, rebalanced at each month end.
- Statistic: mean monthly **long-short** return (top − bottom quintile), t-stat with Newey–West (3 lags).
- Also reported: **long-only** (top quintile − universe average), the version the author could trade.
- Placebo: factor values shuffled across stocks within each month, 5,000 times; p = share with |mean| ≥ observed.

## 5. Tests (one Holm family of 6, list B ∪ C)

T1 composite, T2 value, T3 quality, T4 earnings momentum, T5 price momentum, T6 size. Two-sided in discovery.

## 6. Periods and decision rules

- **Regime definition (decided 2026-09-21, from `results/q8_regime_break.md`):** the AI era is dated from **2023-01** for
  the tests, because break estimates on Korean chip exports (2024-02) and on the semiconductor share of exports (2024-05)
  date the *fundamental* shift a year after the AI narrative began (ChatGPT 2022-11-30, Nvidia guidance 2023-05-24), and a
  2024-02 start would leave only ~17 discovery months. **The 2024-02 split is pre-registered as a robustness report.**
- **Discovery:** month ends 2023-01 → 2025-06 (30 monthly returns). Pass = Holm p < 0.10 **and** placebo p < 0.05.
- **Validation:** 2025-07 → last complete month, survivors only, one-sided in the discovery direction;
  Holm p < 0.05 **and** placebo p < 0.05.
- **Robustness (not decisive):** list A; long-only; value-weighted; split at 2024-02 (before / after the fundamentals break).
- Costs are reported, not part of the pass/fail rule: 0.30% per unit of turnover (includes the ~0.2% sell tax), with the
  monthly turnover of each portfolio.

## 7. Handling of awkward cases (fixed in advance)

- **Delisting inside a month:** that month's return uses the last traded price (liquidation trading); the stock then leaves.
- **Trading halts:** the stock stays at its frozen price (a holder cannot sell).
- **Data errors:** a monthly return is dropped if the month contains a close-to-close move > 31% (either direction) that is
  not followed by delisting within 10 trading days.
- **Fiscal years:** December year-ends assumed; companies whose quarter mapping fails are excluded from factors needing it.

## 8. Known weaknesses (accepted in advance)

- 30 discovery months is short: only fairly strong effects can be detected.
- DART financials are current values (restatements included), so not strictly point-in-time.
- Shares outstanding only at quarter ends.
- Industry codes are today's; renamed or repurposed companies are not tracked historically.
- Yahoo adjusted prices are unverified against KRX for listed names.

## Decisions (user, 2026-09-21, before any return was computed)

- Primary universe B ∪ C; list A as robustness.
- All 6 tests (composite + 5 single factors) decisive, Holm-corrected together.
- Long-short as the main statistic; long-only reported.
- Regime option **C**: discovery from 2023-01, with a 2024-02 robustness split.
