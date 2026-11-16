"""Artificial fixtures test boundaries; project results use only the raw download."""

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone

from src.common import split_data
from src.preprocess import EngineerFeatures, RAW_NUMERIC, build_preprocessor, validate_inputs


@pytest.fixture
def rows() -> pd.DataFrame:
    """Small artificial test fixture, never used for model training/results."""
    return pd.DataFrame({
        "Gender": ["Male", "Female", None], "Married": ["Yes", "No", None],
        "Dependents": ["3+", "0", None], "Education": ["Graduate", "Not Graduate", "Graduate"],
        "Self_Employed": ["No", np.nan, "Yes"], "ApplicantIncome": [4000., 2000., np.nan],
        "CoapplicantIncome": [1000., 0., np.nan], "LoanAmount": [100., np.nan, 80.],
        "Loan_Amount_Term": [360., 180., np.nan], "Credit_History": [1., 0., np.nan],
        "Property_Area": ["Urban", "Rural", "Semiurban"],
    })


def test_missing_and_three_plus(rows: pd.DataFrame) -> None:
    """Imputation leaves finite numeric features without mutating raw inputs."""
    original = rows.copy(deep=True)
    processor = clone(build_preprocessor())
    result = processor.fit_transform(rows)
    assert np.isfinite(result).all()
    assert result.shape[0] == len(rows)
    assert processor.named_steps["clean"].transform(rows)["Dependents"].iloc[0] == 3
    pd.testing.assert_frame_equal(rows, original)


def test_holdout_does_not_change_fitted_medians(rows: pd.DataFrame) -> None:
    """Transform shifted holdout rows and confirm no imputer refit occurs."""
    processor = build_preprocessor().fit(rows)
    imputer = processor.named_steps["impute"].named_transformers_["numeric"]
    before = imputer.statistics_.copy()
    shifted = rows.copy()
    shifted["ApplicantIncome"] = [999999., np.nan, 888888.]
    result = processor.transform(shifted)
    np.testing.assert_equal(imputer.statistics_, before)
    assert before[RAW_NUMERIC.index("ApplicantIncome")] == 3000
    assert np.isfinite(result).all()


def test_formulas_and_zero_income(rows: pd.DataFrame) -> None:
    """EMI converts thousands correctly and zero income cannot divide by zero."""
    clean = validate_inputs(rows).fillna({"ApplicantIncome": 0, "CoapplicantIncome": 0, "LoanAmount": 100, "Loan_Amount_Term": 360})
    output = EngineerFeatures().transform(clean)
    expected = 100000 * .0075 / (1 - (1.0075) ** -360)
    assert output["EMI"].iloc[0] == pytest.approx(expected)
    assert np.isfinite(output["Loan_to_Income_Ratio"]).all()


@pytest.mark.parametrize("column,value", [("LoanAmount", -1), ("Loan_Amount_Term", 0), ("ApplicantIncome", "bad"), ("ApplicantIncome", float("inf")), ("Credit_History", 2), ("Property_Area", "unknown")])
def test_invalid_inputs(rows: pd.DataFrame, column: str, value: object) -> None:
    """Reject bad values instead of turning them silently into imputations."""
    broken = rows.astype(object)
    broken.loc[0, column] = value
    with pytest.raises(ValueError):
        validate_inputs(broken)


def test_real_split_is_disjoint() -> None:
    """Only this integration check requires the authentic raw download."""
    from src.common import ROOT
    if not (ROOT / "data/raw/train.csv").exists():
        pytest.skip("Authentic dataset unavailable")
    x_train, x_test, y_train, y_test = split_data()
    assert not set(x_train.Loan_ID) & set(x_test.Loan_ID)
    assert len(x_train) + len(x_test) == 614
    assert abs(y_train.mean() - y_test.mean()) < .02
