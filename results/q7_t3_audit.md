# Q7 T3 audit — why SUE rank showed +31 % in the recent period (EXPLORATORY data check)

Not a hypothesis test. Nothing here can confirm an edge.

## Recent 2025-07-01 → 2026-06-16: 439 events with SUE, 9 months

### 1. Leak checks

First disclosure kind of the event (share %), and whether a periodic report arrives within the 30-day event:

```
first_kind
quarterly    36.7
half         18.5
timely       17.1
annual       16.4
fair         11.4

events with a periodic report inside the event window: 83.6 %
days from reported quarter end to D0: median 45, min 12, share < 20 days 2.3 %
```

```
T3 slope, all events                         :   31.34 %  t  5.78  n 439
only events WITH a periodic report in window :   27.70 %  (without: 49.89 %, n 72)
excluding D0 < 20 days after quarter end     :   30.64 %  n 429
correlation of SUE rank with EAR rank        : 0.231
```

### 2. Rally or news? SUE rank vs return BEFORE the announcement (D0−61 → D0−2)

```
pre-announcement slope: 30.23 %  t 3.77  n 439   (after-announcement T3: 31.34 %)
```

### 3. Outliers

CAR60 by SUE quintile (%):

```
   count   mean  median
q                      
1     88   3.15   -3.78
2     88   9.13   -4.67
3     87  11.98    0.33
4     88  17.85    3.79
5     88  30.77   14.17
```

Slope without the most extreme 5 % of CAR60: 27.23 % (t 5.05)

Ten events contributing most to the slope:

```
        D0 stock_code        name   sue  r_sue    ear  car60  pre_car
2026-03-13     032580     (주)피델릭스 2.513  0.408  0.023  4.588   -0.322
2026-02-04     355150    (주)코스텍시스 3.582  0.471  0.013  2.777   -0.107
2026-02-23     080220    (주)제주반도체 2.527  0.417 -0.043  1.653    1.154
2025-08-29     089890      (주)코세스 1.805  0.468 -0.091  1.345    0.697
2026-05-11     032580     (주)피델릭스 2.975  0.433  0.695  1.274    0.230
2026-01-29     382800 (주)지앤비에스 에코 1.682  0.287 -0.057  1.726   -0.023
2026-02-25     321260     (주)프로이천 1.876  0.315  0.034  1.581   -0.379
2025-11-13     059120    (주)아진엑스텍 3.038  0.479 -0.039  1.021    0.050
2025-11-13     080220    (주)제주반도체 3.915  0.489 -0.011  0.980    0.310
2026-03-18     092190  서울바이오시스(주) 1.398  0.261 -0.077  1.630    0.332
```

### 4. Slope by event month (months with ≥ 15 events)

```
  month  n  slope_%
2025-08 87    37.58
2025-11 88    16.28
2026-02 64    26.72
2026-03 84    47.30
2026-05 82    17.80
```

## Discovery 2023-01-01 → 2025-06-30: 1023 events with SUE, 23 months

### 1. Leak checks

First disclosure kind of the event (share %), and whether a periodic report arrives within the 30-day event:

```
first_kind
quarterly    36.7
timely       20.4
annual       17.3
half         14.0
fair         11.6

events with a periodic report inside the event window: 82.6 %
days from reported quarter end to D0: median 45, min 6, share < 20 days 2.7 %
```

```
T3 slope, all events                         :    5.91 %  t  2.01  n 1023
only events WITH a periodic report in window :    6.36 %  (without: 4.25 %, n 178)
excluding D0 < 20 days after quarter end     :    6.07 %  n 995
correlation of SUE rank with EAR rank        : 0.223
```

### 2. Rally or news? SUE rank vs return BEFORE the announcement (D0−61 → D0−2)

```
pre-announcement slope: 2.71 %  t 1.07  n 1023   (after-announcement T3: 5.91 %)
```

### 3. Outliers

CAR60 by SUE quintile (%):

```
   count  mean  median
q                     
1    205 -0.81   -4.80
2    204  0.63   -4.64
3    205  4.02   -2.49
4    204  3.05   -4.81
5    205  4.98   -2.00
```

Slope without the most extreme 5 % of CAR60: 2.07 % (t 0.97)

Ten events contributing most to the slope:

```
        D0 stock_code        name    sue  r_sue    ear  car60  pre_car
2023-11-13     080220    (주)제주반도체 -0.019  0.262 -0.001  5.373    0.229
2023-05-11     094170    (주)동운아나텍  1.476  0.500 -0.068  2.120   -0.127
2023-05-15     031980 피에스케이홀딩스(주)  0.403  0.402  0.054  1.421   -0.039
2023-05-12     039440    (주)에스티아이  0.238  0.354  0.007  1.058   -0.145
2023-04-19     094360   (주)칩스앤미디어  0.591  0.427  0.033  0.839    0.151
2025-05-30     089890      (주)코세스  1.533  0.456 -0.009  0.731   -0.091
2023-02-21     117730    (주)티로보틱스  0.381  0.270  0.044  1.174    0.077
2023-02-13     011690   (주)와이투솔루션  0.535  0.317 -0.003  0.971    0.038
2023-05-15     122640      (주)예스티  0.433  0.415 -0.002  0.745    0.120
2024-01-18     042700    한미반도체(주)  0.201  0.199  0.105  1.417   -0.151
```

### 4. Slope by event month (months with ≥ 15 events)

```
  month  n  slope_%
2023-02 61    13.59
2023-03 72    -8.71
2023-05 76    24.55
2023-08 78    -4.03
2023-11 77    10.73
2024-02 57     5.85
2024-03 68     0.86
2024-05 75     6.54
2024-08 75    -6.08
2024-11 83    -3.46
2025-02 66     3.16
2025-03 68    12.97
2025-05 84    21.94
```
