"""Q1 holdout test, exactly as pre-registered in docs/q1_holdout_preregistration.md.

Run once. Uses releases posted on or after 2025-07-01 and fresh price data up to today.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q1_test_signal import build_signals, forward_returns, ols_hac  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EXTRACTED = ROOT / "data" / "interim" / "kcs_releases_extracted.csv"
RESULTS = ROOT / "results"

HOLDOUT_START = "2025-07-01"
ASSETS = ["NVDA", "SOXX", "MU"]
N_PERM = 5000
T_CRIT = -1.70
AI_ERA_INSAMPLE = ("2023-01-01", "2025-05-31")


def load_fresh(ticker: str) -> pd.DataFrame:
    cache = RAW / f"holdout_{ticker}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = yf.Ticker(ticker).history(start="2025-01-01", end=str(date.today() + timedelta(days=1)), auto_adjust=True)
    df.index = df.index.tz_localize(None).normalize()
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.to_parquet(cache)
    return df


def perm_p_one_sided(y: pd.Series, x: pd.Series, rng: np.random.Generator) -> float:
    d = pd.concat([y, x], axis=1, sort=True).dropna()
    yv, xv = d.iloc[:, 0].values, d.iloc[:, 1].values
    xc, yc = xv - xv.mean(), yv - yv.mean()
    beta = xc @ yc / (xc @ xc)
    perm = np.array([rng.permutation(xc) @ yc / (xc @ xc) for _ in range(N_PERM)])
    return float((perm <= beta).mean())


def main() -> None:
    rng = np.random.default_rng(2025)
    rel = build_signals(pd.read_csv(EXTRACTED))

    # Tercile cut-offs from in-sample AI-era S2 only (no holdout information)
    ai = rel[(rel["D"] >= AI_ERA_INSAMPLE[0]) & (rel["D"] <= AI_ERA_INSAMPLE[1])]["S2"].dropna()
    lo, hi = ai.quantile([1 / 3, 2 / 3])

    hold = rel[rel["D"] >= HOLDOUT_START].copy()
    for t in ASSETS:
        hold = pd.concat([hold, forward_returns(hold, load_fresh(t), t)], axis=1)
    hold = hold[hold["NVDA_r5"].notna() & hold["S2"].notna()].copy()
    hold["tercile"] = np.where(hold["S2"] >= hi, "top", np.where(hold["S2"] <= lo, "bottom", "middle"))

    L = ["# Q1 holdout test — AI-era \"sell the news\"", "",
         "Follows `docs/q1_holdout_preregistration.md` (committed before any post-2025-06 data was loaded). Run once.", "",
         f"- Holdout releases used: {len(hold)} ({hold['posted'].min()} → {hold['posted'].max()})",
         f"- In-sample AI-era S2 tercile cut-offs: bottom ≤ {lo:.1f} pp, top ≥ {hi:.1f} pp", "",
         "## Releases", "", "```",
         hold[["posted", "type", "semis_yoy_text", "S2", "tercile", "NVDA_r5", "SOXX_r5"]]
         .to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", ""]

    # Primary
    y, x = hold["NVDA_r5"], hold["S2"]
    prim = ols_hac(y, x)
    p_perm = perm_p_one_sided(y, x, rng)
    top = hold.loc[hold["tercile"] == "top", "NVDA_r5"]
    bot = hold.loc[hold["tercile"] == "bottom", "NVDA_r5"]
    c1 = prim["t"] < T_CRIT
    c2 = p_perm < 0.05
    c3 = len(top) > 0 and len(bot) > 0 and top.mean() < bot.mean()
    L += ["## Primary test: NVDA 5-day return on S2 (one-sided, slope < 0)", "", "```",
          f"n = {prim['n']}, slope per 1 pp of S2 = {prim['slope'] * 100:.4f}% , HAC t = {prim['t']:.2f}, placebo p (one-sided) = {p_perm:.3f}",
          f"mean NVDA r5: top tercile {100 * top.mean():.2f}% (n={len(top)}), bottom tercile {100 * bot.mean():.2f}% (n={len(bot)})",
          "```", "",
          f"1. HAC t < {T_CRIT}: **{'PASS' if c1 else 'FAIL'}**",
          f"2. placebo p < 0.05: **{'PASS' if c2 else 'FAIL'}**",
          f"3. top-tercile mean < bottom-tercile mean: **{'PASS' if c3 else 'FAIL'}**", "",
          f"**Result: {'CONFIRMED' if (c1 and c2 and c3) else 'NOT CONFIRMED'}**", ""]

    # Reported alongside
    side = []
    for t in ["SOXX", "MU"]:
        r = ols_hac(hold[f"{t}_r5"], hold["S2"])
        side.append({"asset": t, "n": r["n"], "slope_pct_per_pp": r["slope"] * 100, "t": r["t"],
                     "placebo_p_one_sided": perm_p_one_sided(hold[f"{t}_r5"], hold["S2"], rng)})
    L += ["## Alongside (not decisive): SOXX and MU", "", "```",
          pd.DataFrame(side).to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", ""]

    out = RESULTS / "q1_holdout_test.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
