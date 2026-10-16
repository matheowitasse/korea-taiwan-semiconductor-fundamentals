
# Q23 spec — is the chip-sector effect distinct from a market-wide Korean quality premium?

Written and committed **2026-09-21, before the Q23 data are built and before any market-wide factor return is
computed.** This is the benchmark test the paper currently lacks: profitability and quality premia are documented in
many markets (Novy-Marx 2013; Fama and French 2015; Asness, Frazzini and Pedersen 2019, covering 24 countries), so a
referee will ask whether our result is simply that premium showing up inside one sector.

AQR's Quality-Minus-Junk country files cover developed markets only and **do not include Korea**; Ken French's
international library does not cover Korea either. There is therefore no off-the-shelf benchmark, and we build one.

## 1. What is built

**KOR-QMJ**: a market-wide Korean quality factor, constructed exactly like our sector signal so that the comparison is
like-for-like.

- **Universe:** every company in the DART register listed on KOSPI or KOSDAQ (`corp_cls` Y or K), with a usable price
  series and the required accounts.
- **Signal:** operating profit over the trailing four quarters ÷ total assets (our "quality"), z-scored
  cross-sectionally each month end, winsorised at ±3.
- **Portfolios:** equal-weight quintiles, held one month; the factor return is top minus bottom quintile.
- **Point-in-time rule:** statutory deadlines, as in Q22 (quarterly/half-year usable 45 days after quarter end, annual
  90 days after year end).
- **KOR-QMJ-ex-chip:** the same factor excluding the 285 companies of the chip universe, so that the control does not
  contain the stocks being explained. **This is the version used in the decisive regression.**

## 2. Tests

| ID | Regression | Question |
|---|---|---|
| **C1 (decisive)** | chip long–short spread ~ index + size + momentum + **KOR-QMJ-ex-chip** | Does the sector effect survive a market-wide quality control? |
| C2 | same, with KOR-QMJ (including chip names) | Sensitivity to the exclusion |
| C3 | chip spread ~ KOR-QMJ-ex-chip alone | How much of the spread is market-wide quality? |
| C4 | correlation of the two series; KOR-QMJ's own mean and t over the same months | Is the market-wide premium itself present in this period? |

Newey–West standard errors (3 lags), Korea, 2023-01 → 2026-08 (the frozen-finding window), and — if Q22's extended
history is available in time — 2015-01 → 2026-08 as well.

## 3. Reading fixed in advance

- **C1 alpha positive with t > 2** → the chip-sector effect is not explained by market-wide Korean quality; this is the
  paper's strongest robustness result and belongs in the abstract.
- **C1 alpha positive but t < 2** → the two cannot be separated in this sample; the paper says the sector effect is
  consistent with, and not distinguishable from, the market-wide premium.
- **C1 alpha near zero** → the honest conclusion is that we have documented the Korean quality premium inside a sector.
  The paper is rewritten around that, and the contribution becomes the protocol plus the implementability evidence.

No pass/fail label attaches to the frozen finding itself; this changes the interpretation, not the measurement.

## 4. Known weaknesses (accepted in advance)

- The market-wide universe uses today's listing register, so companies delisted before the download are missing outside
  the chip sector: **KOR-QMJ is survivorship-biased upward**, and a biased control is a conservative control here
  (it makes C1 harder to pass, not easier).
- One accounting definition of quality (operating profit / assets); Asness et al. use a broader composite.
- Prices from Yahoo for ~2,600 names; coverage and data errors are screened with the same rules as elsewhere
  (zero volume, >31% impossible moves, minimum history).
- Korean financial statements are current (restated) values.
