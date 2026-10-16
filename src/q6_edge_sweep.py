"""Q6: broad edge sweep (14 tests, one Holm family) — as pre-registered in docs/q6_edge_sweep_preregistration.md.

Discovery (2023-01 -> 2025-06) on all 14 tests; validation (2025-07 -> 2026-09-16) ONLY for tests that pass discovery.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from krx_manual_import import read_krx  # noqa: E402
from q3_edge_search import load_full  # noqa: E402
from q4_supplier_rebound import MARKETS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
MANUAL = ROOT / "data" / "raw" / "krx_manual"
NAVER = ROOT / "data" / "raw" / "naver_flows"
EARNINGS = ROOT / "data" / "interim" / "us_earnings_dates.csv"

DISCOVERY = ("2023-01-01", "2025-06-30")
VALIDATION = ("2025-07-01", "2026-09-16")
KRX_START = pd.Timestamp("2023-01-02")
N_DRAWS = 5000
MIN_SHIFT = 20
MIN_STOCKS = 25

INDEX = {"KR": "^KS11", "TW": "^TWII", "JP": "^N225"}
BASKETS = {f"{m}_{kind}": MARKETS[m]["big" if kind == "BIG" else "suppliers"] for m in INDEX for kind in ("BIG", "SUP")}


# ---------- prices ----------

_cache: dict[str, pd.DataFrame] = {}


def prices(ticker: str) -> pd.DataFrame:
    if ticker not in _cache:
        df = load_full(ticker)
        flat = (df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"])
        no_vol = (df["Volume"] == 0) if not ticker.startswith("^") else False
        _cache[ticker] = df.mask(flat | no_vol | (df["Open"] <= 0))
    return _cache[ticker]


def calendar(market: str) -> pd.DatetimeIndex:
    cal = load_full(INDEX[market] if market in INDEX else market).index
    return cal[cal >= "2016-01-01"]


def stock_returns(ticker: str, cal: pd.DatetimeIndex) -> pd.DataFrame:
    df = prices(ticker).reindex(cal)
    o, c = df["Open"], df["Close"]
    return pd.DataFrame({"oc": c / o - 1, "cc": c / c.shift(1) - 1, "gap": o / c.shift(1) - 1,
                         "past5": c / c.shift(5) - 1, "h5": c.shift(-5) / o.shift(-1) - 1})


def basket(name: str) -> pd.DataFrame:
    market = name.split("_")[0]
    cal = calendar(market)
    parts = [stock_returns(t, cal) for t in BASKETS[name]]
    return pd.concat(parts).groupby(level=0).mean()


def in_period(idx: pd.DatetimeIndex, period: tuple[str, str]) -> np.ndarray:
    return (idx >= period[0]) & (idx <= period[1])


# ---------- generic statistics ----------

def ols(y: np.ndarray, x: np.ndarray, hac_lags: int | None) -> tuple[float, float, float]:
    X = sm.add_constant(x)
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags}) if hac_lags else sm.OLS(y, X).fit()
    return fit.params[1], fit.tvalues[1], fit.pvalues[1]


def quintile_spread_bp(x: pd.Series, y: pd.Series) -> float:
    q = pd.qcut(x, 5, labels=False, duplicates="drop")
    return (y[q == q.max()].mean() - y[q == q.min()].mean()) * 1e4


def regression_test(d: pd.DataFrame, hac_lags: int, rng) -> dict:
    """Continuous signal: slope, HAC t, circular-shift placebo."""
    x, y = d["x"].values, d["y"].values
    slope, t, p = ols(y, x, hac_lags)
    n = len(d)
    draws = np.array([ols(y, np.roll(x, rng.integers(MIN_SHIFT, n - MIN_SHIFT)), hac_lags)[1] for _ in range(N_DRAWS)])
    return {"n": n, "effect": slope * 1e4, "effect_unit": "bp per 1.0 of x", "t": t, "p": p,
            "placebo_p": float((np.abs(draws) >= abs(t)).mean()), "size_bp": quintile_spread_bp(d["x"], d["y"])}


def event_regression_test(d: pd.DataFrame, pool: pd.DataFrame, rng) -> dict:
    """Sparse events: plain OLS slope, placebo = random days from the pool."""
    slope, t, p = ols(d["y"].values, d["x"].values, None)
    n = len(d)
    draws = []
    for _ in range(N_DRAWS):
        s = pool.iloc[rng.choice(len(pool), n, replace=False)]
        draws.append(ols(s["y"].values, s["x"].values, None)[1])
    return {"n": n, "effect": slope * 1e4, "effect_unit": "bp per 1.0 of x", "t": t, "p": p,
            "placebo_p": float((np.abs(np.array(draws)) >= abs(t)).mean()), "size_bp": quintile_spread_bp(d["x"], d["y"])}


def event_mean_test(y: pd.Series, is_event: pd.Series, rng) -> dict:
    """Event days vs other days: Welch t, placebo = random day sets of the same size."""
    y = y.dropna()
    ev = is_event.reindex(y.index).fillna(False).astype(bool)
    a, b = y[ev].values, y[~ev].values
    diff = a.mean() - b.mean()
    w = stats.ttest_ind(a, b, equal_var=False)
    vals, n = y.values, len(a)
    draws = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        m = np.zeros(len(vals), dtype=bool)
        m[rng.choice(len(vals), n, replace=False)] = True
        draws[i] = vals[m].mean() - vals[~m].mean()
    return {"n": n, "effect": diff * 1e4, "effect_unit": "bp event − other", "t": w.statistic, "p": w.pvalue,
            "placebo_p": float((np.abs(draws) >= abs(diff)).mean()), "size_bp": diff * 1e4}


# ---------- test definitions ----------

def test_A(asia: str, us: str, period, rng) -> dict:
    x = basket(asia)["cc"]
    u = prices(us)
    y = (u["Close"] / u["Open"] - 1).rename("y")
    d = pd.concat([x.rename("x"), y], axis=1, join="inner").dropna()
    return regression_test(d[in_period(d.index, period)], 1, rng)


def test_B(name: str, period, rng) -> dict:
    b = basket(name)
    d = b[["past5", "h5"]].set_axis(["x", "y"], axis=1).dropna()
    return regression_test(d[in_period(d.index, period)], 5, rng)


def cross_section_panels(freq: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Country-neutral formation returns F[t] and next-period holding returns H[t+1], indexed by holding period start."""
    form, hold, country = {}, {}, {}
    for m in INDEX:
        cal = calendar(m)
        for t in MARKETS[m]["big"] + MARKETS[m]["suppliers"]:
            df = prices(t).reindex(cal)
            key = df.index.to_period(freq)
            last_close = df["Close"].groupby(key).last()
            first_open = df["Open"].groupby(key).first()
            form[t] = last_close / last_close.shift(1) - 1
            hold[t] = last_close / first_open - 1
            country[t] = m
    F = pd.DataFrame(form).sort_index()
    H = pd.DataFrame(hold).sort_index().shift(-1)  # holding return of the NEXT period, aligned to formation period t
    country = pd.Series(country)
    for m in INDEX:
        cols = country[country == m].index
        F[cols] = F[cols].sub(F[cols].mean(axis=1), axis=0)
        H[cols] = H[cols].sub(H[cols].mean(axis=1), axis=0)
    nxt = pd.PeriodIndex(F.index, freq=freq) + 1
    F.index = H.index = nxt.start_time  # label by holding period start
    return F, H, country


