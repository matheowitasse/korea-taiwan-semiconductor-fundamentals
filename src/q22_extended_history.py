"""Q22: does the effect exist before the AI era? Korea, extended history — as pre-registered in
docs/q22_extended_history_preregistration.md.

E1 (decisive) spread over the pre-2023 window · E2 alpha after controls · E3 full history.
One-sided (positive), Newey-West (3 lags), within-month shuffle placebo.

Signal: equal-weight z-mean of quality (trailing-4q operating profit / total assets) and earnings momentum (SUE),
as used in the backtests. Point-in-time: statutory deadlines (45 days after a quarter, 90 after a year end), because
the filing-date calendar only covers 2022-07 onward.

Usage: python src/q22_extended_history.py [--check]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q8_multifactor import nw_stats, quintile_returns, zscores  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"

PRE = ("2015-01-01", "2022-12-31")      # decisive window (actual start is set by data availability, reported)
FULL_END = "2026-08-31"
N_DRAWS = 5000
MIN_NAMES = 25
MAX_MOVE = 0.31


def universe() -> pd.DataFrame:
    comp = pd.read_csv(INTERIM / "dart_companies.csv", dtype=str).drop_duplicates("stock_code")
    kind = pd.read_csv(INTERIM / "kind_delisted.csv", dtype=str).drop_duplicates("stock_code")
    codes = pd.read_csv(INTERIM / "q22_universe_codes.csv", dtype=str)["stock_code"]
    allc = pd.concat([comp[["corp_code", "stock_code", "corp_cls", "induty_code"]],
                      kind[["corp_code", "stock_code", "corp_cls", "induty_code"]]]).drop_duplicates("stock_code")
    return allc[allc["stock_code"].isin(codes)].reset_index(drop=True)


def price_series(code: str) -> pd.Series | None:
    """Daily close: Yahoo for listed names, KRX or Naver for delisted ones."""
    y = RAW / "q7_yahoo" / f"{code}.parquet"
    if y.exists():
        d = pd.read_parquet(y)
        d.columns = [c if isinstance(c, str) else c[0] for c in d.columns]
        return d["Close"].astype(float)
    k = RAW / "krx_prices" / f"{code}.parquet"
    if k.exists():
        return pd.read_parquet(k)["Close"].astype(float)
    n = RAW / "naver_flows" / f"{code}.parquet"
    if n.exists():
        s = pd.read_parquet(n)["close"].astype(float)
        return s[s > 0]
    return None


def monthly_panel(u: pd.DataFrame, cal: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    month_ends = pd.DatetimeIndex(pd.Series(cal, index=cal).groupby([cal.year, cal.month]).max().values)
    px, ret = {}, {}
    for code in u["stock_code"]:
        s = price_series(code)
        if s is None or len(s) < 60:
            continue
        s = s.reindex(cal).ffill()
        s[cal > s.dropna().index.max()] = np.nan
        me = s.reindex(month_ends)
        r = me.shift(-1) / me - 1
        r[r.abs() > 3.0] = np.nan                      # impossible monthly move: unadjusted corporate action
        px[code], ret[code] = me, r
    return pd.DataFrame(px), pd.DataFrame(ret)


def quarterly_fundamentals() -> pd.DataFrame:
    """Per company-quarter: total assets, trailing-4q operating profit, SUE, and the statutory availability date."""
    fin = pd.read_csv(INTERIM / "dart_financials.csv", dtype={"corp_code": str})
    fin["pref"] = (fin["fs_div"] == "CFS").astype(int)
    fin = fin.sort_values("pref", ascending=False).drop_duplicates(["corp_code", "year", "quarter", "account"])
    amt = fin.pivot_table(index=["corp_code", "year", "quarter"], columns="account", values="amount", aggfunc="first")
    cum = fin.pivot_table(index=["corp_code", "year", "quarter"], columns="account", values="cum", aggfunc="first")
    d = pd.DataFrame({"assets": amt.get("자산총계"), "op": amt.get("영업이익"),
                      "op_cum": cum.get("영업이익")}).reset_index()
    d["t"] = d["year"] * 4 + d["quarter"]
    out = []
    for corp, g in d.groupby("corp_code"):
        g = g.sort_values("t").set_index("t")
        g = g.reindex(range(int(g.index.min()), int(g.index.max()) + 1))
        # Q4 is reported as a full year: subtract the nine-month cumulative of the same year where available
        q4 = g.index % 4 == 0
        prev_cum = g["op_cum"].shift(1)
        op_q = g["op"].where(~q4, g["op"] - prev_cum.where(prev_cum.notna(), 0))
        ttm = op_q.rolling(4, min_periods=4).sum()
        yoy = op_q - op_q.shift(4)
        sue = yoy / yoy.shift(1).rolling(8, min_periods=6).std().replace(0, np.nan)
        for t in g.index:
            year, quarter = (t - 1) // 4, (t - 1) % 4 + 1
            q_end = pd.Timestamp(year=int(year), month=quarter * 3, day=1) + pd.offsets.MonthEnd(0)
            out.append({"corp_code": corp, "avail": q_end + pd.Timedelta(days=90 if quarter == 4 else 45),
                        "assets": g.at[t, "assets"], "op_ttm": ttm.get(t, np.nan), "sue": sue.get(t, np.nan)})
    return pd.DataFrame(out).dropna(subset=["avail"]).sort_values("avail")


def signal_panel(u: pd.DataFrame, px: pd.DataFrame) -> pd.DataFrame:
    f = quarterly_fundamentals()
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
    stack = pd.concat([zscores(quality), zscores(earn)], axis=0, keys=[0, 1])
    return stack.groupby(level=1).mean().where(stack.groupby(level=1).count() >= 1)


def placebo_p(sig: pd.DataFrame, ret: pd.DataFrame, observed: float, rng) -> float:
    draws = np.empty(N_DRAWS)
    vals = sig.values
    for j in range(N_DRAWS):
        shuffled = np.array([rng.permutation(row) for row in vals])
        s = pd.DataFrame(shuffled, index=sig.index, columns=sig.columns)
        draws[j] = quintile_returns(s, ret)["ls"].mean()
    return float((draws >= observed).mean())


def window(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    return df[(df.index >= a) & (df.index <= b)]


def fmt(df: pd.DataFrame) -> str:
    return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.2f}") + "\n```"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    u = universe()
    cal = pd.read_parquet(RAW / "full_IDX_KS11.parquet").index
    px, ret = monthly_panel(u, cal)
    sig = signal_panel(u, px)
    names = sig.notna().sum(axis=1)
    first_ok = names[names >= MIN_NAMES].index.min()
    print(f"universe {len(u)} codes, price series {px.shape[1]}, first month with >= {MIN_NAMES} signals: "
          f"{first_ok.date()}", file=sys.stderr)
    if a.check:
        cov = pd.DataFrame({"names_with_signal": names}).loc["2015":"2023"].resample("YE").median()
        print(cov.to_string())
        return

    rng = np.random.default_rng(42)
    rows = []
    for label, (start, end) in (("E1 pre-AI (decisive)", (max(PRE[0], str(first_ok.date())), PRE[1])),
                                ("E3 full history", (max(PRE[0], str(first_ok.date())), FULL_END))):
        s, r = window(sig, start, end), window(ret, start, end)
        q = quintile_returns(s, r)
        st = nw_stats(q["ls"])
        p_one = st["p"] / 2 if st["t"] > 0 else 1 - st["p"] / 2
        rows.append({"test": label, "start": start[:7], "end": end[:7], "months": st["months"],
                     "median_names": float(s.notna().sum(axis=1).median()), "spread_bp": st["mean_bp"], "t": st["t"],
                     "p_one_sided": p_one, "placebo_p": placebo_p(s, r, q["ls"].mean(), rng)})
    res = pd.DataFrame(rows)
    e1 = res.iloc[0]
    passed = bool(e1["t"] > 2 and e1["placebo_p"] < 0.05)

    # E2: alpha with the controls available before 2022 (index and momentum; market caps start 2022-06)
    kospi = pd.read_parquet(RAW / "full_IDX_KS11.parquet")["Close"]
    idx_m = kospi.resample("ME").last()
    bench = (idx_m.shift(-1) / idx_m - 1)
    bench.index = [min([d for d in px.index if d.to_period("M") == p.to_period("M")], default=pd.NaT) for p in bench.index]
    bench = bench[bench.index.notna()]
    mom = quintile_returns(px.shift(1) / px.shift(12) - 1, ret)["ls"]
    e2 = []
    for label, (start, end) in (("pre-AI", (str(first_ok.date()), PRE[1])), ("full", (str(first_ok.date()), FULL_END))):
        y = window(quintile_returns(window(sig, start, end), window(ret, start, end)), start, end)["ls"]
        X = pd.DataFrame({"index": bench.reindex(y.index), "momentum": mom.reindex(y.index)})
        d = pd.concat([y.rename("spread"), X], axis=1).dropna()
        m = sm.OLS(d["spread"], sm.add_constant(d.drop(columns="spread"))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        e2.append({"window": label, "months": len(d), "alpha_bp": 1e4 * m.params["const"], "alpha_t": m.tvalues["const"],
                   "beta_index": m.params["index"], "beta_momentum": m.params["momentum"]})

    sub = []
    for label, (start, end) in (("2017–2019", ("2017-01-01", "2019-12-31")),
                                ("2018–2019 memory bust", ("2018-01-01", "2019-12-31")),
                                ("2020–2022", ("2020-01-01", "2022-12-31")),
                                ("2023–2026 (known)", ("2023-01-01", FULL_END))):
        s, r = window(sig, start, end), window(ret, start, end)
        if len(s) < 6:
            continue
        st = nw_stats(quintile_returns(s, r)["ls"])
        sub.append({"period": label, "months": st["months"], "spread_bp": st["mean_bp"], "t": st["t"]})

    L = ["# Q22 — Does the effect exist before the AI era? (Korea, extended history)", "",
         "Follows `docs/q22_extended_history_preregistration.md` (committed before this script was written).",
         "One-sided (positive); the decisive test is E1.", "",
         f"Universe: {len(u)} codes ({px.shape[1]} with prices). DART's multi-account API returns only annual figures for",
         f"2015, so trailing-four-quarter signals begin later: the first month with at least {MIN_NAMES} signals is",
         f"**{first_ok.date()}**, which sets the start of the decisive window (a data constraint, not a chosen window).", "",
         "## E1 and E3", "", fmt(res), "",
         f"**E1 {'PASSES' if passed else 'FAILS'}** (needs t > 2 and one-sided placebo p < 0.05).", "",
         "## E2 — alpha after controls", "",
         "Market caps start at the 2022-06 KRX snapshot, so the size control is unavailable before 2023 and these",
         "regressions use the index and momentum controls only.", "", fmt(pd.DataFrame(e2)), "",
         "## Sub-periods (descriptive, no significance tests)", "", fmt(pd.DataFrame(sub)), ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q22_extended_history.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
