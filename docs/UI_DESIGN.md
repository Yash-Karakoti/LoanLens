# Application design and references

## Intent and available data

LoanLens is a local educational workspace for one application, a batch CSV, and generated model evidence. Available data are application fields, predicted approval scores, a training-selected threshold, SHAP contributions, held-out metrics and demographic audit summaries. The app has no real lending decisions, customer accounts, repayment histories, loan books, live counts, identity verification, or deployment claims. No mock dashboard totals are displayed.

## Design choices

- Three native Streamlit tabs keep application entry, batch review and evidence separate without a custom frontend or additional dependency.
- A wide layout puts grouped income/loan and profile fields beside a concise review guide. Native columns collapse on smaller screens; visible labels and native widgets preserve keyboard access.
- A navy text / teal action palette, pale page background, white bordered surfaces, and consistent spacing keep the form readable. These are original project choices, not claimed copies of reference-site tokens.
- Every number displayed as a result comes from the loaded model or generated reports. Blank inputs remain blank rather than silently selecting a demographic category or inventing an applicant record.
- The result shows the binary historical suggestion, score and active threshold together, followed by three model reasons and the SHAP chart. Text communicates the outcome as well as color. The score is not labeled repayment probability or guaranteed confidence.
- A policy selector defaults to the pre-specified standard threshold of 0.50; the saved training-selected cost threshold remains available as an explicitly failed scenario. The fitted decision tree's leaf class weights are normalized to obtain its maximum possible positive-class score, without using holdout data. When the saved cost threshold exceeds this bound, a prominent message explains that the scenario rejects every possible applicant. The application passes a shallow artifact copy with the selected threshold to single, batch and explanation functions; it never edits the saved model. Changing policy clears the prior result until the user submits again.
- Unknown or missing values use the training-only imputation contract. An entirely blank application or one containing only excluded demographic audit fields is rejected. Batch validation errors are visible; oversized or empty batches are rejected before prediction. Raw CSV headers are read with Python's CSV reader before pandas, so duplicate field names cannot be silently renamed.
- Uploaded data are processed in memory. CSV downloads neutralize formula-like text in both data cells and column headers. No external font, analytics, account, or LLM connection is required.
- Missing model and missing evaluation-report states show concrete next actions instead of fake results. Explanation failure leaves a valid prediction visible and names the failed operation.

## Reference research

These are pattern references, not copied code or a claim that every competitor was exhaustively reviewed. The entries below were checked through their primary public pages/documentation during this build. Pixel-level competitor screenshots and authenticated dashboards were not inspected.

| Primary reference | What was checked | Adaptation | What was avoided |
|---|---|---|---|
| [Streamlit finance app gallery](https://streamlit.io/gallery?category=finance) | Public gallery and finance category | Dedicated data-analysis workspace with evidence alongside the task | Unavailable market feeds or fictional portfolio totals |
| [Streamlit forms](https://docs.streamlit.io/develop/concepts/architecture/forms) | Native form batching | All application details submit together | Predictions rerunning on every input keystroke |
| [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing) | Real widget test interface | Submit actual form inputs in automated integration tests | Treating a server health check as proof the prediction flow works |
| [GOV.UK summary list](https://design-system.service.gov.uk/components/summary-list/) | Primary component guidance | Group related details and use plain field labels | Copying the government brand or adding a review step the project does not need |
| [GOV.UK error summary](https://design-system.service.gov.uk/components/error-summary/) | Primary validation guidance | Visible, concise messages explaining invalid input and recovery | Hiding validation errors in logs or relying only on color |

Streamlit controls provide the accessible interaction baseline. This project does not claim a formal WCAG audit; visual/keyboard checks and AppTest evidence should be read alongside the final verification notes.

## How to demonstrate

1. Start the app from the project root using the README command.
2. Enter clearly identified demonstration inputs or a known dataset record; do not present them as a real bank application.
3. Explain the suggestion, model score and active standard threshold before opening the SHAP reasons. Inspect the optional saved cost scenario to demonstrate its failed score-range check, rather than presenting it as a successful operating policy.
4. Upload a schema-compatible CSV and download the screening result.
5. Open Model evidence and compare ordinary 0.5 metrics with the cost-selected policy, then discuss the fairness and default-label limitations.
