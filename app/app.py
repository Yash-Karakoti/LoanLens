"""Streamlit interface for educational, human-reviewed loan screening."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.explain import explain_single
from src.interface import csv_download, emi_calculation, maximum_tree_approval_score, read_upload
from src.predict import load_artifact, predict_frame
from src.preprocess import INPUT_COLUMNS

# ── EDA figure captions ──────────────────────────────────────────────────────
EDA_CAPTIONS = {
    "eda_01_target.png": "Target Distribution — Historical approval vs rejection counts in the training set.",
    "eda_02_income_histograms.png": "Income Distributions — Applicant and co-applicant monthly income (all nonmissing values).",
    "eda_03_loan_distribution.png": "Loan Distribution — Requested loan amounts and outlier box plots by outcome.",
    "eda_04_credit_history.png": "Credit History — Historical approval rates by credit-history group.",
    "eda_05_property_area.png": "Property Area — Historical approval rates by Urban / Semiurban / Rural.",
    "eda_06_education.png": "Education — Historical approval rates by Graduate vs Not Graduate.",
    "eda_07_married.png": "Marital Status — Historical approval rates by marital status (audit only).",
    "eda_08_self_employed.png": "Self-Employed — Historical approval rates by employment type.",
    "eda_09_income_boxplots.png": "Income by Outcome — Symlog-axis box plots of income distributions by decision.",
    "eda_10_correlations.png": "Feature Correlations — Pearson correlation heat-map (pairwise nonmissing).",
}


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


def confidence_badge(probability: float) -> None:
    """Render a High / Medium / Low confidence indicator based on score distance."""
    if probability >= 0.75 or probability <= 0.25:
        st.success(f"🟢 **High Confidence** — The model score ({probability:.1%}) is far from the decision boundary.")
    elif probability >= 0.60 or probability <= 0.40:
        st.warning(f"🟡 **Medium Confidence** — The model score ({probability:.1%}) is moderately decisive.")
    else:
        st.error(f"🔴 **Low Confidence** — The model score ({probability:.1%}) is close to the boundary; human review is especially important.")
    st.caption("Confidence reflects how far the score is from 0.50, not the probability of loan repayment.")


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
        # ── Confidence badge (new) ───────────────────────────────────────────
        confidence_badge(result["probability"])
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
            import csv as _csv
            frame = read_upload(uploaded.getvalue())
            with st.spinner("Screening applications…"):
                predictions = predict_frame(frame, artifact).reset_index(drop=True)
            output = pd.concat([frame.reset_index(drop=True), predictions], axis=1)
            left, right, other = st.columns(3)
            left.metric("Applications screened", len(predictions))
            right.metric("Approved suggestions", int(predictions["prediction"].eq("Approved").sum()))
            other.metric("Rejected suggestions", int(predictions["prediction"].eq("Rejected").sum()))
            st.dataframe(output, hide_index=True, use_container_width=True)
            st.download_button("Download screening results", csv_download(output), "loan_screening_results.csv", "text/csv", type="primary")

            # ── Batch Analytics (new) ────────────────────────────────────────
            st.divider()
            st.markdown("### 📊 Batch Analytics")
            try:
                from src.batch_analytics import batch_summary_stats, plot_batch_breakdown
                stats = batch_summary_stats(predictions, frame)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Approval Rate", f"{stats['approval_rate']:.1%}")
                c2.metric("High-Confidence Approvals", stats["high_confidence_approvals"])
                c3.metric("High-Confidence Rejections", stats["high_confidence_rejections"])
                c4.metric("Avg. Probability Score", f"{stats['avg_probability']:.1%}")
                fig = plot_batch_breakdown(predictions, frame)
                st.pyplot(fig, clear_figure=True)
                plt.close(fig)
            except Exception as analytics_error:
                st.info(f"Analytics unavailable: {analytics_error}")

            st.warning("Batch results require individual human review. Uploaded labels, if present, are not used as model inputs.")
        except Exception as error:
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
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    with st.expander("Cross-validation model comparison", expanded=True):
        path = ROOT / "reports" / "model_comparison.csv"
        if path.exists():
            st.dataframe(pd.read_csv(path), hide_index=True, use_container_width=True)
        else:
            st.info("Model comparison is not available.")
    with st.expander("Fairness audit"):
        st.write("Group-level approval rates can reveal disparities. Small groups, historical bias and proxy variables limit interpretation; this audit does not certify fairness.")
        path = ROOT / "reports" / "fairness.csv"
        if path.exists():
            st.dataframe(pd.read_csv(path), hide_index=True, use_container_width=True)
        else:
            st.info("Fairness report is not available.")
    # ── Calibration report (new) ─────────────────────────────────────────────
    with st.expander("Calibration analysis"):
        cal_path = ROOT / "reports" / "calibration.json"
        if cal_path.exists():
            cal = json.loads(cal_path.read_text(encoding="utf-8"))
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("Brier Score (before)", f"{cal['brier_before']:.4f}")
            cc2.metric("Brier Score (after isotonic)", f"{cal['brier_after']:.4f}")
            cc3.metric("Improvement", f"{cal['improvement_pct']:.1f}%")
            bands = cal.get("confidence_distribution", {})
            if bands:
                band_df = pd.DataFrame([
                    {"Band": k, "Count": v["count"], "Percentage": f"{v['percentage']:.1f}%"}
                    for k, v in bands.items()
                ])
                st.dataframe(band_df, hide_index=True)
            cal_fig_path = ROOT / "reports" / "figures" / "calibration_curve.png"
            if cal_fig_path.exists():
                st.image(str(cal_fig_path), caption="Reliability diagram — before and after isotonic calibration")
        else:
            st.info("Run `python -m src.calibration` to generate calibration analysis.")
    # ── Learning curves (new) ────────────────────────────────────────────────
    with st.expander("Learning curves"):
        lc_path = ROOT / "reports" / "figures" / "learning_curves.png"
        if lc_path.exists():
            st.image(str(lc_path), caption="Learning curves — training F1 vs validation F1 across dataset sizes")
        else:
            st.info("Run `python -m src.learning_curves` to generate learning curves.")
    summary_path = ROOT / "reports" / "figures" / "shap_summary.png"
    if summary_path.exists():
        st.image(str(summary_path), caption="Global SHAP explanation of the fitted model")
    st.info("Approval labels do not contain repayment outcomes. This project cannot validate default reduction or NPA prevention.")


def render_whatif(artifact: dict) -> None:
    """Interactive What-If simulator: adjust inputs and see real-time prediction."""
    st.subheader("🔄 What-If Simulator")
    st.write("Adjust the sliders below to see how changing applicant details affects the approval score in real time.")
    threshold = float(artifact["threshold"])

    col_a, col_b = st.columns(2)
    with col_a:
        wi_income = st.slider("Applicant monthly income", 500, 20000, 4000, 100, key="wi_income")
        wi_loan = st.slider("Loan amount (thousands)", 10, 500, 128, 5, key="wi_loan")
        wi_term = st.selectbox("Loan term (months)", [60, 120, 180, 240, 300, 360], index=5, key="wi_term")
        wi_co_income = st.slider("Co-applicant monthly income", 0, 10000, 1500, 100, key="wi_co_income")
    with col_b:
        wi_credit = st.radio("Credit history meets guidelines", ["Yes", "No"], index=0, key="wi_credit", horizontal=True)
        wi_edu = st.radio("Education", ["Graduate", "Not Graduate"], index=0, key="wi_edu", horizontal=True)
        wi_area = st.selectbox("Property area", ["Urban", "Semiurban", "Rural"], key="wi_area")
        wi_employed = st.radio("Self-employed", ["No", "Yes"], index=0, key="wi_employed", horizontal=True)
        wi_deps = st.selectbox("Dependents", ["0", "1", "2", "3+"], key="wi_deps")

    applicant = {
        "ApplicantIncome": float(wi_income),
        "CoapplicantIncome": float(wi_co_income),
        "LoanAmount": float(wi_loan),
        "Loan_Amount_Term": float(wi_term),
        "Credit_History": 1.0 if wi_credit == "Yes" else 0.0,
        "Education": wi_edu,
        "Dependents": wi_deps,
        "Property_Area": wi_area,
        "Self_Employed": wi_employed,
        "Gender": None,
        "Married": None,
    }

    try:
        frame = pd.DataFrame([applicant])
        result = predict_frame(frame, artifact).iloc[0]
        prob = float(result["probability"])
        decision = str(result["prediction"])

        st.divider()
        res_col, bar_col = st.columns([1, 2])
        with res_col:
            st.metric("Approval Score", f"{prob:.1%}")
            st.metric("Decision (threshold={:.2f})".format(threshold), decision)
            dist = prob - threshold
            if dist >= 0:
                st.success(f"✅ Above threshold by **{dist:+.1%}**")
            else:
                st.error(f"❌ Below threshold by **{dist:+.1%}**")
        with bar_col:
            st.markdown(f"**Approval probability: {prob:.1%}**")
            st.progress(min(prob, 1.0))
            st.caption(f"Threshold line at {threshold:.0%} — scores above this would be Approved under the cost policy.")

        # ── Factor hints ─────────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 💡 What could improve the score?")
        hints = []
        if wi_credit == "No":
            hints.append("🔑 **Credit history** — Meeting credit guidelines is the strongest single factor.")
        if wi_income < 4000:
            hints.append("💰 **Higher applicant income** — Incomes above ₹4,000/month improve the debt-to-income ratio.")
        if wi_loan > 200:
            hints.append("📉 **Lower loan amount** — A smaller loan reduces the EMI-to-income burden.")
        if wi_area == "Rural":
            hints.append("🏙️ **Property in Semiurban/Urban area** — Historically associated with higher approval rates.")
        if wi_edu == "Not Graduate":
            hints.append("🎓 **Graduate education** — Historically correlated with higher approval rates.")
        if wi_co_income == 0:
            hints.append("👥 **Adding a co-applicant income** — Increases total household income, improving affordability ratios.")
        if not hints:
            hints.append("✨ The profile already reflects strong approval indicators.")
        for hint in hints:
            st.write(f"• {hint}")
        st.caption("These hints describe historical associations in the training data. They are not guaranteed paths to approval.")

    except Exception as error:
        st.error(f"Could not compute prediction: {error}")


def render_eda_explorer() -> None:
    """Browse all 10 EDA figures with descriptive captions."""
    st.subheader("📈 EDA Explorer")
    st.write("Exploratory Data Analysis charts generated from the **training partition only** (holdout excluded).")
    figures_dir = ROOT / "reports" / "figures"
    found = [name for name in sorted(EDA_CAPTIONS.keys()) if (figures_dir / name).is_file()]
    if not found:
        st.info(
            "EDA figures have not been generated yet. Run the EDA pipeline step first:\n\n"
            "```powershell\n.venv\\Scripts\\python.exe -m src.eda\n```"
        )
        return
    for name in found:
        path = figures_dir / name
        caption = EDA_CAPTIONS.get(name, name)
        st.image(str(path), caption=caption, use_container_width=True)
        st.caption(f"File: `reports/figures/{name}`")
        st.markdown("---")


def main() -> None:
    """Load the trusted model and render the five application workflows."""
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

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🏠 LoanLens")
        st.caption("EXPLAINABLE LOAN SCREENING")
        st.divider()
        st.markdown("**Workspace**\n\nSingle application\n\nBatch screening\n\nModel evidence\n\nWhat-If Simulator\n\nEDA Explorer")
        st.divider()
        st.markdown("**Built for review**")
        st.caption("Compare model suggestions, understand contributing factors and inspect evaluation evidence.")
        st.warning("For education and human review. Do not use as an autonomous lending decision.")

        # ── Threshold Explorer ────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🔧 Threshold Explorer")
        explorer_threshold = st.slider(
            "Approval threshold", 0.30, 0.90, 0.50, 0.01, key="threshold_explorer",
            help="Drag to see how changing the decision cutoff would change the last prediction.",
        )
        last_result = st.session_state.get("screening_result")
        if last_result:
            prob = last_result["probability"]
            decision = "✅ Approved" if prob >= explorer_threshold else "❌ Rejected"
            st.markdown(f"**At threshold {explorer_threshold:.2f}:** last application → **{decision}** (score {prob:.1%})")
        else:
            st.caption("Submit a prediction on the Single Application tab to see it update here.")

        # ── EMI Calculator ────────────────────────────────────────────────────
        st.divider()
        st.markdown("#### 💰 EMI Calculator")
        emi_loan = st.number_input("Loan amount (₹ thousands)", min_value=1.0, value=128.0, step=10.0, key="emi_loan")
        emi_term = st.number_input("Term (months)", min_value=12.0, value=360.0, step=12.0, key="emi_term")
        emi_rate = st.number_input("Annual interest rate (%)", min_value=1.0, max_value=30.0, value=9.0, step=0.5, key="emi_rate")
        try:
            emi = emi_calculation(emi_loan, emi_term, emi_rate)
            st.metric("Monthly EMI", f"₹ {emi['monthly_emi']:,.0f}")
            st.caption(f"Total payment: ₹ {emi['total_payment']:,.0f} · Interest paid: ₹ {emi['total_interest']:,.0f}")
        except Exception:
            st.caption("Enter valid values above.")

    # ── Hero ──────────────────────────────────────────────────────────────────
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

    single, batch, evidence, whatif, eda = st.tabs([
        "Single application", "Batch screening", "Model evidence", "What-If Simulator", "EDA Explorer"
    ])
    with single:
        render_single(artifact)
    with batch:
        render_batch(artifact)
    with evidence:
        render_evidence(artifact)
    with whatif:
        render_whatif(artifact)
    with eda:
        render_eda_explorer()

    st.divider()
    st.caption("Housing Loan Approval Prediction Using Machine Learning Algorithms · Python · scikit-learn · SHAP · Streamlit")


if __name__ == "__main__":
    main()
