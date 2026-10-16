"""Q8 step 0: when did the AI era start? Structural-break estimate on series that are NOT Q8 outcomes.

Q8's outcomes are Korean chip-stock returns, so the break date is estimated only from:
  (a) Korean semiconductor exports (KCS releases, working-day adjusted YoY) — a macro series;
  (b) US semiconductor index level relative to the S&P 500 (SOXX / SPY) — US prices, not part of the Q8 universe.
Method: Quandt-Andrews / sup-Wald single-break test on the mean of a monthly series (15% trimming), with a
bootstrap distribution of break dates (moving-block bootstrap, 1,000 draws) for an interval estimate.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "results" / "q8_regime_break.md"
TRIM = 0.15
N_BOOT = 1000
BLOCK = 6


def exports_series() -> pd.Series:
    """Monthly working-day-adjusted YoY growth of Korean semiconductor exports (first-release figures)."""
    df = pd.read_csv(INTERIM / "kcs_releases_extracted.csv")
    df["date"] = pd.to_datetime(df["posted"])
    wd = df["workdays_prev_year"] / df["workdays_curr_year"]
    df["adj_yoy"] = ((1 + df["semis_yoy_text"] / 100) * wd.fillna(1) - 1) * 100
    s = df.set_index("date")["adj_yoy"].sort_index()
    return s.resample("ME").mean().dropna()


def soxx_vs_spy() -> pd.Series:
    """Monthly log return of SOXX relative to SPY (US prices; not a Q8 outcome)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from q3_edge_search import load_full
    soxx = load_full("SOXX")["Close"].resample("ME").last()
    spy = load_full("SPY")["Close"].resample("ME").last()
    rel = np.log(soxx / spy).dropna()
    return rel.diff().dropna() * 100


def sup_wald(y: np.ndarray) -> tuple[int, float, np.ndarray]:
    """Single break in the mean: returns best break index, its F statistic, and F for every candidate."""
    n = len(y)
    lo, hi = int(n * TRIM), int(n * (1 - TRIM))
    ssr0 = ((y - y.mean()) ** 2).sum()
    fs = np.full(n, np.nan)
    for k in range(lo, hi):
        a, b = y[:k], y[k:]
        ssr1 = ((a - a.mean()) ** 2).sum() + ((b - b.mean()) ** 2).sum()
        fs[k] = (ssr0 - ssr1) / (ssr1 / (n - 2))
    return int(np.nanargmax(fs)), float(np.nanmax(fs)), fs


def bootstrap_breaks(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Moving-block bootstrap around the estimated break: distribution of estimated break indices."""
    k0, _, _ = sup_wald(y)
    resid = np.concatenate([y[:k0] - y[:k0].mean(), y[k0:] - y[k0:].mean()])
    fitted = np.concatenate([np.full(k0, y[:k0].mean()), np.full(len(y) - k0, y[k0:].mean())])
    n = len(y)
    out = []
    for _ in range(N_BOOT):
        idx = np.concatenate([np.arange(s, s + BLOCK) % n for s in rng.integers(0, n, n // BLOCK + 1)])[:n]
        k, _, _ = sup_wald(fitted + resid[idx])
        out.append(k)
    return np.array(out)


def analyse(name: str, s: pd.Series, rng: np.random.Generator, lines: list) -> None:
    y = s.values.astype(float)
    k, f, fs = sup_wald(y)
    boot = bootstrap_breaks(y, rng)
    dates = s.index
    ci = (dates[int(np.percentile(boot, 5))], dates[int(np.percentile(boot, 95))])
    before, after = y[:k].mean(), y[k:].mean()
    top = pd.Series(fs, index=dates).dropna().sort_values(ascending=False).head(5)
    lines += [f"### {name}", "",
              f"- months: {len(s)} ({dates[0]:%Y-%m} → {dates[-1]:%Y-%m})",
              f"- **estimated break: {dates[k]:%Y-%m}** (sup-Wald F = {f:.1f}); 90% bootstrap interval "
              f"{ci[0]:%Y-%m} → {ci[1]:%Y-%m}",
              f"- mean before {before:.2f} → after {after:.2f}",
              "- five highest-scoring break months:", "",
              "```", top.to_string(float_format=lambda v: f"{v:.1f}"), "```", ""]


def share_series() -> pd.Series:
    """Semiconductors as a share of total Korean exports (%), from first releases (available from 2019)."""
    df = pd.read_csv(INTERIM / "kcs_releases_extracted.csv")
    df["date"] = pd.to_datetime(df["posted"])
    share = 100 * df["semis_exports_usd_mn"] / (df["exports_total_usd_100mn_text"] * 100)
    s = pd.Series(share.values, index=df["date"]).dropna().sort_index()
    return s.resample("ME").mean().dropna()


def two_breaks(y: np.ndarray) -> tuple[int, int, float]:
    """Best pair of breaks in the mean (grid search, same 15% trimming and minimum segment length)."""
    n = len(y)
    lo, hi = int(n * TRIM), int(n * (1 - TRIM))
    ssr0 = ((y - y.mean()) ** 2).sum()
    best = (None, None, -np.inf)
    for k1 in range(lo, hi):
        for k2 in range(k1 + lo, hi):
            segs = [y[:k1], y[k1:k2], y[k2:]]
            ssr1 = sum(((s - s.mean()) ** 2).sum() for s in segs)
            f = (ssr0 - ssr1) / (ssr1 / (n - 3))
            if f > best[2]:
                best = (k1, k2, f)
    return best


def analyse_two(name: str, s: pd.Series, lines: list) -> None:
    y = s.values.astype(float)
    k1, k2, f = two_breaks(y)
    d = s.index
    lines += [f"### {name} — two breaks", "",
              f"- **breaks: {d[k1]:%Y-%m} and {d[k2]:%Y-%m}** (F = {f:.1f})",
              f"- means: {y[:k1].mean():.2f} → {y[k1:k2].mean():.2f} → {y[k2:].mean():.2f}", ""]


def main() -> None:
    rng = np.random.default_rng(8)
    lines = ["# Q8 step 0 — when did the AI era start?", "",
             "Break estimated **only** on series that are not Q8 outcomes (Korean chip-stock returns):",
             "Korean semiconductor exports and the US semiconductor index relative to the S&P 500.", ""]
    analyse("Korean semiconductor exports, working-day adjusted YoY (KCS first releases)", exports_series(), rng, lines)
    analyse("SOXX relative to SPY, monthly", soxx_vs_spy(), rng, lines)
    analyse("Semiconductors as a share of Korean exports (%)", share_series(), rng, lines)
    analyse_two("Korean semiconductor exports, working-day adjusted YoY", exports_series(), lines)
    analyse_two("Semiconductors as a share of Korean exports (%)", share_series(), lines)
    analyse_two("SOXX relative to SPY, monthly", soxx_vs_spy(), lines)
    lines += ["### External reference dates", "",
              "- 2022-11-30 ChatGPT public launch (start of the AI demand narrative)",
              "- 2023-05-24 Nvidia's guidance shock (AI data-centre capex repriced across semis)", ""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
