"""Rebuild every generated experiment artifact and optionally verify reproduction."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import math
import platform
import sys
from datetime import datetime, timezone
from numbers import Real
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd

from src.common import ROOT, file_hash, split_data, write_json
from src.predict import load_artifact

TOLERANCE = 1e-12
PHASES = ["download_data", "dataset_report", "eda", "train", "evaluate", "explain"]


def snapshot_results() -> dict[str, Any]:
    """Capture the saved artifact and reports before a new training run replaces them."""
    artifact = load_artifact()
    metrics = json.loads((ROOT / "reports/metrics.json").read_text(encoding="utf-8"))
    comparison = pd.read_csv(ROOT / "reports/model_comparison.csv").sort_values(["model", "strategy"])
    comparison["parameters"] = comparison["parameters"].map(json.loads)
    holdout = pd.read_csv(ROOT / "reports/holdout_predictions.csv")
    _, x_test, _, y_test = split_data()
    if holdout["Loan_ID"].tolist() != x_test["Loan_ID"].tolist():
        raise ValueError("Saved holdout report does not match the fixed split's application IDs.")
    if not np.array_equal(holdout["actual"].to_numpy(), y_test.to_numpy()):
        raise ValueError("Saved holdout labels do not match the fixed split.")
    actual_scores = artifact["pipeline"].predict_proba(x_test)[:, 1]
    if not np.allclose(actual_scores, holdout["probability"], atol=TOLERANCE, rtol=0):
        raise ValueError("Saved artifact predictions do not match the holdout report.")
    raw_sha256 = file_hash(ROOT / "data/raw/train.csv")
    if artifact["raw_sha256"] != raw_sha256:
        raise ValueError("Saved artifact belongs to a different raw dataset.")
    return {
        "artifact": {name: artifact[name] for name in ["schema_version", "model_name", "strategy", "threshold", "raw_sha256"]},
        "raw_sha256": raw_sha256,
        "metrics": metrics,
        "comparison": comparison.to_dict(orient="records"),
        "holdout": holdout.to_dict(orient="list"),
    }


def compare_snapshots(before: dict[str, Any], after: dict[str, Any], tolerance: float = TOLERANCE) -> dict[str, Any]:
    """Reject changed identities/parameters/labels or numeric differences above tolerance."""
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("Reproduction tolerance must be finite and nonnegative.")

    def compare(left: Any, right: Any, path: str) -> None:
        """Walk the small JSON-shaped experiment record with useful failure paths."""
        if isinstance(left, dict) and isinstance(right, dict):
            if left.keys() != right.keys():
                raise ValueError(f"Reproduction mismatch at {path}: dictionary keys changed.")
            for name in left:
                compare(left[name], right[name], f"{path}.{name}")
        elif isinstance(left, list) and isinstance(right, list):
            if len(left) != len(right):
                raise ValueError(f"Reproduction mismatch at {path}: row/column count changed.")
            for index, (old, new) in enumerate(zip(left, right)):
                compare(old, new, f"{path}[{index}]")
        elif isinstance(left, Real) and isinstance(right, Real) and not isinstance(left, bool) and not isinstance(right, bool):
            if not math.isfinite(float(left)) or not math.isfinite(float(right)) or abs(left - right) > tolerance:
                raise ValueError(f"Reproduction mismatch at {path}: {left!r} versus {right!r}.")
        elif type(left) is not type(right) or left != right:
            raise ValueError(f"Reproduction mismatch at {path}: {left!r} versus {right!r}.")

    compare(before, after, "results")
    old_scores = np.asarray(before["holdout"]["probability"], dtype=float)
    new_scores = np.asarray(after["holdout"]["probability"], dtype=float)
    return {
        "matched": True, "tolerance": tolerance,
        "max_probability_difference": float(np.max(np.abs(old_scores - new_scores))) if len(old_scores) else 0.0,
        "holdout_rows_compared": len(old_scores),
        "candidates_compared": len(before["comparison"]),
        "checks": ["artifact model/strategy/threshold", "raw SHA-256", "all reported metrics", "all CV numeric values and parameters", "holdout IDs, labels, scores and decisions"],
    }


def execute_notebook(path: Path | None = None) -> int:
    """Execute every EDA cell in this exact Python interpreter and shut its kernel down."""
    import nbformat
    from jupyter_client import KernelManager
    from nbclient import NotebookClient

    path = ROOT / "notebooks/01_eda.ipynb" if path is None else path
    notebook = nbformat.read(path, as_version=4)
    manager = KernelManager(kernel_name="python3")
    specification = manager.kernel_spec
    if specification is None:
        raise RuntimeError("The installed ipykernel Python kernel is unavailable.")
    # Change the in-memory command only; never modify a user's installed kernelspec.
    specification.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    client = NotebookClient(notebook, km=manager, timeout=180, allow_errors=False)
    client.execute(cwd=str(ROOT), cleanup_kc=True)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    if any(cell.execution_count is None or any(output.output_type == "error" for output in cell.outputs) for cell in code_cells):
        raise RuntimeError("The notebook did not execute all code cells successfully.")
    nbformat.write(notebook, path)
    return len(code_cells)


def main(verify_reproduction: bool | None = None) -> None:
    """Run all experiment phases in order, recording real execution evidence."""
    if verify_reproduction is None:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--verify-reproduction", action="store_true", help="Compare a complete existing experiment with a fresh refit.")
        verify_reproduction = parser.parse_args().verify_reproduction
    before = snapshot_results() if verify_reproduction else None
    if before is not None:
        write_json(ROOT / "reports/reproduction_before.json", before)
    started = perf_counter()
    manifest: dict[str, Any] = {
        "started_utc": datetime.now(timezone.utc).isoformat(), "status": "running",
        "python_executable": sys.executable, "python_version": platform.python_version(),
        "platform": platform.platform(), "verify_reproduction": verify_reproduction,
        "versions": {name: importlib.metadata.version(name) for name in ["pandas", "numpy", "scikit-learn", "imbalanced-learn", "xgboost", "lightgbm", "shap", "streamlit", "nbclient"]},
        "phases": [],
    }
    write_json(ROOT / "reports/run_manifest.json", manifest)
    current_phase = "initialization"
    try:
        for current_phase in PHASES:
            phase_started = perf_counter()
            print(f"Running {current_phase} ...", flush=True)
            importlib.import_module(f"src.{current_phase}").main()
            manifest["phases"].append({"name": current_phase, "status": "passed", "seconds": perf_counter() - phase_started})
            write_json(ROOT / "reports/run_manifest.json", manifest)
        current_phase = "notebook"
        phase_started = perf_counter()
        manifest["notebook_code_cells_executed"] = execute_notebook()
        manifest["phases"].append({"name": current_phase, "status": "passed", "seconds": perf_counter() - phase_started})
        manifest["raw_sha256"] = file_hash(ROOT / "data/raw/train.csv")
        if before is not None:
            current_phase = "reproduction_comparison"
            result = compare_snapshots(before, snapshot_results())
            write_json(ROOT / "reports/reproduction.json", result)
            manifest["reproduction"] = result
        manifest["status"] = "passed"
    except Exception as error:
        manifest["status"] = "failed"
        manifest["failed_phase"] = current_phase
        manifest["error"] = f"{type(error).__name__}: {error}"
        if before is not None:
            write_json(ROOT / "reports/reproduction.json", {"matched": False, "tolerance": TOLERANCE, "failed_phase": current_phase, "error": manifest["error"]})
        raise
    finally:
        manifest["seconds"] = perf_counter() - started
        manifest["completed_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(ROOT / "reports/run_manifest.json", manifest)
    print(f"Whole pipeline passed in {manifest['seconds']:.2f}s; notebook cells={manifest['notebook_code_cells_executed']}", flush=True)


if __name__ == "__main__":
    main()
