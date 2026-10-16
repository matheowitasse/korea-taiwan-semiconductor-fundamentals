"""Q1 step 3: extract first-release figures from the downloaded KCS 10-day / 20-day releases.

Output: data/interim/kcs_releases_extracted.csv, one row per release, with:
  period (year, month, day_end 10/20), posted date,
  total exports (USD mn) and YoY %, semiconductor exports (USD mn) and YoY %, semis share %,
  working days (previous year / current year), daily average exports,
  quality flags (which fields were found, text vs table YoY agreement).

Format notes:
  2016-2018: semis YoY only in text; no working days.
  2019+    : detail table with semis value, working days and daily average in a footnote.
  2024+    : semis share of exports; table in USD mn instead of USD 100mn.
"""

import html as htmllib
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_text import document_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "kcs"
OUT = ROOT / "data" / "interim" / "kcs_releases_extracted.csv"

NUM = r"[△\-]?\s*\d[\d,]*\.?\d*"
Q = r"[’'‘`]?"


def to_float(s: str | None) -> float | None:
    if s is None:
        return None
    s = s.replace(",", "").replace(" ", "")
    neg = s.startswith("△") or s.startswith("-")
    v = float(s.lstrip("△-"))
    return -v if neg else v


def pick_document(folder: Path) -> Path | None:
    for ext in (".hwp", ".hwpx", ".pdf"):
        files = sorted(folder.glob(f"*{ext}"))
        if files:
            return files[0]
    return None


def page_body_text(folder: Path) -> str:
    html = (folder / "page.html").read_text(encoding="utf-8")
    html = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.S)
    return htmllib.unescape(re.sub(r"<[^>]+>", "\n", html))


def export_section(text: str) -> str:
    """Text between the export overview and the import overview (import lines also mention 반도체)."""
    start = text.find("수출현황")
    end = text.find("수입현황", start + 1)
    return text[start:end if end > 0 else len(text)] if start >= 0 else text


def extract(text: str) -> dict:
    t = text.replace("\r", "")
    flat = re.sub(r"\s+", " ", t)
    row: dict = {}

    m = re.search(r"수출\s*(" + NUM + r")\s*억\s*(?:달러|불)", flat)
    row["exports_total_usd_100mn_text"] = to_float(m.group(1)) if m else None
    m = re.search(r"전년\s*동기\s*대비\s*수출\s*(" + NUM + r")\s*%", flat)
    row["exports_total_yoy_text"] = to_float(m.group(1)) if m else None

    sec = re.sub(r"\s+", " ", export_section(t))
    # 2023 format adds an arrow: 반도체(△35.4%↓)
    m = re.search(r"반도체\s*\(\s*(" + NUM + r")\s*%?\s*[↑↓]?\s*\)", sec)
    row["semis_yoy_text"] = to_float(m.group(1)) if m else None
    m = re.search(r"반도체\s*수출\s*비중은\s*(" + NUM + r")\s*%", flat)
    row["semis_share_pct"] = to_float(m.group(1)) if m else None

    # Detail table: "반도체" line, then value line, then YoY line (first occurrence = export column)
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    row["semis_exports_usd_mn"] = row["semis_yoy_table"] = None
    for i, ln in enumerate(lines[:-2]):
        if ln == "반도체" and re.fullmatch(r"\d[\d,]*\.?\d*", lines[i + 1]) and re.match(r"[△\-]?\d", lines[i + 2]):
            before = "\n".join(lines[:i])
            unit_pos = max(before.rfind("단위"), 0)
            unit = before[unit_pos:unit_pos + 20]
            value = to_float(lines[i + 1])
            row["semis_exports_usd_mn"] = value * 100 if "억" in unit else value
            row["semis_yoy_table"] = to_float(re.match(NUM, lines[i + 2]).group(0))
            break

    m = re.search(r"조업일수\s*\[\s*\(\s*" + Q + r"(\d\d)[^)]*\)\s*([\d.]+)\s*일\s*,\s*\(\s*" + Q + r"(\d\d)[^)]*\)\s*([\d.]+)\s*일", flat)
    row["workdays_prev_year"] = float(m.group(2)) if m else None
    row["workdays_curr_year"] = float(m.group(4)) if m else None
    if not m:  # 2018 variant: (조업일수:’17년,’18년 7.5일 동일) -> same in both years
        m2 = re.search(r"조업일수\s*[:：]\s*" + Q + r"\d\d\s*년\s*,\s*" + Q + r"\d\d\s*년\s*([\d.]+)\s*일\s*동일", flat)
        if m2:
            row["workdays_prev_year"] = row["workdays_curr_year"] = float(m2.group(1))
    if row["workdays_curr_year"] is None:  # 2019 variant: 조업일수는 14.5일로 전년 동기와 동일
        m4 = re.search(r"조업일수는\s*([\d.]+)\s*일로\s*전년\s*동기와\s*동일", flat)
        if m4:
            row["workdays_prev_year"] = row["workdays_curr_year"] = float(m4.group(1))
    if row["workdays_curr_year"] is None:  # 2018 variant: 조업일수는 ... ’17년 15.5일에서 ’18년 13일로
        m3 = re.search(r"조업일수는.{0,40}?" + Q + r"\d\d\s*년\s*([\d.]+)\s*일에서\s*" + Q + r"\d\d\s*년\s*([\d.]+)\s*일", flat)
        if m3:
            row["workdays_prev_year"], row["workdays_curr_year"] = float(m3.group(1)), float(m3.group(2))
    m = re.search(r"일평균\s*수출액?\s*\[\s*\([^)]*\)\s*([\d.]+)\s*,\s*\([^)]*\)\s*([\d.]+)\s*억", flat)
    row["daily_avg_exports_prev_usd_100mn"] = float(m.group(1)) if m else None
    row["daily_avg_exports_curr_usd_100mn"] = float(m.group(2)) if m else None
    return row