def spread(f: np.ndarray, h: np.ndarray) -> float:
    ok = ~np.isnan(f) & ~np.isnan(h)
    if ok.sum() < MIN_STOCKS:
        return np.nan
    f, h = f[ok], h[ok]
    k = int(round(len(f) * 0.2))
    order = np.argsort(f)
    return h[order[:k]].mean() - h[order[-k:]].mean()  # losers − winners


def test_C(freq: str, period, rng) -> dict:
    F, H, _ = cross_section_panels(freq)
    sel = in_period(F.index, period)
    F, H = F[sel].values, H[sel].values
    s = np.array([spread(F[i], H[i]) for i in range(len(F))])
    valid = ~np.isnan(s)
    s_obs = s[valid]
    t = stats.ttest_1samp(s_obs, 0.0)
    rows = np.where(valid)[0]
    draws = np.empty(N_DRAWS)
    for j in range(N_DRAWS):
        vals = []
        for i in rows:
            f = F[i].copy()
            ok = ~np.isnan(f) & ~np.isnan(H[i])
            f[ok] = rng.permutation(f[ok])
            vals.append(spread(f, H[i]))
        draws[j] = np.nanmean(vals)
    return {"n": int(valid.sum()), "effect": s_obs.mean() * 1e4, "effect_unit": "bp losers − winners per period",
            "t": t.statistic, "p": t.pvalue, "placebo_p": float((np.abs(draws) >= abs(s_obs.mean())).mean()),
            "size_bp": s_obs.mean() * 1e4}


