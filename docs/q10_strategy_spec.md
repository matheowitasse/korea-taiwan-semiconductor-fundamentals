# Q10 — strategy specification (fixed before the backtest)

Turns the validated Q8/Q9 signals into a tradable, long-only portfolio. Written and committed **before** running the
portfolio backtest. No parameter search: every number below is chosen a priori from the earlier results or from
practical constraints, not tuned.

## 1. What the evidence supports

| Signal | Korea (Q8) | Japan (Q9) | Taiwan (Q9) |
|---|---|---|---|
| Quality (operating profit / assets) | confirmed | positive, weak | not available |
| Earnings / revenue momentum | confirmed | positive, weak | **confirmed (revenue, t 4.1)** |
| Composite | confirmed | **confirmed (t 3.5)** | **confirmed (t 2.1)** |
| Value (book / price) | weak | positive, weak | **negative (t −2.1)** |

**Decision (documented now): value is dropped from the strategy.** It failed Korean validation and had the wrong sign in
Taiwan. The strategy signal is the **improvement composite**: the mean of available z-scores of
quality and earnings/revenue momentum (in Taiwan, revenue momentum only).

## 2. Portfolio rules (identical in every market)

- **Universe:** the market's chip-supply-chain list from Q8/Q9.
- **Liquidity filters, applied at formation:** market cap ≥ 50 bn KRW (≈ $37m) or local equivalent — Japan ≥ ¥5 bn,
  Taiwan ≥ NT$1.5 bn — and a share price ≥ the market's penny threshold (KRW 1,000 / ¥100 / NT$10).
- **Holdings:** the **top 20 stocks** by signal, **equal weight**. (20 chosen a priori: large enough to diversify
  single-stock risk, small enough to hold manually.)
- **Rebalance:** monthly, at the last trading day's close; positions held one month.
- **Long only.** No shorting, no leverage, no market timing.
- **Costs charged in the backtest:** Korea 0.30% round trip (incl. ~0.2% sell tax), Japan 0.10%, Taiwan 0.60%
  (incl. 0.3% sell tax), applied to the traded fraction each month.
- **Cash:** fully invested; if fewer than 20 stocks qualify, hold the ones that do.

## 3. What is reported (no thresholds, no selection)

- Monthly and annualised return, volatility, Sharpe, maximum drawdown, hit rate, turnover.
- The same for the local index (KOSPI/KOSDAQ blend, Nikkei, TAIEX) as the benchmark, plus excess return and tracking error.
- Contribution of the biggest winners, and the result with the best 1% of stock-months removed.
- Sensitivity, **reported only, never used to choose**: top 10 / top 30 holdings, and quarterly instead of monthly rebalancing.
- Per-year breakdown, so a bad year is visible rather than hidden in an average.

## 4. Honest framing of this backtest

- It reuses the same data that produced the signals, so it is **not new evidence**; it answers "what would this have
  returned, net of costs?", not "is the effect real?".
- The real test is the live tracking that started 2026-09-21 (`src/q8_live_tracker.py`), extended to Japan and Taiwan.
- Japan and Taiwan universes exclude delisted companies; Korea includes them.
- 2023–2026 is one AI upcycle in all three markets.

## 5. Tradability (to check before any real money)

- **Korea:** available through IBKR since 2026-05-07; ~0.2% sell tax; some KOSDAQ names are thinly traded.
- **Japan:** available through IBKR.
- **Taiwan:** foreign retail access is usually restricted — to be verified in the author's own account; if unavailable,
  Taiwan stays a research result only.
