"""Q12: Japan with five years of history — exactly as pre-registered in docs/q12_japan_extended_preregistration.md.

Decisive: the composite long-short spread over 2021-10 → 2024-06 (never seen; includes the 2022-23 memory downturn).
The 2024-07 → 2026-06 window was already used in Q9 and is reported separately, never as confirmation.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import q9_japan_test as jp
from q8_multifactor import quintile_returns

ROOT = Path(__file__).resolve().parents[1]
RAW, RESULTS = ROOT / "data" / "raw", ROOT / "results"
WINDOWS = {"decisive (unseen) 2021-10 → 2024-06": ("2021-10-01", "2024-06-30"),
           "already seen in Q9: 2024-07 → 2026-06": ("2024-07-01", "2026-06-30"),
           "full sample (mixed)": ("2021-10-01", "2026-09-30")}
MIN_STOCKS = 30


def main() -> None:
    rng = np.random.default_rng(12)
    master = pd.read_csv(RAW / "jquants" / "master.csv", dtype={"Code": str})
    uni = set(master.loc[master["S33Nm"].isin(jp.SECTORS), "Code"])
    fins = pd.read_csv(RAW / "jquants" / "fins_summary.csv", dtype={"Code": str})
    cal = pd.read_parquet(RAW / "full_IDX_N225.parquet").index
    px, ret = jp.monthly(RAW / "q9_jp_prices", cal)
    factors = jp.build(jp.quarterly_profits(fins[fins["Code"].isin(uni)]), px)

    rows = []
    for wname, (a, b) in WINDOWS.items():
        for k in ["composite", "quality", "earn_mom", "value"]:
            f = factors[k]
            use = f.index[(f.notna().sum(axis=1) >= MIN_STOCKS) & (f.index >= a) & (f.index <= b)]
            if len(use) < 6:
                rows.append({"window": wname, "factor": k, "months": len(use)})
                continue
            st = jp.one_sided(f.loc[use], ret, rng)
            rows.append({"window": wname, "factor": k, "months": st["months_used"], "mean_bp": st["mean_bp"],
                         "t": st["t"], "p_one_sided": st["p"], "placebo_p": st["placebo_p"],
                         "long_only_bp": st["long_only_bp"],
                         "span": f"{use.min():%Y-%m} → {use.max():%Y-%m}"})
    df = pd.DataFrame(rows)

    # risk adjustment on the unseen window only
    a, b = WINDOWS["decisive (unseen) 2021-10 → 2024-06"]
    f = factors["composite"]
    use = f.index[(f.notna().sum(axis=1) >= MIN_STOCKS) & (f.index >= a) & (f.index <= b)]
    ls = quintile_returns(f.loc[use], ret.reindex(use))["ls"]
    mom = quintile_returns((px.shift(1) / px.shift(12) - 1).reindex(use), ret.reindex(use))["ls"]
    idx = pd.read_parquet(RAW / "full_IDX_N225.parquet")["Close"].resample("ME").last()
    idx = (idx.shift(-1) / idx - 1)
    idx.index = [min([d for d in px.index if d.to_period("M") == p.to_period("M")], default=pd.NaT) for p in idx.index]
    idx = idx[idx.index.notna()]
    d = pd.concat([ls.rename("ls"), idx.reindex(ls.index).rename("index"), mom.reindex(ls.index).rename("momentum")],
                  axis=1).dropna()
    adj = {}
    if len(d) > 10:
        m = sm.OLS(d["ls"], sm.add_constant(d.drop(columns="ls"))).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        adj = {"months": len(d), "alpha_bp": 1e4 * m.params["const"], "alpha_t": m.tvalues["const"],
               "alpha_p_one_sided": float(stats.norm.sf(m.tvalues["const"])),
               "beta_index": m.params["index"], "beta_momentum": m.params["momentum"], "r2": m.rsquared}

    dec = df[(df["window"].str.startswith("decisive")) & (df["factor"] == "composite")].iloc[0]
    confirmed = bool(dec.get("t", 0) > 2 and dec.get("placebo_p", 1) < 0.05)

    L = ["# Q12 — Japan with five years of history", "",
         "Follows `docs/q12_japan_extended_preregistration.md` (committed before the data was downloaded).", "",
         f"Financials 2021-09-21 → 2026-09-18, 276 companies, median 23 statements each.", "",
         "## All windows (only the first is decisive)", "",
         "```", df.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", "",
         f"**Decisive test — composite, unseen window: {'CONFIRMED' if confirmed else 'NOT CONFIRMED'}** "
         f"(mean {dec.get('mean_bp', float('nan')):.0f} bp/month, t {dec.get('t', float('nan')):.2f}, "
         f"placebo p {dec.get('placebo_p', float('nan')):.3f}, {int(dec.get('months', 0))} months)", "",
         "## Risk adjustment on the unseen window (index + momentum spread, HAC 3 lags)", "",
         "```", pd.Series(adj).to_string(float_format=lambda v: f"{v:.3f}") if adj else "not enough months", "```", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q12_japan_extended.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
