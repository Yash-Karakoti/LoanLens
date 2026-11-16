"""Serve LoanLens and its real, memory-only screening API.

Run locally with ``python -m uvicorn web.server:app --host 127.0.0.1 --port 8000``.
Only the static website and explicitly allowed aggregate figures are public.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
from threading import RLock
from typing import Any, Literal

import matplotlib.pyplot as plt
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, ValidationError
from sklearn.metrics import precision_recall_curve, roc_curve
from starlette.concurrency import run_in_threadpool

from src.common import ROOT, split_data
from src.explain import explain_single
from src.interface import csv_download, maximum_tree_approval_score, read_upload
from src.predict import load_artifact, predict_frame
from src.preprocess import CATEGORICAL, INPUT_COLUMNS, RAW_NUMERIC, validate_inputs

STATIC_DIRECTORY = ROOT / "web/static"
MAX_BODY_BYTES = 5 * 1024 * 1024
PLOT_LOCK = RLock()
Policy = Literal["standard", "cost"]
FIGURE_NAMES = {
    "confusion_matrix.png", "confusion_matrix_tuned.png", "roc_curve.png", "pr_curve.png",
    "threshold_cost.png", "shap_summary.png", "shap_waterfall_example.png",
    "eda_01_target.png", "eda_02_income_histograms.png", "eda_03_loan_distribution.png",
    "eda_04_credit_history.png", "eda_05_property_area.png", "eda_06_education.png",
    "eda_07_married.png", "eda_08_self_employed.png", "eda_09_income_boxplots.png",
    "eda_10_correlations.png",
}

app = FastAPI(title="LoanLens screening API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)


@app.middleware("http")
async def response_headers(request: Request, call_next: Any) -> Response:
    """Prevent stored applicant responses and MIME sniffing without opening CORS."""
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


class PredictionRequest(BaseModel):
    """The explicit policy changes a copy, never the saved model experiment."""

    model_config = ConfigDict(extra="forbid")
    applicant: dict[str, Any]
    policy: Policy = "standard"
    explain: bool = True


@lru_cache(maxsize=1)
def _load_model(model_stamp: int) -> dict[str, Any]:
    """Cache only the trusted local artifact, refreshing after retraining."""
    return load_artifact()


def model_artifact() -> dict[str, Any]:
    """Return a model or an actionable service error without filesystem details."""
    try:
        stamp = (ROOT / "models/best_model.joblib").stat().st_mtime_ns
        return _load_model(stamp)
    except (OSError, ValueError, ImportError, KeyError) as error:
        raise HTTPException(503, "The trained model is unavailable. Run the project training pipeline.") from error


def policy_artifact(policy: Policy) -> dict[str, Any]:
    """Resolve a known screening policy without editing the saved artifact."""
    if policy not in {"standard", "cost"}:
        raise HTTPException(422, "Policy must be standard or cost.")
    saved = model_artifact()
    return {**saved, "threshold": .5 if policy == "standard" else saved["threshold"]}


def json_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert dataframe values to strict JSON, with absent values represented by null."""
    return json.loads(frame.to_json(orient="records", double_precision=15))


def report_json(name: str) -> dict[str, Any]:
    """Read a named aggregate report; callers never supply arbitrary filenames."""
    try:
        return json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise HTTPException(503, "Model evaluation reports are unavailable. Run the project pipeline.") from error


