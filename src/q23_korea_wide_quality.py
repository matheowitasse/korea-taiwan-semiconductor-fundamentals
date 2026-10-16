"""Q23: build a market-wide Korean quality factor (KOR-QMJ) — as specified in docs/q23_korea_wide_quality_spec.md.

AQR's QMJ country files and Ken French's international library do not cover Korea, so the benchmark is built here from
every KOSPI/KOSDAQ company in the DART register.

Steps (run in order):
  python src/q23_korea_wide_quality.py prices       # monthly bars for ~2,600 listed companies (Yahoo)
  python src/q23_korea_wide_quality.py financials   # DART: total assets + operating profit, 2015 -> today
  python src/q23_korea_wide_quality.py build        # KOR-QMJ and KOR-QMJ-ex-chip monthly factor returns

Outputs: data/raw/kr_wide/prices_monthly.parquet, data/interim/kr_wide_financials.csv,
         data/interim/kr_wide_quality_factor.csv
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
RAW = ROOT / "data" / "raw" / "kr_wide"
PRICES = RAW / "prices_monthly.parquet"
FINS = INTERIM / "kr_wide_financials.csv"
FACTOR = INTERIM / "kr_wide_quality_factor.csv"

API = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
REPORTS = {"11013": 1, "11012": 2, "11014": 3, "11011": 4}
YEARS = range(2015, 2027)
KEEP = {"자산총계", "영업이익"}
START = "2014-01-01"
BATCH = 60
WINSOR = 3.0
MIN_NAMES = 100


def listed() -> pd.DataFrame:
    c = pd.read_csv(INTERIM / "dart_companies.csv", dtype=str)
    c = c[c["corp_cls"].isin(["Y", "K"]) & c["stock_code"].notna()].drop_duplicates("stock_code").copy()
    c["ticker"] = c["stock_code"] + c["corp_cls"].map({"Y": ".KS", "K": ".KQ"})
    return c.reset_index(drop=True)


# ---------------------------------------------------------------- prices

def cmd_prices() -> None:
    u = listed()
    RAW.mkdir(parents=True, exist_ok=True)
    have = pd.read_parquet(PRICES) if PRICES.exists() else pd.DataFrame()
    todo = [t for t in u["ticker"] if t.split(".")[0] not in have.columns]
    print(f"{len(u)} listed companies; {len(todo)} to download")
    frames = [have] if len(have) else []
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        d = yf.download(batch, start=START, interval="1mo", auto_adjust=True, group_by="ticker",
                        threads=True, progress=False)
        cols = {}
        for t in batch:
            try:
                s = d[t]["Close"].dropna() if len(batch) > 1 else d["Close"].dropna()
            except KeyError:
                continue
            if len(s) >= 12:
                cols[t.split(".")[0]] = s
        if cols:
            frames.append(pd.DataFrame(cols))
        print(f"  {min(i + BATCH, len(todo))}/{len(todo)} ({sum(len(f.columns) for f in frames)} series)", flush=True)
        time.sleep(1.5)
    out = pd.concat(frames, axis=1)
    out = out.loc[:, ~out.columns.duplicated()]
    out.index = pd.to_datetime(out.index).tz_localize(None).normalize()
    out.to_parquet(PRICES)
    print(f"saved {PRICES}: {out.shape[1]} companies, {out.index.min().date()} -> {out.index.max().date()}")


# ---------------------------------------------------------------- financials

def get_json(session: requests.Session, params: dict, tries: int = 5) -> dict:
    for attempt in range(tries):
        try:
            return session.get(API, params=params, timeout=60).json()
        except (requests.RequestException, ValueError):
            if attempt == tries - 1:
                raise
            time.sleep(3 * (attempt + 1))
    return {}


def cmd_financials() -> None:
    """Each request returns 100 companies' statements and DART answers slowly, so the batches for one year are
    fetched by a small thread pool (measured: ~90 minutes per year sequentially)."""
    key = os.environ.get("DART_API_KEY") or sys.exit("DART_API_KEY is not set")
    years = YEARS
    if "--years" in sys.argv:
        a, b = sys.argv[sys.argv.index("--years") + 1].split("-")
        years = range(int(a), int(b) + 1)
    corp = sorted(listed()["corp_code"].unique())
    done = pd.read_csv(FINS, dtype={"corp_code": str}) if FINS.exists() else pd.DataFrame()
    done_keys = set(zip(done.get("year", []), done.get("quarter", []))) if len(done) else set()
    batches = [corp[i:i + 100] for i in range(0, len(corp), 100)]
    rows = []

    def fetch(args):
        year, reprt, q, chunk = args
        session = requests.Session()
        j = get_json(session, {"crtfc_key": key, "corp_code": ",".join(chunk), "bsns_year": year,
                               "reprt_code": reprt})
        if j.get("status") == "020":
            raise SystemExit("DART request limit reached; re-run later (progress is saved per year)")
        out = []
        for r in j.get("list", []):
            acc = r.get("account_nm", "").replace(" ", "")
            if acc in KEEP:
                out.append({"corp_code": r["corp_code"], "year": year, "quarter": q, "account": acc,
                            "fs_div": r.get("fs_div"),
                            "amount": pd.to_numeric(str(r.get("thstrm_amount", "")).replace(",", ""), errors="coerce"),
                            "cum": pd.to_numeric(str(r.get("thstrm_add_amount", "")).replace(",", ""), errors="coerce")})
        return out

    for year in years:
        tasks = [(year, reprt, q, chunk) for reprt, q in REPORTS.items()
                 if (year, q) not in done_keys for chunk in batches]
        if not tasks:
            continue
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=6) as pool:
            for out in pool.map(fetch, tasks):
                rows += out
        print(f"  {year} done in {time.time() - t0:.0f}s, {len(rows)} rows so far", flush=True)
        pd.concat([done, pd.DataFrame(rows)], ignore_index=True).to_csv(FINS, index=False, encoding="utf-8-sig")
    print(f"saved {FINS}")


# ---------------------------------------------------------------- factor

def quality_panel(fins: pd.DataFrame, month_ends: pd.DatetimeIndex, code_of: dict) -> pd.DataFrame:
    """Trailing four-quarter operating profit / total assets, usable only after the statutory filing deadline."""
    fins = fins.copy()
    fins["pref"] = (fins["fs_div"] == "CFS").astype(int)
    fins = fins.sort_values("pref", ascending=False).drop_duplicates(["corp_code", "year", "quarter", "account"])
    wide = fins.pivot_table(index=["corp_code", "year", "quarter"], columns="account", values=["amount", "cum"])
    out = {}
    for corp, g in wide.groupby(level=0):
        code = code_of.get(corp)
        if code is None:
            continue
        g = g.droplevel(0)
        idx = [(y, q) for y, q in g.index]
        op = pd.Series({(y, q): (g.loc[(y, q), ("amount", "영업이익")] if ("amount", "영업이익") in g.columns else np.nan)
                        for y, q in idx})
        assets = pd.Series({(y, q): (g.loc[(y, q), ("amount", "자산총계")] if ("amount", "자산총계") in g.columns else np.nan)
                            for y, q in idx})
        t = pd.Series({k: k[0] * 4 + k[1] for k in op.index})
        s = pd.DataFrame({"op": op.values, "assets": assets.values, "t": t.values}).dropna(subset=["t"]).sort_values("t")
        s = s.set_index("t")
        s = s.reindex(range(int(s.index.min()), int(s.index.max()) + 1))
        ttm = s["op"].rolling(4, min_periods=4).sum()
        q = (ttm / s["assets"]).dropna()
        vals = {}
        for tq, v in q.items():
            year, quarter = (tq - 1) // 4, (tq - 1) % 4 + 1
            q_end = pd.Timestamp(year=int(year), month=quarter * 3, day=1) + pd.offsets.MonthEnd(0)
            usable = q_end + pd.Timedelta(days=90 if quarter == 4 else 45)
            vals[usable] = v
        if vals:
            s2 = pd.Series(vals).sort_index()
            out[code] = s2.reindex(s2.index.union(month_ends)).ffill().reindex(month_ends)
    return pd.DataFrame(out)


def zscore(df: pd.DataFrame) -> pd.DataFrame:
    z = df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)
    return z.clip(-WINSOR, WINSOR)


def spread(sig: pd.DataFrame, ret: pd.DataFrame) -> pd.Series:
    rows = {}
    for t in sig.index:
        if t not in ret.index:
            continue
        d = pd.concat([sig.loc[t].rename("s"), ret.loc[t].rename("r")], axis=1).dropna()
        if len(d) < MIN_NAMES:
            continue
        q = pd.qcut(d["s"].rank(method="first"), 5, labels=False)
        rows[t] = d.loc[q == 4, "r"].mean() - d.loc[q == 0, "r"].mean()
    return pd.Series(rows).sort_index()


def cmd_build() -> None:
    px = pd.read_parquet(PRICES)
    px = px[~px.index.duplicated()].sort_index()
    ret = px.shift(-1) / px - 1                      # next-month return
    fins = pd.read_csv(FINS, dtype={"corp_code": str})
    u = listed()
    code_of = dict(zip(u["corp_code"], u["stock_code"]))
    qual = quality_panel(fins, px.index, code_of)
    qual = qual.reindex(columns=px.columns)
    chip = set(pd.read_csv(INTERIM / "q22_universe_codes.csv", dtype=str)["stock_code"])
    z_all = zscore(qual)
    z_ex = zscore(qual.drop(columns=[c for c in qual.columns if c in chip], errors="ignore"))
    f_all, f_ex = spread(z_all, ret), spread(z_ex, ret.reindex(columns=z_ex.columns))
    out = pd.DataFrame({"kor_qmj": f_all, "kor_qmj_ex_chip": f_ex})
    out.to_csv(FACTOR)
    names = qual.notna().sum(axis=1)
    print(f"quality coverage: median {names.median():.0f} companies per month (max {names.max():.0f})")
    print(f"factor months: {len(out.dropna())}, {out.index.min().date()} -> {out.index.max().date()}")
    print((out.dropna().mean() * 1e4).round(1).to_string(), "bp per month (mean)")
    print(f"saved {FACTOR}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"prices": cmd_prices, "financials": cmd_financials, "build": cmd_build}.get(
        cmd, lambda: sys.exit(__doc__))()
