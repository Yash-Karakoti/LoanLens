"""Check fold boundaries, resampling semantics and threshold costs."""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate

from src.common import ROOT, split_data
from src.preprocess import RAW_NUMERIC
from src.train import make_pipeline, tune_threshold


def test_cost_threshold_uses_correct_positive_label() -> None:
    """Y=approval: a false approval is actual N but predicted Y."""
    y = np.array([0, 0, 1, 1])
    p = np.array([.1, .6, .7, .9])
    threshold, table = tune_threshold(y, p)
    assert .6 < threshold <= .7
    assert table.cost.min() == 0
    assert table.loc[np.isclose(table.threshold, .5), "cost"].iloc[0] == 5


def test_cost_search_can_reject_probability_one() -> None:
    """Reject-all is possible even for an overconfident mistaken classifier."""
    threshold, table = tune_threshold(np.array([0, 1]), np.array([1., .1]))
    assert threshold > 1
    assert table.cost.min() == 1


def test_audit_only_record_is_not_an_application() -> None:
    """Excluded demographic fields cannot bypass the empty-input boundary."""
    from src.predict import predict_frame
    from src.preprocess import INPUT_COLUMNS
    frame = pd.DataFrame([{name: None for name in INPUT_COLUMNS}])
    frame["Gender"] = "Male"
    with pytest.raises(ValueError, match="model input"):
        predict_frame(frame, artifact={})


@pytest.mark.parametrize("strategy", ["class_weight", "SMOTENC"])
def test_cv_imputers_fit_only_fold_training_rows(strategy: str) -> None:
    """Inspect actual fitted fold estimators, not just pipeline structure."""
    if not (ROOT / "data/raw/train.csv").exists():
        pytest.skip("Authentic dataset unavailable")
    x_train, _, y_train, _ = split_data()
    splitter = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    folds = list(splitter.split(x_train, y_train))
    result = cross_validate(make_pipeline(LogisticRegression(max_iter=2000), strategy), x_train, y_train, cv=folds, return_estimator=True, error_score="raise")
    for (fit_indices, validation_indices), estimator in zip(folds, result["estimator"]):
        preprocessing = estimator
        cleaned = preprocessing.named_steps["clean"].transform(x_train.iloc[fit_indices])
        expected = cleaned[RAW_NUMERIC].median().to_numpy()
        actual = preprocessing.named_steps["impute"].named_transformers_["numeric"].statistics_
        np.testing.assert_allclose(actual, expected)
        assert len(estimator.predict(x_train.iloc[validation_indices])) == len(validation_indices)
        if strategy == "SMOTENC":
            sampler = estimator.named_steps["sampler"]
            assert sum(sampler.sampling_strategy_.values()) > 0


def test_prediction_single_and_batch_consistent() -> None:
    """The published artifact agrees for one row and batch inference."""
    if not (ROOT / "models/best_model.joblib").exists():
        pytest.skip("Model not trained yet")
    from src.predict import load_artifact, predict_frame
    x_train, _, _, _ = split_data()
    artifact = load_artifact()
    batch = predict_frame(x_train.iloc[:3], artifact)
    one = predict_frame(x_train.iloc[[0]], artifact)
    assert batch.probability.iloc[0] == pytest.approx(one.probability.iloc[0])
    assert batch.prediction.iloc[0] == one.prediction.iloc[0]
    assert batch.probability.between(0, 1).all()
    flipped = x_train.iloc[:3].copy()
    flipped["Gender"] = "Female"
    flipped["Married"] = "No"
    np.testing.assert_allclose(predict_frame(flipped, artifact).probability, batch.probability)
