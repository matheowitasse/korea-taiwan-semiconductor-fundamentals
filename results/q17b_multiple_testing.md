# Q17b — Correcting the exploratory scan for having searched 264 combinations

Both corrections use only existing data (new regime 2025-07-01 → 2026-09-16). Exploratory: a small p means the
scan found more than chance explains, not that a specific rule is tradable.

- Tests in the scan: 264
- Max |t| observed: 3.19
- Max |t| from 500 scans of shifted signals (null): median 3.55, 90th pct 4.66, max 7.16
- **Share of null scans whose best test beats our best test: 0.736**
- Tests with BH-FDR q < 0.10: 0; q < 0.05: 0
- Tests that survive the max-t correction (p_scan < 0.05): 0

## Top 20 by |t| in the new regime

```
    asset              signal      outcome      condition   t_NEW  p_raw  p_BH_fdr  p_scan_maxt
    Hynix retail flow z (t−1) same-day o→c       all days  3.1893 0.0014    0.1330       0.7360
    Hynix retail flow z (t−1) same-day o→c US night < −1%  3.1863 0.0014    0.1330       0.7380
    Hynix retail flow z (t−1) same-day o→c       high vol  3.1698 0.0015    0.1330       0.7440
   KOSDAQ       KRW overnight same-day o→c       high vol -3.0873 0.0020    0.1330       0.7880
Suppliers           overshoot  next 5 days       high vol -3.0210 0.0025    0.1330       0.8280
   KOSDAQ           overshoot same-day o→c       all days  2.8400 0.0045    0.1747       0.8940
    Hynix            past 20d same-day o→c       all days  2.8186 0.0048    0.1747       0.9040
    Hynix            past 20d same-day o→c US night < −1%  2.7631 0.0057    0.1747       0.9220
  Samsung           overshoot  next 5 days       all days -2.7502 0.0060    0.1747       0.9300
  Samsung           overshoot  next 5 days       high vol -2.6493 0.0081    0.2129       0.9620
  Samsung retail flow z (t−1) same-day o→c       high vol  2.6028 0.0092    0.2211       0.9700
    KOSPI       KRW overnight same-day o→c       high vol -2.5495 0.0108    0.2211       0.9760
   KOSDAQ        prev day o→c same-day o→c US night < −1%  2.5265 0.0115    0.2211       0.9820
   KOSDAQ       KRW overnight same-day o→c       all days -2.5110 0.0120    0.2211       0.9820
   KOSDAQ    Hynix−Samsung 5d  next 5 days       high vol -2.4690 0.0135    0.2211       0.9920
  Samsung retail flow z (t−1) same-day o→c       all days  2.4563 0.0140    0.2211       0.9920
    KOSPI           overshoot same-day o→c       all days  2.4512 0.0142    0.2211       0.9920
Suppliers           overshoot  next 5 days       all days -2.3390 0.0193    0.2796       0.9980
   KOSDAQ    Hynix−Samsung 5d  next 5 days US night < −1% -2.3240 0.0201    0.2796       0.9980
    Hynix        prev day o→c  next 5 days US night < −1%  2.2835 0.0224    0.2954       0.9980
```
