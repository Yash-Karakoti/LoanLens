"""The reproduction check must detect changed results, not merely finish a refit."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

from src.run_pipeline import compare_snapshots, execute_notebook


@pytest.fixture
def snapshot() -> dict:
    """Small artificial comparator fixture; never reported as experiment results."""
    return {
        "artifact": {"model_name": "test model", "strategy": "class_weight", "threshold": .6, "raw_sha256": "test digest"},
        "metrics": {"test_default": {"f1": .7}, "test_tuned": {"f1": .6}},
        "comparison": [{"model": "test model", "strategy": "class_weight", "cv_f1": .8, "parameters": {"depth": 2}}],
        "holdout": {"Loan_ID": ["test-a", "test-b"], "probability": [.2, .8], "actual": [0, 1]},
    }


def test_identical_snapshots_pass_with_float_tolerance(snapshot: dict) -> None:
    """Ignore only machine-scale numeric differences, not changed experiment choices."""
    after = deepcopy(snapshot)
    after["holdout"]["probability"][0] += 1e-13
    result = compare_snapshots(snapshot, after)
    assert result["matched"] is True
    assert result["max_probability_difference"] == pytest.approx(1e-13, abs=1e-16)


@pytest.mark.parametrize("change", ["metric", "threshold", "cv", "parameters", "ids", "probability", "hash"])
def test_changed_experiment_is_rejected(snapshot: dict, change: str) -> None:
    """Each result category required by the final rebuild is checked explicitly."""
    after = deepcopy(snapshot)
    if change == "metric":
        after["metrics"]["test_tuned"]["f1"] += .01
    elif change == "threshold":
        after["artifact"]["threshold"] += .01
    elif change == "cv":
        after["comparison"][0]["cv_f1"] += .01
    elif change == "parameters":
        after["comparison"][0]["parameters"]["depth"] = 3
    elif change == "ids":
        after["holdout"]["Loan_ID"].reverse()
    elif change == "probability":
        after["holdout"]["probability"][0] += .01
    else:
        after["artifact"]["raw_sha256"] = "changed digest"
    with pytest.raises(ValueError, match="Reproduction mismatch"):
        compare_snapshots(snapshot, after)


def test_nonfinite_metrics_are_rejected(snapshot: dict) -> None:
    """Matching NaNs cannot silently count as reproducible metrics."""
    snapshot["metrics"]["test_default"]["f1"] = float("nan")
    with pytest.raises(ValueError, match="Reproduction mismatch"):
        compare_snapshots(snapshot, deepcopy(snapshot))


def test_notebook_uses_this_interpreter(tmp_path: Path) -> None:
    """Execute one temporary cell and verify the kernel uses the project venv."""
    import nbformat

    path = tmp_path / "kernel_check.ipynb"
    notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("import sys\nprint(sys.executable)")])
    nbformat.write(notebook, path)
    assert execute_notebook(path) == 1
    executed = nbformat.read(path, as_version=4)
    actual = executed.cells[0].outputs[0].text.strip()
    assert Path(actual).resolve() == Path(sys.executable).resolve()
