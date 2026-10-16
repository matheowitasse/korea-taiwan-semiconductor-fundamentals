"""Q17: EXPLORATORY scan for anything exploitable, with the AI-era / new-regime split in mind.

**This is not a test.** It scans a grid of signals x assets x conditions and reports what looks strongest.
Nothing here can be claimed: by construction, scanning produces apparent hits. Anything interesting becomes a
hypothesis to pre-register and confirm on data after 2026-09-16.

Discipline used instead of a pass rule:
  - the statistic is computed in three periods: PRE (2016 → 2022), AI (2023-01 → 2025-06), NEW (2025-07 → 2026-09-16);
  - a candidate must be strong in NEW (|t| >= 2) AND have the same sign in AI AND in PRE;
  - the number of candidates is compared with the number expected by chance (reported);
  - the shortlist gets a 5,000-draw circular-shift placebo and an economic size vs a 0.30% round-trip cost.

Usage: python src/q17_exploratory_scan.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from krx_manual_import import read_krx  # noqa: E402
from q3_edge_search import load_full  # noqa: E402
from q4_supplier_rebound import MARKETS, us_signal  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"
KRX_START = pd.Timestamp("2023-01-02")
PERIODS = {"PRE": ("2016-01-01", "2022-12-31"), "AI": ("2023-01-01", "2025-06-30"), "NEW": ("2025-07-01", "2026-09-16")}
N_DRAWS = 5000
MIN_SHIFT = 20
COST_BP = 30
MIN_N = 40

SUP = MARKETS["KR"]["suppliers"]


def clean(ticker: str, cal: pd.DatetimeIndex) -> pd.DataFrame:
    df = load_full(ticker)
    flat = (df["Open"] == df["High"]) & (df["High"] == df["Low"]) & (df["Low"] == df["Close"])
    no_vol = (df["Volume"] == 0) if not ticker.startswith("^") and "=" not in ticker else False
    return df.mask(flat | no_vol | (df["Open"] <= 0)).reindex(cal)


def basket(tickers: list[str], cal, field) -> pd.Series:
    return pd.concat([field(clean(t, cal)) for t in tickers], axis=1).mean(axis=1)


def flow_z(code: str, cal: pd.DatetimeIndex, group: str) -> pd.Series:
    nav = pd.read_parquet(RAW / "naver_flows" / f"{code}.parquet")
    krx = pd.concat([read_krx(p) for p in sorted((RAW / "krx_manual").glob(f"{code}_*.csv"))])
    krx = krx[~krx.index.duplicated()].sort_index()
    cols = {"foreign": ["Foreigners", "Other foreigners"], "individual": ["Individuals"]}[group]
    navcol = {"foreign": "foreign_net_shares", "individual": "individual_net_shares"}[group]
    traded = (nav["close"] * nav["volume"]).where(nav["volume"] > 0)
    ratio = pd.concat([(nav[navcol] / nav["volume"].where(nav["volume"] > 0))[lambda s: s.index < KRX_START],
                       (krx[cols].sum(axis=1) / traded.reindex(krx.index))[lambda s: s.index >= KRX_START]])
    ratio = ratio.clip(-1, 1).reindex(cal)
    past = ratio.shift(1).rolling(60, min_periods=40)
    return (ratio - past.mean()) / past.std()


def build() -> pd.DataFrame:
    cal = load_full("^KS11").index
    cal = cal[cal >= "2016-01-01"]
    oc = lambda d: d["Close"] / d["Open"] - 1          # noqa: E731
    cc = lambda d: d["Close"] / d["Close"].shift(1) - 1  # noqa: E731
    gap = lambda d: d["Open"] / d["Close"].shift(1) - 1  # noqa: E731
    sig = us_signal(cal, load_full("SOXX")).reindex(cal)
    d = pd.DataFrame(index=cal)
    d["signal"] = sig

    assets = {"Samsung": ["005930.KS"], "Hynix": ["000660.KS"], "Suppliers": SUP, "KOSPI": ["^KS11"], "KOSDAQ": ["^KQ11"]}
    for name, tk in assets.items():
        d[f"oc_{name}"] = basket(tk, cal, oc)
        d[f"cc_{name}"] = basket(tk, cal, cc)
        d[f"gap_{name}"] = basket(tk, cal, gap)
        c = basket(tk, cal, lambda x: x["Close"])
        d[f"fwd5_{name}"] = c.shift(-5) / basket(tk, cal, lambda x: x["Open"]).shift(-1) - 1
        # LOOK-AHEAD FIX (2026-09-18): past returns must end at the PREVIOUS close, never the close being predicted
        d[f"past5_{name}"] = c.shift(1) / c.shift(6) - 1
        d[f"past20_{name}"] = c.shift(1) / c.shift(21) - 1
        # overshoot: how much more the open moved than its recent relationship with the US night implies
        beta = sig.rolling(60, min_periods=40).cov(d[f"gap_{name}"]) / sig.rolling(60, min_periods=40).var()
        d[f"overshoot_{name}"] = d[f"gap_{name}"] - beta.shift(1) * sig
        d[f"vol20_{name}"] = d[f"cc_{name}"].rolling(20).std()

    krw = clean("KRW=X", cal)
    d["krw_overnight"] = (krw["Open"] / krw["Close"].shift(1) - 1)
    d["krw_prev"] = krw["Close"].pct_change().shift(1)
    for code, name in (("005930", "Samsung"), ("000660", "Hynix")):
        d[f"foreign_z_{name}"] = flow_z(code, cal, "foreign").shift(1)      # yesterday's flow, known before the open
        d[f"indiv_z_{name}"] = flow_z(code, cal, "individual").shift(1)
    d["spread5"] = d["past5_Hynix"] - d["past5_Samsung"]
    return d


def tstat(y: np.ndarray, x: np.ndarray) -> tuple[float, float, float]:
    fit = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    return fit.params[1], fit.tvalues[1], fit.pvalues[1]


def grid(d: pd.DataFrame) -> list[dict]:
    assets = ["Samsung", "Hynix", "Suppliers", "KOSPI", "KOSDAQ"]
    rows = []
    for a in assets:
        signals = {"US night": "signal", "overshoot": f"overshoot_{a}", "prev day o→c": None,
                   "past 5d": f"past5_{a}", "past 20d": f"past20_{a}", "KRW overnight": "krw_overnight",
                   "KRW prev day": "krw_prev", "Hynix−Samsung 5d": "spread5"}
        if a in ("Samsung", "Hynix"):
            signals["foreign flow z (t−1)"] = f"foreign_z_{a}"
            signals["retail flow z (t−1)"] = f"indiv_z_{a}"
        for sname, scol in signals.items():
            x = d[f"oc_{a}"].shift(1) if scol is None else d[scol]
            for yname, ycol in (("same-day o→c", f"oc_{a}"), ("next 5 days", f"fwd5_{a}")):
                for cname, mask in (("all days", pd.Series(True, index=d.index)),
                                    ("high vol", d[f"vol20_{a}"] > d[f"vol20_{a}"].rolling(250, min_periods=100).quantile(0.67)),
                                    ("US night < −1%", d["signal"] < -0.01)):
                    rows.append({"asset": a, "signal": sname, "outcome": yname, "condition": cname,
                                 "x": x, "y": d[ycol], "mask": mask})
    return rows


def evaluate(rows: list[dict]) -> pd.DataFrame:
    out = []
    for r in rows:
        rec = {k: r[k] for k in ("asset", "signal", "outcome", "condition")}
        ok = True
        for p, (a, b) in PERIODS.items():
            frame = pd.DataFrame({"x": r["x"], "y": r["y"]})[r["mask"].fillna(False)]
            frame = frame[(frame.index >= a) & (frame.index <= b)].dropna()
            if len(frame) < MIN_N:
                ok = False
                break
            beta, t, _ = tstat(frame["y"].values, frame["x"].values)
            rec[f"n_{p}"], rec[f"beta_{p}"], rec[f"t_{p}"] = len(frame), beta, t
        if ok:
            out.append(rec)
    return pd.DataFrame(out)


def placebo(r: pd.Series, rows: list[dict], rng) -> float:
    src = next(x for x in rows if all(x[k] == r[k] for k in ("asset", "signal", "outcome", "condition")))
    frame = pd.DataFrame({"x": src["x"], "y": src["y"]})[src["mask"].fillna(False)]
    frame = frame[(frame.index >= PERIODS["NEW"][0]) & (frame.index <= PERIODS["NEW"][1])].dropna()
    y, x = frame["y"].values, frame["x"].values
    obs = abs(tstat(y, x)[1])
    draws = np.array([abs(tstat(y, np.roll(x, rng.integers(MIN_SHIFT, len(x) - MIN_SHIFT)))[1]) for _ in range(N_DRAWS)])
    return float((draws >= obs).mean())


def main() -> None:
    d = build()
    rows = grid(d)
    res = evaluate(rows)
    same_sign = (np.sign(res["beta_NEW"]) == np.sign(res["beta_AI"])) & (np.sign(res["beta_NEW"]) == np.sign(res["beta_PRE"]))
    strong = res["t_NEW"].abs() >= 2
    cand = res[strong & same_sign].copy()
    # how many would pass by chance: P(|t|>=2) ~ 0.045 x P(both signs agree | sign random) = 0.25
    expected = len(res) * 0.045 * 0.25

    rng = np.random.default_rng(42)
    if len(cand):
        cand["placebo_p_NEW"] = [placebo(r, rows, rng) for _, r in cand.iterrows()]
        cand["quintile_size_bp"] = np.nan
        cand = cand.sort_values("placebo_p_NEW")

    L = ["# Q17 — EXPLORATORY scan (not a test)", "",
         "Scans signals x assets x conditions in three periods. **Nothing here is a claim**: scanning produces apparent",
         "hits by construction. Candidates are hypotheses to pre-register and confirm on data after 2026-09-16.", "",
         f"Grid: {len(res)} signal/asset/outcome/condition combinations with enough data in all three periods.",
         f"Filter: |t| ≥ 2 in NEW (2025-07 → 2026-09-16) **and** same sign in AI (2023 → 2025H1) **and** in PRE (2016 → 2022).",
         f"**Candidates found: {len(cand)}. Expected by chance under no effect: ≈ {expected:.1f}.**", ""]
    if len(cand):
        cols = ["asset", "signal", "outcome", "condition", "n_NEW", "beta_NEW", "t_NEW", "placebo_p_NEW",
                "beta_AI", "t_AI", "beta_PRE", "t_PRE"]
        L += ["## Candidates (sorted by placebo p in the new regime)", "",
              "```", cand[cols].to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", ""]
    # regime-specific view: strong in NEW, no sign agreement required (the author's point: the AI boom is another regime)
    new_only = res[strong].reindex(res[strong]["t_NEW"].abs().sort_values(ascending=False).index).head(15).copy()
    if len(new_only):
        new_only["placebo_p_NEW"] = [placebo(r, rows, rng) for _, r in new_only.iterrows()]
    L += ["## Strongest in the new regime, sign agreement NOT required (regime-specific view)", "",
          f"{int(strong.sum())} of {len(res)} combinations reach |t| ≥ 2 in NEW; ≈ {len(res) * 0.045:.0f} expected by chance.", "",
          "```", new_only.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", ""]

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q17_exploratory_scan.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
