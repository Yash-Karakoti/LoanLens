"""Compare five algorithms and two imbalance strategies using training-only CV."""

from __future__ import annotations

import importlib.metadata
import json
from typing import Any

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTENC
from imblearn.pipeline import Pipeline
from lightgbm import LGBMClassifier
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, cross_val_predict
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from src.common import ROOT, SEED, file_hash, split_data, write_json
from src.preprocess import CATEGORY_INDICES, build_encoder, build_preprocessor

CV_FOLDS = 5
SEARCH_ITERATIONS = 4
FALSE_APPROVAL_COST = 5
FALSE_REJECTION_COST = 1


class BalancedXGBClassifier(XGBClassifier):
    """XGBoost with balanced sample weights recomputed inside every fit/fold."""

    def fit(self, x: np.ndarray, y: pd.Series, **kwargs: Any) -> BalancedXGBClassifier:
        """Weight classes using only the labels received by this fit call."""
        return super().fit(x, y, sample_weight=compute_sample_weight("balanced", y), **kwargs)


def make_pipeline(model: Any, strategy: str) -> Pipeline:
    """Keep all learned transforms and resampling inside CV's fit boundary."""
    sampler = SMOTENC(categorical_features=CATEGORY_INDICES, random_state=SEED, k_neighbors=3) if strategy == "SMOTENC" else "passthrough"
    return Pipeline(build_preprocessor().steps + [
        ("sampler", sampler),
        ("encode", build_encoder()), ("model", model),
    ])


def candidates(strategy: str) -> dict[str, tuple[Any, dict[str, list]]]:
    """Return modest search spaces that are explainable in a college viva."""
    weight = "balanced" if strategy == "class_weight" else None
    # A stable module path lets a weighted XGBoost winner unpickle in the app.
    from src.train import BalancedXGBClassifier as weighted_xgb
    xgb_type = weighted_xgb if weight else XGBClassifier
    return {
        "Logistic Regression": (
            LogisticRegression(max_iter=3000, class_weight=weight, random_state=SEED),
            {"model__C": [.01, .1, 1., 10., 100.]},
        ),
        "Decision Tree": (
            DecisionTreeClassifier(class_weight=weight, random_state=SEED),
            {"model__max_depth": [2, 3, 5, 8], "model__min_samples_leaf": [5, 10, 20]},
        ),
        "Random Forest": (
            RandomForestClassifier(n_estimators=150, class_weight=weight, n_jobs=1, random_state=SEED),
            {"model__max_depth": [3, 5, 8, None], "model__min_samples_leaf": [2, 5, 10], "model__max_features": ["sqrt", .8]},
        ),
        "XGBoost": (
            xgb_type(n_estimators=120, objective="binary:logistic", eval_metric="logloss", n_jobs=1, random_state=SEED),
            {"model__max_depth": [2, 3, 4], "model__learning_rate": [.03, .07, .1], "model__reg_lambda": [1., 5., 10.]},
        ),
        "LightGBM": (
            LGBMClassifier(n_estimators=120, class_weight=weight, n_jobs=1, verbosity=-1, random_state=SEED, deterministic=True, force_col_wise=True),
            {"model__num_leaves": [4, 8, 15], "model__learning_rate": [.03, .07, .1], "model__min_child_samples": [15, 25, 40]},
        ),
    }


