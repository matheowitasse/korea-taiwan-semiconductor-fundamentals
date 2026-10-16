
# Q29 pre-registration — the standard-methods checks a referee will ask for

Written and committed **2026-10-15, before any Q29 code exists.** Purpose: take the paper from working paper to
journal submission. Every test below uses data the project has already examined, so none of it is *new* evidence for
the finding; what is new is the estimator. The point of fixing the specifications in advance is that the paper can
report each one as run, with no searching over controls, windows or definitions. **A failure is reported in the paper
as a failure** and the claim is narrowed accordingly.

Signals and universes are exactly those of the paper: the fundamentals-improvement signal (z-mean of quality and SUE)
on the Korean extended universe (`src/q22_extended_history.py`), revenue momentum on the Taiwanese universe
(`src/q10_strategy_backtest.taiwan`). Characteristics are winsorised z-scores within market and month.

## 1. Decisive tests (one-sided, positive; each must clear t > 2 with Newey–West, 3 lags)

| ID | Test | Window |
|---|---|---|
| **F1** | **Fama–MacBeth, Korea.** Monthly cross-sectional OLS of next-month return on the signal z, with 12-1 price momentum z and prior-month return z (short-term reversal) as controls. Statistic: time-series mean of the signal coefficient. | 2016-11 → 2026-08 |
| **F2** | **Fama–MacBeth, Taiwan.** Same specification with revenue momentum as the signal. | 2016-01 → 2026-08 |
| **A1** | **Extended factor alpha, Korea.** The long–short spread regressed on the KOSPI return, the in-universe momentum spread, and three market-wide Korean factors built from all listed companies *excluding the chip universe*: profitability (KOR-QMJ-ex-chip, already built in Q23), investment (low minus high total-asset growth over four quarters, equal-weight quintile spread), and momentum (12-1, equal-weight quintile spread). | 2016-12 → 2026-08 (start set by KOR-QMJ) |
| **U1** | **Rule-only universe, Korea.** The long–short spread on the universe defined only by DART industry codes 261, 29271 and 262 — i.e. without the five companies added by name (Samsung Electronics, Leeno, ISC, Wonik IPS, Jusung Engineering). | 2016-11 → 2026-08 |

Holm across F1, F2, A1, U1 (family of four) is reported alongside the individual t-statistics.

## 2. Secondary (reported with the same bar, not decisive — short windows)

| ID | Test | Window |
|---|---|---|
| F3 | F1 plus log market capitalisation and book-to-market (book equity / market cap) as controls; market caps exist only from the 2022-06 KRX snapshot. | 2022-07 → 2026-08 |
| F4 | F2 plus book-to-market (1 / price-to-book; TWSE-listed names only — TPEx has no valuation file). | 2016-01 → 2026-08 |

## 3. Descriptive (no pass/fail)

- **S1 Skip a month:** signal formed at month end *t*, return over *t+1 → t+2*. Measures how fast the information decays
  and guards against a result that lives in the first month's microstructure.
- **D1 Performance statistics** of the long–short in both markets over the full samples: annualised mean, volatility,
  Sharpe ratio, skewness, maximum drawdown, share of positive months, and the spread in each calendar year.
- **D2 Summary statistics** for the paper's data section: names per month, the distribution of each characteristic,
  and the correlation between quality and earnings momentum.

## 4. What changes in the paper

- Pass → the result goes in a new robustness table; the claim is unchanged.
- F1 or F2 fails → the paper states that the effect is a portfolio-sort result that the regression estimator does
  not confirm, and discusses why (non-linearity in the extremes is the usual reason).
- A1 fails → the claim is narrowed to "not explained by the in-universe controls", and the factor that absorbs it is
  named.
- U1 fails → the paper must say that the Korean result depends on hand-added names. This is the most consequential of
  the four.

## 5. Not done, and why

- **Value-weighted spreads over the full samples:** Korean market caps begin in 2022-06 and Taiwan has none, so the
  44-month value-weighted result of Q21 (+517 bp, t 1.91) remains the only one; stated as a limitation.
- **A full local Fama–French five-factor set:** market-wide book equity and pre-2022 market caps are not in the
  project's data. A1 covers profitability, investment and momentum; size and value enter through F3/F4 where the data
  allow.
