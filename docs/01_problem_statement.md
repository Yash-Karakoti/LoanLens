# Problem statement

**Project:** Housing Loan Approval Prediction Using Machine Learning Algorithms: Build an Explainable Loan Screening Assistant.

Banks review housing-loan applications using financial, credit and application details. This intermediate college project builds a local decision-support prototype that learns historical approval patterns and gives a consistent screening recommendation with an explanation. A human reviewer remains responsible for a real decision.

## Machine-learning task

This is supervised binary classification. The target is `Loan_Status`: Y means historically approved (positive class 1) and N means historically rejected (class 0). The output is Approved/Rejected at a documented threshold, a model-estimated historical approval probability, and SHAP-based explanations of the fitted model's associations.

Candidate predictors include applicant/co-applicant income, loan amount, loan term, credit-history indicator, education, property area, employment status and dependents. Loan_ID is an identifier and is dropped. Gender and Married are retained for requested descriptive analysis and group auditing, but excluded from predictors. Engineered variables describe combined income and illustrative affordability; they do not add independently observed financial facts.

## Evaluation and decision costs

- **Precision:** of applications predicted approved, how many were historically approved? A false positive predicts approval for a historical rejection.
- **Recall:** of historically approved applications, how many does the model shortlist? A false negative misses a historical approval.
- **F1:** harmonic mean of approval-class precision and recall; used for training-CV model selection, with ROC-AUC breaking ties. It must be read alongside minority-class errors and the majority baseline.
- **ROC-AUC:** ranking performance across all thresholds; it does not measure the quality of a chosen operating threshold by itself.
- **Accuracy, confusion matrix and PR curve:** additional context on overall and class-specific mistakes; train/test gaps indicate possible overfitting.

A false approval can create additional manual review or conflict with screening policy; a false rejection can miss a suitable applicant. The project demonstrates an assumed cost of five units per false approval and one per false rejection, tuning the threshold on training out-of-fold predictions only. These are scenario costs, not measured money or default losses. Standard 0.5-threshold metrics and tuned-threshold metrics are reported separately.

## Reproducible experiment

Split raw observations with stratified 80/20 sampling and seed 42 before fitting anything. Compare Logistic Regression, Decision Tree, Random Forest, XGBoost and LightGBM using five-fold shuffled stratified CV and randomized searches. Compare class weighting with SMOTENC inside complete pipelines. Select the model and threshold without using the holdout. Report final holdout metrics, group approval rates and errors honestly; small datasets may not clearly separate models.

## Scope and limits

Deliver the data provenance audit, preprocessing code, training-only EDA notebook and plots, comparative training, evaluation, SHAP explanations, Streamlit single/batch screening UI, automated checks and viva documentation. Uploaded applications are handled in memory.

The business motivation is to reduce screening effort and support consistent review. This dataset contains approvals, not repayment/default outcomes, processing-time measurements, collateral valuations or complete bank policy. It cannot verify creditworthiness, quantify NPA reduction, establish real-world bank savings or validate production lending suitability. Historical bias can be learned by the model; a descriptive fairness check is not a fairness or legal certification.
