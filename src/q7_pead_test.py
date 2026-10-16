"""Q7: post-earnings-announcement drift in Korean chip stocks — as pre-registered (and approved) in
docs/q7_pead_preregistration.md.

Fixed-sequence design:
  discovery  T1 alone (p < 0.10, placebo < 0.05); T2–T5 Holm family only if T1 passes (else descriptive)
  validation T1 only if it passed discovery; T2–T5 survivors only if T1 validates

Usage:
  python src/q7_pead_test.py --check   # structure only: event counts, exclusions, coverage (no test statistics)
  python src/q7_pead_test.py           # the pre-registered run (once)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import rankdata
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"

DISCOVERY = ("2023-01-01", "2025-06-30")
VALIDATION_START = "2025-07-01"
MERGE_DAYS = 30
MAX_MOVE = 0.31
DELIST_GRACE = 10
MIN_HISTORY = 60
N_DRAWS = 5000
B_EXTRA = ["005930", "058470", "095340", "240810", "036930"]  # Samsung, Leeno, ISC, Wonik IPS, Jusung Engineering


# ---------------------------------------------------------------- universe and events

def companies() -> pd.DataFrame:
    comp = pd.read_csv(INTERIM / "dart_companies.csv", dtype=str)
    kind = pd.read_csv(INTERIM / "kind_delisted.csv", dtype=str)
    real = kind[(kind["market_transfer"] == "False") & (kind["spac_or_reit"] == "False")]
    delist = real.assign(delist_date=pd.to_datetime(real["폐지일자"]))[["corp_code", "delist_date"]]
    allc = pd.concat([comp[["corp_code", "stock_code", "corp_cls", "induty_code"]],
                      real[["corp_code", "stock_code", "corp_cls", "induty_code"]]]).drop_duplicates("corp_code")
    allc = allc.merge(delist.drop_duplicates("corp_code"), on="corp_code", how="left")
    ind = allc["induty_code"].fillna("")
    allc["A"] = ind.str.match(r"^(261|29271)")
    allc["B"] = allc["A"] | allc["stock_code"].isin(B_EXTRA)
    allc["C"] = allc["A"] | ind.str.startswith("262")
    allc["BC"] = allc["B"] | allc["C"]
    return allc[allc["BC"]].reset_index(drop=True)


def raw_events(comp: pd.DataFrame) -> pd.DataFrame:
    disc = pd.read_csv(INTERIM / "dart_earnings_disclosures.csv", dtype=str)
    disc = disc[~disc["report_nm"].str.strip().str.startswith("[") & disc["corp_code"].isin(comp["corp_code"])].copy()
    disc["date"] = pd.to_datetime(disc["rcept_dt"], format="%Y%m%d")
    disc = disc.sort_values(["corp_code", "date"])
    events, last = [], {}
    for r in disc.itertuples():
        if r.corp_code in last and (r.date - last[r.corp_code]).days <= MERGE_DAYS:
            continue
        last[r.corp_code] = r.date
        events.append((r.corp_code, r.date))
    ev = pd.DataFrame(events, columns=["corp_code", "rcept_date"])
    qe = ev["rcept_date"].dt.to_period("Q") - 1
    ev["year"], ev["quarter"] = qe.dt.year, qe.dt.quarter
    return ev.merge(comp, on="corp_code", how="left")


# ---------------------------------------------------------------- prices

def calendar() -> pd.DatetimeIndex:
    return pd.read_parquet(RAW / "full_IDX_KS11.parquet").index


def load_prices(code: str) -> tuple[pd.DataFrame | None, str | None]:
    """Close + volume on the stock's own trading days, and the KRX market type if known."""
    krx = RAW / "krx_prices" / f"{code}.parquet"
    if krx.exists():
        k = pd.read_parquet(krx)
        return k.rename(columns={"Trading volume": "Volume"})[["Close", "Volume"]].astype(float), str(k["Market type"].iloc[-1])
    yh = RAW / "q7_yahoo" / f"{code}.parquet"
    if yh.exists():
        y = pd.read_parquet(yh)
        y.columns = [c if isinstance(c, str) else c[0] for c in y.columns]
        return y[["Close", "Volume"]].astype(float), None
    return None, None


