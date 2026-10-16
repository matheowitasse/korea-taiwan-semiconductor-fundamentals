"""Q14: does hedging the index make the long leg tradable? Rules fixed in docs/q14_hedged_spec.md before running."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt
from q8_multifactor import nw_stats, quintile_returns

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
START = pd.Timestamp("2023-01-01")
STOCK_COST, FUT_COST, BETA_WINDOW = 0.0030, 0.0002, 24
MIN_CAP = {"Korea": 50e9, "Taiwan": 1.5e9}
MIN_PRICE = {"Korea": 1000, "Taiwan": 10}


def long_leg(name, sig, px, ret, mcap) -> pd.DataFrame:
    held, rows = [], []
    for t in [d for d in sig.index if d >= START]:
        if t not in ret.index:
            continue
        s = sig.loc[t].dropna()
        s = s[px.loc[t].reindex(s.index) >= MIN_PRICE[name]]
        if mcap is not None:
            s = s[mcap.loc[t].reindex(s.index).fillna(0) >= MIN_CAP[name]]
        if len(s) < 25:
            continue
        keep = list(s[s.rank(pct=True) > 0.8].index)
        turn = 1.0 if not held else len(set(keep) - set(held)) / max(len(keep), 1)
        held = keep
        r = ret.loc[t].reindex(keep).dropna()
        if len(r):
            rows.append({"date": t, "gross": r.mean(), "net": r.mean() - STOCK_COST * turn, "n": len(r)})
    return pd.DataFrame(rows).set_index("date")


def hedged(port: pd.Series, bench: pd.Series, rule: str) -> pd.Series:
    b = bench.reindex(port.index)
    out = {}
    for i, t in enumerate(port.index):
        if rule == "H2_full":
            beta = 1.0
        else:  # rolling beta from the previous 24 months only
            hist = pd.concat([port.iloc[:i], b.iloc[:i]], axis=1).dropna().tail(BETA_WINDOW)
            if len(hist) < BETA_WINDOW:
                continue
            beta = sm.OLS(hist.iloc[:, 0], sm.add_constant(hist.iloc[:, 1])).fit().params.iloc[1]
        if np.isfinite(b.iloc[i]):
            out[t] = port.iloc[i] - beta * b.iloc[i] - FUT_COST
    return pd.Series(out)


def main() -> None:
    rows, extra, years = [], [], []
    for name, fn in [("Korea", bt.korea), ("Taiwan", bt.taiwan)]:
        sig, px, ret, mcap, index_close = fn()
        idx = index_close.resample("ME").last()
        bench = (idx.shift(-1) / idx - 1)
        bench.index = [min([d for d in px.index if d.to_period("M") == p.to_period("M")], default=pd.NaT)
                       for p in bench.index]
        bench = bench[bench.index.notna()]
        leg = long_leg(name, sig, px, ret, mcap)
        mom_ls = quintile_returns(px.shift(1) / px.shift(12) - 1, ret)["ls"]
        size_ls = quintile_returns(-np.log(mcap.where(mcap > 0)), ret)["ls"] if mcap is not None else None

        for rule in ["H1_rolling_beta", "H2_full"]:
            h = hedged(leg["net"], bench, rule)
            if len(h) < 6:
                rows.append({"market": name, "rule": rule, "months": len(h)})
                continue
            st = nw_stats(h)
            st["p_one_sided"] = float(stats.norm.sf(st["t"]))
            eq = (1 + h).cumprod()
            controls = pd.DataFrame({"momentum": mom_ls.reindex(h.index)})
            if size_ls is not None:
                controls["size"] = size_ls.reindex(h.index)
            d = pd.concat([h.rename("y"), controls], axis=1).dropna()
            m = sm.OLS(d["y"], sm.add_constant(d.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
            row = {"market": name, "rule": rule, "months": st["months"], "mean_bp": st["mean_bp"], "t": st["t"],
                   "p_one_sided": st["p_one_sided"], "ann_%": 100 * ((1 + h).prod() ** (12 / len(h)) - 1),
                   "vol_%": 100 * h.std() * np.sqrt(12), "max_dd_%": 100 * (eq / eq.cummax() - 1).min(),
                   "hit_%": 100 * (h > 0).mean(), "alpha_vs_size_mom_bp": 1e4 * m.params["const"],
                   "alpha_t": m.tvalues["const"]}
            (rows if name == "Korea" else extra).append(row)
            for y, g in h.groupby(h.index.year):
                years.append({"market": name, "rule": rule, "year": y, "return_%": 100 * ((1 + g).prod() - 1)})

        un = leg["net"]
        extra.append({"market": name, "rule": "unhedged long-only", "months": len(un), **nw_stats(un),
                      "ann_%": 100 * ((1 + un).prod() ** (12 / len(un)) - 1), "vol_%": 100 * un.std() * np.sqrt(12)})

    dec = pd.DataFrame(rows)
    if len(dec):
        ok = dec["p_one_sided"].notna()
        dec.loc[ok, "p_holm"] = multipletests(dec.loc[ok, "p_one_sided"], method="holm")[1]
        dec["pass"] = (dec["p_holm"] < 0.05) & (dec["mean_bp"] > 0)

    def fmt(x):
        return "```\n" + pd.DataFrame(x).to_string(index=False, float_format=lambda v: f"{v:.2f}") + "\n```"

    L = ["# Q14 — market-hedged implementation", "",
         "Follows `docs/q14_hedged_spec.md` (committed before running). Long top quintile, short the index",
         "(H1: beta from the previous 24 months only; H2: 1:1). Costs: 0.30% per unit of stock turnover, 0.02%/month futures.",
         "Implementation study on data already used; it cannot change the frozen finding.", "",
         "## Decisive: Korea", "", fmt(dec), "",
         f"**Pass: {', '.join(dec.loc[dec.get('pass', False) == True, 'rule']) if len(dec) else 'n/a'}**" if len(dec) else "",
         "", "## Reported only (Taiwan, and the unhedged portfolios)", "", fmt(extra), "",
         "## Year by year", "", fmt(years), ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q14_hedged.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
