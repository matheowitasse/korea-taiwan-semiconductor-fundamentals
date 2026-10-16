"""Q26b: how high would the borrow fee have to be to kill the net spread?

The borrow fee is the one cost input that is not publicly observable — commissions and the securities transaction tax
are published, spreads are estimated from public prices, and impact is a model. Q26 assumed 1–5% a year. Rather than
guess harder, this inverts the question and reports the bound: the fee at which the net long–short return reaches
zero, and the fee at which its t-statistic and risk-adjusted alpha fall below 2.

Implementation work on the frozen finding: it re-prices the same monthly spread, it does not re-test it.
Output: results/q26b_borrow_bound.md
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402
import q26_transaction_costs as q26  # noqa: E402
from q8_multifactor import nw_stats, quintile_returns  # noqa: E402
from q13_leg_decomposition import adjust  # noqa: E402
from q18_short_ban import controls_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "q26b_borrow_bound.md"

FUND_SIZES_USD = (1e6, 1e7, 5e7)
FEES = np.round(np.arange(0.0, 0.601, 0.0025), 4)      # 0% to 60% a year


def crossing(fees: np.ndarray, values: np.ndarray, level: float) -> float:
    """First fee at which `values` falls to `level`, linearly interpolated. NaN if it never does."""
    below = np.where(values <= level)[0]
    if len(below) == 0:
        return float("nan")
    i = below[0]
    if i == 0:
        return 0.0
    x0, x1, y0, y1 = fees[i - 1], fees[i], values[i - 1], values[i]
    return x0 if y1 == y0 else x0 + (y0 - level) * (x1 - x0) / (y0 - y1)


def main() -> None:
    sig, px, ret, mcap, index_close = bt.korea()
    sig = sig.loc[sig.index >= q26.START]
    ret = ret.reindex(sig.index)
    hs, lam, _ = q26.cost_panels(px.columns, sig.index)

    q = quintile_returns(sig, ret)
    gross_ls = q["ls"]
    w_top, w_bot = q26.leg_weights(sig, ret, 5), q26.leg_weights(sig, ret, 1)
    ctrl = controls_for(px, ret, mcap, index_close)

    rows = []
    for usd in FUND_SIZES_USD:
        fund = usd * q26.KRW_PER_USD / 2
        c_long = q26.costs_for(w_top, hs, lam, fund, q26.SELL_TAX, 0.0, False)
        nets, ts, alphas, alpha_ts = [], [], [], []
        for fee in FEES:
            c_short = q26.costs_for(w_bot, hs, lam, fund, q26.SELL_TAX, fee, True)
            net = (gross_ls - c_long - c_short).dropna()
            st, a = nw_stats(net), adjust(net, ctrl)
            nets.append(st["mean_bp"])
            ts.append(st["t"])
            alphas.append(a.get("alpha_bp", np.nan))
            alpha_ts.append(a.get("alpha_t", np.nan))
        nets, ts, alphas, alpha_ts = map(np.asarray, (nets, ts, alphas, alpha_ts))
        rows.append({
            "fund_usd_m": usd / 1e6,
            "net_bp_at_3%": nets[np.isclose(FEES, 0.03)][0],
            "fee_net_zero_%": 100 * crossing(FEES, nets, 0.0),
            "fee_t_below_2_%": 100 * crossing(FEES, ts, 2.0),
            "fee_alpha_zero_%": 100 * crossing(FEES, alphas, 0.0),
            "fee_alpha_t_below_2_%": 100 * crossing(FEES, alpha_ts, 2.0),
        })
    res = pd.DataFrame(rows)

    lines = [
        "# Q26b — the borrow-fee bound",
        "",
        "The borrow fee is the only cost input in Q26 that cannot be looked up: commissions and the securities",
        "transaction tax are published, half-spreads are estimated from public prices (Corwin-Schultz), and impact is a",
        "model. So instead of assuming a better number, we report how large the fee would have to be to overturn the",
        "conclusion. Everything else is held at the Q26 settings; the fee is swept from 0% to 60% a year.",
        "",
        "## Bounds on the Korean long-short, 2023-01 onwards",
        "",
        "```",
        res.round(2).to_string(index=False),
        "```",
        "",
        "Columns: the fee at which the net monthly return crosses zero, at which its Newey-West t crosses 2, and the",
        "same two for the risk-adjusted alpha (market, size and momentum controls).",
        "",
        "## Reading",
        "",
        "The point estimate is robust to the assumption: borrow would have to cost tens of per cent a year, which is",
        "deep special-rate territory, before the net spread disappears at a small fund size. Statistical significance is",
        "the fragile part -- the t-statistic falls below 2 at a far lower fee, so the confidence in the after-cost result,",
        "not the after-cost result itself, is what the borrow assumption buys.",
        "",
        "Borrow fees for the actual short-leg names can be observed directly from a broker's stock-loan quotes, or",
        "historically from Markit Securities Finance (WRDS). Until then these bounds stand in for the missing input.",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(res.round(2).to_string(index=False))
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
