"""Create training-only exploratory plots and an executable notebook."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.common import ROOT, split_data, write_json
from src.dataset_report import markdown_table

FIGURE_NAMES = [
    "eda_01_target.png", "eda_02_income_histograms.png", "eda_03_loan_distribution.png",
    "eda_04_credit_history.png", "eda_05_property_area.png", "eda_06_education.png",
    "eda_07_married.png", "eda_08_self_employed.png", "eda_09_income_boxplots.png",
    "eda_10_correlations.png",
]


def training_frame() -> pd.DataFrame:
    """Return raw training rows and labels, excluding the reserved holdout."""
    train_x, _, train_y, _ = split_data()
    frame = train_x.copy()
    frame["Approved"] = train_y
    frame["Loan_Status"] = train_y.map({0: "Rejected", 1: "Approved"})
    return frame


def approval_by_group(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Keep unknown groups visible and include their actual sample sizes."""
    groups = frame[column].astype("string").fillna("Missing")
    return frame.groupby(groups, sort=True)["Approved"].agg(count="size", approval_rate="mean").reset_index()


def key_insights(frame: pd.DataFrame) -> list[str]:
    """Derive factual descriptive findings from training observations only."""
    approved = int(frame["Approved"].sum())
    credit = approval_by_group(frame, "Credit_History")
    credit_text = "; ".join(
        f"{row.Credit_History}: {row.approval_rate:.1%} approved (n={row.count})"
        for row in credit.itertuples(index=False)
    )
    area = approval_by_group(frame, "Property_Area")
    area_text = "; ".join(
        f"{row.Property_Area}: {row.approval_rate:.1%} (n={row.count})"
        for row in area.itertuples(index=False)
    )
    return [
        f"The training partition contains {len(frame)} applications: {approved} approved ({approved / len(frame):.1%}) and {len(frame) - approved} rejected. An always-approve baseline therefore has {approved / len(frame):.1%} training accuracy.",
        f"Observed credit-history groups: {credit_text}. These are historical label associations, not repayment probabilities.",
        f"Observed approval rates by property area: {area_text}. Group composition may explain part of these differences.",
        f"Applicant income has median {frame['ApplicantIncome'].median():.2f}, mean {frame['ApplicantIncome'].mean():.2f}, and maximum {frame['ApplicantIncome'].max():.2f} dataset units. Log1p features retain these observations while reducing scale differences.",
        f"The training loan amount has median {frame['LoanAmount'].median():.2f} and maximum {frame['LoanAmount'].max():.2f} thousand dataset units, with {int(frame['LoanAmount'].isna().sum())} missing values. Plots omit missing numeric values; fold-local median imputation handles them during modeling.",
        f"Credit_History has {int(frame['Credit_History'].isna().sum())} missing training values; Self_Employed has {int(frame['Self_Employed'].isna().sum())}. Missing groups remain visible in approval-rate plots.",
        "Income and loan distributions and group differences are descriptive. Neither this EDA nor SHAP can establish causal effects, fair treatment, repayment performance or NPA reduction.",
    ]


def generate_figures(frame: pd.DataFrame) -> list[Path]:
    """Save ten readable plots using only raw training rows."""
    destination = ROOT / "reports/figures"
    destination.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", palette=["#157f83", "#d17843"], context="notebook")
    plt.rcParams.update({"axes.titleweight": "bold", "figure.facecolor": "#ffffff"})
    paths: list[Path] = []

    def save(figure: plt.Figure, name: str) -> None:
        figure.suptitle(figure._suptitle.get_text() + f" | Training only (n={len(frame)})" if figure._suptitle else f"Training only (n={len(frame)})", fontsize=12)
        figure.tight_layout()
        path = destination / name
        figure.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(figure)
        paths.append(path)

    figure, axis = plt.subplots(figsize=(7, 4))
    counts = frame["Loan_Status"].value_counts().reindex(["Rejected", "Approved"])
    bars = axis.bar(counts.index, counts.values, color=["#d17843", "#157f83"])
    axis.bar_label(bars, padding=3)
    axis.set(ylabel="Applications", title="Historical target distribution")
    axis.set_ylim(0, counts.max() * 1.15)
    save(figure, FIGURE_NAMES[0])

    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    for axis, column in zip(axes, ["ApplicantIncome", "CoapplicantIncome"]):
        sns.histplot(data=frame, x=column, bins=30, ax=axis)
        axis.set(title=column, xlabel="Income in dataset units", ylabel="Applications")
    figure.suptitle("Income distributions; all nonmissing values retained")
    save(figure, FIGURE_NAMES[1])

    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    sns.histplot(data=frame, x="LoanAmount", bins=30, ax=axes[0])
    sns.boxplot(data=frame, x="Loan_Status", y="LoanAmount", order=["Rejected", "Approved"], ax=axes[1])
    axes[0].set(xlabel="Loan amount (thousand dataset units)", ylabel="Applications")
    axes[1].set(xlabel="Historical outcome", ylabel="Loan amount (thousand dataset units)")
    figure.suptitle("Requested loan distribution and outliers")
    save(figure, FIGURE_NAMES[2])

    for name, column in zip(FIGURE_NAMES[3:8], ["Credit_History", "Property_Area", "Education", "Married", "Self_Employed"]):
        grouped = approval_by_group(frame, column)
        figure, axis = plt.subplots(figsize=(8, 4.5))
        bars = axis.bar(grouped[column].astype(str), grouped["approval_rate"], color="#157f83")
        labels = [f"{rate:.1%}\nn={count}" for rate, count in zip(grouped["approval_rate"], grouped["count"])]
        axis.bar_label(bars, labels=labels, padding=3)
        axis.set(ylim=(0, 1.15), ylabel="Historical approval proportion", xlabel=column, title=f"Approval by {column}")
        axis.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))
        save(figure, name)

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for axis, column in zip(axes, ["ApplicantIncome", "CoapplicantIncome"]):
        sns.boxplot(data=frame, x="Loan_Status", y=column, order=["Rejected", "Approved"], ax=axis)
        axis.set(yscale="symlog", title=column, xlabel="Historical outcome", ylabel="Income (symlog axis; dataset units)")
    figure.suptitle("Income by outcome; symlog includes zero co-applicant income")
    save(figure, FIGURE_NAMES[8])

    columns = ["ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Loan_Amount_Term", "Credit_History", "Approved"]
    figure, axis = plt.subplots(figsize=(9, 6))
    sns.heatmap(frame[columns].corr(), annot=True, fmt=".2f", cmap="vlag", center=0, vmin=-1, vmax=1, ax=axis)
    axis.set_title("Pearson correlations (pairwise nonmissing observations)")
    save(figure, FIGURE_NAMES[9])
    if len(paths) != 10 or any(not path.exists() or path.stat().st_size == 0 for path in paths):
        raise AssertionError("Expected ten non-empty EDA figures.")
    return paths


