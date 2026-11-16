# Viva notes

## A short explanation of the project

"My project learns historical housing-loan approval patterns from the Dream Housing Finance dataset. I compare five classifiers using training-only cross-validation, save the selected complete preprocessing/model pipeline, and explain its approval scores with SHAP. A Streamlit interface supports one application, CSV batches and model evidence. It is an educational screening assistant for human review. Approval labels do not tell us whether borrowers repay, so I cannot claim that the project measures default risk or reduces NPAs."

The experiment uses 614 real applications. A raw stratified split reserves 123 for final evaluation and uses 491 for development. The selected class-weighted Decision Tree has CV F1 0.869626. On the holdout at conventional 0.5, accuracy is 0.886179, F1 0.921348 and ROC-AUC 0.841950. Present the majority baseline and the failed cost-threshold experiment alongside these results.

## Follow one application through the code

```text
raw application fields
  -> validate values and required columns
  -> exclude identifier and demographic audit fields
  -> impute missing numeric/category values using fitted training statistics
  -> calculate financial proxies and log features
  -> scale numerics and temporarily encode categories
  -> skip the training-only sampler during inference
  -> one-hot encode categories
  -> obtain final classifier approval score
  -> apply the selected application policy threshold
  -> explain the same score using SHAP
```

During cross-validation, every fitted step is cloned and fitted on each fold's training rows. SMOTENC generates extra minority training observations only during `fit`. It never changes the raw dataset or resamples an applicant being predicted. The outer imbalanced-learn Pipeline is flat because imbalanced-learn rejects an intermediate nested Pipeline; its steps come from the shared preprocessor factory.

## What each source, app and test file does

| File | Plain-English purpose and main design choice |
| --- | --- |
| `src/__init__.py` | Marks the source directory as a Python package so commands run as `python -m src.module`. |
| `src/common.py` | Defines paths/seed, hashes and validates raw data, writes finite JSON, and provides the single stratified raw split. A shared split prevents different phases silently using different holdouts. |
| `src/download_data.py` | Tries authentic organizer/mirror URLs in order, checks expected shape, writes raw bytes once with exclusive creation, and records source/checksum. Existing raw files are verified rather than overwritten. |
| `src/dataset_report.py` | Generates the dictionary, dtypes, missingness, class balance, dataset notes and actual before/after imputation checks. Its separate reporting fit is not reused as training input. |
| `src/preprocess.py` | Contains input validation, stateless cleaning/feature transformers, fold-local median/mode imputers, scaling and encoders. Shared factories keep training and app transformations consistent. |
| `src/eda.py` | Generates ten plots and calculated insights using training rows only; creates the executable EDA notebook. Unknown groups stay visible and numeric plots omit missing values. |
| `src/train.py` | Searches five algorithms under two imbalance strategies, chooses by CV F1, generates training OOF scores, demonstrates cost tuning and saves the complete winning pipeline. XGBoost's balanced sample weights are calculated inside each fit. |
| `src/evaluate.py` | Evaluates the already selected model on holdout rows; writes standard/tuned metrics, a majority baseline, actual error rows, subgroup rates and plots. It does not choose a new model from test results. |
| `src/predict.py` | Loads the trusted project artifact and provides one validation/prediction function for single and batch use. It rejects non-finite scores and rows with no model inputs. |
| `src/explain.py` | Explains final encoded approval probabilities with permutation SHAP, uses training-only background rows, checks additivity, and produces readable reasons and figures. |
| `src/run_pipeline.py` | Runs all phases from raw data, executes the notebook in this interpreter and records phase outcomes. Optional reproduction checking compares a new complete fit with an existing result snapshot. |
| `app/app.py` | Implements Streamlit input, output, explanation, CSV and model-evidence tabs. Native forms submit inputs together; trusted models are cached, uploads stay in memory, and text exports neutralize spreadsheet formulas. |
| `tests/test_data.py` | Checks the real source hash/shape and verifies that an altered temporary copy is rejected. The real raw file is never edited in a test. |
| `tests/test_preprocess.py` | Checks missingness, `3+`, feature formulas, invalid inputs, finite transforms and unchanged imputer statistics on holdout transformation. Artificial fixtures test boundaries and are not training observations or reported data. |
| `tests/test_training.py` | Inspects actual fitted CV fold imputers, checks resampling/prediction behavior, threshold costs and single/batch prediction agreement. |
| `tests/test_evaluate.py` | Checks positive-class/error-cost direction, actual versus predicted subgroup rates, missing groups and undefined metric cases. |
| `tests/test_explain.py` | Checks agreement with prediction, probability reconstruction, three reasons, readable feature labels and training-only background IDs. |
| `tests/test_app.py` | Uses Streamlit AppTest to exercise the actual form and result; also checks blank submissions, upload limits and formula-safe CSV output. |
| `tests/test_reproduction.py` | Proves the reproduction comparator rejects changed metrics, thresholds, model parameters, IDs, raw hashes or scores, while allowing only tiny floating-point tolerance. |