def market_series(cal: pd.DatetimeIndex) -> dict[str, np.ndarray]:
    return {m: pd.read_parquet(RAW / f"full_IDX_{t}.parquet")["Close"].reindex(cal).ffill().values
            for m, t in (("KOSPI", "KS11"), ("KOSDAQ", "KQ11"))}


# ---------------------------------------------------------------- event measures

def build_events(require_days: int = 61) -> tuple[pd.DataFrame, dict]:
    """require_days = trading days after D0 that must be complete (61 = Q7 default; 21 for CAR20-only tests, Q8 S2)."""
    cal = calendar()
    last_day = cal.max()
    mkt = market_series(cal)
    comp = companies()
    ev = raw_events(comp)
    ev["D0"] = [cal[cal >= d][0] if (cal >= d).any() else pd.NaT for d in ev["rcept_date"]]
    ev = ev.dropna(subset=["D0"])

    snaps = pd.read_parquet(INTERIM / "krx_marketcap_quarterly.parquet")
    snaps["stock_code"] = snaps["stock_code"].astype(str).str.zfill(6)
    snap_dates = np.sort(snaps["date"].unique())
    snap_idx = snaps.set_index(["date", "stock_code"])

    sue = pd.read_csv(INTERIM / "dart_sue.csv", dtype={"corp_code": str})
    ev = ev.merge(sue, on=["corp_code", "year", "quarter"], how="left")

    delisted_codes = set(comp.loc[comp["delist_date"].notna(), "stock_code"])
    price_cache, flows_cache = {}, {}
    out, counts = [], {"raw": len(ev), "no_price_or_not_listed": 0, "zero_volume": 0, "move_gt_31pct": 0,
                       "short_history": 0, "window_incomplete": 0}
    pos_of = {d: i for i, d in enumerate(cal)}

    for r in ev.itertuples():
        code = r.stock_code
        if code not in price_cache:
            p, krx_market = load_prices(code)
            if p is not None:
                # delisted: the series ends at the last trade (exit there); listed: halts keep the last price to the end
                last_trade = p.index.max() if code in delisted_codes else cal.max()
                close = p["Close"].reindex(cal)
                close = close.where(close.index <= last_trade).ffill().where(close.index <= last_trade)
                vol = p["Volume"].reindex(cal).fillna(0).values
                has_px = p["Close"].reindex(cal).notna().values
                price_cache[code] = (close.values, vol, has_px, last_trade, krx_market)
            else:
                price_cache[code] = None
        pc = price_cache[code]
        i = pos_of[r.D0]

        # listed on KOSPI / KOSDAQ at D0: market from last snapshot before D0, else DART / KRX market
        prior = snap_dates[snap_dates < np.datetime64(r.D0)]
        market, mcap = None, np.nan
        if len(prior) and (prior[-1], code) in snap_idx.index:
            row = snap_idx.loc[(prior[-1], code)]
            row = row.iloc[0] if isinstance(row, pd.DataFrame) else row
            market, mcap = str(row["market"]), float(row["market_cap"])
        elif pc is not None and pc[4]:
            market = pc[4]
        else:
            market = {"Y": "KOSPI", "K": "KOSDAQ"}.get(r.corp_cls)
        market = "KOSDAQ" if market and market.startswith("KOSDAQ") else market
        delisted_before = pd.notna(r.delist_date) and r.delist_date <= r.D0
        if pc is None or market not in ("KOSPI", "KOSDAQ") or delisted_before or i < 2 or np.isnan(pc[0][i]):
            counts["no_price_or_not_listed"] += 1
            continue
        close, vol, has_px, last_trade, _ = pc
        last_pos = pos_of.get(last_trade, len(cal) - 1)

        # exclusion 1: zero volume on D0-1, D0, D0+1
        if i + 1 >= len(cal) or min(vol[i - 1], vol[i], vol[i + 1]) <= 0:
            counts["zero_volume"] += 1
            continue
        # window: complete 61 days after D0 in the data, unless the stock was delisted (exit at last trade)
        end60 = min(i + require_days, last_pos)
        if i + require_days > len(cal) - 1 and last_pos >= len(cal) - 1:
            counts["window_incomplete"] += 1
            continue
        # exclusion 3: fewer than 60 trading days with prices before D0
        if has_px[:i].sum() < MIN_HISTORY:
            counts["short_history"] += 1
            continue
        # exclusion 2: |close-to-close| > 31% from D0-2 to D0+61, unless delisted within 10 trading days after that day
        seg = close[i - 3:end60 + 1]
        moves = seg[1:] / seg[:-1] - 1
        bad = np.where(np.abs(moves) > MAX_MOVE)[0]
        delisted = pd.notna(r.delist_date)
        if any(not (delisted and last_pos - (i - 2 + k) <= DELIST_GRACE) for k in bad):
            counts["move_gt_31pct"] += 1
            continue

        m = mkt[market]
        ear = (close[i + 1] / close[i - 2] - 1) - (m[i + 1] / m[i - 2] - 1)
        end20 = min(i + 21, last_pos)
        car60 = ((close[end60] / close[i + 1] - 1) - (m[end60] / m[i + 1] - 1) if end60 > i + 1 else 0.0) \
            if require_days == 61 else np.nan  # only the full 61-day window is CAR60
        car20 = (close[end20] / close[i + 1] - 1) - (m[end20] / m[i + 1] - 1) if end20 > i + 1 else 0.0

        if code not in flows_cache:
            f = RAW / "naver_flows" / f"{code}.parquet"
            flows_cache[code] = pd.read_parquet(f) if f.exists() else None
        fl = flows_cache[code]
        indiv = np.nan
        if fl is not None:
            days = [cal[i], cal[i + 1]]
            sub = fl.reindex(days)
            if sub["individual_net_shares"].notna().all():
                indiv = float((sub["individual_net_shares"] * sub["close"]).sum())

        out.append({"corp_code": r.corp_code, "stock_code": code, "D0": r.D0, "market": market,
                    "A": r.A, "B": r.B, "C": r.C, "BC": r.BC, "delisted_in_window": bool(delisted and end60 < i + require_days),
                    "ear": ear, "car60": car60, "car20": car20, "sue": r.sue, "indiv_value": indiv, "mcap": mcap,
                    "end60_date": cal[end60]})
    return pd.DataFrame(out), counts


