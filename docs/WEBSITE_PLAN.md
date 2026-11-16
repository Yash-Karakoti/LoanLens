# Custom website plan

The user requested a complete localhost website, prepared for later deployment, with a visual design that closely follows researched references. The custom website becomes the primary interface; the original Streamlit UI remains a compatible alternative.

## Scope and design contract

- Primary reference: the actual official Mercury interactive dashboard at https://demo.mercury.com/dashboard. A locally inspected reference screenshot and measured layout details are recorded in `WEBSITE_REFERENCES.md` and `design-references/`.
- Preserve the reference's quiet operational layout: a narrow pale sidebar, white canvas, compact utility header, restrained page title, pill actions, thin borders, two-column panels and ledger-style tables. Original LoanLens branding, text, icons and system fonts replace proprietary assets. Match the visual relationships across every page rather than mixing unrelated themes.
- Real routes: overview, application assessment, batch screening, model evidence, methodology and reference notes. Navigation, form submission, uploads, results, downloads and error/loading states must work.
- Every metric, chart point, example application and explanation comes from existing verified reports, the actual public dataset or the fitted model. Do not invent operational history, applicants, users, account balances or savings.
- Standard threshold 0.50 remains the default. Preserve 0.76 as an explicitly failed cost experiment, with its actual limitation visible where relevant. Historical approval is not repayment/default probability.

## Implementation

Use a buildless HTML/CSS/JavaScript frontend served by FastAPI on the same origin. This retains Python for the actual model and SHAP while avoiding an additional frontend package manager/build tool. Native browser controls, focused JavaScript modules and shared Python validation keep the viva explanation simple.

`web/server.py` serves explicit page routes, static assets, model evidence and bounded prediction/batch APIs. Shared CSV validation/export and tree-score checks are extracted to `src/interface.py` so both interfaces use the same boundary. Existing raw data, training code and fitted model are preserved.

The site runs locally using `python -m web`. Prepare a container recipe, Linux runtime dependency set and deployment instructions; do not register or publish a hosted Site now. The user explicitly asked for localhost with deployment later.

## Verification

Run API boundary tests and the complete existing pytest suite. Use the installed Playwright verification environment to test real prediction/SHAP, CSV upload/export, navigation/back/refresh, invalid inputs, keyboard behavior and responsive layouts. Capture the implemented pages and compare them with the actual reference screenshot and measured design contract. Verify raw/model checksums before and after work. Record unexecuted deployment checks honestly.