## Configuration, notebooks and artifacts

| File or artifact | Purpose |
| --- | --- |
| `requirements.txt` | Direct library requirements with bounded version ranges. |
| `requirements-lock.txt` | Exact package versions installed for this experiment. Use Python 3.12 for this frozen environment. |
| `pytest.ini` | Makes the project importable in tests, sets the test directory and filters the documented feature-name warning. |
| `.gitignore` | Keeps the virtual environment, caches, logs, credentials and unlicensed-to-redistribute raw CSV out of Git. It does not delete those local files. |
| `.streamlit/config.toml` | Sets the original navy/teal light theme, upload-size limit and disables Streamlit usage-statistics collection. |
| `notebooks/01_eda.ipynb` | A readable executable view of training-only EDA, with calculated final Key Insights. The runner records successful execution; an unexecuted notebook alone is not evidence. |
| `data/raw/train.csv` | The unchanged authentic organizer download, retained locally. |
| `data/raw/source.json` | Exact requested/resolved URLs, download time, byte count, checksum, Kaggle fallback and license uncertainty. |
| `data/processed/split_manifest.json` | Exact train/holdout Loan_ID lists, seed, class counts and raw hash. It makes overlap checks auditable. |
| `data/processed/train_oof.csv` | Real training labels and out-of-fold model scores used for the experimental cost threshold. |
| `models/best_model.joblib` | The fitted complete pipeline and metadata. Joblib can execute Python during loading, so only this trusted local artifact is loaded; users cannot upload models. |
| `models/metadata.json` | Human-readable model identity, threshold experiment, dataset hash and package versions. |
| `reports/dataset_summary.json` | Observed shape, split/class counts, duplicate counts, missing totals and transform-finiteness checks. |
| `reports/data_dictionary.csv`, `missing_values.csv`, `class_balance.csv` | Generated schema descriptions, per-column missingness and target counts. |
| `reports/preprocessing_missing_values.csv` | Observed missing counts before/after the actual fitted imputation stage for train and holdout. |
| `reports/eda_approval_by_*.csv`, `eda_insights.json` | Training-only grouped counts/rates, named plot outputs and calculated insight sentences. |
| `reports/model_comparison.csv` | Best sampled parameters, mean CV metrics, fold standard deviations and train F1 for every candidate. |
| `reports/training_failures.json` | Candidate exceptions, if any; an empty list means no candidate failed in that completed run. |
| `reports/threshold_costs.csv` | False approvals, false rejections and assumed costs at each training OOF threshold. |
| `reports/metrics.json` | Actual standard/tuned holdout metrics, train metrics, class counts, confusion matrices, baseline and train-test gaps. |
| `reports/holdout_predictions.csv`, `error_analysis.csv` | All holdout scores/decisions and rows wrong under either standard or experimental policy. |
| `reports/error_groups.csv` | Actual error counts/rates grouped by credit history, property area and education. |
| `reports/fairness.csv` | Actual and predicted Gender/Married approval rates, sample sizes, class denominators and group TPR/FPR. |
| `reports/shap_metadata.json`, `shap_example.json` | Background/summary IDs, explanation settings, additivity error, global rankings and a real worked example. |
| `reports/run_manifest.json`, `reproduction.json` | Generated full-run outcomes/environment and comparison evidence when those commands are executed. Their existence and status must be inspected before claiming success. |
| `reports/figures/` | Ten `eda_*.png` plots, actual evaluation curves/confusion matrices, training cost curve, global SHAP and a single-app waterfall. All are generated from code and real observations. |

Generated logs and cached bytecode are execution aids, not research evidence or source code. The virtual environment is installed third-party software, not student-authored code to explain line by line.

## Documentation map

