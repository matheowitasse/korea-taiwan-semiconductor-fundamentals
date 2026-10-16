# Q9 pre-registration — does the Korean factor result also appear in Japan and Taiwan?

Written and committed **before any Japanese or Taiwanese return is computed** (2026-09-21). Data collection so far used
no returns: company lists, quarterly statements, month-end valuation ratios, monthly revenue, price files.

## 1. Hypothesis

The Q8 result in Korea — chip-supply-chain stocks that are **more profitable relative to assets** (quality) or whose
**profits/sales are improving fastest** (earnings or revenue momentum) outperform over the following month — also holds
in Japan and Taiwan. Direction is fixed by the Korean finding, so **all tests are one-sided (positive)**.

This is a confirmation test of a hypothesis formed on Korean data: the Japanese and Taiwanese data have never been used
for it, so the whole window is out-of-sample and there is **no discovery / validation split**.

## 2. Universes (fixed now)

- **Japan:** J-Quants sectors 電気機器 (electric appliances) and 精密機器 (precision instruments) — 276 companies with data
  (`data/raw/jquants/master.csv`). Prices: Yahoo (`data/raw/q9_jp_prices/`).
- **Taiwan:** TWSE industry codes **24 (semiconductors)** and **28 (electronic components)** plus the same codes on TPEx
  (`data/raw/taiwan/companies_twse.csv`, `companies_tpex.csv`). Prices: Yahoo (`.TW` / `.TWO`).
- Both lists are companies listed **today**, so companies delisted during the period are missing (the Korean test
  included them). This survivorship gap is a known weakness, and it works **against** finding the effect only if failures
  were concentrated in low-quality names — which is the direction of the hypothesis, so results must be read with care.

## 3. Factors (only what each market's data supports)

**Japan** (quarterly statements are cumulative within the fiscal year → quarterly amounts by differencing; fiscal years
differ by company, taken from `CurFYSt`/`CurFYEn`; a statement is usable from the next trading day after its disclosure
date, or the same day if disclosed before 15:00):

| Factor | Definition |
|---|---|
| quality | operating profit over the last 4 quarters / total assets |
| value | book value per share (BPS) / price |
| earn_mom | operating profit of the latest quarter vs the same quarter a year earlier, in % |
| composite | mean of available z-scores (at least 2 of 3) |

**Taiwan**:

| Factor | Definition |
|---|---|
| value | 1 / price-to-book at the month end (TWSE daily valuation file) |
| rev_mom | latest published monthly revenue vs the same month a year earlier, in % (published by the 10th, so the month-end portfolio uses the figure published that month) |
| composite | mean of the two z-scores (both required) |

z-scores are cross-sectional within the market and month, winsorised at ±3.

## 4. Portfolios and statistics (same as Q8)

- Month-end ranking, **equal-weight quintiles**, held one month.
- Statistic: mean monthly **long-short** (top − bottom quintile) return, Newey–West t (3 lags), **one-sided positive**.
- Also reported: long-only (top quintile − universe average), turnover, and costs at 0.30% per unit of turnover.
- Placebo: factor values shuffled across stocks within each month, 500 shuffles.
- A month enters only if at least 30 stocks have the factor and a next-month return.

## 5. Decision rules

- Each market is its own family: Holm correction across that market's tests (Japan 4, Taiwan 3).
- **Confirmed in that market** = Holm-adjusted one-sided p < 0.05 **and** placebo p < 0.05.
- Expected windows (driven by data availability, not by results): Japan quality/earn_mom from about 2025-08, value from
  about 2024-10, to 2026-06; Taiwan 2023-01 → 2026-08.
- If a market confirms, the Korean result is much more credible; if neither does, the Korean result stays a single-market
  finding to be judged by live tracking.

## 6. Known weaknesses (accepted in advance)

- Japan's usable window is short (~11–20 months depending on the factor) → low power.
- Taiwan cannot test quality (quarterly statements are not accessible without scraping MOPS), so its test is value plus a
  revenue-momentum signal that Korea does not have — a related but not identical hypothesis.
- No delisted companies in either market.
- Sector definitions differ across the three markets; the Japanese sectors are broader than "chips".
- Yahoo prices are unverified against the local exchanges.
