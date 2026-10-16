"""Q20 step 1: download dilution-related filings (major-event reports) for the chip universe from DART.

Queried per company: with a corp_code the API accepts the full date range, so this is 262 requests rather than
paging every filing in Korea quarter by quarter (which is what a market-wide query requires).

Needs DART_API_KEY in the environment (never printed). No returns are computed here.
Output: data/interim/dart_major_events_raw.csv  (+ counts by filing type)
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
OUT = INTERIM / "dart_major_events_raw.csv"
API = "https://opendart.fss.or.kr/api/list.json"
START, END = "20220701", "20260921"
PAUSE = 0.12

TYPES = {"rights issue (유상증자)": "유상증자결정",
         "convertible bond (전환사채)": "전환사채권발행결정",
         "warrant bond (신주인수권부사채)": "신주인수권부사채권발행결정",
         "bonus issue (무상증자)": "무상증자결정",
         "exchangeable bond (교환사채)": "교환사채권발행결정",
         "capital reduction (감자)": "감자결정"}


def universe_corp_codes() -> list[str]:
    comp = pd.read_csv(INTERIM / "dart_companies.csv", dtype=str)
    uni = pd.read_csv(INTERIM / "q7_universe_codes.csv", dtype=str)
    return sorted(comp.merge(uni, on="stock_code")["corp_code"].dropna().unique())


def fetch(session: requests.Session, key: str, corp: str) -> list[dict]:
    rows, page = [], 1
    while True:
        j = session.get(API, params={"crtfc_key": key, "corp_code": corp, "bgn_de": START, "end_de": END,
                                     "pblntf_ty": "B", "page_no": page, "page_count": 100}, timeout=60).json()
        status = j.get("status")
        if status == "013":  # no filings for this company in the window
            return rows
        if status != "000":
            raise SystemExit(f"DART error for {corp}: {status} {j.get('message')}")
        rows += j.get("list", [])
        if page >= j.get("total_page", 1):
            return rows
        page += 1
        time.sleep(PAUSE)


def main() -> None:
    key = os.environ.get("DART_API_KEY") or sys.exit("DART_API_KEY is not set")
    corps = universe_corp_codes()
    session, rows = requests.Session(), []
    for i, corp in enumerate(corps, 1):
        rows += fetch(session, key, corp)
        if i % 50 == 0:
            print(f"  {i}/{len(corps)} companies, {len(rows)} filings", file=sys.stderr, flush=True)
        time.sleep(PAUSE)

    df = pd.DataFrame(rows).drop_duplicates("rcept_no")
    df["report_clean"] = df["report_nm"].str.replace(r"\[.*?\]", "", regex=True).str.strip()
    df["is_correction"] = df["report_nm"].str.strip().str.startswith("[")
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"major-event filings, {len(corps)} companies, {START} → {END}: {len(df)} "
          f"({int(df['is_correction'].sum())} corrections)")
    print(df.loc[~df["is_correction"], "report_clean"].value_counts().head(12).to_string())
    print()
    for label, name in TYPES.items():
        sub = df[(~df["is_correction"]) & df["report_clean"].str.contains(name, regex=False)]
        by_year = pd.to_datetime(sub["rcept_dt"]).dt.year.value_counts().sort_index().to_dict() if len(sub) else {}
        print(f"{label:34s}: {len(sub):4d} filings, {sub['corp_code'].nunique():3d} companies, by year {by_year}")


if __name__ == "__main__":
    main()
