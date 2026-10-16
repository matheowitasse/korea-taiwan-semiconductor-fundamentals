
# Q21 spec — is the effect just illiquidity? (robustness, fixed before running)

Written and committed **2026-09-21, before the Q21 script is written or run.** Robustness on data already used: it
cannot change the Q8/Q9 verdicts. It exists because the objection below is the first one a referee will raise, and
because our own value-weighted robustness result (composite +67 bp, t 0.55) already points at it.

## The objection

The universe is small and mid-cap KOSDAQ companies. Equal-weight quintiles in illiquid names can manufacture spreads
through bid–ask bounce, price-limit effects and an illiquidity premium, none of which require any fundamental
information. If the effect is concentrated in the least liquid names and disappears among the liquid ones, the honest
reading is "an illiquidity-related pattern", not "fundamentals predict returns".

## Measures (computed per stock-month, from data already in the repository)

- **Amihud illiquidity**: mean over the previous 12 months of |daily return| / (close × volume), scaled by 1e6; at
  least 120 valid days required.
- **Turnover**: median over the previous 12 months of (close × volume) / market capitalisation (Korea only; Taiwan has
  no market-cap series in the repository).
- **Price level**: month-end close.
- Liquidity groups are terciles of Amihud within each month (most liquid / middle / least liquid).

## What is reported

| ID | Question |
|---|---|
| R1 | Long–short spread computed **inside each Amihud tercile** (Korea; see note) |
| R2 | Alpha after adding an **illiquidity factor** (long–short of the Amihud rank, built in the same universe) to the existing market/size/momentum controls |
| R3 | Spread excluding the smallest 20% of the universe by market capitalisation (Korea) |
| R4 | Spread excluding stocks priced below KRW 1,000 at the month end (Korea) |
| R5 | The known value-weighted result, repeated next to the others for comparison |

Statistics as elsewhere: mean monthly return in basis points, Newey–West t (3 lags); alphas from the same regression
design as `src/q10_risk_adjustment.py`.

## Reading fixed in advance

- **Survives** if the spread stays positive with t > 2 in the **most liquid tercile** and the alpha stays positive with
  t > 2 after the illiquidity factor is added.
- **Partially survives** if it holds in the two more liquid terciles but not the least liquid, or vice versa: report
  which, and restrict the paper's claim to that part of the universe.
- **Fails** if the effect is confined to the least liquid tercile or disappears once illiquidity is controlled. In that
  case the paper says so in the abstract, not only in a robustness table.

Nothing here is a new hypothesis test; no pass/fail label is attached to the finding itself. The purpose is to state
which reading of the existing result the data supports.

**Note added before running (2026-09-21):** the cached Taiwanese price files contain closing prices only, with no
volume, so Amihud cannot be computed there without re-downloading the series. R1 and R2 are therefore **Korea-only**
in this run; Taiwan is left pending rather than silently dropped, and will be added if the volume series are downloaded.

## Known weaknesses

- Amihud from daily Yahoo data, not intraday spreads; it is a proxy for trading cost, not a measurement of it.
- Market caps come from quarter-end KRX snapshots (2022-06 onward), so the market-cap screens apply only to the
  existing 44-month sample.
- Terciles of ~50 names each in Korea and ~140 in Taiwan; quintile spreads inside a tercile are noisy by construction.
