"""Q7/Q21: import KIND delisting lists (상장폐지현황, 'Excel' export = HTML table in EUC-KR) and flag chip companies.

Copies every 상장폐지현황*.xls found in ~/Downloads into data/raw/kind/, parses and concatenates them with the files
already stored there (de-duplicated on stock code + delisting date), matches companies to the DART company list
(industry codes) and writes data/interim/kind_delisted.csv.
Several files are expected: the original 2022-07 → 2026-09 export plus year-by-year exports back to 2015, downloaded
for the extended-history sample. No price or return data is used.
"""

import html
import re
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "kind"
OUT = ROOT / "data" / "interim" / "kind_delisted.csv"
COMPANIES = ROOT / "data" / "interim" / "dart_companies.csv"
DOWNLOADS = Path.home() / "Downloads"


def norm(name: str) -> str:
    name = re.sub(r"\(주\)|㈜|주식회사|\(유\)|유한회사", "", str(name))
    return re.sub(r"[\s\.\-·]", "", name).upper()


def parse(path: Path) -> pd.DataFrame:
    text = path.read_bytes().decode("euc-kr", errors="replace")
    rows = []
    for tr in re.findall(r"<tr.*?</tr>", text, flags=re.S | re.I):
        cells = [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S | re.I)]
        rows.append([re.sub(r"\s+", " ", c) for c in cells])
    header, body = rows[0], [r for r in rows[1:] if len(r) == len(rows[0])]
    return pd.DataFrame(body, columns=header)


def collect() -> pd.DataFrame:
    """Copy any new downloads into data/raw/kind/, then parse everything stored there."""
    RAW.mkdir(parents=True, exist_ok=True)
    for src in sorted(DOWNLOADS.glob("상장폐지현황*.xls")):
        dest = RAW / f"kind_{src.stem}.xls"
        if not dest.exists():
            shutil.copy2(src, dest)
            print(f"copied {src.name} -> {dest.name}")
    frames = []
    for f in sorted(RAW.glob("*.xls")):
        d = parse(f)
        d["source_file"] = f.name
        print(f"  {f.name}: {len(d)} rows, columns {list(d.columns)[:6]}")
        frames.append(d)
    if not frames:
        raise SystemExit("no KIND files found in data/raw/kind/ or ~/Downloads")
    df = pd.concat(frames, ignore_index=True)
    code_col = next(c for c in df.columns if "종목코드" in c)
    date_col = next(c for c in df.columns if "폐지일자" in c)
    before = len(df)
    df = df.drop_duplicates([code_col, date_col]).reset_index(drop=True)
    print(f"total {before} rows -> {len(df)} after de-duplication on stock code + delisting date")
    return df


def main() -> None:
    df = collect()

    name_col = next(c for c in df.columns if "회사명" in c)
    code_col = next(c for c in df.columns if "종목코드" in c)
    reason_col = next(c for c in df.columns if "사유" in c)
    comp = pd.read_csv(COMPANIES, dtype=str)[["corp_code", "corp_name", "stock_code", "corp_cls", "induty_code"]]
    m = df.merge(comp.drop_duplicates("stock_code"), left_on=code_col, right_on="stock_code", how="left")
    # Moving between KOSDAQ and KOSPI (이전상장 / 시장 상장) is not a real delisting
    m["market_transfer"] = m[reason_col].str.contains("이전상장|시장 상장|시장상장", regex=True)
    m["spac_or_reit"] = m[name_col].str.contains("스팩|리츠|SPAC", case=False, regex=True)
    ind = m["induty_code"].fillna("")
    m["in_A"] = ind.str.startswith("261") | ind.str.startswith("29271")
    m["in_C_extra"] = ind.str.startswith("262")
    m.to_csv(OUT, index=False, encoding="utf-8-sig")

    real = m[~m["market_transfer"]]
    print(f"matched to DART by stock code: {m['corp_code'].notna().sum()} / {len(m)} | market transfers: {m['market_transfer'].sum()} "
          f"| SPACs/REITs: {m['spac_or_reit'].sum()}")
    chips = real[real["in_A"] | real["in_C_extra"]]
    print(f"real delistings in chip lists (A or 262): {len(chips)}")
    print(chips[[name_col, code_col, "폐지일자", reason_col, "induty_code", "in_A"]].to_string(index=False))
    unmatched = real[real["corp_code"].isna() & ~real["spac_or_reit"]]
    print(f"\nunmatched, not SPAC/REIT ({len(unmatched)}):", ", ".join(unmatched[name_col]))


if __name__ == "__main__":
    main()
