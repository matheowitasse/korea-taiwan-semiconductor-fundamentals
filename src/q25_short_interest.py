"""Q25: do the stocks this strategy would short actually carry short interest?

Descriptive measurement (not a hypothesis test). It replaces the inference in the paper's Section 6 — that small
KOSDAQ names probably cannot be borrowed — with what the market actually does, now that every listed Korean stock has
been eligible for short selling since 2025-03-31.

For each KRX short-position snapshot: the share of names carrying any net short position, and the size of that
position relative to market capitalisation, for
    - the strategy's bottom quintile (what it would short),
    - its top quintile (what it would buy),
    - the rest of the chip universe,
    - all listed issues on that market, and the 350 largest companies (a KOSPI 200 / KOSDAQ 150 scale reference).

Usage: python src/q25_short_interest.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SHORT = ROOT / "data" / "raw" / "krx_short"
RESULTS = ROOT / "results"


def load_snapshots() -> pd.DataFrame:
    frames = []
    for f in sorted(SHORT.glob("*_position.csv")):
        market, date, _ = f.stem.split("_")
        d = pd.read_csv(f, dtype={"Issue code": str})
        d.columns = [c.strip() for c in d.columns]
        d["stock_code"] = d["Issue code"].str.zfill(6)
        d["date"] = pd.Timestamp(date)
        d["market"] = market
        for c in ("Quantity_Net short position", "Amount_Net short position", "Amount_Market cap.", "Proportion"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
        frames.append(d[["stock_code", "date", "market", "Quantity_Net short position",
                         "Amount_Net short position", "Amount_Market cap.", "Proportion"]])
    return pd.concat(frames, ignore_index=True)


def load_transactions() -> pd.DataFrame:
    frames = []
    for f in sorted(SHORT.glob("*_transaction.csv")):
        market, date, _ = f.stem.split("_")
        d = pd.read_csv(f, dtype={"Issue code": str})
        d.columns = [c.strip() for c in d.columns]
        d["stock_code"] = d["Issue code"].str.zfill(6)
        d["date"], d["market"] = pd.Timestamp(date), market
        vol = pd.to_numeric(d["Quantity_Short-selling volume_Total"], errors="coerce")
        tot = pd.to_numeric(d["Quantity_Trading volume"], errors="coerce")
        d["short_volume"], d["trading_volume"] = vol, tot
        d["short_share_%"] = 100 * vol / tot.replace(0, np.nan)
        frames.append(d[["stock_code", "date", "market", "short_volume", "trading_volume", "short_share_%"]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def describe_txn(g: pd.DataFrame, label: str) -> dict:
    if not len(g):
        return {"group": label, "names": 0}
    traded = g["trading_volume"] > 0
    shorted = g["short_volume"] > 0
    return {"group": label, "names": len(g), "traded_%": 100 * traded.mean(),
            "with_any_short_sale_%": 100 * shorted.mean(),
            "median_short_share_of_volume_%": g.loc[shorted, "short_share_%"].median() if shorted.any() else 0.0}


def describe(g: pd.DataFrame, label: str) -> dict:
    if not len(g):
        return {"group": label, "names": 0}
    has = g["Amount_Net short position"] > 0
    return {"group": label, "names": len(g), "with_short_%": 100 * has.mean(),
            "median_short_%_of_cap": g.loc[has, "Proportion"].median() if has.any() else 0.0,
            "mean_short_%_of_cap": g["Proportion"].mean(),
            "median_cap_bn_KRW": (g["Amount_Market cap."] / 1e9).median()}


def main() -> None:
    snaps = load_snapshots()
    sig, px, ret, mcap, _ = bt.korea()
    rows = []
    for date, day in snaps.groupby("date"):
        month_ends = sig.index[sig.index <= date]
        if not len(month_ends):
            continue
        t = month_ends[-1]
        s = sig.loc[t].dropna()
        q = pd.qcut(s.rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        bottom = set(s.index[q == 1])
        top = set(s.index[q == 5])
        universe = set(s.index)
        day = day.copy()
        big = set(day.nlargest(350, "Amount_Market cap.")["stock_code"])
        for label, codes in (("strategy short side (bottom quintile)", bottom),
                             ("strategy long side (top quintile)", top),
                             ("rest of the chip universe", universe - bottom - top),
                             ("350 largest listed companies", big)):
            r = describe(day[day["stock_code"].isin(codes)], label)
            rows.append({"date": date.date(), "signal_month": str(t.date()), **r})
        rows.append({"date": date.date(), "signal_month": str(t.date()), **describe(day, "all listed issues")})

    # short-sale volume on the transaction date
    txn = load_transactions()
    txn_rows = []
    if len(txn):
        for date, day in txn.groupby("date"):
            t = sig.index[sig.index <= date][-1]
            s2 = sig.loc[t].dropna()
            q2 = pd.qcut(s2.rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
            groups = {"strategy short side (bottom quintile)": set(s2.index[q2 == 1]),
                      "strategy long side (top quintile)": set(s2.index[q2 == 5]),
                      "rest of the chip universe": set(s2.index) - set(s2.index[q2 == 1]) - set(s2.index[q2 == 5])}
            for label, codes in groups.items():
                txn_rows.append({"date": date.date(), **describe_txn(day[day["stock_code"].isin(codes)], label)})
            txn_rows.append({"date": date.date(), **describe_txn(day, "all listed issues")})

    res = pd.DataFrame(rows)
    piv = res.pivot_table(index="group", columns="date", values="with_short_%").round(1)
    med = res.pivot_table(index="group", columns="date", values="median_short_%_of_cap").round(2)

    L = ["# Q25 — Do the stocks the strategy would short actually carry short interest?", "",
         "Descriptive measurement from KRX net short positions by issue (page 33001), imported with",
         "`src/q25_import_short_positions.py`. Every listed Korean stock has been eligible for short selling since",
         "2025-03-31, so these snapshots show what the market does rather than what the rules allow.", "",
         "## Share of names carrying any net short position (%)", "", "```", piv.to_string(), "```", "",
         "## Median net short position as a share of market capitalisation, among names that have one (%)", "",
         "```", med.to_string(), "```", "",
         "## Short-sale volume on 2026-09-17 (page 32001)", "", "```",
         (pd.DataFrame(txn_rows).to_string(index=False, float_format=lambda v: f"{v:.2f}")
          if txn_rows else "no transaction files imported"), "```", "",
         "## Full detail (positions)", "", "```",
         res.to_string(index=False, float_format=lambda v: f"{v:.2f}"), "```", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q25_short_interest.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
