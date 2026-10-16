"""Q2 first exploration: does the US overnight semis move carry into the Korean session?

For each Korean trading day D (previous Korean trading day P):
  - US signal  = compounded SOXX open-to-close return over US sessions dated in [P, D).
                 Those sessions start after Korea's close on P and end before Korea's open on D.
  - KR gap     = open(D) / close(P) - 1          -> what is priced at the open
  - KR intraday= close(D) / open(D) - 1          -> what is left after the open (the edge question)

Pre-holdout data only (see README). Yahoo daily data: no after-hours, no KOSPI 200 night futures yet.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"

START = "2015-01-01"
HOLDOUT_START = "2025-07-01"  # nothing on or after this date is used
PERIODS = {
    "pre_AI (2015-2022)": ("2015-01-01", "2022-12-31"),
    "AI_era (2023-2025H1)": ("2023-01-01", "2025-06-30"),
}

US_SIGNAL = "SOXX"
BIG = {"005930.KS": "Samsung", "000660.KS": "SK Hynix"}
SUPPLIERS = {
    "042700.KS": "Hanmi Semi",
    "000990.KS": "DB HiTek",
    "058470.KQ": "Leeno",
    "095340.KQ": "ISC",
    "240810.KQ": "Wonik IPS",
    "036930.KQ": "Jusung Eng",
    "084370.KQ": "Eugene Tech",
    "403870.KQ": "HPSP",
}
BENCH = {"^KS11": "KOSPI"}

COST_ROUND_TRIP = 0.0030  # assumption: ~0.20% KR sell tax + ~0.10% commissions/spread
BIG_MOVE = 0.02           # SOXX overnight move threshold for "big night"
N_PERM = 2000
HAC_LAGS = 5


def load(ticker: str) -> pd.DataFrame:
    RAW.mkdir(parents=True, exist_ok=True)
    cache = RAW / f"{ticker.replace('^', 'IDX_')}.parquet"
    if cache.exists():
        df = pd.read_parquet(cache)
    else:
        df = yf.Ticker(ticker).history(start=START, end=HOLDOUT_START, auto_adjust=True)
        df.index = df.index.tz_localize(None).normalize()
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df.to_parquet(cache)
    return df[df.index < HOLDOUT_START]


def quality_report(ticker: str, df: pd.DataFrame) -> dict:
    prev_close = df["Close"].shift(1)
    gap = df["Open"] / prev_close - 1
    return {
        "ticker": ticker,
        "rows": len(df),
        "open==prev_close %": round(100 * (df["Open"] == prev_close).mean(), 2),
        "zero volume %": round(100 * (df["Volume"] == 0).mean(), 2),
        "flat bar (O=H=L=C) %": round(100 * ((df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"])).mean(), 2),
        "|gap|>30% days": int((gap.abs() > 0.30).sum()),
    }


def us_overnight_signal(kr_dates: pd.DatetimeIndex, us: pd.DataFrame) -> pd.DataFrame:
    us_oc = us["Close"] / us["Open"] - 1
    rows = []
    for prev, cur in zip(kr_dates[:-1], kr_dates[1:]):
        window = us_oc[(us_oc.index >= prev) & (us_oc.index < cur)]
        rows.append((cur, float(np.prod(1 + window.values) - 1) if len(window) else 0.0, len(window)))
    return pd.DataFrame(rows, columns=["date", "us_oc", "n_us_sessions"]).set_index("date")


def kr_returns(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["gap"] = df["Open"] / df["Close"].shift(1) - 1
    out["intraday"] = df["Close"] / df["Open"] - 1
    # Drop broken bars: zero volume or flat bars are usually halts / bad data
    bad = (df["Volume"] == 0) | ((df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"]))
    return out[~bad]


def hac_beta(y: pd.Series, x: pd.Series) -> tuple[float, float, float, int]:
    d = pd.concat([y, x], axis=1, sort=True).dropna()
    if len(d) < 50:
        return np.nan, np.nan, np.nan, len(d)
    model = sm.OLS(d.iloc[:, 0], sm.add_constant(d.iloc[:, 1])).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    return float(model.params.iloc[1]), float(model.tvalues.iloc[1]), float(model.rsquared), len(d)


def perm_pvalue(y: pd.Series, x: pd.Series, rng: np.random.Generator) -> float:
    """Placebo: shuffle which night goes with which Korean day; how often is |beta| as large?"""
    d = pd.concat([y, x], axis=1, sort=True).dropna()
    yv, xv = d.iloc[:, 0].values, d.iloc[:, 1].values
    xc = xv - xv.mean()
    beta = (xc @ (yv - yv.mean())) / (xc @ xc)
    perm = np.array([(p @ (yv - yv.mean())) / (xc @ xc) for p in (rng.permutation(xc) for _ in range(N_PERM))])
    return float((np.abs(perm) >= abs(beta)).mean())


def main() -> None:
    rng = np.random.default_rng(42)
    RESULTS.mkdir(parents=True, exist_ok=True)
    lines = ["# Q2 exploration — US overnight semis move vs Korean session", "",
             f"Sample: {START} to 2025-06-30 (holdout from {HOLDOUT_START} untouched). Data: Yahoo Finance daily, adjusted.",
             f"US signal: {US_SIGNAL} open-to-close, compounded over US sessions between Korea's previous close and today's open.",
             f"Cost assumption: {COST_ROUND_TRIP:.2%} round trip. HAC lags: {HAC_LAGS}. Permutations: {N_PERM}.", ""]

    us = load(US_SIGNAL)
    kospi = load("^KS11")
    signal = us_overnight_signal(kospi.index, us)

    all_kr = {**BIG, **SUPPLIERS, **BENCH}
    data = {t: load(t) for t in all_kr}

    # 1. Data quality
    q = pd.DataFrame([quality_report(t, df) for t, df in data.items()]).set_index("ticker")
    q.insert(0, "name", [all_kr[t] for t in q.index])
    lines += ["## 1. Data quality (Yahoo Korean daily bars)", "", "```", q.to_string(), "```", ""]

    rets = {t: kr_returns(df) for t, df in data.items()}
    groups = {
        "KOSPI": rets["^KS11"],
        "Samsung": rets["005930.KS"],
        "SK Hynix": rets["000660.KS"],
        "Suppliers (EW)": pd.concat({t: rets[t] for t in SUPPLIERS}, axis=1, sort=True).T.groupby(level=1).mean().T,
    }

    n_tests = 0
    reg_rows, bucket_rows, big_rows = [], [], []
    for period, (a, b) in PERIODS.items():
        s = signal.loc[a:b, "us_oc"]
        for g, r in groups.items():
            r = r.loc[a:b]
            bg, tg, r2g, _ = hac_beta(r["gap"], s)
            bi, ti, r2i, n = hac_beta(r["intraday"], s)
            p_perm = perm_pvalue(r["intraday"], s, rng)
            n_tests += 1
            reg_rows.append({"period": period, "group": g, "n": n,
                             "gap beta": round(bg, 3), "gap R2": round(r2g, 3),
                             "intraday beta": round(bi, 3), "intraday t(HAC)": round(ti, 2),
                             "placebo p": round(p_perm, 3)})

            d = pd.concat([r["intraday"], s], axis=1, sort=True).dropna()
            d["bucket"] = pd.qcut(d["us_oc"], 5, labels=["Q1 (US down most)", "Q2", "Q3", "Q4", "Q5 (US up most)"])
            m = d.groupby("bucket", observed=True)["intraday"].mean() * 100
            bucket_rows.append({"period": period, "group": g, **{k: round(v, 3) for k, v in m.items()}})

            for label, mask in [("US up > 2%", d["us_oc"] > BIG_MOVE), ("US down < -2%", d["us_oc"] < -BIG_MOVE)]:
                x = d.loc[mask, "intraday"]
                t = x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan
                n_tests += 1
                big_rows.append({"period": period, "group": g, "night": label, "n": len(x),
                                 "mean intraday %": round(100 * x.mean(), 3), "t": round(t, 2),
                                 "beats cost?": bool(abs(x.mean()) > COST_ROUND_TRIP)})

    lines += ["## 2. How much is priced at the open, and what is left after it", "",
              "- `gap beta`: Korean opening gap per 1.0 of US overnight move (priced at the open).",
              "- `intraday beta`: open-to-close move per 1.0 of US move. > 0 continuation (underreaction), < 0 reversal (overreaction).",
              "- `placebo p`: share of shuffled nights giving a |beta| at least as large.", "",
              "```", pd.DataFrame(reg_rows).to_string(index=False), "```", ""]
    lines += ["## 3. Mean Korean open-to-close return (%) by US overnight quintile", "",
              "```", pd.DataFrame(bucket_rows).to_string(index=False), "```", ""]
    lines += [f"## 4. Big US nights (|SOXX overnight| > {BIG_MOVE:.0%})", "",
              f"`beats cost?` = |mean| above the {COST_ROUND_TRIP:.2%} round-trip cost (a necessary, not sufficient, condition).", "",
              "```", pd.DataFrame(big_rows).to_string(index=False), "```", ""]
    lines += ["## Notes", "",
              f"- Formal tests in this run: {n_tests} (log them; correct for multiple testing before believing any single one).",
              "- Limitations: no US after-hours (earnings nights), no KOSPI 200 night futures control, Yahoo open prices unverified vs KRX,",
              "  suppliers list chosen with today's knowledge (HPSP only from 2022-07) — survivorship/look-ahead risk in group selection.", ""]

    out = RESULTS / "q2_explore_overnight.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
