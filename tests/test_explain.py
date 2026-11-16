"""Verify explanations against actual fitted-model probabilities."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest

from src.common import ROOT, split_data
from src.explain import build_explainer, explain_single, readable_names
from src.predict import load_artifact, predict_frame


@pytest.fixture
def artifact() -> dict:
    """Use only the genuine trained artifact for explanation integration tests."""
    if not (ROOT / "models/best_model.joblib").exists():
        pytest.skip("Train the authentic-data model before explanation integration tests.")
    return load_artifact()


def test_explanation_matches_prediction_and_adds_up(artifact: dict) -> None:
    """Waterfall contributions must reconstruct the same score used by the app."""
    train_x, _, _, _ = split_data()
    applicant = train_x.iloc[[0]]
    expected = predict_frame(applicant, artifact).iloc[0]
    result = explain_single(applicant.iloc[0].to_dict(), artifact)
    try:
        assert result["prediction"] == expected["prediction"]
        assert result["probability"] == pytest.approx(expected["probability"])
        assert result["base_value"] + np.sum(result["shap_values"]) == pytest.approx(result["probability"], abs=1e-6)
        assert len(result["reasons"]) == 3
        assert all("percentage points" in reason and "training background" in reason for reason in result["reasons"])
        assert len(result["feature_names"]) == len(result["shap_values"])
        assert result["figure"].axes
    finally:
        plt.close(result["figure"])


def test_background_is_training_only_and_labels_match(artifact: dict) -> None:
    """SHAP's baseline must contain no held-out applications or audit features."""
    train_x, test_x, _, _ = split_data()
    _, background = build_explainer(artifact)
    assert set(background.Loan_ID).issubset(set(train_x.Loan_ID))
    assert not set(background.Loan_ID) & set(test_x.Loan_ID)
    names = readable_names(artifact["pipeline"])
    width = artifact["pipeline"][:-1].transform(train_x.iloc[[0]]).shape[1]
    assert len(names) == width
    assert not any("Gender" in name or "Married" in name for name in names)
