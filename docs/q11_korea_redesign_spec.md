# Q11 — Korea implementation redesign (rules fixed before running)

Q10 showed the problem: the **signal** keeps a large return after controlling for market, size and momentum
(+287 bp/month, t 3.59 in Korea), but the **long-only top-20 portfolio** does not (+154 bp/month, t 1.37). Most of the
signal's value sits in avoiding the worst-ranked stocks, which a 20-stock long-only portfolio cannot express.

This study asks one question: **is there a long-only construction a retail investor can run that keeps a positive
risk-adjusted return?** Two designs, fixed now, no parameter search.

## 1. Designs (Korea only, universe and signal unchanged from Q8/Q10)

Signal = improvement composite (mean z-score of quality and earnings momentum), monthly, same liquidity filters
(market cap ≥ 50 bn KRW, price ≥ 1,000 KRW), same costs (0.30% per unit of turnover, includes the ~0.2% sell tax).

| ID | Design | Rationale |
|---|---|---|
| **D1 avoidance** | Equal-weight **all qualifying stocks except the bottom 40% by signal**, rebalanced monthly | Captures "do not own the bad ones", which is where the spread's value sits |
| **D2 momentum-neutral** | Split the universe into **3 momentum terciles** (12-1, skipping the latest month); inside each tercile take the **top 7 by signal**; hold all ~21 equal weight | Removes the momentum exposure that explained most of the Q10 portfolio's excess return |

Reference portfolios, reported but not decisive: the Q10 top-20 design, the equal-weight universe, and the KOSPI index.

## 2. Decisive statistic

For each design: monthly net-of-cost return regressed on
(a) the local index, (b) the universe size spread (small − big quintiles), (c) the universe momentum spread
(12-1 winners − losers quintiles), HAC standard errors (3 lags).

**The alpha (intercept) is the decisive number**, one-sided positive.

**Pass = Holm-adjusted one-sided p < 0.10 across the two designs, and alpha > 0 after costs.**

If neither design passes, the honest conclusion is: *a real cross-sectional signal that a long-only retail investor in
Korea cannot harvest* — which is reported as such, and the live tracking continues on the signal, not on a strategy.

## 3. Also reported (never used to choose)

Annualised return, volatility, Sharpe, maximum drawdown, turnover, tracking error versus KOSPI, year-by-year returns
including 2024, and the number of holdings.

## 4. Status of this evidence

This reuses the 2023-01 → 2026-08 Korean data that produced the signal, so it is an **implementation study, not new
evidence**. Whatever passes here still has to prove itself in the live tracking that started 2026-09-21.
