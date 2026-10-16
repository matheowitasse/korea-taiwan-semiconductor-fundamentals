"""Q19: does the signal work only where the stock cannot be shorted? — as pre-registered in
docs/q19_limits_to_arbitrage_preregistration.md.

T1 (primary, one-sided b3 < 0): ret(t+1) = month FE + b1 rank + b2 shortable + b3 rank x shortable
T2: quintile spreads inside the shortable and unshortable groups separately
T3: among shortable names, ban months vs other months
Mechanism test of the frozen finding: it cannot change the Q8/Q9 verdicts, only the explanation.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402
from q8_multifactor import nw_stats, quintile_returns  # noqa: E402
from q18_short_ban import BAN, shortable_map  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
START = pd.Timestamp("2023-01-01")
N_DRAWS = 5000
MIN_GROUP = 25


def panel() -> pd.DataFrame:
    sig, px, ret, mcap, _ = bt.korea()
    sig = sig.loc[sig.index >= START]
    smap = shortable_map()
    snap_dates = np.sort(smap["date"].unique())
    members = {d: set(g.loc[g["shortable"], "stock_code"]) for d, g in smap.groupby("date")}
    rows = []
    for t in sig.index:
        if t not in ret.index:
            continue
        d = pd.concat([sig.loc[t].rename("sig"), ret.loc[t].rename("ret")], axis=1).dropna()
        if len(d) < 50:
            continue
        prior = snap_dates[snap_dates < np.datetime64(t)]
        mem = members.get(prior[-1], set()) if len(prior) else set()
        d["rank"] = (d["sig"].rank(method="first") - 1) / (len(d) - 1) - 0.5
        d["shortable"] = [1.0 if c in mem else 0.0 for c in d.index]
        d["logcap"] = np.log(mcap.loc[t].reindex(d.index).where(lambda s: s > 0))
        d["date"] = t
        d["ban"] = 1.0 if BAN[0] <= t <= BAN[1] else 0.0
        rows.append(d.reset_index().rename(columns={"index": "code"}))
    return pd.concat(rows, ignore_index=True)


def interaction_fit(p: pd.DataFrame, with_size: bool) -> dict:
    d = p.dropna(subset=["ret", "rank", "shortable"] + (["logcap"] if with_size else [])).copy()
    X = pd.DataFrame({"rank": d["rank"], "shortable": d["shortable"], "rank_x_shortable": d["rank"] * d["shortable"]})
    if with_size:
        z = (d["logcap"] - d.groupby("date")["logcap"].transform("mean")) / d.groupby("date")["logcap"].transform("std")
        X["logcap_z"], X["rank_x_logcap"] = z, d["rank"] * z
    X = pd.concat([X, pd.get_dummies(d["date"], prefix="m", drop_first=True, dtype=float)], axis=1)
    fit = sm.OLS(d["ret"].values, X.values).fit(cov_type="cluster", cov_kwds={"groups": d["date"].values})
    i = list(X.columns).index("rank_x_shortable")
    return {"coef_bp": fit.params[i] * 1e4, "t": fit.tvalues[i],
            "p_one_sided": float(fit.pvalues[i] / 2 if fit.tvalues[i] < 0 else 1 - fit.pvalues[i] / 2),
            "n_obs": len(d), "b_rank_bp": fit.params[0] * 1e4, "with_size_controls": with_size}


def placebo_interaction(p: pd.DataFrame, observed: float, rng) -> float:
    """Shuffle the shortable labels within each month, keeping the count per month fixed."""
    d = p.dropna(subset=["ret", "rank", "shortable"]).copy()
    groups = [g.index.values for _, g in d.groupby("date")]
    months = pd.get_dummies(d["date"], prefix="m", drop_first=True, dtype=float).values
    rank = d["rank"].values
    y = d["ret"].values
    draws = np.empty(N_DRAWS)
    base_short = d["shortable"].values
    for j in range(N_DRAWS):
        s = base_short.copy()
        for g in groups:
            s[g] = rng.permutation(base_short[g])
        X = np.column_stack([rank, s, rank * s, months])
        draws[j] = np.linalg.lstsq(X, y, rcond=None)[0][2]
    return float((draws <= observed).mean())


def group_spreads(p: pd.DataFrame, mask: pd.Series, label: str) -> dict:
    d = p[mask]
    sig = d.pivot_table(index="date", columns="code", values="sig")
    ret = d.pivot_table(index="date", columns="code", values="ret")
    keep = sig.notna().sum(axis=1) >= MIN_GROUP
    q = quintile_returns(sig[keep], ret[keep])
    st = nw_stats(q["ls"])
    return {"group": label, "months": st["months"], "median_names": float(sig[keep].notna().sum(axis=1).median()),
            "spread_bp": st["mean_bp"], "t": st["t"]}


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n```"


def main() -> None:
    p = panel()
    rng = np.random.default_rng(42)

    t1 = interaction_fit(p, with_size=False)
    t1_size = interaction_fit(p, with_size=True)
    t1["placebo_p"] = placebo_interaction(p, t1["coef_bp"] / 1e4, rng)
    t1["pass"] = bool(t1["p_one_sided"] < 0.05 and t1["placebo_p"] < 0.05)

    t2 = pd.DataFrame([group_spreads(p, p["shortable"] == 0, "unshortable (proxy)"),
                       group_spreads(p, p["shortable"] == 1, "shortable (proxy)")])

    short_only = p[p["shortable"] == 1]
    t3 = pd.DataFrame([group_spreads(short_only, short_only["ban"] == 1, "shortable, ban months"),
                       group_spreads(short_only, short_only["ban"] == 0, "shortable, other months")])

    share = p.groupby("date")["shortable"].mean()
    out = ["# Q19 — Does the effect live where it cannot be shorted?", "",
           "Follows `docs/q19_limits_to_arbitrage_preregistration.md` (committed before this script was written).",
           "Mechanism test: it cannot change the Q8/Q9 finding, only whether the limits-to-arbitrage explanation holds.", "",
           f"Korean universe, {p['date'].nunique()} months, {len(p):,} stock-months. "
           f"Proxy-shortable share of the universe: median {share.median():.1%} (min {share.min():.1%}, max {share.max():.1%}).", "",
           "## T1 (primary) — rank × shortable interaction, month fixed effects, clustered by month", "",
           fmt(pd.DataFrame([t1, t1_size])), "",
           f"**T1 {'PASSES' if t1['pass'] else 'FAILS'}** (needs one-sided p < 0.05 and placebo p < 0.05 for b3 < 0).",
           "Per the pre-registration: if the interaction loses significance once size is controlled, the size version is",
           "the main answer.", "",
           "## T2 — quintile spreads computed inside each group", "", fmt(t2), "",
           "## T3 — among proxy-shortable names: ban months vs other months", "", fmt(t3), ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q19_limits_to_arbitrage.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
