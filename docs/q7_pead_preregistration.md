# Q7 pre-registration — post-earnings drift in Korean chip stocks

**Finalised on 2026-09-18 (with the fixed-sequence design of section 6).** It is committed **before** the test script is written and before any return
of any stock in the Q7 universe is computed. Data checks done so far used no returns: price existence, zero-volume days,
impossible moves > 31% (data errors), market-cap snapshots, investor-flow coverage, DART operating-profit coverage.

## 1. Hypothesis

After an earnings announcement, Korean chip companies whose stock reacted most positively keep outperforming the market,
and those that reacted most negatively keep underperforming, over the following 1–3 months (post-earnings-announcement
drift, PEAD). Prior research on Korea links PEAD to individual investors trading against the news, strongest on KOSDAQ and in
small firms. Discovery tests are two-sided: a reversal would also be reported.

## 2. Universe

- **List A (decisive):** companies whose DART industry code starts with 261 (semiconductor manufacturing) or 29271
  (semiconductor manufacturing machinery), listed on KOSPI or KOSDAQ at the event date: currently listed
  (`data/interim/dart_companies.csv`) **plus delisted** (`data/interim/kind_delisted.csv`, real delistings only; market
  transfers KOSDAQ ↔ KOSPI are not delistings).
- **Lists B, C, B ∪ C (consistency only):** B = A + Samsung Electronics, Leeno, ISC, Wonik IPS, Jusung Engineering;
  C = A + industry codes starting with 262 (electronic components); B ∪ C. Same rules; ranks computed within each list.
- Codes: `data/interim/q7_universe_codes.csv` (262 stock codes).
- Known weaknesses: industry codes are today's (e.g. SBW Life Sciences → FutureCore); December fiscal year-ends assumed.

## 3. Events

- Source: `data/interim/dart_earnings_disclosures.csv`; original filings only (report names starting with "[" dropped):
  preliminary results (영업(잠정)실적), sales/profit change disclosures (매출액또는손익구조), annual / half-year / quarterly reports.
- One event = the **first** such disclosure of a company; its later earnings disclosures within 30 calendar days belong to
  the same event. List A discovery period: 1,309 events before exclusions.
- **D0** = first trading day (KOSPI calendar) on or after the DART receipt date. DART gives no time of day.
- **Reported quarter** = last completed calendar quarter before the receipt date.
- Exclusions (none uses returns after D0+1):
  1. zero trading volume on any of D0−1, D0, D0+1;
  2. a close-to-close move > 31% (up or down) on any day from D0−2 to D0+61, **unless** the stock is delisted within 10
     trading days after that day (liquidation trading, kept);
  3. fewer than 60 trading days with prices before D0 (recent listings).
  The number of events removed by each rule is reported.

## 4. Measures

- **Prices:** Yahoo adjusted daily prices (`data/raw/q7_yahoo/`) for listed stocks; KRX prices (`data/raw/krx_prices/`)
  for delisted stocks.
- **Market return:** KOSDAQ index (^KQ11) for KOSDAQ stocks, KOSPI (^KS11) for KOSPI stocks. Market = the stock's market in
  the last quarter-end snapshot before D0 ("KOSDAQ GLOBAL" = KOSDAQ); if none, the DART listing market.
