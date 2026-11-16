# Assumptions and decisions

- The Windows folder is `Housing Loan Approval Prediction`; the complete project title is **Housing Loan Approval Prediction Using Machine Learning Algorithms: Build an Explainable Loan Screening Assistant**. A colon is invalid in a Windows directory name and the shorter path avoids long-path installation issues.
- This is a local educational prototype for human review. Approval labels are historical decisions, not creditworthiness, repayment, or default labels. No claim of NPA reduction can be validated with this dataset.
- Python 3.12 is installed and satisfies Python 3.10+. Use the project `.venv` and a frozen requirements file for reproducibility.
- Kaggle credentials and the Kaggle command were checked by existence only; none were available. Public organizer/mirror download is the next authorized option. Never inspect or commit credentials.
- Hold out a stratified 20% with seed 42 before any fitted preprocessing. Five-fold shuffled stratified CV on the remaining 80% selects hyperparameters and models by F1, with ROC-AUC as a tie-breaker. The holdout never selects the model or decision threshold.
- Compare balanced class weights with SMOTENC (the mixed categorical/numeric variant of SMOTE) for every requested algorithm. Ordinary SMOTE on one-hot features invents fractional categories; SMOTENC avoids that. Synthetic samples exist only inside training folds, never in the raw file or EDA.
- Exclude Gender and Married from model features but retain them for requested descriptive EDA/fairness audits. This prevents direct demographic use but does not eliminate proxy bias or prove fairness.
- LoanAmount is recorded in thousands; terms are months. Income units/currency and collection date are not independently documented. Display dataset monetary units rather than claiming rupees or dollars.
- EMI is an illustrative amortized monthly installment with a fixed assumed 9% annual rate; principal = LoanAmount × 1,000. Balance_Income = TotalIncome − EMI. These are engineered proxies, not bank quotes. The rate is a documented assumption, not learned from data.
- Use log1p transforms for skewed income/loan values, not row removal or global IQR clipping. Dependents `3+` becomes 3 (lower bound).
- A false approval (predict Y when historical label N) has an illustrative cost of 5 units; a false rejection costs 1. Costs are assumptions, not measured monetary losses. Select the threshold on training out-of-fold probabilities; report it separately from standard 0.5 metrics. Hyperparameters were selected using the same training folds, so OOF tuning scores can have selection optimism; only holdout metrics are final evaluation.
- SHAP explains fitted model associations, not causes or legally sufficient adverse-action reasons. Correlated engineered features share attribution. Use training-only background data.
- No login, database, external LLM, cloud deployment or real lending decisions are required. Uploaded applicants are processed in memory and are not persisted by the application.
- Do not copy third-party application code. Record relevant repositories as references with limitations and license status rather than claiming an exhaustive search or a universal best implementation.
- The fitted tree's leaf-score support tops out at 0.6394436519258202, below the training-selected 0.76 cost threshold. Training OOF cost tuning itself chose reject-all under the assumed 5:1 costs. Retain the saved cost experiment unchanged. The UI defaults to the conventional, pre-existing 0.50 policy and exposes 0.76 only as a labeled failed scenario, by passing a copy of the artifact with an explicit threshold. This deployment choice follows the model's structural score support, not a search on holdout outcomes. Both policies' held-out results remain visible.
- The cost grid includes 0.00–1.00 by 0.01 plus the next floating-point value above 1.0 to represent reject-all even when a classifier returns exactly 1.0. This edge-case fix does not alter the selected 0.76 result.
- SMOTENC interpolates numeric engineered features, which may no longer exactly satisfy their original financial formulas. It is a comparison experiment, not additional observed applications or a source of EDA data.

## Custom website follow-up

- The custom website is the primary localhost interface; Streamlit remains available for the original notebook-oriented demonstration. The trained model and both threshold policies are preserved.
- Use FastAPI with a same-origin, buildless HTML/CSS/JavaScript frontend. A separate React toolchain is unnecessary for these six pages and would make setup and the viva explanation more complex.
- Mercury's official public interactive demo supplies the primary visual reference. Follow its layout, spacing and surface hierarchy with original LoanLens content and assets. The design is an adaptation, not Mercury affiliation or a claim of pixel-identical proprietary typography.
- No authentication, durable applicant storage or cloud publication is added. Website input remains in memory. Deployment instructions distinguish a publicly reachable educational demo from real lending use.

## Homepage revision

- The user explicitly requested a homepage and hero, superseding the previous dashboard-only root and its blue Mercury palette. The operational overview moves to `/workspace`; existing screening routes remain available.
- The new brand adapts Better's verified forest/ivory/green action palette and Blend's split hero hierarchy, with original content and appropriately licensed substitute fonts. No bank affiliation or proprietary font reuse is implied.
- The architectural hero is an original AI-generated illustration, clearly distinguished from applicant data. All displayed model figures and interactive predictions still use actual reports/API results.
- Preserve the existing untracked `recipes.json`; it is unrelated user work and is not part of this change.
- Inside-UI follow-up: interpret "match the outer one" as sharing the actual public header/footer, Instrument Serif titles, pill actions, ivory/sage surfaces and housing visual. Replace the desktop sidebar with full-width tool navigation and a mobile grid. Keep all model inputs, validation, policies and inference semantics unchanged; no new UI plugin is needed.
