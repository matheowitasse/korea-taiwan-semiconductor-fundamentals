# Q27 pre-registration — does the Taiwanese effect exist before the AI era?

Written and committed **2026-09-22, before any Taiwanese data earlier than 2022-06 was downloaded** and before any
Taiwanese return before 2023-01 was computed. Mirrors Q22, which extended Korea back to 2016-11 and found the effect
present outside the AI boom.

## 1. Why

The frozen finding rests on Korea (118 months, 2016-11 → 2026-08) and Taiwan (44 months, all inside the AI boom).
The open objection is that the pre-boom evidence comes from a single market. Taiwan's monthly revenue disclosures and
month-end valuation files are archived back to at least 2013, so the same test can be run on years nobody has examined.

## 2. Decisive test

- **Window: 2016-01 → 2022-12** (84 months, never examined; includes the 2018–19 semiconductor downturn and the 2022
  selloff). The window is set by data availability and by the Korean extension's start, not by any result.
- **Signal:** monthly revenue momentum, exactly as in Q9 — latest published monthly revenue versus the same month a year
  earlier, in per cent, ranked cross-sectionally each month end. At a month end the latest published figure is the
  previous month's, matching Taiwan's disclosure deadline of the 10th.
- **Portfolios:** equal-weight quintiles, held one month; statistic = mean monthly long–short return (top − bottom),
  Newey–West standard errors (3 lags), **one-sided positive** (direction fixed by the existing results).
- **Placebo:** revenue-momentum values shuffled across stocks within each month, 500 draws.
- **Pass = t > 2 and one-sided placebo p < 0.05.** One test, run once.

## 3. Universe and prices

- **Universe (decisive):** companies in TWSE/TPEx industry codes 24 (semiconductors) and 28 (electronic components), as
  in Q9. Prices: Yahoo adjusted daily closes, so returns include dividends and capital changes.
  This universe contains only companies listed today → **survivorship bias**, which removes the worst outcomes from the
  bottom quintile and therefore works **against** the hypothesis.
- **Survivorship robustness (reported, not decisive):** a point-in-time universe rebuilt from each month's own revenue
  file, which carries the industry label and includes companies that later delisted, priced with the exchange's
  all-issues month-end file. Those prices are **unadjusted for dividends**, which biases returns downward for
  high-yielding stocks; the two versions therefore bracket the truth rather than either being clean.

## 4. Also reported (not decisive)

- The same statistic over 2023-01 → 2026-08 (already seen in Q9) and over the full 2016 → 2026 sample.
- Risk-adjusted alpha over the decisive window (local index and a momentum spread built inside the universe).
- Number of scored names per month; months with fewer than 30 are dropped.
- The value factor (book-to-price) over the decisive window, for comparison with its negative AI-era result.

## 5. What each outcome means

- **Pass:** the effect exists before the AI boom in **two** markets with different disclosure regimes and different
  signals. This closes the main remaining objection to the paper.
- **Fail:** the Taiwanese result stays boom-period evidence, Korea remains the only pre-AI market, and the paper says so.

## 6. Known weaknesses (accepted in advance)

- The decisive universe is survivorship-affected; the robustness version fixes that but loses dividend adjustment.
- Industry classification is today's for the decisive universe, and the filing month's for the robustness version.
- Taiwan's revenue signal has no Korean equivalent, so this extends the cross-market evidence rather than replicating a
  single measure.
