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


## Phase 7 — explainability verified
- Generated global SHAP from 60 real training rows and 30 training background rows, plus a single-app waterfall and three descriptive reasons.
- Probability additivity maximum error: 1.1102230246251565e-16. Both explanation tests passed and global artifacts regenerated in full refit.
- Encoded-feature/independent-masking limitations and baseline-versus-threshold distinction documented.


## Phase 8 — application verified
- Streamlit launched headless at http://127.0.0.1:8501; health HTTP 200.
- Eight app tests passed: single prediction and SHAP, policy copy, blank/audit-only rejection, bounded CSVs, duplicate-header rejection and formula-safe headers/cells.
- Live Chromium checks passed: real application LP002804 score matches saved report, SHAP image, batch upload/download, model evidence, desktop 1440px and mobile 390px without page overflow; zero uncaught JavaScript errors.
- Built-in browser connection failed three times; Playwright fallback succeeded. No cloud deployment claimed.


## Phase 9 — documentation and final reproduction verified
- README, eight-section STATUS_UPDATE, twenty-question VIVA_NOTES and MORNING_SUMMARY completed with generated real results.
- Full fresh pipeline process exit 0; final run 161.128366799996 seconds. All ten candidates and 123 holdout scores matched prior results at tolerance 1e-12, maximum score difference 0.0.
- Executed all twelve notebook code cells without errors. Full pytest process exit 0: 43 passed, zero skipped/failures; final output 57.74 seconds.
- Live browser process exit 0; health HTTP 200. Dependency compatibility, source compilation and whitespace checks passed.
- Machine evidence saved in reports/verification.json, reproduction.json, run_manifest.json, pytest_results.xml and browser_check.json.
- Independent re-review found all five initial findings addressed. External bank validation, formal accessibility audit, cloud publication and a Python-version matrix were outside this local educational build.


## Website follow-up — research and shared interface verified
- User requested a complete custom localhost website with close reference matching and later deployment support.
- Inspected 12 primary UI references; measured Mercury's official live dashboard and saved eight reference captures. Design contract in docs/WEBSITE_REFERENCES.md.
- Extracted shared CSV upload/export and tree-score checks to src/interface.py. Legacy Streamlit regression checks: 8 passed after extraction.
- Added FastAPI/uvicorn to the frozen environment; model and raw-data SHA-256 baselines recorded. Existing trained model is reused without refitting.


## Website follow-up — model API verified
- Added explicit website routes and same-origin FastAPI prediction, real SHAP, batch, evidence, template and allowlisted-figure endpoints.
- API checks: 18 passed, including actual model agreement, probability additivity, malformed inputs, streamed body limits and single/batch numerical precision.
- Independent review found and fixed batch JSON precision and container health-check PORT handling. Saved model and raw bytes are unchanged.


## Website follow-up — complete frontend verified
- Delivered six custom website routes with actual prediction/SHAP, CSV screening/export, model evidence, methodology and references.
- Measured browser match to Mercury: 220px rail, 968px content, 472px first panel, 28px/36px title, #5266eb primary action, 12px panels and 8px active navigation.
- Native Chromium passed every functional flow and 30 responsive checks across six routes at 320, 390, 768, 1024 and 1440px; zero uncaught JavaScript errors.
- Three delayed-real-response regressions initially reproduced, then passed after fixing late-example invalidation, overlapping batch cleanup and policy-toggle keyboard focus.
- axe-core 4.14.0 found contrast issues in switch/badge text; fixed them. Final six-route automated WCAG A/AA check reports zero violations; formal assistive-technology auditing is not claimed.
- Saved actual screenshots and a side-by-side reference comparison. Source formatting and JavaScript syntax checks use development tooling only; the app needs no Node runtime.


## Website follow-up - deployment and final handoff verified
- Final full suite: 62 passed, zero failures/errors/skips; 49.43 seconds. API documentation now includes editable bounded JSON/CSV request schemas.
- Linux amd64 image built and passed full browser flows plus 30 responsive checks. Non-root UID 10001, read-only filesystem and health on PORT 8080 verified.
- All 15 website source files in the image matched local bytes. Raw/model hashes remained unchanged; native/container score difference was 0.0.
- Automated axe-core 4.14.0 checked six routes with WCAG 2 A/AA and 2.1 A/AA tags: zero violations. Three asynchronous/focus regression checks passed.
- Saved combined reports, screenshots, reference board, deployment guide and WEBSITE_HANDOFF. Native localhost site remains on port 8000. Temporary verification container is stopped after evidence collection; no cloud publication performed.
