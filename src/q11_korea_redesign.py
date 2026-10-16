"""Q11: can a long-only retail construction in Korea keep a positive risk-adjusted return?
Two designs fixed in docs/q11_korea_redesign_spec.md before running. Implementation study, not new evidence.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt
from q8_multifactor import quintile_returns

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
COST, START = 0.0030, pd.Timestamp("2023-01-01")
MIN_CAP, MIN_PRICE = 50e9, 1000
DROP_BOTTOM, N_TERCILES, PER_TERCILE = 0.40, 3, 7


def eligible(sig: pd.DataFrame, px: pd.DataFrame, mcap: pd.DataFrame, t) -> pd.Series:
    s = sig.loc[t].dropna()
    s = s[px.loc[t].reindex(s.index) >= MIN_PRICE]
    return s[mcap.loc[t].reindex(s.index).fillna(0) >= MIN_CAP]


def run(design: str, sig, px, ret, mcap, mom) -> pd.DataFrame:
    held, rows = [], []
    for t in [d for d in sig.index if d >= START]:
        if t not in ret.index:
            continue
        s = eligible(sig, px, mcap, t)
        if len(s) < 25:
            continue
        if design == "D1_avoidance":
            keep = list(s[s.rank(pct=True) > DROP_BOTTOM].index)
        elif design == "D2_momentum_neutral":
            m = mom.loc[t].reindex(s.index)
            keep = []
            for _, grp in s.groupby(pd.qcut(m.rank(method="first"), N_TERCILES, labels=False), observed=True):
                keep += list(grp.sort_values(ascending=False).head(PER_TERCILE).index)
        elif design == "top20":
            keep = list(s.sort_values(ascending=False).head(20).index)
        else:  # equal-weight universe
            keep = list(s.index)
        turn = 1.0 if not held else len(set(keep) - set(held)) / max(len(keep), 1)
        held = keep
        r = ret.loc[t].reindex(keep).dropna()
        if len(r) == 0:
            continue
        rows.append({"date": t, "ret": r.mean() - COST * turn, "n": len(r), "turnover": turn})
    return pd.DataFrame(rows).set_index("date")


def risk_adjust(r: pd.Series, index_ret, size_ls, mom_ls) -> dict:
    X = pd.DataFrame({"index": index_ret.reindex(r.index), "size": size_ls.reindex(r.index),
                      "momentum": mom_ls.reindex(r.index)})
    d = pd.concat([r.rename("y"), X], axis=1).dropna()
    m = sm.OLS(d["y"], sm.add_constant(d.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    from scipy import stats as st
    return {"months": len(d), "alpha_bp": 1e4 * m.params["const"], "alpha_t": m.tvalues["const"],
            "alpha_p_one_sided": float(st.norm.sf(m.tvalues["const"])), "beta_index": m.params["index"],
            "beta_size": m.params["size"], "beta_momentum": m.params["momentum"], "r2": m.rsquared}


def perf(r: pd.Series, bench: pd.Series) -> dict:
    ann = (1 + r).prod() ** (12 / len(r)) - 1
    vol = r.std() * np.sqrt(12)
    eq = (1 + r).cumprod()
    b = bench.reindex(r.index).dropna()
    te = (r.reindex(b.index) - b).std() * np.sqrt(12)
    return {"ann_%": 100 * ann, "vol_%": 100 * vol, "sharpe": ann / vol if vol else np.nan,
            "max_dd_%": 100 * (eq / eq.cummax() - 1).min(), "tracking_error_%": 100 * te,
            "hit_%": 100 * (r > 0).mean()}


def main() -> None:
    sig, px, ret, mcap, index_close = bt.korea()
    idx_m = index_close.resample("ME").last()
    bench = (idx_m.shift(-1) / idx_m - 1)
    bench.index = [min([d for d in px.index if d.to_period("M") == p.to_period("M")], default=pd.NaT) for p in bench.index]
    bench = bench[bench.index.notna()]
    mom = px.shift(1) / px.shift(12) - 1
    mom_ls = quintile_returns(mom, ret)["ls"]
    size_ls = quintile_returns(-np.log(mcap.where(mcap > 0)), ret)["ls"]

    decisive, extra, years = [], [], []
    for design in ["D1_avoidance", "D2_momentum_neutral", "top20", "universe_equal_weight"]:
        out = run(design, sig, px, ret, mcap, mom)
        if not len(out):
            continue
        r = out["ret"]
        row = {"design": design, **risk_adjust(r, bench, size_ls, mom_ls), **perf(r, bench),
               "avg_holdings": round(out["n"].mean(), 1), "turnover": round(out["turnover"].mean(), 2)}
        (decisive if design in ("D1_avoidance", "D2_momentum_neutral") else extra).append(row)
        for y, g in r.groupby(r.index.year):
            bg = bench.reindex(g.index).dropna()
            years.append({"design": design, "year": y, "strategy_%": 100 * ((1 + g).prod() - 1),
                          "index_%": 100 * ((1 + bg).prod() - 1) if len(bg) else np.nan})

    dec = pd.DataFrame(decisive)
    dec["p_holm"] = multipletests(dec["alpha_p_one_sided"], method="holm")[1]
    dec["pass"] = (dec["p_holm"] < 0.10) & (dec["alpha_bp"] > 0)

    def fmt(x):
        return "```\n" + pd.DataFrame(x).to_string(index=False, float_format=lambda v: f"{v:.2f}") + "\n```"

    L = ["# Q11 — Korea implementation redesign", "",
         "Follows `docs/q11_korea_redesign_spec.md` (committed before running). Decisive number: alpha after controlling",
         "for the KOSPI, a size spread and a momentum spread (HAC 3 lags), one-sided positive, Holm over the two designs.",
         "Implementation study on data already used — not new evidence.", "",
         "## Decisive: the two new designs", "", fmt(dec), "",
         f"**Pass: {', '.join(dec.loc[dec['pass'], 'design']) or 'neither design'}**", "",
         "## Reference portfolios (not decisive)", "", fmt(extra), "",
         "## Year by year", "", fmt(years), ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q11_korea_redesign.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
