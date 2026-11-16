"""Fold-local preprocessing and simple, documented financial proxy features."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

INPUT_COLUMNS = [
    "Gender", "Married", "Dependents", "Education", "Self_Employed",
    "ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term",
    "Credit_History", "Property_Area",
]
RAW_NUMERIC = ["Dependents", "ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term"]
CATEGORICAL = ["Education", "Self_Employed", "Credit_History", "Property_Area"]
NUMERIC = RAW_NUMERIC + [
    "TotalIncome", "EMI", "Balance_Income", "Loan_to_Income_Ratio",
    "Log_ApplicantIncome", "Log_CoapplicantIncome", "Log_LoanAmount", "Log_TotalIncome",
]
CATEGORY_INDICES = list(range(len(NUMERIC), len(NUMERIC) + len(CATEGORICAL)))
ANNUAL_INTEREST_RATE = 0.09


def validate_inputs(frame: pd.DataFrame) -> pd.DataFrame:
    """Check external CSV/form input without learning statistics or mutating it."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("Provide at least one applicant row.")
    if frame.columns.duplicated().any():
        raise ValueError("Duplicate column names are not allowed.")
    missing = set(INPUT_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing input columns: {', '.join(sorted(missing))}")
    clean = frame.loc[:, INPUT_COLUMNS].copy()
    clean = clean.where(clean.notna(), np.nan)
    for name in clean.select_dtypes(include=["object", "string"]):
        clean[name] = clean[name].map(lambda value: np.nan if isinstance(value, str) and not value.strip() else value)
    clean["Dependents"] = clean["Dependents"].replace("3+", 3)
    for name in RAW_NUMERIC + ["Credit_History"]:
        converted = pd.to_numeric(clean[name], errors="coerce")
        invalid = (clean[name].notna() & converted.isna()) | (converted.notna() & ~np.isfinite(converted))
        if invalid.any():
            raise ValueError(f"{name} must contain finite numbers or blank values.")
        if converted.dropna().lt(0).any():
            raise ValueError(f"{name} cannot be negative.")
        clean[name] = converted.astype(float)
    for name in ["LoanAmount", "Loan_Amount_Term"]:
        if clean[name].dropna().le(0).any():
            raise ValueError(f"{name} must be greater than zero when provided.")
    if not clean["Dependents"].dropna().isin([0, 1, 2, 3]).all():
        raise ValueError("Dependents must be 0, 1, 2, or 3+ (3 is also accepted).")
    if not clean["Credit_History"].dropna().isin([0, 1]).all():
        raise ValueError("Credit_History must be 0, 1, or blank.")
    categories = {
        "Gender": ["Male", "Female"], "Married": ["Yes", "No"],
        "Education": ["Graduate", "Not Graduate"], "Self_Employed": ["Yes", "No"],
        "Property_Area": ["Rural", "Semiurban", "Urban"],
    }
    for name, allowed in categories.items():
        if not clean[name].dropna().isin(allowed).all():
            raise ValueError(f"{name} must be one of {allowed}, or blank.")
    return clean


class CleanInputs(TransformerMixin, BaseEstimator):
    """Normalize raw values and drop identifiers and demographic audit columns."""

    def fit(self, x: pd.DataFrame, y: pd.Series | None = None) -> CleanInputs:
        """Validate only; no statistics are fitted in this step."""
        validate_inputs(x)
        return self

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        """Return selected numeric and categorical columns as a fresh frame."""
        clean = validate_inputs(x)
        clean["Credit_History"] = clean["Credit_History"].map({0.0: "0", 1.0: "1"})
        return clean[RAW_NUMERIC + CATEGORICAL]


class EngineerFeatures(TransformerMixin, BaseEstimator):
    """Add deterministic financial proxies after fold-local imputation."""

    def fit(self, x: pd.DataFrame, y: pd.Series | None = None) -> EngineerFeatures:
        """Feature formulas do not learn parameters from the dataset."""
        return self

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        """Calculate amortized EMI, income ratios and log transforms."""
        result = x.copy()
        result["TotalIncome"] = result["ApplicantIncome"] + result["CoapplicantIncome"]
        principal = result["LoanAmount"] * 1000
        monthly_rate = ANNUAL_INTEREST_RATE / 12
        # A stable amortization formula avoids overflow for long supplied terms.
        result["EMI"] = principal * monthly_rate / (-np.expm1(-result["Loan_Amount_Term"] * np.log1p(monthly_rate)))
        result["Balance_Income"] = result["TotalIncome"] - result["EMI"]
        result["Loan_to_Income_Ratio"] = principal / (12 * result["TotalIncome"].clip(lower=1))
        for name in ["ApplicantIncome", "CoapplicantIncome", "LoanAmount", "TotalIncome"]:
            result[f"Log_{name}"] = np.log1p(result[name])
        return result


def build_preprocessor() -> Pipeline:
    """Build cloneable, fold-local imputation, engineering and scaling."""
    impute = ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median", keep_empty_features=True), RAW_NUMERIC),
        ("category", SimpleImputer(strategy="most_frequent", keep_empty_features=True), CATEGORICAL),
    ], verbose_feature_names_out=False).set_output(transform="pandas")
    prepare = ColumnTransformer([
        ("numeric", StandardScaler(), NUMERIC),
        ("category", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CATEGORICAL),
    ], verbose_feature_names_out=False)
    return Pipeline([("clean", CleanInputs()), ("impute", impute), ("features", EngineerFeatures()), ("prepare", prepare)])


def build_encoder() -> ColumnTransformer:
    """One-hot encode nominal columns after optional SMOTENC resampling."""
    return ColumnTransformer([
        ("numeric", "passthrough", list(range(len(NUMERIC)))),
        ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORY_INDICES),
    ], verbose_feature_names_out=False)


def feature_names(pipeline: Pipeline) -> list[str]:
    """Return final estimator feature labels for SHAP."""
    return list(pipeline.named_steps["encode"].get_feature_names_out(NUMERIC + CATEGORICAL))
