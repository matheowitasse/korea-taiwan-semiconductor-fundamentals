"""Q7 T3 audit (EXPLORATORY, data check): why did SUE rank show +31% (t 5.8) in the recent period (Q7b)?

Not a test of any hypothesis; nothing here can confirm an edge. Checks:
  1. leak: reported-quarter mapping vs the kind of first disclosure and its timing; profit not yet published at D0
  2. rally vs news: does SUE rank also "predict" the return BEFORE the announcement (D0-61 -> D0-2)?
  3. outliers: quintile means vs medians, slope without the most extreme 5% of CAR60, top contributors
  4. timing: slope by event month
Same for discovery (2023-01 -> 2025-06) for comparison.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q7_pead_test as q7  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
RESULTS = ROOT / "results"
RECENT = ("2025-07-01", "2026-06-16")


def first_disclosures() -> pd.DataFrame:
    comp = q7.companies()
    disc = pd.read_csv(INTERIM / "dart_earnings_disclosures.csv", dtype=str)
    disc = disc[~disc["report_nm"].str.strip().str.startswith("[") & disc["corp_code"].isin(comp["corp_code"])].copy()
    disc["date"] = pd.to_datetime(disc["rcept_dt"], format="%Y%m%d")
    disc = disc.sort_values(["corp_code", "date"])
    rows, last = [], {}
    for r in disc.itertuples():
        if r.corp_code in last and (r.date - last[r.corp_code][0]).days <= q7.MERGE_DAYS:
            last[r.corp_code][1].append(r.kind)
            continue
        kinds = [r.kind]
        last[r.corp_code] = (r.date, kinds)
        rows.append({"corp_code": r.corp_code, "rcept_date": r.date, "first_kind": r.kind, "first_report": r.report_nm,
                     "kinds": kinds})
    out = pd.DataFrame(rows)
    out["periodic_within_30d"] = out["kinds"].apply(lambda k: any(x in ("quarterly", "half", "annual") for x in k))
    return out.drop(columns="kinds")


def pre_car(ev: pd.DataFrame) -> pd.Series:
    """Market-adjusted return D0-61 -> D0-2 (before the announcement), same price rules as Q7."""
    cal = q7.calendar()
    mkt = q7.market_series(cal)
    pos = {d: i for i, d in enumerate(cal)}
    cache, out = {}, []
    for r in ev.itertuples():
        if r.stock_code not in cache:
            p, _ = q7.load_prices(r.stock_code)
            cache[r.stock_code] = p["Close"].reindex(cal).ffill().values if p is not None else None
        c = cache[r.stock_code]
        i = pos[r.D0]
        if c is None or i < 61 or np.isnan(c[i - 61]) or np.isnan(c[i - 2]):
            out.append(np.nan)
            continue
        m = mkt[r.market]
        out.append((c[i - 2] / c[i - 61] - 1) - (m[i - 2] / m[i - 61] - 1))
    return pd.Series(out, index=ev.index)


def slope(d: pd.DataFrame, y: str, x: str = "r_sue") -> tuple[float, float, int]:
    d = d[[x, y, "month_key"]].dropna()
    if len(d) < 20 or d["month_key"].nunique() < 2:
        return np.nan, np.nan, len(d)
    fit = sm.OLS(d[y], sm.add_constant(d[x])).fit(cov_type="cluster", cov_kwds={"groups": d["month_key"]})
    return fit.params[x] * 100, fit.tvalues[x], len(d)


def audit(d: pd.DataFrame, label: str, fd: pd.DataFrame) -> list[str]:
    d = d[d["sue"].notna()].copy()
    d["r_sue"] = q7.centered_rank(d["sue"].values, d["quarter_key"].values)
    d["r_ear"] = q7.centered_rank(d["ear"].values, d["quarter_key"].values)
    d = d.merge(fd, left_on=["corp_code", "D0_rcept"], right_on=["corp_code", "rcept_date"], how="left")
    d["pre_car"] = pre_car(d)
    d["days_after_q_end"] = (d["D0"] - (d["D0"].dt.to_period("Q") - 1).dt.end_time.dt.normalize()).dt.days
    L = [f"## {label}: {len(d)} events with SUE, {d['month_key'].nunique()} months", ""]

    # 1. leak
    L += ["### 1. Leak checks", "",
          "First disclosure kind of the event (share %), and whether a periodic report arrives within the 30-day event:", "", "```",
          (d["first_kind"].value_counts(normalize=True) * 100).round(1).to_string(), "",
          f"events with a periodic report inside the event window: {d['periodic_within_30d'].mean() * 100:.1f} %",
          f"days from reported quarter end to D0: median {d['days_after_q_end'].median():.0f}, "
          f"min {d['days_after_q_end'].min():.0f}, share < 20 days {(d['days_after_q_end'] < 20).mean() * 100:.1f} %",
          "```", ""]
    s_all = slope(d, "car60")
    no_periodic = d[~d["periodic_within_30d"].astype(bool)]
    early = d[d["days_after_q_end"] >= 20]
    L += ["```",
          f"T3 slope, all events                         : {s_all[0]:7.2f} %  t {s_all[1]:5.2f}  n {s_all[2]}",
          f"only events WITH a periodic report in window : {slope(d[d['periodic_within_30d'].astype(bool)], 'car60')[0]:7.2f} %  "
          f"(without: {slope(no_periodic, 'car60')[0]:.2f} %, n {len(no_periodic)})",
          f"excluding D0 < 20 days after quarter end     : {slope(early, 'car60')[0]:7.2f} %  n {len(early)}",
          f"correlation of SUE rank with EAR rank        : {d[['r_sue', 'r_ear']].corr().iloc[0, 1]:.3f}",
          "```", ""]

    # 2. rally vs news
    sp = slope(d, "pre_car")
    L += ["### 2. Rally or news? SUE rank vs return BEFORE the announcement (D0−61 → D0−2)", "", "```",
          f"pre-announcement slope: {sp[0]:.2f} %  t {sp[1]:.2f}  n {sp[2]}   (after-announcement T3: {s_all[0]:.2f} %)",
          "```", ""]

    # 3. outliers
    d["q"] = pd.qcut(d["r_sue"], 5, labels=[1, 2, 3, 4, 5])
    qt = d.groupby("q", observed=True)["car60"].agg(["count", "mean", "median"]).mul([1, 100, 100])
    lo, hi = d["car60"].quantile([0.025, 0.975])
    trimmed = d[(d["car60"] >= lo) & (d["car60"] <= hi)]
    top = d.assign(contrib=d["r_sue"] * (d["car60"] - d["car60"].mean())).nlargest(10, "contrib")
    names = pd.read_csv(INTERIM / "dart_companies.csv", dtype=str).set_index("stock_code")["corp_name"]
    top["name"] = top["stock_code"].map(names)
    L += ["### 3. Outliers", "", "CAR60 by SUE quintile (%):", "", "```", qt.round(2).to_string(), "```", "",
          f"Slope without the most extreme 5 % of CAR60: {slope(trimmed, 'car60')[0]:.2f} % (t {slope(trimmed, 'car60')[1]:.2f})", "",
          "Ten events contributing most to the slope:", "", "```",
          top[["D0", "stock_code", "name", "sue", "r_sue", "ear", "car60", "pre_car"]].round(3).to_string(index=False),
          "```", ""]

    # 4. timing
    bym = [{"month": m, "n": len(g), "slope_%": slope(g.assign(month_key="x" + g["quarter_key"]), "car60")[0]
            if False else sm.OLS(g["car60"], sm.add_constant(g["r_sue"])).fit().params["r_sue"] * 100}
           for m, g in d.groupby("month_key") if len(g) >= 15]
    L += ["### 4. Slope by event month (months with ≥ 15 events)", "", "```", pd.DataFrame(bym).round(2).to_string(index=False), "```", ""]
    return L


def main() -> None:
    ev, _ = q7.build_events()
    ev["D0_rcept"] = pd.NaT
    fd = first_disclosures()
    # map each kept event back to its rcept_date (first disclosure date): last rcept_date <= D0 for that company
    fd_sorted = fd.sort_values("rcept_date")
    ev = ev.sort_values("D0")
    ev = pd.merge_asof(ev, fd_sorted[["corp_code", "rcept_date"]].rename(columns={"rcept_date": "D0_rcept"}),
                       left_on="D0", right_on="D0_rcept", by="corp_code", direction="backward", suffixes=("_x", ""))
    ev = ev.drop(columns=[c for c in ev.columns if c.endswith("_x")])

    L = ["# Q7 T3 audit — why SUE rank showed +31 % in the recent period (EXPLORATORY data check)", "",
         "Not a hypothesis test. Nothing here can confirm an edge.", ""]
    L += audit(q7.prepare(ev, "A", RECENT), f"Recent {RECENT[0]} → {RECENT[1]}", fd)
    L += audit(q7.prepare(ev, "A", q7.DISCOVERY), f"Discovery {q7.DISCOVERY[0]} → {q7.DISCOVERY[1]}", fd)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q7_t3_audit.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
