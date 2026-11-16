# Project status update

## 1. Problem Statement

Housing Loan Approval Prediction Using Machine Learning Algorithms: Build an Explainable Loan Screening Assistant is a binary classification college project. It predicts historical `Loan_Status` approval labels, displays an approval model score and explains model associations for a human reviewer. Approval is class 1; rejection is class 0. F1, precision, recall and ROC-AUC are reported alongside accuracy, minority-class results and a majority baseline. Repayment, default and NPA reduction are not observed outcomes in this dataset.

## 2. Dataset Collection

The authentic Dream Housing Finance CSV was downloaded from the public organizer URL recorded in `data/raw/source.json` and `docs/02_dataset.md`. It contains **614 rows, 13 columns, 149 missing cells**, and no duplicate Loan_ID values. The raw target has **422 approvals and 192 rejections**. The raw SHA-256 is `8c2cc67a13279ec746b15f76f14e8503154274ef7f221d2437033b4407c80ca8`.

Kaggle credentials/CLI were unavailable, so the public direct source was used. The raw file is preserved unchanged and checked by hash on load. Its redistribution license remains unverified, so the CSV is excluded from Git while the exact source and checksum are retained.

## 3. Data Preprocessing

Raw stratified 80/20 splitting with seed 42 produces **491 training applications** (337 approved, 154 rejected) and **123 holdout applications** (85 approved, 38 rejected). This happens before fitting any imputer, scaler, encoder or sampler.

The pipeline validates values, removes Loan_ID and demographic predictors, maps Dependents `3+` to 3, fits numeric medians and categorical modes, engineers TotalIncome/EMI/Balance_Income/Loan_to_Income_Ratio/log features, standardizes numerics and encodes categories. Credit_History is categorical. The reporting fit produced **17 columns before final one-hot encoding**, with **zero non-finite values** in both partitions and zero remaining missing values at the imputation stage.

Median/mode statistics are fitted separately within each CV training fold. SMOTENC runs only during candidate fitting, before final one-hot encoding; inference never resamples applicants. EMI uses an explicit assumed annual rate of **9%**, principal = LoanAmount × 1,000, and terms in months. Currency and income-period metadata are not independently established; the monthly interpretation is a documented assumption.

## 4. Exploratory Data Analysis (EDA)

The training-only notebook and EDA module generate **10 PNG plots**: target balance, income histograms, loan distribution, approval by credit history/property/education/marriage/self-employment, income boxplots and numeric correlations. The notebook ends with insights calculated from the real training rows.

In the training partition, **337 of 491** applications were approved. Observed approval rates are **9.0%** for credit-history indicator 0 (67 rows), **79.0%** for indicator 1 (381 rows), and **69.8%** for missing credit history (43 rows). Property-area approval rates are **60.7% Rural**, **77.7% Semiurban**, and **65.4% Urban**. These describe historical associations, not causal effects or repayment likelihood. No holdout labels are used in target-informed EDA.

## 5. Model Development

Logistic Regression, Decision Tree, Random Forest, XGBoost and LightGBM were each compared under balanced weighting and SMOTENC: **10 candidates**, with four sampled hyperparameter settings and five stratified CV folds per candidate. The completed search recorded no failed candidate.

The selected **class-weighted Decision Tree** has `max_depth=2`, `min_samples_leaf=5`. It ranked first on approval-class CV F1, **0.869626 ± 0.027836**, with CV ROC-AUC **0.683752**. Random Forest had higher CV ROC-AUC (**0.771284**), illustrating that the winner depends on the predeclared F1 objective. Selection did not use holdout metrics. The fitted complete pipeline is saved as `models/best_model.joblib`.

## 6. Model Evaluation

The reserved holdout contains **123 applications**. At the conventional **0.50** threshold, accuracy is **0.886179**, precision **0.881720**, recall **0.964706**, F1 **0.921348**, and ROC-AUC **0.841950**. The confusion matrix has **27 true rejections, 11 false approvals, 3 false rejections and 82 true approvals**. The always-approve baseline has accuracy **0.691057** and F1 **0.817308**. Training accuracy is **0.806517** and training F1 **0.872825**; this small holdout happened to score better, which is not evidence of guaranteed generalization.

