# Q25 — Do the stocks the strategy would short actually carry short interest?

Descriptive measurement from KRX net short positions by issue (page 33001), imported with
`src/q25_import_short_positions.py`. Every listed Korean stock has been eligible for short selling since
2025-03-31, so these snapshots show what the market does rather than what the rules allow.

## Share of names carrying any net short position (%)

```
date                                   2025-06-30  2025-12-30  2026-06-30  2026-09-17
group                                                                                
350 largest listed companies                 91.4        94.9        94.6        94.9
all listed issues                            51.4        57.5        62.0        62.4
rest of the chip universe                    63.9        69.9        70.0        71.8
strategy long side (top quintile)            66.7        77.1        82.0        92.0
strategy short side (bottom quintile)        55.8        56.2        60.0        56.0
```

## Median net short position as a share of market capitalisation, among names that have one (%)

```
date                                   2025-06-30  2025-12-30  2026-06-30  2026-09-17
group                                                                                
350 largest listed companies                 0.48        0.46        0.48        0.54
all listed issues                            0.38        0.38        0.45        0.47
rest of the chip universe                    0.38        0.38        0.41        0.41
strategy long side (top quintile)            0.31        0.34        0.30        0.59
strategy short side (bottom quintile)        0.63        0.66        0.56        0.55
```

## Short-sale volume on 2026-09-17 (page 32001)

```
      date                                 group  names  traded_%  with_any_short_sale_%  median_short_share_of_volume_%
2026-09-17 strategy short side (bottom quintile)     50     94.00                  76.00                            1.54
2026-09-17     strategy long side (top quintile)     50     98.00                  98.00                            3.54
2026-09-17             rest of the chip universe    149     96.64                  86.58                            1.43
2026-09-17                     all listed issues   2762     95.69                  78.96                            1.89
```

## Full detail (positions)

```
      date signal_month                                 group  names  with_short_%  median_short_%_of_cap  mean_short_%_of_cap  median_cap_bn_KRW
2025-06-30   2025-06-30 strategy short side (bottom quintile)     43         55.81                   0.63                 0.44              91.63
2025-06-30   2025-06-30     strategy long side (top quintile)     39         66.67                   0.31                 0.42             200.89
2025-06-30   2025-06-30             rest of the chip universe    119         63.87                   0.38                 0.51              99.34
2025-06-30   2025-06-30          350 largest listed companies    350         91.43                   0.47                 0.79             423.26
2025-06-30   2025-06-30                     all listed issues   1796         51.39                   0.38                 0.34              87.24
2025-12-30   2025-12-30 strategy short side (bottom quintile)     48         56.25                   0.66                 0.46              84.88
2025-12-30   2025-12-30     strategy long side (top quintile)     48         77.08                   0.34                 0.57             296.62
2025-12-30   2025-12-30             rest of the chip universe    143         69.93                   0.38                 0.49             139.73
2025-12-30   2025-12-30          350 largest listed companies    350         94.86                   0.46                 0.87            2392.61
2025-12-30   2025-12-30                     all listed issues   2788         57.46                   0.38                 0.36             116.24
2026-06-30   2026-06-30 strategy short side (bottom quintile)     50         60.00                   0.56                 0.51              75.04
2026-06-30   2026-06-30     strategy long side (top quintile)     50         82.00                   0.30                 0.58             786.87
2026-06-30   2026-06-30             rest of the chip universe    150         70.00                   0.41                 0.44             122.54
2026-06-30   2026-06-30          350 largest listed companies    350         94.57                   0.48                 0.91            2840.92
2026-06-30   2026-06-30                     all listed issues   2769         62.01                   0.45                 0.42              94.36
2026-09-17   2026-09-16 strategy short side (bottom quintile)     50         56.00                   0.55                 0.49              63.57
2026-09-17   2026-09-16     strategy long side (top quintile)     50         92.00                   0.59                 1.00             718.37
2026-09-17   2026-09-16             rest of the chip universe    149         71.81                   0.41                 0.59             126.07
2026-09-17   2026-09-16          350 largest listed companies    350         94.86                   0.54                 0.98            2608.67
2026-09-17   2026-09-16                     all listed issues   2762         62.38                   0.47                 0.46              98.25
```
