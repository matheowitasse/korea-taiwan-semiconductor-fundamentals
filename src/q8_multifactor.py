"""Q8: multi-factor cross-section in Korean chip stocks — exactly as pre-registered in
docs/q8_multifactor_preregistration.md.

Discovery (2023-01 → 2025-06) on 6 tests; validation (2025-07 → last complete month) ONLY for discovery survivors.
Robustness (not decisive): list A, long-only, value-weighted, split at the 2024-02 fundamentals break.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
RAW, INTERIM, RESULTS = ROOT / "data" / "raw", ROOT / "data" / "interim", ROOT / "results"

DISCOVERY = ("2023-01-31", "2025-06-30")
VALIDATION = ("2025-07-01", "2026-12-31")
BREAK = "2024-02-01"          # fundamentals break from results/q8_regime_break.md (robustness split)
EXTRA_B = ["005930", "058470", "095340", "240810", "036930"]
N_PERM, NW_LAGS, JUMP = 5000, 3, 0.31
FACTORS = ["composite", "value", "quality", "earn_mom", "price_mom", "size"]


# ---------------------------------------------------------------- data

def universe() -> pd.DataFrame:
    comp = pd.read_csv(INTERIM / "dart_companies.csv", dtype=str)
    codes = pd.read_csv(INTERIM / "q7_universe_codes.csv", dtype=str)["stock_code"]
    u = comp[comp["stock_code"].isin(codes)].drop_duplicates("stock_code").copy()
    ind = u["induty_code"].fillna("")
    u["in_A"] = ind.str.startswith("261") | ind.str.startswith("29271")
    u["in_BC"] = u["in_A"] | ind.str.startswith("262") | u["stock_code"].isin(EXTRA_B)
    return u[u["in_BC"]].reset_index(drop=True)


def price_frame(code: str) -> pd.DataFrame | None:
    y, k = RAW / "q7_yahoo" / f"{code}.parquet", RAW / "krx_prices" / f"{code}.parquet"
    if y.exists():
        df = pd.read_parquet(y).rename(columns={"Close": "close", "Volume": "volume"})
    elif k.exists():
        df = pd.read_parquet(k).rename(columns={"Close": "close", "Trading volume": "volume"})
    else:
        return None
    df = df[["close", "volume"]].sort_index()
    return df[df["close"] > 0]


def monthly_panel(u: pd.DataFrame, cal: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Month-end prices (halts carried forward, delisting = last traded price) and next-month returns."""
    month_ends = pd.Series(cal, index=cal).groupby([cal.year, cal.month]).max().values
    month_ends = pd.DatetimeIndex(month_ends)
    px, ret = {}, {}
    for code in u["stock_code"]:
        df = price_frame(code)
        if df is None or len(df) < 30:
            continue
        s = df["close"].reindex(cal).ffill()
        s[cal > df.index.max()] = np.nan          # after delisting / last data: out of the universe
        s[cal < df.index.min()] = np.nan
        me = s.reindex(month_ends)
        # a month whose end falls after the last trading day keeps the last traded price as the exit
        last = df.index.max()
        if month_ends[0] <= last <= month_ends[-1]:
            pos = month_ends.searchsorted(last)
            if pos < len(month_ends) and pd.isna(me.iloc[pos]):
                me.iloc[pos] = df["close"].iloc[-1]
        r = me.shift(-1) / me - 1
        # drop months containing an unexplained > 31% move (unless delisted within 10 trading days after it)
        chg = df["close"].pct_change().abs()
        for d in chg.index[chg > JUMP]:
            if (df.index > d).sum() > 10:          # not liquidation trading
                i = month_ends.searchsorted(d)
                if i > 0:
                    r.iloc[i - 1] = np.nan
        px[code], ret[code] = me, r
    return pd.DataFrame(px), pd.DataFrame(ret)


