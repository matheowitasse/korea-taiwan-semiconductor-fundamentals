"""Q7: quarterly operating profit from DART (multi-company key accounts) for the SUE surprise measure, and the
pre-registered coverage check (SUE kept only if available for >= 70% of list-A discovery events). No returns are used.

DART fnlttMultiAcnt: up to 100 companies per call; reprt_code 11013 = Q1, 11012 = half-year, 11014 = Q3, 11011 = annual.
For Q1/half/Q3 reports thstrm_amount is the 3-month amount; for the annual report it is the full year, so
Q4 = annual − cumulative 9 months (thstrm_add_amount of the Q3 report). Consolidated (CFS) preferred, else separate (OFS).
Figures are as currently stored by DART (later restatements included) — not strictly point-in-time.
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
OUT = INTERIM / "dart_operating_profit.csv"
API = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
REPORTS = {"11013": 1, "11012": 2, "11014": 3, "11011": 4}
YEARS = range(2020, 2027)


def amount(s) -> float:
    s = str(s).replace(",", "").strip()
    return float(s) if s not in ("", "-", "nan", "None") else np.nan


def universe_corp_codes() -> list[str]:
    comp = pd.read_csv(INTERIM / "dart_companies.csv", dtype=str)
    codes = pd.read_csv(INTERIM / "q7_universe_codes.csv", dtype=str)["stock_code"]
    return sorted(comp[comp["stock_code"].isin(codes)]["corp_code"].unique())


def download() -> pd.DataFrame:
    key = os.environ.get("DART_API_KEY") or exit("DART_API_KEY is not set")
    corp = universe_corp_codes()
    rows, session = [], requests.Session()
    for year in YEARS:
        for reprt, q in REPORTS.items():
            for i in range(0, len(corp), 100):
                j = session.get(API, params={"crtfc_key": key, "corp_code": ",".join(corp[i:i + 100]),
                                             "bsns_year": year, "reprt_code": reprt}, timeout=60).json()
                if j.get("status") == "020":
                    raise SystemExit("DART request limit reached")
                for r in j.get("list", []):
                    if r.get("account_nm", "").replace(" ", "") == "영업이익" and r.get("sj_div") == "IS":
                        rows.append({"corp_code": r["corp_code"], "year": year, "quarter": q, "fs_div": r["fs_div"],
                                     "amount": amount(r.get("thstrm_amount")), "cum": amount(r.get("thstrm_add_amount"))})
                time.sleep(0.3)
        print(f"  {year} done, {len(rows)} rows")
    raw = pd.DataFrame(rows)
    # prefer consolidated statements
    raw["pref"] = (raw["fs_div"] == "CFS").astype(int)
    raw = raw.sort_values("pref", ascending=False).drop_duplicates(["corp_code", "year", "quarter"])
    wide = raw.set_index(["corp_code", "year", "quarter"])
    out = []
    for (c, y, q), r in wide.iterrows():
        op = r["amount"]
        if q == 4:  # annual report = full year; Q4 = year − 9-month cumulative from the Q3 report
            q3 = wide["cum"].get((c, y, 3), np.nan)
            op = r["amount"] - q3 if pd.notna(q3) else np.nan
        out.append({"corp_code": c, "year": y, "quarter": q, "fs_div": r["fs_div"], "op_profit": op})
    df = pd.DataFrame(out).sort_values(["corp_code", "year", "quarter"])
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    return df


def sue_table(op: pd.DataFrame) -> pd.DataFrame:
    op = op.copy()
    op["t"] = op["year"] * 4 + op["quarter"]
    full = op.set_index(["corp_code", "t"])["op_profit"]
    res = []
    for c, g in op.groupby("corp_code"):
        s = g.set_index("t")["op_profit"].reindex(range(g["t"].min(), g["t"].max() + 1))
        yoy = s - s.shift(4)
        sd = yoy.shift(1).rolling(8, min_periods=6).std()  # previous 8 quarters of YoY changes, at least 6
        sue = yoy / sd.replace(0, np.nan)
        for t, v in sue.dropna().items():
            res.append({"corp_code": c, "year": (t - 1) // 4, "quarter": (t - 1) % 4 + 1, "sue": v})
    return pd.DataFrame(res)


def coverage(sue: pd.DataFrame) -> None:
    comp = pd.read_csv(INTERIM / "dart_companies.csv", dtype=str)
    kind = pd.read_csv(INTERIM / "kind_delisted.csv", dtype=str)
    allc = pd.concat([comp[["corp_code", "induty_code"]], kind[["corp_code", "induty_code"]]]).drop_duplicates("corp_code")
    a_codes = set(allc[allc["induty_code"].fillna("").str.match(r"^(261|29271)")]["corp_code"])
    disc = pd.read_csv(INTERIM / "dart_earnings_disclosures.csv", dtype=str)
    disc = disc[~disc["report_nm"].str.strip().str.startswith("[") & disc["corp_code"].isin(a_codes)].copy()
    disc["date"] = pd.to_datetime(disc["rcept_dt"], format="%Y%m%d")
    disc = disc.sort_values(["corp_code", "date"])
    events, last = [], {}
    for r in disc.itertuples():
        if r.corp_code in last and (r.date - last[r.corp_code]).days <= 30:
            continue
        last[r.corp_code] = r.date
        events.append((r.corp_code, r.date))
    ev = pd.DataFrame(events, columns=["corp_code", "date"])
    ev = ev[(ev["date"] >= "2023-01-01") & (ev["date"] <= "2025-06-30")]
    # the reported quarter = the last completed calendar quarter before the disclosure
    # (e.g. Feb/Mar -> previous Q4, May -> Q1, Aug -> Q2, Nov -> Q3); assumes December fiscal year-ends
    qe = ev["date"].dt.to_period("Q") - 1
    ev["year"], ev["quarter"] = qe.dt.year, qe.dt.quarter
    m = ev.merge(sue, on=["corp_code", "year", "quarter"], how="left")
    share = m["sue"].notna().mean() * 100
    print(f"list-A discovery events: {len(m)} | with SUE: {m['sue'].notna().sum()} ({share:.1f}%) "
          f"-> T3 {'KEPT' if share >= 70 else 'DROPPED'} (pre-registered threshold 70%)")


def main() -> None:
    op = pd.read_csv(OUT, dtype={"corp_code": str}) if OUT.exists() else download()
    print(f"operating profit rows: {len(op)}, companies: {op['corp_code'].nunique()}")
    sue = sue_table(op)
    sue.to_csv(INTERIM / "dart_sue.csv", index=False, encoding="utf-8-sig")
    coverage(sue)


if __name__ == "__main__":
    main()
