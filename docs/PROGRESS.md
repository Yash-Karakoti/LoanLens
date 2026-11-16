# Progress log

## Phase 0 — setup started

- New isolated project repository; existing projects are outside the edit scope.
- Python 3.12 virtual environment created. Dependency installation and verification pending.
- User explicitly authorized implementation, phase commits and independent agents; no questions required.

## Phase 0 — verified
- Python 3.12.13 venv; 137 packages installed. uv pip check reports compatible dependencies. Frozen exact versions in requirements-lock.txt.
- Authentic download succeeded; initial preprocessing checks: 10 passed (later phases will expand tests).
- Setup-only commit excludes unfinished application code and external raw CSV.


## Phase 1 — problem and research verified
- Defined historical approval as the positive class, precision/recall/F1/ROC-AUC, asymmetric illustrative review cost, and human-review scope.
- Reviewed comparable source code and primary references; documented leakage findings and UI references in docs/00_research.md.
- Verified docs avoid claims of measured default reduction or production readiness.


## Phase 2 — dataset verified
- Organizer CSV downloaded: 614 rows, 13 columns, SHA-256 recorded. Raw file excluded from Git because redistribution rights are unverified.
- Code-generated dictionary, dtypes, 149 missing cells, class balance and disjoint 491/123 split recorded.
- Dataset report rerun successfully; raw hash checked on load. Integrity tests: 2 passed including tampered temporary copy rejection.


## Phase 3 — preprocessing verified
- Median/mode imputation, feature engineering, scaling and encoding live in the pipeline; demographic audit fields and ID excluded from predictors.
- Preprocessing and training-boundary checks: 14 passed. Fold estimators' medians were compared to their own training rows for weighting and SMOTENC.
- Actual before/after missingness and finite arrays saved. Initial nested-pipeline failure and fix recorded in BLOCKERS.md.


## Phase 4 — EDA verified
- Generated ten PNG figures using only 491 training rows; verified zero holdout overlap.
- Executed 12 notebook code cells with no cell errors. Non-fatal Windows Jupyter event-loop warning observed.
- Insights generated from actual training statistics in docs/04_eda.md and the notebook.


## Phase 5 — modeling verified
- All five algorithms completed both class-weight and SMOTENC searches: ten candidates, four parameter settings each, five folds, no failed candidate.
- Training-only CV selected Decision Tree/class_weight (F1 0.8696259724084484). Saved complete pipeline, version metadata, OOF scores and disjoint IDs.
- Training OOF cost threshold is 0.76; reject-all behavior retained as failed cost scenario. Conventional 0.50 app policy documented separately.
- Full fresh refit reproduced all CV results and saved model scores. Training-boundary/threshold checks passed in the full 43-test suite.


## Phase 6 — evaluation verified
- Frozen holdout has 123 rows. At 0.50: accuracy 0.886179, F1 0.921348, ROC-AUC 0.841950; confusion counts 27/11/3/82.
- Failed 0.76 policy rejects all: 85 false rejections, cost 85 versus 58 at 0.50. No threshold retuning on holdout.
- Wrote baselines, default/tuned matrices, curves, row/group errors and demographic audits with counts/undefined rates.
- Five evaluation-focused tests passed; outputs reproduced in full rebuild.

