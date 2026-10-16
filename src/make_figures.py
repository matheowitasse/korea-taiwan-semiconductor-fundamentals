"""Figures for the paper, built from the same code paths as the results tables.

fig1: cumulative long-short spread, Korea (full history) and Taiwan, with the AI-era boundary marked.
fig2: the cost ladder — net spread by fund size, with the break-even point.

Usage: python src/make_figures.py
Output: paper/figures/fig1_cumulative.png, paper/figures/fig2_capacity.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402
import q22_extended_history as ext  # noqa: E402
from q8_multifactor import quintile_returns  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "figures"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 200})


def fig1() -> None:
    u = ext.universe()
    cal = pd.read_parquet(ROOT / "data" / "raw" / "full_IDX_KS11.parquet").index
    px, ret = ext.monthly_panel(u, cal)
    sig = ext.signal_panel(u, px)
    kr = quintile_returns(sig, ret)["ls"].dropna()
    kr = kr[kr.index >= "2016-11-01"]

    sig_tw, px_tw, ret_tw, _, _ = bt.taiwan()
    tw = quintile_returns(sig_tw.loc[sig_tw.index >= "2016-01-01"], ret_tw)["ls"].dropna()  # Q27: Taiwan extended back to 2016

    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    ax.plot(kr.index, (1 + kr).cumprod(), label=f"Korea ({len(kr)} months)", lw=1.6)
    ax.plot(tw.index, (1 + tw).cumprod(), label=f"Taiwan ({len(tw)} months)", lw=1.6)
    ax.axvline(pd.Timestamp("2023-01-01"), color="grey", ls="--", lw=0.9)
    ax.text(pd.Timestamp("2023-02-01"), ax.get_ylim()[1] * 0.97, "AI-era window begins",
            fontsize=7.5, color="grey", va="top")
    ax.set_yscale("log")
    ax.set_ylabel("cumulative long–short return (log scale, 1 = start)")
    ax.set_xlabel("")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Long–short spread on the fundamentals-improvement signal", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_cumulative.png")
    print("fig1:", len(kr), "Korean months,", len(tw), "Taiwanese months")


def fig2() -> None:
    sizes = np.array([1, 10, 50, 200])
    net = {1: 313.95, 3: 313.95, 5: 297.28}
    rows = {1.0: [330.62, 266.42, -18.90, -1088.83],
            3.0: [313.95, 249.75, -35.56, -1105.50],
            5.0: [297.28, 233.09, -52.23, -1122.17]}
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    for fee, vals in rows.items():
        ax.plot(sizes, vals, marker="o", lw=1.5, ms=4, label=f"borrow fee {fee:.0f}%")
    ax.axhline(0, color="black", lw=0.8)
    ax.axvspan(43, 47, color="grey", alpha=0.15)
    ax.text(48, 150, "break-even\n≈ USD 43–47m", fontsize=7.5, color="grey")
    ax.set_xscale("log")
    ax.set_xticks(sizes)
    ax.set_xticklabels(["1", "10", "50", "200"])
    ax.set_xlabel("fund size (USD m)")
    ax.set_ylabel("net long–short return (bp per month)")
    ax.legend(frameon=False)
    ax.set_title("What the spread is worth after costs", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_capacity.png")
    print("fig2 written")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig1()
    fig2()
