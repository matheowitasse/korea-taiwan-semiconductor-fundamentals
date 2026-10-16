
# Q26 spec — what do transaction costs do to the spread?

Written and committed **2026-09-21, before the Q26 script is written or run.** Implementation work on the frozen
finding: it cannot change what the spread is, only what is left of it after trading.

## Why now

Costs have been carried through the project as a flat assumption (0.30% per unit of turnover). That was always a
placeholder, and it is now the last unexamined obstacle between the measured effect and a tradable strategy: Q24 showed
eligibility does not bind after March 2025, and Q25 showed the short side carries real short interest. What remains is
whether the spread survives spreads, taxes, borrow fees and market impact in companies whose median market
capitalisation is around KRW 90–160 bn.

## Cost components, all fixed here

| Component | Treatment |
|---|---|
| **Bid–ask spread** | Estimated per stock-month from daily highs and lows with the Corwin–Schultz (2012) estimator; negative estimates set to zero; we pay **half the spread** per trade |
| **Commission** | 5 bp per trade, each way (institutional Korean rate, stated as an assumption) |
| **Securities transaction tax** | 20 bp on **sells only**, applied to the long leg's sells and the short leg's opening sales (the current Korean rate on KOSDAQ; stated as an assumption and varied in the sensitivity table) |
| **Borrow fee (short leg only)** | 1%, 3% and 5% a year, charged on the short position's value while held |
| **Market impact** | Amihud-style linear model: impact (in return units) = λ × (order value), with λ estimated per stock-month as the trailing-12-month mean of \|return\| / traded value. Orders are sized from an assumed fund size |
| **Fund size** | USD 1m, 10m, 50m and 200m, converted at 1,300 KRW/USD, equal-weighted across the quintile |

## What is computed

1. **Monthly turnover** of the long and short legs of the quintile portfolio (fraction of the portfolio replaced).
2. **Gross spread** (as reported elsewhere), and **net spread** after each cost component, cumulatively, so the table
   shows which component does the damage.
3. **Net alpha** after the market, size and momentum controls, with Newey–West (3 lags) t-statistics, per fund size.
4. **Break-even fund size**: the size at which net alpha crosses zero, by interpolation.
5. The same for the **long leg alone** (no borrow fee, no short sales), since that is the form most investors could use.

Period: 2023-01 → 2026-08 for the headline table (the frozen-finding window), and 2016-11 → 2026-08 where the extended
history allows it.

## Reading fixed in advance

- **Net alpha positive with t > 2 at USD 10m** → the effect survives realistic costs at small scale; the paper may
  describe it as implementable at that size, with the assumptions listed.
- **Net alpha positive only below USD 10m** → implementable only at very small scale; say so with the break-even size.
- **Net alpha not distinguishable from zero at any size** → the effect is not tradable after costs, and that becomes the
  paper's conclusion.

## Known weaknesses (accepted in advance)

- Corwin–Schultz is an estimator from daily data, not observed quotes; it is known to be noisy for illiquid stocks and
  can be biased when overnight returns are large.
- The linear impact model is a convention, not a measurement; real impact is concave and depends on participation rate.
- Commission, tax and borrow-fee levels are assumptions; the sensitivity table varies them.
- Korean price limits (±30%) and the uptick rule for short sales are ignored; both would raise costs in stressed months.
