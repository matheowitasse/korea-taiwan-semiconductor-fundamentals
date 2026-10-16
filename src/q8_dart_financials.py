"""Q8 step 1: full DART key accounts (balance sheet + income statement) for the chip universe.

Same API as q7_dart_operating_profit.py (fnlttMultiAcnt, 100 companies per call) but keeps every key account
(자산총계, 자본총계, 매출액, 영업이익, 당기순이익, ...), which the value and quality factors need.
Output: data/interim/dart_financials.csv (one row per company / year / quarter / account). No returns are used.
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
OUT = INTERIM / "dart_financials.csv"
API = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
REPORTS = {"11013": 1, "11012": 2, "11014": 3, "11011": 4}
YEARS = range(2020, 2027)   # default: the frozen-finding sample; --years extends it (Q22)
KEEP = {"자산총계", "부채총계", "자본총계", "매출액", "영업이익", "당기순이익", "이익잉여금"}


def get_json(session: requests.Session, params: dict, tries: int = 5) -> dict:
    """DART occasionally drops the connection on long runs; retry with backoff instead of losing the whole pull."""
    for attempt in range(tries):
        try:
            return session.get(API, params=params, timeout=60).json()
        except (requests.RequestException, ValueError) as e:
            if attempt == tries - 1:
                raise
            print(f"    retry {attempt + 1}/{tries - 1} after {type(e).__name__}", flush=True)
            time.sleep(3 * (attempt + 1))
    return {}


def amount(s) -> float:
    s = str(s).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return np.nan


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", help="e.g. 2014-2019; default is the frozen-finding range")
    ap.add_argument("--codes-file", default=str(INTERIM / "q7_universe_codes.csv"))
    a = ap.parse_args()
    years = YEARS if not a.years else range(*(int(x) for x in a.years.split("-")[:1] + [int(a.years.split("-")[1]) + 1]))

    key = os.environ.get("DART_API_KEY") or exit("DART_API_KEY is not set")
    comp = pd.read_csv(INTERIM / "dart_companies.csv", dtype=str)
    codes = pd.read_csv(a.codes_file, dtype=str)["stock_code"]
    corp = sorted(comp[comp["stock_code"].isin(codes)]["corp_code"].unique())
    done = pd.read_csv(OUT, dtype={"corp_code": str}) if OUT.exists() else pd.DataFrame()
    done_years = set(zip(done.get("year", []), done.get("quarter", []))) if len(done) else set()

    rows, session = [], requests.Session()
    for year in years:
        for reprt, q in REPORTS.items():
            if (year, q) in done_years:
                continue
            for i in range(0, len(corp), 100):
                j = get_json(session, {"crtfc_key": key, "corp_code": ",".join(corp[i:i + 100]),
                                       "bsns_year": year, "reprt_code": reprt})
                if j.get("status") == "020":
                    raise SystemExit("DART request limit reached; re-run later")
                for r in j.get("list", []):
                    acc = r.get("account_nm", "").replace(" ", "")
                    if acc in KEEP:
                        rows.append({"corp_code": r["corp_code"], "year": year, "quarter": q, "account": acc,
                                     "fs_div": r.get("fs_div"), "sj_div": r.get("sj_div"),
                                     "amount": amount(r.get("thstrm_amount")), "cum": amount(r.get("thstrm_add_amount"))})
                time.sleep(0.3)
        print(f"  {year} done, {len(rows)} new rows", flush=True)
        if rows:
            pd.concat([done, pd.DataFrame(rows)], ignore_index=True).to_csv(OUT, index=False, encoding="utf-8-sig")
    df = pd.concat([done, pd.DataFrame(rows)], ignore_index=True) if len(rows) else done
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"saved {len(df)} rows ({df['corp_code'].nunique()} companies, accounts: {sorted(df['account'].unique())}) -> {OUT}")


if __name__ == "__main__":
    main()
