"""Generate dataset and preprocessing documentation from verified raw observations."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.common import ROOT, load_data, split_data, write_json
from src.preprocess import CATEGORICAL, NUMERIC, RAW_NUMERIC, build_preprocessor

DICTIONARY = {
    "Loan_ID": "Unique application identifier; excluded from predictors.",
    "Gender": "Male/Female; retained for descriptive audit, excluded from predictors.",
    "Married": "Yes/No; retained for descriptive audit, excluded from predictors.",
    "Dependents": "0, 1, 2, or 3+; 3+ becomes numeric 3, a lower bound.",
    "Education": "Graduate or Not Graduate.",
    "Self_Employed": "Yes/No self-employment indicator.",
    "ApplicantIncome": "Applicant income in dataset monetary units; monthly interpretation assumed.",
    "CoapplicantIncome": "Co-applicant income, using the same assumed time/unit basis.",
    "LoanAmount": "Requested principal in thousands of dataset monetary units.",
    "Loan_Amount_Term": "Repayment term in months.",
    "Credit_History": "1/0 indicating whether credit history meets guidelines; not a credit score.",
    "Property_Area": "Urban, Semiurban, or Rural.",
    "Loan_Status": "Historical approval target: Y = 1; N = 0. Not a default/repayment label.",
}


def markdown_table(frame: pd.DataFrame) -> str:
    """Render a small table without adding the optional tabulate dependency."""
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    rows = [[cell(item) for item in frame.columns]]
    rows += [["---"] * len(frame.columns)]
    rows += [[cell(item) for item in row] for row in frame.itertuples(index=False, name=None)]
    return "\n".join("| " + " | ".join(row) + " |" for row in rows)


def main() -> None:
    """Write actual shape, schema, missingness, balance and train-only transform checks."""
    data = load_data()
    source = json.loads((ROOT / "data/raw/source.json").read_text(encoding="utf-8"))
    train_x, test_x, train_y, test_y = split_data(data)
    reports = ROOT / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    schema = pd.DataFrame({
        "column": data.columns,
        "dtype": data.dtypes.astype(str).to_list(),
        "description": [DICTIONARY.get(name, "Additional source column.") for name in data.columns],
    })
    missing = pd.DataFrame({
        "column": data.columns,
        "missing_count": data.isna().sum().to_numpy(),
        "missing_percent": (data.isna().mean() * 100).round(3).to_numpy(),
    })
    balance = data["Loan_Status"].value_counts().rename_axis("Loan_Status").reset_index(name="count")
    balance["percent"] = (100 * balance["count"] / len(data)).round(3)
    schema.to_csv(reports / "data_dictionary.csv", index=False)
    missing.to_csv(reports / "missing_values.csv", index=False)
    balance.to_csv(reports / "class_balance.csv", index=False)

    preprocessor = build_preprocessor()
    train_transformed = preprocessor.fit_transform(train_x, train_y)
    test_transformed = preprocessor.transform(test_x)
    # Inspect the real fitted imputation stage rather than estimating its results.
    clean_train = preprocessor.named_steps["clean"].transform(train_x)
    imputed_train = preprocessor.named_steps["impute"].transform(clean_train)
    clean_test = preprocessor.named_steps["clean"].transform(test_x)
    imputed_test = preprocessor.named_steps["impute"].transform(clean_test)
    checks = pd.DataFrame({
        "column": RAW_NUMERIC + CATEGORICAL,
        "train_before": clean_train.isna().sum().to_numpy(),
        "train_after": imputed_train.isna().sum().to_numpy(),
        "test_before": clean_test.isna().sum().to_numpy(),
        "test_after": imputed_test.isna().sum().to_numpy(),
    })
    checks.to_csv(reports / "preprocessing_missing_values.csv", index=False)
    if not np.isfinite(train_transformed.astype(float)).all() or not np.isfinite(test_transformed.astype(float)).all():
        raise AssertionError("Preprocessing produced non-finite outputs.")
    if checks[["train_after", "test_after"]].to_numpy().sum() != 0:
        raise AssertionError("Imputation left missing values.")
    split_info = {
        "total_rows": len(data), "raw_columns": len(data.columns),
        "train_rows": len(train_x), "test_rows": len(test_x),
        "train_approved": int(train_y.sum()), "test_approved": int(test_y.sum()),
        "train_rejected": int((train_y == 0).sum()), "test_rejected": int((test_y == 0).sum()),
        "seed": 42, "test_fraction": 0.2,
        "duplicate_rows": int(data.duplicated().sum()),
        "duplicate_loan_ids": int(data["Loan_ID"].duplicated().sum()),
        "missing_cells": int(data.isna().sum().sum()),
        "preprocessed_columns_before_one_hot": len(NUMERIC + CATEGORICAL),
        "train_nonfinite_after_transform": int((~np.isfinite(train_transformed.astype(float))).sum()),
        "test_nonfinite_after_transform": int((~np.isfinite(test_transformed.astype(float))).sum()),
    }
    write_json(reports / "dataset_summary.json", split_info)
    dataset_doc = f"""# Dataset collection and audit

