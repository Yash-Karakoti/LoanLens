"""One validated prediction function shared by the app, batch mode and tests."""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.common import ROOT
from src.preprocess import CATEGORICAL, RAW_NUMERIC, validate_inputs


def load_artifact() -> dict[str, Any]:
    """Load only this project's trusted local joblib, never an uploaded artifact."""
    artifact = joblib.load(ROOT / "models/best_model.joblib")
    if artifact.get("schema_version") != 1:
        raise ValueError("Unsupported model artifact; retrain with this project version.")
    return artifact


def predict_frame(frame: pd.DataFrame, artifact: dict[str, Any] | None = None) -> pd.DataFrame:
    """Return thresholded historical approval suggestions and raw model scores."""
    clean = validate_inputs(frame)
    if clean[RAW_NUMERIC + CATEGORICAL].isna().all(axis=1).any():
        raise ValueError("Each row must provide at least one model input; audit fields alone are insufficient.")
    artifact = load_artifact() if artifact is None else artifact
    probability = artifact["pipeline"].predict_proba(clean)[:, 1]
    if not np.isfinite(probability).all():
        raise ValueError("Model returned a non-finite score.")
    threshold = artifact["threshold"]
    return pd.DataFrame({
        "prediction": np.where(probability >= threshold, "Approved", "Rejected"),
        "probability": probability, "threshold": threshold,
    }, index=frame.index)