| Document | What to use it for |
| --- | --- |
| `README.md` | Setup, exact commands, real results and the most important limitations. |
| `docs/00_research.md` | Curated primary methodology, inspected GitHub projects, leakage findings, license notes and UI references. |
| `docs/01_problem_statement.md` | Target, inputs, outputs, intended use, metrics and cost semantics. |
| `docs/02_dataset.md` | Exact source, dictionary, observed shape/types/missingness/balance and split. |
| `docs/03_preprocessing.md` | Pipeline steps and actual before/after missingness checks. |
| `docs/04_eda.md` | Training-only plots and calculated descriptive insights. |
| `docs/05_modeling.md` | Candidate algorithms, search setup, real CV comparison and threshold experiment. |
| `docs/06_evaluation.md` | Actual holdout results, baseline, errors, policy trade-offs and group audit. |
| `docs/07_explainability.md` | How to read SHAP, actual setup/example and limits. |
| `docs/UI_DESIGN.md` | Original interface choices and verified design references. |
| `docs/ASSUMPTIONS.md` | Decisions made where source metadata or requirements were ambiguous. |
| `docs/PROGRESS.md` | Per-phase work and verification history. |
| `docs/BLOCKERS.md` | Failures, attempted operations and recoveries. |
| `docs/STATUS_UPDATE.md` | The requested eight-section college-project status report. |
| `docs/VIVA_NOTES.md` | This file: file explanations, formulas, demonstration and questions. |
| `docs/MORNING_SUMMARY.md` | Final handoff with what actually completed, failed and needs attention first. |

## Feature formulas and choices

Let `A` and `C` be applicant/co-applicant monthly income in dataset units, `L` the dataset LoanAmount in thousands, `n` the term in months, and `r = 0.09 / 12` the assumed monthly rate.

| Feature | Formula and meaning |
| --- | --- |
| TotalIncome | `A + C`: combined income, assuming the same period/unit basis. |
| Principal | `L * 1000`: convert the amount from thousands to dataset monetary units. |
| EMI | `Principal * r / (1 - (1+r)**(-n))`: illustrative fixed-rate amortized monthly installment. Code uses equivalent `log1p`/`expm1` operations for numerical stability. |
| Balance_Income | `TotalIncome - EMI`: a simplified residual; it omits living costs, existing debt and other real affordability factors. |
| Loan_to_Income_Ratio | `Principal / (12 * max(TotalIncome, 1))`: principal divided by assumed annual income; denominator protection prevents division by zero. |
| Log transforms | `log1p` of ApplicantIncome, CoapplicantIncome, LoanAmount and TotalIncome; it handles zero and compresses skew without dropping outlier observations. |

The 9% rate and monthly income interpretation are assumptions, not observed dataset facts. `3+` dependents become 3, a lower bound rather than an exact count. All financial proxies are calculated after imputation so missing source values do not propagate NaNs. None is a credit-policy rule or guaranteed estimate of affordability.

## Twenty likely viva questions and answers

### 1. What exactly does the model predict?

Historical approval (`Y`) versus rejection (`N`). It estimates patterns in recorded decisions. It does not predict repayment, future default, creditworthiness as an objective truth, or NPA reduction because those labels are absent.

### 2. Where did the data come from, and did you create any rows?

The authentic 614-row CSV came from the organizer's public download URL, recorded with a SHA-256 checksum in `source.json`. I did not invent raw rows or plots. SMOTENC creates explicitly synthetic minority samples only inside training folds; artificial pytest fixtures exercise boundaries and are never presented as observations.

### 3. Why split before preprocessing?

Imputers, scalers and encoders learn statistics. Fitting them using all rows lets information from the holdout influence training and can inflate evaluation. I first split raw rows, then fit the entire pipeline within each CV training fold. Holdout inference only transforms and predicts.

### 4. Why use stratification, seed 42 and five folds?

Stratification keeps approval/rejection proportions similar across partitions. The fixed seed reproduces the row assignment and searches. Five folds provide several validation views while retaining enough rows to train each model; they do not make a small dataset representative of all banks.

### 5. How do you handle missing and invalid values?

Valid blanks use numeric medians or categorical modes fitted on training rows. Malformed numbers, infinities, negative income, nonpositive supplied loan/term, invalid categories and missing required columns are rejected. Entirely blank model-input rows are rejected rather than silently scored from defaults.

### 6. Why these engineered features and log transforms?

Combined income, installment and income ratios provide simple affordability-related summaries of existing fields. `log1p` reduces skew while retaining observations and accepting zero income. I explicitly document units and the assumed interest rate; these proxies do not add actual debt or repayment information.

### 7. Why drop Loan_ID, Gender and Married?

Loan_ID identifies a record rather than an applicant characteristic intended for generalization. Gender and Married are excluded from prediction and retained for requested audits/EDA. Exclusion prevents direct use but does not remove correlated proxies or prove fairness.

### 8. Why use one-hot encoding and scaling?

One-hot encoding represents nominal categories without imposing an artificial ordering. Numeric standardization helps Logistic Regression and nearest-neighbor operations used by SMOTENC. Tree models do not generally require scaling, but sharing the pipeline makes the comparison consistent.

### 9. Why SMOTENC rather than ordinary SMOTE?

The dataset mixes numeric and categorical fields. Ordinary interpolation of one-hot values can create fractional categories. SMOTENC handles category identities separately before final one-hot encoding. Its synthetic numeric engineered features can still violate their defining formulas, which is a documented limitation.

