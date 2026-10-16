"""Q26: what do transaction costs do to the spread? — as specified in docs/q26_transaction_costs_spec.md.

Costs modelled per stock-month: half the Corwin-Schultz spread, commission, securities transaction tax on sells,
a borrow fee on the short leg, and Amihud-style linear market impact that grows with fund size.

Implementation work on the frozen finding: it changes the net return, not the measured spread.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402
from q8_multifactor import nw_stats, quintile_returns  # noqa: E402
from q13_leg_decomposition import adjust  # noqa: E402
from q18_short_ban import controls_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"

START = pd.Timestamp("2023-01-01")
COMMISSION = 0.0005          # 5 bp each way
SELL_TAX = 0.0020            # 20 bp on sells (assumption, varied below)
BORROW_FEES = (0.01, 0.03, 0.05)
FUND_SIZES_USD = (1e6, 1e7, 5e7, 2e8)
KRW_PER_USD = 1300
MIN_DAYS = 120


def daily(code: str) -> pd.DataFrame | None:
    y, k = RAW / "q7_yahoo" / f"{code}.parquet", RAW / "krx_prices" / f"{code}.parquet"
    if y.exists():
        d = pd.read_parquet(y)
        d.columns = [c if isinstance(c, str) else c[0] for c in d.columns]
        return d[["High", "Low", "Close", "Volume"]].astype(float)
    if k.exists():
        d = pd.read_parquet(k)
        return d.rename(columns={"Trading volume": "Volume"})[["High", "Low", "Close", "Volume"]].astype(float)
    return None


def corwin_schultz(h: pd.Series, l: pd.Series) -> pd.Series:
    """Two-day high-low spread estimator (Corwin and Schultz, 2012); negatives set to zero."""
    hl = np.log(h / l) ** 2
    beta = hl + hl.shift(1)
    h2, l2 = h.rolling(2).max(), l.rolling(2).min()
    gamma = np.log(h2 / l2) ** 2
    k = 3 - 2 * np.sqrt(2)
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    s = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    return s.clip(lower=0)


def cost_panels(codes, month_ends: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Per stock-month: half-spread, Amihud lambda (return per KRW traded) and median daily traded value."""
    half_spread, lam, value = {}, {}, {}
    for code in codes:
        d = daily(code)
        if d is None or len(d) < MIN_DAYS:
            continue
        d = d[(d["Volume"] > 0) & (d["Close"] > 0) & (d["High"] >= d["Low"])]
        if len(d) < MIN_DAYS:
            continue
        s = corwin_schultz(d["High"], d["Low"]).rolling(60, min_periods=20).median()
        traded = d["Close"] * d["Volume"]
        illiq = (d["Close"].pct_change().abs() / traded).replace([np.inf, -np.inf], np.nan)
        illiq = illiq.clip(upper=illiq.quantile(0.99))     # trim days with almost no turnover
        half_spread[code] = (s / 2).reindex(month_ends, method="ffill")
        lam[code] = illiq.rolling(250, min_periods=MIN_DAYS).mean().reindex(month_ends, method="ffill")
        value[code] = traded.rolling(250, min_periods=MIN_DAYS).median().reindex(month_ends, method="ffill")
    return pd.DataFrame(half_spread), pd.DataFrame(lam), pd.DataFrame(value)


