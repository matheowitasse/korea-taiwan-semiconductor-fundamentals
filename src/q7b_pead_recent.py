"""Q7b: post-earnings drift in the recent Korean market (second look after the Q7 near-miss) + descriptive regime
comparison — as pre-registered in docs/q7b_pead_recent_market_preregistration.md.

Part 1 (decisive): Q7 T1 on D0 from 2025-07-01, one-sided (coefficient > 0).
Part 2 (descriptive): before (2023-01 → 2025-06) vs after (2025-07 → 2026-09-16), fixed measures, break date fixed.

Usage:
  python src/q7b_pead_recent.py --check   # part 2 inputs and event counts only (no part-1 statistics)
  python src/q7b_pead_recent.py           # the pre-registered run (once)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q7_pead_test as q7  # noqa: E402
from krx_manual_import import read_krx  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"
BEFORE = ("2023-01-01", "2025-06-30")
AFTER = ("2025-07-01", "2026-09-16")
MAX_MOVE = 0.31


def sel(s: pd.Series | pd.DataFrame, period):
    return s[(s.index >= period[0]) & (s.index <= period[1])]


def index_measures() -> list[dict]:
    rows = []
    for name, t in (("KOSPI", "KS11"), ("KOSDAQ", "KQ11")):
        c = pd.read_parquet(RAW / f"full_IDX_{t}.parquet")["Close"]
        r = c.pct_change()
        for label, per in (("before", BEFORE), ("after", AFTER)):
            x = sel(r, per).dropna()
            years = len(x) / 252
            rows.append({"measure": f"{name} return, annualised %", "period": label,
                         "value": ((1 + x).prod() ** (1 / years) - 1) * 100})
            rows.append({"measure": f"{name} volatility, annualised %", "period": label, "value": x.std() * np.sqrt(252) * 100})
    return rows


def stock_measures(codes: list[str]) -> pd.DataFrame:
    snaps = pd.read_parquet(ROOT / "data" / "interim" / "krx_marketcap_quarterly.parquet")
    snaps["stock_code"] = snaps["stock_code"].astype(str).str.zfill(6)
    out = []
    for code in codes:
        p, _ = q7.load_prices(code)
        if p is None:
            continue
        p = p[p["Volume"] > 0].copy()
        r = p["Close"].pct_change()
        r = r[r.abs() <= MAX_MOVE]
        caps = snaps[snaps["stock_code"] == code][["date", "market_cap"]].sort_values("date")
        caps["date"] = caps["date"].astype("datetime64[ns]")
        tv = (p["Close"] * p["Volume"]).rename("traded").reset_index().rename(columns={p.index.name or "index": "Date"})
        tv.columns = ["Date", "traded"]
        tv["Date"] = tv["Date"].astype("datetime64[ns]")
        tv = pd.merge_asof(tv.sort_values("Date"), caps.rename(columns={"date": "Date"}), on="Date",
                           allow_exact_matches=False).set_index("Date")
        turnover = tv["traded"] / tv["market_cap"]
        f = RAW / "naver_flows" / f"{code}.parquet"
        retail = None
        if f.exists():
            fl = pd.read_parquet(f)
            fl = fl[fl["volume"] > 0]
            retail = fl["individual_net_shares"].abs() / fl["volume"]
        for label, per in (("before", BEFORE), ("after", AFTER)):
            rr = sel(r, per).dropna()
            if len(rr) < 100:
                continue
            out.append({"stock_code": code, "period": label, "vol_ann_%": rr.std() * np.sqrt(252) * 100,
                        "turnover_daily_%": sel(turnover, per).median() * 100,
                        "retail_net_share_%": sel(retail, per).median() * 100 if retail is not None else np.nan})
    return pd.DataFrame(out)


def foreign_monthly() -> pd.DataFrame:
    krx = pd.concat([read_krx(p) for p in sorted((RAW / "krx_manual").glob("KOSPI_*.csv"))])
    krx = krx[~krx.index.duplicated()].sort_index()
    m = ((krx["Foreigners"] + krx["Other foreigners"]) / 1e12).resample("ME").sum()
    return m


def compare(before: pd.Series, after: pd.Series, name: str, how: str) -> dict:
    b, a = before.dropna(), after.dropna()
    if how == "welch":
        p = stats.ttest_ind(a, b, equal_var=False).pvalue
    else:
        p = stats.mannwhitneyu(a, b).pvalue
    return {"measure": name, "before": b.median() if how == "mw" else b.mean(), "after": a.median() if how == "mw" else a.mean(),
            "ratio_after/before": (a.median() / b.median()) if how == "mw" else (a.mean() / b.mean()),
            "n_before": len(b), "n_after": len(a), "test": "Mann-Whitney (medians)" if how == "mw" else "Welch (means)",
            "p_descriptive": p}


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n```"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    ev, _ = q7.build_events()
    last_complete = ev.loc[~ev["delisted_in_window"], "end60_date"].max()
    recent = (AFTER[0], str(ev.loc[ev["end60_date"] <= last_complete, "D0"].max().date()))
    dA_before = q7.prepare(ev, "A", q7.DISCOVERY)
    dA_recent = q7.prepare(ev, "A", recent)

    head = ["# Q7b — Post-earnings drift in the recent Korean market + did the market change?", "",
            "Follows `docs/q7b_pead_recent_market_preregistration.md` (committed before this script was written).",
            "**Follow-up chosen after the Q7 near-miss** → a pass is weaker evidence than a pass of the original Q7 sequence.", "",
            f"Recent period (part 1): D0 {recent[0]} → {recent[1]}, list A, {len(dA_recent)} events, "
            f"{dA_recent['month_key'].nunique()} event months.", ""]

    comp = q7.companies()
    codes = sorted(comp.loc[comp["A"], "stock_code"].dropna().unique())
    sm_ = stock_measures(codes)
    fm = foreign_monthly()

    if a.check:
        print("\n".join(head + [
            f"(check) list-A stocks with measures: before {int((sm_.period == 'before').sum())}, "
            f"after {int((sm_.period == 'after').sum())}; retail share available {int(sm_['retail_net_share_%'].notna().sum())} rows; "
            f"KOSPI foreign months: before {len(sel(fm, BEFORE))}, after {len(sel(fm, AFTER))}; "
            f"discovery events {len(dA_before)}"]))
        return

    # ---- part 1 (decisive)
    rng = np.random.default_rng(42)
    t1 = q7.run_test(dA_recent, "T1", rng, sign=+1)
    t1["pass"] = (t1["p"] < 0.05) and (t1["placebo_p"] < 0.05)
    extra = [{"what": f"T1 list {lst}", **q7.run_test(q7.prepare(ev, lst, recent), "T1", rng, sign=+1)} for lst in ("B", "C", "BC")]
    extra.append({"what": "T3 (SUE) list A", **q7.run_test(dA_recent, "T3", rng, sign=+1)})
    before_t1 = q7.run_test(dA_before, "T1", np.random.default_rng(42))
    part1 = ["## Part 1 — T1 on the recent market (decisive, one-sided: drift > 0)", "", fmt(pd.DataFrame([t1])), "",
             f"**T1 {'PASSED' if t1['pass'] else 'FAILED'}** (needs one-sided p < 0.05 and one-sided placebo p < 0.05)", "",
             "Reported, not decisive (one-sided, same period):", "", fmt(pd.DataFrame(extra)), "",
             f"T1 coefficient: discovery 2023-01 → 2025-06 = {before_t1['coef_pct']:.2f} %, recent = {t1['coef_pct']:.2f} %, "
             f"difference = {t1['coef_pct'] - before_t1['coef_pct']:.2f} pp", ""]
    part1 += q7.strategy_illustration(dA_before, dA_recent)

    # ---- part 2 (descriptive)
    p2 = [compare(sm_.loc[sm_.period == "before", c], sm_.loc[sm_.period == "after", c], f"list-A stock {c} (per-stock medians)", "mw")
          for c in ("vol_ann_%", "turnover_daily_%", "retail_net_share_%")]
    p2.append(compare(sel(fm, BEFORE), sel(fm, AFTER), "KOSPI foreign net buying per month, trn KRW", "welch"))
    p2.append(compare(dA_before["ear"].abs() * 100, dA_recent["ear"].abs() * 100, "list-A |EAR| %, per event", "mw"))
    ear_sd = {"measure": "list-A EAR cross-sectional std %", "before": dA_before["ear"].std() * 100,
              "after": dA_recent["ear"].std() * 100}
    ear_sd["ratio_after/before"] = ear_sd["after"] / ear_sd["before"]
    idx = pd.DataFrame(index_measures()).pivot(index="measure", columns="period", values="value")[["before", "after"]]
    idx["ratio_after/before"] = idx["after"] / idx["before"]
    part2 = ["## Part 2 — did the market change? (descriptive only; break date fixed at 2025-07-01)", "",
             f"Before = {BEFORE[0]} → {BEFORE[1]}, after = {AFTER[0]} → {AFTER[1]}. p-values are descriptive, not a break test.", "",
             "```", idx.round(2).to_string(), "```", "", fmt(pd.DataFrame(p2)), "", fmt(pd.DataFrame([ear_sd])), "",
             "Earlier findings (cited, not re-tested): Q2 SK Hynix overnight gap beta 0.54 → 0.77 (break 2023); "
             "Q4b 2025-07+ US sell-off nights far more volatile; Q5 KOSPI foreign net buying 2023 +11.3, 2024 +1.3, "
             "2025 −4.7, 2026 (to 09-16) −179 trn KRW.", ""]
    L = head + part1 + part2

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q7b_pead_recent.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
