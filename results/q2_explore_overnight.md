# Q2 exploration — US overnight semis move vs Korean session

Sample: 2015-01-01 to 2025-06-30 (holdout from 2025-07-01 untouched). Data: Yahoo Finance daily, adjusted.
US signal: SOXX open-to-close, compounded over US sessions between Korea's previous close and today's open.
Cost assumption: 0.30% round trip. HAC lags: 5. Permutations: 2000.

## 1. Data quality (Yahoo Korean daily bars)

```
                  name  rows  open==prev_close %  zero volume %  flat bar (O=H=L=C) %  |gap|>30% days
ticker                                                                                               
005930.KS      Samsung  2573                1.36           0.70                  0.70               0
000660.KS     SK Hynix  2573                1.17           0.66                  0.66               0
042700.KS   Hanmi Semi  2573                2.22           1.32                  1.32               0
000990.KS     DB HiTek  2573                1.71           1.05                  1.05               0
058470.KQ        Leeno  2573                1.48           1.09                  1.09               0
095340.KQ          ISC  2573                1.63           0.66                  0.66               0
240810.KQ    Wonik IPS  2244                0.94           0.58                  0.58               0
036930.KQ   Jusung Eng  2573                1.36           0.74                  0.74               2
084370.KQ  Eugene Tech  2573                1.52           0.66                  0.66               0
403870.KQ         HPSP   722                0.14           0.00                  0.00               0
^KS11            KOSPI  2572                0.16           0.04                  0.04               0
```

## 2. How much is priced at the open, and what is left after it

- `gap beta`: Korean opening gap per 1.0 of US overnight move (priced at the open).
- `intraday beta`: open-to-close move per 1.0 of US move. > 0 continuation (underreaction), < 0 reversal (overreaction).
- `placebo p`: share of shuffled nights giving a |beta| at least as large.

```
              period          group    n  gap beta  gap R2  intraday beta  intraday t(HAC)  placebo p
  pre_AI (2015-2022)          KOSPI 1964     0.254   0.352         -0.038            -2.13      0.002
  pre_AI (2015-2022)        Samsung 1947     0.361   0.255         -0.064            -2.80      0.002
  pre_AI (2015-2022)       SK Hynix 1948     0.543   0.331         -0.117            -3.40      0.000
  pre_AI (2015-2022) Suppliers (EW) 1955     0.431   0.388         -0.053            -1.70      0.050
AI_era (2023-2025H1)          KOSPI  606     0.255   0.392          0.013             0.57      0.472
AI_era (2023-2025H1)        Samsung  607     0.376   0.344         -0.031            -1.37      0.299
AI_era (2023-2025H1)       SK Hynix  607     0.769   0.444         -0.017            -0.37      0.746
AI_era (2023-2025H1) Suppliers (EW)  607     0.586   0.472         -0.072            -1.56      0.147
```

## 3. Mean Korean open-to-close return (%) by US overnight quintile

```
              period          group  Q1 (US down most)     Q2     Q3     Q4  Q5 (US up most)
  pre_AI (2015-2022)          KOSPI              0.018 -0.023 -0.070 -0.067           -0.091
  pre_AI (2015-2022)        Samsung              0.131  0.012  0.005 -0.021           -0.089
  pre_AI (2015-2022)       SK Hynix              0.107  0.009 -0.144 -0.144           -0.262
  pre_AI (2015-2022) Suppliers (EW)              0.080 -0.105  0.004 -0.049           -0.134
AI_era (2023-2025H1)          KOSPI             -0.083  0.009  0.019 -0.184           -0.008
AI_era (2023-2025H1)        Samsung             -0.059 -0.099  0.042 -0.068           -0.251
AI_era (2023-2025H1)       SK Hynix             -0.103  0.241  0.035 -0.210            0.166
AI_era (2023-2025H1) Suppliers (EW)              0.308  0.024  0.141 -0.462            0.055
```

## 4. Big US nights (|SOXX overnight| > 2%)

`beats cost?` = |mean| above the 0.30% round-trip cost (a necessary, not sufficient, condition).

```
              period          group         night   n  mean intraday %     t  beats cost?
  pre_AI (2015-2022)          KOSPI    US up > 2% 148           -0.069 -0.65        False
  pre_AI (2015-2022)          KOSPI US down < -2% 160            0.187  2.27        False
  pre_AI (2015-2022)        Samsung    US up > 2% 145           -0.220 -1.66        False
  pre_AI (2015-2022)        Samsung US down < -2% 157            0.273  2.78        False
  pre_AI (2015-2022)       SK Hynix    US up > 2% 143           -0.294 -1.51        False
  pre_AI (2015-2022)       SK Hynix US down < -2% 158            0.432  2.96         True
  pre_AI (2015-2022) Suppliers (EW)    US up > 2% 145           -0.070 -0.36        False
  pre_AI (2015-2022) Suppliers (EW) US down < -2% 159            0.390  2.34         True
AI_era (2023-2025H1)          KOSPI    US up > 2%  57           -0.102 -0.92        False
AI_era (2023-2025H1)          KOSPI US down < -2%  56            0.012  0.10        False
AI_era (2023-2025H1)        Samsung    US up > 2%  58           -0.446 -2.71         True
AI_era (2023-2025H1)        Samsung US down < -2%  56            0.032  0.16        False
AI_era (2023-2025H1)       SK Hynix    US up > 2%  58           -0.025 -0.10        False
AI_era (2023-2025H1)       SK Hynix US down < -2%  56            0.126  0.44        False
AI_era (2023-2025H1) Suppliers (EW)    US up > 2%  58            0.015  0.05        False
AI_era (2023-2025H1) Suppliers (EW) US down < -2%  56            0.524  1.60         True
```

## Notes

- Formal tests in this run: 24 (log them; correct for multiple testing before believing any single one).
- Limitations: no US after-hours (earnings nights), no KOSPI 200 night futures control, Yahoo open prices unverified vs KRX,
  suppliers list chosen with today's knowledge (HPSP only from 2022-07) — survivorship/look-ahead risk in group selection.
