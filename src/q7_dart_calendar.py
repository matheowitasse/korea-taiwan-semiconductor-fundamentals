"""Q7 step 2: earnings-announcement calendar for all Korean listed companies from DART.

Downloads disclosure lists (no company filter, 3-month windows) for:
  - I002 공정공시 (fair disclosure)  -> preliminary results: report names containing "영업(잠정)실적"
  - I001 수시공시 (timely disclosure) -> "매출액또는손익구조" (sales / profit change of 30%+, 15% for large firms)
  - A001/A002/A003 정기공시          -> annual / half-year / quarterly reports
Keeps only earnings-related rows. Output: data/interim/dart_earnings_disclosures.csv
DART gives the receipt DATE only (no time) -> studies must not rely on intraday timing.
No price or return data is used.
"""

import os
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "dart_earnings_disclosures.csv"
API = "https://opendart.fss.or.kr/api/list.json"
START, END = date(2022, 7, 1), date.today()
DETAIL_TYPES = {"I002": "fair", "I001": "timely", "A001": "annual", "A002": "half", "A003": "quarterly"}
EARNINGS_KEYWORDS = ("영업(잠정)실적", "매출액또는손익구조", "사업보고서", "반기보고서", "분기보고서")
SLEEP = 0.15


def windows(start: date, end: date, months: int = 3):
    cur = start
    while cur <= end:
        nxt = min(date(cur.year + (cur.month + months - 1) // 12, (cur.month + months - 1) % 12 + 1, 1) - timedelta(days=1), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def fetch(session: requests.Session, key: str, detail: str, a: date, b: date) -> list[dict]:
    rows, page = [], 1
    while True:
        params = {"crtfc_key": key, "bgn_de": f"{a:%Y%m%d}", "end_de": f"{b:%Y%m%d}", "pblntf_detail_ty": detail,
                  "page_no": page, "page_count": 100}
        for attempt in range(4):
            try:
                j = session.get(API, params=params, timeout=60).json()
                break
            except (requests.RequestException, ValueError):
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(f"failed: {detail} {a}..{b} page {page}")
        if j.get("status") == "013":
            return rows
        if j.get("status") == "020":
            raise SystemExit("DART request limit reached; re-run later (finished windows are kept)")
        if j.get("status") != "000":
            raise RuntimeError(f"DART status {j.get('status')}: {j.get('message')}")
        rows += [r for r in j["list"] if any(k in r["report_nm"].replace(" ", "") for k in EARNINGS_KEYWORDS)]
        if page >= int(j["total_page"]):
            return rows
        page += 1
        time.sleep(SLEEP)


def main() -> None:
    key = os.environ.get("DART_API_KEY") or exit("DART_API_KEY is not set")
    done = pd.read_csv(OUT, dtype=str) if OUT.exists() else pd.DataFrame()
    done_keys = set(zip(done["detail"], done["window"])) if len(done) else set()
    session = requests.Session()
    for detail, label in DETAIL_TYPES.items():
        for a, b in windows(START, END):
            wkey = f"{a:%Y%m%d}-{b:%Y%m%d}"
            if (detail, wkey) in done_keys and b < END:
                continue
            rows = fetch(session, key, detail, a, b)
            df = pd.DataFrame(rows).assign(detail=detail, kind=label, window=wkey)
            if len(done):
                done = done[~((done["detail"] == detail) & (done["window"] == wkey))]
            done = pd.concat([done, df], ignore_index=True)
            done.to_csv(OUT, index=False, encoding="utf-8-sig")
            print(f"{detail} {wkey}: {len(rows)} earnings-related disclosures")
    print(f"saved {len(done)} rows -> {OUT}")
    print(done.groupby("kind").size().to_string())


if __name__ == "__main__":
    main()
