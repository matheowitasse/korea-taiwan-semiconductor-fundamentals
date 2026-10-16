"""Q1 step 1: index Korea Customs Service press releases about trade (10-day, 20-day, monthly).

Builds data/interim/kcs_release_index.csv with one row per press release: post id, title, posting date,
release type. Does not download attachments yet — this only answers "how far back does the archive go?".
"""

import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "kcs_release_index.csv"

LIST_URL = "https://www.customs.go.kr/kcs/na/ntt/selectNttList.do"
HEADERS = {"User-Agent": "Mozilla/5.0 (academic research; korea-chip-loop)"}
PAGE_SIZE = 50
SLEEP = 1.0

ROW_RE = re.compile(r"<tr.*?</tr>", re.S)
LINK_RE = re.compile(r'data-id="(\d+)"\s+data-url="([0-9a-f]+)"\s+class="nttInfoBtn"\s+title="([^"]+)"')
DATE_RE = re.compile(r"(20\d\d)[.-](\d\d)[.-](\d\d)")


def classify(title: str) -> str:
    t = re.sub(r"[∼〜～\-]", "~", title.replace(" ", ""))  # titles mix several tilde characters
    if re.search(r"1일~(\d+월)?10일", t):
        return "10day"
    if re.search(r"1일~(\d+월)?20일", t):
        return "20day"
    if "월간" in t or "수출입동향" in t or re.search(r"\d+월수출입현황", t):
        return "monthly"
    return "other"


def fetch_page(session: requests.Session, page: int) -> list[dict]:
    data = {"mi": "2891", "bbsId": "1362", "searchType": "sj", "searchValue": "수출입",
            "listCo": str(PAGE_SIZE), "currPage": str(page)}
    r = session.post(LIST_URL, data=data, headers=HEADERS, timeout=60)
    r.raise_for_status()
    rows = []
    for tr in ROW_RE.findall(r.text):
        m = LINK_RE.search(tr)
        if not m:
            continue
        dates = DATE_RE.findall(tr)
        posted = "-".join(dates[-1]) if dates else None
        title = m.group(3).strip()
        rows.append({"ntt_sn": m.group(1), "ntt_sn_url": m.group(2), "title": title,
                     "posted": posted, "type": classify(title)})
    return rows


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    all_rows, page = [], 1
    while True:
        rows = fetch_page(session, page)
        new = [r for r in rows if r["ntt_sn"] not in {x["ntt_sn"] for x in all_rows}]
        if not new:
            break
        all_rows += new
        print(f"page {page}: {len(new)} rows, oldest so far {min(r['posted'] or '9999' for r in all_rows)}")
        page += 1
        time.sleep(SLEEP)

    df = pd.DataFrame(all_rows).sort_values("posted")
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    df["year"] = df["posted"].str[:4]
    print("\nReleases by year and type:")
    print(df.pivot_table(index="year", columns="type", values="ntt_sn", aggfunc="count", fill_value=0).to_string())
    for kind in ["10day", "20day", "monthly"]:
        sub = df[df["type"] == kind]
        if len(sub):
            print(f"{kind}: {len(sub)} releases, oldest {sub['posted'].min()} ({sub.iloc[0]['title']})")
    print(f"Saved {len(df)} rows to {OUT}")


if __name__ == "__main__":
    main()
