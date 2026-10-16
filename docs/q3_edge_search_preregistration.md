# Q3 pre-registration — edge search around Korean export releases (ideas A–E)

Written and committed **2026-09-16, before any of these tests were run.**
Goal: find out whether *any* reliable price effect exists around the KCS 10-day / 20-day export releases,
ignoring trading costs for now. Structured as discovery → validation to limit false discoveries.

## 1. Data

- Releases: all 10-day and 20-day releases in `data/interim/kcs_releases_extracted.csv`.
- Release day `D` = first Korean trading day (KOSPI calendar) on or after the posting date.
  Releases are published during the Korean morning (09:00 KST where stated), i.e. inside the day-D session.
- Prices: Yahoo Finance daily adjusted OHLCV, fresh download 2015-01-01 → today, separate cache (`data/raw/full_*.parquet`).
  Bars with zero volume or O=H=L=C are treated as missing; a daily return is missing if either bar is missing.
- Portfolios (equal-weight daily average of available members):
  - **Big2** = Samsung Electronics (005930.KS), SK Hynix (000660.KS)
  - **Suppliers** = Hanmi Semi, DB HiTek, Leeno, ISC, Wonik IPS, Jusung Eng, Eugene Tech, HPSP (same list as Q2; chosen with
    hindsight — disclosed weakness)
  - **KOSPI** = ^KS11
- Signal **S2** (as in `q1_preregistration.md`): semis YoY(t) − mean(semis YoY of previous 3 releases).

## 2. Periods

- **Discovery:** releases with D from 2016-08-01 to 2022-12-31.
- **Validation:** releases with D from 2023-01-01 to 2026-09-16 (return windows must be complete).
- Disclosure: 2023+ data was already seen for US assets (NVDA/SOXX/MU r1/r5/r20 vs S1/S2) and Korean day-0 close-to-close
  for SK Hynix / Samsung vs S1/S2 (`results/q1_first_test.md`). **Idea D overlaps with that last check** (both use SK Hynix
  and Samsung day-0 returns with S2); its validation result must be read with that in mind.

## 3. The 8 tests (the complete family)

Daily return r(t) = close(t)/close(t−1) − 1. "Non-event days" = trading days in the same period that are neither a release
day D nor the day before a release (D−1).

| ID | Idea | Measure | Test |
|---|---|---|---|
| A1 | Pre-release drift | Big2 return on D−1 | mean(D−1 days) − mean(non-event days), Welch t |
| A2 | Pre-release drift | Suppliers return on D−1 | same |
| B1 | Release-day premium | Big2 return on D | mean(D days) − mean(non-event days), Welch t |
| B2 | Release-day premium | Suppliers return on D | same |
| B3 | Release-day premium | KOSPI return on D | same |
| C  | Suppliers react slowly | Suppliers open(D) → close(D) | OLS on S2, HAC (2 lags) |
| D  | Pair trade | SK Hynix r(D) − Samsung r(D) | OLS on S2, HAC (2 lags) |
| E  | Slow 20-day reaction | SK Hynix close(D) → close(D+20) | OLS on S2, HAC (3 lags, overlapping windows) |

Placebo for every test (5,000 draws):
- A, B: the same number of days drawn at random from the non-event days; p = share with |mean − non-event mean| ≥ observed |difference|.
- C, D, E: S2 shuffled across releases; p = share with |slope| ≥ observed |slope|.

## 4. Decision rules

**Discovery pass** (per test): Holm-adjusted p (across all 8 tests) **< 0.10** AND placebo p **< 0.05**.

**Validation** (only for tests that pass discovery; nothing else is run on the validation period):
- one-sided test in the **same direction** as the discovery estimate;
- Holm-adjusted one-sided p (across the survivors) **< 0.05** AND one-sided placebo p **< 0.05**.

**An "edge" = passes both.** Effect sizes are reported in basis points per event. Costs are ignored at this stage.
If nothing passes discovery, the result is "no edge found among A–E" and no validation test is run.

## 5. Known weaknesses (accepted in advance)

- Yahoo open prices for Korean stocks not verified against KRX (matters for C).
- Older releases have no stated time; if some were published before 09:00 KST, part of the reaction is already in the open (C).
- Supplier list chosen with hindsight; survivorship bias.
- Discovery period ~130 releases; small effects may be missed.
