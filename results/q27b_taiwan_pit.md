# Q27b — Taiwan with a point-in-time universe (delisted companies included)

Robustness version pre-registered in `docs/q27_taiwan_pre_ai_preregistration.md` (section 3). The universe in
each month is the chip companies listed in that month's revenue file; prices are exchange month-end closes,
**unadjusted for dividends**, which biases returns downward for high-yielding stocks.

Chip codes in the archive 2016-2026: **417**; of those, **1** is absent from today's lists. Taiwan's chip
sector is therefore almost survivorship-free over this period, which is itself the main finding of this
robustness run. (An earlier version of this line compared the Taiwanese codes against the Korean universe
file and reported 417; corrected 2026-09-22. No test statistic is affected.)

Price coverage: a median of 348 of the 416 priced chip names appear in any given month-end file; the
"disappearing names" column therefore counts mostly temporary absences (no quote that day), not exits —
only 2 series end permanently before the last month.

```
 delisted_marked_-50%                         window  months  mean_bp     t  p_one_sided  placebo_p  long_only_bp  median_names  disappearing_names_per_month
                False     DECISIVE 2016-01 → 2022-12      83  161.748 3.874        0.000      0.002        88.680           333                        10.390
                False already seen 2023-01 → 2026-08      44  284.769 4.093        0.000      0.000       114.398           384                         1.200
                False                    full sample     127  204.370 5.481        0.000      0.000        97.590           348                         7.200
                 True     DECISIVE 2016-01 → 2022-12      83  184.634 4.487        0.000      0.004        85.787           333                        10.390
                 True already seen 2023-01 → 2026-08      44  313.836 4.462        0.000      0.000       123.054           384                         1.200
                 True                    full sample     127  229.397 6.179        0.000      0.000        98.698           348                         7.200
```

The two panels bracket the treatment of a company's final month: dropped (unobservable) or marked at −50%.
