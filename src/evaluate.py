"""Evaluate the frozen model and training-selected threshold on untouched holdout rows."""

from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay, PrecisionRecallDisplay, RocCurveDisplay,
    accuracy_score, average_precision_score, balanced_accuracy_score,
    brier_score_loss, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)

from src.common import ROOT, file_hash, split_data, write_json
from src.dataset_report import markdown_table
from src.predict import load_artifact
from src.train import FALSE_APPROVAL_COST, FALSE_REJECTION_COST


def metric_summary(y: pd.Series | np.ndarray, probability: np.ndarray, threshold: float = .5) -> dict[str, Any]:
    """Compute approval-positive metrics and explicit historical-decision error costs."""
    actual = np.asarray(y)
    probability = np.asarray(probability, dtype=float)
    if actual.ndim != 1 or probability.shape != actual.shape or not len(actual):
        raise ValueError("Labels and probabilities must be nonempty matching one-dimensional arrays.")
    if not np.isin(actual, [0, 1]).all() or not np.isfinite(probability).all() or not ((0 <= probability) & (probability <= 1)).all():
        raise ValueError("Expected binary labels and finite probabilities between zero and one.")
    actual = actual.astype(int)
    if not 0 <= threshold <= np.nextafter(1., 2.):
        raise ValueError("Threshold must be in [0, 1], or the immediate reject-all endpoint above 1.")
    predicted = (probability >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[0, 1]).ravel()
    both_classes = len(np.unique(actual)) == 2
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(actual, probability)) if both_classes else None,
        "average_precision": float(average_precision_score(actual, probability)) if actual.sum() else None,
        "brier_score": float(brier_score_loss(actual, probability)),
        "balanced_accuracy": float(balanced_accuracy_score(actual, predicted)),
        "macro_f1": float(f1_score(actual, predicted, labels=[0, 1], average="macro", zero_division=0)),
        "rejection_recall": float(tn / (tn + fp)) if tn + fp else None,
        "false_approvals": int(fp), "false_rejections": int(fn),
        "true_approvals": int(tp), "true_rejections": int(tn),
        "cost": int(FALSE_APPROVAL_COST * fp + FALSE_REJECTION_COST * fn),
    }


def fairness_table(frame: pd.DataFrame, y: pd.Series | np.ndarray, probability: np.ndarray, threshold: float) -> pd.DataFrame:
    """Compare actual/predicted group rates, preserving missing labels and denominators."""
    actual = np.asarray(y, dtype=int)
    default = np.asarray(probability) >= .5
    tuned = np.asarray(probability) >= threshold
    if len(frame) != len(actual) or len(default) != len(actual):
        raise ValueError("Group rows, labels and probabilities must have matching lengths.")
    rows: list[dict[str, Any]] = []
    for attribute in ["Gender", "Married"]:
        groups = frame[attribute].astype("string").fillna("Missing").to_numpy()
        for group in sorted(set(groups)):
            mask = groups == group
            labels = actual[mask]
            positives, negatives = int(labels.sum()), int((labels == 0).sum())
            row = {
                "attribute": attribute, "group": str(group), "n": int(mask.sum()),
                "n_actual_approved": positives, "n_actual_rejected": negatives,
                "historical_approval_rate": float(labels.mean()),
                "small_group": bool(mask.sum() < 30),
            }
            for policy, prediction in [("default", default), ("tuned", tuned)]:
                selected = prediction[mask]
                row[f"predicted_approval_rate_{policy}"] = float(selected.mean())
                row[f"tpr_{policy}"] = float(selected[labels == 1].mean()) if positives else None
                row[f"fpr_{policy}"] = float(selected[labels == 0].mean()) if negatives else None
            rows.append(row)
    return pd.DataFrame(rows)


