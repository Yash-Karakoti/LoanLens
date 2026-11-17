"""Shared upload, export and score-support helpers for both user interfaces."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any

import pandas as pd


def neutralize_formula(value: object) -> object:
    """Keep untrusted text from becoming a spreadsheet formula."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def csv_download(frame: pd.DataFrame) -> bytes:
    """Encode CSV while neutralizing formulas in text cells and headers."""
    safe = frame.copy()
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(neutralize_formula)
    safe.columns = [neutralize_formula(column) for column in safe.columns]
    return safe.to_csv(index=False).encode("utf-8-sig")


def read_upload(content: bytes) -> pd.DataFrame:
    """Read a bounded UTF-8 CSV and reject duplicate headers before pandas."""
    if len(content) > 5 * 1024 * 1024:
        raise ValueError("Upload a CSV smaller than 5 MB.")
    text = content.decode("utf-8-sig")
    header = next(csv.reader(StringIO(text)), None)
    if not header:
        raise ValueError("The CSV has no column header.")
    if len(header) != len(set(header)):
        raise ValueError("Duplicate column names are not allowed.")
    frame = pd.read_csv(StringIO(text), nrows=1001)
    if len(frame) > 1000:
        raise ValueError("Upload at most 1,000 applications at a time.")
    if frame.empty:
        raise ValueError("The CSV has a header but no applications.")
    return frame


def maximum_tree_approval_score(artifact: dict[str, Any]) -> float | None:
    """Bound every possible tree prediction using fitted leaf class weights."""
    model = artifact["pipeline"].named_steps["model"]
    if not hasattr(model, "tree_"):
        return None
    leaf_weights = model.tree_.value[model.tree_.children_left == -1, 0, :]
    approval_column = list(model.classes_).index(1)
    return float((leaf_weights[:, approval_column] / leaf_weights.sum(axis=1)).max())


def emi_calculation(principal_thousands: float, term_months: float, annual_rate_pct: float = 9.0) -> dict:
    """Calculate monthly EMI and return breakdown dict."""
    import numpy as np
    principal = principal_thousands * 1000
    monthly_rate = annual_rate_pct / 100 / 12
    if monthly_rate == 0:
        emi = principal / term_months
    else:
        emi = principal * monthly_rate / (1 - np.power(1 + monthly_rate, -term_months))
    total_payment = emi * term_months
    return {
        "monthly_emi": round(float(emi), 2),
        "total_payment": round(float(total_payment), 2),
        "total_interest": round(float(total_payment - principal), 2),
        "principal": round(float(principal), 2),
    }
