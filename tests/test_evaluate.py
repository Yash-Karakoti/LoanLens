"""Check approval-positive confusion semantics and descriptive subgroup calculations."""

import numpy as np
import pandas as pd
import pytest

from src.evaluate import error_group_table, fairness_table, metric_summary


def test_confusion_counts_and_business_cost() -> None:
    """A false approval is actual rejection, predicted approval; >= includes cutoff."""
    values = metric_summary(np.array([0, 0, 0, 1, 1]), np.array([.1, .6, .5, .2, .9]))
    assert values["true_rejections"] == 1
    assert values["false_approvals"] == 2
    assert values["false_rejections"] == 1
    assert values["true_approvals"] == 1
    assert values["cost"] == 11
    assert values["accuracy"] == pytest.approx(2 / 5)
    assert values["rejection_recall"] == pytest.approx(1 / 3)


def test_group_rates_use_model_predictions_and_keep_missing_groups() -> None:
    """Historical and model selection rates differ; missing/single-class groups persist."""
    frame = pd.DataFrame({"Gender": ["Female", "Female", "Male", None], "Married": ["No", "Yes", "No", None]}, index=[15, 3, 100, 8])
    table = fairness_table(frame, np.array([0, 1, 1, 0]), np.array([.6, .8, .4, .9]), .75)
    female = table[(table.attribute == "Gender") & (table.group == "Female")].iloc[0]
    assert female["n"] == 2
    assert female["historical_approval_rate"] == .5
    assert female["predicted_approval_rate_default"] == 1
    assert female["predicted_approval_rate_tuned"] == .5
    assert female["tpr_default"] == 1
    assert female["fpr_default"] == 1
    assert female["fpr_tuned"] == 0
    missing = table[(table.attribute == "Gender") & (table.group == "Missing")].iloc[0]
    assert missing["n"] == 1
    assert missing["n_actual_approved"] == 0
    assert pd.isna(missing["tpr_default"])
    assert missing["fpr_default"] == 1
    assert missing["small_group"]
    assert table.groupby("attribute")["n"].sum().eq(len(frame)).all()


def test_error_groups_count_each_policy_separately() -> None:
    """One policy can falsely approve while the other falsely rejects a group member."""
    frame = pd.DataFrame({"Credit_History": [1, 1], "Property_Area": ["Urban", "Urban"], "Education": ["Graduate", "Graduate"]})
    predictions = pd.DataFrame({"actual": [0, 1], "predicted_default": [1, 1], "predicted_tuned": [0, 0]})
    table = error_group_table(frame, predictions)
    assert table["n"].eq(2).all()
    assert table["false_approvals_default"].eq(1).all()
    assert table["false_rejections_tuned"].eq(1).all()
    assert table["error_rate_default"].eq(.5).all()


@pytest.mark.parametrize("probability", [np.array([np.nan, .1]), np.array([1.1, .1])])
def test_metrics_reject_non_probability_values(probability: np.ndarray) -> None:
    """Invalid model scores cannot become apparently valid saved metrics."""
    with pytest.raises(ValueError, match="finite probabilities"):
        metric_summary(np.array([0, 1]), probability)