def expiry_days(cal: pd.DatetimeIndex) -> pd.DatetimeIndex:
    out = []
    for month in pd.period_range(cal.min(), cal.max(), freq="M"):
        days = pd.date_range(month.start_time, month.end_time, freq="D")
        second_thu = days[days.weekday == 3][1]
        prior = cal[cal <= second_thu]
        if len(prior) and prior[-1].to_period("M") == month:
            out.append(prior[-1])
    return pd.DatetimeIndex(out)


def test_E1(period, rng) -> dict:
    b = basket("KR_BIG")
    y = b["oc"][in_period(b.index, period)]
    ev = pd.Series(y.index.isin(expiry_days(calendar("KR"))), index=y.index)
    return event_mean_test(y, ev, rng)


def test_E2(period, rng) -> dict:
    cal = calendar("KR")
    k = prices("^KS11").reindex(cal)["Close"]
    y = (k / k.shift(1) - 1)
    s = pd.Series(cal, index=cal)
    month = cal.to_period("M")
    rank_fwd = s.groupby(month).cumcount()
    rank_back = s.groupby(month).cumcount(ascending=False)
    tom = (rank_fwd < 3) | (rank_back == 0)
    y = y[in_period(y.index, period)]
    return event_mean_test(y, tom.reindex(y.index), rng)


def big2_foreign_value(cal: pd.DatetimeIndex) -> pd.Series:
    total = []
    for code in ("005930", "000660"):
        krx = pd.concat([read_krx(p) for p in sorted(MANUAL.glob(f"{code}_*.csv"))])
        krx = krx[~krx.index.duplicated()].sort_index()
        krx_val = krx["Foreigners"] + krx["Other foreigners"]
        nav = pd.read_parquet(NAVER / f"{code}.parquet")
        nav_val = nav["foreign_net_shares"] * nav["close"]
        total.append(pd.concat([nav_val[nav_val.index < KRX_START], krx_val[krx_val.index >= KRX_START]]).reindex(cal))
    return pd.concat(total, axis=1).sum(axis=1, min_count=2)


def test_F1(period, rng) -> dict:
    cal = calendar("KR")
    neg = (big2_foreign_value(cal) < 0).astype(int)
    run = neg.groupby((neg != neg.shift()).cumsum()).cumsum() * neg
    b = basket("KR_BIG")
    y = b["h5"][in_period(b.index, period)]
    return event_mean_test(y, (run == 5).reindex(y.index), rng)