def main() -> None:
    rows = []
    for folder in sorted(p for p in RAW.iterdir() if p.is_dir() and (p / "page.html").exists()):
        posted, kind, ntt_sn = folder.name.split("_")
        doc = pick_document(folder)
        source, text, error = None, "", None
        try:
            if doc is not None:
                source, text = doc.suffix.lower().lstrip("."), document_text(doc)
            if "반도체" not in text:  # fall back to the page body
                source, text = "html", page_body_text(folder)
        except Exception as e:  # keep going; record the failure
            error = f"{type(e).__name__}: {e}"
        title_m = re.search(r"(20\d\d|" + Q + r"\d\d)\s*년\s*(\d+)\s*월", text)
        row = {"posted": posted, "type": kind, "ntt_sn": ntt_sn, "source": source, "error": error}
        if title_m:
            y = title_m.group(1).lstrip("’'‘`")
            row["period_year"] = int(y) if len(y) == 4 else 2000 + int(y)
            row["period_month"] = int(title_m.group(2))
        row["period_day_end"] = 10 if kind == "10day" else 20
        row.update(extract(text) if text else {})
        rows.append(row)

    df = pd.DataFrame(rows)
    df["yoy_text_table_match"] = (df["semis_yoy_text"] - df["semis_yoy_table"]).abs() < 0.05
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")

    df["year"] = df["posted"].str[:4]
    cov = df.groupby("year").agg(
        releases=("ntt_sn", "count"),
        semis_yoy=("semis_yoy_text", lambda s: s.notna().sum()),
        semis_value=("semis_exports_usd_mn", lambda s: s.notna().sum()),
        workdays=("workdays_curr_year", lambda s: s.notna().sum()),
        total_exports=("exports_total_usd_100mn_text", lambda s: s.notna().sum()),
        errors=("error", lambda s: s.notna().sum()),
    )
    print(cov.to_string())
    both = df.dropna(subset=["semis_yoy_text", "semis_yoy_table"])
    print(f"\ntext vs table semis YoY agree: {both['yoy_text_table_match'].sum()}/{len(both)}")
    print(f"Saved {len(df)} rows to {OUT}")


if __name__ == "__main__":
    main()