def error_group_table(frame: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    """Describe holdout errors by credit, property and education without selecting changes."""
    rows: list[dict[str, Any]] = []
    for attribute in ["Credit_History", "Property_Area", "Education"]:
        groups = frame[attribute].astype("string").fillna("Missing").to_numpy()
        for group in sorted(set(groups)):
            part = predictions.loc[groups == group]
            row = {"attribute": attribute, "group": str(group), "n": len(part)}
            for policy in ["default", "tuned"]:
                actual = part["actual"].to_numpy()
                predicted = part[f"predicted_{policy}"].to_numpy()
                row[f"error_rate_{policy}"] = float((actual != predicted).mean())
                row[f"false_approvals_{policy}"] = int(((actual == 0) & (predicted == 1)).sum())
                row[f"false_rejections_{policy}"] = int(((actual == 1) & (predicted == 0)).sum())
            rows.append(row)
    return pd.DataFrame(rows)


def save_figures(actual: np.ndarray, probability: np.ndarray, threshold: float) -> None:
    """Render true holdout curves/matrices and the training OOF threshold-cost curve."""
    destination = ROOT / "reports/figures"
    destination.mkdir(parents=True, exist_ok=True)
    for policy, cutoff in [("default", .5), ("tuned", threshold)]:
        figure, axis = plt.subplots(figsize=(6, 5))
        ConfusionMatrixDisplay.from_predictions(actual, probability >= cutoff, labels=[0, 1], display_labels=["Rejected", "Approved"], cmap="Blues", colorbar=False, ax=axis)
        axis.set_title(f"Holdout confusion matrix | {policy}, threshold={cutoff:.2f}")
        figure.tight_layout()
        name = "confusion_matrix.png" if policy == "default" else "confusion_matrix_tuned.png"
        figure.savefig(destination / name, dpi=150)
        plt.close(figure)
    figure, axis = plt.subplots(figsize=(7, 5))
    RocCurveDisplay.from_predictions(actual, probability, name="Frozen selected model", ax=axis)
    axis.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Chance ranking")
    axis.set_title("Holdout ROC curve | historical approval is positive")
    axis.legend()
    figure.tight_layout()
    figure.savefig(destination / "roc_curve.png", dpi=150)
    plt.close(figure)
    figure, axis = plt.subplots(figsize=(7, 5))
    PrecisionRecallDisplay.from_predictions(actual, probability, name="Frozen selected model", ax=axis)
    axis.axhline(actual.mean(), linestyle="--", color="gray", label=f"Holdout approval prevalence ({actual.mean():.3f})")
    axis.set_title("Holdout precision-recall curve")
    axis.legend()
    figure.tight_layout()
    figure.savefig(destination / "pr_curve.png", dpi=150)
    plt.close(figure)
    costs = pd.read_csv(ROOT / "reports/threshold_costs.csv")
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.plot(costs["threshold"], costs["cost"], color="#157f83", label="Training OOF cost")
    axis.axvline(threshold, color="#d17843", label=f"Training-selected threshold {threshold:.2f}")
    axis.axvline(.5, linestyle="--", color="gray", label="Standard threshold 0.5")
    axis.set(xlabel="Approval threshold", ylabel="Scenario cost (5 × false approvals + false rejections)", title="Training OOF threshold selection | no holdout tuning")
    axis.legend()
    figure.tight_layout()
    figure.savefig(destination / "threshold_cost.png", dpi=150)
    plt.close(figure)


def main() -> None:
    """Evaluate without fitting, changing or reselecting the saved application model."""
    artifact = load_artifact()
    if artifact["raw_sha256"] != file_hash(ROOT / "data/raw/train.csv"):
        raise ValueError("Saved model and raw dataset provenance do not match.")
    x_train, x_test, y_train, y_test = split_data()
    model = artifact["pipeline"]
    threshold = float(artifact["threshold"])
    train_probability = model.predict_proba(x_train)[:, 1]
    probability = model.predict_proba(x_test)[:, 1]
    train_metrics = metric_summary(y_train, train_probability)
    default = metric_summary(y_test, probability)
    tuned = metric_summary(y_test, probability, threshold)
    baseline = DummyClassifier(strategy="most_frequent").fit(x_train, y_train)
    baseline_metrics = metric_summary(y_test, baseline.predict_proba(x_test)[:, 1])
    actual = y_test.to_numpy()
    default_prediction, tuned_prediction = (probability >= .5).astype(int), (probability >= threshold).astype(int)
    metrics = {
        "model_name": artifact["model_name"], "strategy": artifact["strategy"],
        "threshold": threshold, "n_train": len(x_train), "n_test": len(x_test),
        "train_default": train_metrics, "test_default": default, "test_tuned": tuned,
        "confusion_matrix": confusion_matrix(actual, default_prediction, labels=[0, 1]).tolist(),
        "confusion_matrix_tuned": confusion_matrix(actual, tuned_prediction, labels=[0, 1]).tolist(),
        "majority_baseline": baseline_metrics,
        "accuracy_gap": train_metrics["accuracy"] - default["accuracy"],
        "f1_gap": train_metrics["f1"] - default["f1"],
    }
    write_json(ROOT / "reports/metrics.json", metrics)
    predictions = pd.DataFrame({
        "Loan_ID": x_test["Loan_ID"].to_numpy(), "actual": actual,
        "probability": probability, "predicted_default": default_prediction,
        "predicted_tuned": tuned_prediction,
        "error_default": actual != default_prediction, "error_tuned": actual != tuned_prediction,
    })
    predictions.to_csv(ROOT / "reports/holdout_predictions.csv", index=False)
    error_rows = predictions["error_default"] | predictions["error_tuned"]
    errors = x_test.reset_index(drop=True).merge(predictions, on="Loan_ID", validate="one_to_one")
    errors.loc[error_rows].to_csv(ROOT / "reports/error_analysis.csv", index=False)
    groups = error_group_table(x_test, predictions)
    groups.to_csv(ROOT / "reports/error_groups.csv", index=False)
    fairness = fairness_table(x_test, actual, probability, threshold)
    fairness.to_csv(ROOT / "reports/fairness.csv", index=False)
    save_figures(actual, probability, threshold)
    comparison = pd.read_csv(ROOT / "reports/model_comparison.csv")
    selected = comparison[(comparison["model"] == artifact["model_name"]) & (comparison["strategy"] == artifact["strategy"])].iloc[0]
    costs = pd.read_csv(ROOT / "reports/threshold_costs.csv")
    oof_selected = costs.iloc[(costs["threshold"] - threshold).abs().argmin()]
    comparison_rows = []
    for name, values in [("Majority baseline / test", baseline_metrics), ("Model / train / 0.5", train_metrics), ("Model / test / 0.5", default), (f"Model / test / {threshold:.2f}", tuned)]:
        comparison_rows.append({"policy": name, **{key: round(values[key], 6) if values[key] is not None else "Undefined" for key in ["accuracy", "precision", "recall", "f1", "roc_auc", "balanced_accuracy", "macro_f1", "rejection_recall", "average_precision", "brier_score", "cost"]}})
    doc = f"""# Model evaluation

Generated by `python -m src.evaluate`. The saved model and decision threshold were frozen before this evaluation. No model, feature, parameter or threshold was changed using the holdout.

## Model selection

**Best model: {artifact['model_name']} / {artifact['strategy']} because it ranked first by training five-fold stratified CV approval-class F1, with ROC-AUC as the predefined tie-breaker.** Its selected mean CV F1 is **{selected['cv_f1']:.6f}** (fold standard deviation {selected['cv_f1_std']:.6f}); CV ROC-AUC is **{selected['cv_roc_auc']:.6f}**. Parameters: `{selected['parameters']}`. Best means best under this search and selection criterion, not universally best, best on all metrics, or proven superior statistically.

Each of the five requested algorithms was compared under class weights and SMOTENC with randomized search on training-only folds. The independent final split contains **{len(x_train)} training applications** and **{len(x_test)} holdout applications**. The positive class is historical approval Y=1. Baseline is an actual `DummyClassifier(strategy='most_frequent')` fitted only on training labels.

## Real metric comparison

{markdown_table(pd.DataFrame(comparison_rows))}

Precision, recall and F1 refer to approvals. `macro_f1` weights both classes equally; `rejection_recall` is the fraction of historically rejected cases correctly rejected. Balanced accuracy averages the two class recalls. Average precision summarizes the PR curve. Brier score measures probability squared error (lower is better), but is not a complete calibration validation. The score is a model estimate, not an established real-world probability.

The apparent training minus holdout accuracy gap is **{metrics['accuracy_gap']:.6f}**; the F1 gap is **{metrics['f1_gap']:.6f}**. Apparent training scores are optimistic in-sample measurements. A small/negative gap does not establish generalization, especially with this small holdout. These gaps compare the same standard 0.5 policy.

## Confusion matrices and minority failures

Rows are actual [Rejected, Approved], columns predicted [Rejected, Approved]. At threshold 0.5: `{metrics['confusion_matrix']}`. At the training-selected {threshold:.2f}: `{metrics['confusion_matrix_tuned']}`.

At 0.5 the model makes **{default['false_approvals']} false approvals** and **{default['false_rejections']} false rejections**; it correctly rejects **{default['true_rejections']}** of **{int((actual == 0).sum())}** historical rejections. Approval F1 alone can hide these rejection errors. At the tuned threshold it makes **{tuned['false_approvals']} false approvals** and **{tuned['false_rejections']} false rejections**. Read `error_analysis.csv` for every application wrong under either policy, `holdout_predictions.csv` for all evaluated applications, and `error_groups.csv` for descriptive error rates by credit history, property and education. These diagnoses do not trigger tuning on the holdout.

## Business-cost threshold demonstration

The assumed scenario cost is **{FALSE_APPROVAL_COST} units per false approval** and **{FALSE_REJECTION_COST} per false rejection**. The threshold **{threshold:.2f}** was selected using training out-of-fold probabilities, never holdout labels. Holdout scenario cost is **{default['cost']} at 0.5** and **{tuned['cost']} at {threshold:.2f}**, a change of **{tuned['cost'] - default['cost']:+d} units**. A training-selected threshold can perform worse on unseen rows; the reported values remain as measured. The application uses the training-selected policy, while the standard metrics remain visible for comparison. These costs are assumptions, not actual financial/default losses.

At that selected threshold, training OOF predictions approve **{int(oof_selected['true_approvals'] + oof_selected['false_approvals'])}** of **{len(x_train)}** rows, with scenario cost **{int(oof_selected['cost'])}**. The tuned policy approves **{tuned['true_approvals'] + tuned['false_approvals']}** of **{len(x_test)}** holdout rows. A reject-all result can minimize this assumed cost while failing the practical shortlisting objective; it must not be presented as successful screening. Class weighting changes fitted probability estimates, and the scores have not been recalibrated. A meaningful operating policy needs independently justified costs and further training/validation evidence rather than a threshold changed after seeing this holdout.

Hyperparameters and model family were selected with the same training folds later used to create threshold-tuning out-of-fold predictions. Those OOF predictions therefore retain model-selection optimism; this is not nested CV. Holdout results are final evaluation, not another optimization target.

## Fairness audit

`reports/fairness.csv` reports Gender and Married groups, including Missing, with group size, actual-positive/negative denominators, historical approval rate, predicted approval rates at both thresholds, true-positive rates and false-positive rates. Undefined rates have blank CSV cells, not invented zeros. Groups with n < 30 are flagged as small. **{int(fairness['small_group'].sum())}** of **{len(fairness)}** reported attribute/group rows are flagged; attribute tables overlap because each applicant belongs to one group per attribute.

{markdown_table(fairness[['attribute', 'group', 'n', 'historical_approval_rate', 'predicted_approval_rate_default', 'predicted_approval_rate_tuned', 'small_group']].round(6))}

Gender and Married are excluded from predictors, but correlated variables can still reproduce disparities. Historical approvals can themselves be biased. Small or single-class groups make rates unstable or undefined. These descriptive checks do not certify fairness, legal compliance or absence of discrimination.

## Evidence and limits

Plots: `confusion_matrix.png`, `confusion_matrix_tuned.png`, `roc_curve.png`, `pr_curve.png` and `threshold_cost.png` under `reports/figures`. The cost plot uses training OOF data; ROC/PR curves and matrices use the holdout.

This dataset contains decisions rather than repayment/default outcomes; no conclusion about NPA reduction or verified creditworthiness follows. The collection date, deployment distribution and complete lending policy are unknown. The holdout is small and one random split is not external validation. Substantial production work would require richer consented data, calibrated/validated scores, uncertainty assessment, documented policy and human governance. These are limitations, not unimplemented claims of this college prototype.
"""
    (ROOT / "docs/06_evaluation.md").write_text(doc, encoding="utf-8")
    print(f"Frozen evaluation: {artifact['model_name']}/{artifact['strategy']}; test n={len(x_test)}; F1={default['f1']:.6f}; AUC={default['roc_auc']:.6f}; cost {default['cost']} -> {tuned['cost']}.")


if __name__ == "__main__":
    main()