# ---------------------------------------------------------------- test machinery

def centered_rank(values: np.ndarray, groups: np.ndarray) -> np.ndarray:
    out = np.full(len(values), np.nan)
    for g in np.unique(groups):
        idx = np.where((groups == g) & ~np.isnan(values))[0]
        if len(idx) >= 2:
            out[idx] = (rankdata(values[idx]) - 1) / (len(idx) - 1) - 0.5
    return out


def design(d: pd.DataFrame, test: str, ear: np.ndarray, sue: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    """X (with constant), y, index of tested coefficient."""
    q = d["quarter_key"].values
    r_ear = centered_rank(ear, q)
    if test == "T1":
        X, y, k = r_ear[:, None], d["car60"].values, 1
    elif test == "T2":
        X, y, k = r_ear[:, None], d["car20"].values, 1
    elif test == "T3":
        X, y, k = centered_rank(sue, q)[:, None], d["car60"].values, 1
    elif test == "T4":
        against = ((np.sign(d["indiv_value"].fillna(0).values) * np.sign(ear)) < 0).astype(float)
        X, y, k = np.column_stack([r_ear, against, r_ear * against]), d["car60"].values, 3
    elif test == "T5":
        small = d["small"].values
        X, y, k = np.column_stack([r_ear, small, r_ear * small]), d["car60"].values, 3
    X = sm.add_constant(X, has_constant="add")
    return X, y, k


def usable(d: pd.DataFrame, test: str) -> pd.DataFrame:
    if test == "T3":
        return d[d["sue"].notna()]
    if test == "T5":
        return d[d["small"].notna()]
    return d


def run_test(events: pd.DataFrame, test: str, rng, sign: int = 0) -> dict:
    """sign = 0: two-sided; +1/-1: one-sided in that direction (validation)."""
    d = usable(events, test).reset_index(drop=True)
    X, y, k = design(d, test, d["ear"].values, d["sue"].values)
    ok = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    fit = sm.OLS(y[ok], X[ok]).fit(cov_type="cluster", cov_kwds={"groups": d["month_key"].values[ok]})
    coef, t, p = fit.params[k], fit.tvalues[k], fit.pvalues[k]

    months = d["month_key"].values
    groups = [np.where(months == m)[0] for m in np.unique(months)]
    ear0, sue0 = d["ear"].values, d["sue"].values
    draws = np.empty(N_DRAWS)
    for j in range(N_DRAWS):
        ear_s, sue_s = ear0.copy(), sue0.copy()
        for g in groups:
            perm = rng.permutation(g)
            ear_s[g], sue_s[g] = ear0[perm], sue0[perm]
        Xs, ys, _ = design(d, test, ear_s, sue_s)
        oks = ~np.isnan(Xs).any(axis=1) & ~np.isnan(ys)
        draws[j] = np.linalg.lstsq(Xs[oks], ys[oks], rcond=None)[0][k]

    if sign == 0:
        p_used, placebo = p, float((np.abs(draws) >= abs(coef)).mean())
    else:
        p_used = p / 2 if np.sign(t) == sign else 1 - p / 2
        placebo = float((draws * sign >= coef * sign).mean())
    return {"test": test, "n": int(ok.sum()), "months": len(groups), "coef_pct": coef * 100, "t": t,
            "p": p_used, "placebo_p": placebo}


def prepare(ev: pd.DataFrame, lst: str, period: tuple[str, str]) -> pd.DataFrame:
    d = ev[ev[lst] & (ev["D0"] >= period[0]) & (ev["D0"] <= period[1])].copy()
    d["quarter_key"] = d["D0"].dt.to_period("Q").astype(str).values
    d["month_key"] = d["D0"].dt.to_period("M").astype(str).values
    med = d.groupby("quarter_key")["mcap"].transform("median")
    d["small"] = np.where(d["mcap"].notna(), (d["mcap"] < med).astype(float), np.nan)
    return d.reset_index(drop=True)


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.4f}") + "\n```"


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    ev, counts = build_events()
    last_complete = ev.loc[~ev["delisted_in_window"], "end60_date"].max()
    validation = (VALIDATION_START, str(ev.loc[ev["end60_date"] <= last_complete, "D0"].max().date()))

    L = ["# Q7 — Post-earnings drift in Korean chip stocks", "",
         "Follows `docs/q7_pead_preregistration.md` (approved and committed before this script was written).", "",
         f"Discovery {DISCOVERY[0]} → {DISCOVERY[1]}; validation {validation[0]} → {validation[1]}.",
         "Coefficients in % of market-adjusted return, top-minus-bottom surprise rank (T1–T3) or the interaction (T4–T5).", "",
         "## Events", "", "Exclusion counts (all lists B ∪ C, all dates):", "", "```",
         pd.Series(counts).to_string(), "```", ""]
    for lst in ("A", "B", "C", "BC"):
        for name, per in (("discovery", DISCOVERY), ("validation", validation)):
            d = prepare(ev, lst, per)
            L.append(f"- list {lst}, {name}: {len(d)} events, {d['stock_code'].nunique()} companies, "
                     f"KOSDAQ {int((d['market'] == 'KOSDAQ').sum())} / KOSPI {int((d['market'] == 'KOSPI').sum())}, "
                     f"with SUE {int(d['sue'].notna().sum())}, with market cap {int(d['mcap'].notna().sum())}, "
                     f"with retail flows {int(d['indiv_value'].notna().sum())}, delisted in window {int(d['delisted_in_window'].sum())}")
    dA = prepare(ev, "A", DISCOVERY)
    L += ["", "List A discovery events per quarter:", "", "```", dA["quarter_key"].value_counts().sort_index().to_string(), "```", ""]

    if a.check:
        print("\n".join(L))
        return

    rng = np.random.default_rng(42)
    t1 = run_test(dA, "T1", rng)
    t1["pass"] = (t1["p"] < 0.10) and (t1["placebo_p"] < 0.05)
    rest = pd.DataFrame([run_test(dA, t, rng) for t in ("T2", "T3", "T4", "T5")])
    rest["p_holm"] = multipletests(rest["p"], method="holm")[1]
    if t1["pass"]:
        rest["pass"] = (rest["p_holm"] < 0.10) & (rest["placebo_p"] < 0.05)
    else:
        rest["pass"] = "descriptive only (T1 failed)"
    L += ["## Discovery — step 1: T1 alone (decisive)", "", fmt(pd.DataFrame([t1])), "",
          f"**T1 {'PASSED' if t1['pass'] else 'FAILED'} discovery** (needs p < 0.10 and placebo p < 0.05)", "",
          "## Discovery — step 2: T2–T5 " + ("(Holm family, decisive)" if t1["pass"] else "(descriptive only, because T1 failed)"),
          "", fmt(rest), ""]

    passed = (["T1"] if t1["pass"] else []) + (rest.loc[rest["pass"] == True, "test"].tolist() if t1["pass"] else [])  # noqa: E712
    if not t1["pass"]:
        L += ["**T1 failed → by the fixed-sequence rule nothing else can pass and validation is not run. No edge found.**", ""]
    else:
        L += ["## Consistency (lists B, C, B ∪ C; discovery; sign must match list A)", ""]
        cons = []
        for t in passed:
            for lst in ("B", "C", "BC"):
                r = run_test(prepare(ev, lst, DISCOVERY), t, rng)
                cons.append({"list": lst, **r})
        L += [fmt(pd.DataFrame(cons)), ""]

        dV = prepare(ev, "A", validation)
        s1 = int(np.sign(t1["coef_pct"]))
        v1 = run_test(dV, "T1", rng, sign=s1)
        v1["edge"] = (v1["p"] < 0.05) and (v1["placebo_p"] < 0.05)
        L += ["## Validation — T1 (one-sided in the discovery direction)", "", fmt(pd.DataFrame([v1])), "",
              f"**T1 {'VALIDATED' if v1['edge'] else 'NOT validated'}**", ""]
        others = [t for t in passed if t != "T1"]
        if v1["edge"] and others:
            disc_sign = rest.set_index("test")["coef_pct"]
            vr = pd.DataFrame([run_test(dV, t, rng, sign=int(np.sign(disc_sign[t]))) for t in others])
            vr["p_holm"] = multipletests(vr["p"], method="holm")[1]
            vr["edge"] = (vr["p_holm"] < 0.05) & (vr["placebo_p"] < 0.05)
            L += ["## Validation — T2–T5 survivors (Holm)", "", fmt(vr), ""]
        if v1["edge"]:
            L += strategy_illustration(dA, dV)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q7_pead.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def strategy_illustration(dA: pd.DataFrame, dV: pd.DataFrame) -> list[str]:
    """Not decisive: long the top EAR quintile at close(D0+1), 60 days, vs market; per event, with and without costs."""
    rows = []
    for name, d in (("discovery", dA), ("validation", dV)):
        q = d.groupby("quarter_key")["ear"].transform(
            lambda s: pd.qcut(s.rank(method="first"), 5, labels=False) if len(s) >= 5 else pd.Series(np.nan, index=s.index))
        top = d[q == 4]
        rows.append({"period": name, "positions": len(top), "mean_car60_%": top["car60"].mean() * 100,
                     "after_0.30%_cost_%": (top["car60"].mean() - 0.003) * 100,
                     "hit_rate_%": (top["car60"] > 0).mean() * 100, "worst_%": top["car60"].min() * 100,
                     "from_delisted_%": top.loc[top["delisted_in_window"], "car60"].sum() / top["car60"].sum() * 100})
    return ["## Strategy illustration (not decisive): long top EAR quintile, 60 days, vs market", "",
            fmt(pd.DataFrame(rows)), ""]


if __name__ == "__main__":
    main()
