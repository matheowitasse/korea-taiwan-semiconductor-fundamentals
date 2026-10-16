"""Q24: the implementable short leg, with short-selling eligibility applied by regime.

Supersedes Q18 Part B, which restricted the short leg to KOSPI 200 / KOSDAQ 150 members in every non-ban month. That
was based on an incorrect reading of the rules (corrected 2026-09-21). The actual regimes are:

    2021-05-03 → 2023-11-05   partial resumption: only KOSPI 200 / KOSDAQ 150 constituents may be shorted
    2023-11-06 → 2025-03-30   full ban: nothing may be shorted
    2025-03-31 → today        full resumption: every listed stock may be shorted

Eligibility therefore binds for the first ten months of the sample and not at all after March 2025. Q18 Part A (the ban
diagnostic) is unaffected and is not re-run here.

Diagnostic on data already used; it changes no verdict of Q8/Q9.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402
from q8_multifactor import nw_stats, quintile_returns  # noqa: E402
from q13_leg_decomposition import adjust  # noqa: E402
from q18_short_ban import controls_for, shortable_map  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
START = pd.Timestamp("2023-01-01")
INDEX_ONLY_END = pd.Timestamp("2023-11-05")   # partial resumption: index constituents only
BAN = (pd.Timestamp("2023-11-06"), pd.Timestamp("2025-03-30"))
FULL_FROM = pd.Timestamp("2025-03-31")        # every listed stock eligible
MIN_SHORTABLE = 5


def regime(t: pd.Timestamp) -> str:
    if t <= INDEX_ONLY_END:
        return "index-only"
    if BAN[0] <= t <= BAN[1]:
        return "ban"
    return "all eligible"


def build() -> pd.DataFrame:
    sig, px, ret, mcap, index_close = bt.korea()
    sig = sig.loc[sig.index >= START]
    smap = shortable_map()
    snap_dates = np.sort(smap["date"].unique())
    members = {d: set(g.loc[g["shortable"], "stock_code"]) for d, g in smap.groupby("date")}
    rows = []
    for t in sig.index:
        if t not in ret.index:
            continue
        d = pd.concat([sig.loc[t].rename("sig"), ret.loc[t].rename("ret")], axis=1).dropna()
        if len(d) < 25:
            continue
        prior = snap_dates[snap_dates < np.datetime64(t)]
        mem = members.get(prior[-1], set()) if len(prior) else set()
        d["q"] = pd.qcut(d["sig"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        bottom = d[d["q"] == 1]
        reg = regime(t)
        if reg == "ban":
            elig = bottom.iloc[0:0]
        elif reg == "index-only":
            elig = bottom[[c in mem for c in bottom.index]]
        else:
            elig = bottom
        rows.append({"date": t, "regime": reg, "universe": d["ret"].mean(), "top": d.loc[d["q"] == 5, "ret"].mean(),
                     "n_bottom": len(bottom), "n_eligible": len(elig),
                     "bottom_all": bottom["ret"].mean(),
                     "bottom_eligible": elig["ret"].mean() if len(elig) >= MIN_SHORTABLE else np.nan})
    out = pd.DataFrame(rows).set_index("date")
    out["short_leg_all"] = out["universe"] - out["bottom_all"]
    out["short_leg_impl"] = out["universe"] - out["bottom_eligible"]
    out["long_leg"] = out["top"] - out["universe"]
    return out, (sig, px, ret, mcap, index_close)


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.2f}") + "\n```"


def main() -> None:
    d, (sig, px, ret, mcap, index_close) = build()
    ctrl = controls_for(px, ret, mcap, index_close)

    by_regime = []
    for reg, g in d.groupby("regime"):
        st = nw_stats(g["short_leg_impl"].dropna())
        by_regime.append({"regime": reg, "months": len(g), "months_tradable": int(g["short_leg_impl"].notna().sum()),
                          "median_eligible_names": float(g["n_eligible"].median()),
                          "median_bottom_names": float(g["n_bottom"].median()),
                          "short_leg_impl_bp": st["mean_bp"], "t": st["t"]})

    tradable = d[d["short_leg_impl"].notna()]
    rows = []
    for label, series in (("implementable short leg (eligibility by regime)", tradable["short_leg_impl"]),
                          ("full short leg, same months", tradable["short_leg_all"]),
                          ("long leg, same months", tradable["long_leg"]),
                          ("long + implementable short", tradable["long_leg"] + tradable["short_leg_impl"])):
        st = nw_stats(series)
        rows.append({"portfolio": label, "months": st["months"], "mean_bp": st["mean_bp"], "t": st["t"],
                     **adjust(series, ctrl)})
    res = pd.DataFrame(rows)
    impl = res.iloc[0]
    survives = bool(impl["t"] > 2 and impl.get("alpha_t", np.nan) > 2)

    L = ["# Q24 — The implementable short leg, with eligibility applied by regime", "",
         "**Supersedes Q18 Part B.** That test restricted the short leg to KOSPI 200 / KOSDAQ 150 members in every",
         "non-ban month, based on an incorrect reading of the rules. Korean short selling was limited to index",
         "constituents from 2021-05 to 2023-11-05, banned to 2025-03-30, and **fully reinstated for all listed stocks**",
         "on 2025-03-31. Q18 Part A (the ban diagnostic) used the correct dates and is unaffected.", "",
         "## Eligible names and the short leg, by regime", "", fmt(pd.DataFrame(by_regime)), "",
         "## Tradable months only", "", fmt(res), "",
         f"**Implementable short leg {'SURVIVES' if survives else 'does NOT survive'} the Q18 bar (mean t > 2 and alpha t > 2).**", "",
         "Eligibility is a legal question. Borrow supply and cost are not observed here and remain the open constraint.", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q24_implementable_corrected.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
