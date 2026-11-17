"""Learning curves for the best trained model.

Plots training score vs validation score vs training size using F1 scoring
for the approval class (positive class = 1).
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import learning_curve

from src.common import ROOT, SEED, split_data
from src.predict import load_artifact


def main() -> None:
    """Generate and save learning curves for the best pipeline."""
    artifact = load_artifact()
    x_train, _, y_train, _ = split_data()

    pipeline = artifact["pipeline"]

    train_sizes, train_scores, val_scores = learning_curve(
        pipeline,
        x_train,
        y_train,
        cv=5,
        scoring="f1",
        train_sizes=np.linspace(0.1, 1.0, 10),
        random_state=SEED,
        n_jobs=-1,
    )

    train_mean = train_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    val_mean = val_scores.mean(axis=1)
    val_std = val_scores.std(axis=1)

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(train_sizes, train_mean, "o-", color="steelblue", label="Training F1")
    ax.fill_between(
        train_sizes,
        train_mean - train_std,
        train_mean + train_std,
        alpha=0.15,
        color="steelblue",
    )

    ax.plot(train_sizes, val_mean, "s-", color="darkorange", label="Validation F1 (CV)")
    ax.fill_between(
        train_sizes,
        val_mean - val_std,
        val_mean + val_std,
        alpha=0.15,
        color="darkorange",
    )

    ax.set_xlabel("Training set size")
    ax.set_ylabel("F1 score (approval class)")
    ax.set_title("Learning Curves – Loan Approval Model")
    ax.legend(loc="lower right")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    dest = ROOT / "reports/figures"
    dest.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest / "learning_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(
        f"Learning curves saved | final train F1={train_mean[-1]:.4f} | "
        f"final val F1={val_mean[-1]:.4f}"
    )
    print("Saved: reports/figures/learning_curves.png")


if __name__ == "__main__":
    main()