def availability() -> pd.DataFrame:
    """When each company's quarterly figures became public (first earnings disclosure, else statutory deadline)."""
    d = pd.read_csv(INTERIM / "dart_earnings_disclosures.csv", dtype=str)
    d = d[~d["report_nm"].str.strip().str.startswith("[")].copy()
    d["date"] = pd.to_datetime(d["rcept_dt"], format="%Y%m%d")
    q = d["date"].dt.to_period("Q") - 1
    d["year"], d["quarter"] = q.dt.year, q.dt.quarter
    first = d.groupby(["corp_code", "year", "quarter"])["date"].min().reset_index(name="avail")
    return first


def fundamentals() -> pd.DataFrame:
    fin = pd.read_csv(INTERIM / "dart_financials.csv", dtype={"corp_code": str})
    fin["pref"] = (fin["fs_div"] == "CFS").astype(int)
    fin = fin.sort_values("pref", ascending=False).drop_duplicates(["corp_code", "year", "quarter", "account"])
    wide = fin.pivot_table(index=["corp_code", "year", "quarter"], columns="account", values="amount", aggfunc="first")
    wide = wide.rename(columns={"자본총계": "equity", "자산총계": "assets"}).reset_index()

    op = pd.read_csv(INTERIM / "dart_operating_profit.csv", dtype={"corp_code": str})
    op["t"] = op["year"] * 4 + op["quarter"]
    op = op.sort_values(["corp_code", "t"])
    op["op_ttm"] = op.groupby("corp_code")["op_profit"].transform(lambda s: s.rolling(4, min_periods=4).sum())

    sue = pd.read_csv(INTERIM / "dart_sue.csv", dtype={"corp_code": str})
    f = wide.merge(op[["corp_code", "year", "quarter", "op_ttm"]], on=["corp_code", "year", "quarter"], how="outer")
    f = f.merge(sue, on=["corp_code", "year", "quarter"], how="left")
    avail = availability()
    f = f.merge(avail, on=["corp_code", "year", "quarter"], how="left")
    qend = pd.PeriodIndex.from_fields(year=f["year"], quarter=f["quarter"], freq="Q").to_timestamp(how="end").normalize()
    deadline = qend + pd.to_timedelta(np.where(f["quarter"] == 4, 90, 45), unit="D")
    f["avail"] = f["avail"].fillna(pd.Series(deadline, index=f.index))
    return f.dropna(subset=["avail"]).sort_values("avail")


def latest_known(f: pd.DataFrame, corp: str, when: pd.Timestamp) -> pd.Series | None:
    g = f[(f["corp_code"] == corp) & (f["avail"] <= when)]
    return g.iloc[-1] if len(g) else None


# ---------------------------------------------------------------- factors

def build_factors(u: pd.DataFrame, px: pd.DataFrame, month_ends: pd.DatetimeIndex) -> dict[str, pd.DataFrame]:
    f = fundamentals()
    by_corp = {c: g for c, g in f.groupby("corp_code")}
    snaps = pd.read_parquet(INTERIM / "krx_marketcap_quarterly.parquet")
    snaps["shares"] = pd.to_numeric(snaps["shares"], errors="coerce")
    shares_by_code = {c: g.set_index("date")["shares"].sort_index() for c, g in snaps.groupby("stock_code")}
    code2corp = dict(zip(u["stock_code"], u["corp_code"]))

    out = {k: pd.DataFrame(index=month_ends, columns=px.columns, dtype=float) for k in FACTORS[1:]}
    mcap = pd.DataFrame(index=month_ends, columns=px.columns, dtype=float)
    for code in px.columns:
        sh = shares_by_code.get(code)
        g = by_corp.get(code2corp.get(code, ""), None)
        for t in month_ends:
            price = px.at[t, code]
            if not np.isfinite(price):
                continue
            if sh is not None:
                past = sh[sh.index <= t]
                if len(past) and np.isfinite(past.iloc[-1]):
                    mcap.at[t, code] = past.iloc[-1] * price
            if g is not None:
                known = g[g["avail"] <= t]
                if len(known):
                    r = known.iloc[-1]
                    m = mcap.at[t, code]
                    if np.isfinite(m) and m > 0 and np.isfinite(r.get("equity", np.nan)):
                        out["value"].at[t, code] = r["equity"] / m
                    if np.isfinite(r.get("assets", np.nan)) and r["assets"] > 0 and np.isfinite(r.get("op_ttm", np.nan)):
                        out["quality"].at[t, code] = r["op_ttm"] / r["assets"]
                    if np.isfinite(r.get("sue", np.nan)):
                        out["earn_mom"].at[t, code] = r["sue"]
    out["price_mom"] = px.shift(1) / px.shift(12) - 1
    out["size"] = -np.log(mcap.where(mcap > 0))
    return out, mcap


