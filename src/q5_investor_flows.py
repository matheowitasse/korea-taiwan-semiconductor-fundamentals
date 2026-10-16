"""Q5: do foreign / retail investor flows predict Korean chip stock returns? — as pre-registered in
docs/q5_investor_flows_preregistration.md.

Discovery (2023-01 -> 2025-06) on all 8 tests; validation (2025-07 -> 2026-09-16) ONLY for tests that pass discovery.
Flows: KRX hand downloads (data/raw/krx_manual/), with Naver only to fill the 60-day z-score window before 2023-01-02.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from krx_manual_import import read_krx  # noqa: E402
from q3_edge_search import load_full  # noqa: E402
from q4_supplier_rebound import us_signal  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "data" / "raw" / "krx_manual"
NAVER = ROOT / "data" / "raw" / "naver_flows"
RESULTS = ROOT / "results"

DISCOVERY = ("2023-01-01", "2025-06-30")
VALIDATION = ("2025-07-01", "2026-09-16")
KRX_START = pd.Timestamp("2023-01-02")
N_DRAWS = 5000
WINDOW, MIN_OBS = 60, 40
HAC_LAGS = 5
MIN_SHIFT = 20
BIG_DOWN = -0.02

BIG2 = ["005930", "000660"]
SUP = ["042700", "000990", "058470", "095340", "240810", "036930", "084370", "403870"]
YAHOO = {"005930": "005930.KS", "000660": "000660.KS", "042700": "042700.KS", "000990": "000990.KS",
         "058470": "058470.KQ", "095340": "095340.KQ", "240810": "240810.KQ", "036930": "036930.KQ",
         "084370": "084370.KQ", "403870": "403870.KQ", "KOSPI": "^KS11"}

TESTS = {  # id: (basket, investor group, horizon, big-down days only)
    "T1": ("BIG2", "foreign", "h1", False),
    "T2": ("BIG2", "foreign", "h5", False),
    "T3": ("SUP", "foreign", "h1", False),
    "T4": ("SUP", "foreign", "h5", False),
    "T5": ("BIG2", "individual", "h5", False),
    "T6": ("SUP", "individual", "h5", False),
    "T7": ("BIG2", "foreign", "h5", True),
    "T8": ("KOSPI", "foreign", "h5", False),
}


# ---------- data ----------

def load_krx(name: str) -> pd.DataFrame:
    df = pd.concat([read_krx(p) for p in sorted(MANUAL.glob(f"{name}_*.csv"))])
    return df[~df.index.duplicated()].sort_index()


def zscore(s: pd.Series) -> pd.Series:
    past = s.shift(1).rolling(WINDOW, min_periods=MIN_OBS)
    return (s - past.mean()) / past.std()


def stock_flow_z(code: str, cal: pd.DatetimeIndex) -> dict[str, pd.Series]:
    nav = pd.read_parquet(NAVER / f"{code}.parquet")
    krx = load_krx(code)
    traded = (nav["close"] * nav["volume"]).where(nav["volume"] > 0)
    out = {}
    for group, krx_cols, nav_col in [("foreign", ["Foreigners", "Other foreigners"], "foreign_net_shares"),
                                     ("individual", ["Individuals"], "individual_net_shares")]:
        krx_ratio = krx[krx_cols].sum(axis=1) / traded.reindex(krx.index)
        nav_ratio = (nav[nav_col] / nav["volume"].where(nav["volume"] > 0))
        ratio = pd.concat([nav_ratio[nav_ratio.index < KRX_START], krx_ratio[krx_ratio.index >= KRX_START]])
        out[group] = zscore(ratio.clip(-1, 1).reindex(cal))
    return out


def kospi_flow_z(cal: pd.DatetimeIndex) -> pd.Series:
    krx = load_krx("KOSPI")
    krx_val = krx["Foreigners"] + krx["Other foreigners"]
    nav = pd.read_parquet(NAVER / "index_KOSPI.parquet")
    nav_val = nav["foreign_net_100m_krw"] * 1e8
    val = pd.concat([nav_val[nav_val.index < KRX_START], krx_val[krx_val.index >= KRX_START]])
    return zscore(val.reindex(cal))


def returns(ticker: str, cal: pd.DatetimeIndex) -> pd.DataFrame:
    df = load_full(ticker)
    flat = (df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"])
    no_volume = (df["Volume"] == 0) if not ticker.startswith("^") else False  # Yahoo index volume is unreliable
    bad = flat | no_volume | (df["Open"] <= 0)
    df = df.mask(bad).reindex(cal)
    o1 = df["Open"].shift(-1)
    return pd.DataFrame({"h1": df["Close"].shift(-1) / o1 - 1, "h5": df["Close"].shift(-5) / o1 - 1})


def build() -> tuple[pd.DataFrame, pd.Series]:
    cal = load_full("^KS11").index
    cal = cal[cal >= "2016-01-01"]
    cols = {}
    for basket, codes in [("BIG2", BIG2), ("SUP", SUP)]:
        z = {g: [] for g in ("foreign", "individual")}
        r = {h: [] for h in ("h1", "h5")}
        for c in codes:
            fz = stock_flow_z(c, cal)
            rr = returns(YAHOO[c], cal)
            for g in z:
                z[g].append(fz[g])
            for h in r:
                r[h].append(rr[h])
        for g in z:
            cols[f"{basket}_{g}"] = pd.concat(z[g], axis=1).mean(axis=1)
        for h in r:
            cols[f"{basket}_{h}"] = pd.concat(r[h], axis=1).mean(axis=1)
    cols["KOSPI_foreign"] = kospi_flow_z(cal)
    kr = returns("^KS11", cal)
    cols["KOSPI_h1"], cols["KOSPI_h5"] = kr["h1"], kr["h5"]
    data = pd.DataFrame(cols, index=cal)
    soxx = us_signal(cal, load_full("SOXX")).reindex(cal)
    return data, soxx


# ---------- tests ----------

def ols_t(y: np.ndarray, x: np.ndarray, hac: bool) -> tuple[float, float, float]:
    X = sm.add_constant(x)
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS}) if hac else sm.OLS(y, X).fit()
    return fit.params[1], fit.tvalues[1], fit.pvalues[1]


def run_test(test_id: str, data: pd.DataFrame, soxx: pd.Series, period: tuple[str, str],
             rng: np.random.Generator) -> dict:
    basket, group, horizon, event_only = TESTS[test_id]
    d = data.loc[period[0]:period[1], [f"{basket}_{group}", f"{basket}_{horizon}"]].dropna()
    d.columns = ["x", "y"]
    pool = d
    if event_only:
        d = d[soxx.reindex(d.index) < BIG_DOWN]
    x, y = d["x"].values, d["y"].values
    slope, t, p = ols_t(y, x, hac=not event_only)

    draws = np.empty(N_DRAWS)
    n = len(d)
    for i in range(N_DRAWS):
        if event_only:
            s = pool.iloc[rng.choice(len(pool), n, replace=False)]
            draws[i] = ols_t(s["y"].values, s["x"].values, hac=False)[1]
        else:
            k = rng.integers(MIN_SHIFT, n - MIN_SHIFT)
            draws[i] = ols_t(y, np.roll(x, k), hac=True)[1]

    q = pd.qcut(d["x"], 5, labels=False, duplicates="drop")
    top, bottom = d.loc[q == q.max(), "y"].mean(), d.loc[q == q.min(), "y"].mean()
    return {"id": test_id, "signal": f"{basket} {group} z", "return": horizon, "sell-off days only": event_only,
            "n": n, "slope_bp_per_z": slope * 1e4, "t": t, "p": p,
            "placebo_p": float((np.abs(draws) >= abs(t)).mean()),
            "top_q_bp": top * 1e4, "bottom_q_bp": bottom * 1e4, "top_minus_bottom_bp": (top - bottom) * 1e4}


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n```"


def main() -> None:
    rng = np.random.default_rng(42)
    data, soxx = build()
    ids = list(TESTS)

    L = ["# Q5 — Do investor flows predict Korean chip stock returns?", "",
         "Follows `docs/q5_investor_flows_preregistration.md` (committed before this script was written).", "",
         f"Discovery {DISCOVERY[0]} → {DISCOVERY[1]}; validation {VALIDATION[0]} → {VALIDATION[1]}. "
         "Signal = 60-day z-score of day-D net buying (KRX); return starts at the open of D+1. "
         "Slope in bp of return per 1 z. Two-sided. Costs ignored (0.30% round trip for reference).", ""]

    cover = data.loc[DISCOVERY[0]:VALIDATION[1]].notna().mean().mul(100).round(1)
    L += ["Data coverage 2023-01 → 2026-09 (% of KOSPI trading days with a value):", "", "```",
          cover.to_string(), "```", ""]

    disc = pd.DataFrame([run_test(i, data, soxx, DISCOVERY, rng) for i in ids])
    disc["p_holm"] = multipletests(disc["p"], method="holm")[1]
    disc["pass"] = (disc["p_holm"] < 0.10) & (disc["placebo_p"] < 0.05)
    L += ["## Discovery (decisive)", "", fmt(disc), ""]

    survivors = disc.loc[disc["pass"], "id"].tolist()
    if not survivors:
        L += ["**No test passed discovery → validation not run (as pre-registered). No edge found.**", ""]
    else:
        val = pd.DataFrame([run_test(i, data, soxx, VALIDATION, rng) for i in survivors])
        val["p_holm"] = multipletests(val["p"], method="holm")[1]
        sign = disc.set_index("id").loc[survivors, "slope_bp_per_z"].values
        val["edge"] = (val["p_holm"] < 0.05) & (val["placebo_p"] < 0.05) & (np.sign(val["slope_bp_per_z"]) == np.sign(sign))
        L += [f"Survivors: {', '.join(survivors)}", "", "## Validation — survivors only", "", fmt(val), "",
              f"**Edges confirmed: {', '.join(val.loc[val['edge'], 'id']) or 'none'}**", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q5_investor_flows.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