def write_notebook(insights: list[str]) -> None:
    """Write a plain executable notebook with findings calculated by this run."""
    def cell(kind: str, source: str) -> dict:
        value = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
        if kind == "code":
            value.update({"execution_count": None, "outputs": []})
        return value

    cells = [
        cell("markdown", "# Housing loan screening: exploratory data analysis\n\nThis notebook explores only the locked 80% training partition. The raw file is hash-verified; no imputer, scaler, encoder or sampler is fitted before the split. Missing numeric observations are omitted by plotting functions, while missing categorical groups are shown explicitly. Monetary values use dataset units. This notebook can be run from the project root or notebooks folder.\n"),
        cell("code", "from pathlib import Path\nimport sys\n\nproject_root = Path.cwd()\nif not (project_root / 'src').exists():\n    project_root = project_root.parent\nif not (project_root / 'src').exists():\n    raise RuntimeError('Open this notebook from the project root or notebooks directory.')\nif str(project_root) not in sys.path:\n    sys.path.insert(0, str(project_root))\n\nfrom IPython.display import Image, display\nfrom src.eda import training_frame, generate_figures, key_insights\nframe = training_frame()\nprint(f'Training observations: {len(frame)}; holdout excluded from all EDA.')\ndisplay(frame.drop(columns=['Loan_ID']).head())\nfigure_paths = generate_figures(frame)\n"),
    ]
    for index, name in enumerate(FIGURE_NAMES):
        cells.append(cell("markdown", f"## Figure {index + 1}: {name.removeprefix('eda_').removesuffix('.png').replace('_', ' ')}\n"))
        cells.append(cell("code", f"display(Image(filename=str(figure_paths[{index}]), width=1000))\n"))
    cells.append(cell("code", "# Recalculate the prose evidence if observations change.\nfor insight in key_insights(frame):\n    print(insight + '\\n')\n"))
    cells.append(cell("markdown", "## Key Insights\n\n" + "\n\n".join(f"- {insight}" for insight in insights) + "\n"))
    notebook = {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12"}},
        "nbformat": 4, "nbformat_minor": 4,
    }
    path = ROOT / "notebooks/01_eda.ipynb"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    """Generate figures, factual EDA findings and a reproducible notebook."""
    frame = training_frame()
    paths = generate_figures(frame)
    insights = key_insights(frame)
    write_json(ROOT / "reports/eda_insights.json", {"partition": "training", "rows": len(frame), "figures": [path.name for path in paths], "insights": insights})
    group_tables = []
    for column in ["Credit_History", "Property_Area", "Education", "Married", "Self_Employed"]:
        grouped = approval_by_group(frame, column)
        grouped.to_csv(ROOT / f"reports/eda_approval_by_{column.lower()}.csv", index=False)
        display_table = grouped.copy()
        display_table["approval_rate"] = display_table["approval_rate"].map(lambda rate: f"{rate:.3%}")
        group_tables.append(f"### {column}\n\n{markdown_table(display_table)}")
    doc = f"""# Exploratory data analysis

Generated by `python -m src.eda` from **{len(frame)} raw training observations**. Holdout labels and features do not inform these plots or findings. This EDA is descriptive; it does not fit preprocessing, remove outliers, alter raw data or prove causality.

## Figures

""" + "\n".join(f"{index + 1}. `reports/figures/{path.name}`" for index, path in enumerate(paths)) + "\n\nIncome histograms and loan distributions retain all nonmissing observations, including extreme values. Income boxplots use a symmetric-log axis to include zero. Group plots include missing labels and sample counts. Pearson correlations use pairwise nonmissing observations, so denominators can differ by pair.\n\n## Observed group rates\n\n" + "\n\n".join(group_tables) + "\n\n## Key Insights\n\n" + "\n\n".join(f"- {insight}" for insight in insights) + "\n"
    (ROOT / "docs/04_eda.md").write_text(doc, encoding="utf-8")
    write_notebook(insights)
    print(f"EDA: {len(paths)} training-only figures; notebook and calculated insights written.")


if __name__ == "__main__":
    main()
