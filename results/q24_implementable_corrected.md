# Q24 — The implementable short leg, with eligibility applied by regime

**Supersedes Q18 Part B.** That test restricted the short leg to KOSPI 200 / KOSDAQ 150 members in every
non-ban month, based on an incorrect reading of the rules. Korean short selling was limited to index
constituents from 2021-05 to 2023-11-05, banned to 2025-03-30, and **fully reinstated for all listed stocks**
on 2025-03-31. Q18 Part A (the ban diagnostic) used the correct dates and is unaffected.

## Eligible names and the short leg, by regime

```
      regime  months  months_tradable  median_eligible_names  median_bottom_names  short_leg_impl_bp    t
all eligible      18               18                  48.00                48.00             286.28 4.07
         ban      16                0                   0.00                46.00                NaN  NaN
  index-only      10                7                   9.00                44.00             270.62 3.15
```

## Tradable months only

```
                                      portfolio  months  mean_bp    t  alpha_bp  alpha_t  alpha_p_one_sided
implementable short leg (eligibility by regime)      25   281.90 4.97    217.24     4.36               0.00
                    full short leg, same months      25   240.59 3.56    175.49     3.38               0.00
                          long leg, same months      25   309.96 3.60    212.42     3.59               0.00
                     long + implementable short      25   591.86 4.38    429.66     4.25               0.00
```

**Implementable short leg SURVIVES the Q18 bar (mean t > 2 and alpha t > 2).**

Eligibility is a legal question. Borrow supply and cost are not observed here and remain the open constraint.
