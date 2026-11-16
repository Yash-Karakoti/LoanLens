"""Streamlit interface for educational, human-reviewed loan screening."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.explain import explain_single
from src.interface import csv_download, maximum_tree_approval_score, read_upload
from src.predict import load_artifact, predict_frame
from src.preprocess import INPUT_COLUMNS


@st.cache_resource(show_spinner=False)
def model_artifact(model_stamp: int) -> dict:
    """Cache the trusted local artifact, refreshing when the model changes."""
    return load_artifact()


def optional_choice(label: str, options: list[str], key: str) -> str | None:
    """Keep an explicit missing category instead of silently choosing one."""
    return st.selectbox(label, options, index=None, placeholder="Not provided", key=key)


def numeric_input(label: str, key: str, minimum: float = 0.0) -> float | None:
    """Collect a numeric field with a visible label and optional missing value."""
    return st.number_input(
        label,
        min_value=minimum,
        value=None,
        step=1.0,
        placeholder="Not provided",
        key=key,
    )


def render_single(artifact: dict) -> None:
    """Render the input form and its last submitted result."""
    form_column, guide_column = st.columns([2.2, 1], gap="large")
    with form_column:
        st.subheader("Application details")
        st.caption("Blank fields use medians or modes learned from training data.")
        with st.form("application", border=True):
            st.markdown("#### Income & loan")
            left, right = st.columns(2)
            with left:
                applicant_income = numeric_input("Applicant monthly income (dataset units)", "income")
                loan_amount = numeric_input("Loan amount (thousands of dataset units)", "loan", 0.001)
            with right:
                coapplicant_income = numeric_input("Co-applicant monthly income (dataset units)", "co_income")
                term = numeric_input("Loan term (months)", "term", 1.0)
            st.divider()
            st.markdown("#### Applicant & property")
            left, right = st.columns(2)
            with left:
                credit = optional_choice("Credit history meets guidelines", ["Yes", "No"], "credit")
                education = optional_choice("Education", ["Graduate", "Not Graduate"], "education")
                dependents = optional_choice("Dependents", ["0", "1", "2", "3+"], "dependents")
            with right:
                area = optional_choice("Property area", ["Urban", "Semiurban", "Rural"], "area")
                employed = optional_choice("Self-employed", ["Yes", "No"], "self_employed")
            with st.expander("Optional audit fields"):
                st.caption("Gender and marital status are excluded from model inputs. They are retained for group audits.")
                left, right = st.columns(2)
                with left:
                    gender = optional_choice("Gender", ["Female", "Male"], "gender")
                with right:
                    married = optional_choice("Married", ["Yes", "No"], "married")
            submitted = st.form_submit_button("Predict approval", type="primary", width="stretch")
        if submitted:
            applicant = {
                "ApplicantIncome": applicant_income,
                "CoapplicantIncome": coapplicant_income,
                "LoanAmount": loan_amount,
                "Loan_Amount_Term": term,
                "Credit_History": {"Yes": 1.0, "No": 0.0}.get(credit),
                "Education": education,
                "Dependents": dependents,
                "Property_Area": area,
                "Self_Employed": employed,
                "Gender": gender,
                "Married": married,
            }
            if all(value is None for name, value in applicant.items() if name not in {"Gender", "Married"}):
                st.session_state.pop("screening_result", None)
                st.error("Enter at least one model application field before predicting; audit fields alone are not enough.")
            else:
                try:
                    frame = pd.DataFrame([applicant])
                    prediction = predict_frame(frame, artifact).iloc[0]
                    st.session_state["screening_result"] = {
                        "prediction": prediction["prediction"],
                        "probability": float(prediction["probability"]),
                        "threshold": float(artifact["threshold"]),
                        "applicant": applicant,
                        "missing": sum(value is None for value in applicant.values()),
                    }
                except (ValueError, TypeError, KeyError) as error:
                    st.session_state.pop("screening_result", None)
                    st.error(f"There is a problem with the application: {error}")
    with guide_column:
        with st.container(border=True):
            st.markdown("#### A decision you can inspect")
            st.write("1. Enter the application details.\n2. Review the model suggestion.\n3. Inspect the reasons and verify the source documents.")
            st.divider()
            st.markdown("**About the score**")
            st.write("The score estimates similarity to historical approvals. It is not a probability of repayment or a bank commitment.")
            st.caption("Loan amount uses thousands; income uses monthly dataset units. Currency was not independently documented.")
        st.info("Educational prototype · A human must review every application.")
    result = st.session_state.get("screening_result")
    if result:
        st.divider()
        st.subheader("Screening result")
        decision, score, cutoff = st.columns([1.5, 1, 1])
        with decision:
            st.metric("Historical approval suggestion", result["prediction"])
        with score:
            st.metric("Approval model score", f"{result['probability']:.1%}")
        with cutoff:
            st.metric("Active policy threshold", f"{result['threshold']:.3f}")
        st.caption("Approved means score ≥ threshold; Rejected means score < threshold. Neither is a final lending decision.")
        if result["missing"]:
            st.warning(f"{result['missing']} fields were not provided. Missing model inputs use training-only imputation; missing audit fields are ignored.")
        st.markdown("### Why this suggestion?")
        try:
            with st.spinner("Calculating model explanations…"):
                explanation = explain_single(result["applicant"], artifact)
            for reason in explanation["reasons"]:
                st.write(f"• {reason}")
            st.pyplot(explanation["figure"], clear_figure=True)
            plt.close(explanation["figure"])
            st.caption("SHAP explains model associations relative to training examples. It does not establish causes, fairness or actions that guarantee approval.")
        except Exception as error:
            st.warning(f"Prediction is available, but its SHAP explanation could not be calculated: {error}")


def render_batch(artifact: dict) -> None:
    """Predict bounded CSV uploads in memory and offer a safe download."""
    st.subheader("Screen a batch")
    st.write("Upload application records with the same column names as the dataset. Use the template to check the format.")
    st.download_button(
        "Download blank CSV template",
        pd.DataFrame(columns=INPUT_COLUMNS).to_csv(index=False).encode("utf-8"),
        "loan_applications_template.csv",
        "text/csv",
    )
    uploaded = st.file_uploader("Application CSV (up to 1,000 rows, 5 MB)", type=["csv"])
    st.caption("Files are processed in memory. The application does not save uploaded applications.")
    if uploaded is not None:
        try:
            frame = read_upload(uploaded.getvalue())
            with st.spinner("Screening applications…"):
                predictions = predict_frame(frame, artifact).reset_index(drop=True)
            output = pd.concat([frame.reset_index(drop=True), predictions], axis=1)
            left, right, other = st.columns(3)
            left.metric("Applications screened", len(predictions))
            right.metric("Approved suggestions", int(predictions["prediction"].eq("Approved").sum()))
            other.metric("Rejected suggestions", int(predictions["prediction"].eq("Rejected").sum()))
            st.dataframe(output, hide_index=True, width="stretch")
            st.download_button("Download screening results", csv_download(output), "loan_screening_results.csv", "text/csv", type="primary")
            st.warning("Batch results require individual human review. Uploaded labels, if present, are not used as model inputs.")
        except (ValueError, TypeError, KeyError, UnicodeError, csv.Error, pd.errors.ParserError) as error:
            st.error(f"There is a problem with the CSV: {error}")


def render_evidence(artifact: dict) -> None:
    """Display only generated evidence; missing reports remain explicit."""
    st.subheader("Model evidence")
    st.caption("These are generated results from the held-out dataset, not claims about live bank applications.")
    metrics_path = ROOT / "reports" / "metrics.json"
    if not metrics_path.exists():
        st.info("Evaluation reports are not available yet. Run the evaluation phase to generate them.")
        return
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    st.write(f"**Selected model:** {metrics.get('model_name', artifact.get('model_name', 'Unknown'))}")
    st.write(f"**Training records:** {metrics['n_train']} · **Held-out records:** {metrics['n_test']}")
    default = metrics["test_default"]
    columns = st.columns(4)
    for column, (key, label) in zip(columns, [("accuracy", "Accuracy"), ("precision", "Precision"), ("recall", "Recall"), ("f1", "F1")]):
        column.metric(label, f"{default[key]:.3f}")
    st.caption("Metrics above use the fixed standard threshold of 0.50, which is the application's default policy. The saved training-selected cost scenario is reported separately and failed the fitted model's score-range check.")
    st.write(f"**ROC-AUC:** {default['roc_auc']:.3f} · **Active application threshold:** {artifact['threshold']:.3f} · **Saved cost threshold:** {metrics['threshold']:.3f}")
    if "test_tuned" in metrics:
        rows = [{"Threshold policy": "Standard 0.50 (app default)", **default}, {"Threshold policy": "Saved cost scenario (failed policy)", **metrics["test_tuned"]}]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    with st.expander("Cross-validation model comparison", expanded=True):
        path = ROOT / "reports" / "model_comparison.csv"
        if path.exists():
            st.dataframe(pd.read_csv(path), hide_index=True, width="stretch")
        else:
            st.info("Model comparison is not available.")
    with st.expander("Fairness audit"):
        st.write("Group-level approval rates can reveal disparities. Small groups, historical bias and proxy variables limit interpretation; this audit does not certify fairness.")
        path = ROOT / "reports" / "fairness.csv"
        if path.exists():
            st.dataframe(pd.read_csv(path), hide_index=True, width="stretch")
        else:
            st.info("Fairness report is not available.")
    summary_path = ROOT / "reports" / "figures" / "shap_summary.png"
    if summary_path.exists():
        st.image(str(summary_path), caption="Global SHAP explanation of the fitted model")
    st.info("Approval labels do not contain repayment outcomes. This project cannot validate default reduction or NPA prevention.")


def main() -> None:
    """Load the trusted model and render the three application workflows."""
    st.set_page_config(page_title="LoanLens · Explainable Loan Screening", page_icon="🏠", layout="wide")
    st.markdown(
        """<style>
        .block-container {max-width:1280px;padding-top:4.5rem;padding-bottom:3rem;}
        h1,h2,h3 {letter-spacing:-0.025em;}
        [data-testid="stSidebar"] {border-right:1px solid #dce3eb;}
        .project-kicker {font-size:.78rem;font-weight:700;letter-spacing:.13em;color:#0f766e;}
        .hero-subtitle {font-size:1.12rem;line-height:1.6;color:#40536b;max-width:760px;}
        [data-testid="stMetric"] {background:white;border:1px solid #dce3eb;border-radius:12px;padding:1rem;}
        button[kind="primary"] {font-weight:650;}
        </style>""",
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown("## 🏠 LoanLens")
        st.caption("EXPLAINABLE LOAN SCREENING")
        st.divider()
        st.markdown("**Workspace**\n\nSingle application\n\nBatch screening\n\nModel evidence")
        st.divider()
        st.markdown("**Built for review**")
        st.caption("Compare model suggestions, understand contributing factors and inspect evaluation evidence.")
        st.warning("For education and human review. Do not use as an autonomous lending decision.")
    st.markdown('<div class="project-kicker">HOUSING LOAN APPROVAL · COLLEGE MAJOR PROJECT</div>', unsafe_allow_html=True)
    st.title("Clearer screening. Explainable decisions.")
    st.markdown('<p class="hero-subtitle">Review a housing loan application, see its historical approval estimate, and understand the factors behind the model suggestion.</p>', unsafe_allow_html=True)
    model_path = ROOT / "models" / "best_model.joblib"
    if not model_path.exists():
        st.info("No trained model found. Run the training pipeline from the project folder, then refresh this page.")
        st.code(r".\.venv\Scripts\python.exe -m src.train", language="powershell")
        return
    try:
        saved_artifact = model_artifact(model_path.stat().st_mtime_ns)
    except Exception as error:
        st.error(f"The local model could not be loaded: {error}")
        st.caption("Use only the trusted model created by this project. Re-run training if the environment or dependencies changed.")
        return
    policy = st.radio(
        "Screening policy",
        ["Standard (0.50)", f"Cost scenario ({saved_artifact['threshold']:.2f})"],
        horizontal=True,
        key="screening_policy",
        help="Standard uses the fixed 0.50 threshold. The optional cost scenario preserves the training-selected threshold for inspection, including its documented failure.",
    )
    artifact = {**saved_artifact, "threshold": 0.5 if policy == "Standard (0.50)" else saved_artifact["threshold"]}
    if st.session_state.get("_active_threshold") != artifact["threshold"]:
        st.session_state.pop("screening_result", None)
        st.session_state["_active_threshold"] = artifact["threshold"]
    maximum_score = maximum_tree_approval_score(saved_artifact)
    if maximum_score is not None and saved_artifact["threshold"] > maximum_score:
        message = (
            f"The saved cost scenario failed: its threshold {saved_artifact['threshold']:.3f} exceeds the fitted tree's maximum possible approval score {maximum_score:.5f}. "
            "It rejects every possible application. This check uses fitted leaf class weights, not held-out outcomes. "
            "Standard (0.50) is the fixed default policy; the cost scenario is retained only for inspecting this failure."
        )
        if policy != "Standard (0.50)":
            st.error(message)
        else:
            st.warning(message)
    with st.container(border=True):
        st.caption(f"MODEL · {artifact.get('model_name', 'Trained classifier')}    |    PROTOCOL · Stratified holdout + training-only preprocessing    |    MODE · Human review")
    single, batch, evidence = st.tabs(["Single application", "Batch screening", "Model evidence"])
    with single:
        render_single(artifact)
    with batch:
        render_batch(artifact)
    with evidence:
        render_evidence(artifact)
    st.divider()
    st.caption("Housing Loan Approval Prediction Using Machine Learning Algorithms · Python · scikit-learn · SHAP · Streamlit")


if __name__ == "__main__":
    main()
