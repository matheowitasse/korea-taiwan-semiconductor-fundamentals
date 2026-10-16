"""Q18: the Korean short-selling ban (mechanism) and a short leg restricted to shortable names (implementation) —
as pre-registered in docs/q18_short_ban_and_implementable_preregistration.md.

Part A: leg returns split into pre-ban / ban / post-ban, Korea vs Taiwan (control, no ban).
Part B: short leg using only KOSPI 200 / KOSDAQ 150 proxy members, in months when shorting was allowed.

Diagnostic / implementation work on the frozen finding: it re-uses Q13's construction and changes no verdict.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402
from q8_multifactor import nw_stats, quintile_returns  # noqa: E402
from q13_leg_decomposition import adjust, legs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SNAPS = ROOT / "data" / "interim" / "krx_marketcap_quarterly.parquet"

BAN = (pd.Timestamp("2023-11-06"), pd.Timestamp("2025-03-30"))
PERIODS = {"pre-ban": ("2023-01-01", "2023-11-05"), "ban": ("2023-11-06", "2025-03-30"),
           "post-ban": ("2025-03-31", "2026-12-31")}
TOP = {"KOSPI": 200, "KOSDAQ": 150}
MIN_SHORTABLE = 5
BORROW_FEE_ANNUAL = 0.01


def period_of(ts: pd.Timestamp) -> str:
    for name, (a, b) in PERIODS.items():
        if pd.Timestamp(a) <= ts <= pd.Timestamp(b):
            return name
    return "outside"


def controls_for(px, ret, mcap, index_close) -> pd.DataFrame:
    idx = index_close.resample("ME").last()
    idx = (idx.shift(-1) / idx - 1)
    idx.index = [min([d for d in px.index if d.to_period("M") == p.to_period("M")], default=pd.NaT) for p in idx.index]
    idx = idx[idx.index.notna()]
    c = pd.DataFrame({"index": idx, "momentum": quintile_returns(px.shift(1) / px.shift(12) - 1, ret)["ls"]})
    if mcap is not None:
        c["size"] = quintile_returns(-np.log(mcap.where(mcap > 0)), ret)["ls"]
    return c


def shortable_map() -> pd.DataFrame:
    """Per snapshot date: stock_code -> shortable (top 200 KOSPI / top 150 KOSDAQ by market cap within its market)."""
    s = pd.read_parquet(SNAPS).copy()
    s["stock_code"] = s["stock_code"].astype(str).str.zfill(6)
    s["market"] = s["market"].str.replace("KOSDAQ GLOBAL", "KOSDAQ", regex=False)
    s = s[s["market"].isin(TOP)]
    s["rank"] = s.groupby(["date", "market"])["market_cap"].rank(ascending=False, method="first")
    s["shortable"] = s.apply(lambda r: r["rank"] <= TOP[r["market"]], axis=1)
    return s[["date", "stock_code", "market", "shortable"]]


def implementable_short(sig: pd.DataFrame, ret: pd.DataFrame, smap: pd.DataFrame) -> pd.DataFrame:
    snap_dates = np.sort(smap["date"].unique())
    lookup = {d: set(g.loc[g["shortable"], "stock_code"]) for d, g in smap.groupby("date")}
    rows = []
    for t in sig.index:
        if t not in ret.index:
            continue
        d = pd.concat([sig.loc[t].rename("sig"), ret.loc[t].rename("ret")], axis=1).dropna()
        if len(d) < 25:
            continue
        prior = snap_dates[snap_dates < np.datetime64(t)]
        members = lookup.get(prior[-1], set()) if len(prior) else set()
        d["q"] = pd.qcut(d["sig"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        bottom = d[d["q"] == 1]
        short_ok = bottom[[c in members for c in bottom.index]]
        allowed = not (BAN[0] <= t <= BAN[1])
        rows.append({"date": t, "allowed": allowed, "n_bottom": len(bottom), "n_shortable": len(short_ok),
                     "universe": d["ret"].mean(), "bottom_all": bottom["ret"].mean(),
                     "bottom_shortable": short_ok["ret"].mean() if len(short_ok) >= MIN_SHORTABLE else np.nan,
                     "top": d.loc[d["q"] == 5, "ret"].mean()})
    out = pd.DataFrame(rows).set_index("date")
    out["short_leg_all"] = out["universe"] - out["bottom_all"]
    out["short_leg_impl"] = out["universe"] - out["bottom_shortable"]
    out["long_leg"] = out["top"] - out["universe"]
    return out


def fmt(df: pd.DataFrame, dec: int = 2) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.{dec}f}") + "\n```"


def main() -> None:
    L_out, cmp_rows = [], []
    korea_data = None
    for name, fn in [("Korea", bt.korea), ("Taiwan", bt.taiwan)]:
        sig, px, ret, mcap, index_close = fn()
        if name == "Korea":
            korea_data = (sig, px, ret, mcap, index_close)
        L = legs(sig, ret)
        ctrl = controls_for(px, ret, mcap, index_close)
        for leg in ["long_leg", "short_leg", "long_short"]:
            for p in PERIODS:
                x = L[leg][[period_of(t) == p for t in L.index]]
                if len(x) < 5:
                    continue
                st = nw_stats(x)
                L_out.append({"market": name, "leg": leg, "period": p, "months": st["months"],
                              "mean_bp": st["mean_bp"], "t": st["t"], **adjust(x, ctrl)})
        ban_mask = np.array([BAN[0] <= t <= BAN[1] for t in L.index])
        for leg in ["short_leg", "long_leg"]:
            a, b = L[leg][ban_mask], L[leg][~ban_mask]
            w = stats.ttest_ind(a, b, equal_var=False)
            cmp_rows.append({"market": name, "leg": leg, "ban_mean_bp": 1e4 * a.mean(), "other_mean_bp": 1e4 * b.mean(),
                             "difference_bp": 1e4 * (a.mean() - b.mean()), "welch_t": w.statistic, "p_two_sided": w.pvalue,
                             "n_ban": len(a), "n_other": len(b)})

    part_a = pd.DataFrame(L_out)
    cmp_df = pd.DataFrame(cmp_rows)

    # ---- Part B (Korea only)
    sig, px, ret, mcap, index_close = korea_data
    imp = implementable_short(sig.loc[sig.index >= "2023-01-01"], ret, shortable_map())
    ctrl = controls_for(px, ret, mcap, index_close)
    allowed = imp[imp["allowed"]]
    rows = []
    for label, series in [("short leg, all names (all months)", imp["short_leg_all"]),
                          ("short leg, all names (allowed months)", allowed["short_leg_all"]),
                          ("short leg, SHORTABLE only (allowed months)", allowed["short_leg_impl"].dropna()),
                          ("long leg (allowed months)", allowed["long_leg"]),
                          ("long + implementable short (allowed months)",
                           (allowed["long_leg"] + allowed["short_leg_impl"]).dropna())]:
        st = nw_stats(series)
        rows.append({"portfolio": label, "months": st["months"], "mean_bp": st["mean_bp"], "t": st["t"], **adjust(series, ctrl)})
    part_b = pd.DataFrame(rows)
    survives = bool(part_b.loc[2, "alpha_t"] > 2 and part_b.loc[2, "mean_bp"] > 0)
    borrow_bp = BORROW_FEE_ANNUAL / 12 * 1e4

    out = ["# Q18 — The Korean short-selling ban, and a short leg you could actually trade", "",
           "Follows `docs/q18_short_ban_and_implementable_preregistration.md` (committed before this script was written).",
           "Implementation / mechanism work on the frozen finding: it changes no verdict of Q8/Q9.", "",
           f"Ban: {BAN[0].date()} → {BAN[1].date()}. Taiwan had no ban (control).", "",
           "## Part A — leg returns by sub-period", "", fmt(part_a), "",
           "### Ban months vs all other months (Welch, two-sided)", "", fmt(cmp_df), "",
           "## Part B — Korea: short leg restricted to shortable names (KOSPI 200 / KOSDAQ 150 proxy)", "",
           f"Bottom-quintile names shortable per month: median {imp['n_shortable'].median():.0f} of "
           f"{imp['n_bottom'].median():.0f} ({100 * (imp['n_shortable'] / imp['n_bottom']).median():.0f} %); "
           f"months skipped for fewer than {MIN_SHORTABLE} shortable names: {int(allowed['short_leg_impl'].isna().sum())}.", "",
           fmt(part_b), "",
           f"**Implementable short leg {'SURVIVES' if survives else 'does NOT survive'} the pre-registered bar "
           f"(alpha t > 2, same sign).**", "",
           f"Borrow cost reference: {BORROW_FEE_ANNUAL:.0%} a year ≈ {borrow_bp:.0f} bp a month on the short leg.", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q18_short_ban.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