Training OOF cost tuning under assumed false-approval/false-rejection costs **5:1** selected **0.76**. This threshold exceeds the final tree's maximum leaf approval score, **0.6394436519258202**, and therefore rejects every application. On the holdout it gives **zero approvals, 85 false rejections, F1 0.000000**, and scenario cost **85**, versus **58** at 0.50. The failed experiment is retained and explained. The app defaults to conventional 0.50 and exposes 0.76 only as an explicitly labeled experimental policy; no test-set threshold retuning was performed.

Generated evaluation artifacts include confusion matrices, ROC/PR curves, a training threshold curve, row-level errors, grouped errors, and Gender/Married audits comparing actual and predicted approval rates. Small group counts and missing denominators are reported. These audits do not certify fairness or absence of proxy bias.

## 7. Application/Deployment

The primary interface is a custom localhost website started with `python -m web` at **http://127.0.0.1:8000**. Its seven routes provide a public homepage, workspace overview, new assessment, batch screening, model evidence, methodology and design references. The homepage includes a housing hero, process explanation, genuine optional model example, FAQs and footer. Native HTML/CSS/JavaScript modules share an origin with FastAPI, which calls the existing frozen Python pipeline and SHAP code. The original Streamlit interface remains an alternative at port 8501.

The website provides grouped applicant input, an explicitly labeled real public training example, a screening suggestion with score and threshold, a SHAP waterfall and three plain-English associations, batch CSV processing, downloadable results and generated model evidence. Both interfaces use the shared prediction and `src/interface.py` upload/export helpers. Uploads are bounded to **1,000 rows and 5 MB**, validated by received bytes, processed in memory, and not persisted as application history. No login or database is added.

The current design adapts Better's measured forest/ivory palette and pill actions, Blend's split hero, and Habito's numbered narrative. The homepage research records **seven primary sources** with captures and measurements in `HOMEPAGE_RESEARCH.md`; older dashboard research remains historical. Original housing artwork is explicitly illustrative, and DM Sans / Instrument Serif are self-hosted under OFL licenses. The inside screens now share the actual homepage header/footer, editorial titles and pill actions; horizontal tool navigation and a mobile grid replace the old sidebar. Assessment fields, policy, empty/result panels and all other workspace surfaces have been restyled together. Model values remain genuine API outputs.

SHAP uses **30 training background rows**, **60 training summary rows**, and five permutation cycles. The maximum recorded additivity error is **1.1102230246251565e-16**. Explanations are in probability space on standardized/one-hot features and explicitly describe model associations. The website reuses these model semantics without a new fit. A non-root Linux container recipe and separate runtime lock prepare the site for later hosting. Local API, browser and container outcomes are recorded separately in `HOMEPAGE_HANDOFF.md` and `reports/website_verification.json`; the original pipeline/Streamlit evidence remains in `MORNING_SUMMARY.md`. No cloud publication or production lending deployment is claimed.

## 8. Current Challenges and Next Steps

The main observed modeling challenge is the degenerate cost threshold: OOF fold score scales did not transfer to the final fitted tree's score support. The conventional policy remains an educational demonstration; a real policy needs independently justified costs, calibration and prospective validation. Hyperparameter selection and threshold tuning share training data, so OOF tuning scores can be optimistic and are not nested-CV estimates.

The dataset is small, its collection process/date and authoritative currency metadata are unavailable, and historical labels may encode bias. SMOTENC's synthetic numeric engineered features can violate their original financial formulas. Independent SHAP masking can create unrealistic feature combinations, and correlated features share attribution. None of these outputs establish causal effects, creditworthiness, repayment risk or NPA reduction.

The website is a local educational service, not an authenticated bank portal. Before public distribution or real applicant use, review the source dataset's redistribution rights, access control, data handling, operational limits and independent lending validation. Read the final website handoff for the checks actually executed; do not treat unexecuted deployment or accessibility checks as passed.

For the viva, inspect the standard-versus-cost policy comparison first, start the custom website and explain one labeled dataset example, then inspect the raw provenance, shared API validation and fold-boundary tests. Future model work should collect contemporary permissioned data with repayment outcomes, obtain external validation, assess calibration and subgroup uncertainty, and involve bank/domain reviewers before real use. Do not repeatedly tune this model on the already examined holdout.
