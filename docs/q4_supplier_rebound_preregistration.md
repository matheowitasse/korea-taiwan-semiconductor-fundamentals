# Q4 pre-registration — Asian chip suppliers rebound after big US chip sell-offs (Korea, Taiwan, Japan)

Written and committed **2026-09-16, before running any test on Taiwan or Japan and before loading any
Korean, Taiwanese or Japanese price data after 2025-06-30 for this purpose.**
Design: AI-era discovery → AI-era validation (the design described in the paper, Section 4).

## 1. Hypothesis

After a night where US semiconductors fall sharply, Asian chip **supplier** stocks, which absorb news more slowly than the
large names, open too low and **rise from the open to the close** of the next Asian session.

Prior evidence (Q2, Korea only, Yahoo daily): after SOXX overnight < −2%, Korean supplier basket open→close
+0.39% (t 2.34) in 2015–2022 and +0.52% (t 1.60, n = 56) in 2023-01 → 2025-06. **The Korean discovery-period numbers
have therefore already been seen.** Taiwan and Japan have not been looked at.

## 2. Data

- Yahoo Finance daily adjusted OHLCV (fresh download, `data/raw/full_*.parquet`). Bars with zero volume or O=H=L=C → missing.
- Each market uses its own trading calendar (KOSPI ^KS11, TAIEX ^TWII, Nikkei ^N225).
- **US signal** for Asian trading day D (previous trading day P of that market): SOXX open→close compounded over US
  sessions dated in [P, D). All three markets open after the US close.
- **Big-down night:** signal < −2%.
- **Supplier baskets** (equal-weight mean of available members' open→close return on D):
  - Korea: Hanmi Semi 042700.KS, DB HiTek 000990.KS, Leeno 058470.KQ, ISC 095340.KQ, Wonik IPS 240810.KQ,
    Jusung Eng 036930.KQ, Eugene Tech 084370.KQ, HPSP 403870.KQ
  - Taiwan: ASE 3711.TW, Alchip 3661.TW, Global Unichip 3443.TW, King Yuan 2449.TW, Chroma 2360.TW, Gudeng 3680.TWO,
    ASPEED 5274.TWO, Wiwynn 6669.TW, Quanta 2382.TW, Elite Material 2383.TW, Gold Circuit 2368.TW, WinWay 6515.TW, MPI 6223.TWO
  - Japan: Disco 6146.T, Lasertec 6920.T, Screen 7735.T, Kokusai Electric 6525.T (from 2023-10), Socionext 6526.T,
    Ibiden 4062.T, Shibaura Mechatronics 6590.T, Tokyo Seimitsu 7729.T, Towa 6315.T, Micronics Japan 6871.T, Rorze 6323.T, Ferrotec 6890.T
- **Large names** (reported for contrast only): Samsung, SK Hynix / TSMC, MediaTek / Tokyo Electron, Advantest.

## 3. The 4 tests (complete family)

| ID | Measure on big-down nights |
|---|---|
| KR | Korea supplier basket open→close |
| TW | Taiwan supplier basket open→close |
| JP | Japan supplier basket open→close |
| POOL | per date, mean of the market baskets that had a big-down night that day |

- Statistic: mean open→close return on big-down nights. **One-sided, H1: mean > 0.** One-sample t-test.
- Placebo (5,000 draws): the same number of days drawn at random from all trading days of that market in the period
  (POOL: from the daily cross-market average of available baskets); p = share of draws with mean ≥ observed.

## 4. Periods and decision rules

- **Discovery:** D from 2023-01-01 to 2025-06-30. Pass = Holm-adjusted p (over the 4 tests) < 0.10 **and** placebo p < 0.05.
- **Validation:** D from 2025-07-01 to 2026-09-16, **only for tests that pass discovery**.
  Edge = Holm-adjusted p (over the survivors) < 0.05 **and** placebo p < 0.05, same direction (mean > 0).
- If nothing passes discovery, validation is not run.
- Costs ignored at this stage. Effects reported in basis points.

## 5. Robustness planned in advance (not decisive)

- Korean results re-run with official KRX prices once the author's KRX account is available.
- If an edge is confirmed: 1-minute IBKR data to see when during the session the rebound happens.

## 6. Known weaknesses (accepted in advance)

- Supplier lists chosen in 2026 by AI-supply-chain relevance → hindsight / survivorship bias.
- The same US nights drive all three markets → POOL is not three times the independent evidence.
- Yahoo open prices unverified; Taiwan and Korea show ~1–2% of days with open equal to previous close.
- Kokusai Electric only from 2023-10; HPSP from 2022-07.
- Big-down nights are few: roughly 1–3 per month in volatile periods, fewer in calm ones.
