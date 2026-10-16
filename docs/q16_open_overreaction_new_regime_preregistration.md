# Q16 pre-registration — has the Korean open overreaction come back in the new regime?

Written and committed **2026-09-18, before the Q16 script is written or run.**

## Background

Q2 (`results/q2_explore_overnight.md`) found that before 2023 the Korean open **overshot** the overnight US chip move and
partly reversed during the Korean session: SK Hynix intraday beta −0.12 (t −3.4, placebo p < 0.001), Samsung and KOSPI
similar, strongest after US down nights (SK Hynix +0.43 % open→close, t 3.0). In the AI era 2023-01 → 2025-06 the reversal
was **gone** (placebo p 0.30–0.75), leaving only a weak negative beta for suppliers (−0.07, p 0.15).

Q7b showed the market changed again after mid-2025: KOSPI volatility 18 % → 50 % a year, foreign investors selling
~11.5 trn KRW a month, chip-stock volatility 60 % → 87 %. Higher volatility and forced selling are exactly the conditions
under which opening overreaction is documented in the literature. **Question: is the reversal back in 2025-07 → today?**

Not a fresh data set: Q4b already used the Korean supplier basket's open→close return on the 34 nights with SOXX < −2 %
inside this period. The tests below use all trading days and three more assets, but that overlap is recorded here.

## Data and definitions (identical to Q2 / Q4)

- Yahoo daily (`data/raw/full_*.parquet`), Q4 cleaning (zero volume or O=H=L=C → missing), KOSPI calendar (^KS11).
- **US overnight signal** for Korean day D: SOXX open→close compounded over the US sessions between the previous Korean
  close and D's open.
- **Outcome:** Korean open→close return on D (the reversal is measured after the open, so it is tradable at the open).
- Assets: KOSPI ^KS11, Samsung 005930.KS, SK Hynix 000660.KS, the 8-supplier equal-weight basket (Q4 list).

## Tests (one Holm family of 4)

| ID | Asset | Model |
|---|---|---|
| R1 | KOSPI | open→close = a + b · signal |
| R2 | Samsung | same |
| R3 | SK Hynix | same |
| R4 | Supplier basket | same |

- **b < 0 = reversal** (the open overshot), **b > 0 = continuation**. **Two-sided** tests: the new regime could show either.
- OLS with HAC (lag 1) standard errors. Placebo: circular shift of the signal by ≥ 20 trading days, 5,000 draws, seed 42;
  p = share with |t| ≥ observed.
- **Period: D from 2025-07-01 to 2026-09-16** (one regime, ~300 trading days). No discovery/validation split is possible:
  this is a single-period test of a specific question, and it is labelled that way.
- **Pass = Holm-adjusted p (over the 4 tests) < 0.10 and placebo p < 0.05.**

## Reported alongside (not decisive)

- The same four regressions for 2016-01 → 2022-12 and 2023-01 → 2025-06 (both already seen in Q2), so the three periods
  can be compared in one table.
- Mean open→close return after US down nights (signal < −1 %) and after big down nights (< −2 %) in each period; the
  −2 % column for suppliers repeats Q4/Q4b numbers that have been seen.
- Economic size: the fitted reversal for a −2 % US night, against the 0.30 % round-trip cost assumption.

## Known weaknesses (accepted in advance)

- One regime, ~300 days, and a period partly seen through Q4b (supplier big-down nights).
- A pass would be a **single-period result**, not a validated edge: it could only be confirmed on data after 2026-09-16.
- Yahoo opening prices are unverified against KRX (the same caveat as Q2–Q6); an opening-auction or bid-ask artefact can
  create a spurious reversal, which is why the economic size is compared with costs.
