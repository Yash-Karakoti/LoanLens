"""Batch analytics helpers for the LoanLens Housing Loan Approval Prediction app."""

from __future__ import annotations

from typing import Any

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd

# Colour palette shared across charts
_APPROVED_COLOR = "#157f83"
_REJECTED_COLOR = "#d17843"


def approval_rate_by_group(
    predictions_df: pd.DataFrame,
    raw_df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """
    Compute approval rate grouped by *column*.

    Parameters
    ----------
    predictions_df:
        Output of predict_frame(); must contain a 'prediction' column with
        values 'Approved' / 'Rejected' and optionally a 'probability' column.
    raw_df:
        The original uploaded DataFrame (same row order as predictions_df).
    column:
        A column name that must exist in raw_df.

    Returns
    -------
    DataFrame with columns [column, 'total', 'approved', 'rejected',
    'approval_rate'] sorted by 'approval_rate' descending.
    Missing values in the grouping column are labelled 'Missing'.
    """
    try:
        combined = raw_df[[column]].copy().reset_index(drop=True)
        combined["prediction"] = predictions_df["prediction"].values
        combined[column] = combined[column].fillna("Missing").astype(str)

        grouped = (
            combined.groupby(column, sort=False)
            .agg(
                total=("prediction", "count"),
                approved=("prediction", lambda s: (s == "Approved").sum()),
            )
            .reset_index()
        )
        grouped["rejected"] = grouped["total"] - grouped["approved"]
        grouped["approval_rate"] = (grouped["approved"] / grouped["total"]).round(4)
        return grouped.sort_values("approval_rate", ascending=False).reset_index(drop=True)
    except Exception:
        # Return an empty frame with the expected schema on any error
        return pd.DataFrame(
            columns=[column, "total", "approved", "rejected", "approval_rate"]
        )


def batch_summary_stats(
    predictions_df: pd.DataFrame,
    raw_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Return a comprehensive summary dict for the batch prediction run.

    Keys
    ----
    total, approved, rejected, approval_rate,
    avg_loan_amount, avg_income, avg_probability,
    by_property_area, by_education, by_credit_history,
    high_confidence_approvals, high_confidence_rejections
    """
    total = len(predictions_df)
    approved = int((predictions_df["prediction"] == "Approved").sum())
    rejected = total - approved
    approval_rate = round(approved / total, 4) if total else 0.0

    # Optional numeric columns from raw_df
    def _avg(col: str) -> float | None:
        try:
            return float(raw_df[col].dropna().mean())
        except Exception:
            return None

    avg_loan_amount = _avg("LoanAmount")
    avg_income = _avg("ApplicantIncome")

    # Probability column (predict_frame may call it 'probability' or 'score')
    prob_col = None
    for cname in ("probability", "score", "prob"):
        if cname in predictions_df.columns:
            prob_col = cname
            break

    avg_probability = 0.0
    high_conf_approvals = 0
    high_conf_rejections = 0
    if prob_col:
        probs = predictions_df[prob_col].dropna()
        avg_probability = round(float(probs.mean()), 4) if len(probs) else 0.0
        approved_mask = predictions_df["prediction"] == "Approved"
        rejected_mask = predictions_df["prediction"] == "Rejected"
        high_conf_approvals = int((predictions_df.loc[approved_mask, prob_col] >= 0.75).sum())
        high_conf_rejections = int((predictions_df.loc[rejected_mask, prob_col] <= 0.25).sum())

    def _group_dicts(col: str) -> list[dict]:
        df = approval_rate_by_group(predictions_df, raw_df, col)
        return df.to_dict(orient="records")

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "approval_rate": approval_rate,
        "avg_loan_amount": avg_loan_amount,
        "avg_income": avg_income,
        "avg_probability": avg_probability,
        "by_property_area": _group_dicts("Property_Area"),
        "by_education": _group_dicts("Education"),
        "by_credit_history": _group_dicts("Credit_History"),
        "high_confidence_approvals": high_conf_approvals,
        "high_confidence_rejections": high_conf_rejections,
    }


def plot_batch_breakdown(
    predictions_df: pd.DataFrame,
    raw_df: pd.DataFrame,
) -> matplotlib.figure.Figure:
    """
    Create a 2×2 figure:
      - Top-left : Approval rate by Property_Area (bar)
      - Top-right: Approval rate by Education (bar)
      - Bottom-left : Approval rate by Credit_History (bar)
      - Bottom-right: Histogram of prediction probabilities coloured by decision
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Batch Prediction Breakdown", fontsize=14, fontweight="bold", y=1.01)

    categorical_charts = [
        (axes[0, 0], "Property_Area", "Approval Rate by Property Area"),
        (axes[0, 1], "Education", "Approval Rate by Education"),
        (axes[1, 0], "Credit_History", "Approval Rate by Credit History"),
    ]

    for ax, col, title in categorical_charts:
        try:
            df = approval_rate_by_group(predictions_df, raw_df, col)
            if df.empty:
                ax.text(0.5, 0.5, f"'{col}' not available", ha="center", va="center")
                ax.set_title(title)
                continue
            bars = ax.bar(
                df[col].astype(str),
                df["approval_rate"] * 100,
                color=_APPROVED_COLOR,
                edgecolor="white",
            )
            # Annotate bars
            for bar, rate in zip(bars, df["approval_rate"]):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1,
                    f"{rate * 100:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )
            ax.set_ylim(0, 115)
            ax.set_ylabel("Approval Rate (%)")
            ax.set_title(title)
            ax.tick_params(axis="x", rotation=15)
        except Exception:
            ax.text(0.5, 0.5, f"Error plotting '{col}'", ha="center", va="center")
            ax.set_title(title)

    # Bottom-right: Probability histogram coloured by decision
    ax_hist = axes[1, 1]
    try:
        prob_col = None
        for cname in ("probability", "score", "prob"):
            if cname in predictions_df.columns:
                prob_col = cname
                break

        if prob_col:
            approved_mask = predictions_df["prediction"] == "Approved"
            rejected_mask = predictions_df["prediction"] == "Rejected"

            ax_hist.hist(
                predictions_df.loc[approved_mask, prob_col].dropna(),
                bins=20,
                color=_APPROVED_COLOR,
                alpha=0.75,
                label="Approved",
                edgecolor="white",
            )
            ax_hist.hist(
                predictions_df.loc[rejected_mask, prob_col].dropna(),
                bins=20,
                color=_REJECTED_COLOR,
                alpha=0.75,
                label="Rejected",
                edgecolor="white",
            )
            ax_hist.set_xlabel("Predicted Probability")
            ax_hist.set_ylabel("Count")
            ax_hist.set_title("Prediction Probability Distribution")
            ax_hist.legend()
        else:
            # Fallback: simple approved/rejected bar
            counts = predictions_df["prediction"].value_counts()
            colors = {
                "Approved": _APPROVED_COLOR,
                "Rejected": _REJECTED_COLOR,
            }
            ax_hist.bar(
                counts.index,
                counts.values,
                color=[colors.get(k, "#aaaaaa") for k in counts.index],
                edgecolor="white",
            )
            ax_hist.set_ylabel("Count")
            ax_hist.set_title("Approval / Rejection Count")
    except Exception:
        ax_hist.text(0.5, 0.5, "Error plotting probability distribution", ha="center", va="center")
        ax_hist.set_title("Prediction Probability Distribution")

    fig.tight_layout()
    return fig
