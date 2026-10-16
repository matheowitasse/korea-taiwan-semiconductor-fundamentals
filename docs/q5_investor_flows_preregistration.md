# Q5 pre-registration — do foreign / retail investor flows predict Korean chip stock returns?

Written 2026-09-16 and **committed before the test script is written or run.**
Design: AI-era discovery → AI-era validation (same as Q4).

What has been seen of the flow data before committing this — data checks only, **no flow data has been joined to returns**:
- first/last rows of SK Hynix Naver flows (download format); Naver volume vs Yahoo volume; Naver close vs Yahoo close;
- correlation of Naver (shares × close) vs KRX net buying value for all 10 stocks, 2023-01 → 2026-09 (0.91–0.9999),
  and the dates with the largest disagreement for Wonik IPS (2023-12-01) and HPSP (several days in 2023), which look
  like block trades counted by KRX but not by Naver.

## 1. Idea in plain words

Korean exchange data tells us every day who bought and who sold: foreigners, institutions and individuals (retail).
Two well-known stories:
- **Foreigners are "informed" or move prices slowly**: when they buy a lot today, the stock keeps rising for a few days.
- **Retail chases attention**: when individuals pile into a stock, it tends to do worse afterwards.

And one question specific to this project: when US chips sell off overnight and foreigners dump Korean chip stocks,
is that selling **panic that reverses** or **information that continues**? (User: no strong prior. A first answer
"it reverses" was withdrawn the same evening, before any test was written or run.)

The final numbers for day D are published after the Korean close, so the earliest realistic trade is at the **open of
D+1**. Every test below starts its return at that open — no look-ahead.

## 2. Data

- **Flows, 2023-01-02 → 2026-09-16 (all tests): official KRX data**, downloaded by hand from KRX Data Marketplace
  and stored in `data/raw/krx_manual/` (imported and identified with `src/krx_manual_import.py`).
  - Stocks: page [12009] "Trading by investor (individual issue)", daily, trading value, net buying, details.
    10 stocks × 2 files, complete for the period.
  - Market (T8): page [12008] "Trading by investor", daily, KOSPI, trading value, net buying (2 files, to be
    downloaded before the script is run).
  - **Foreign** = "Foreigners" + "Other foreigners". **Individual** = "Individuals".
- **Naver flows** (`src/naver_download_flows.py`) are used only for the 2016–2022 context run, and for daily
  close × volume (see definitions). Naver and KRX agree to correlation ≥ 0.99 except on block-trade days.
- **Prices:** Yahoo daily (`data/raw/full_*.parquet`), same cleaning as Q4 (zero volume or O=H=L=C → missing).
- **Stocks:** BIG2 = Samsung 005930, SK Hynix 000660. SUP = the 8 Korean suppliers of Q4
  (Hanmi Semi 042700, DB HiTek 000990, Leeno 058470, ISC 095340, Wonik IPS 240810, Jusung Eng 036930,
  Eugene Tech 084370, HPSP 403870). Market = KOSPI (^KS11).

## 3. Definitions

- **Flow ratio** of investor group g, stock i, day D: KRX net buying value / (Naver close × Naver volume) on D,
  clipped to [−1, 1] (block trades outside the regular session can push it beyond ±1). Days with no volume → missing.
- **Flow signal** z(g, i, D): (flow ratio on D − mean of the previous 60 trading days) / std of the previous 60 days
  (D itself excluded; needs ≥ 40 valid days). Basket signal = mean of available members' z.
  The 60-day window may reach back before 2023-01-02 only through Naver data for the same stock
  (shares × close), so that the first discovery days have a signal.
- **KOSPI signal (T8):** KRX KOSPI foreign net buying value on D (KRW, not scaled), z-scored the same way
  (60-day window reaching before 2023-01-02 through Naver KOSPI market-wide values if needed).
- **Returns** (Yahoo; basket = equal-weight mean of available members):
  - **h1** = open(D+1) → close(D+1)
  - **h5** = open(D+1) → close(D+5)
- **Big-down night:** SOXX overnight signal of Q4 for Korean day D < −2%.

## 4. The 8 tests (complete family)

| ID | Signal on D | Return | Expected sign (not used for the test) |
|---|---|---|---|
| T1 | BIG2 foreign z | h1 | + |
| T2 | BIG2 foreign z | h5 | + |
| T3 | SUP foreign z | h1 | + |
| T4 | SUP foreign z | h5 | + |
| T5 | BIG2 individual z | h5 | − |
| T6 | SUP individual z | h5 | − |
| T7 | BIG2 foreign z, **big-down days D only** | h5 | ? (no prior) |
| T8 | KOSPI foreign z | KOSPI h5 | + |

- Statistic: slope of return ~ signal (OLS). **Two-sided** for all tests, including T7.
  Standard errors: Newey-West HAC, lag 5 (overlapping h5 returns). T7 uses plain OLS (events are sparse).
- Placebo (5,000 draws): circularly shift the signal series by a random offset of ≥ 20 trading days within the period
  (keeps the signal's own autocorrelation), refit; p = share of draws with |t| ≥ |observed t|.
  T7: draw the same number of days at random from all days in the period instead.
- Also reported, not decisive: mean h1/h5 return in the top vs bottom quintile of the signal (bp), compared with a
  0.30% round-trip cost.

## 5. Periods and decision rules

- **Discovery:** D from 2023-01-01 to 2025-06-30. Pass = Holm-adjusted p (over the 8 tests) < 0.10 **and** placebo p < 0.05.
- **Validation:** D from 2025-07-01 to 2026-09-16 (last D such that D+5 exists), **only for tests that pass discovery**.
  Edge = Holm-adjusted p (over survivors) < 0.05 **and** placebo p < 0.05 **and** same sign as discovery.
- If nothing passes discovery, validation is not run, and 2025-07+ stays untouched for these tests.
- 2016–2022 is run afterwards on Naver data as context only (clearly labelled), never as a filter.

## 6. Robustness planned in advance (not decisive)

- Re-run any passing test with the largest 1% of |flow ratio| days removed (block trades, index rebalancing).
- Re-run any passing test on Naver flows instead of KRX.

## 7. Known weaknesses (accepted in advance)

- KRX files downloaded by hand (checked against Naver, but no second official copy).
- Block trades included (KRX counts them); they are rare but can dominate a small stock's day.
- Supplier list chosen in 2026 with hindsight (same as Q4).
- Samsung and SK Hynix flows are strongly driven by the same foreign index-fund flows → T1/T2 and T8 are not independent.
- T7 has few events (~55 big-down nights in discovery) → low power.
- Yahoo open prices unverified (same caveat as Q2–Q4).
