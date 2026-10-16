"""Q27b (robustness, pre-registered in docs/q27_taiwan_pre_ai_preregistration.md section 3):
the Taiwanese test on a point-in-time universe that includes companies which have since delisted.

Universe in month t = the chip companies (半導體業 / 電子零組件業) listed in that month's revenue file.
Prices = exchange month-end closes, NOT adjusted for dividends (the trade-off of this version).
A company that disappears from the price file is delisted: the main version drops that final month (unobservable),
a sensitivity assigns it −50%.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from q8_multifactor import nw_stats, quintile_returns

ROOT = Path(__file__).resolve().parents[1]
PIT, RESULTS = ROOT / "data" / "raw" / "taiwan_pit", ROOT / "results"
DECISIVE, SEEN, FULL = ("2016-01-01", "2022-12-31"), ("2023-01-01", "2026-08-31"), ("2016-01-01", "2026-08-31")
MIN_STOCKS, N_PERM, DELIST_RETURN = 30, 500, -0.50


def load_prices() -> pd.DataFrame:
    frames = []
    for p in sorted(PIT.glob("prices_*.csv")):
        d = pd.read_csv(p, dtype={"code": str})
        d["date"] = pd.Timestamp(p.stem.split("_")[1] + "01")  # placeholder; real date is in the file
        frames.append(pd.read_csv(p, dtype={"code": str}))
    px = pd.concat(frames, ignore_index=True)
    px["date"] = pd.to_datetime(px["date"])
    return px.pivot_table(index="date", columns="code", values="close", aggfunc="last").sort_index()


def load_universe() -> pd.DataFrame:
    frames = [pd.read_csv(p, dtype={"code": str}) for p in sorted(PIT.glob("universe_*.csv"))]
    u = pd.concat(frames, ignore_index=True)
    u["period"] = pd.PeriodIndex.from_fields(year=u["year"], month=u["month"], freq="M")
    u["yoy"] = np.where(u["revenue_year_ago"] > 0, 100 * (u["revenue_current"] / u["revenue_year_ago"] - 1), np.nan)
    return u.dropna(subset=["yoy"])


def build(px: pd.DataFrame, uni: pd.DataFrame, delist: bool) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Signal and next-month return, both restricted to the universe of that month."""
    months = px.index
    sig = pd.DataFrame(index=months, columns=px.columns, dtype=float)
    ret = pd.DataFrame(index=months, columns=px.columns, dtype=float)
    gone = {}
    for i, t in enumerate(months[:-1]):
        published = (t.to_period("M") - 1)                      # revenue for the previous month is public by the 10th
        d = uni[uni["period"] == published].drop_duplicates("code").set_index("code")["yoy"]
        live = [c for c in d.index if c in px.columns and np.isfinite(px.at[t, c])]
        sig.loc[t, live] = d[live].values
        nxt = px.iloc[i + 1]
        r = nxt[live] / px.loc[t, live] - 1
        missing = [c for c in live if not np.isfinite(nxt.get(c, np.nan))]
        gone[t] = len(missing)
        if delist:
            r[missing] = DELIST_RETURN
        ret.loc[t, live] = r.values
    return sig, ret, pd.Series(gone)


def window(f: pd.DataFrame, period) -> pd.DatetimeIndex:
    idx = f.index[f.notna().sum(axis=1) >= MIN_STOCKS]
    return idx[(idx >= period[0]) & (idx <= period[1])]


def test(sig: pd.DataFrame, ret: pd.DataFrame, rng) -> dict:
    port = quintile_returns(sig, ret.reindex(sig.index))
    st = nw_stats(port["ls"])
    st["p_one_sided"] = float(stats.norm.sf(st["t"])) if np.isfinite(st["t"]) else np.nan
    draws = []
    for _ in range(N_PERM):
        sh = sig.apply(lambda row: pd.Series(rng.permutation(row.values), index=row.index), axis=1)
        draws.append(quintile_returns(sh, ret.reindex(sh.index))["ls"].mean())
    st["placebo_p"] = float((np.array(draws) >= port["ls"].mean()).mean())
    st["long_only_bp"] = nw_stats(port["long_only"])["mean_bp"]
    st["median_names"] = int(sig.notna().sum(axis=1).median())
    return st


def main() -> None:
    rng = np.random.default_rng(272)
    px, uni = load_prices(), load_universe()
    import q9_taiwan_test as tw_current
    current = set(tw_current.universe()["code"])  # today's Taiwanese lists
    all_codes = set(uni["code"])
    print(f"price months {len(px)} | universe files cover {uni['period'].nunique()} months | "
          f"distinct chip codes ever listed {len(all_codes)}")

    rows = []
    for delist in (False, True):
        sig, ret, gone = build(px, uni, delist)
        for name, period in [("DECISIVE 2016-01 → 2022-12", DECISIVE), ("already seen 2023-01 → 2026-08", SEEN),
                             ("full sample", FULL)]:
            use = window(sig, period)
            if len(use) < 6:
                continue
            st = test(sig.loc[use], ret, rng)
            rows.append({"delisted_marked_-50%": delist, "window": name, "months": st["months"],
                         "mean_bp": st["mean_bp"], "t": st["t"], "p_one_sided": st["p_one_sided"],
                         "placebo_p": st["placebo_p"], "long_only_bp": st["long_only_bp"],
                         "median_names": st["median_names"],
                         "disappearing_names_per_month": round(gone.reindex(use).mean(), 2)})
    df = pd.DataFrame(rows)

    never_listed_now = len(all_codes - current)
    L = ["# Q27b — Taiwan with a point-in-time universe (delisted companies included)", "",
         "Robustness version pre-registered in `docs/q27_taiwan_pre_ai_preregistration.md` (section 3). The universe in",
         "each month is the chip companies listed in that month's revenue file; prices are exchange month-end closes,",
         "**unadjusted for dividends**, which biases returns downward for high-yielding stocks.", "",
         f"Chip codes in the archive: **{len(all_codes)}**; of those, **{never_listed_now}** are absent from today's "
         f"lists, so Taiwan's chip sector is almost survivorship-free over this period.", "",
         "```", df.to_string(index=False, float_format=lambda v: f"{v:.3f}"), "```", "",
         "The two panels bracket the treatment of a company's final month: dropped (unobservable) or marked at −50%.", ""]
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "q27b_taiwan_pit.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