def test_H1(period, rng) -> dict:
    cal = calendar("KR")
    e = pd.read_csv(EARNINGS)
    days = sorted({cal[cal > pd.Timestamp(d)][0] for d in e["us_date"] if (cal > pd.Timestamp(d)).any()})
    b = basket("KR_BIG")[["gap", "oc"]].set_axis(["x", "y"], axis=1).dropna()
    b = b[in_period(b.index, period)]
    d = b[b.index.isin(days)]
    return event_regression_test(d, b, rng)


TESTS = {
    "A1": ("KR_BIG cc → SOXX oc (same date)", lambda p, r: test_A("KR_BIG", "SOXX", p, r)),
    "A2": ("KR_BIG cc → MU oc (same date)", lambda p, r: test_A("KR_BIG", "MU", p, r)),
    "A3": ("TW_BIG cc → SOXX oc (same date)", lambda p, r: test_A("TW_BIG", "SOXX", p, r)),
    "A4": ("JP_BIG cc → SOXX oc (same date)", lambda p, r: test_A("JP_BIG", "SOXX", p, r)),
    "B1": ("KR_BIG past 5d → h5", lambda p, r: test_B("KR_BIG", p, r)),
    "B2": ("KR_SUP past 5d → h5", lambda p, r: test_B("KR_SUP", p, r)),
    "B3": ("TW_SUP past 5d → h5", lambda p, r: test_B("TW_SUP", p, r)),
    "B4": ("JP_SUP past 5d → h5", lambda p, r: test_B("JP_SUP", p, r)),
    "C1": ("39 names weekly reversal (losers − winners)", lambda p, r: test_C("W-FRI", p, r)),
    "C2": ("39 names monthly reversal (losers − winners)", lambda p, r: test_C("M", p, r)),
    "E1": ("KR_BIG oc on KOSPI200 options expiry", test_E1),
    "E2": ("KOSPI cc on turn of month", test_E2),
    "F1": ("KR_BIG h5 after 5-day foreign selling streak", test_F1),
    "H1": ("MU/NVDA earnings: KR_BIG gap → oc", test_H1),
}


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n```"


def run(ids, period, rng) -> pd.DataFrame:
    rows = []
    for i in ids:
        label, fn = TESTS[i]
        print(f"  running {i} {label} ...", file=sys.stderr, flush=True)
        rows.append({"id": i, "test": label, **fn(period, rng)})
    return pd.DataFrame(rows)


def main() -> None:
    rng = np.random.default_rng(42)
    L = ["# Q6 — Broad edge sweep (14 tests, one Holm family)", "",
         "Follows `docs/q6_edge_sweep_preregistration.md` (committed before this script was written).", "",
         f"Discovery {DISCOVERY[0]} → {DISCOVERY[1]}; validation {VALIDATION[0]} → {VALIDATION[1]}. Two-sided. "
         "size_bp = top − bottom signal quintile (A/B/H), mean spread (C), event − other (E/F). "
         "Costs: 0.30% round trip (C: ~0.60% per period).", ""]

    disc = run(TESTS, DISCOVERY, rng)
    disc["p_holm"] = multipletests(disc["p"], method="holm")[1]
    disc["pass"] = (disc["p_holm"] < 0.10) & (disc["placebo_p"] < 0.05)
    L += ["## Discovery (decisive)", "", fmt(disc), ""]

    survivors = disc.loc[disc["pass"], "id"].tolist()
    if not survivors:
        L += ["**No test passed discovery → validation not run (as pre-registered). No edge found.**", ""]
    else:
        val = run(survivors, VALIDATION, rng)
        val["p_holm"] = multipletests(val["p"], method="holm")[1]
        sign = np.sign(disc.set_index("id").loc[survivors, "effect"].values)
        val["edge"] = (val["p_holm"] < 0.05) & (val["placebo_p"] < 0.05) & (np.sign(val["effect"].values) == sign)
        L += [f"Survivors: {', '.join(survivors)}", "", "## Validation — survivors only", "", fmt(val), "",
              f"**Edges confirmed: {', '.join(val.loc[val['edge'], 'id']) or 'none'}**", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q6_edge_sweep.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
