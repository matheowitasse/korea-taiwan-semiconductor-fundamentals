"""Q9 step 2: Taiwanese data without any API key.

(a) Month-end valuation ratios per stock (P/E, P/B, dividend yield) from TWSE (listed) and TPEx (OTC).
(b) Monthly revenue per company from the MOPS archive (published by the 10th of the following month) — a fundamental
    signal Korea does not have.
(c) Prices come from Yahoo (already used for Taiwan tickers elsewhere in the project).

Outputs: data/raw/taiwan/pbr_<YYYYMM>.csv, data/raw/taiwan/revenue_<YYYY>_<M>_<market>.csv
No returns are computed here.
"""

import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "taiwan"
UA = {"User-Agent": "Mozilla/5.0 (academic research; korea-chip-loop)"}
START, END = pd.Timestamp("2016-01-01"), pd.Timestamp.today()  # Q27: extended back from 2022-06 for the pre-AI test
SLEEP = 3.0  # TWSE blocks fast clients


def month_ends() -> list[pd.Timestamp]:
    cal = pd.read_parquet(ROOT / "data" / "raw" / "full_IDX_TWII.parquet").index
    cal = cal[(cal >= START) & (cal <= END)]
    return list(pd.Series(cal, index=cal).groupby([cal.year, cal.month]).max())


def fetch_pbr(d: pd.Timestamp) -> pd.DataFrame | None:
    """TWSE: P/E, dividend yield and P/B for every listed stock on one date."""
    url = "https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d"
    r = requests.get(url, params={"date": f"{d:%Y%m%d}", "selectType": "ALL", "response": "json"},
                     headers=UA, timeout=60)
    if r.status_code != 200 or not r.text.strip().startswith("{"):
        return None
    j = r.json()
    rows = j.get("data") or (j.get("tables", [{}])[0].get("data") if j.get("tables") else None)
    if not rows:
        return None
    cols = ["code", "name", "pe", "dividend_yield", "pb"]
    df = pd.DataFrame([r[:5] for r in rows], columns=cols[:5])
    for c in ["pe", "dividend_yield", "pb"]:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce")
    return df.assign(date=d.date())


def fetch_revenue(year: int, month: int, market: str) -> pd.DataFrame | None:
    """MOPS monthly revenue archive (ROC year). market: 'sii' listed, 'otc' over-the-counter."""
    roc = year - 1911
    url = f"https://mopsov.twse.com.tw/nas/t21/{market}/t21sc03_{roc}_{month}.html"
    r = requests.get(url, headers=UA, timeout=60)
    if r.status_code != 200:
        return None
    html = r.content.decode("big5", errors="replace")
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.S):
        cells = [re.sub(r"<[^>]+>|&nbsp;", " ", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)]
        if len(cells) >= 5 and re.fullmatch(r"\d{4}", cells[0] or ""):
            rows.append({"code": cells[0], "name": cells[1], "revenue_current": cells[2],
                         "revenue_prev_month": cells[3], "revenue_year_ago": cells[4]})
    if not rows:
        return None
    df = pd.DataFrame(rows)
    for c in ["revenue_current", "revenue_prev_month", "revenue_year_ago"]:
        df[c] = pd.to_numeric(df[c].str.replace(",", ""), errors="coerce")
    return df.assign(year=year, month=month, market=market)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for d in month_ends():
        path = OUT / f"pbr_{d:%Y%m}.csv"
        if path.exists():
            continue
        df = fetch_pbr(d)
        if df is None:
            print(f"  valuation {d.date()}: no data")
        else:
            df.to_csv(path, index=False, encoding="utf-8-sig")
            print(f"  valuation {d.date()}: {len(df)} stocks")
        time.sleep(SLEEP)

    period = pd.period_range(START.to_period("M"), (END - pd.Timedelta(days=40)).to_period("M"), freq="M")
    for p in period:
        for market in ["sii", "otc"]:
            path = OUT / f"revenue_{p.year}_{p.month}_{market}.csv"
            if path.exists():
                continue
            df = fetch_revenue(p.year, p.month, market)
            if df is None:
                print(f"  revenue {p} {market}: no data")
            else:
                df.to_csv(path, index=False, encoding="utf-8-sig")
                print(f"  revenue {p} {market}: {len(df)} companies")
            time.sleep(SLEEP)

    print(f"valuation files: {len(list(OUT.glob('pbr_*.csv')))} | revenue files: {len(list(OUT.glob('revenue_*.csv')))}")


if __name__ == "__main__":
    main()
