# Q8 diagnostics — what drives the multi-factor result

Not decisive: the pre-registered verdict stands in `results/q8_multifactor.md`. These runs test whether the
long-short result survives restrictions that remove micro-caps, extreme returns, delisting losses and costs.

## discovery 2023-01→2025-06

```
                                                  variant    factor  months  n_stocks  ls_bp  ls_t  long_only_bp  long_only_t  turnover  long_only_after_cost_bp
                                        as pre-registered composite      30       228  147.2   2.7          78.1          3.4       0.2                     73.0
                                        as pre-registered   quality      30       225  189.8   2.4          86.4          1.9       0.1                     84.4
                                        as pre-registered  earn_mom      30       205  156.4   2.6          85.5          2.3       0.2                     78.8
                                        as pre-registered     value      30       236  121.5   2.2          56.7          1.8       0.1                     54.6
                                  returns winsorised ±30% composite      30       228  155.4   3.8          73.8          3.1       0.2                     68.7
                                  returns winsorised ±30%   quality      30       225  192.1   3.1          99.7          2.4       0.1                     97.7
                                  returns winsorised ±30%  earn_mom      30       205  117.9   1.9          71.3          2.0       0.2                     64.6
                                  returns winsorised ±30%     value      30       236  164.9   3.3          79.7          2.5       0.1                     77.5
                           price ≥ 1,000 KRW at formation composite      30       223  153.6   2.6          81.8          3.3       0.2                     76.6
                           price ≥ 1,000 KRW at formation   quality      30       220  192.9   2.5          88.3          2.0       0.1                     86.1
                           price ≥ 1,000 KRW at formation  earn_mom      30       200  148.3   2.3          94.0          2.4       0.2                     87.3
                           price ≥ 1,000 KRW at formation     value      30       231  126.4   2.5          58.0          2.0       0.1                     55.7
                                   market cap ≥ 50 bn KRW composite      30       194  167.8   2.2          91.0          2.6       0.2                     85.0
                                   market cap ≥ 50 bn KRW   quality      30       191  205.5   2.7         111.1          2.8       0.1                    108.8
                                   market cap ≥ 50 bn KRW  earn_mom      30       174  160.1   2.2          80.2          2.0       0.2                     73.4
                                   market cap ≥ 50 bn KRW     value      30       202  119.1   1.7          53.0          1.4       0.1                     49.9
                                  market cap ≥ 200 bn KRW composite      30       107  220.7   1.8         114.6          2.0       0.2                    107.4
                                  market cap ≥ 200 bn KRW   quality      30       106  270.5   3.1         137.4          2.2       0.1                    134.4
                                  market cap ≥ 200 bn KRW  earn_mom      30        99  168.4   1.7         118.7          1.8       0.3                    111.0
                                  market cap ≥ 200 bn KRW     value      30       110  230.7   3.0          99.8          2.4       0.1                     95.2
                              delisted companies excluded composite      30       218  161.9   3.1          75.7          3.1       0.2                     70.5
                              delisted companies excluded   quality      30       216  170.2   2.2          81.4          1.8       0.1                     79.3
                              delisted companies excluded  earn_mom      30       196  138.3   2.1          77.6          1.9       0.2                     71.0
                              delisted companies excluded     value      30       227  113.1   2.1          52.2          1.7       0.1                     50.2
all of the above (cap ≥ 50 bn, price ≥ 1,000, winsorised) composite      30       191  185.5   3.1          94.9          3.2       0.2                     88.7
all of the above (cap ≥ 50 bn, price ≥ 1,000, winsorised)   quality      30       189  201.8   3.6         109.8          3.3       0.1                    107.6
all of the above (cap ≥ 50 bn, price ≥ 1,000, winsorised)  earn_mom      30       172  126.0   1.7          76.5          2.2       0.2                     69.7
all of the above (cap ≥ 50 bn, price ≥ 1,000, winsorised)     value      30       199  199.7   3.4          99.3          3.3       0.1                     96.0
```

## validation 2025-07→today

