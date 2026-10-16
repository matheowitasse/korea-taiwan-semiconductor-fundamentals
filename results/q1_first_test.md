# Q1 first test — Korean chip export releases → US semis

Follows `docs/q1_preregistration.md` (committed before this run).

## Sample

- In-sample releases: 195 (2016-08-22 → 2025-05-21)
- With S1 (working-day adjusted, needs 3 prior adjusted releases): 155
- With S2 (raw YoY): 192

## Primary test: SOXX 5-day return on S1

```
  n  slope     t     p  placebo_p
155  0.000 0.243 0.808      0.860
```

Regime split:

```
     regime  n  slope      t     p
  2016-2022 97 -0.000 -0.513 0.608
2023-2025H1 58  0.000  1.025 0.305
```

Tercile means of SOXX r5 (%): top 0.37, bottom -0.39, spread 0.76 (n=155)

Pre-registered criteria:
1. t > 2 and placebo p < 0.05: **FAIL**
2. same slope sign in both regimes: **FAIL**
3. top − bottom tercile spread > 0.5 pp: **PASS**

**Primary result: NOT PROMISING**

## Secondary tests (18 regressions, Holm-corrected)

```
signal asset horizon   n  slope      t     p  p_holm
    S1  SOXX      r1 155 -0.000 -0.912 0.362   1.000
    S1  SOXX      r5 155  0.000  0.243 0.808   1.000
    S1  SOXX     r20 155  0.000  1.157 0.247   1.000
    S1  NVDA      r1 155 -0.000 -0.456 0.648   1.000
    S1  NVDA      r5 155  0.000  0.484 0.628   1.000
    S1  NVDA     r20 155  0.001  1.678 0.093   1.000
    S1    MU      r1 155 -0.000 -1.050 0.294   1.000
    S1    MU      r5 155  0.000  1.030 0.303   1.000
    S1    MU     r20 155  0.001  2.078 0.038   0.679
    S2  SOXX      r1 192  0.000  0.301 0.764   1.000
    S2  SOXX      r5 192 -0.000 -0.105 0.917   1.000
    S2  SOXX     r20 192  0.000  0.892 0.373   1.000
    S2  NVDA      r1 192  0.000  0.215 0.829   1.000
    S2  NVDA      r5 192 -0.000 -0.410 0.682   1.000
    S2  NVDA     r20 192  0.001  1.049 0.294   1.000
    S2    MU      r1 192 -0.000 -0.314 0.754   1.000
    S2    MU      r5 192  0.000  0.355 0.723   1.000
    S2    MU     r20 192  0.000  0.634 0.526   1.000
```

## S2 by regime (r5)

```
signal      regime asset horizon   n  slope      t     p
    S2   2016-2022  SOXX      r5 134  0.000  1.402 0.161
    S2   2016-2022  NVDA      r5 134  0.000  0.860 0.390
    S2   2016-2022    MU      r5 134  0.000  1.746 0.081
    S2 2023-2025H1  SOXX      r5  58 -0.001 -2.012 0.044
    S2 2023-2025H1  NVDA      r5  58 -0.002 -3.362 0.001
    S2 2023-2025H1    MU      r5  58 -0.002 -1.637 0.102
```

## Volatility: SOXX 5-day realised vol (annualised) after releases

```
          test   n  slope      t     p  placebo_p
   vol5 ~ |S1| 155  0.001  1.342 0.180      0.242
vol5 ~ 1[S1<0] 155 -0.008 -0.217 0.828      0.829
   vol5 ~ |S2| 192 -0.000 -0.271 0.787      0.752
vol5 ~ 1[S2<0] 192  0.005  0.213 0.831      0.855
```

## Context: Korean same-day reaction (close D-1 → close D)

```
   asset signal   n  slope     t     p
SK Hynix     S1 155  0.000 1.368 0.171
SK Hynix     S2 192  0.000 1.240 0.215
 Samsung     S1 155  0.000 1.175 0.240
 Samsung     S2 192  0.000 0.074 0.941
```

## Notes

- Total regressions run: 35. Only the primary test was pre-registered as decisive.
