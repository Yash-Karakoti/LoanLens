# Morning summary — 16 November 2026

> **Website follow-up:** the current primary interface is the custom website at http://127.0.0.1:8000, now with a public housing homepage and a workspace at `/workspace`. Read [HOMEPAGE_HANDOFF.md](HOMEPAGE_HANDOFF.md) for the current UI, reference comparison and fresh checks. The material below preserves the original scientific/Streamlit build handoff.

The complete local college project is built in `D:\Koding\Housing Loan Approval Prediction`. All requested phases are implemented. The final training pipeline, notebook, tests and live app workflows were actually run. Results below come from generated reports, not external repository claims.

## What to check first

1. Open [the app](http://127.0.0.1:8501). The local server was left running and its health endpoint returned HTTP 200 at handoff. If it has stopped, use the PowerShell command below.
2. Keep **Standard (0.50)** selected. Read the warning about the failed **0.76 cost scenario** before demonstrating it. The failed experiment is preserved, not hidden or retuned on test labels.
3. Read [06_evaluation.md](06_evaluation.md) and [VIVA_NOTES.md](VIVA_NOTES.md). Explain approval versus repayment, the raw split, fold-local preprocessing and threshold selection before quoting accuracy.
4. Open the executed notebook and [STATUS_UPDATE.md](STATUS_UPDATE.md). The notebook contains real outputs and calculated Key Insights; the status update has the requested eight sections, and the viva notes include twenty questions and answers.

```powershell
Set-Location 'D:\Koding\Housing Loan Approval Prediction'
.\.venv\Scripts\python.exe -m streamlit run app/app.py --server.headless true --server.address 127.0.0.1
```

## Completed

- Created a separate Git repository and Python 3.12 virtual environment. Installed the requested stack and froze the actual package versions. Existing projects were not edited.
- Researched comparable GitHub implementations, inspected their source for leakage and licensing, and documented primary methodological references and UI references in [00_research.md](00_research.md). No third-party application code was copied; this is a curated review, not a claim to have found every related repository.
- Downloaded the authentic organizer CSV: **614 applications, 13 columns, 149 missing cells**. The exact URL and SHA-256 are in [02_dataset.md](02_dataset.md) and `data/raw/source.json`. Raw bytes remain unchanged and are checked on load.
- Created the raw stratified **491/123** train/test split with seed 42, complete preprocessing/feature-engineering pipelines, fold-local weighting/SMOTENC comparisons and data-boundary tests.
- Generated **10 training-only EDA figures** and executed all **12 notebook code cells** without cell errors.
- Compared **10 model/strategy candidates**: the five requested algorithms under class weights and SMOTENC, each with four sampled settings and five stratified folds. No candidate failed in the completed searches. Saved the best complete pipeline, metadata, real OOF scores and split IDs.
- Generated baseline and holdout metrics, default/tuned confusion matrices, ROC and PR curves, train/test gaps, cost tuning, demographic audits and row/group error analysis.
- Generated global and single-app probability-space SHAP explanations. Background: **30 real training rows**; summary: **60 training rows**. Maximum recorded additivity error: **1.1102230246251565e-16**.
- Built Streamlit single-application, batch-CSV and model-evidence tabs with shared validation, missing-field notices, SHAP waterfall and three descriptive reasons. CSV size/row limits, duplicate headers, formula-safe downloads, invalid input and audit-only submissions are checked.
- Completed the README, assumptions, research/design notes, phase reports, progress log, blockers, status update and viva guide. Phase commits record the work locally; nothing was pushed or deployed publicly.

## Actual results

The selected model is **Decision Tree / class_weight**, with `max_depth=2` and `min_samples_leaf=5`, selected by training CV F1 **0.869626 ± 0.027836**. The objective was fixed before evaluating the holdout; the model with the highest ROC-AUC was not necessarily the F1 winner.

On the **123 untouched holdout applications**, at the conventional **0.50** threshold:

| Metric | Observed value |
| --- | ---: |
| Accuracy | 0.886179 |
| Precision | 0.881720 |
| Recall | 0.964706 |
| F1 | 0.921348 |
| ROC-AUC | 0.841950 |
| True rejections / false approvals | 27 / 11 |
| False rejections / true approvals | 3 / 82 |
| Always-approve baseline accuracy / F1 | 0.691057 / 0.817308 |

**The cost experiment failed as a useful shortlisting policy.** Training OOF tuning under assumed false-approval/false-rejection costs of **5:1** chose **0.76**, already a reject-all optimum on those OOF predictions. The fitted final tree's maximum possible leaf score is **0.6394436519258202**, below the saved threshold. The cost policy therefore rejects every possible applicant. On the holdout it rejects all **85** historically approved applicants, gives F1 **0**, and costs **85** illustrative units versus **58** at 0.50. The app defaults to the pre-existing fixed 0.50 policy and exposes 0.76 only as an explicitly failed scenario. No replacement threshold was fitted to holdout labels. The shared API uses the saved threshold unless an explicit policy copy is supplied, as the app does.

## Fresh verification evidence

The final commands returned **process exit 0**:

```powershell
.\.venv\Scripts\python.exe -m src.run_pipeline --verify-reproduction
.\.venv\Scripts\python.exe -m pytest -q --junitxml=reports/pytest_results.xml
uv tool run --from playwright python tests/browser_live.py
```

- **43 tests passed**, **0 failures/errors**, **0 skipped**. Final pytest output reported **57.74 seconds**. The JUnit sum is recorded separately in `reports/verification.json`.
- Final full rebuild: **161.128366799996 seconds** on this host. Every candidate was fitted again from raw rows; no transformed training array was reused.
- Reproduction matched all model identities/parameters, CV values, reported metrics, raw checksum, holdout IDs/labels/scores/decisions and the saved threshold at absolute tolerance **1e-12**. Maximum holdout probability difference: **0.0** across **123 rows**, with **10 candidates** compared.
- Notebook: **12 code cells executed**, no error outputs. Correct project interpreter verified by a separate temporary-notebook test.
- Live Chromium: actual public application **LP002804** displayed the saved score, prediction and SHAP; batch CSV upload and downloadable predictions worked; the evidence tab rendered generated metrics. **Zero uncaught browser JavaScript errors**. Desktop **1440×1100** and mobile **390×844** were checked; the mobile page had no horizontal overflow. Screenshots are in `reports/figures/app_*.png`.
- Dependency compatibility (`uv pip check`), source compilation and `git diff --check` passed. Independent source review rechecked all five initial findings and found no remaining concrete issue in the reviewed changes.

Machine-readable evidence: `reports/verification.json`, `reports/reproduction.json`, `reports/run_manifest.json`, `reports/pytest_results.xml`, `reports/browser_check.json`. Ignored local logs remain in `reports/` for diagnosis.

## What failed and how it was handled

- Initial training rejected a nested Pipeline before fitting. Confirmed imbalanced-learn's restriction, flattened preprocessing into its outer pipeline, then verified actual fold-specific fitted medians for both imbalance strategies.
- The built-in computer-use browser connection timed out three times. Stopped retrying and completed live browser checks with Playwright instead.
- The first Playwright script used a dropdown option selector that did not match the current widget. Replaced it with keyboard selection and reran the complete live check successfully. A diagnostic print also hit Windows console encoding; using UTF-8 fixed the harness output. Neither changed model behavior or results.
- One redirected PowerShell invocation returned an error status on non-fatal Jupyter stderr even though the internal pipeline manifest passed. A further full rerun captured the native process exit explicitly and returned **0**. Upstream SHAP deprecation warnings and local notebook runtime warnings remain visible; they were not test failures.
- The cost-policy failure is an observed modeling result, not a repaired performance claim. It remains clearly labeled in the app and reports.

## Assumptions and practical limits

See [ASSUMPTIONS.md](ASSUMPTIONS.md) for the full record. The shorter folder name avoids an invalid Windows colon and long paths. Income is interpreted monthly in dataset units; authoritative currency/collection-date metadata was not found. Loan amount is in thousands and term in months. EMI assumes a fixed **9% annual rate** and is an educational proxy, not a bank offer. SMOTENC creates training-only synthetic feature vectors, never observed raw applications; derived numeric features can become inconsistent after interpolation.

Gender and Married are excluded as predictors but audited. This does not eliminate proxy bias or certify fairness. SHAP explains model associations on standardized/encoded features, not causes or lawful adverse-action reasons; masking correlated/one-hot features can create unrealistic combinations. Training OOF threshold estimates share data with hyperparameter selection and are not nested-CV results.

The CSV contains historical approval decisions, **not repayment/default labels**. This project cannot demonstrate creditworthiness, reduced NPAs, real bank savings or production lending suitability. No external bank validation, formal accessibility audit, cloud deployment or Python-version matrix was performed. Raw dataset redistribution rights remain unverified; the local CSV is excluded from Git and can be downloaded from its recorded source.

The project is ready for local demonstration and viva preparation. Future model revisions need new external validation data; do not repeatedly tune against the examined holdout.
