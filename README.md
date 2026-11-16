# Housing Loan Approval Prediction Using Machine Learning Algorithms

## Build an Explainable Loan Screening Assistant

**LoanLens** is an intermediate college major project that compares five machine-learning algorithms, explains their predictions with SHAP, and provides a Streamlit application for single and batch screening.

It learns **historical approval decisions**, not repayment or default outcomes. The goal is to support a human reviewer's shortlist. This dataset cannot validate reduced non-performing assets, real bank savings, or production lending suitability.

## Start the existing local project

Run these commands in Windows PowerShell:

```powershell
Set-Location 'D:\Koding\Housing Loan Approval Prediction'
.\.venv\Scripts\python.exe -m streamlit run app/app.py --server.headless true --server.address 127.0.0.1
```

Open the local URL printed by Streamlit. The application contains **Single application**, **Batch screening**, and **Model evidence** tabs. All application data are processed in memory; the app does not save uploads.

## Setup on a fresh machine

The project was built with **Python 3.12.13**. Use Python 3.12 for the frozen dependency set. The requested Python 3.10+ requirement is met by this interpreter; older interpreters were not separately verified.

With the installed `uv` tool:

```powershell
Set-Location 'D:\Koding\Housing Loan Approval Prediction'
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-lock.txt
```

Or, with the Windows Python launcher and standard `venv`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Use one setup method. Activating the environment is optional because commands below explicitly use its interpreter. `requirements.txt` describes direct dependency ranges; `requirements-lock.txt` freezes the packages actually installed for this run.

## Reproduce the complete experiment

```powershell
.\.venv\Scripts\python.exe -m src.run_pipeline
.\.venv\Scripts\python.exe -m pytest -q
```

The runner verifies/downloads the authentic raw CSV, regenerates dataset reports and training-only EDA, fits all model candidates, evaluates the selected model, calculates SHAP, and executes the EDA notebook. Training starts again from raw rows; saved transformed arrays are not reused for fitting.

After a successful run, compare an independent complete rerun with its existing results:

```powershell
.\.venv\Scripts\python.exe -m src.run_pipeline --verify-reproduction
```

Raw CSV bytes are never overwritten. An existing download must match `data/raw/source.json`. The raw data are excluded from Git because redistribution rights were not independently established; the downloader retrieves them from the recorded public organizer URL.

Individual phases can also be run:

```powershell
.\.venv\Scripts\python.exe -m src.download_data
.\.venv\Scripts\python.exe -m src.dataset_report
.\.venv\Scripts\python.exe -m src.eda
.\.venv\Scripts\python.exe -m src.train
.\.venv\Scripts\python.exe -m src.evaluate
.\.venv\Scripts\python.exe -m src.explain
```

The EDA command regenerates a clean executable notebook. Use the full runner to regenerate and execute it together. To explore it interactively:

```powershell
.\.venv\Scripts\python.exe -m jupyter notebook notebooks/01_eda.ipynb
```

## Dataset and leakage prevention

