"""Q8 live tracker: record the portfolio the pre-registered rules pick each month, then score it afterwards.

Everything before today is already used up (discovery + validation), so only FUTURE months are honest evidence.
This script writes down the picks at the time, so they cannot be changed later.

Monthly routine (run after the last trading day of the month):
  python src/q8_extend_prices.py            # refresh prices
  python src/q8_dart_financials.py          # refresh DART accounts (needs DART_API_KEY)
  python src/q7_dart_operating_profit.py    # refresh operating profit + SUE
  python src/q8_live_tracker.py record      # write this month's portfolio
  python src/q8_live_tracker.py evaluate    # score the months that have completed

Files: data/live/portfolio_<YYYY-MM>.csv (the picks) and data/live/live_results.csv (realised monthly returns).

Note: picks are recorded as of the latest available price date. If that is mid-month, the first live period runs from
that date to the end of the next month (slightly longer than the month-end-to-month-end periods used in the backtest).
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q8_multifactor import RAW, build_factors, composite, monthly_panel, nw_stats, universe

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "live"
TRACKED = ["composite", "quality", "earn_mom"]  # the three that passed discovery AND validation


def current_state():
    u = universe()
    cal = pd.read_parquet(RAW / "full_IDX_KS11.parquet").index
    px, ret = monthly_panel(u, cal)
    factors, mcap = build_factors(u, px, px.index)
    factors = {"composite": composite(factors), **factors}
    names = dict(zip(u["stock_code"], u["corp_name"]))
    return px, ret, factors, mcap, names


def record() -> None:
    LIVE.mkdir(parents=True, exist_ok=True)
    px, ret, factors, mcap, names = current_state()
    t = px.index[-1]
    rows = []
    for f in TRACKED:
        s = factors[f].loc[t].dropna()
        if len(s) < 25:
            print(f"{f}: only {len(s)} scored stocks — skipped")
            continue
        top = s[s.rank(method="first") > 0.8 * len(s)]
        for code, score in top.items():
            rows.append({"month_end": t.date(), "factor": f, "stock_code": code, "name": names.get(code, ""),
                         "score": round(float(score), 4), "price": float(px.at[t, code]),
                         "market_cap_bn_krw": round(float(mcap.at[t, code]) / 1e9, 1) if np.isfinite(mcap.at[t, code]) else np.nan})
    if not rows:
        print("nothing recorded")
        return
    out = LIVE / f"portfolio_{t:%Y-%m}.csv"
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"recorded {len(df)} picks for {t:%Y-%m} ({df['factor'].value_counts().to_dict()}) -> {out}")
    print("universe size:", px.loc[t].notna().sum())


def evaluate() -> None:
    px, ret, factors, mcap, names = current_state()
    rows = []
    for f in sorted(LIVE.glob("portfolio_*.csv")):
        picks = pd.read_csv(f, dtype={"stock_code": str})
        t = pd.Timestamp(picks["month_end"].iloc[0])
        if t not in ret.index or ret.loc[t].notna().sum() == 0:
            print(f"{t:%Y-%m}: next month not complete yet")
            continue
        r = ret.loc[t]
        universe_ret = r.dropna().mean()
        for fac, g in picks.groupby("factor"):
            held = r.reindex(g["stock_code"]).dropna()
            rows.append({"month_end": t.date(), "factor": fac, "n_held": len(held),
                         "portfolio_%": round(100 * held.mean(), 2), "universe_%": round(100 * universe_ret, 2),
                         "excess_%": round(100 * (held.mean() - universe_ret), 2)})
    if not rows:
        print("no completed months yet")
        return
    res = pd.DataFrame(rows)
    res.to_csv(LIVE / "live_results.csv", index=False, encoding="utf-8-sig")
    print(res.to_string(index=False))
    print("\nrunning record since live tracking started:")
    for fac, g in res.groupby("factor"):
        st = nw_stats(g["excess_%"] / 100)
        print(f"  {fac:10s} months {st['months']:3d} | mean excess {st['mean_bp'] / 100:6.2f}%/month | t {st['t']:5.2f} "
              f"| positive months {100 * (g['excess_%'] > 0).mean():.0f}%")
    print("\nReminder: expected to be much smaller than the 2025-26 boom result. Judge after 6-12 months.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["record", "evaluate"])
    a = ap.parse_args()
    record() if a.what == "record" else evaluate()