def tune_threshold(y: pd.Series | np.ndarray, probabilities: np.ndarray) -> tuple[float, pd.DataFrame]:
    """Minimize an illustrative asymmetric cost without consulting test labels."""
    rows = []
    # The endpoint also represents reject-all when a model emits probability 1.
    for threshold in np.append(np.linspace(0, 1, 101), np.nextafter(1., 2.)):
        predicted = (probabilities >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
        rows.append({"threshold": float(threshold), "false_approvals": int(fp), "false_rejections": int(fn),
                     "cost": int(FALSE_APPROVAL_COST * fp + FALSE_REJECTION_COST * fn), "true_approvals": int(tp), "true_rejections": int(tn)})
    table = pd.DataFrame(rows)
    # Favor the standard operating point among equal-cost thresholds.
    winner = table.assign(distance=(table.threshold - .5).abs()).sort_values(["cost", "distance", "threshold"]).iloc[0]
    return float(winner.threshold), table


def main() -> None:
    """Search ten candidates, select by CV F1, then tune training OOF threshold."""
    x_train, x_test, y_train, y_test = split_data()
    for folder in ["models", "reports", "data/processed"]:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED)
    scoring = {"f1": "f1", "precision": "precision", "recall": "recall", "roc_auc": "roc_auc", "accuracy": "accuracy"}
    comparisons: list[dict] = []
    fitted: dict[tuple[str, str], Pipeline] = {}
    failed: list[str] = []
    for strategy in ["class_weight", "SMOTENC"]:
        for name, (model, parameters) in candidates(strategy).items():
            print(f"Searching {name} / {strategy} ...", flush=True)
            try:
                search = RandomizedSearchCV(
                    make_pipeline(model, strategy), parameters, n_iter=SEARCH_ITERATIONS,
                    scoring=scoring, refit="f1", cv=cv, random_state=SEED,
                    n_jobs=1, error_score="raise", return_train_score=True,
                )
                search.fit(x_train, y_train)
                best = search.best_index_
                row = {"model": name, "strategy": strategy, "parameters": json.dumps(search.best_params_, sort_keys=True)}
                for metric in scoring:
                    row[f"cv_{metric}"] = float(search.cv_results_[f"mean_test_{metric}"][best])
                    row[f"cv_{metric}_std"] = float(search.cv_results_[f"std_test_{metric}"][best])
                row["cv_train_f1"] = float(search.cv_results_["mean_train_f1"][best])
                comparisons.append(row)
                fitted[(name, strategy)] = search.best_estimator_
                pd.DataFrame(comparisons).to_csv(ROOT / "reports/model_comparison.csv", index=False)
                print(f"CV F1={row['cv_f1']:.6f}; ROC-AUC={row['cv_roc_auc']:.6f}", flush=True)
            except (ValueError, RuntimeError, TypeError) as error:
                message = f"{name}/{strategy}: {type(error).__name__}: {error}"
                failed.append(message)
                print(message, flush=True)
    write_json(ROOT / "reports/training_failures.json", failed)
    if not comparisons:
        raise RuntimeError("Every model candidate failed; inspect reports/training_failures.json.")
    table = pd.DataFrame(comparisons).sort_values(["cv_f1", "cv_roc_auc", "model", "strategy"], ascending=[False, False, True, True])
    table.to_csv(ROOT / "reports/model_comparison.csv", index=False)
    winner = table.iloc[0]
    pipeline = fitted[(winner["model"], winner["strategy"])]
    oof = cross_val_predict(clone(pipeline), x_train, y_train, cv=cv, method="predict_proba", n_jobs=1)[:, 1]
    threshold, costs = tune_threshold(y_train, oof)
    costs.to_csv(ROOT / "reports/threshold_costs.csv", index=False)
    pd.DataFrame({"Loan_ID": x_train.Loan_ID, "actual": y_train, "probability": oof}).to_csv(ROOT / "data/processed/train_oof.csv", index=False)
    artifact = {
        "schema_version": 1, "pipeline": pipeline, "threshold": threshold,
        "model_name": str(winner["model"]), "strategy": str(winner["strategy"]),
        "raw_sha256": file_hash(ROOT / "data/raw/train.csv"), "random_state": SEED,
        "versions": {name: importlib.metadata.version(name) for name in ["scikit-learn", "imbalanced-learn", "xgboost", "lightgbm", "pandas", "numpy", "shap"]},
    }
    joblib.dump(artifact, ROOT / "models/best_model.joblib")
    write_json(ROOT / "models/metadata.json", {key: value for key, value in artifact.items() if key != "pipeline"})
    write_json(ROOT / "data/processed/split_manifest.json", {
        "random_state": SEED, "test_size": .2, "train_ids": x_train.Loan_ID.tolist(),
        "test_ids": x_test.Loan_ID.tolist(), "train_positive": int(y_train.sum()),
        "test_positive": int(y_test.sum()), "raw_sha256": artifact["raw_sha256"],
    })
    print(f"Selected {winner['model']}/{winner['strategy']} using CV only; OOF threshold={threshold:.2f}")


if __name__ == "__main__":
    main()
