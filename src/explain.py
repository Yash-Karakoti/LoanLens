"""Probability-space SHAP explanations using training-only background rows.

SHAP describes the fitted model, not causes or repayment risk. Explanations are
on encoded features: independent masking may combine correlated or one-hot
features unrealistically, so the attributions are descriptive approximations.
"""

from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from matplotlib.figure import Figure

from src.common import ROOT, SEED, split_data, write_json
from src.predict import load_artifact, predict_frame
from src.preprocess import CATEGORICAL, NUMERIC, feature_names

BACKGROUND_ROWS = 30
SUMMARY_ROWS = 60
PERMUTATIONS = 5


def readable_names(pipeline: Any) -> list[str]:
    """Replace ordinal category codes with their fitted original category names."""
    encoded_names = feature_names(pipeline)
    names = [name.replace("_", " ") + " (standardized)" for name in NUMERIC]
    ordinal = pipeline.named_steps["prepare"].named_transformers_["category"]
    encoder = pipeline.named_steps["encode"].named_transformers_["category"]
    for column, originals, codes in zip(CATEGORICAL, ordinal.categories_, encoder.categories_):
        for code in codes:
            category = str(originals[int(code)]) if 0 <= int(code) < len(originals) else "unknown"
            if column == "Credit_History":
                category = {"0": "does not meet guidelines", "1": "meets guidelines"}.get(category, category)
            names.append(f"{column.replace('_', ' ')} = {category} (indicator)")
    if len(names) != len(encoded_names):
        raise ValueError("SHAP labels do not match the final model feature columns.")
    return names


def build_explainer(artifact: dict[str, Any]) -> tuple[shap.PermutationExplainer, pd.DataFrame]:
    """Build a generic explainer with real training examples, never the holdout."""
    x_train, _, _, _ = split_data()
    background = x_train.sample(n=min(BACKGROUND_ROWS, len(x_train)), random_state=SEED)
    pipeline = artifact["pipeline"]
    encoded = np.asarray(pipeline[:-1].transform(background), dtype=float)
    model = pipeline.named_steps["model"]

    def approval_probability(values: np.ndarray) -> np.ndarray:
        """Explain positive-class model probability instead of hard predictions."""
        return model.predict_proba(values)[:, 1]

    explainer = shap.PermutationExplainer(
        approval_probability,
        shap.maskers.Independent(encoded, max_samples=len(encoded)),
        feature_names=readable_names(pipeline),
        seed=SEED,
    )
    return explainer, background


def compute_explanations(
    frame: pd.DataFrame,
    artifact: dict[str, Any],
    explainer: shap.PermutationExplainer,
) -> shap.Explanation:
    """Compute approximate attributions and require probability additivity."""
    encoded = np.asarray(artifact["pipeline"][:-1].transform(frame), dtype=float)
    explanation = explainer(encoded, max_evals=PERMUTATIONS * (2 * encoded.shape[1] + 1), silent=True)
    probabilities = artifact["pipeline"].predict_proba(frame)[:, 1]
    reconstructed = np.asarray(explanation.base_values) + np.asarray(explanation.values).sum(axis=1)
    if not np.allclose(reconstructed, probabilities, atol=1e-6, rtol=1e-6):
        raise ValueError("SHAP additivity failed: explanation does not reconstruct the model probability.")
    return explanation


def plain_english_reasons(explanation: shap.Explanation) -> list[str]:
    """Describe the largest three model associations in percentage points."""
    reasons = []
    values = np.asarray(explanation.values)
    for index in np.argsort(-np.abs(values), kind="stable")[:3]:
        name = str(explanation.feature_names[index])
        contribution = float(values[index])
        direction = "increased" if contribution > 0 else "decreased" if contribution < 0 else "did not change"
        if name.endswith(" (indicator)"):
            state = "present" if float(explanation.data[index]) > .5 else "absent"
            name = name.removesuffix(" (indicator)") + f" indicator ({state})"
        reasons.append(
            f"{name} {direction} the model approval score by {abs(contribution) * 100:.2f} "
            "percentage points relative to the training background."
        )
    return reasons