async def limited_body(request: Request) -> bytes:
    """Bound bytes actually received, including requests without Content-Length."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_BODY_BYTES or int(content_length) < 0:
                raise HTTPException(413, "Request body must be at most 5 MB.")
        except ValueError as error:
            raise HTTPException(400, "Invalid Content-Length header.") from error
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_BODY_BYTES:
            raise HTTPException(413, "Request body must be at most 5 MB.")
        content.extend(chunk)
    return bytes(content)


def screen_applicant(payload: PredictionRequest) -> dict[str, Any]:
    """Calculate one validated prediction and optional SHAP explanation in memory."""
    artifact = policy_artifact(payload.policy)
    frame = pd.DataFrame([payload.applicant])
    clean = validate_inputs(frame)
    prediction = predict_frame(frame, artifact).iloc[0]
    explanation = None
    if payload.explain:
        # Matplotlib's global figure state is not safe across concurrent requests.
        with PLOT_LOCK:
            figures_before = set(plt.get_fignums())
            try:
                result = explain_single(payload.applicant, artifact)
                image = BytesIO()
                result["figure"].savefig(image, format="png", dpi=130, bbox_inches="tight")
                explanation = {
                    "reasons": result["reasons"], "base_value": result["base_value"],
                    "contributions": [{"feature": name, "value": float(value)} for name, value in zip(result["feature_names"], result["shap_values"])],
                    "image": "data:image/png;base64," + base64.b64encode(image.getvalue()).decode("ascii"),
                }
            except OSError as error:
                raise HTTPException(503, "The explanation background data are unavailable. Restore the verified project data.") from error
            finally:
                for number in set(plt.get_fignums()) - figures_before:
                    plt.close(number)
    return {
        "prediction": str(prediction["prediction"]), "probability": float(prediction["probability"]),
        "threshold": float(prediction["threshold"]), "policy": payload.policy,
        "missing_fields": [name for name in RAW_NUMERIC + CATEGORICAL if pd.isna(clean.iloc[0][name])],
        "explanation": explanation,
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    """Allow hosting health checks even before model artifacts have been installed."""
    try:
        model_artifact()
        ready = True
    except HTTPException:
        ready = False
    return {"status": "ok", "model_ready": ready}


@app.get("/api/overview")
def overview() -> dict[str, Any]:
    """Expose generated aggregate evidence without raw data or artifact downloads."""
    artifact = model_artifact()
    maximum = maximum_tree_approval_score(artifact)
    try:
        comparison = pd.read_csv(ROOT / "reports/model_comparison.csv")
        fairness = pd.read_csv(ROOT / "reports/fairness.csv")
        holdout = pd.read_csv(ROOT / "reports/holdout_predictions.csv")
        credit = pd.read_csv(ROOT / "reports/eda_approval_by_credit_history.csv").rename(columns={"Credit_History": "group"})
        area = pd.read_csv(ROOT / "reports/eda_approval_by_property_area.csv").rename(columns={"Property_Area": "group"})
    except (OSError, ValueError) as error:
        raise HTTPException(503, "Model comparison reports are unavailable. Run the project pipeline.") from error
    fpr, tpr, _ = roc_curve(holdout.actual, holdout.probability)
    precision, recall, _ = precision_recall_curve(holdout.actual, holdout.probability)
    credit["group"] = credit["group"].astype(str)
    area["group"] = area["group"].astype(str)
    return {
        "model": {"name": artifact["model_name"], "strategy": artifact["strategy"],
                  "standard_threshold": .5, "cost_threshold": artifact["threshold"],
                  "max_approval_score": maximum,
                  "cost_policy_degenerate": maximum is not None and artifact["threshold"] > maximum},
        "metrics": report_json("metrics.json"), "dataset": report_json("dataset_summary.json"),
        "comparison": json_frame(comparison), "fairness": json_frame(fairness),
        "shap": report_json("shap_metadata.json"),
        "charts": {"roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
                   "pr": {"precision": precision.tolist(), "recall": recall.tolist()},
                   "credit": json_frame(credit), "area": json_frame(area)},
        "figures": [{"name": name, "url": f"/api/figures/{name}"} for name in sorted(FIGURE_NAMES) if (ROOT / "reports/figures" / name).is_file()],
    }


@app.get("/api/example")
def example() -> dict[str, Any]:
    """Supply a labeled real training row for an honest interactive demonstration."""
    try:
        train, _, _, _ = split_data()
    except (OSError, ValueError) as error:
        raise HTTPException(503, "The public training example is unavailable.") from error
    complete = train.dropna(subset=INPUT_COLUMNS)
    preferred = complete.loc[complete.Credit_History == 1]
    selected = (preferred if not preferred.empty else complete if not complete.empty else train).iloc[[0]]
    return {"applicant": json_frame(selected[INPUT_COLUMNS])[0], "loan_id": str(selected.Loan_ID.iloc[0]), "source": "Real public training-set example"}


@app.post("/api/predict", openapi_extra={
    "requestBody": {"required": True, "content": {
        "application/json": {"schema": PredictionRequest.model_json_schema()},
    }},
})
async def predict(request: Request) -> dict[str, Any]:
    """Accept a bounded JSON application and return the actual fitted-model result."""
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise HTTPException(415, "Send application/json.")
    content = await limited_body(request)
    try:
        payload = PredictionRequest.model_validate_json(content)
    except ValidationError as error:
        raise HTTPException(422, "Provide an applicant object, standard/cost policy, and a boolean explain flag.") from error
    try:
        return await run_in_threadpool(screen_applicant, payload)
    except (ValueError, TypeError, KeyError, OverflowError) as error:
        raise HTTPException(422, str(error)) from error


def screen_batch(content: bytes, policy: Policy) -> dict[str, Any]:
    """Read, validate, predict and encode a CSV without writing uploaded records."""
    frame = read_upload(content)
    reserved = {"prediction", "probability", "threshold"}.intersection(frame.columns)
    if reserved:
        raise ValueError("Remove existing output columns before screening: " + ", ".join(sorted(reserved)))
    artifact = policy_artifact(policy)
    predictions = predict_frame(frame, artifact).reset_index(drop=True)
    output = pd.concat([frame.reset_index(drop=True), predictions], axis=1)
    approved = int(predictions.prediction.eq("Approved").sum())
    return {
        "rows": json_frame(output),
        "summary": {"total": len(output), "approved": approved, "rejected": len(output) - approved,
                    "policy": policy, "threshold": float(artifact["threshold"])},
        "csv": csv_download(output).decode("utf-8-sig"),
    }


@app.post("/api/batch", openapi_extra={
    "requestBody": {"required": True, "content": {
        "text/csv": {"schema": {"type": "string", "format": "binary"}},
    }},
})
async def batch(request: Request, policy: Policy = "standard") -> dict[str, Any]:
    """Accept bounded raw CSV bytes; multipart and files on disk are unnecessary."""
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() not in {"text/csv", "application/octet-stream"}:
        raise HTTPException(415, "Send CSV bytes with Content-Type text/csv.")
    content = await limited_body(request)
    try:
        return await run_in_threadpool(screen_batch, content, policy)
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as error:
        raise HTTPException(422, str(error)) from error


@app.get("/api/template")
def template() -> Response:
    """Download the exact input header without invented applicant data."""
    return Response(
        pd.DataFrame(columns=INPUT_COLUMNS).to_csv(index=False), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="loan_applications_template.csv"'},
    )


@app.get("/api/figures/{name}")
def figure(name: str) -> FileResponse:
    """Serve only known generated aggregate PNGs, never arbitrary report files."""
    path = ROOT / "reports/figures" / name
    if name not in FIGURE_NAMES or not path.is_file():
        raise HTTPException(404, "Figure not found.")
    return FileResponse(path, media_type="image/png")


@app.get("/")
@app.get("/assessment")
@app.get("/batch")
@app.get("/evidence")
@app.get("/methodology")
@app.get("/references")
def website() -> FileResponse:
    """Serve a refreshable website shell only for the declared public routes."""
    index = STATIC_DIRECTORY / "index.html"
    if not index.is_file():
        raise HTTPException(503, "The website assets are not installed.")
    return FileResponse(index)


app.mount("/assets", StaticFiles(directory=STATIC_DIRECTORY, check_dir=False), name="assets")
