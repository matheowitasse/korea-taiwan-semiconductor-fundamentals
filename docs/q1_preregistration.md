# Q1 pre-registration — Korean chip export releases → US semiconductor stocks

Written and committed **2026-09-16, before any Q1 return data was looked at.**
Any change after this date is logged in the project's research log with the reason, and results are reported
against this original plan as well.

## 1. Data

- Releases: Korea Customs Service 10-day and 20-day preliminary trade releases, first-release figures as published
  (`data/interim/kcs_releases_extracted.csv`).
- Release date `D` = posting date. Releases are published during the Korean day, i.e. before the next US open
  (09:00 KST = 19:00/20:00 ET on D-1; any time before 23:30 KST is still before the US open on US date D).
- Prices: Yahoo Finance daily adjusted OHLC.
- **In-sample:** releases whose longest return window (20 US trading days) ends on or before 2025-06-30.
  Everything after is holdout and is not used for exploration.

## 2. Signal definitions (fixed now)

For each release *t*:

- `semis_yoy` = semiconductor exports YoY % as published.
- `wd_ratio` = working days previous year / working days current year (published from 2019).
- **`adj_yoy`** = (1 + semis_yoy/100) × wd_ratio − 1 → YoY growth of chip exports **per working day**.
- **Primary signal `S1`** = `adj_yoy(t)` − mean(`adj_yoy` of the previous 3 releases).
  Positive = chip export growth accelerating vs recent releases. Available from ~2019.
- **Secondary signal `S2`** = `semis_yoy(t)` − mean(`semis_yoy` of the previous 3 releases), no working-day adjustment.
  Available from 2016 (bigger sample, noisier).

## 3. Returns

Entry = **open** of the first US trading day with date ≥ D (first US session after the release).

- `r1`  = open(day 0) → close(day 0)
- `r5`  = open(day 0) → close(day 4)
- `r20` = open(day 0) → close(day 19)

Assets: **SOXX (primary)**; NVDA, MU (secondary). Korean reaction for context only: SK Hynix, Samsung close(D−1) → close(D).

## 4. Primary test (one test)

OLS of **SOXX `r5` on `S1`**, HAC standard errors (2 lags).

Supporting evidence required for the primary result to count as "promising" (all three):
1. slope t-stat > 2 **and** placebo p < 0.05 (signal shuffled across releases, 5,000 permutations);
2. same sign of the slope in both regimes: 2019–2022 and 2023–2025H1;
3. mean `r5` of the top-tercile `S1` releases minus bottom-tercile > 0.5 percentage points.

If all three hold → build the strategy rules and run **one** holdout test. Otherwise the primary result is reported as negative.

## 5. Secondary tests (reported, corrected for multiple testing)

- {S1, S2} × {SOXX, NVDA, MU} × {r1, r5, r20} = 18 regressions, Holm–Bonferroni correction reported next to raw p-values.
- Volatility: does |S1| (or S1 < 0) predict higher 5-day realised volatility of SOXX than placebo release dates?
- Regime split for all of the above: pre-2023 vs 2023+.

## 6. Strategy (only if section 4 is promising)

Overlay on a long US semis position, rebalanced at the open after each release:
- S1 top tercile → 100% exposure; middle → 75%; bottom → 50% (tercile cut-offs from in-sample only).
- Compared with buy-and-hold on return, volatility, max drawdown, Sharpe, after 0.05% per rebalance.

## 7. Known weaknesses (accepted in advance)

- Working-day adjustment only from 2019 → ~150 in-sample releases for S1.
- 10-day and 20-day releases of the same month overlap (days 1–10 are inside days 1–20).
- 2023–2025 AI boom: huge YoY numbers, possible base effects; regime split is mandatory.
- Missing months in the customs archive are left missing (not filled from other sources) in this first test.
