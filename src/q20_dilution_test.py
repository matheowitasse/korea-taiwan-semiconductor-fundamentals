"""Q20: do dilution filings predict returns in Korean chip stocks? — as pre-registered in
docs/q20_dilution_events_preregistration.md.

  T1 (primary) CB     -> market-adjusted close(D0+1) -> close(D0+21)
  T2           CB     -> close(D0+1) -> close(D0+61)
  T3           CB     -> close(D0+1) -> close(D0+121)
  T4           RIGHTS -> close(D0+1) -> close(D0+21)
  T5           RIGHTS -> close(D0+1) -> close(D0+61)

One-sided (H1: mean < 0), month-clustered standard errors, Holm across the family, matched-day placebo.
Prices, market adjustment and exclusions follow Q7 (`src/q7_pead_test.py`).

Usage:
  python src/q20_dilution_test.py --check   # event counts and coverage only, no test statistics
  python src/q20_dilution_test.py           # the pre-registered run (once)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q7_pead_test as q7  # noqa: E402
from q18_short_ban import shortable_map  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
RESULTS = ROOT / "results"
FILINGS = INTERIM / "dart_major_events_raw.csv"

START, END = "2022-07-01", "2026-09-21"
MERGE_DAYS = 30
MIN_EVENTS = 40
N_DRAWS = 5000
COST_BP = 30
KINDS = {"CB": "전환사채권발행결정", "RIGHTS": "유상증자결정"}
TESTS = {"T1": ("CB", 21), "T2": ("CB", 61), "T3": ("CB", 121), "T4": ("RIGHTS", 21), "T5": ("RIGHTS", 61)}


# ---------------------------------------------------------------- events

def filings(kind: str) -> pd.DataFrame:
    df = pd.read_csv(FILINGS, dtype=str)
    df = df[df["is_correction"].map({"True": True, "False": False}) == False]  # noqa: E712
    df = df[df["report_clean"].str.contains(KINDS[kind], regex=False)].copy()
    df["date"] = pd.to_datetime(df["rcept_dt"], format="%Y%m%d")
    df = df[(df["date"] >= START) & (df["date"] <= END)].sort_values(["corp_code", "date"])
    keep, last = [], {}
    for r in df.itertuples():                       # one event per company per 30 calendar days
        if r.corp_code in last and (r.date - last[r.corp_code]).days <= MERGE_DAYS:
            continue
        last[r.corp_code] = r.date
        keep.append({"corp_code": r.corp_code, "date": r.date})
    return pd.DataFrame(keep)


def build(kind: str, horizon: int) -> tuple[pd.DataFrame, dict]:
    """Market-adjusted return close(D0+1) -> close(D0+1+horizon), Q7 price rules and exclusions."""
    cal = q7.calendar()
    mkt = q7.market_series(cal)
    pos = {d: i for i, d in enumerate(cal)}
    comp = q7.companies()
    codes = comp.set_index("corp_code")["stock_code"].to_dict()
    delisted = set(comp.loc[comp["delist_date"].notna(), "stock_code"])
    snaps = pd.read_parquet(INTERIM / "krx_marketcap_quarterly.parquet")
    snaps["stock_code"] = snaps["stock_code"].astype(str).str.zfill(6)
    snap_dates = np.sort(snaps["date"].unique())
    snap_idx = snaps.set_index(["date", "stock_code"])
    shortable = {d: set(g.loc[g["shortable"], "stock_code"]) for d, g in shortable_map().groupby("date")}

    cache, out = {}, []
    counts = {"filings_events": 0, "no_price_or_not_listed": 0, "zero_volume": 0, "move_gt_31pct": 0,
              "short_history": 0, "window_incomplete": 0}
    for r in filings(kind).itertuples():
        counts["filings_events"] += 1
        code = codes.get(r.corp_code)
        if code is None:
            counts["no_price_or_not_listed"] += 1
            continue
        if code not in cache:
            p, krx_market = q7.load_prices(code)
            if p is None:
                cache[code] = None
            else:
                last_trade = p.index.max() if code in delisted else cal.max()
                close = p["Close"].reindex(cal)
                close = close.where(close.index <= last_trade).ffill().where(close.index <= last_trade)
                cache[code] = (close.values, p["Volume"].reindex(cal).fillna(0).values,
                               p["Close"].reindex(cal).notna().values, last_trade, krx_market)
        pc = cache[code]
        nxt = cal[cal >= r.date]
        if pc is None or not len(nxt):
            counts["no_price_or_not_listed"] += 1
            continue
        d0 = nxt[0]
        i = pos[d0]
        prior = snap_dates[snap_dates < np.datetime64(d0)]
        market = None
        if len(prior) and (prior[-1], code) in snap_idx.index:
            row = snap_idx.loc[(prior[-1], code)]
            row = row.iloc[0] if isinstance(row, pd.DataFrame) else row
            market = str(row["market"])
        elif pc[4]:
            market = pc[4]
        market = "KOSDAQ" if market and market.startswith("KOSDAQ") else market
        close, vol, has_px, last_trade, _ = pc
        if market not in ("KOSPI", "KOSDAQ") or i < 2 or np.isnan(close[i]):
            counts["no_price_or_not_listed"] += 1
            continue
        last_pos = pos.get(last_trade, len(cal) - 1)
        if i + 1 >= len(cal) or min(vol[i - 1], vol[i], vol[i + 1]) <= 0:
            counts["zero_volume"] += 1
            continue
        end = min(i + 1 + horizon, last_pos)
        if i + 1 + horizon > len(cal) - 1 and last_pos >= len(cal) - 1:
            counts["window_incomplete"] += 1
            continue
        if has_px[:i].sum() < q7.MIN_HISTORY:
            counts["short_history"] += 1
            continue
        seg = close[i - 3:end + 1]
        moves = seg[1:] / seg[:-1] - 1
        bad = np.where(np.abs(moves) > q7.MAX_MOVE)[0]
        if any(not (code in delisted and last_pos - (i - 2 + k) <= q7.DELIST_GRACE) for k in bad):
            counts["move_gt_31pct"] += 1
            continue
        m = mkt[market]
        members = shortable.get(prior[-1], set()) if len(prior) else set()
        out.append({"corp_code": r.corp_code, "stock_code": code, "D0": d0, "market": market,
                    "month": d0.to_period("M").strftime("%Y-%m"),
                    "ret": (close[end] / close[i + 1] - 1) - (m[end] / m[i + 1] - 1),
                    "ann_window": (close[i + 1] / close[i - 2] - 1) - (m[i + 1] / m[i - 2] - 1),
                    "shortable": code in members})
    return pd.DataFrame(out), counts


# ---------------------------------------------------------------- inference

def clustered_mean(x: pd.Series, groups: pd.Series) -> tuple[float, float, float]:
    fit = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="cluster", cov_kwds={"groups": groups.values})
    t = fit.tvalues[0]
    return float(x.mean()), float(t), float(fit.pvalues[0] / 2 if t < 0 else 1 - fit.pvalues[0] / 2)


def placebo(events: pd.DataFrame, horizon: int, pool: dict, rng) -> float:
    """Draw the same number of stock-days from the same universe, period and market mix."""
    obs = events["ret"].mean()
    n_by_market = events["market"].value_counts().to_dict()
    draws = np.empty(N_DRAWS)
    for j in range(N_DRAWS):
        vals = [rng.choice(pool[mk], n, replace=False) for mk, n in n_by_market.items() if len(pool.get(mk, []))]
        draws[j] = np.concatenate(vals).mean() if vals else np.nan
    return float((draws <= obs).mean())


def return_pool(horizon: int) -> dict:
    """All market-adjusted horizon returns in the universe and period, by market — the placebo sampling frame."""
    cal = q7.calendar()
    mkt = q7.market_series(cal)
    comp = q7.companies()
    delisted = set(comp.loc[comp["delist_date"].notna(), "stock_code"])
    snaps = pd.read_parquet(INTERIM / "krx_marketcap_quarterly.parquet")
    snaps["stock_code"] = snaps["stock_code"].astype(str).str.zfill(6)
    market_of = (snaps.sort_values("date").groupby("stock_code")["market"].last()
                 .str.replace("KOSDAQ GLOBAL", "KOSDAQ", regex=False).to_dict())
    lo, hi = pd.Timestamp(START), pd.Timestamp(END)
    pool = {"KOSPI": [], "KOSDAQ": []}
    for code in comp["stock_code"].dropna().unique():
        market = market_of.get(code)
        if market not in pool:
            continue
        p, _ = q7.load_prices(code)
        if p is None:
            continue
        last_trade = p.index.max() if code in delisted else cal.max()
        close = p["Close"].reindex(cal)
        close = close.where(close.index <= last_trade).ffill().where(close.index <= last_trade).values
        m = mkt[market]
        idx = np.where((cal >= lo) & (cal <= hi))[0]
        idx = idx[(idx + horizon) < len(cal)]
        r = (close[idx + horizon] / close[idx] - 1) - (m[idx + horizon] / m[idx] - 1)
        pool[market].append(r[~np.isnan(r)])
    return {k: np.concatenate(v) if v else np.array([]) for k, v in pool.items()}


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n```"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    built = {tid: build(*spec) for tid, spec in TESTS.items()}
    L = ["# Q20 — Do dilution filings predict returns in Korean chip stocks?", "",
         "Follows `docs/q20_dilution_events_preregistration.md` (committed before this script was written).",
         "Direction fixed in advance: **negative** (dilution, hedge selling, refixing). Returns start at the close of",
         "D0+1, so the announcement-day reaction and its documented leakage are excluded.", "", "## Events", ""]
    for tid, (kind, h) in TESTS.items():
        ev, counts = built[tid]
        L.append(f"- **{tid}** ({kind}, {h} trading days): {len(ev)} events, {ev['corp_code'].nunique()} companies, "
                 f"{ev['month'].nunique()} months, KOSDAQ {int((ev['market'] == 'KOSDAQ').sum())} / "
                 f"KOSPI {int((ev['market'] == 'KOSPI').sum())}; excluded — "
                 + ", ".join(f"{k} {v}" for k, v in counts.items() if k != "filings_events"))
    if a.check:
        print("\n".join(L))
        return

    rng = np.random.default_rng(42)
    pools = {h: return_pool(h) for h in sorted({h for _, h in TESTS.values()})}
    rows = []
    for tid, (kind, h) in TESTS.items():
        ev, _ = built[tid]
        if len(ev) < MIN_EVENTS:
            rows.append({"test": tid, "event": kind, "days": h, "n": len(ev), "note": "descriptive (< 40 events)"})
            continue
        mean, t, p = clustered_mean(ev["ret"], ev["month"])
        rows.append({"test": tid, "event": kind, "days": h, "n": len(ev), "months": ev["month"].nunique(),
                     "mean_%": mean * 100, "median_%": ev["ret"].median() * 100, "t": t, "p_one_sided": p,
                     "placebo_p": placebo(ev, h, pools[h], rng),
                     "announcement_window_%": ev["ann_window"].mean() * 100,
                     "shortable_%": 100 * ev["shortable"].mean()})
    res = pd.DataFrame(rows)
    decisive = res[res["n"] >= MIN_EVENTS].copy()
    decisive["p_holm"] = multipletests(decisive["p_one_sided"], method="holm")[1]
    decisive["pass"] = (decisive["p_holm"] < 0.05) & (decisive["placebo_p"] < 0.05)

    L += ["", "## Tests (one-sided, H1: mean < 0; Holm across the family)", "", fmt(decisive), "",
          f"**Passed: {', '.join(decisive.loc[decisive['pass'], 'test']) or 'none'}**", "",
          "`announcement_window_%` is the market-adjusted return from close(D0−2) to close(D0+1), reported only to check",
          "whether the positive announcement effect documented in the Korean literature appears in our sample.",
          f"`shortable_%` is the share of event stocks inside the KOSPI 200 / KOSDAQ 150 proxy — the fraction of any",
          f"negative result that could be traded at all. Cost reference: {COST_BP} bp round trip.", ""]

    for label, sub in [("split at 2025-07 (regime break used elsewhere)", "period"), ("by market", "market")]:
        parts = []
        for tid, (kind, h) in TESTS.items():
            ev, _ = built[tid]
            if len(ev) < MIN_EVENTS:
                continue
            if sub == "period":
                ev = ev.assign(group=np.where(ev["D0"] < "2025-07-01", "before", "after"))
            else:
                ev = ev.assign(group=ev["market"])
            for g, gg in ev.groupby("group"):
                if len(gg) >= 20:
                    m, t, _ = clustered_mean(gg["ret"], gg["month"])
                    parts.append({"test": tid, "group": g, "n": len(gg), "mean_%": m * 100, "t": t})
        L += [f"### Reported, not decisive: {label}", "", fmt(pd.DataFrame(parts)), ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q20_dilution.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
