"""Q3 edge search A-E, exactly as pre-registered in docs/q3_edge_search_preregistration.md.

Discovery (2016-08 -> 2022-12) on all 8 tests; validation (2023-01 -> today) is run ONLY for tests that pass discovery.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf
from scipy import stats
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q1_test_signal import build_signals  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EXTRACTED = ROOT / "data" / "interim" / "kcs_releases_extracted.csv"
RESULTS = ROOT / "results"

DISCOVERY = ("2016-08-01", "2022-12-31")
VALIDATION = ("2023-01-01", "2026-09-16")
N_DRAWS = 5000

SAMSUNG, HYNIX, KOSPI = "005930.KS", "000660.KS", "^KS11"
SUPPLIERS = ["042700.KS", "000990.KS", "058470.KQ", "095340.KQ", "240810.KQ", "036930.KQ", "084370.KQ", "403870.KQ"]

TESTS = {
    "A1": ("Pre-release drift, Big2 on D-1", "event", "big2", "Dm1"),
    "A2": ("Pre-release drift, Suppliers on D-1", "event", "supp", "Dm1"),
    "B1": ("Release-day premium, Big2 on D", "event", "big2", "D"),
    "B2": ("Release-day premium, Suppliers on D", "event", "supp", "D"),
    "B3": ("Release-day premium, KOSPI on D", "event", "kospi", "D"),
    "C": ("Suppliers open->close on D vs S2", "reg", "supp_intraday", 2),
    "D": ("SK Hynix minus Samsung on D vs S2", "reg", "pair", 2),
    "E": ("SK Hynix close(D)->close(D+20) vs S2", "reg", "hynix_post20", 3),
}


def load_full(ticker: str) -> pd.DataFrame:
    cache = RAW / f"full_{ticker.replace('^', 'IDX_')}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = yf.Ticker(ticker).history(start="2015-01-01", end=str(date.today() + timedelta(days=1)), auto_adjust=True)
    df.index = df.index.tz_localize(None).normalize()
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.to_parquet(cache)
    return df


def clean_prices(df: pd.DataFrame, cal: pd.DatetimeIndex) -> pd.DataFrame:
    bad = (df["Volume"] == 0) | ((df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"]))
    df = df.mask(bad).reindex(cal)
    out = pd.DataFrame(index=cal)
    out["close"] = df["Close"]
    out["ret"] = df["Close"] / df["Close"].shift(1) - 1
    out["intraday"] = df["Close"] / df["Open"] - 1
    return out


def daily_series(cal: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.Series]:
    p = {t: clean_prices(load_full(t), cal) for t in [SAMSUNG, HYNIX, KOSPI, *SUPPLIERS]}
    s = pd.DataFrame(index=cal)
    s["big2"] = pd.concat([p[SAMSUNG]["ret"], p[HYNIX]["ret"]], axis=1).mean(axis=1)
    s["supp"] = pd.concat([p[t]["ret"] for t in SUPPLIERS], axis=1).mean(axis=1)
    s["supp_intraday"] = pd.concat([p[t]["intraday"] for t in SUPPLIERS], axis=1).mean(axis=1)
    s["kospi"] = p[KOSPI]["ret"]
    s["pair"] = p[HYNIX]["ret"] - p[SAMSUNG]["ret"]
    return s, p[HYNIX]["close"]


def in_period(dates: pd.Series | pd.DatetimeIndex, period: tuple[str, str]):
    return (dates >= period[0]) & (dates <= period[1])


def event_test(series: pd.Series, event_days: pd.DatetimeIndex, nonevent_days: pd.DatetimeIndex,
               rng: np.random.Generator, direction: int = 0) -> dict:
    ev = series.reindex(event_days).dropna().values
    pool = series.reindex(nonevent_days).dropna().values
    diff = ev.mean() - pool.mean()
    alt = "two-sided" if direction == 0 else ("greater" if direction > 0 else "less")
    p = stats.ttest_ind(ev, pool, equal_var=False, alternative=alt).pvalue
    draws = np.array([rng.choice(pool, len(ev), replace=False).mean() for _ in range(N_DRAWS)]) - pool.mean()
    placebo = (np.abs(draws) >= abs(diff)).mean() if direction == 0 else ((direction * draws) >= direction * diff).mean()
    return {"n": len(ev), "effect_bp": diff * 1e4, "t_or_welch_p": p, "placebo_p": float(placebo), "sign": np.sign(diff)}


def reg_test(y: pd.Series, x: pd.Series, lags: int, rng: np.random.Generator, direction: int = 0) -> dict:
    d = pd.concat([y, x], axis=1).dropna()
    m = sm.OLS(d.iloc[:, 0], sm.add_constant(d.iloc[:, 1])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    slope, t = float(m.params.iloc[1]), float(m.tvalues.iloc[1])
    p = float(m.pvalues.iloc[1]) if direction == 0 else float(stats.norm.sf(direction * t))
    xc, yc = d.iloc[:, 1].values - d.iloc[:, 1].mean(), d.iloc[:, 0].values - d.iloc[:, 0].mean()
    perm = np.array([rng.permutation(xc) @ yc / (xc @ xc) for _ in range(N_DRAWS)])
    placebo = (np.abs(perm) >= abs(slope)).mean() if direction == 0 else ((direction * perm) >= direction * slope).mean()
    # effect: bp of return per +10 pp of S2
    return {"n": len(d), "effect_bp": slope * 10 * 1e4, "t_or_welch_p": p, "placebo_p": float(placebo),
            "t": t, "sign": np.sign(slope)}


def run_tests(ids, period, series, hynix_close, rel, cal, rng, directions=None) -> pd.DataFrame:
    all_D = pd.DatetimeIndex(rel["D_kr"].unique())
    all_Dm1 = pd.DatetimeIndex(rel["Dm1"].unique())
    cal_p = cal[in_period(cal, period)]
    nonevent = cal_p.difference(all_D).difference(all_Dm1)
    r = rel[in_period(rel["D_kr"], period)]
    rows = []
    for tid in ids:
        label, kind, var, arg = TESTS[tid]
        direction = 0 if directions is None else directions[tid]
        if kind == "event":
            days = pd.DatetimeIndex(r["D_kr"] if arg == "D" else r["Dm1"]).unique()
            res = event_test(series[var], days, nonevent, rng, direction)
        else:
            if var == "hynix_post20":
                pos = cal.get_indexer(r["D_kr"])
                y = pd.Series([hynix_close.iloc[i + 20] / hynix_close.iloc[i] - 1 if i + 20 < len(cal) else np.nan
                               for i in pos], index=r.index)
            else:
                y = pd.Series(series[var].reindex(r["D_kr"]).values, index=r.index)
            res = reg_test(y, r["S2"], arg, rng, direction)
        rows.append({"id": tid, "test": label, **res})
    return pd.DataFrame(rows)


def main() -> None:
    rng = np.random.default_rng(316)
    cal = load_full(KOSPI).index
    series, hynix_close = daily_series(cal)

    rel = build_signals(pd.read_csv(EXTRACTED))
    pos = cal.searchsorted(rel["D"])
    rel = rel[pos < len(cal)].copy()
    pos = pos[pos < len(cal)]
    rel["D_kr"] = cal[pos]
    rel["Dm1"] = cal[pos - 1]

    fmt = lambda df: "```\n" + df.drop(columns=["sign"], errors="ignore").to_string(index=False, float_format=lambda v: f"{v:.4f}") + "\n```"
    L = ["# Q3 edge search A–E", "", "Follows `docs/q3_edge_search_preregistration.md` (committed before running).", "",
         f"Discovery {DISCOVERY[0]} → {DISCOVERY[1]}; validation {VALIDATION[0]} → {VALIDATION[1]}.",
         "Effects: A/B = event-day minus non-event-day mean return (bp); C/D/E = bp of return per +10 pp of S2.", ""]

    disc = run_tests(list(TESTS), DISCOVERY, series, hynix_close, rel, cal, rng)
    disc["p_holm"] = multipletests(disc["t_or_welch_p"], method="holm")[1]
    disc["pass"] = (disc["p_holm"] < 0.10) & (disc["placebo_p"] < 0.05)
    L += ["## Discovery (all 8 tests)", "", fmt(disc), ""]

    survivors = disc.loc[disc["pass"], "id"].tolist()
    if not survivors:
        L += ["**No test passed discovery → no edge found among A–E. Validation not run (as pre-registered).**", ""]
    else:
        directions = {tid: int(disc.set_index("id").loc[tid, "sign"]) for tid in survivors}
        val = run_tests(survivors, VALIDATION, series, hynix_close, rel, cal, rng, directions)
        val["p_holm_one_sided"] = multipletests(val["t_or_welch_p"], method="holm")[1]
        val["edge"] = (val["p_holm_one_sided"] < 0.05) & (val["placebo_p"] < 0.05)
        L += [f"Survivors: {', '.join(survivors)}", "", "## Validation (survivors only, one-sided in discovery direction)", "",
              fmt(val), "", f"**Edges confirmed: {', '.join(val.loc[val['edge'], 'id']) or 'none'}**", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q3_edge_search.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
