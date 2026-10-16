"""Q29: the standard-methods checks a referee will ask for — as pre-registered in
docs/q29_referee_robustness_preregistration.md (committed before this script was written).

Decisive (one-sided, t > 2, Newey-West 3 lags): F1 Fama-MacBeth Korea, F2 Fama-MacBeth Taiwan,
A1 extended factor alpha Korea, U1 rule-only Korean universe. Secondary: F3, F4. Descriptive: S1, D1, D2.

Usage: python src/q29_referee_robustness.py
Output: results/q29_referee_robustness.md, data/interim/q29_*.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402
import q22_extended_history as ext  # noqa: E402
import q23_korea_wide_quality as kw  # noqa: E402
import q9_taiwan_test as tw  # noqa: E402
from q8_multifactor import nw_stats, quintile_returns, zscores  # noqa: E402
from q18_short_ban import controls_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW, INTERIM, RESULTS = ROOT / "data" / "raw", ROOT / "data" / "interim", ROOT / "results"
KR = ("2016-11-01", "2026-08-31")
TW = ("2016-01-01", "2026-08-31")
KR_CAPS = ("2022-07-01", "2026-08-31")
A1_WIN = ("2016-12-01", "2026-08-31")
RULE = ("261", "29271", "262")
MIN_XS = 25


def window(df, a, b):
    return df[(df.index >= a) & (df.index <= b)]


def to_month(s: pd.Series) -> pd.Series:
    out = s.copy()
    out.index = pd.PeriodIndex(pd.to_datetime(out.index), freq="M")
    return out[~out.index.duplicated()]


# ---------------------------------------------------------------- Korean panels

def korea_components(u, px):
    """Quality and SUE panels (the two halves of the signal), same point-in-time rule as Q22."""
    f = ext.quarterly_fundamentals()
    by_corp = {c: g for c, g in f.groupby("corp_code")}
    code2corp = dict(zip(u["stock_code"], u["corp_code"]))
    quality = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    earn = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    for code in px.columns:
        g = by_corp.get(code2corp.get(code, ""))
        if g is None:
            continue
        for t in px.index:
            if not np.isfinite(px.at[t, code]):
                continue
            known = g[g["avail"] <= t]
            if not len(known):
                continue
            r = known.iloc[-1]
            if np.isfinite(r["assets"]) and r["assets"] > 0 and np.isfinite(r["op_ttm"]):
                quality.at[t, code] = r["op_ttm"] / r["assets"]
            if np.isfinite(r["sue"]):
                earn.at[t, code] = r["sue"]
    return quality, earn


def signal_from(quality, earn):
    stack = pd.concat([zscores(quality), zscores(earn)], axis=0, keys=[0, 1])
    return stack.groupby(level=1).mean().where(stack.groupby(level=1).count() >= 1)


def korea_caps_and_bm(u, px):
    """Market cap = latest KRX quarter-end shares x month-end price (snapshots start 2022-06);
    book-to-market = point-in-time book equity / market cap."""
    snap = pd.read_parquet(INTERIM / "krx_marketcap_quarterly.parquet")
    snap["date"] = pd.to_datetime(snap["date"])
    shares = snap.pivot_table(index="date", columns="stock_code", values="shares", aggfunc="last")
    sh = shares.reindex(shares.index.union(px.index)).ffill().reindex(px.index)
    sh = sh.reindex(columns=px.columns)
    sh[px.index < shares.index.min()] = np.nan
    mcap = px * sh

    fin = pd.read_csv(INTERIM / "dart_financials.csv", dtype={"corp_code": str})
    fin = fin[fin["account"] == "자본총계"].copy()
    fin["pref"] = (fin["fs_div"] == "CFS").astype(int)
    fin = fin.sort_values("pref", ascending=False).drop_duplicates(["corp_code", "year", "quarter"])
    code2corp = dict(zip(u["stock_code"], u["corp_code"]))
    corp2rows = {c: g for c, g in fin.groupby("corp_code")}
    book = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    for code in px.columns:
        g = corp2rows.get(code2corp.get(code, ""))
        if g is None:
            continue
        vals = {}
        for _, r in g.iterrows():
            q_end = pd.Timestamp(year=int(r["year"]), month=int(r["quarter"]) * 3, day=1) + pd.offsets.MonthEnd(0)
            vals[q_end + pd.Timedelta(days=90 if int(r["quarter"]) == 4 else 45)] = r["amount"]
        s = pd.Series(vals).sort_index()
        book[code] = s.reindex(s.index.union(px.index)).ffill().reindex(px.index)
    bm = (book / mcap).where((book > 0) & (mcap > 0))
    return mcap, bm


# ---------------------------------------------------------------- market-wide Korean factors (ex chip)

def assets_growth_panel(fins, month_ends, code_of):
    """Four-quarter growth in total assets, usable after the statutory deadline (as KOR-QMJ's quality)."""
    fins = fins[fins["account"] == "자산총계"].copy()
    fins["pref"] = (fins["fs_div"] == "CFS").astype(int)
    fins = fins.sort_values("pref", ascending=False).drop_duplicates(["corp_code", "year", "quarter"])
    out = {}
    for corp, g in fins.groupby("corp_code"):
        code = code_of.get(corp)
        if code is None:
            continue
        s = pd.Series(g["amount"].values, index=(g["year"] * 4 + g["quarter"]).values).sort_index()
        s = s[~s.index.duplicated()]
        s = s.reindex(range(int(s.index.min()), int(s.index.max()) + 1))
        growth = (s / s.shift(4) - 1).where(s.shift(4) > 0).dropna()
        vals = {}
        for tq, v in growth.items():
            year, quarter = (tq - 1) // 4, (tq - 1) % 4 + 1
            q_end = pd.Timestamp(year=int(year), month=quarter * 3, day=1) + pd.offsets.MonthEnd(0)
            vals[q_end + pd.Timedelta(days=90 if quarter == 4 else 45)] = v
        if vals:
            s2 = pd.Series(vals).sort_index()
            out[code] = s2.reindex(s2.index.union(month_ends)).ffill().reindex(month_ends)
    return pd.DataFrame(out)


def market_wide_factors():
    px = pd.read_parquet(kw.PRICES)
    px = px[~px.index.duplicated()].sort_index()
    ret = px.shift(-1) / px - 1
    chip = set(pd.read_csv(INTERIM / "q22_universe_codes.csv", dtype=str)["stock_code"])
    keep = [c for c in px.columns if c not in chip]
    px, ret = px[keep], ret[keep]
    fins = pd.read_csv(kw.FINS, dtype={"corp_code": str})
    u = kw.listed()
    code_of = dict(zip(u["corp_code"], u["stock_code"]))
    ag = assets_growth_panel(fins, px.index, code_of).reindex(columns=px.columns)
    cma = kw.spread(kw.zscore(-ag), ret)                         # conservative (low growth) minus aggressive
    mom = px.shift(1) / px.shift(12) - 1
    umd = kw.spread(kw.zscore(mom), ret)
    qmj = pd.read_csv(INTERIM / "kr_wide_quality_factor.csv", index_col=0, parse_dates=True)["kor_qmj_ex_chip"]
    f = pd.DataFrame({"rmw_ex_chip": to_month(qmj), "cma_ex_chip": to_month(cma), "umd_ex_chip": to_month(umd)})
    f.to_csv(INTERIM / "q29_market_wide_factors.csv")
    return f, int(ag.notna().sum(axis=1).median())


# ---------------------------------------------------------------- estimators

def fama_macbeth(y_ret, regs: dict, a, b):
    """Monthly cross-sectional OLS; returns the time series of slope coefficients."""
    rows = {}
    for t in y_ret.index:
        if not (a <= str(t.date()) <= b):
            continue
        d = pd.concat({"y": y_ret.loc[t], **{k: v.loc[t] if t in v.index else pd.Series(dtype=float)
                                              for k, v in regs.items()}}, axis=1).dropna()
        if len(d) < MIN_XS:
            continue
        X = d.drop(columns="y")
        X = X.loc[:, X.std() > 0]                       # a regressor constant in one month carries no information
        m = sm.OLS(d["y"], sm.add_constant(X, has_constant="add")).fit()
        rows[t] = m.params.drop("const")
        rows[t]["n"] = len(d)
        rows[t]["r2"] = m.rsquared
    return pd.DataFrame(rows).T


def fm_summary(coefs, name):
    out = []
    for c in [c for c in coefs.columns if c not in ("n", "r2")]:
        st = nw_stats(coefs[c])
        out.append({"test": name, "regressor": c, "months": st["months"], "coef_bp_per_sd": st["mean_bp"],
                    "t": st["t"], "median_names": float(coefs["n"].median()), "avg_r2": float(coefs["r2"].mean())})
    return out


def regress(y, X):
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    m = sm.OLS(d["y"], sm.add_constant(d.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    out = {"months": len(d), "alpha_bp": 1e4 * m.params["const"], "alpha_t": m.tvalues["const"], "r2": m.rsquared}
    for c in X.columns:
        out[f"beta_{c}"], out[f"t_{c}"] = m.params[c], m.tvalues[c]
    return out


def perf(ls: pd.Series):
    ls = ls.dropna()
    cum = (1 + ls).cumprod()
    dd = (cum / cum.cummax() - 1).min()
    return {"months": len(ls), "ann_mean_%": 100 * ls.mean() * 12, "ann_vol_%": 100 * ls.std() * np.sqrt(12),
            "sharpe": ls.mean() / ls.std() * np.sqrt(12), "skew": float(ls.skew()),
            "max_drawdown_%": 100 * dd, "positive_months_%": 100 * (ls > 0).mean()}


# ---------------------------------------------------------------- main

def main():
    rng_note = []
    # Korea
    u = ext.universe()
    cal = pd.read_parquet(RAW / "full_IDX_KS11.parquet").index
    px, ret = ext.monthly_panel(u, cal)
    quality, earn = korea_components(u, px)
    sig = signal_from(quality, earn)
    mom = px.shift(1) / px.shift(12) - 1
    rev = px / px.shift(1) - 1
    print("Korea panels built", file=sys.stderr)

    # Taiwan
    tsig, tpx, tret, _, _ = bt.taiwan()
    tmom = tpx.shift(1) / tpx.shift(12) - 1
    trev = tpx / tpx.shift(1) - 1
    tbm = tw.value_factor(tpx)
    print("Taiwan panels built", file=sys.stderr)

    fm_rows = []
    # F1 / F2 decisive
    f1 = fama_macbeth(ret, {"signal": zscores(sig), "mom_12_1": zscores(mom), "rev_1m": zscores(rev)}, *KR)
    f2 = fama_macbeth(tret, {"signal": zscores(tsig), "mom_12_1": zscores(tmom), "rev_1m": zscores(trev)}, *TW)
    fm_rows += fm_summary(f1, "F1 Korea") + fm_summary(f2, "F2 Taiwan")
    # F3 / F4 secondary
    mcap, bm = korea_caps_and_bm(u, px)
    f3 = fama_macbeth(ret, {"signal": zscores(sig), "mom_12_1": zscores(mom), "rev_1m": zscores(rev),
                            "log_size": zscores(np.log(mcap.where(mcap > 0))), "bm": zscores(bm)}, *KR_CAPS)
    f4 = fama_macbeth(tret, {"signal": zscores(tsig), "mom_12_1": zscores(tmom), "rev_1m": zscores(trev),
                             "bm": zscores(tbm)}, *TW)
    fm_rows += fm_summary(f3, "F3 Korea + size, B/M") + fm_summary(f4, "F4 Taiwan + B/M (TWSE only)")
    fm = pd.DataFrame(fm_rows)

    # A1 extended factor alpha
    ls = quintile_returns(window(sig, *KR), ret)["ls"].dropna()
    ctrl = controls_for(px, ret, None, pd.read_parquet(RAW / "full_IDX_KS11.parquet")["Close"])
    ctrl = to_month(ctrl)
    mw, ag_names = market_wide_factors()
    y = to_month(ls)
    per = pd.period_range(A1_WIN[0], A1_WIN[1], freq="M")
    y = y.reindex(per).dropna()
    X_base = ctrl.reindex(y.index)
    a1 = regress(y, X_base.join(mw.reindex(y.index)))
    a0 = regress(y, X_base)
    alpha = pd.DataFrame([{"test": "A0 index + in-universe momentum (reference)", **a0},
                          {"test": "A1 + market-wide RMW, CMA, UMD (ex chip)", **a1}])
    mw_stats = pd.DataFrame([{"factor": c, **nw_stats(mw[c].reindex(per).dropna())} for c in mw.columns])

    # U1 rule-only universe
    rule_codes = set(u.loc[u["induty_code"].astype(str).str.startswith(RULE), "stock_code"])
    dropped = sorted(set(u["stock_code"]) - rule_codes)
    rcols = [c for c in sig.columns if c in rule_codes]
    sig_rule = signal_from(quality[rcols], earn[rcols])
    u1 = nw_stats(quintile_returns(window(sig_rule, *KR), ret[rcols])["ls"])
    base = nw_stats(ls)

    # S1 skip a month
    s1_kr = nw_stats(quintile_returns(window(sig, *KR), ret.shift(-1))["ls"])
    s1_tw = nw_stats(quintile_returns(window(tsig, *TW), tret.shift(-1))["ls"])
    tls = quintile_returns(window(tsig, *TW), tret)["ls"].dropna()

    # D1 performance + calendar years
    d1 = pd.DataFrame([{"market": "Korea", **perf(ls)}, {"market": "Taiwan", **perf(tls)}])
    years = pd.DataFrame({"Korea_bp": ls.groupby(ls.index.year).mean() * 1e4,
                          "Taiwan_bp": tls.groupby(tls.index.year).mean() * 1e4,
                          "Korea_months": ls.groupby(ls.index.year).size(),
                          "Taiwan_months": tls.groupby(tls.index.year).size()})

    # D2 summary statistics
    def desc(name, frame, a, b):
        w = window(frame, a, b)
        n = w.notna().sum(axis=1)
        v = w.stack()
        return {"variable": name, "names_per_month_median": float(n.median()), "min": int(n.min()), "max": int(n.max()),
                "p10": float(v.quantile(.1)), "median": float(v.median()), "p90": float(v.quantile(.9))}
    d2 = pd.DataFrame([desc("Korea quality (TTM op. profit / assets)", quality, *KR),
                       desc("Korea earnings momentum (SUE)", earn, *KR),
                       desc("Korea next-month return", ret, *KR),
                       desc("Korea market cap (KRW bn, from 2022-07)", mcap / 1e9, *KR_CAPS),
                       desc("Taiwan revenue growth (YoY, z-score)", tsig, *TW),
                       desc("Taiwan next-month return", tret, *TW)])
    corr = pd.concat([zscores(quality).stack().rename("q"), zscores(earn).stack().rename("e")], axis=1).dropna()
    xs_corr = corr.groupby(level=0).apply(lambda g: g["q"].corr(g["e"]) if len(g) > 10 else np.nan)

    # verdicts + Holm across the four decisive tests (one-sided)
    from scipy import stats
    dec = {"F1": fm[(fm.test == "F1 Korea") & (fm.regressor == "signal")].iloc[0]["t"],
           "F2": fm[(fm.test == "F2 Taiwan") & (fm.regressor == "signal")].iloc[0]["t"],
           "A1": a1["alpha_t"], "U1": u1["t"]}
    p = {k: float(stats.norm.sf(v)) for k, v in dec.items()}
    order = sorted(p, key=p.get)
    holm, run = {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, p[k] * (len(order) - i)))
        holm[k] = run
    verdict = pd.DataFrame([{"test": k, "t": dec[k], "p_one_sided": p[k], "p_holm": holm[k],
                             "pass (t > 2)": bool(dec[k] > 2)} for k in dec])

    def md(df, fmt="{:.2f}"):
        return "```\n" + df.to_string(index=False, float_format=lambda v: fmt.format(v)) + "\n```"

    L = ["# Q29 — standard-methods robustness (referee checks)", "",
         "Follows `docs/q29_referee_robustness_preregistration.md`, committed before this script. All data here had been",
         "examined before; these are new estimators on known data, reported as run.", "",
         "## Decisive tests (one-sided, bar t > 2; Holm across the four)", "", md(verdict, "{:.3f}"), "",
         "## Fama–MacBeth (F1–F4): monthly cross-sectional OLS, Newey–West on the coefficient series", "",
         "Coefficients are bp of next-month return per one cross-sectional standard deviation of the regressor.", "",
         md(fm), "",
         "## Extended factor alpha (A1), Korea", "",
         f"Market-wide factors built from all listed Korean companies **excluding the chip universe** (median "
         f"{ag_names} companies with asset growth per month).", "", md(alpha), "",
         "Market-wide factor premia over the same window:", "", md(mw_stats), "",
         "## Rule-only universe (U1), Korea", "",
         f"Universe defined only by DART industry codes {', '.join(RULE)}: {len(rule_codes)} of {len(u)} codes. "
         f"Dropped (added by name, not by rule): {', '.join(dropped)}. Leeno (058470) qualifies by rule (code 2629) "
         "and stays.", "",
         md(pd.DataFrame([{"universe": "paper (rule + named)", **base}, {"universe": "rule only", **u1}])), "",
         "## Skip a month (S1)", "",
         md(pd.DataFrame([{"market": "Korea", **s1_kr}, {"market": "Taiwan", **s1_tw}])), "",
         "## Performance (D1)", "", md(d1), "", "Calendar years (mean monthly spread, bp):", "",
         md(years.reset_index().rename(columns={"index": "year"}), "{:.0f}"), "",
         "## Summary statistics (D2)", "", md(d2, "{:.3f}"), "",
         f"Median monthly cross-sectional correlation between the quality and SUE z-scores: {xs_corr.median():.2f}.", ""]
    (RESULTS / "q29_referee_robustness.md").write_text("\n".join(L), encoding="utf-8")
    fm.to_csv(INTERIM / "q29_fama_macbeth.csv", index=False)
    print("\n".join(L))


if __name__ == "__main__":
    main()