def leg_weights(sig: pd.DataFrame, ret: pd.DataFrame, which: int) -> pd.DataFrame:
    """Equal weights on the chosen quintile each month (1 = bottom, 5 = top)."""
    w = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    for t in sig.index:
        if t not in ret.index:
            continue
        d = pd.concat([sig.loc[t].rename("s"), ret.loc[t].rename("r")], axis=1).dropna()
        if len(d) < 25:
            continue
        q = pd.qcut(d["s"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        names = d.index[q == which]
        if len(names):
            w.loc[t, names] = 1.0 / len(names)
    return w


def costs_for(w: pd.DataFrame, hs: pd.DataFrame, lam: pd.DataFrame, fund_krw: float,
              tax_on_sell: float, borrow: float, is_short: bool) -> pd.Series:
    """Monthly cost of running one leg, in return units.

    Costs are computed per stock and weighted by how much of that stock is traded. Market impact is the Amihud form
    applied to each stock's own order: cost_i = lambda_i * (fund * |dw_i|), and the portfolio pays |dw_i| of it, so the
    leg-level impact is fund * sum_i lambda_i * dw_i^2. (An earlier version applied the whole portfolio's order value
    to every stock, which overstated impact by roughly the number of holdings.)
    """
    dw = (w - w.shift(1)).abs()
    hs_a = hs.reindex_like(w)
    lam_a = lam.reindex_like(w)
    spread_cost = (dw * hs_a).sum(axis=1)                  # half-spread paid on the value traded
    commission = dw.sum(axis=1) * COMMISSION
    tax = (dw.sum(axis=1) / 2) * tax_on_sell               # half of the traded value is sales
    impact = fund_krw * (lam_a * dw.pow(2)).sum(axis=1)
    return spread_cost + commission + tax + impact + (borrow / 12 if is_short else 0.0)


def main() -> None:
    sig, px, ret, mcap, index_close = bt.korea()
    sig = sig.loc[sig.index >= START]
    ret = ret.reindex(sig.index)
    hs, lam, value = cost_panels(px.columns, sig.index)
    print(f"cost inputs: spread {hs.notna().sum(axis=1).median():.0f} names/month, "
          f"lambda {lam.notna().sum(axis=1).median():.0f}", file=sys.stderr)

    q = quintile_returns(sig, ret)
    gross_long, gross_short = q["top"] - q["universe"], q["universe"] - q["bottom"]
    gross_ls = q["ls"]
    w_top, w_bot = leg_weights(sig, ret, 5), leg_weights(sig, ret, 1)
    ctrl = controls_for(px, ret, mcap, index_close)
    turn_top = (w_top - w_top.shift(1)).abs().sum(axis=1).div(2)
    turn_bot = (w_bot - w_bot.shift(1)).abs().sum(axis=1).div(2)

    rows = []
    for usd in FUND_SIZES_USD:
        fund = usd * KRW_PER_USD / 2          # half the fund on each leg of the long-short
        for borrow in BORROW_FEES:
            c_long = costs_for(w_top, hs, lam, fund, SELL_TAX, 0.0, False)
            c_short = costs_for(w_bot, hs, lam, fund, SELL_TAX, borrow, True)
            net_ls = (gross_ls - c_long - c_short).dropna()
            net_long = (gross_long - c_long).dropna()
            st_ls, st_lo = nw_stats(net_ls), nw_stats(net_long)
            a_ls, a_lo = adjust(net_ls, ctrl), adjust(net_long, ctrl)
            rows.append({"fund_usd_m": usd / 1e6, "borrow_%": borrow * 100,
                         "cost_long_bp": 1e4 * c_long.mean(), "cost_short_bp": 1e4 * c_short.mean(),
                         "net_long_short_bp": st_ls["mean_bp"], "t": st_ls["t"],
                         "alpha_bp": a_ls.get("alpha_bp", np.nan), "alpha_t": a_ls.get("alpha_t", np.nan),
                         "net_long_leg_bp": st_lo["mean_bp"], "long_leg_alpha_t": a_lo.get("alpha_t", np.nan)})
    res = pd.DataFrame(rows)

    # cost build-up at USD 10m, 3% borrow
    fund = 1e7 * KRW_PER_USD / 2
    build = []
    running_long = gross_long.copy()
    running_short = gross_short.copy()
    steps = [("gross", 0.0, 0.0, 0.0, False),
             ("+ half spread", None, 0.0, 0.0, False),
             ("+ commission", None, None, 0.0, False),
             ("+ sell tax", None, None, SELL_TAX, False),
             ("+ borrow 3%", None, None, SELL_TAX, True)]
    hs_l = (w_top * hs.reindex_like(w_top)).sum(axis=1)
    hs_s = (w_bot * hs.reindex_like(w_bot)).sum(axis=1)
    lam_l = (w_top * lam.reindex_like(w_top)).sum(axis=1)
    lam_s = (w_bot * lam.reindex_like(w_bot)).sum(axis=1)
    cum_l = pd.Series(0.0, index=gross_long.index)
    cum_s = pd.Series(0.0, index=gross_short.index)
    for label in ["gross", "+ half spread", "+ commission", "+ sell tax", "+ borrow 3%", "+ market impact (USD 10m)"]:
        if label == "+ half spread":
            cum_l += ((w_top - w_top.shift(1)).abs() * hs.reindex_like(w_top)).sum(axis=1)
            cum_s += ((w_bot - w_bot.shift(1)).abs() * hs.reindex_like(w_bot)).sum(axis=1)
        elif label == "+ commission":
            cum_l += (w_top - w_top.shift(1)).abs().sum(axis=1) * COMMISSION
            cum_s += (w_bot - w_bot.shift(1)).abs().sum(axis=1) * COMMISSION
        elif label == "+ sell tax":
            cum_l += (w_top - w_top.shift(1)).abs().sum(axis=1) / 2 * SELL_TAX
            cum_s += (w_bot - w_bot.shift(1)).abs().sum(axis=1) / 2 * SELL_TAX
        elif label == "+ borrow 3%":
            cum_s += 0.03 / 12
        elif label == "+ market impact (USD 10m)":
            cum_l += fund * (lam.reindex_like(w_top) * (w_top - w_top.shift(1)).abs().pow(2)).sum(axis=1)
            cum_s += fund * (lam.reindex_like(w_bot) * (w_bot - w_bot.shift(1)).abs().pow(2)).sum(axis=1)
        net = (gross_ls - cum_l - cum_s).dropna()
        st = nw_stats(net)
        build.append({"step": label, "net_bp": st["mean_bp"], "t": st["t"]})

    # break-even fund size: impact is linear in fund, so net alpha is linear in it too
    breakeven = []
    for borrow in BORROW_FEES:
        sub = res[res["borrow_%"] == borrow * 100].sort_values("fund_usd_m")
        x, y = sub["fund_usd_m"].values, sub["net_long_short_bp"].values
        cross = np.nan
        for i in range(len(x) - 1):
            if y[i] > 0 >= y[i + 1]:
                cross = x[i] + (x[i + 1] - x[i]) * y[i] / (y[i] - y[i + 1])
                break
        xl, yl = sub["fund_usd_m"].values, sub["net_long_leg_bp"].values
        cross_long = np.nan
        for i in range(len(xl) - 1):
            if yl[i] > 0 >= yl[i + 1]:
                cross_long = xl[i] + (xl[i + 1] - xl[i]) * yl[i] / (yl[i] - yl[i + 1])
                break
        breakeven.append({"borrow_%": borrow * 100, "long_short_breakeven_usd_m": cross,
                          "long_leg_breakeven_usd_m": cross_long})

    def fmt(df):
        return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.2f}") + "\n```"

    L = ["# Q26 — Transaction costs", "",
         "Follows `docs/q26_transaction_costs_spec.md` (committed before this script was written).",
         f"Korea, {sig.index.min().date()} → {sig.index.max().date()}. Half-spread from Corwin–Schultz, commission 5 bp",
         f"each way, sell tax {SELL_TAX*1e4:.0f} bp, Amihud linear impact, borrow fee on the short leg only.", "",
         f"Monthly turnover: long leg {turn_top.mean():.0%}, short leg {turn_bot.mean():.0%}. "
         f"Median half-spread among held names: long {hs_l[hs_l > 0].median()*1e4:.0f} bp, short {hs_s[hs_s > 0].median()*1e4:.0f} bp.", "",
         "## Cost build-up (USD 10m fund, 3% borrow)", "", fmt(pd.DataFrame(build)), "",
         "## Net performance by fund size and borrow fee", "", fmt(res), "",
         "## Break-even fund size (net monthly return crosses zero)", "", fmt(pd.DataFrame(breakeven)), "",
         "Impact is linear in fund size in this model, so these are interpolations between the rows above, not a",
         "separate estimate. Capacity in the real market is also limited by borrow availability: Q25 measured typical",
         "net short positions of about 0.55% of market capitalisation in these names.", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q26_transaction_costs.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
