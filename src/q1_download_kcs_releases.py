"""Q1 step 2: download the 10-day and 20-day KCS trade releases (page body + attachments).

Reads data/interim/kcs_release_index.csv, and for each release saves into data/raw/kcs/<posted>_<type>_<ntt_sn>/:
  - page.html        the press release page (some years include the text in the body)
  - attachments      every attached file (hwp / hwpx / pdf), original file names kept
Already-downloaded releases are skipped, so the script can be re-run safely.
"""

import html as htmllib
import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "interim" / "kcs_release_index.csv"
RAW = ROOT / "data" / "raw" / "kcs"

BASE = "https://www.customs.go.kr"
DETAIL_URL = BASE + "/kcs/na/ntt/selectNttInfo.do"
HEADERS = {"User-Agent": "Mozilla/5.0 (academic research; korea-chip-loop)"}
SLEEP = 1.0

# <a href="/common/nttFileDownload.do?fileKey=...">file name.hwp</a> (name may be in the link text or title)
FILE_LINK_RE = re.compile(r'href="(/common/nttFileDownload\.do\?fileKey=[0-9a-f]+)"[^>]*>(.*?)</a>', re.S)
EXT_RE = re.compile(r"[^<>/\\\n]+?\.(?:hwpx|hwp|pdf|xlsx|xls|zip)", re.I)


def get_with_retry(session: requests.Session, url: str, tries: int = 4, **kwargs) -> requests.Response:
    """The customs server occasionally times out; retry with increasing pauses."""
    for attempt in range(1, tries + 1):
        try:
            r = session.get(url, headers=HEADERS, **kwargs)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == tries:
                raise
            print(f"  retry {attempt}/{tries - 1} after {type(e).__name__}")
            time.sleep(15 * attempt)


def safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\s]+', "_", name).strip("_")


def main() -> None:
    idx = pd.read_csv(INDEX, dtype=str)
    todo = idx[idx["type"].isin(["10day", "20day"])].sort_values("posted")
    session = requests.Session()
    log = []
    for i, row in enumerate(todo.itertuples(), 1):
        folder = RAW / f"{row.posted}_{row.type}_{row.ntt_sn}"
        if (folder / "page.html").exists():
            continue
        folder.mkdir(parents=True, exist_ok=True)
        r = get_with_retry(session, DETAIL_URL, timeout=60,
                           params={"mi": "2891", "bbsId": "1362", "nttSn": row.ntt_sn, "nttSnUrl": row.ntt_sn_url})
        page = r.text
        n_files = 0
        for href, inner in FILE_LINK_RE.findall(page):
            text = htmllib.unescape(re.sub(r"<[^>]+>", " ", inner))
            m = EXT_RE.search(text)
            fname = safe_name(m.group(0)) if m else f"attachment_{href[-8:]}"
            f = get_with_retry(session, BASE + href, timeout=120)
            (folder / fname).write_bytes(f.content)
            n_files += 1
            time.sleep(SLEEP)
        (folder / "page.html").write_text(page, encoding="utf-8")  # written last = marks release as complete
        log.append({"folder": folder.name, "title": row.title, "files": n_files})
        print(f"[{i}/{len(todo)}] {folder.name}: {n_files} file(s)")
        time.sleep(SLEEP)

    if log:
        pd.DataFrame(log).to_csv(RAW / "download_log.csv", mode="a", index=False,
                                 header=not (RAW / "download_log.csv").exists(), encoding="utf-8-sig")
    print("done")


if __name__ == "__main__":
    main()
