"""Exercise the website API against the actual frozen project model."""

from __future__ import annotations

import base64
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pandas as pd
import pytest

from src.common import split_data
from src.predict import load_artifact, predict_frame
from src.preprocess import INPUT_COLUMNS
from web import server


@pytest.fixture
def client() -> TestClient:
    """Use the real ASGI application without binding a TCP port."""
    return TestClient(server.app)


@pytest.fixture
def applicant() -> dict:
    """Use a complete real training observation for HTTP inference checks."""
    train, _, _, _ = split_data()
    return server.json_frame(train.dropna(subset=INPUT_COLUMNS).iloc[[0]][INPUT_COLUMNS])[0]


@pytest.mark.parametrize("policy", ["standard", "cost"])
def test_real_prediction_matches_shared_pipeline(client: TestClient, applicant: dict, policy: str) -> None:
    """The API uses the same model and changes only an explicit policy copy."""
    response = client.post("/api/predict", json={"applicant": applicant, "policy": policy, "explain": False})
    assert response.status_code == 200
    result = response.json()
    saved = load_artifact()
    artifact = {**saved, "threshold": .5 if policy == "standard" else saved["threshold"]}
    expected = predict_frame(pd.DataFrame([applicant]), artifact).iloc[0]
    assert result["probability"] == pytest.approx(expected.probability)
    assert result["prediction"] == expected.prediction
    assert result["threshold"] == artifact["threshold"]
    assert result["policy"] == policy and result["explanation"] is None
    assert response.headers["cache-control"] == "no-store"
    assert load_artifact()["threshold"] == saved["threshold"]


def test_real_shap_reconstructs_probability(client: TestClient, applicant: dict) -> None:
    """Return actual additive contributions and a valid generated PNG."""
    response = client.post("/api/predict", json={"applicant": applicant, "explain": True})
    assert response.status_code == 200
    result = response.json()
    explanation = result["explanation"]
    assert len(explanation["reasons"]) == 3
    reconstructed = explanation["base_value"] + sum(row["value"] for row in explanation["contributions"])
    assert reconstructed == pytest.approx(result["probability"], abs=1e-6)
    assert base64.b64decode(explanation["image"].split(",", 1)[1]).startswith(b"\x89PNG\r\n\x1a\n")


