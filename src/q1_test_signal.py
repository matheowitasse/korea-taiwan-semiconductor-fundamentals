"""Q1 first test, exactly as pre-registered in docs/q1_preregistration.md.

Signal from Korean chip export releases -> US semis returns after the release.
In-sample only: releases whose 20-day return window ends by 2025-06-30.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EXTRACTED = ROOT / "data" / "interim" / "kcs_releases_extracted.csv"
RESULTS = ROOT / "results"

START = "2016-01-01"
HOLDOUT_START = "2025-07-01"
US_ASSETS = ["SOXX", "NVDA", "MU"]
KR_ASSETS = {"000660.KS": "SK Hynix", "005930.KS": "Samsung"}
HORIZONS = {"r1": 1, "r5": 5, "r20": 20}
HAC_LAGS = 2
N_PERM = 5000
REGIMES = {"2016-2022": ("2016-01-01", "2022-12-31"), "2023-2025H1": ("2023-01-01", "2025-06-30")}


def load(ticker: str) -> pd.DataFrame:
    RAW.mkdir(parents=True, exist_ok=True)
    cache = RAW / f"{ticker.replace('^', 'IDX_')}.parquet"
    if cache.exists():
        df = pd.read_parquet(cache)
        if df.index.min() > pd.Timestamp(START):  # cache from another script may start later
            cache.unlink()
            return load(ticker)
    else:
        df = yf.Ticker(ticker).history(start="2015-01-01", end=HOLDOUT_START, auto_adjust=True)
        df.index = df.index.tz_localize(None).normalize()
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df.to_parquet(cache)
    return df[df.index < HOLDOUT_START]


def build_signals(rel: pd.DataFrame) -> pd.DataFrame:
    rel = rel.sort_values(["posted", "period_day_end"]).reset_index(drop=True)
    rel["D"] = pd.to_datetime(rel["posted"])
    wd_ratio = rel["workdays_prev_year"] / rel["workdays_curr_year"]
    rel["adj_yoy"] = ((1 + rel["semis_yoy_text"] / 100) * wd_ratio - 1) * 100
    prev3_adj = rel["adj_yoy"].shift(1).rolling(3, min_periods=3).mean()
    prev3_raw = rel["semis_yoy_text"].shift(1).rolling(3, min_periods=3).mean()
    rel["S1"] = rel["adj_yoy"] - prev3_adj
    rel["S2"] = rel["semis_yoy_text"] - prev3_raw
    return rel


def forward_returns(rel: pd.DataFrame, px: pd.DataFrame, prefix: str) -> pd.DataFrame:
    dates = px.index
    out = {f"{prefix}_{h}": [] for h in HORIZONS}
    out[f"{prefix}_vol5"] = []
    daily = px["Close"].pct_change()
    for d in rel["D"]:
        i = dates.searchsorted(d)  # first US trading day with date >= D
        for h, n in HORIZONS.items():
            j = i + n - 1
            out[f"{prefix}_{h}"].append(px["Close"].iloc[j] / px["Open"].iloc[i] - 1 if j < len(dates) else np.nan)
        out[f"{prefix}_vol5"].append(daily.iloc[i:i + 5].std() * np.sqrt(252) if i + 5 <= len(dates) else np.nan)
    return pd.DataFrame(out, index=rel.index)


def korean_reaction(rel: pd.DataFrame, px: pd.DataFrame, name: str) -> pd.Series:
    ret = px["Close"].pct_change()
    return rel["D"].map(lambda d: ret.get(d, np.nan)).rename(f"{name}_day0")


def ols_hac(y: pd.Series, x: pd.Series) -> dict:
    d = pd.concat([y, x], axis=1, sort=True).dropna()
    if len(d) < 20:
        return {"n": len(d), "slope": np.nan, "t": np.nan, "p": np.nan}
    m = sm.OLS(d.iloc[:, 0], sm.add_constant(d.iloc[:, 1])).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    return {"n": len(d), "slope": float(m.params.iloc[1]), "t": float(m.tvalues.iloc[1]), "p": float(m.pvalues.iloc[1])}


def perm_p(y: pd.Series, x: pd.Series, rng: np.random.Generator) -> float:
    d = pd.concat([y, x], axis=1, sort=True).dropna()
    yv, xv = d.iloc[:, 0].values, d.iloc[:, 1].values
    xc, yc = xv - xv.mean(), yv - yv.mean()
    beta = xc @ yc / (xc @ xc)
    perm = np.array([rng.permutation(xc) @ yc / (xc @ xc) for _ in range(N_PERM)])
    return float((np.abs(perm) >= abs(beta)).mean())


def tercile_spread(y: pd.Series, x: pd.Series) -> tuple[float, float, float, int]:
    d = pd.concat([y, x], axis=1, sort=True).dropna()
    d.columns = ["y", "x"]
    d["t"] = pd.qcut(d["x"], 3, labels=["bottom", "middle", "top"])
    m = d.groupby("t", observed=True)["y"].mean() * 100
    return float(m["top"]), float(m["bottom"]), float(m["top"] - m["bottom"]), len(d)


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n```"


def main() -> None:
    rng = np.random.default_rng(7)
    RESULTS.mkdir(parents=True, exist_ok=True)
    rel = build_signals(pd.read_csv(EXTRACTED))

    for t in US_ASSETS:
        rel = pd.concat([rel, forward_returns(rel, load(t), t)], axis=1)
    for t, name in KR_ASSETS.items():
        rel[f"{name}_day0"] = korean_reaction(rel, load(t), name)

    # In-sample rule: the 20-day window must be complete before the holdout starts
    ins = rel[rel["SOXX_r20"].notna() & (rel["D"] < HOLDOUT_START)].copy()
    ins.to_csv(ROOT / "data" / "interim" / "q1_insample_panel.csv", index=False, encoding="utf-8-sig")

    L = ["# Q1 first test — Korean chip export releases → US semis", "",
         "Follows `docs/q1_preregistration.md` (committed before this run).", "",
         "## Sample", "",
         f"- In-sample releases: {len(ins)} ({ins['posted'].min()} → {ins['posted'].max()})",
         f"- With S1 (working-day adjusted, needs 3 prior adjusted releases): {ins['S1'].notna().sum()}",
         f"- With S2 (raw YoY): {ins['S2'].notna().sum()}", ""]

    # ---- Primary test
    y, x = ins["SOXX_r5"], ins["S1"]
    prim = ols_hac(y, x)
    prim["placebo_p"] = perm_p(y, x, rng)
    top, bot, spread, n_t = tercile_spread(y, x)
    regime = []
    for name, (a, b) in REGIMES.items():
        sub = ins[(ins["D"] >= a) & (ins["D"] <= b)]
        r = ols_hac(sub["SOXX_r5"], sub["S1"])
        regime.append({"regime": name, **r})
    same_sign = len({np.sign(r["slope"]) for r in regime if not np.isnan(r["slope"])}) == 1
    c1 = prim["t"] > 2 and prim["placebo_p"] < 0.05
    c2 = same_sign
    c3 = spread > 0.5
    L += ["## Primary test: SOXX 5-day return on S1", "", fmt(pd.DataFrame([prim])), "",
          "Regime split:", "", fmt(pd.DataFrame(regime)), "",
          f"Tercile means of SOXX r5 (%): top {top:.2f}, bottom {bot:.2f}, spread {spread:.2f} (n={n_t})", "",
          "Pre-registered criteria:",
          f"1. t > 2 and placebo p < 0.05: **{'PASS' if c1 else 'FAIL'}**",
          f"2. same slope sign in both regimes: **{'PASS' if c2 else 'FAIL'}**",
          f"3. top − bottom tercile spread > 0.5 pp: **{'PASS' if c3 else 'FAIL'}**",
          f"\n**Primary result: {'PROMISING' if (c1 and c2 and c3) else 'NOT PROMISING'}**", ""]

    # ---- Secondary tests
    sec = []
    for sig in ["S1", "S2"]:
        for asset in US_ASSETS:
            for h in HORIZONS:
                r = ols_hac(ins[f"{asset}_{h}"], ins[sig])
                sec.append({"signal": sig, "asset": asset, "horizon": h, **r})
    sec = pd.DataFrame(sec)
    ok = sec["p"].notna()
    sec.loc[ok, "p_holm"] = multipletests(sec.loc[ok, "p"], method="holm")[1]
    L += ["## Secondary tests (18 regressions, Holm-corrected)", "", fmt(sec), ""]

    # ---- Regime detail for S2 (longer history)
    reg2 = []
    for name, (a, b) in REGIMES.items():
        sub = ins[(ins["D"] >= a) & (ins["D"] <= b)]
        for asset in US_ASSETS:
            r = ols_hac(sub[f"{asset}_r5"], sub["S2"])
            reg2.append({"signal": "S2", "regime": name, "asset": asset, "horizon": "r5", **r})
    L += ["## S2 by regime (r5)", "", fmt(pd.DataFrame(reg2)), ""]

    # ---- Volatility
    vol = []
    for sig in ["S1", "S2"]:
        d = ins[["SOXX_vol5", sig]].dropna()
        r_abs = ols_hac(d["SOXX_vol5"], d[sig].abs())
        r_neg = ols_hac(d["SOXX_vol5"], (d[sig] < 0).astype(float))
        vol.append({"test": f"vol5 ~ |{sig}|", **r_abs, "placebo_p": perm_p(d["SOXX_vol5"], d[sig].abs(), rng)})
        vol.append({"test": f"vol5 ~ 1[{sig}<0]", **r_neg, "placebo_p": perm_p(d["SOXX_vol5"], (d[sig] < 0).astype(float), rng)})
    L += ["## Volatility: SOXX 5-day realised vol (annualised) after releases", "", fmt(pd.DataFrame(vol)), ""]

    # ---- Korean same-day reaction (context: is the release priced in Korea on day D?)
    kr = []
    for name in KR_ASSETS.values():
        for sig in ["S1", "S2"]:
            kr.append({"asset": name, "signal": sig, **ols_hac(ins[f"{name}_day0"], ins[sig])})
    L += ["## Context: Korean same-day reaction (close D-1 → close D)", "", fmt(pd.DataFrame(kr)), ""]

    n_tests = 1 + len(sec) + len(reg2) + len(vol) + len(kr) + len(regime)
    L += ["## Notes", "", f"- Total regressions run: {n_tests}. Only the primary test was pre-registered as decisive.", ""]

    out = RESULTS / "q1_first_test.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