Generated by `python -m src.dataset_report` from the verified raw CSV.

## Source and integrity

- Exact requested URL: {source['url']}
- Resolved download URL: {source['resolved_url']}
- Downloaded UTC: {source['downloaded_utc']}
- SHA-256: `{source['sha256']}`
- Download bytes: {source['bytes']}
- Kaggle attempt status: {source['kaggle']}
- License: {source['license']}

Organizer: [Analytics Vidhya Loan Prediction](https://www.analyticsvidhya.com/datahack/contest/practice-problem-loan-prediction-2/).
The raw source is downloaded once and verified by hash on every load. Reports and processed data never overwrite it.

## Observed structure

Raw shape: **{data.shape[0]} rows × {data.shape[1]} columns**.
Exact duplicate rows: **{split_info['duplicate_rows']}**; duplicate Loan_ID values: **{split_info['duplicate_loan_ids']}**.
Missing cells: **{split_info['missing_cells']}**. No missing target is accepted by the loader.

{markdown_table(schema)}

## Missing values before preprocessing

{markdown_table(missing)}

## Class balance

{markdown_table(balance)}

The target records historical decisions, not repayment. Dataset collection dates, sampling process, and authoritative currency metadata are unavailable; representativeness and commercial data rights are unverified.

## Locked raw split

A stratified 80/20 split uses `random_state=42` before fitting any imputer, encoder, scaler or sampler.
Training: **{len(train_x)}** rows ({int(train_y.sum())} approved, {int((train_y == 0).sum())} rejected).
Holdout: **{len(test_x)}** rows ({int(test_y.sum())} approved, {int((test_y == 0).sum())} rejected).
Dataset-wide descriptive counts above do not select model features or hyperparameters. Target-informed EDA uses only the training partition.

Generated evidence: `reports/data_dictionary.csv`, `missing_values.csv`, `class_balance.csv`, `dataset_summary.json`, and `preprocessing_missing_values.csv`.
"""
    (ROOT / "docs/02_dataset.md").write_text(dataset_doc, encoding="utf-8")
    preprocessing_doc = f"""# Preprocessing and leakage prevention

Generated checks: `python -m src.dataset_report`.

1. `split_data` creates the raw stratified train/holdout split before fitting.
2. `CleanInputs` validates columns and values, turns Dependents `3+` into 3, drops Loan_ID, and excludes Gender/Married from prediction. Those demographics remain in raw data for EDA and fairness audits.
3. A `ColumnTransformer` fits median imputation on numeric inputs and mode imputation on categorical inputs. Credit_History is treated as a category. All fit statistics come only from the training fold.
4. `EngineerFeatures` computes TotalIncome, amortized EMI, Balance_Income, Loan_to_Income_Ratio, and log1p versions of income/loan values after imputation. Log transforms reduce skew without deleting outlier applicants. Principal is LoanAmount × 1,000; the assumed annual rate is 9%, divided by 12 for EMI; loan-to-income is principal divided by annual household income. TotalIncome is clipped to at least one only in the ratio denominator to avoid division by zero.
5. Numeric features are standardized and categories ordinal-encoded. In SMOTENC candidates, only training folds are resampled and category identities remain categorical. Class-weight candidates bypass resampling. The model pipeline then one-hot encodes categories before the estimator.

Every fitted stage belongs to the model's pipeline. Cross-validation clones and fits the entire pipeline for each fold. No saved, globally preprocessed array is passed into CV. Held-out rows use `transform`/`predict`, never `fit`. This descriptive reporting fit is separate and is not reused to train or select the model.

## Actual before/after missingness

The same imputer fitted on the **{len(train_x)} training rows** transforms the **{len(test_x)} holdout rows**. Counts below are observed at the imputation stage, before derived columns/scaling. Dropped identifiers/audit fields are excluded from this table.

{markdown_table(checks)}

The preprocessor returned {train_transformed.shape[1]} columns before final one-hot encoding, with **{split_info['train_nonfinite_after_transform']}** non-finite training values and **{split_info['test_nonfinite_after_transform']}** non-finite holdout values. Pytest separately checks fitted-statistic isolation, finiteness, formulas and input validation.

## Limits

Income period/currency and fixed-rate EMI assumptions are recorded in `ASSUMPTIONS.md`. Derived affordability variables are proxies and share information with their source columns. Removing Gender and Married does not remove correlated demographic proxies or prove fairness. Missing fields are imputed, so an explanation may reflect a typical training value rather than a supplied fact; the application should identify missing inputs.
"""
    (ROOT / "docs/03_preprocessing.md").write_text(preprocessing_doc, encoding="utf-8")
    print(f"Dataset report: {data.shape}; split {len(train_x)}/{len(test_x)}; transformed arrays finite.")


if __name__ == "__main__":
    main()
