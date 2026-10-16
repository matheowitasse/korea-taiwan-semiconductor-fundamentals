# Q14 — market-hedged implementation (rules fixed before running)

The frozen finding (tag `finding-v1`) is a long-short result. Retail investors cannot short Korean small caps, but they
can short the **index** through futures. This study asks: **does hedging the market turn the long leg into something
with measurable alpha?**

Implementation study on data already used (2023-01 → 2026-08). It cannot change the frozen finding.

## 1. The portfolio

- Long: **top quintile** of the improvement composite (quality + earnings momentum), equal weight, monthly rebalance,
  same liquidity filters as Q10 (market cap ≥ 50 bn KRW, price ≥ 1,000 KRW). Korea is the decisive market
  (KOSPI 200 futures are available through IBKR); Taiwan is reported only.
- Short: the **local index**, sized by one of two pre-specified rules:

| ID | Hedge rule | Rationale |
|---|---|---|
| **H1 rolling beta** | short the index at the portfolio's beta estimated on the **previous 24 months only** (no look-ahead); first hedge starts once 24 months of history exist | what a disciplined investor would actually do |
| **H2 full hedge** | short the index 1:1 | simplest possible rule, no estimation |

- Costs: stock leg 0.30% per unit of turnover (includes the ~0.2% Korean sell tax); futures leg 0.02% per month
  (commission plus roll), charged every month regardless of turnover.

## 2. Decisive test

Mean monthly **hedged return** (net of both cost legs), **one-sided positive**, Newey–West t (3 lags).

**Pass = t > 2 for at least one of H1 / H2 in Korea, Holm-corrected across the two rules**, and the mean remains positive
after costs.

Secondary, reported: the same after controlling for the size and momentum spreads (the market is already hedged);
volatility, Sharpe, maximum drawdown, year-by-year, and the unhedged long-only portfolio for comparison.

## 3. What each outcome means

- **Pass:** there is a construction a retail investor can run (long basket + short index futures) whose return is not
  explained by market exposure — the practical version of the finding.
- **Fail:** the finding stays a long-short research result; the honest conclusion is that retail access to Korean
  small-cap shorting is what stands between the signal and a tradable strategy.

## 4. Known weaknesses

- The hedge uses the cap-weighted index while the portfolio is equal-weight small/mid caps; the residual still contains
  a size mismatch that futures cannot remove.
- Futures margin, rolls and mark-to-market are approximated by a flat monthly cost.
- 44 months remains a short sample; a failure here is weak evidence of absence.
