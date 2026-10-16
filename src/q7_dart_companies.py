"""Q7 step 1: all Korean listed companies with their DART industry code (KSIC).

Downloads DART's company code list, then the company overview (company.json) for every company with a stock code.
Output: data/interim/dart_companies.csv (resumable: companies already fetched are skipped).
No price or return data is used.

Needs the DART API key in the environment variable DART_API_KEY (never printed or saved by this script).
"""

import io
import os
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "dart_companies.csv"
API = "https://opendart.fss.or.kr/api"
FIELDS = ["corp_code", "corp_name", "corp_name_eng", "stock_code", "corp_cls", "induty_code", "est_dt", "acc_mt"]
SLEEP = 0.12


def api_key() -> str:
    key = os.environ.get("DART_API_KEY")
    if not key:
        raise SystemExit("DART_API_KEY is not set")
    return key


def corp_codes(key: str) -> pd.DataFrame:
    r = requests.get(f"{API}/corpCode.xml", params={"crtfc_key": key}, timeout=120)
    r.raise_for_status()
    xml = zipfile.ZipFile(io.BytesIO(r.content)).read("CORPCODE.xml")
    rows = [{c.tag: (c.text or "").strip() for c in item} for item in ET.fromstring(xml).iter("list")]
    df = pd.DataFrame(rows)
    return df[df["stock_code"] != ""].reset_index(drop=True)


def main() -> None:
    key = api_key()
    codes = corp_codes(key)
    print(f"companies with a stock code: {len(codes)}")
    done = pd.read_csv(OUT, dtype=str) if OUT.exists() else pd.DataFrame(columns=FIELDS)
    todo = codes[~codes["corp_code"].isin(done["corp_code"])]
    rows, session = [], requests.Session()
    for i, row in enumerate(todo.itertuples(), 1):
        for attempt in range(4):
            try:
                j = session.get(f"{API}/company.json", params={"crtfc_key": key, "corp_code": row.corp_code}, timeout=30).json()
                break
            except (requests.RequestException, ValueError):
                time.sleep(5 * (attempt + 1))
        else:
            continue
        if j.get("status") == "020":  # request limit reached: save and stop, re-run later
            print("DART request limit reached; saving progress")
            break
        if j.get("status") == "000":
            rows.append({f: j.get(f, "") for f in FIELDS})
        if i % 250 == 0:
            pd.concat([done, pd.DataFrame(rows)]).to_csv(OUT, index=False, encoding="utf-8-sig")
            print(f"  {i}/{len(todo)}")
        time.sleep(SLEEP)
    out = pd.concat([done, pd.DataFrame(rows)]).drop_duplicates("corp_code")
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"saved {len(out)} companies -> {OUT}")
    print(out["corp_cls"].value_counts().to_string())


if __name__ == "__main__":
    main()
