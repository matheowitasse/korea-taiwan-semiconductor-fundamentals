# Q18 pre-registration — the Korean short-selling ban, and a short leg you could actually trade

Written and committed **2026-09-21, before the Q18 script is written or run.** Implementation / mechanism work on the
frozen finding (tag `finding-v1`): it does **not** re-run or re-tune the decisive Q8/Q9 tests, and it
cannot change what they found. It can change what the finding **means** and whether it is tradable.

## Background

Q13 split the Korean spread into a long leg (+196 bp/month, alpha +137 bp, t 2.86) and a short leg (+182 bp/month, alpha
+144 bp, t 4.20). Korea **banned short selling from 2023-11-06 to 2025-03-30** — about 17 of the 44 sample months — and
since the 2025-03-31 reinstatement short selling is allowed (retail on the same terms as institutions) but **only in
KOSPI 200 and KOSDAQ 150 constituents**. Taiwan had no ban in the period. Miller (1977): when pessimists cannot short,
overvalued stocks stay overvalued, which would inflate a short leg exactly during a ban.

## Part A — mechanism: is the short-leg alpha concentrated in the ban months?

- Monthly leg returns from Q13's construction, unchanged (`src/q13_leg_decomposition.py` / `src/q8_multifactor.py`).
- Sub-periods by month end: **pre-ban** 2023-01 → 2023-10 (10 months), **ban** 2023-11 → 2025-03 (17 months),
  **post-ban** 2025-04 → 2026-08 (17 months).
- For Korea and for **Taiwan as the control** (same dates, no ban there): mean, HAC(3) t, and risk-adjusted alpha
  (local index, momentum spread, size spread where caps exist) for the long leg, the short leg and the spread.
- **Formal comparison:** difference in the short-leg monthly mean between ban months and all other months, Welch
  two-sided, in Korea and in Taiwan.
- **Interpretation fixed now:**
  - Korea's difference significant (p < 0.05) **and** Taiwan's not → the short leg is at least partly a ban artefact;
    the claim narrows to "the effect exists, but a tradable share of it came from months when shorting was impossible".
  - Neither significant → no evidence the ban drove it; the finding stands as is.
  - Both significant → a common shock, not the ban; report as such.
  - With 17 ban months a null is weak evidence; sub-period estimates are noisy and are reported with that caveat.

## Part B — implementation: a short leg restricted to shortable names

- **Shortable proxy (real index membership is not in the data):** from the KRX quarter-end snapshots
  (`data/interim/krx_marketcap_quarterly.parquet`, all listed issues), at each snapshot rank issues by market cap
  **within their market**; a universe stock counts as shortable in the months following that snapshot if it ranks
  **top 200 on KOSPI** or **top 150 on KOSDAQ**. This approximates KOSPI 200 / KOSDAQ 150, which also use sector and
  liquidity screens — so membership is approximate, and the whole part is labelled a proxy. It will be re-run if the author
  downloads real constituent lists.
- **Allowed months:** every month except 2023-11 → 2025-03 (the ban). Pre-ban months count as allowed, since the
  partial resumption from 2021-05 covered exactly these index constituents.
- **Implementable short leg** for an allowed month = universe average return − average return of the bottom-quintile
  stocks **that are shortable**. Quintiles are formed on the full universe as before; only the traded names are filtered.
  Months with fewer than 5 shortable bottom-quintile names are skipped and counted.
- Reported: share of bottom-quintile names that are shortable per month; implementable short-leg mean, HAC(3) t and alpha;
  the same for the long leg (unrestricted, for comparison); and the combined long + implementable-short portfolio.
- **What counts as "survives":** implementable short-leg **alpha t > 2** over the allowed months, with the same sign as
  the full short leg. Below that, the tradable form of the finding is unproven — it is not a new failure of the finding.
- Costs are reported, not decisive: 0.30 % per unit of turnover plus an assumed 1 % annual borrow fee on the short leg.

## Known weaknesses (accepted in advance)

- Market-cap proxy for index membership; no borrow availability or fee data (the author checks IBKR separately).
- Allowed months in two disconnected blocks (10 pre-ban + 17 post-ban) → ~27 months, low power.
- Sub-period splitting of 44 months is descriptive by nature; this study locates effects, it does not establish new ones.
- Taiwan is an imperfect control: no ban, but a different market, universe and sector mix.