```
                                                  variant    factor  months  n_stocks  ls_bp  ls_t  long_only_bp  long_only_t  turnover  long_only_after_cost_bp
                                        as pre-registered composite      14       245  426.6   2.0         148.0          1.2       0.2                    141.4
                                        as pre-registered   quality      14       242  600.5   4.4         238.7          3.1       0.1                    236.7
                                        as pre-registered  earn_mom      14       221  604.4   3.3         330.9          2.4       0.2                    324.3
                                        as pre-registered     value      14       250  198.1   1.4         -15.7         -0.2       0.1                    -19.1
                                  returns winsorised ±30% composite      14       245  302.1   2.5         100.7          1.2       0.2                     94.1
                                  returns winsorised ±30%   quality      14       242  452.8   5.0         189.8          3.2       0.1                    187.9
                                  returns winsorised ±30%  earn_mom      14       221  369.3   4.0         174.6          2.1       0.2                    168.0
                                  returns winsorised ±30%     value      14       250  216.7   2.2          48.9          0.6       0.1                     45.5
                           price ≥ 1,000 KRW at formation composite      14       238  403.2   1.9         122.4          1.0       0.2                    115.8
                           price ≥ 1,000 KRW at formation   quality      14       236  612.4   4.6         252.1          3.3       0.1                    250.1
                           price ≥ 1,000 KRW at formation  earn_mom      14       215  557.8   3.0         328.1          2.4       0.2                    321.4
                           price ≥ 1,000 KRW at formation     value      14       243  163.8   1.1         -38.5         -0.4       0.1                    -41.8
                                   market cap ≥ 50 bn KRW composite      14       196  459.9   2.2         146.1          1.5       0.2                    139.0
                                   market cap ≥ 50 bn KRW   quality      14       195  635.2   4.0         260.3          3.6       0.1                    258.3
                                   market cap ≥ 50 bn KRW  earn_mom      14       178  564.4   5.1         334.1          3.2       0.2                    326.9
                                   market cap ≥ 50 bn KRW     value      14       201  339.0   2.4          38.7          0.5       0.2                     34.0
                                  market cap ≥ 200 bn KRW composite      14       119  450.7   2.0         152.1          1.3       0.2                    144.6
                                  market cap ≥ 200 bn KRW   quality      14       119  507.9   2.1         175.3          1.5       0.1                    172.0
                                  market cap ≥ 200 bn KRW  earn_mom      14       112  701.5   3.5         295.2          1.9       0.3                    287.5
                                  market cap ≥ 200 bn KRW     value      14       120  358.9   2.6          37.5          1.0       0.1                     33.0
                              delisted companies excluded composite      14       239  441.7   2.1         150.6          1.2       0.2                    144.1
                              delisted companies excluded   quality      14       237  644.7   4.7         280.5          3.6       0.1                    278.7
                              delisted companies excluded  earn_mom      14       217  596.8   3.0         324.6          2.3       0.2                    318.0
                              delisted companies excluded     value      14       244  194.9   1.3         -16.2         -0.2       0.1                    -19.4
all of the above (cap ≥ 50 bn, price ≥ 1,000, winsorised) composite      14       195  333.5   2.5         121.4          1.5       0.2                    114.1
all of the above (cap ≥ 50 bn, price ≥ 1,000, winsorised)   quality      14       194  455.0   4.6         184.1          3.9       0.1                    182.1
all of the above (cap ≥ 50 bn, price ≥ 1,000, winsorised)  earn_mom      14       177  339.3   3.9         181.5          2.7       0.2                    174.3
all of the above (cap ≥ 50 bn, price ≥ 1,000, winsorised)     value      14       200  313.4   4.9          85.3          2.2       0.2                     80.5
```

## Shape of the returns (2023-01 → today, both periods pooled)

```
   factor  mean_ls_bp  median_ls_bp  months_positive_%  worst_month_bp  best_month_bp  top_bp  bottom_bp  universe_bp
composite       236.1         196.7               70.5          -988.6         2053.0   269.6       33.5        169.2
  quality       320.4         271.4               72.7         -1291.0         2384.1   303.3      -17.2        168.4
 earn_mom       299.0         163.8               72.7          -868.2         2405.9   336.3       37.3        172.7
    value       145.9         188.9               61.4         -1323.4         2806.0   194.0       48.1        160.3
```