The [Dream Housing Finance organizer CSV](https://datahack-prod.s3.ap-south-1.amazonaws.com/train_file/train_u6lujuX_CVtuZ9i.csv) contains **614 applications and 13 columns**, with **149 missing cells**. The target is `Loan_Status` (`Y` = approved; `N` = rejected). See [the dataset audit](docs/02_dataset.md) for the exact source, checksum, dictionary, types, missingness and balance.

A stratified 80/20 split with seed 42 creates **491 training rows** and **123 holdout rows** before any fitted preprocessing. Five-fold stratified CV fits the entire imputation, engineering, scaling, encoding and optional SMOTENC chain inside each fold. Target-informed EDA uses training rows only.

Loan_ID is dropped. Gender and Married are excluded from predictors but retained for descriptive group audits. This prevents direct use of those fields; it does not prove fairness or remove demographic proxies.

## Actual results

The selected model is a **class-weighted Decision Tree**, `max_depth=2`, `min_samples_leaf=5`. It ranked first on training CV approval-class F1: **0.869626 ± 0.027836**. Selection used CV, not holdout scores. The search compared the requested Logistic Regression, Decision Tree, Random Forest, XGBoost and LightGBM algorithms under class weighting and SMOTENC.

On the reserved 123 applications:

| Policy | Accuracy | Precision | Recall | F1 | ROC-AUC | False approvals | False rejections | Illustrative cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Majority always-approve baseline | 0.691057 | 0.691057 | 1.000000 | 0.817308 | 0.500000 | 38 | 0 | 190 |
| Standard threshold 0.50 | 0.886179 | 0.881720 | 0.964706 | 0.921348 | 0.841950 | 11 | 3 | 58 |
| Training cost experiment, threshold 0.76 | 0.308943 | 0.000000 | 0.000000 | 0.000000 | 0.841950 | 0 | 85 | 85 |

Approval is the positive class. ROC-AUC uses scores and therefore is unchanged when only the threshold changes. Zero precision for an all-reject policy uses the documented `zero_division=0` reporting convention.

**The cost-threshold experiment failed as a useful screening policy.** Under an assumed cost of five units for a false approval and one for a false rejection, training OOF tuning selected 0.76. The final fitted tree's maximum leaf approval score is only **0.6394436519258202**, so 0.76 rejects every possible application. The holdout cost is also worse than at 0.5. The app therefore defaults to the conventional **0.50** threshold and exposes the failed cost policy as a clearly labeled experiment. The experimental result is retained rather than retuned on test labels. Neither policy is validated for real lending.

See [model development](docs/05_modeling.md), [evaluation](docs/06_evaluation.md), and `reports/model_comparison.csv` for the objective, search limitations, class-specific errors and subgroup audit. Scores are model estimates, not independently calibrated probabilities of bank approval or repayment.

## Explainability and inputs

SHAP uses **30 real training background rows** and **60 training summary rows**. The observed maximum probability reconstruction error was **1.1102230246251565e-16**. Global and single-app plots are saved in `reports/figures/`; the app shows a waterfall and three plain-English model associations. See [explainability notes](docs/07_explainability.md).

Income is interpreted as monthly dataset units; the currency was not independently documented. LoanAmount is in **thousands** of those units and term is in **months**. EMI is an engineered illustration using a fixed assumed annual rate of **9%**, not a bank quote. Missing model fields use training-only medians or modes. Entirely blank applications and invalid values are rejected.

Batch CSVs must have the input column names shown by the downloadable blank template. The app accepts at most **1,000 applications and 5 MB** per upload, validates through the shared prediction function, and offers a formula-safe result download. A supplied `Loan_Status` is not a predictor.

## Project map

| Path | Purpose |
| --- | --- |
| `data/raw/` | Immutable local CSV and its source/checksum record |
| `data/processed/` | Split manifest and real training OOF probabilities |
| `src/` | Download, reporting, preprocessing, training, evaluation, prediction, SHAP and runner modules |
| `notebooks/01_eda.ipynb` | Executable training-only EDA with generated insights |
| `models/` | Trusted fitted pipeline artifact and readable metadata |
| `app/app.py` | Streamlit single/batch/evidence interface |
| `reports/` | Code-generated metrics, comparisons, audits, errors and figures |
| `tests/` | Data integrity, preprocessing, CV boundaries, prediction, evaluation, SHAP and app checks |
| `docs/` | Research, assumptions, phase notes, progress, viva notes and morning summary |

Start with [MORNING_SUMMARY.md](docs/MORNING_SUMMARY.md), [STATUS_UPDATE.md](docs/STATUS_UPDATE.md), and [VIVA_NOTES.md](docs/VIVA_NOTES.md). [PROGRESS.md](docs/PROGRESS.md) records phase verification and commits; [BLOCKERS.md](docs/BLOCKERS.md) records failures and recoveries. [Research notes](docs/00_research.md) contain inspected GitHub references and UI sources; no third-party application code was copied.

Final test, server and reproduction evidence should be read from the morning summary. A trained local app is not a cloud deployment, a fairness certification, or a production lending system.

Optional live browser verification uses a separate Playwright tool environment, not an app dependency:

```powershell
uv tool run --from playwright playwright install chromium
uv tool run --from playwright python tests/browser_live.py
```

It checks a real held-out applicant against saved scores, SHAP, CSV upload, evidence, and desktop/mobile layouts. Evidence is in `reports/browser_check.json` and `reports/figures/app_*.png`.
