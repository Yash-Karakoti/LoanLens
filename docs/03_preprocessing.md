# Preprocessing and leakage prevention

Generated checks: `python -m src.dataset_report`.

1. `split_data` creates the raw stratified train/holdout split before fitting.
2. `CleanInputs` validates columns and values, turns Dependents `3+` into 3, drops Loan_ID, and excludes Gender/Married from prediction. Those demographics remain in raw data for EDA and fairness audits.
3. A `ColumnTransformer` fits median imputation on numeric inputs and mode imputation on categorical inputs. Credit_History is treated as a category. All fit statistics come only from the training fold.
4. `EngineerFeatures` computes TotalIncome, amortized EMI, Balance_Income, Loan_to_Income_Ratio, and log1p versions of income/loan values after imputation. Log transforms reduce skew without deleting outlier applicants. Principal is LoanAmount × 1,000; the assumed annual rate is 9%, divided by 12 for EMI; loan-to-income is principal divided by annual household income. TotalIncome is clipped to at least one only in the ratio denominator to avoid division by zero.
5. Numeric features are standardized and categories ordinal-encoded. In SMOTENC candidates, only training folds are resampled and category identities remain categorical. Class-weight candidates bypass resampling. The model pipeline then one-hot encodes categories before the estimator.

Every fitted stage belongs to the model's pipeline. Cross-validation clones and fits the entire pipeline for each fold. No saved, globally preprocessed array is passed into CV. Held-out rows use `transform`/`predict`, never `fit`. This descriptive reporting fit is separate and is not reused to train or select the model.

## Actual before/after missingness

The same imputer fitted on the **491 training rows** transforms the **123 holdout rows**. Counts below are observed at the imputation stage, before derived columns/scaling. Dropped identifiers/audit fields are excluded from this table.

| column | train_before | train_after | test_before | test_after |
| --- | --- | --- | --- | --- |
| Dependents | 8 | 0 | 7 | 0 |
| ApplicantIncome | 0 | 0 | 0 | 0 |
| CoapplicantIncome | 0 | 0 | 0 | 0 |
| LoanAmount | 20 | 0 | 2 | 0 |
| Loan_Amount_Term | 12 | 0 | 2 | 0 |
| Education | 0 | 0 | 0 | 0 |
| Self_Employed | 27 | 0 | 5 | 0 |
| Credit_History | 43 | 0 | 7 | 0 |
| Property_Area | 0 | 0 | 0 | 0 |

The preprocessor returned 17 columns before final one-hot encoding, with **0** non-finite training values and **0** non-finite holdout values. Pytest separately checks fitted-statistic isolation, finiteness, formulas and input validation.

## Limits

Income period/currency and fixed-rate EMI assumptions are recorded in `ASSUMPTIONS.md`. Derived affordability variables are proxies and share information with their source columns. Removing Gender and Married does not remove correlated demographic proxies or prove fairness. Missing fields are imputed, so an explanation may reflect a typical training value rather than a supplied fact; the application should identify missing inputs.