### 10. How does class weighting differ from oversampling?

Weighting changes how much fitting penalizes errors on each class; it does not add observations. SMOTENC adds synthetic minority training samples. They are compared as separate strategies. XGBoost receives balanced per-row weights calculated from each fit's labels because it lacks the same native class_weight option used by the other candidates.

### 11. Why compare these five algorithms?

Logistic Regression is a simple linear baseline; Decision Tree captures nonlinear rules; Random Forest averages many trees; XGBoost and LightGBM are boosting implementations. Comparing their actual CV results is more defensible than assuming the most complex model must win.

### 12. How was the best model selected?

Each algorithm/strategy used four sampled parameter settings and five-fold stratified CV. Mean approval-class F1 selected the winner, with ROC-AUC as a tie-breaker. The shallow class-weighted Decision Tree achieved CV F1 0.869626. Its holdout score did not choose it, and a higher-AUC Random Forest was not relabeled the winner after evaluation.

### 13. Why is accuracy alone insufficient?

An always-approve baseline already gets holdout accuracy 0.691057 and F1 0.817308 because approvals are common. I also report approval precision/recall, rejection recall, macro-F1, balanced accuracy, confusion counts and ROC-AUC so minority failures remain visible.

### 14. What do the final standard-policy numbers mean?

At 0.5 on 123 reserved rows, accuracy is 0.886179, precision 0.881720, recall 0.964706, F1 0.921348 and ROC-AUC 0.841950. There are 11 false approvals and 3 false rejections. These are results on this split, not guaranteed real-world performance or calibrated repayment probabilities.

### 15. What happened to business-cost threshold tuning?

With assumed false-approval/false-rejection costs of 5:1, training OOF tuning selected 0.76. The final tree's highest leaf score is about 0.639444, so that threshold rejects every applicant. Holdout scenario cost is 85 rather than 58 at 0.5. I retain this failed experiment, explain the fold-to-final score-scale mismatch, and use the pre-existing conventional 0.5 policy as the app default without retuning a new threshold on test labels.

### 16. Why can the holdout score exceed the training score?

A small random holdout can happen to contain easier cases. Training accuracy here is 0.806517, lower than holdout 0.886179. This alone neither proves leakage nor proves better generalization. I inspect the pipeline boundary, disjoint IDs, CV variability and limitations instead of treating one favorable split as certainty.

### 17. What does SHAP explain, and how do you verify it?

Permutation SHAP explains the saved classifier's approval probability on final encoded features. The background uses 30 training applications and the global plot uses 60 training applications. I check that background score plus SHAP contributions reconstructs the same model probability; the recorded maximum error is approximately 1.11e-16.

### 18. Are SHAP reasons causal, and why can a positive contribution still accompany rejection?

They are model associations relative to a training background, not causes or guaranteed actions. The SHAP background score differs from the policy threshold, so a score can rise from its background yet remain below a threshold. Independent masking and correlated raw/engineered features can produce unrealistic combinations or shared attribution. Standardized plot values are not raw currency values.

### 19. Does the demographic audit prove the model is fair?

No. It compares actual and predicted approval rates and error rates by Gender and Married with sample sizes and denominators. Small groups and missing labels limit interpretation; undefined rates remain undefined. Historical labels and proxy features may carry bias even after protected fields are removed.

### 20. How do you demonstrate reproducibility and what would you improve next?

Run the full pipeline from unchanged raw data, execute all notebook cells, run pytest, and use `--verify-reproduction` to compare model choices, parameters, metrics and holdout scores with an independent refit. For real use, collect contemporary permissioned data with repayment outcomes, validate externally, justify costs and calibration, quantify subgroup uncertainty and involve bank reviewers. I would not repeatedly tune against this examined holdout.

## A practical viva demonstration

1. Open the README results and explain standard versus failed experimental thresholds before showing the app.
2. Show the exact raw source/checksum and the 491/123 split manifest.
3. Open the notebook's training-only figures and its calculated Key Insights.
4. Show the CV comparison and explain why F1 selected the shallow tree although another candidate had higher ROC-AUC.
5. Enter an explicitly identified demonstration application or a known dataset row, inspect the score/threshold and explain the SHAP baseline/contributions.
6. Show a batch result, the held-out confusion matrix, the group audit, and fresh verification evidence in the morning summary.

Never describe hypothetical form inputs as newly collected bank observations or treat a UI launch as evidence that all prediction paths passed. Read final execution evidence and limitations together.

Optional `tests/browser_live.py` opens the running app with Playwright and uses one real public dataset row to check displayed scores, SHAP, CSV upload, evidence and mobile overflow. It is separate from pytest so the app needs no browser dependency; use the transient tool command in the README.
