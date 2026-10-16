"""Q10: long-only 20-stock strategy backtest in Korea, Japan and Taiwan, exactly as specified in
docs/q10_strategy_spec.md (rules fixed before running; no parameter search).

Signal = "improvement composite": mean z-score of quality and earnings/revenue momentum (Taiwan: revenue momentum only).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q8_multifactor as kr
import q9_japan_test as jp
import q9_taiwan_test as tw

ROOT = Path(__file__).resolve().parents[1]
RAW, RESULTS = ROOT / "data" / "raw", ROOT / "results"
N_HOLD, COSTS = 20, {"Korea": 0.0030, "Japan": 0.0010, "Taiwan": 0.0060}
MIN_CAP = {"Korea": 50e9, "Japan": 5e9, "Taiwan": 1.5e9}
MIN_PRICE = {"Korea": 1000, "Japan": 100, "Taiwan": 10}
START = pd.Timestamp("2023-01-01")


def zmean(frames: list[pd.DataFrame]) -> pd.DataFrame:
    stack = pd.concat([kr.zscores(f) for f in frames], axis=0, keys=range(len(frames)))
    return stack.groupby(level=1).mean().where(stack.groupby(level=1).count() >= 1)


def korea():
    u = kr.universe()
    cal = pd.read_parquet(RAW / "full_IDX_KS11.parquet").index
    px, ret = kr.monthly_panel(u, cal)
    f, mcap = kr.build_factors(u, px, px.index)
    sig = zmean([f["quality"], f["earn_mom"]])
    return sig, px, ret, mcap, pd.read_parquet(RAW / "full_IDX_KS11.parquet")["Close"]


def japan():
    master = pd.read_csv(RAW / "jquants" / "master.csv", dtype={"Code": str})
    uni = set(master.loc[master["S33Nm"].isin(jp.SECTORS), "Code"])
    fins = pd.read_csv(RAW / "jquants" / "fins_summary.csv", dtype={"Code": str})
    cal = pd.read_parquet(RAW / "full_IDX_N225.parquet").index
    px, ret = jp.monthly(RAW / "q9_jp_prices", cal)
    f = jp.build(jp.quarterly_profits(fins[fins["Code"].isin(uni)]), px)
    sig = zmean([f["quality"], f["earn_mom"]])
    shares = None  # no share counts on the free plan -> market-cap filter approximated by price filter only
    return sig, px, ret, shares, pd.read_parquet(RAW / "full_IDX_N225.parquet")["Close"]


def taiwan():
    u = tw.universe()
    px, ret = tw.monthly_prices(list(u["code"]))
    sig = zmean([tw.revenue_factor(px)])
    return sig, px, ret, None, pd.read_parquet(RAW / "full_IDX_TWII.parquet")["Close"]


def backtest(name, sig, px, ret, mcap, n_hold=N_HOLD, step=1) -> tuple[pd.Series, pd.Series]:
    """Equal-weight top-n portfolio, rebalanced every `step` months, net of costs."""
    cost, held, rows, turns = COSTS[name], [], [], []
    months = [t for t in sig.index if t >= START]
    for i, t in enumerate(months):
        if t not in ret.index:
            continue
        ok = sig.loc[t].dropna()
        ok = ok[px.loc[t].reindex(ok.index) >= MIN_PRICE[name]]
        if mcap is not None:
            ok = ok[mcap.loc[t].reindex(ok.index).fillna(0) >= MIN_CAP[name]]
        if len(ok) < 5:
            continue
        if i % step == 0 or not held:
            new = list(ok.sort_values(ascending=False).head(n_hold).index)
            turn = 1.0 if not held else len(set(new) - set(held)) / max(len(new), 1)
            held = new
        else:
            turn = 0.0
        r = ret.loc[t].reindex(held).dropna()
        if len(r) == 0:
            continue
        rows.append({"date": t, "ret": r.mean() - cost * turn, "gross": r.mean(), "n": len(r)})
        turns.append(turn)
    out = pd.DataFrame(rows).set_index("date")
    out["turnover"] = turns
    return out["ret"], out


def stats(r: pd.Series, bench: pd.Series | None = None) -> dict:
    if len(r) < 3:
        return {}
    ann = (1 + r).prod() ** (12 / len(r)) - 1
    vol = r.std() * np.sqrt(12)
    eq = (1 + r).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    d = {"months": len(r), "ann_return_%": 100 * ann, "ann_vol_%": 100 * vol, "sharpe": ann / vol if vol else np.nan,
         "max_drawdown_%": 100 * dd, "hit_rate_%": 100 * (r > 0).mean(), "best_%": 100 * r.max(), "worst_%": 100 * r.min()}
    if bench is not None and len(bench):
        b = bench.reindex(r.index).dropna()
        common = r.index.intersection(b.index)
        if len(common) > 2:
            ex = r.loc[common] - b.loc[common]
            d["bench_ann_%"] = 100 * ((1 + b.loc[common]).prod() ** (12 / len(common)) - 1)
            d["excess_ann_%"] = d["ann_return_%"] - d["bench_ann_%"]
            d["tracking_error_%"] = 100 * ex.std() * np.sqrt(12)
    return d


def main() -> None:
    L = ["# Q10 — long-only 20-stock strategy backtest", "",
         "Rules fixed in `docs/q10_strategy_spec.md` before running. Long only, equal weight, monthly rebalance,",
         "net of costs (Korea 0.30%, Japan 0.10%, Taiwan 0.60% per unit of turnover). Signal: quality + earnings/revenue",
         "momentum (value dropped: it failed in Korea and had the wrong sign in Taiwan).", "",
         "**This reuses the data that produced the signals — it is a cost-and-implementation study, not new evidence.**", ""]
    summary, per_year, sens = [], [], []
    for name, fn in [("Korea", korea), ("Japan", japan), ("Taiwan", taiwan)]:
        sig, px, ret, mcap, index_close = fn()
        idx_m = index_close.resample("ME").last()
        bench = (idx_m.shift(-1) / idx_m - 1)
        bench.index = bench.index.to_period("M").to_timestamp("M")
        r, detail = backtest(name, sig, px, ret, mcap)
        if not len(r):
            L += [f"## {name}: no usable months", ""]
            continue
        b = bench.copy()
        b.index = [min([d for d in r.index if d.to_period("M") == p.to_period("M")], default=pd.NaT) for p in b.index]
        b = b[b.index.notna()]
        summary.append({"market": name, **stats(r, b), "avg_turnover": round(detail["turnover"].mean(), 2),
                        "avg_holdings": round(detail["n"].mean(), 1)})
        for y, g in r.groupby(r.index.year):
            bg = b.reindex(g.index).dropna()
            row = {"market": name, "year": y, "months": len(g), "strategy_%": 100 * ((1 + g).prod() - 1)}
            if len(bg):
                row["index_%"] = 100 * ((1 + bg).prod() - 1)
                row["excess_%"] = row["strategy_%"] - row["index_%"]
            per_year.append(row)
        for n_hold in (10, 20, 30):
            rr, _ = backtest(name, sig, px, ret, mcap, n_hold=n_hold)
            sens.append({"market": name, "variant": f"top {n_hold}", **{k: round(v, 2) for k, v in stats(rr).items()}})
        rr, _ = backtest(name, sig, px, ret, mcap, step=3)
        sens.append({"market": name, "variant": "quarterly rebalance", **{k: round(v, 2) for k, v in stats(rr).items()}})
        trimmed = r.copy()
        trimmed.loc[trimmed.nlargest(max(1, len(r) // 100)).index] = trimmed.median()
        sens.append({"market": name, "variant": "best months replaced by median", **{k: round(v, 2) for k, v in stats(trimmed).items()}})

    def fmt(rows):
        return "```\n" + pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.2f}") + "\n```"

    L += ["## Strategy vs local index", "", fmt(summary), "",
          "## Year by year (net of costs)", "", fmt(per_year), "",
          "## Sensitivity (reported, not used to choose)", "", fmt(sens), ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q10_strategy_backtest.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