- **Surprise 1 — EAR:** stock return minus market return from close(D0−2) to close(D0+1) (days −1, 0, +1).
- **Surprise 2 — SUE:** (operating profit of the reported quarter − same quarter one year earlier) / standard deviation of
  that year-over-year change over the previous 8 quarters (at least 6 required), from `data/interim/dart_sue.csv`
  (consolidated statements preferred; Q4 = annual − 9-month cumulative; DART's current values). Coverage check passed:
  1,058 / 1,309 list-A discovery events (80.8% ≥ 70%) → T3 kept.
- **Ranks:** EAR and SUE ranked within the calendar quarter of D0 (within each list) and scaled to [−0.5, +0.5], so the
  slope is the top-minus-bottom difference.
- **Drift (outcome):** buy-and-hold stock return minus buy-and-hold market return
  - `CAR60`: close(D0+1) → close(D0+61) (60 trading days ≈ 3 months);
  - `CAR20`: close(D0+1) → close(D0+21).
  - Trading halts inside the window: the price stays where it is (a holder cannot sell).
  - Delisting inside the window: last traded price (liquidation trading) is the exit; market return to the same date.
- **Retail against the news (`against`):** individuals' net buying value on D0 and D0+1
  (Naver `individual_net_shares` × close, summed) has the opposite sign of EAR; 1 = against, 0 = otherwise (including zero).
- **Small firm (`small`):** market cap at the last quarter-end snapshot before D0
  (`data/interim/krx_marketcap_quarterly.parquet`) below the median of that quarter's list events; 1 = small.

## 5. Tests (list A; order of testing in section 6)

| ID | Model | Tested coefficient |
|---|---|---|
| T1 (primary) | CAR60 = a + b·rank(EAR) | b |
| T2 | CAR20 = a + b·rank(EAR) | b |
| T3 | CAR60 = a + b·rank(SUE) | b |
| T4 | CAR60 = a + b1·rank(EAR) + b2·against + b3·rank(EAR)·against | b3 |
| T5 | CAR60 = a + b1·rank(EAR) + b2·small + b3·rank(EAR)·small | b3 |

- OLS, standard errors **clustered by calendar month of D0**.
- Placebo: the surprise ranks shuffled **within the same calendar month** (for T4/T5 the interaction is rebuilt with the
  shuffled rank; `against` recomputed from the shuffled EAR sign), 5,000 times; p = share with |coefficient| ≥ observed.

## 6. Periods and decision rules

Fixed-sequence (gatekeeping) design, chosen by the author before any return was computed:

- **Discovery** (D0 from 2023-01-01 to 2025-06-30):
  1. **T1 alone:** pass = two-sided p < 0.10 **and** placebo p < 0.05. No multiple-testing penalty.
  2. **Only if T1 passes:** T2–T5 as one Holm family of 4; pass = Holm-adjusted p < 0.10 **and** placebo p < 0.05.
     If T1 fails, T2–T5 are still computed and reported as **descriptive only** (never "passed").
- **Validation** (D0 from 2025-07-01 to the last date whose 60-day window is complete in the data):
  1. **T1 only if it passed discovery:** edge = same sign as discovery, one-sided p < 0.05 **and** one-sided placebo p < 0.05.
  2. **Only if T1 validates:** T2–T5 tests that passed discovery, Holm over those survivors; edge = same sign, one-sided
     Holm-adjusted p < 0.05 **and** one-sided placebo p < 0.05.
  If T1 fails discovery, validation is not run for any test.
- **No test may be dropped, added or re-ordered after results are seen.** Any such change is exploratory only.
- **Consistency:** for every test that passes, lists B, C and B ∪ C are reported; it is called a *chip-stock* edge only if
  all of them have the same sign.
- Costs and shorting constraints are not part of the pass/fail rule: the question is whether an edge exists for **any**
  market participant (e.g. an institution with low costs and access to borrow). Who can actually use it (retail vs
  institutional, long-only vs long-short) is discussed in the write-up.

## 7. Reported alongside (not decisive)

- Strategy illustration for validated tests only: equal-weight long the top EAR quintile at close(D0+1), hold 60 trading
  days, vs the market index; with and without 0.30% round-trip costs (includes the ~0.2% sell tax); number of positions,
  worst drawdown, share of the result coming from delisted stocks.
- Event counts removed by each exclusion rule; distribution of events by quarter and market.

## Decisions (user, 2026-09-18, before any return was computed)

- Holding period: 60 trading days main (T1), 20 days second (T2).
- T4 (retail against the news) and T5 (size) kept as tests, in a fixed sequence behind T1 (section 6).
- Fixed-sequence design chosen over a single Holm family of 5 (option B, 2026-09-18). The author's suggestion to remove tests
  after negative results was declined as post-hoc; decided instead before running.
- T3 (SUE) kept only if coverage ≥ 70% → coverage 80.8% → kept.
- Universe: A decisive; B, C, B ∪ C as consistency checks.
- The > 31% exclusion applies to moves in either direction; liquidation-trading losses are kept.
