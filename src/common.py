"""Shared paths, strict raw-data loading, and the single holdout split."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
SEED = 42


def write_json(path: Path, value: Any) -> None:
    """Write readable JSON, rejecting non-finite metrics."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_data() -> pd.DataFrame:
    """Load unchanged raw observations and verify recorded provenance."""
    from src.preprocess import INPUT_COLUMNS, validate_inputs

    path = ROOT / "data/raw/train.csv"
    provenance_path = ROOT / "data/raw/source.json"
    if not path.exists():
        raise FileNotFoundError("Dataset missing. Run: python -m src.download_data")
    if not provenance_path.exists():
        raise ValueError("Raw dataset needs data/raw/source.json provenance before use.")
    source = json.loads(provenance_path.read_text(encoding="utf-8"))
    if file_hash(path) != source["sha256"]:
        raise ValueError("Raw dataset hash changed; restore the original download.")
    data = pd.read_csv(path)
    required = set(INPUT_COLUMNS) | {"Loan_ID", "Loan_Status"}
    if not required.issubset(data.columns):
        raise ValueError(f"Missing dataset columns: {sorted(required - set(data.columns))}")
    if data["Loan_Status"].isna().any() or not data["Loan_Status"].isin(["Y", "N"]).all():
        raise ValueError("Loan_Status must contain only Y and N without missing labels.")
    if data["Loan_ID"].isna().any() or data["Loan_ID"].duplicated().any():
        raise ValueError("Loan_ID must be present and unique.")
    validate_inputs(data.drop(columns="Loan_Status"))
    return data


def split_data(data: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split raw rows before any learned transform; Y=1 is historical approval."""
    data = load_data() if data is None else data
    x = data.drop(columns="Loan_Status")
    y = data["Loan_Status"].map({"N": 0, "Y": 1}).astype(int)
    return train_test_split(x, y, test_size=0.2, stratify=y, random_state=SEED)
