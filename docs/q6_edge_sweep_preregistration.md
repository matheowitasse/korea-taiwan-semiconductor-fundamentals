# Q6 pre-registration — broad edge sweep with the data we already have

Written and committed **2026-09-17, before the Q6 script is written or run.**
Design: AI-era discovery → AI-era validation (same as Q4/Q5). **One family of 14 tests, Holm across all 14.**

## Why a sweep, and how it stays honest

After Q1–Q5 and Q4b found nothing, the author asked to "test everything related". Testing many ideas raises the chance
that one looks good by luck. So: all ideas are written down here first, they form a single family with one Holm
correction, and only discovery survivors are validated on 2025-07 → 2026-09-16.

What has been seen of these specific signals: nothing. Earlier studies used the same price files (Q2 lead-lag from US to
Korea; Q4/Q4b supplier baskets on SOXX < −2% nights; Q5 flows), but none of the signal–return pairs below.
Data fetched for Q6 before committing: past Micron / Nvidia earnings dates (`data/interim/us_earnings_dates.csv`,
counts only checked: 10 each in discovery).

## Data

- Yahoo daily adjusted OHLCV (`data/raw/full_*.parquet`), Q4 cleaning (zero volume or O=H=L=C → missing).
- Baskets (equal-weight of available members):
  - **KR_BIG** Samsung 005930.KS, SK Hynix 000660.KS · **KR_SUP** the 8 Q4 Korean suppliers
  - **TW_BIG** TSMC 2330.TW, MediaTek 2454.TW · **TW_SUP** the 13 Q4 Taiwan suppliers
  - **JP_BIG** Tokyo Electron 8035.T, Advantest 6857.T · **JP_SUP** the 12 Q4 Japan suppliers
  - US: SOXX, MU. Korean market: KOSPI ^KS11.
- Flows (F1): KRX hand downloads (2023+), Naver before 2023 (same construction as Q5).
- Earnings (H1): Micron and Nvidia report dates from Yahoo; all treated as known before the next Korean open.

Notation: day D in the relevant market's own calendar. oc = open→close on D. cc = close(D−1)→close(D).
h5 = open(D+1) → close(D+5).

## The 14 tests

### A. Asia → US same day (Asia closes before the US opens)
Signal = Asian basket cc on date D. Return = US open→close on the same calendar date D (US days only).
Statistic: OLS slope, two-sided, HAC lag 1. Placebo: circular shift of the signal (≥ 20 days).
- **A1** KR_BIG cc → SOXX oc
- **A2** KR_BIG cc → MU oc
- **A3** TW_BIG cc → SOXX oc
- **A4** JP_BIG cc → SOXX oc

### B. Time-series momentum / reversal (5 days)
Signal = basket close(D) / close(D−5) − 1. Return = basket h5.
Statistic: OLS slope, two-sided, HAC lag 5. Placebo: circular shift (≥ 20 days).
- **B1** KR_BIG · **B2** KR_SUP · **B3** TW_SUP · **B4** JP_SUP

### C. Cross-sectional reversal / momentum across all 39 Asian chip names (KR 10, TW 15, JP 14)
Periods on a common calendar grid (week ending Friday for C1, calendar month for C2).
- Formation return per stock = close at end of period t / close at end of period t−1 − 1, minus its country's
  mean formation return (country-neutral).
- Holding return = open of first trading day of period t+1 → close of last trading day of t+1, minus country mean.
- Portfolio = mean holding return of bottom formation quintile − top quintile (needs ≥ 25 stocks with both returns).
- Statistic: mean of the period series, two-sided one-sample t-test. Placebo: shuffle formation returns across stocks
  within each period (5,000 draws), p = share with |mean| ≥ |observed|.
- **C1** weekly (1-week reversal: positive mean = losers beat winners)
- **C2** monthly (1-month)

### E. Calendar
Statistic: difference in means (event days − other days), Welch two-sided t-test.
Placebo: same number of days drawn at random from all days in the period, difference recomputed.
- **E1** KOSPI 200 monthly options expiry (2nd Thursday of the month; if not a trading day, the previous trading
  day): KR_BIG oc on expiry day vs other days.
- **E2** Turn of the month (last trading day + first 3 trading days of each month): KOSPI cc vs other days.

### F. Foreign selling streaks
- **F1** Event = day D on which KR_BIG foreign net buying value (sum over Samsung + SK Hynix) has been negative for
  exactly 5 consecutive days (D−4 … D). Return = KR_BIG h5. Statistic: difference in means (event − all other days),
  Welch two-sided. Placebo: random days as in E.

### H. US chip earnings → Korea
- **H1** Events = Micron and Nvidia reports. Korean day D = first KOSPI trading day with date > US report date.
  x = KR_BIG gap on D (open(D)/close(D−1) − 1), y = KR_BIG oc on D. Statistic: OLS slope (continuation > 0,
  reversal < 0), two-sided, plain OLS. Placebo: same number of days drawn at random from all Korean days in the period.

## Periods and decision rules

- **Discovery:** D (or holding period start) from 2023-01-01 to 2025-06-30.
  Pass = Holm-adjusted p (over the 14 tests) < 0.10 **and** placebo p < 0.05.
- **Validation:** 2025-07-01 → 2026-09-16, **only for survivors.**
  Edge = Holm-adjusted p (over survivors) < 0.05 **and** placebo p < 0.05 **and** same sign as discovery.
- If nothing passes discovery, validation is not run.
- Every test also reports an economic size in bp (A/B/H: mean return in top vs bottom signal quintile; C: mean spread;
  E/F: difference in means), compared with a 0.30% round-trip cost (C: ~4 legs per period → 0.60%). Not decisive.

## Known weaknesses (accepted in advance)

- 14 tests with Holm is strict: the best raw p must be below ~0.007 to pass. Small real effects will be missed.
- A: the US open already reflects Asia via pre-market and ADRs (TSMC ADR), so A mostly tests late US reaction.
- C: 39 names, quintiles of ~8 stocks, country-neutral only; short legs may be hard to borrow in Korea/Taiwan.
- E1: KOSPI 200 weekly options (since 2023) dilute the monthly expiry effect.
- H1: only ~20 events in discovery → low power.
- Supplier lists chosen in 2026 with hindsight; Yahoo opens unverified.
