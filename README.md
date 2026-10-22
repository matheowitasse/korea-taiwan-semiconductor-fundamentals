# Strong and Improving Fundamentals Predict Returns

Replication package for *Strong and Improving Fundamentals Predict Returns: Pre-Registered Evidence from Korean and
Taiwanese Semiconductor Stocks, 2016–2026* (Matheo Witasse, working paper, 2026).

The paper is `paper/Witasse_Korea_Taiwan_semiconductors.pdf`; its only source is `paper/latex/main.tex`.

## How the project was run

Every study is numbered (Q1–Q29). For each one:

1. the hypothesis, definitions and pass/fail rules were written in `docs/qNN_*` and committed **before** any code for
   that study existed;
2. the script in `src/qNN_*.py` was then written and run once;
3. its output was saved to `results/qNN_*.md`, whether the test passed or failed.

`docs/commit_history.txt` gives the date and order of every pre-registration, script and result. The decisive results
were frozen at tag `finding-v1`; later studies are robustness, implementation or diagnostics and do not re-tune them.
Appendix B of the paper lists every study and its outcome.

## Reproducing the paper

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

The headline results come from these scripts, in this order:

| Step | Script | Produces |
|---|---|---|
| Korean universe and fundamentals | `q7_dart_companies.py`, `q8_dart_financials.py`, `q7_dart_operating_profit.py` | `data/interim/` |
| Korean discovery and validation | `q8_multifactor.py` | `results/q8_multifactor.md` |
| Taiwan and Japan | `q9_taiwan_download.py`, `q9_taiwan_test.py`, `q9_japan_test.py`, `q12_japan_extended.py` | `results/q9_*`, `results/q12_*` |
| Risk adjustment, legs | `q10_risk_adjustment.py`, `q13_leg_decomposition.py` | `results/q10_*`, `results/q13_*` |
| Pre-AI extensions | `q22_extended_history.py`, `q27_taiwan_pre_ai.py`, `q27b_taiwan_pit.py` | `results/q22_*`, `results/q27*` |
| Robustness | `q21_*.py`, `q23_*.py`, `q29_referee_robustness.py` | `results/q21_*`, `q23_*`, `q29_*` |
| Implementation | `q24_*.py`, `q25_*.py`, `q26_transaction_costs.py`, `q26b_borrow_bound.py` | `results/q24_*` – `q26b_*` |
| Figures and paper | `make_figures.py`, `build_paper.py` | `paper/` |

`python src/build_paper.py` needs a LaTeX installation (pdfLaTeX and BibTeX).

## Data

| Source | Used for | In this package |
|---|---|---|
| DART OpenAPI (Korea) | quarterly financial statements, company list | downloaded by the scripts; needs a free API key in `DART_API_KEY` |
| Yahoo Finance | daily prices | downloaded by the scripts |
| TWSE, TPEx, MOPS (Taiwan) | prices, valuation ratios, monthly revenue | downloaded by the scripts; no key needed |
| KRX Data Marketplace (Korea) | delisted-company prices, market-cap snapshots, short interest | **not included** — KRX terms do not allow redistribution; files must be downloaded by hand and imported with `src/krx_manual_import.py` and related scripts |
| J-Quants (Japan) | statements and prices | **not included** — subscription data; needs your own key in `JQUANTS_TOKEN` |
| Korea Customs Service | export releases (short-horizon studies) | downloaded by `src/q1_download_kcs_releases.py` |


