# Q17 — EXPLORATORY scan (not a test)

Scans signals x assets x conditions in three periods. **Nothing here is a claim**: scanning produces apparent
hits by construction. Candidates are hypotheses to pre-register and confirm on data after 2026-09-16.

Grid: 264 signal/asset/outcome/condition combinations with enough data in all three periods.
Filter: |t| ≥ 2 in NEW (2025-07 → 2026-09-16) **and** same sign in AI (2023 → 2025H1) **and** in PRE (2016 → 2022).
**Candidates found: 16. Expected by chance under no effect: ≈ 3.0.**

## Candidates (sorted by placebo p in the new regime)

```
    asset               signal      outcome      condition  n_NEW  beta_NEW  t_NEW  placebo_p_NEW  beta_AI   t_AI  beta_PRE  t_PRE
    Hynix             past 20d same-day o→c US night < −1%     68     0.037  2.763          0.000    0.004  0.184     0.008  0.709
    Hynix  retail flow z (t−1) same-day o→c       high vol    173     0.008  3.170          0.000    0.001  0.831     0.001  1.476
    Hynix  retail flow z (t−1) same-day o→c US night < −1%     68     0.012  3.186          0.000    0.002  0.970     0.001  1.238
   KOSDAQ        KRW overnight same-day o→c       high vol    145    -1.341 -3.087          0.000   -0.126 -0.622    -0.048 -0.325
    Hynix  retail flow z (t−1) same-day o→c       all days    297     0.006  3.189          0.003    0.001  1.363     0.001  2.514
   KOSDAQ            overshoot same-day o→c       all days    296     0.494  2.840          0.006    0.356  2.148     0.016  0.152
  Samsung            overshoot  next 5 days       all days    289    -0.336 -2.750          0.013   -0.090 -0.535    -0.256 -2.468
    KOSPI            overshoot same-day o→c       all days    296     0.253  2.451          0.018    0.166  1.786     0.029  0.418
  Samsung  retail flow z (t−1) same-day o→c       all days    297     0.004  2.456          0.019    0.000  0.619     0.001  2.214
  Samsung            overshoot  next 5 days       high vol    230    -0.321 -2.649          0.020   -0.068 -0.327    -0.445 -2.779
   KOSDAQ        KRW overnight same-day o→c       all days    297    -0.760 -2.511          0.023   -0.030 -0.283    -0.043 -0.621
Suppliers            overshoot same-day o→c       high vol    166     0.274  2.254          0.025    0.075  0.566     0.011  0.101
    KOSPI         prev day o→c  next 5 days       high vol    182    -0.278 -2.104          0.037   -0.157 -0.871    -0.192 -0.977
  Samsung     Hynix−Samsung 5d same-day o→c       all days    295     0.044  2.205          0.037    0.006  0.477     0.013  1.304
    Hynix foreign flow z (t−1) same-day o→c       all days    297    -0.004 -2.080          0.062   -0.002 -2.338    -0.001 -2.837
    Hynix         prev day o→c same-day o→c       all days    296    -0.139 -2.047          0.070   -0.042 -1.028    -0.102 -4.099
```

## Strongest in the new regime, sign agreement NOT required (regime-specific view)

32 of 264 combinations reach |t| ≥ 2 in NEW; ≈ 12 expected by chance.

```
    asset              signal      outcome      condition  n_PRE  beta_PRE  t_PRE  n_AI  beta_AI   t_AI  n_NEW  beta_NEW  t_NEW  placebo_p_NEW
    Hynix retail flow z (t−1) same-day o→c       all days   1660     0.001  2.514   607    0.001  1.363    297     0.006  3.189          0.004
    Hynix retail flow z (t−1) same-day o→c US night < −1%    338     0.001  1.238   130    0.002  0.970     68     0.012  3.186          0.000
    Hynix retail flow z (t−1) same-day o→c       high vol    471     0.001  1.476   313    0.001  0.831    173     0.008  3.170          0.000
   KOSDAQ       KRW overnight same-day o→c       high vol    590    -0.048 -0.325   187   -0.126 -0.622    145    -1.341 -3.087          0.000
Suppliers           overshoot  next 5 days       high vol    654     0.186  0.262   218   -0.163 -0.519    166    -0.826 -3.021          0.000
   KOSDAQ           overshoot same-day o→c       all days   1676     0.016  0.152   607    0.356  2.148    296     0.494  2.840          0.008
    Hynix            past 20d same-day o→c       all days   1657    -0.006 -1.391   607   -0.007 -0.973    295     0.021  2.819          0.086
    Hynix            past 20d same-day o→c US night < −1%    331     0.008  0.709   130    0.004  0.184     68     0.037  2.763          0.000
  Samsung           overshoot  next 5 days       all days   1625    -0.256 -2.468   607   -0.090 -0.535    289    -0.336 -2.750          0.012
  Samsung           overshoot  next 5 days       high vol    494    -0.445 -2.779   252   -0.068 -0.327    230    -0.321 -2.649          0.024
  Samsung retail flow z (t−1) same-day o→c       high vol    501     0.001  2.235   252   -0.000 -0.097    230     0.005  2.603          0.024
    KOSPI       KRW overnight same-day o→c       high vol    593     0.070  0.703   204   -0.250 -1.759    184    -1.075 -2.550          0.005
   KOSDAQ        prev day o→c same-day o→c US night < −1%    354    -0.067 -0.572   130    0.302  2.087     67     0.249  2.527          0.000
   KOSDAQ       KRW overnight same-day o→c       all days   1710    -0.043 -0.621   604   -0.030 -0.283    297    -0.760 -2.511          0.020
   KOSDAQ    Hynix−Samsung 5d  next 5 days       high vol    560     0.008  0.152   190   -0.109 -1.543    143    -0.240 -2.469          0.035
```
