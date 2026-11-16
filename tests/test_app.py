"""Exercise the real Streamlit form and its CSV input boundary."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.app import csv_download, maximum_tree_approval_score, read_upload
from src.predict import load_artifact

ROOT = Path(__file__).resolve().parents[1]


def test_csv_upload_limits_and_empty_file() -> None:
    """Reject empty or oversized batches before invoking the model."""
    with pytest.raises(ValueError, match="no applications"):
        read_upload(b"ApplicantIncome,LoanAmount\n")
    with pytest.raises(ValueError, match="1,000"):
        read_upload(pd.DataFrame({"ApplicantIncome": range(1001)}).to_csv(index=False).encode())
    assert read_upload(b"ApplicantIncome,LoanAmount\n5000,100\n").shape == (1, 2)


def test_csv_download_neutralizes_formulas() -> None:
    """Do not let user-supplied text become a formula when exported."""
    result = csv_download(pd.DataFrame({"Loan_ID": ["=1+1", " @SUM(1)", "safe"], "score": [0.2, 0.3, 0.4]})).decode("utf-8-sig")
    assert "'=1+1" in result
    assert "' @SUM(1)" in result
    assert "safe" in result


def test_csv_upload_rejects_duplicate_headers_before_pandas_renames() -> None:
    """Duplicate raw headers must not become silently renamed input fields."""
    with pytest.raises(ValueError, match="Duplicate column"):
        read_upload(b"\xef\xbb\xbfApplicantIncome,ApplicantIncome\n5000,6000\n")


def test_csv_download_neutralizes_header_formulas() -> None:
    """Column labels are untrusted CSV cells too."""
    result = csv_download(pd.DataFrame({"=SUM(1)": ["safe"], " @name": [1]})).decode("utf-8-sig")
    assert result.splitlines()[0] == "'=SUM(1),' @name"


def test_tree_score_bound_and_saved_threshold_are_inspectable() -> None:
    """The saved failed threshold must remain unchanged and be explained."""
    if not (ROOT / "models" / "best_model.joblib").exists():
        pytest.skip("Train the real model before inspecting its score range.")
    artifact = load_artifact()
    maximum = maximum_tree_approval_score(artifact)
    assert maximum is not None and 0 <= maximum <= 1
    assert artifact["threshold"] > maximum


def test_app_starts_and_predicts() -> None:
    """Submit a labeled test input through Streamlit and inspect its result."""
    app = AppTest.from_file(str(ROOT / "app" / "app.py"), default_timeout=120).run()
    assert not app.exception
    assert app.title[0].value == "Clearer screening. Explainable decisions."
    if not (ROOT / "models" / "best_model.joblib").exists():
        assert "No trained model" in app.info[0].value
        return
    saved_threshold = load_artifact()["threshold"]
    assert app.radio(key="screening_policy").value == "Standard (0.50)"
    assert any("rejects every possible application" in warning.value for warning in app.warning)
    app.number_input(key="income").set_value(5000.0)
    app.number_input(key="co_income").set_value(1000.0)
    app.number_input(key="loan").set_value(120.0)
    app.number_input(key="term").set_value(360.0)
    app.selectbox(key="credit").select("Yes")
    app.selectbox(key="education").select("Graduate")
    app.selectbox(key="dependents").select("0")
    app.selectbox(key="area").select("Urban")
    app.selectbox(key="self_employed").select("No")
    app.button[0].click().run(timeout=120)
    assert not app.exception
    decisions = [metric.value for metric in app.metric if metric.label == "Historical approval suggestion"]
    assert len(decisions) == 1 and decisions[0] in {"Approved", "Rejected"}
    assert any(metric.label == "Active policy threshold" and metric.value == "0.500" for metric in app.metric)
    assert not any("could not be calculated" in warning.value for warning in app.warning)
    assert not any("There is a problem" in error.value for error in app.error)
    assert load_artifact()["threshold"] == saved_threshold
    app.radio(key="screening_policy").set_value(f"Cost scenario ({saved_threshold:.2f})").run()
    assert not any(metric.label == "Historical approval suggestion" for metric in app.metric)
    app.button[0].click().run(timeout=120)
    assert not app.exception
    assert any(metric.label == "Historical approval suggestion" and metric.value == "Rejected" for metric in app.metric)
    assert not any("could not be calculated" in warning.value for warning in app.warning)
    assert load_artifact()["threshold"] == saved_threshold


def test_app_rejects_blank_application() -> None:
    """An entirely blank form should not produce a misleading suggestion."""
    if not (ROOT / "models" / "best_model.joblib").exists():
        pytest.skip("Train the real model before the form integration test.")
    app = AppTest.from_file(str(ROOT / "app" / "app.py"), default_timeout=120).run()
    app.button[0].click().run()
    assert not app.exception
    assert any("at least one" in error.value for error in app.error)


def test_app_rejects_audit_only_application() -> None:
    """Demographic audit fields do not supply any information to the model."""
    if not (ROOT / "models" / "best_model.joblib").exists():
        pytest.skip("Train the real model before the form integration test.")
    app = AppTest.from_file(str(ROOT / "app" / "app.py"), default_timeout=120).run()
    app.selectbox(key="gender").select("Female")
    app.selectbox(key="married").select("Yes")
    app.button[0].click().run()
    assert not app.exception
    assert any("audit fields alone" in error.value for error in app.error)
    assert not any(metric.label == "Historical approval suggestion" for metric in app.metric)