def test_missing_explanation_background_is_actionable(client: TestClient, applicant: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """A deployment missing raw background data returns a clear service error."""
    def missing(*args: object, **kwargs: object) -> dict:
        raise FileNotFoundError("Test-only missing background")

    monkeypatch.setattr(server, "explain_single", missing)
    response = client.post("/api/predict", json={"applicant": applicant, "explain": True})
    assert response.status_code == 503
    assert "background data" in response.json()["detail"]


@pytest.mark.parametrize("problem", ["missing_column", "negative_income", "invalid_category", "audit_only", "empty"])
def test_invalid_applications(client: TestClient, applicant: dict, problem: str) -> None:
    """HTTP callers cannot bypass the shared input-validation boundary."""
    if problem == "missing_column":
        applicant.pop("Education")
    elif problem == "negative_income":
        applicant["ApplicantIncome"] = -1
    elif problem == "invalid_category":
        applicant["Property_Area"] = "unknown"
    else:
        applicant = {name: None for name in INPUT_COLUMNS}
        if problem == "audit_only":
            applicant["Gender"] = "Male"
    response = client.post("/api/predict", json={"applicant": applicant, "explain": False})
    assert response.status_code == 422 and "Traceback" not in response.text


def test_schema_and_content_type(client: TestClient, applicant: dict) -> None:
    """Reject malformed JSON, invalid policies and non-JSON posts."""
    assert client.post("/api/predict", content=b"{broken", headers={"content-type": "application/json"}).status_code == 422
    assert client.post("/api/predict", json={"applicant": applicant, "policy": "automatic"}).status_code == 422
    assert client.post("/api/predict", json={"applicant": "not an object"}).status_code == 422
    assert client.post("/api/predict", content=b"text").status_code == 415


def test_body_limit_checks_actual_chunks(client: TestClient) -> None:
    """A missing Content-Length must not bypass received-byte bounds."""
    chunks = (chunk for chunk in [b"x" * server.MAX_BODY_BYTES, b"x"])
    assert client.post("/api/batch", content=chunks, headers={"content-type": "text/csv"}).status_code == 413
    response = client.post("/api/predict", content=b"{}", headers={"content-type": "application/json", "content-length": str(server.MAX_BODY_BYTES + 1)})
    assert response.status_code == 413


def test_real_batch_and_safe_download(client: TestClient, applicant: dict) -> None:
    """Keep real model results and neutralize untrusted export cells/headers."""
    frame = pd.DataFrame([applicant, applicant])
    # Artificial strings here test CSV safety; they are not observed applicant data.
    frame["Loan_ID"] = ["=1+1", "test-export-only"]
    frame["=untrusted_header"] = ["safe", " @SUM(1)"]
    response = client.post("/api/batch", content=frame.to_csv(index=False).encode(), headers={"content-type": "text/csv"})
    assert response.status_code == 200
    result = response.json()
    assert result["summary"]["total"] == len(result["rows"]) == 2
    assert result["summary"]["approved"] + result["summary"]["rejected"] == 2
    assert "'=1+1" in result["csv"] and "'=untrusted_header" in result["csv"] and "' @SUM(1)" in result["csv"]
    assert result["rows"][0]["probability"] == pytest.approx(result["rows"][1]["probability"])


def test_ambiguous_csv_and_invalid_policy(client: TestClient, applicant: dict) -> None:
    """Duplicates and reserved result columns must not be silently overwritten."""
    headers = {"content-type": "text/csv"}
    duplicate = client.post("/api/batch", content=b"ApplicantIncome,ApplicantIncome\n1,2\n", headers=headers)
    assert duplicate.status_code == 422 and "Duplicate column" in duplicate.json()["detail"]
    frame = pd.DataFrame([applicant])
    frame["prediction"] = "old"
    assert client.post("/api/batch", content=frame.to_csv(index=False).encode(), headers=headers).status_code == 422
    assert client.post("/api/batch", content=b"ApplicantIncome\n", headers=headers).status_code == 422
    many = pd.DataFrame({"ApplicantIncome": range(1001)}).to_csv(index=False).encode()
    assert client.post("/api/batch", content=many, headers=headers).status_code == 422
    assert client.post("/api/batch?policy=unknown", content=b"x\n1", headers=headers).status_code == 422
    assert client.post("/api/batch", content=b"x\n1", headers={"content-type": "text/plain"}).status_code == 415


def test_single_and_batch_scores_keep_numerical_precision(client: TestClient, applicant: dict) -> None:
    """Serialization must not truncate the same fitted model score in batch mode."""
    single = client.post("/api/predict", json={"applicant": applicant, "explain": False}).json()
    batch = client.post("/api/batch", content=pd.DataFrame([applicant]).to_csv(index=False).encode(), headers={"content-type": "text/csv"}).json()
    assert abs(single["probability"] - batch["rows"][0]["probability"]) < 1e-14


def test_overview_uses_real_metrics_and_curves(client: TestClient) -> None:
    """Expose report values, descriptive group counts and true held-out curves."""
    response = client.get("/api/overview")
    assert response.status_code == 200
    result = response.json()
    assert result["dataset"]["total_rows"] == 614 and result["metrics"]["n_test"] == 123
    assert result["metrics"]["test_default"]["accuracy"] == pytest.approx(109 / 123)
    assert len(result["comparison"]) == 10 and result["fairness"]
    assert result["model"]["cost_policy_degenerate"] is True
    assert result["model"]["cost_threshold"] > result["model"]["max_approval_score"]
    assert "NaN" not in response.text
    assert len(result["charts"]["roc"]["fpr"]) == len(result["charts"]["roc"]["tpr"])
    assert sum(row["count"] for row in result["charts"]["credit"]) == 491


def test_example_and_template(client: TestClient) -> None:
    """Label the real training example and keep the template empty."""
    example = client.get("/api/example").json()
    train, test, _, _ = split_data()
    assert example["loan_id"] in train.Loan_ID.values and example["loan_id"] not in test.Loan_ID.values
    assert example["source"] == "Real public training-set example"
    assert set(example["applicant"]) == set(INPUT_COLUMNS)
    template = client.get("/api/template")
    assert template.status_code == 200 and template.text.strip().split(",") == INPUT_COLUMNS
    assert len(template.text.splitlines()) == 1


def test_api_docs_describe_the_bounded_request_bodies(client: TestClient) -> None:
    """Manual streaming validation must still expose useful OpenAPI payload schemas."""
    paths = client.get("/api/openapi.json").json()["paths"]
    prediction = paths["/api/predict"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert "applicant" in prediction["required"]
    assert prediction["properties"]["policy"]["enum"] == ["standard", "cost"]
    batch = paths["/api/batch"]["post"]["requestBody"]["content"]["text/csv"]["schema"]
    assert batch == {"type": "string", "format": "binary"}


def test_only_allowlisted_figures_are_public(client: TestClient) -> None:
    """Do not expose raw applicants, model artifacts or arbitrary report files."""
    response = client.get("/api/figures/roc_curve.png")
    assert response.status_code == 200 and response.content.startswith(b"\x89PNG")
    for path in ["/api/figures/metrics.json", "/api/figures/..%2F..%2Fdata%2Fraw%2Ftrain.csv", "/data/raw/train.csv", "/models/best_model.joblib", "/reports/holdout_predictions.csv", "/assets/..%2F..%2Fdata/raw/train.csv"]:
        assert client.get(path).status_code == 404


def test_web_routes_without_model(client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Declared pages refresh correctly and remain available if training is missing."""
    (tmp_path / "index.html").write_text("<!doctype html><title>Test shell</title>", encoding="utf-8")
    monkeypatch.setattr(server, "STATIC_DIRECTORY", tmp_path)
    for path in ["/", "/assessment", "/batch", "/evidence", "/methodology", "/references"]:
        assert client.get(path).status_code == 200
    assert client.get("/not-a-page").status_code == 404

    def unavailable() -> dict:
        raise HTTPException(503, "The trained model is unavailable.")

    monkeypatch.setattr(server, "model_artifact", unavailable)
    assert client.get("/api/health").json() == {"status": "ok", "model_ready": False}
    assert client.get("/").status_code == 200
    assert client.get("/api/overview").status_code == 503
