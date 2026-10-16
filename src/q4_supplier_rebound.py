"""Q4: Asian chip suppliers rebound after big US chip sell-offs — as pre-registered in
docs/q4_supplier_rebound_preregistration.md.

Discovery (2023-01 -> 2025-06) on all 4 tests; validation (2025-07 -> 2026-09-16) ONLY for tests that pass discovery.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q3_edge_search import load_full  # noqa: E402  (Yahoo daily, 2015 -> today, cached as data/raw/full_*.parquet)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

DISCOVERY = ("2023-01-01", "2025-06-30")
VALIDATION = ("2025-07-01", "2026-09-16")
THRESHOLD = -0.02
N_DRAWS = 5000
US_SIGNAL = "SOXX"

MARKETS = {
    "KR": {"index": "^KS11",
           "suppliers": ["042700.KS", "000990.KS", "058470.KQ", "095340.KQ", "240810.KQ", "036930.KQ", "084370.KQ", "403870.KQ"],
           "big": ["005930.KS", "000660.KS"]},
    "TW": {"index": "^TWII",
           "suppliers": ["3711.TW", "3661.TW", "3443.TW", "2449.TW", "2360.TW", "3680.TWO", "5274.TWO", "6669.TW",
                         "2382.TW", "2383.TW", "2368.TW", "6515.TW", "6223.TWO"],
           "big": ["2330.TW", "2454.TW"]},
    "JP": {"index": "^N225",
           "suppliers": ["6146.T", "6920.T", "7735.T", "6525.T", "6526.T", "4062.T", "6590.T", "7729.T", "6315.T",
                         "6871.T", "6323.T", "6890.T"],
           "big": ["8035.T", "6857.T"]},
}


def intraday(ticker: str, cal: pd.DatetimeIndex) -> pd.Series:
    df = load_full(ticker)
    bad = (df["Volume"] == 0) | ((df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"]))
    df = df.mask(bad).reindex(cal)
    return df["Close"] / df["Open"] - 1


def us_signal(cal: pd.DatetimeIndex, us: pd.DataFrame) -> pd.Series:
    us_oc = us["Close"] / us["Open"] - 1
    vals = {}
    for prev, cur in zip(cal[:-1], cal[1:]):
        w = us_oc[(us_oc.index >= prev) & (us_oc.index < cur)]
        vals[cur] = float(np.prod(1 + w.values) - 1) if len(w) else 0.0
    return pd.Series(vals)


def build() -> dict:
    us = load_full(US_SIGNAL)
    out = {}
    for m, cfg in MARKETS.items():
        cal = load_full(cfg["index"]).index
        out[m] = pd.DataFrame({
            "signal": us_signal(cal, us),
            "suppliers": pd.concat([intraday(t, cal) for t in cfg["suppliers"]], axis=1).mean(axis=1),
            "big": pd.concat([intraday(t, cal) for t in cfg["big"]], axis=1).mean(axis=1),
        }).iloc[1:]
    return out


def in_period(idx: pd.DatetimeIndex, period: tuple[str, str]) -> np.ndarray:
    return (idx >= period[0]) & (idx <= period[1])


def event_and_pool(data: dict, test_id: str, period: tuple[str, str], col: str) -> tuple[pd.Series, pd.Series]:
    if test_id != "POOL":
        d = data[test_id][in_period(data[test_id].index, period)]
        return d.loc[d["signal"] < THRESHOLD, col].dropna(), d[col].dropna()
    ev = pd.concat({m: d[col].where(d["signal"] < THRESHOLD) for m, d in data.items()}, axis=1, sort=True)
    allv = pd.concat({m: d[col] for m, d in data.items()}, axis=1, sort=True)
    ev, allv = ev[in_period(ev.index, period)], allv[in_period(allv.index, period)]
    return ev.mean(axis=1).dropna(), allv.mean(axis=1).dropna()


def test(data: dict, test_id: str, period: tuple[str, str], rng: np.random.Generator, col: str = "suppliers") -> dict:
    ev, pool = event_and_pool(data, test_id, period, col)
    t = stats.ttest_1samp(ev.values, 0.0, alternative="greater")
    draws = np.array([rng.choice(pool.values, len(ev), replace=False).mean() for _ in range(N_DRAWS)])
    return {"id": test_id, "n_nights": len(ev), "mean_bp": ev.mean() * 1e4, "all_days_mean_bp": pool.mean() * 1e4,
            "hit_rate_%": (ev > 0).mean() * 100, "t": t.statistic, "p_one_sided": t.pvalue,
            "placebo_p": float((draws >= ev.mean()).mean())}


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n```"


def main() -> None:
    rng = np.random.default_rng(42)
    data = build()
    ids = ["KR", "TW", "JP", "POOL"]

    L = ["# Q4 — Asian chip suppliers after big US chip sell-offs (SOXX overnight < −2%)", "",
         "Follows `docs/q4_supplier_rebound_preregistration.md` (committed before running).", "",
         f"Discovery {DISCOVERY[0]} → {DISCOVERY[1]}; validation {VALIDATION[0]} → {VALIDATION[1]}. "
         "Returns = open→close on the Asian session after the US night. Costs ignored.", ""]

    disc = pd.DataFrame([test(data, i, DISCOVERY, rng) for i in ids])
    disc["p_holm"] = multipletests(disc["p_one_sided"], method="holm")[1]
    disc["pass"] = (disc["p_holm"] < 0.10) & (disc["placebo_p"] < 0.05)
    L += ["## Discovery — supplier baskets (decisive)", "", fmt(disc), ""]

    big = pd.DataFrame([test(data, i, DISCOVERY, rng, col="big") for i in ids])
    L += ["Contrast, not decisive — large names (Samsung/SK Hynix, TSMC/MediaTek, Tokyo Electron/Advantest):", "", fmt(big), ""]

    survivors = disc.loc[disc["pass"], "id"].tolist()
    if not survivors:
        L += ["**No test passed discovery → validation not run (as pre-registered). No edge found.**", ""]
    else:
        val = pd.DataFrame([test(data, i, VALIDATION, rng) for i in survivors])
        val["p_holm"] = multipletests(val["p_one_sided"], method="holm")[1]
        val["edge"] = (val["p_holm"] < 0.05) & (val["placebo_p"] < 0.05) & (val["mean_bp"] > 0)
        L += [f"Survivors: {', '.join(survivors)}", "", "## Validation — survivors only", "", fmt(val), "",
              f"**Edges confirmed: {', '.join(val.loc[val['edge'], 'id']) or 'none'}**", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q4_supplier_rebound.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
