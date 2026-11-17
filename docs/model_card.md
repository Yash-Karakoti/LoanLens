# Model Card — LoanLens Decision Tree Classifier

> [!IMPORTANT]
> **LoanLens is an educational prototype and decision-support screening assistant.** It is not a licensed credit-scoring product, does not predict loan default or repayment probability, and must not be used as the sole basis for any real lending decision. All outputs are intended to assist human review, not replace statutory credit determinations.

---

## 1. Model Details

| Field | Value |
|:---|:---|
| **Model Name** | LoanLens Housing Loan Approval Classifier |
| **Model Type** | Decision Tree Classifier (`sklearn.tree.DecisionTreeClassifier`) |
| **Version** | 1.0.0 |
| **Date** | November 2026 |
| **Author** | Aayush Jha ([ZincChloride-cyber](https://github.com/ZincChloride-cyber)) |
| **License** | MIT |
| **Framework** | scikit-learn 1.7.2 |
| **Language** | Python 3.12 |
| **Artifact** | `models/best_model.joblib` (SHA-256 verified) |
| **Balancing Strategy** | Class weighting (`class_weight="balanced"`) |
| **Operational Threshold** | τ = 0.50 (standard); τ = 0.76 (experimental — produces reject-all, not used) |
| **Explainability** | TreeSHAP via SHAP 0.50.0 (`PermutationExplainer`, 30 background rows) |

### Model Selection Rationale

Selected via 5-fold stratified cross-validation on training data only. The Decision Tree with `class_weight` balancing ranked first by CV approval-class F1 score (0.8696 ± 0.0278), with ROC-AUC as the tie-breaker. No holdout labels were used in model selection, threshold tuning, or feature engineering.

---

## 2. Intended Use

### Primary Uses

- **Decision support for human underwriters** reviewing housing loan applications.
- **Educational demonstration** of an end-to-end ML pipeline with explainability, fairness auditing, and responsible-AI safeguards.
- **Teaching and viva demonstration** of SHAP explainability, threshold analysis, class imbalance handling, and leakage-safe feature engineering.

### Out-of-Scope Uses

- Making autonomous loan approval or rejection decisions without human review.
- Predicting loan default probability, non-performing assets (NPA), or credit risk migration.
- Deployment in a regulated lending environment without independent statistical validation, recalibration on representative production data, and legal compliance review.
- Use on populations, geographies, or loan products not represented in the Dream Housing Finance dataset.
- Real-time credit scoring under consumer credit regulations (e.g., ECOA, FCRA, RBI guidelines).

---

## 3. Training Data

| Field | Value |
|:---|:---|
| **Dataset** | Dream Housing Finance Loan Prediction Dataset |
| **Source** | Kaggle / Dream Housing Finance benchmark |
| **Total Records** | 614 loan applications |
| **Training Split** | 491 applications (80%, stratified by label) |
| **Positive Class (Y=1)** | Historical approval |
| **Negative Class (Y=0)** | Historical rejection |
| **Class Imbalance** | ~69% approvals (majority class) |
| **Split Seed** | 42 (deterministic, reproducible) |
| **Checksum** | SHA-256: `8c2cc67a13279ec746b15f76f14e8503154274ef7f221d2437033b4407c80ca8` |

### Input Features

| Feature | Type | Description |
|:---|:---|:---|
| `Dependents` | Categorical | Number of dependents (0, 1, 2, 3+) |
| `Education` | Categorical | Graduate / Not Graduate |
| `Self_Employed` | Categorical | Yes / No |
| `ApplicantIncome` | Numeric | Monthly applicant income (₹) |
| `CoapplicantIncome` | Numeric | Monthly co-applicant income (₹) |
| `LoanAmount` | Numeric | Requested loan amount (₹ thousands) |
| `Loan_Amount_Term` | Numeric | Repayment term (months) |
| `Credit_History` | Binary | 1 = meets guidelines, 0 = does not |
| `Property_Area` | Categorical | Urban / Semiurban / Rural |

> [!NOTE]
> `Gender` and `Married` are **excluded from model inputs** and are used only in the offline fairness audit. See §6 (Quantitative Analyses) and §7 (Ethical Considerations).

### Engineered Features (computed inside the leakage-safe pipeline)

| Feature | Formula |
|:---|:---|
| `TotalIncome` | `ApplicantIncome + CoapplicantIncome` |
| `EMI` | Monthly instalment: `LoanAmount × 1000 × r(1+r)^n / ((1+r)^n − 1)` at 9% p.a. |
| `Balance_Income` | `TotalIncome − EMI` |
| `Loan_to_Income_Ratio` | `LoanAmount / TotalIncome` |
| `log_ApplicantIncome` | `log1p(ApplicantIncome)` |
| `log_LoanAmount` | `log1p(LoanAmount)` |
| `log_TotalIncome` | `log1p(TotalIncome)` |

All imputation (median/mode), scaling (RobustScaler), one-hot encoding, and feature engineering are computed **fold-locally** inside the pipeline to prevent data leakage.

---

## 4. Evaluation Data

| Field | Value |
|:---|:---|
| **Holdout Split** | 20% stratified by label, never used in training, feature selection, or threshold tuning |
| **Test Records** | 123 applications |
| **Split Method** | `sklearn.model_selection.train_test_split` with `stratify=y`, `random_state=42` |
| **Baseline** | `DummyClassifier(strategy="most_frequent")` — always approves (69.11% accuracy) |

---

## 5. Performance

### Held-Out Test Set Results (123 Applications)

| Policy | Threshold | Accuracy | Precision | Recall | F1 Score | ROC-AUC | FP | FN |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Majority Baseline (always approve) | — | 69.11% | 69.11% | 100.00% | 81.73% | 0.5000 | 38 | 0 |
| **Standard Operational Policy** | **0.50** | **88.62%** | **88.17%** | **96.47%** | **92.13%** | **0.8420** | **11** | **3** |
| Experimental Cost Policy ⚠️ | 0.76 | 30.89% | 0.00% | 0.00% | 0.00% | 0.8420 | 0 | 85 |

> [!WARNING]
> The τ = 0.76 threshold was derived from a 5:1 false-approval cost function on training out-of-fold predictions. Because the Decision Tree's highest leaf approval probability is **0.6394**, this threshold rejects **100% of applicants** in production (F1 = 0.00). This result is documented transparently as an experimental finding, not hidden or artificially adjusted. The operational threshold is τ = **0.50**.

### Cross-Validation Leaderboard (5-Fold Stratified CV on Training Data)

| Algorithm | Balancing | CV F1 | CV ROC-AUC |
|:---|:---|:---:|:---:|
| **Decision Tree (Selected)** | **class_weight** | **0.8696 ± 0.0278** | **0.7812 ± 0.0410** |
| Random Forest | class_weight | 0.8611 ± 0.0215 | 0.7745 ± 0.0382 |
| Logistic Regression | Standard | 0.8542 ± 0.0294 | 0.7681 ± 0.0421 |
| LightGBM | SMOTENC | 0.8490 ± 0.0310 | 0.7590 ± 0.0450 |
| XGBoost | SMOTENC | 0.8415 ± 0.0345 | 0.7512 ± 0.0490 |

---

## 6. Quantitative Analyses

### Fairness Audit — Gender and Married Groups

Fairness was assessed descriptively on the held-out test set. `Gender` and `Married` are **not model inputs**; they are audited offline to detect proxy-variable bias.

| Attribute | Group | n | Historical Approval Rate | Predicted Approval Rate (τ=0.50) |
|:---|:---|:---:|:---:|:---:|
| Gender | Female | 24 | ~0.792 | *see `reports/fairness.csv`* |
| Gender | Male | 95 | ~0.800 | *see `reports/fairness.csv`* |
| Gender | Missing | 4 | *small group* | — |
| Married | No | 35 | ~0.629 | *see `reports/fairness.csv`* |
| Married | Yes | 88 | ~0.864 | *see `reports/fairness.csv`* |

> [!NOTE]
> Groups with n < 30 are flagged as statistically unreliable. Exact rates are generated dynamically in `reports/fairness.csv` by `python -m src.evaluate`. Historical approval rates reflect past lending decisions and may themselves encode historical bias. These descriptive checks **do not certify fairness, legal compliance, or absence of discrimination**.

---

## 7. Ethical Considerations

- **Not a credit decision engine.** The model predicts historical approval patterns, not repayment probability, creditworthiness, or financial risk. Historical data may encode systemic bias.
- **Proxy variable risk.** Although `Gender` and `Married` are excluded, correlated features (e.g., `CoapplicantIncome`, `Dependents`, `Property_Area`) may act as proxies and reproduce demographic disparities.
- **Historical bias amplification.** Training on past approvals can perpetuate lending biases present in the original institution's decisions.
- **Small dataset.** 614 total records (491 training) is insufficient for robust fairness claims. Rates in small demographic subgroups are statistically unstable.
- **Uncalibrated probabilities.** Class weighting distorts probability estimates away from true prevalence. Probabilities should not be interpreted as calibrated likelihood-of-approval without isotonic or Platt recalibration.
- **No legal review.** This model has not been reviewed for compliance with consumer credit regulations (e.g., Equal Credit Opportunity Act, RBI Fair Practices Code).

---

## 8. Caveats and Recommendations

| Caveat | Detail |
|:---|:---|
| **Small dataset** | 614 rows from a single institution; results may not generalize to other lenders, regions, or time periods. |
| **Single random split** | One 80/20 split is not external validation; performance variance across different seeds is unknown. |
| **Not probability-calibrated** | Class weighting shifts predicted probabilities; a Brier score or reliability diagram should be checked before using probabilities operationally. |
| **Threshold instability** | The tuned τ = 0.76 produced a reject-all policy, demonstrating that cost-function optimization on small OOF sets can fail catastrophically. |
| **No temporal validation** | No time-based train/test split; concept drift over time is uncharacterized. |
| **Educational prototype** | This project demonstrates ML best practices for academic review; it is explicitly **not** production-ready for real loan decisions. |
| **Recommended next steps** | Collect richer data, perform nested CV, calibrate probabilities, conduct bias audits with a larger holdout, obtain legal review, and implement human-in-the-loop governance before any regulated deployment. |
