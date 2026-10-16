
# Q20 pre-registration — do dilution filings predict returns in Korean chip stocks?

Written and committed **2026-09-21, before the Q20 script is written and before any return around these events is
computed.** A new study, independent of the frozen finding (tag `finding-v1`): it uses a different signal (corporate
filings, not fundamentals ranks) and answers a different question.

## 1. Why this hypothesis, and where it comes from

Mechanism-first, motivated by published evidence on Korea rather than by scanning:

- **Convertible bonds (전환사채) are a KOSDAQ phenomenon.** In 1,421 Korean CB private placements 2015–2018, 83.6 % were
  KOSDAQ issues (Korean Journal of Financial Studies, [e-kjfs.org/journal/view.php?number=891]).
- **The announcement itself is positive and largely leaks before the filing:** CAR(−1,+1) = +4.66 % (t 11.99), of which
  day −1 is +2.87 % and day 0 +1.22 % (same source). **A strategy cannot capture that**, so this study starts the return
  at the close of D0+1.
- **Refixing clauses (in ~95 % of issues) reduce the announcement return by 4.2–4.7 pp**, which the authors read as the
  market pricing expected dilution (same source; also MDPI *Sustainability* 12(21):8933, which reports declines of
  2.6–2.7 pp for refixing and a further 6.2–6.3 pp in 2016–2018, and a weaker response for KOSDAQ than KOSPI firms).
- **Longer horizon: underperformance.** For 204 KOSDAQ hybrid-security issuers 2016–2020, stock performance after
  issuance is markedly negative over two- and three-year horizons (China Finance Review International 15(4):737).
- **Refixing adjustments themselves are negative:** day-0 abnormal return −0.27 % (t −3.16), negative from day −20
  through +1 (Korean Journal of Financial Studies, above).

**Hypothesis (direction fixed now): after a dilution filing, the stock underperforms the market over the following
weeks to months**, driven by expected dilution, hedge selling by CB buyers and the refixing ratchet.

**Stated in advance:** the documented underperformance is measured at two to three years. Our windows (20/60/120 trading
days) are a **shorter-horizon extension of that evidence, not a replication.** A null at these horizons would not
contradict the literature.

**Also stated in advance:** if the effect exists it implies shorting small KOSDAQ names, which Q18 showed are largely
unshortable (~8 % of such names are borrowable). A positive result is a research finding, not a tradable strategy.

## 2. Data

- Universe: the 262 chip-supply-chain companies of `data/interim/q7_universe_codes.csv` (lists B ∪ C, delisted included).
- Events: DART major-event filings (`pblntf_ty=B`), 2022-07-01 → today, cached in
  `data/interim/dart_major_events_raw.csv`, classified by report name:
  - **CB** = 전환사채권발행결정 · **RIGHTS** = 유상증자결정 · (counted only: 신주인수권부사채권발행결정, 무상증자결정).
  - Corrections (names starting with "[") are dropped; one event per company per 30 calendar days (Q7 rule).
- Prices, market adjustment, exclusions: exactly as Q7 (`src/q7_pead_test.py`): Yahoo/KRX prices, KOSPI index for
  KOSPI-listed and KOSDAQ index for KOSDAQ-listed stocks, zero-volume and >31 % impossible-move exclusions, ≥ 60 days of
  prior prices, windows complete in the data.
- **D0** = first KOSPI trading day on or after the filing date. Returns start at the **close of D0+1**.

## 3. Tests

| ID | Events | Outcome |
|---|---|---|
| **T1 (primary)** | CB | market-adjusted return, close(D0+1) → close(D0+21) |
| T2 | CB | close(D0+1) → close(D0+61) |
| T3 | CB | close(D0+1) → close(D0+121) |
| T4 | RIGHTS | close(D0+1) → close(D0+21) |
| T5 | RIGHTS | close(D0+1) → close(D0+61) |

- Statistic: mean market-adjusted return, **one-sided, H1: mean < 0**, one-sample t-test with standard errors clustered
  by calendar month of D0.
- Placebo (5,000 draws, seed 42): the same number of event days drawn at random from all stock-days of the same
  universe and period, matched on market (KOSPI/KOSDAQ); p = share of draws with mean ≤ observed.
- **Holm correction across the five tests.** Pass = Holm-adjusted p < 0.05 **and** placebo p < 0.05.
- A test is run only if it has **≥ 40 events**; otherwise it is reported as descriptive with its count, and the Holm
  family shrinks accordingly (decided before seeing any counts).

## 4. Periods

- One period, **2022-07 → today**, because event counts in this universe are limited; no discovery/validation split.
  This is stated as a weakness, not hidden: a pass here is a single-sample result that would need future filings to confirm.
- Reported alongside, not decisive: results split at 2025-07 (the regime break used elsewhere in the project), and
  KOSPI vs KOSDAQ.

## 5. Reported alongside (not decisive)

- Event counts by type and year; the announcement-window return (D0−1 → D0+1) purely to check the published positive
  effect reproduces in our sample; median as well as mean; the share of events with a refixing clause is **not**
  available from the filing list alone and is not used.
- Economic size against the 0.30 % round-trip cost, and the share of event stocks that are proxy-shortable
  (KOSPI 200 / KOSDAQ 150 top-cap proxy from Q18) — i.e. how much of any effect could be traded at all.

## 6. Known weaknesses (accepted in advance)

- Single sample, no out-of-sample window; ~4 years of filings in one universe.
- Horizon mismatch with the published 2–3-year evidence (above).
- Filing-list classification by report name only; the terms of each issue (size, refixing, investor identity) are in the
  filing documents and are not parsed.
- Event clustering: dilution filings cluster in weak markets, which the month-clustered standard errors and the
  market adjustment only partly handle.
- Any short-side result is not implementable for this universe (Q18).