def explain_single(applicant_dict: dict[str, Any], artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a shared prediction, SHAP waterfall and three descriptive reasons."""
    artifact = load_artifact() if artifact is None else artifact
    frame = pd.DataFrame([applicant_dict])
    prediction = predict_frame(frame, artifact).iloc[0]
    explainer, _ = build_explainer(artifact)
    explanation = compute_explanations(frame, artifact, explainer)[0]
    meaningful = int((np.abs(explanation.values) > 1e-8).sum())
    shap.plots.waterfall(explanation, max_display=min(10, max(4, meaningful + 1)), show=False)
    figure: Figure = plt.gcf()
    figure.suptitle("Why the model gave this approval score", fontsize=12)
    figure.tight_layout()
    return {
        "prediction": str(prediction["prediction"]),
        "probability": float(prediction["probability"]),
        "threshold": float(artifact["threshold"]),
        "figure": figure,
        "reasons": plain_english_reasons(explanation),
        "shap_values": np.asarray(explanation.values),
        "base_value": float(explanation.base_values),
        "feature_names": list(explanation.feature_names),
    }


def main() -> None:
    """Generate an actual global SHAP summary and auditable explanation metadata."""
    artifact = load_artifact()
    x_train, _, _, _ = split_data()
    sample = x_train.sample(n=min(SUMMARY_ROWS, len(x_train)), random_state=SEED + 1)
    explainer, background = build_explainer(artifact)
    explanation = compute_explanations(sample, artifact, explainer)
    destination = ROOT / "reports/figures"
    destination.mkdir(parents=True, exist_ok=True)
    importance = np.abs(np.asarray(explanation.values)).mean(axis=0)
    meaningful = int((importance > 1e-8).sum())
    axes = shap.plots.beeswarm(explanation, max_display=min(15, max(4, meaningful + 1)), show=False, plot_size=(11, 6))
    axes.set_xlabel("SHAP value (change in approval model probability)")
    figure = plt.gcf()
    figure.suptitle("Global SHAP: historical approval model (training sample)", fontsize=12)
    figure.tight_layout()
    figure.savefig(destination / "shap_summary.png", dpi=160, bbox_inches="tight")
    plt.close(figure)
    ranking = sorted(zip(explanation.feature_names, importance), key=lambda item: -item[1])
    probabilities = artifact["pipeline"].predict_proba(sample)[:, 1]
    reconstructed = np.asarray(explanation.base_values) + np.asarray(explanation.values).sum(axis=1)
    metadata = {
        "method": "PermutationExplainer with Independent masker on final encoded features",
        "output_space": "positive-class model probability (not calibrated repayment risk)",
        "background_rows": len(background),
        "summary_rows": len(sample),
        "permutations": PERMUTATIONS,
        "seed": SEED,
        "background_train_ids": background["Loan_ID"].tolist(),
        "summary_train_ids": sample["Loan_ID"].tolist(),
        "max_additivity_error": float(np.max(np.abs(reconstructed - probabilities))),
        "mean_absolute_shap": [{"feature": str(name), "value": float(value)} for name, value in ranking],
        "limitations": [
            "Numeric feature values are standardized; categorical values are one-hot indicators.",
            "Correlated raw and engineered features share attribution; masking can create unrealistic combinations.",
            "Approximate model associations are not causal effects, fairness proof or legal adverse-action reasons.",
        ],
    }
    write_json(ROOT / "reports/shap_metadata.json", metadata)
    single = explain_single(sample.iloc[0].to_dict(), artifact)
    single["figure"].savefig(destination / "shap_waterfall_example.png", dpi=160, bbox_inches="tight")
    plt.close(single["figure"])
    write_json(ROOT / "reports/shap_example.json", {
        "loan_id": str(sample.iloc[0]["Loan_ID"]),
        "prediction": single["prediction"], "probability": single["probability"],
        "threshold": single["threshold"], "base_value": single["base_value"],
        "reasons": single["reasons"],
    })
    print(f"SHAP summary generated from {len(sample)} training rows; background={len(background)}; max additivity error={metadata['max_additivity_error']:.3g}")


if __name__ == "__main__":
    main()
