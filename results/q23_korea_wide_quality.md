# Q23 — Is the chip-sector effect distinct from a market-wide Korean quality premium?

Follows `docs/q23_korea_wide_quality_spec.md` (committed before the data were built).
KOR-QMJ is built here from every KOSPI/KOSDAQ company in the DART register (median 1,807 companies a month,
2016-12 → 2026-08), because AQR's country files and Ken French's international library do not cover Korea.
The decisive control, KOR-QMJ-ex-chip, excludes the 285 companies of the chip universe.

## Regressions

```
                          window                               test  months  alpha_bp  alpha_t   r2  beta_kor_qmj_ex_chip  t_kor_qmj_ex_chip  beta_kor_qmj  t_kor_qmj  beta_index  beta_momentum
frozen finding 2023-01 → 2026-08      C1 controls + KOR-QMJ-ex-chip      44    285.08     3.78 0.48                  0.32               2.22           NaN        NaN        0.03          -0.02
frozen finding 2023-01 → 2026-08 C2 controls + KOR-QMJ (incl. chip)      44    279.32     3.64 0.51                   NaN                NaN          0.44       2.24        0.05          -0.00
frozen finding 2023-01 → 2026-08           C3 KOR-QMJ-ex-chip alone      44    380.48     3.50 0.07                  0.42               1.95           NaN        NaN         NaN            NaN
frozen finding 2023-01 → 2026-08       C0 controls only (reference)      44    281.07     3.60 0.44                   NaN                NaN           NaN        NaN        0.04          -0.00
      extended 2016-12 → 2026-08      C1 controls + KOR-QMJ-ex-chip      51    263.37     3.85 0.49                  0.35               2.39           NaN        NaN        0.06          -0.05
      extended 2016-12 → 2026-08 C2 controls + KOR-QMJ (incl. chip)      51    256.33     3.67 0.51                   NaN                NaN          0.48       2.41        0.07          -0.03
      extended 2016-12 → 2026-08           C3 KOR-QMJ-ex-chip alone      66    271.86     3.19 0.08                  0.48               2.23           NaN        NaN         NaN            NaN
      extended 2016-12 → 2026-08       C0 controls only (reference)      51    260.86     3.70 0.44                   NaN                NaN           NaN        NaN        0.07          -0.03
```

**C1 verdict: the chip-sector effect is distinct from the market-wide premium.**

## The market-wide factor itself

```
                          window  months  corr(chip spread, KOR-QMJ-ex-chip)  KOR-QMJ mean_bp  KOR-QMJ t  KOR-QMJ-ex-chip mean_bp  KOR-QMJ-ex-chip t  chip spread mean_bp  chip spread t
frozen finding 2023-01 → 2026-08      44                                0.27            12.56       0.29                    -6.76              -0.13               377.63           3.30
      extended 2016-12 → 2026-08      66                                0.29             6.82       0.21                    -3.91              -0.10               269.97           3.02
```
