"""Q23 test: is the chip-sector effect distinct from a market-wide Korean quality premium?
As specified in docs/q23_korea_wide_quality_spec.md.

  C1 (decisive)  chip spread ~ index + size + momentum + KOR-QMJ-ex-chip
  C2             same, with KOR-QMJ including chip names
  C3             chip spread ~ KOR-QMJ-ex-chip alone
  C4             correlation, and the market-wide factor's own mean and t over the same months
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q10_strategy_backtest as bt  # noqa: E402
from q8_multifactor import nw_stats, quintile_returns  # noqa: E402
from q18_short_ban import controls_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
RESULTS = ROOT / "results"
WINDOWS = {"frozen finding 2023-01 → 2026-08": ("2023-01-01", "2026-08-31"),
           "extended 2016-12 → 2026-08": ("2016-12-01", "2026-08-31")}


def to_month(s: pd.Series) -> pd.Series:
    """Index a monthly series by calendar month so month-start and month-end labels line up."""
    out = s.copy()
    out.index = pd.PeriodIndex(pd.to_datetime(out.index), freq="M")
    return out[~out.index.duplicated()]


def regress(y: pd.Series, X: pd.DataFrame) -> dict:
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    if len(d) < 12:
        return {"months": len(d)}
    m = sm.OLS(d["y"], sm.add_constant(d.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    out = {"months": len(d), "alpha_bp": 1e4 * m.params["const"], "alpha_t": m.tvalues["const"], "r2": m.rsquared}
    for c in d.columns:
        if c != "y":
            out[f"beta_{c}"] = m.params[c]
            out[f"t_{c}"] = m.tvalues[c]
    return out


def main() -> None:
    f = pd.read_csv(INTERIM / "kr_wide_quality_factor.csv", index_col=0)
    kor_qmj = to_month(f["kor_qmj"])
    kor_ex = to_month(f["kor_qmj_ex_chip"])

    sig, px, ret, mcap, index_close = bt.korea()
    spread = to_month(quintile_returns(sig, ret)["ls"])
    ctrl = controls_for(px, ret, mcap, index_close)
    ctrl.index = pd.PeriodIndex(pd.to_datetime(ctrl.index), freq="M")
    ctrl = ctrl[~ctrl.index.duplicated()]

    rows, extra = [], []
    for label, (a, b) in WINDOWS.items():
        per = pd.period_range(a, b, freq="M")
        y = spread.reindex(per).dropna()
        if len(y) < 12:
            continue
        base = ctrl.reindex(y.index)
        x_ex = kor_ex.reindex(y.index).rename("kor_qmj_ex_chip")
        x_all = kor_qmj.reindex(y.index).rename("kor_qmj")
        rows.append({"window": label, "test": "C1 controls + KOR-QMJ-ex-chip",
                     **regress(y, base.join(x_ex))})
        rows.append({"window": label, "test": "C2 controls + KOR-QMJ (incl. chip)",
                     **regress(y, base.join(x_all))})
        rows.append({"window": label, "test": "C3 KOR-QMJ-ex-chip alone",
                     **regress(y, x_ex.to_frame())})
        rows.append({"window": label, "test": "C0 controls only (reference)", **regress(y, base)})
        st_q, st_e = nw_stats(x_all.dropna()), nw_stats(x_ex.dropna())
        extra.append({"window": label, "months": len(y),
                      "corr(chip spread, KOR-QMJ-ex-chip)": float(y.corr(x_ex)),
                      "KOR-QMJ mean_bp": st_q["mean_bp"], "KOR-QMJ t": st_q["t"],
                      "KOR-QMJ-ex-chip mean_bp": st_e["mean_bp"], "KOR-QMJ-ex-chip t": st_e["t"],
                      "chip spread mean_bp": nw_stats(y)["mean_bp"], "chip spread t": nw_stats(y)["t"]})

    res = pd.DataFrame(rows)
    c1 = res[(res["test"].str.startswith("C1")) & (res["window"].str.startswith("frozen"))]
    verdict = ("distinct from the market-wide premium" if len(c1) and c1.iloc[0]["alpha_t"] > 2
               else "NOT separable from the market-wide premium in this sample")

    keep = [c for c in ["window", "test", "months", "alpha_bp", "alpha_t", "r2",
                        "beta_kor_qmj_ex_chip", "t_kor_qmj_ex_chip", "beta_kor_qmj", "t_kor_qmj",
                        "beta_index", "beta_momentum", "beta_size_small_minus_big"] if c in res.columns]

    def fmt(df):
        return "```\n" + df.to_string(index=False, float_format=lambda v: f"{v:.2f}") + "\n```"

    L = ["# Q23 — Is the chip-sector effect distinct from a market-wide Korean quality premium?", "",
         "Follows `docs/q23_korea_wide_quality_spec.md` (committed before the data were built).",
         "KOR-QMJ is built here from every KOSPI/KOSDAQ company in the DART register (median 1,807 companies a month,",
         "2016-12 → 2026-08), because AQR's country files and Ken French's international library do not cover Korea.",
         "The decisive control, KOR-QMJ-ex-chip, excludes the 285 companies of the chip universe.", "",
         "## Regressions", "", fmt(res[keep]), "",
         f"**C1 verdict: the chip-sector effect is {verdict}.**", "",
         "## The market-wide factor itself", "", fmt(pd.DataFrame(extra)), ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q23_korea_wide_quality.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
