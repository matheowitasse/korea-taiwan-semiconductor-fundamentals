"""Q8 diagnostics (NOT decisive tests): is the multi-factor result real, or an artefact of micro-caps,
extreme returns, delisting losses or costs?

Re-uses the pre-registered pipeline from q8_multifactor.py and re-computes the same portfolios under
restrictions. Nothing here changes the pre-registered verdict; it explains what drives it.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q8_multifactor import (DISCOVERY, FACTORS, INTERIM, RAW, VALIDATION, build_factors, composite, monthly_panel,
                            nw_stats, quintile_returns, universe)

RESULTS = Path(__file__).resolve().parents[1] / "results"
KEY = ["composite", "quality", "earn_mom", "value"]
COST_PER_TURNOVER = 0.0030


def turnover(sig: pd.DataFrame, quantile: int = 5) -> float:
    """Average share of the top-quintile portfolio replaced each month."""
    prev, tos = None, []
    for t in sig.index:
        s = sig.loc[t].dropna()
        if len(s) < 25:
            continue
        q = set(s[s.rank(method="first") > 0.8 * len(s)].index)
        if prev is not None and prev:
            tos.append(len(q - prev) / len(q))
        prev = q
    return float(np.mean(tos)) if tos else np.nan


def main() -> None:
    u = universe()
    cal = pd.read_parquet(RAW / "full_IDX_KS11.parquet").index
    px, ret = monthly_panel(u, cal)
    factors, mcap = build_factors(u, px, px.index)
    factors = {"composite": composite(factors), **factors}

    delisted = set(pd.read_csv(INTERIM / "kind_delisted.csv", dtype=str)["종목코드"].dropna())
    L = ["# Q8 diagnostics — what drives the multi-factor result", "",
         "Not decisive: the pre-registered verdict stands in `results/q8_multifactor.md`. These runs test whether the",
         "long-short result survives restrictions that remove micro-caps, extreme returns, delisting losses and costs.", ""]

    variants = {
        "as pre-registered": dict(),
        "returns winsorised ±30%": dict(wins=0.30),
        "price ≥ 1,000 KRW at formation": dict(min_price=1000),
        "market cap ≥ 50 bn KRW": dict(min_cap=50e9),
        "market cap ≥ 200 bn KRW": dict(min_cap=200e9),
        "delisted companies excluded": dict(drop_delisted=True),
        "all of the above (cap ≥ 50 bn, price ≥ 1,000, winsorised)": dict(wins=0.30, min_price=1000, min_cap=50e9),
    }

    for period_name, period in [("discovery 2023-01→2025-06", DISCOVERY), ("validation 2025-07→today", VALIDATION)]:
        rows = []
        for vname, opt in variants.items():
            r = ret.copy()
            if opt.get("wins"):
                r = r.clip(-opt["wins"], opt["wins"])
            mask = pd.DataFrame(True, index=px.index, columns=px.columns)
            if opt.get("min_price"):
                mask &= px >= opt["min_price"]
            if opt.get("min_cap"):
                mask &= mcap >= opt["min_cap"]
            if opt.get("drop_delisted"):
                mask &= ~pd.Series(px.columns.isin(delisted), index=px.columns)
            for k in KEY:
                sig = factors[k].where(mask)
                sig = sig.loc[(sig.index >= period[0]) & (sig.index <= period[1])]
                port = quintile_returns(sig, r.reindex(sig.index))
                st = nw_stats(port["ls"])
                lo = nw_stats(port["long_only"])
                to = turnover(sig)
                rows.append({"variant": vname, "factor": k, "months": st["months"], "n_stocks": round(port["n"].mean()),
                             "ls_bp": st["mean_bp"], "ls_t": st["t"], "long_only_bp": lo["mean_bp"],
                             "long_only_t": lo["t"], "turnover": round(to, 2) if np.isfinite(to) else np.nan,
                             "long_only_after_cost_bp": lo["mean_bp"] - 1e4 * COST_PER_TURNOVER * (to if np.isfinite(to) else 0)})
        df = pd.DataFrame(rows)
        L += [f"## {period_name}", "", "```", df.to_string(index=False, float_format=lambda v: f"{v:.1f}"), "```", ""]

    # where do the returns come from: monthly medians and the worst/best contributors
    rows = []
    for k in KEY:
        sig = factors[k].loc[(factors[k].index >= DISCOVERY[0]) & (factors[k].index <= VALIDATION[1])]
        port = quintile_returns(sig, ret.reindex(sig.index))
        rows.append({"factor": k, "mean_ls_bp": port["ls"].mean() * 1e4, "median_ls_bp": port["ls"].median() * 1e4,
                     "months_positive_%": 100 * (port["ls"] > 0).mean(), "worst_month_bp": port["ls"].min() * 1e4,
                     "best_month_bp": port["ls"].max() * 1e4,
                     "top_bp": port["top"].mean() * 1e4, "bottom_bp": port["bottom"].mean() * 1e4,
                     "universe_bp": port["universe"].mean() * 1e4})
    L += ["## Shape of the returns (2023-01 → today, both periods pooled)", "", "```",
          pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.1f}"), "```", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q8_diagnostics.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