def zscores(df: pd.DataFrame) -> pd.DataFrame:
    z = df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0, np.nan), axis=0)
    return z.clip(-3, 3)


def composite(factors: dict[str, pd.DataFrame]) -> pd.DataFrame:
    zs = [zscores(factors[k]) for k in FACTORS[1:]]
    stack = pd.concat(zs, axis=0, keys=FACTORS[1:])
    mean = stack.groupby(level=1).mean()
    count = stack.groupby(level=1).count()
    return mean.where(count >= 3)


# ---------------------------------------------------------------- portfolios and statistics

def quintile_returns(sig: pd.DataFrame, ret: pd.DataFrame, weights: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    for t in sig.index:
        s, r = sig.loc[t], ret.loc[t] if t in ret.index else None
        if r is None:
            continue
        d = pd.concat([s.rename("sig"), r.rename("ret")], axis=1).dropna()
        if len(d) < 25:
            continue
        if weights is not None:
            d["w"] = weights.loc[t].reindex(d.index)
        d["q"] = pd.qcut(d["sig"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        if weights is None:
            m = d.groupby("q", observed=True)["ret"].mean()
        else:
            m = d.groupby("q", observed=True).apply(lambda x: np.average(x["ret"], weights=x["w"].fillna(x["w"].median())))
        rows.append({"date": t, "n": len(d), "top": m.get(5, np.nan), "bottom": m.get(1, np.nan),
                     "ls": m.get(5, np.nan) - m.get(1, np.nan), "universe": d["ret"].mean()})
    out = pd.DataFrame(rows).set_index("date")
    out["long_only"] = out["top"] - out["universe"]
    return out


def nw_stats(x: pd.Series) -> dict:
    x = x.dropna()
    if len(x) < 6:
        return {"months": len(x), "mean_bp": np.nan, "t": np.nan, "p": np.nan}
    m = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": NW_LAGS})
    return {"months": len(x), "mean_bp": float(x.mean() * 1e4), "t": float(m.tvalues[0]), "p": float(m.pvalues[0])}


def placebo_p(sig: pd.DataFrame, ret: pd.DataFrame, observed: float, rng: np.random.Generator, one_sided: int = 0) -> float:
    vals = []
    for _ in range(N_PERM // 10):  # 500 shuffles of the whole panel (each month independently)
        shuffled = sig.apply(lambda row: pd.Series(rng.permutation(row.values), index=row.index), axis=1)
        m = quintile_returns(shuffled, ret)["ls"].mean()
        vals.append(m)
    v = np.array(vals)
    return float((v >= observed).mean()) if one_sided > 0 else (
        float((v <= observed).mean()) if one_sided < 0 else float((np.abs(v) >= abs(observed)).mean()))


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.3f}") + "\n```"


def main() -> None:
    rng = np.random.default_rng(88)
    u = universe()
    cal = pd.read_parquet(RAW / "full_IDX_KS11.parquet").index
    px, ret = monthly_panel(u, cal)
    month_ends = px.index
    factors, mcap = build_factors(u, px, month_ends)
    factors = {"composite": composite(factors), **factors}

    L = ["# Q8 — multi-factor cross-section in Korean chip stocks", "",
         "Follows `docs/q8_multifactor_preregistration.md` (committed before this script was written).", "",
         f"Universe B ∪ C: {len(u)} companies (list A: {int(u['in_A'].sum())}). "
         f"Month-ends with prices: {len(month_ends)} ({month_ends.min():%Y-%m} → {month_ends.max():%Y-%m}).",
         "Statistic: mean monthly long-short (top − bottom quintile) return in basis points, Newey–West t (3 lags).", ""]

    def run(period, ids, one_sided=None):
        rows = []
        for k in ids:
            sig = factors[k].loc[(factors[k].index >= period[0]) & (factors[k].index <= period[1])]
            r = ret.reindex(sig.index)
            port = quintile_returns(sig, r)
            st = nw_stats(port["ls"])
            lo = nw_stats(port["long_only"])
            direction = 0 if one_sided is None else one_sided[k]
            if direction and np.isfinite(st["t"]):
                st["p"] = st["p"] / 2 if np.sign(st["t"]) == direction else 1 - st["p"] / 2
            st["placebo_p"] = placebo_p(sig, r, port["ls"].mean(), rng, direction) if np.isfinite(st["mean_bp"]) else np.nan
            rows.append({"factor": k, **st, "long_only_bp": lo["mean_bp"], "long_only_t": lo["t"],
                         "avg_stocks": port["n"].mean()})
        df = pd.DataFrame(rows)
        ok = df["p"].notna()
        df.loc[ok, "p_holm"] = multipletests(df.loc[ok, "p"], method="holm")[1]
        return df

    disc = run(DISCOVERY, FACTORS)
    disc["pass"] = (disc["p_holm"] < 0.10) & (disc["placebo_p"] < 0.05)
    L += ["## Discovery 2023-01 → 2025-06 (decisive)", "", fmt(disc), ""]

    survivors = disc.loc[disc["pass"], "factor"].tolist()
    if not survivors:
        L += ["**No factor passed discovery → validation not run (as pre-registered). No edge found.**", ""]
    else:
        dirs = {k: int(np.sign(disc.set_index("factor").loc[k, "t"])) for k in survivors}
        val = run(VALIDATION, survivors, dirs)
        val["edge"] = (val["p_holm"] < 0.05) & (val["placebo_p"] < 0.05)
        L += [f"Survivors: {', '.join(survivors)}", "", "## Validation 2025-07 → today (survivors only)", "",
              fmt(val), "", f"**Edges confirmed: {', '.join(val.loc[val['edge'], 'factor']) or 'none'}**", ""]

    # Robustness (not decisive)
    L += ["## Robustness (not decisive)", ""]
    a_codes = set(u.loc[u["in_A"], "stock_code"])
    sub = {k: v[[c for c in v.columns if c in a_codes]] for k, v in factors.items()}
    rows = []
    for k in FACTORS:
        s = sub[k].loc[(sub[k].index >= DISCOVERY[0]) & (sub[k].index <= DISCOVERY[1])]
        p = quintile_returns(s, ret.reindex(s.index))
        rows.append({"factor": k, "list": "A", **nw_stats(p["ls"])})
    for k in FACTORS:
        s = factors[k].loc[(factors[k].index >= DISCOVERY[0]) & (factors[k].index <= DISCOVERY[1])]
        p = quintile_returns(s, ret.reindex(s.index), weights=mcap.reindex(s.index))
        rows.append({"factor": k, "list": "B∪C value-weighted", **nw_stats(p["ls"])})
    for label, period in [("2023-01→2024-01", ("2023-01-31", BREAK)), ("2024-02→2025-06", (BREAK, DISCOVERY[1]))]:
        for k in FACTORS:
            s = factors[k].loc[(factors[k].index >= period[0]) & (factors[k].index <= period[1])]
            p = quintile_returns(s, ret.reindex(s.index))
            rows.append({"factor": k, "list": label, **nw_stats(p["ls"])})
    L += [fmt(pd.DataFrame(rows)), ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q8_multifactor.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
