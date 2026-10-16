"""Build the current bottom-quintile (short-leg) name list for a broker stock-loan lookup.

The borrow fee is the one cost input in Q26 with no public source, and Q26b bounds it rather than observing it. This
script produces the list to look up by hand in a broker's stock-loan tool (IBKR: Get Help > Short Securities (SLB)
Availability, which takes a bulk upload), so the assumption can be replaced with quoted rates for the names the
strategy would actually short.

Korean ISINs are KR7 + the six-digit issue code + "00" + an ISIN check digit, which is computable, so the list carries
identifiers the tool accepts directly.

Usage: python src/q28_short_leg_borrow_list.py
Output: data/live/short_leg_borrow_lookup_<month>.csv
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "live"
FACTORS = ("composite",)


def isin_check_digit(body: str) -> str:
    """Standard ISIN check digit: letters to two digits (A=10), then Luhn from the right."""
    digits = "".join(str(int(c, 36)) for c in body)
    total, double = 0, True
    for ch in reversed(digits):
        d = int(ch) * (2 if double else 1)
        total += d - 9 if d > 9 else d
        double = not double
    return str((10 - total % 10) % 10)


def korea_isin(code: str) -> str:
    body = f"KR7{code}00"
    return body + isin_check_digit(body)


def main() -> None:
    sig, px, ret, mcap, _ = bt.korea()
    month = sig.index[-1]
    row = sig.loc[month].dropna()
    if row.empty:
        raise SystemExit("no signal for the latest month")

    n = len(row)
    bottom = row.nsmallest(max(1, n // 5))
    last_px = px.reindex(px.index[px.index <= month]).ffill().iloc[-1]
    last_cap = mcap.reindex(mcap.index[mcap.index <= month]).ffill().iloc[-1] if mcap is not None else None

    out = pd.DataFrame({
        "stock_code": bottom.index,
        "isin": [korea_isin(c) for c in bottom.index],
        "score": bottom.values.round(4),
        "price_krw": [last_px.get(c) for c in bottom.index],
        # bt.korea() carries market capitalisation in KRW; the live files report billions.
        "market_cap_bn_krw": [None if last_cap is None else last_cap.get(c) / 1e9 for c in bottom.index],
    })
    out.insert(0, "month_end", month.date())
    out["borrow_fee_pct"] = ""          # to be filled in by hand from the broker's quote
    out["shares_available"] = ""
    out["n_lenders"] = ""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"short_leg_borrow_lookup_{month:%Y-%m}.csv"
    out.to_csv(path, index=False, encoding="utf-8-sig")

    print(f"universe scored this month: {n}    bottom quintile: {len(out)}")
    print(out.head(10).to_string(index=False))
    print(f"\nwritten: {path}")
    print("\nPaste the isin column into the broker's bulk lookup; record fee, availability and lender count in the")
    print("three empty columns. Q26b's bound (net zero at ~33%/yr, alpha t=2 at ~4.3%) is what these rates replace.")


if __name__ == "__main__":
    main()
