"""Q7 step 3: daily Yahoo prices for the chip universe (lists A, B, C) and a coverage check.

Downloads adjusted daily OHLCV from 2022-06-01 for every company in B ∪ C, caches them in data/raw/q7_yahoo/<code>.parquet
and reports how complete the data is. Only checks that prices EXIST (rows, gaps, zero-volume days) — no returns are computed.
"""

import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
COMPANIES = ROOT / "data" / "interim" / "dart_companies.csv"
CACHE = ROOT / "data" / "raw" / "q7_yahoo"
REPORT = ROOT / "data" / "interim" / "q7_price_coverage.csv"
START = "2022-06-01"
EXTRA = ["005930", "058470", "095340", "240810", "036930"]  # list B additions: Samsung, Leeno, ISC, Wonik IPS, Jusung


def universe() -> pd.DataFrame:
    c = pd.read_csv(COMPANIES, dtype=str)
    c = c[c["corp_cls"].isin(["Y", "K"])].copy()
    ind = c["induty_code"].fillna("")
    c["in_A"] = ind.str.startswith("261") | ind.str.startswith("29271")
    c["in_B"] = c["in_A"] | c["stock_code"].isin(EXTRA)
    c["in_C"] = c["in_A"] | ind.str.startswith("262")
    c = c[c["in_B"] | c["in_C"]].copy()
    c["yahoo"] = c["stock_code"] + c["corp_cls"].map({"Y": ".KS", "K": ".KQ"})
    return c.reset_index(drop=True)


def download(tickers: list[str]) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [t for t in tickers if not (CACHE / f"{t.split('.')[0]}.parquet").exists()]
    end = str(date.today() + timedelta(days=1))
    for i in range(0, len(todo), 40):
        batch = todo[i:i + 40]
        data = yf.download(batch, start=START, end=end, auto_adjust=True, group_by="ticker", threads=True, progress=False)
        for t in batch:
            try:
                df = data[t].dropna(how="all") if len(batch) > 1 else data.dropna(how="all")
            except KeyError:
                df = pd.DataFrame()
            if len(df):
                df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
                df[["Open", "High", "Low", "Close", "Volume"]].to_parquet(CACHE / f"{t.split('.')[0]}.parquet")
        print(f"  downloaded {min(i + 40, len(todo))}/{len(todo)}")
        time.sleep(2)


def main() -> None:
    u = universe()
    print(f"universe B ∪ C: {len(u)} companies (A {u['in_A'].sum()}, B {u['in_B'].sum()}, C {u['in_C'].sum()})")
    download(u["yahoo"].tolist())

    cal = pd.read_parquet(ROOT / "data" / "raw" / "full_IDX_KS11.parquet").index
    cal = cal[cal >= START]
    rows = []
    for r in u.itertuples():
        path = CACHE / f"{r.stock_code}.parquet"
        if not path.exists():
            rows.append({"stock_code": r.stock_code, "corp_name": r.corp_name, "market": r.corp_cls,
                         "in_A": r.in_A, "in_B": r.in_B, "in_C": r.in_C, "rows": 0})
            continue
        df = pd.read_parquet(path)
        span = cal[(cal >= df.index.min()) & (cal <= df.index.max())]
        valid = df[(df["Volume"] > 0) & df["Close"].notna()]
        rows.append({
            "stock_code": r.stock_code, "corp_name": r.corp_name, "market": r.corp_cls,
            "in_A": r.in_A, "in_B": r.in_B, "in_C": r.in_C, "rows": len(df),
            "first": df.index.min().date(), "last": df.index.max().date(),
            "coverage_%": round(100 * len(valid.index.intersection(span)) / max(len(span), 1), 1),
            "zero_volume_days": int((df["Volume"] == 0).sum()),
            "starts_after_2023": df.index.min() > pd.Timestamp("2023-01-02"),
        })
    rep = pd.DataFrame(rows)
    rep.to_csv(REPORT, index=False, encoding="utf-8-sig")

    print(f"\nno Yahoo data: {(rep['rows'] == 0).sum()} -> {', '.join(rep.loc[rep['rows'] == 0, 'corp_name'])}")
    ok = rep[rep["rows"] > 0]
    print(f"with data: {len(ok)} | coverage within their own date span: median {ok['coverage_%'].median()}%, "
          f"< 95%: {(ok['coverage_%'] < 95).sum()} | listed after 2023-01-02 (IPO in the period): {ok['starts_after_2023'].sum()}")
    print(f"zero-volume days (halts / suspensions): companies with > 20 such days: {(ok['zero_volume_days'] > 20).sum()}")
    for lst in ["in_A", "in_B", "in_C"]:
        sub = rep[rep[lst]]
        print(f"  {lst[-1]}: {len(sub)} companies, {int((sub['rows'] > 0).sum())} with Yahoo data")
    print(f"report -> {REPORT}")


if __name__ == "__main__":
    main()
