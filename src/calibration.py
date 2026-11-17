"""Probability calibration for the best trained model using isotonic regression.

Fits a CalibratedClassifierCV wrapper on training data, computes Brier scores
before and after calibration, plots a reliability diagram, and classifies
predictions into confidence bands.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, CalibrationDisplay
from sklearn.metrics import brier_score_loss

from src.common import ROOT, write_json
from src.predict import load_artifact
from src.common import split_data


def classify_confidence(probs: np.ndarray) -> dict[str, dict[str, int | float]]:
    """Classify probabilities into High / Medium / Low confidence bands."""
    high_mask = (probs >= 0.75) | (probs <= 0.25)
    medium_mask = (~high_mask) & ((probs >= 0.60) | (probs <= 0.40))
    low_mask = ~(high_mask | medium_mask)

    total = len(probs)
    counts = {
        "High": int(high_mask.sum()),
        "Medium": int(medium_mask.sum()),
        "Low": int(low_mask.sum()),
    }
    distribution: dict[str, dict[str, int | float]] = {}
    for band, count in counts.items():
        distribution[band] = {
            "count": count,
            "percentage": round(100.0 * count / total, 2) if total > 0 else 0.0,
        }
    return distribution


def main() -> None:
    """Calibrate the pipeline and save reliability diagram + JSON report."""
    artifact = load_artifact()
    x_train, x_test, y_train, y_test = split_data()

    pipeline = artifact["pipeline"]

    # ── Brier score before calibration ──────────────────────────────────────
    probs_before = pipeline.predict_proba(x_test)[:, 1]
    brier_before = float(brier_score_loss(y_test, probs_before))

    # ── Fit isotonic calibration on training set ─────────────────────────────
    calibrated = CalibratedClassifierCV(pipeline, cv="prefit", method="isotonic")
    calibrated.fit(x_train, y_train)

    # ── Brier score after calibration ────────────────────────────────────────
    probs_after = calibrated.predict_proba(x_test)[:, 1]
    brier_after = float(brier_score_loss(y_test, probs_after))

    improvement_pct = round(100.0 * (brier_before - brier_after) / brier_before, 4) if brier_before > 0 else 0.0

    # ── Reliability diagram ──────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    CalibrationDisplay.from_predictions(
        y_test, probs_before, n_bins=10, ax=axes[0], name="Before calibration"
    )
    axes[0].set_title("Before Calibration")

    CalibrationDisplay.from_predictions(
        y_test, probs_after, n_bins=10, ax=axes[1], name="After calibration (isotonic)"
    )
    axes[1].set_title("After Calibration (Isotonic)")

    fig.suptitle("Reliability Diagram – Loan Approval Model", fontsize=13)
    fig.tight_layout()

    dest = ROOT / "reports/figures"
    dest.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest / "calibration_curve.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # ── Confidence bands ─────────────────────────────────────────────────────
    confidence_distribution = classify_confidence(probs_after)

    # ── Save JSON report ──────────────────────────────────────────────────────
    report = {
        "brier_before": brier_before,
        "brier_after": brier_after,
        "improvement_pct": improvement_pct,
        "confidence_distribution": confidence_distribution,
    }
    write_json(ROOT / "reports/calibration.json", report)

    print(
        f"Calibration complete | Brier before={brier_before:.4f} | "
        f"after={brier_after:.4f} | improvement={improvement_pct:.2f}%"
    )
    print(f"Confidence bands: {confidence_distribution}")
    print(f"Saved: reports/figures/calibration_curve.png, reports/calibration.json")


if __name__ == "__main__":
    main()
