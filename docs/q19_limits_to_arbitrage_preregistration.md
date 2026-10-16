
# Q19 pre-registration — does the effect live where it cannot be shorted? (limits-to-arbitrage test)

Written and committed **2026-09-21, before the Q19 script is written or run.** Mechanism test of the frozen finding
(tag `finding-v1`): it cannot change the Q8/Q9 verdicts, but it can **falsify the explanation** the paper wants to give.

## Why

Q18 found that the losers the signal identifies are mostly unshortable (a median of 4 of 47 bottom-quintile names are
KOSPI 200 / KOSDAQ 150 members), and that the short-selling ban did not create the short-leg alpha. The paper's proposed
story is Miller (1977) / limits to arbitrage: overpriced small caps stay overpriced because pessimists cannot act.

**That story makes a testable prediction, and this is it.** If it is right, the signal's power should be concentrated in
stocks that cannot be shorted. If shortable and unshortable stocks behave the same, the story is wrong and the paper must
describe the effect without it.

## Data

- Korean universe, signals and monthly returns exactly as in Q8 (`src/q8_multifactor.py`, list B ∪ C, 2023-01 → 2026-08).
- **Shortable proxy** as in Q18: from each KRX quarter-end snapshot, top 200 by market cap within KOSPI and top 150
  within KOSDAQ; applied to the months following that snapshot. Approximate (the real indices add sector and liquidity
  screens); the study is labelled a proxy test and will be re-run if real constituent lists are obtained.
- Ban months (2023-11-06 → 2025-03-30) are months when even proxy-shortable names could not be shorted.

## Tests

**T1 (primary).** Pooled monthly panel of stock returns on the composite signal rank (centred to [−0.5, +0.5] within
each month), a `shortable` dummy, and their interaction, with month fixed effects and standard errors clustered by
month:

    ret(i, t+1) = month FE + b1 · rank(i, t) + b2 · shortable(i, t) + b3 · rank(i, t) × shortable(i, t)

- **Prediction of the limits-to-arbitrage story: b3 < 0** (the signal works *less* well among shortable names).
- **One-sided, H1: b3 < 0. Pass = p < 0.05** and a placebo p < 0.05 (shortable labels shuffled within each month,
  5,000 draws, keeping the number of shortable names per month fixed).

**T2 (secondary, reported).** Quintile spreads computed separately inside the shortable and unshortable groups
(each needs ≥ 25 stocks in a month), with HAC(3) t-statistics, plus the difference between the two spreads.

**T3 (secondary, reported).** Among proxy-shortable names only, the spread in ban months vs non-ban months. The story
predicts a larger spread while shorting was impossible; Q18 found the opposite at universe level, so this is a check on
consistency, not a claim.

## Interpretation, fixed now

- **T1 passes** → the paper may say the effect is concentrated where arbitrage is blocked, with the proxy caveat.
- **T1 fails and b3 ≈ 0** → the unshortability story is **not** supported; the paper reports the effect without that
  explanation and says so plainly.
- **b3 > 0 significantly** → the opposite of the story; it would have to be reported as such.
- Either way the Q8/Q9 finding itself is untouched.

## Known weaknesses (accepted in advance)

- Market-cap proxy for index membership; no borrow-fee or borrow-availability data.
- `shortable` is strongly correlated with size, and size is itself a return driver; T1 therefore also reports a version
  with log market cap and its interaction with the rank added as controls. If the interaction loses significance once
  size is controlled, that is reported as the main answer, because size is the more parsimonious explanation.
- 44 months, one AI upcycle, one market.
