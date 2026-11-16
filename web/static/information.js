/** Plain-language project guide and the concrete sources behind the interface. */
import { icon, percent, decimal, notice, linkButton } from "./components.js";

export function methodologyPage(main, data) {
  const dataset = data?.dataset;
  const steps = [
    [
      "Start with authentic observations",
      "Dream Housing Finance applications contain historical approval decisions. The original CSV is preserved unchanged and verified by SHA-256.",
    ],
    [
      "Split raw rows before fitting",
      `A stratified 80/20 split with seed 42 reserves ${dataset?.test_rows ?? "the holdout"} applications. Imputers, scalers, encoders and SMOTENC never fit on that holdout.`,
    ],
    [
      "Prepare and engineer within each fold",
      "Numeric medians, categorical modes, income and affordability proxies, scaling and encoding live inside the complete pipeline. Gender and Married remain audit fields, not predictors.",
    ],
    [
      "Compare five algorithms consistently",
      "Logistic Regression, Decision Tree, Random Forest, XGBoost and LightGBM each compare class weighting with SMOTENC. Five-fold training CV selects by approval F1.",
    ],
    [
      "Evaluate once, explain each suggestion",
      "The saved model is evaluated on untouched holdout rows. Probability-space SHAP explains model associations relative to real training background examples. A human reviewer remains responsible.",
    ],
  ];
  main.innerHTML = `<div class="page-heading"><div><h1>Behind the assessment</h1><p>A small, explainable pipeline—with its limits in plain sight.</p></div>${linkButton("/evidence", "Inspect the evidence", "outline", "chart")}</div>
  <div class="prose-grid"><section class="panel prose-card"><ol class="pipeline">${steps.map(([title, text], index) => `<li><span class="pipeline-number">${index + 1}</span><div><h2 style="font-size:13px;line-height:1.5;margin:0 0 5px">${title}</h2><p>${text}</p></div></li>`).join("")}</ol></section><aside class="panel side-facts"><h2>The experiment at a glance</h2><div class="fact"><span>Source dataset</span><strong>Dream Housing Finance</strong></div><div class="fact"><span>Observed applications</span><strong>${dataset?.total_rows ?? "See dataset report"}</strong></div><div class="fact"><span>Train / holdout</span><strong>${dataset ? `${dataset.train_rows} / ${dataset.test_rows}` : "Stratified 80/20"}</strong></div><div class="fact"><span>Standard screening threshold</span><strong>0.50 · fixed policy</strong></div><div class="fact"><span>Selected model</span><strong>${data?.model.name ?? "See saved artifact"}</strong></div><div class="fact"><span>API documentation</span><a href="/api/docs" target="_blank" rel="noopener">Explore the local API ${icon("arrow")}</a></div></aside></div>
  <section class="panel prose-card prose"><h2>What goes into the score?</h2><p>The model uses applicant and co-applicant income, loan amount and term, credit-history indicator, property area, education, self-employment and dependents. <code>Loan_ID</code> is dropped. Gender and marital status are excluded from prediction, while group audits report differences in historical and predicted approvals.</p><h2>Units and financial proxies</h2><p><strong>Income is interpreted as monthly dataset units.</strong> Currency metadata was not independently documented. Loan amount is recorded in thousands; terms are months. Total income adds applicant and co-applicant income. An illustrative EMI assumes a fixed <strong>9% annual rate</strong>, and balance income subtracts it from total income. These are model features, not bank quotes or verified affordability decisions.</p><p>Log transforms retain high-income observations while reducing scale differences. Dependents <code>3+</code> maps to a lower bound of three. Missing numeric fields use training medians; categorical fields use training modes. An explanation can therefore reflect an imputed value instead of a supplied fact.</p><h2>What SHAP can—and cannot—tell you</h2><p>SHAP contributions describe how features move the model approval score relative to a training background. They add up to the predicted score. They do <strong>not</strong> establish causes or actions that guarantee approval. Correlated and engineered features share information; independent masking can produce unrealistic combinations. Plot values are standardized numbers or encoded categories.</p><h2>Why keep a failed cost experiment?</h2><p>The training-only cost study assumed five units for a false approval and one for a false rejection. Its chosen threshold of ${decimal(data?.model.cost_threshold ?? 0.76, 2)} exceeds the final tree’s score support and rejects everyone. The project preserves that failure honestly. This website defaults to the conventional 0.50 policy; it does not fit a replacement threshold to the holdout.</p></section>
  ${notice("<strong>Approval is not repayment.</strong> This dataset cannot demonstrate reduced defaults, fewer non-performing assets, fair treatment, or production lending suitability. Historical labels may encode bias. External validation and domain review are required before any real use.", "warn")}
  <section class="panel prose-card prose"><h2>Privacy by a small scope</h2><p>Application inputs and CSVs are processed in memory. The website does not create accounts, save applicant records, or send data to an external language model. Downloaded CSVs neutralize formula-like text. The public training example is explicitly identified; it is never presented as a new bank application.</p><p>This is an educational, deployable software prototype. Hosting configuration alone does not make it a validated lending system.</p></section>`;
}

export function referencesPage(main) {
  const sources = [
    {
      name: "Blend",
      icon: "assess",
      url: "https://help.blend.com/support/solutions",
      label: "Lending workflow reference",
      text: "Borrower-oriented field grouping, explicit application details, and a separate review outcome. The website does not copy lending claims or a lender identity.",
    },
    {
      name: "Ramp",
      icon: "chart",
      url: "https://support.ramp.com/real-time-reporting/",
      label: "Operational clarity reference",
      text: "Dense but readable evidence tables, clearly grouped reporting, and actions placed next to the task. No simulated finance activity is shown.",
    },
    {
      name: "GOV.UK Design System",
      icon: "shield",
      url: "https://design-system.service.gov.uk/components/error-summary/",
      label: "Accessible validation reference",
      text: "Visible errors, direct recovery instructions, consistent labels, and native keyboard-friendly controls. The government visual identity is not reused.",
    },
  ];
  main.innerHTML = `<div class="page-heading"><div><h1>Design & references</h1><p>One coherent visual direction. Real product evidence behind the choices.</p></div><span class="quiet-label">${icon("link")}Reference-led interface</span></div>
  <section class="panel reference-feature"><div><span class="badge selected">Primary visual reference</span><h2>Mercury’s operational workspace</h2><p>The official public demo informed the navigation, spacing, panels and action hierarchy. LoanLens uses the same restrained workspace relationships with its own brand, content and model evidence.</p><ul class="match-list"><li>${icon("check")}220 px left rail with compact active navigation.</li><li>${icon("check")}28 px page title, white canvas and pale dividers.</li><li>${icon("check")}12 px bordered panels in a balanced two-column grid.</li><li>${icon("check")}Blue action pills, quiet labels and readable ledger tables.</li></ul><a class="text-link" href="https://demo.mercury.com/dashboard" target="_blank" rel="noopener">Inspect the official reference ${icon("arrow")}</a></div><div><div class="reference-visual" role="img" aria-label="Original structural sketch showing a slim sidebar, compact action row, two bordered panels, and a table"><div class="reference-mini-rail"><div class="reference-mini-mark"></div><div class="reference-mini-line active"></div><div class="reference-mini-line"></div><div class="reference-mini-line"></div><div class="reference-mini-line"></div></div><div class="reference-mini-main"><div class="reference-mini-heading"></div><div class="reference-mini-actions"><span></span><span></span><span></span></div><div class="reference-mini-grid"><div class="reference-mini-panel"><i></i><i></i><i></i></div><div class="reference-mini-panel"><i></i><i></i><i></i></div></div><div class="reference-mini-table"></div></div></div><p class="small" style="margin-top:10px">Original structural sketch, not a copied product screenshot.</p></div></section>
  <div class="reference-links">${sources.map((source) => `<section class="panel reference-link-card">${icon(source.icon)}<h2>${source.name}</h2><span class="small muted">${source.label}</span><p style="margin-top:10px">${source.text}</p><a class="text-link" href="${source.url}" target="_blank" rel="noopener">View the primary source ${icon("arrow")}</a></section>`).join("")}</div>
  <section class="panel"><div class="panel-heading"><h2>How the reference maps to LoanLens</h2><span class="quiet-label">Verified structure, original implementation</span></div><div class="table-scroll"><table><thead><tr><th scope="col">Reference pattern</th><th scope="col">LoanLens adaptation</th><th scope="col">What stays truthful</th></tr></thead><tbody><tr><td>Account overview</td><td>Dataset and validation overview</td><td>No invented balances or live application counts</td></tr><tr><td>Compact action pills</td><td>New assessment, upload, evidence</td><td>Every visible action has a working destination</td></tr><tr><td>Charts and account panels</td><td>Empirical ROC and real class balance</td><td>Every plotted value comes from model reports</td></tr><tr><td>Transaction ledger</td><td>Model comparison and batch results</td><td>Actual candidates and submitted application rows</td></tr><tr><td>Structured operational review</td><td>Grouped form and explanation panel</td><td>Score, threshold, missing values and limitations visible</td></tr></tbody></table></div></section>
  <div class="prose small"><p>Research also considered official Stripe, Linear and accessible form guidance. The recorded source review and local reference screenshots are in <code>docs/WEBSITE_REFERENCES.md</code>. Mercury’s proprietary font, branding, balances, avatars and demo data are not redistributed in the website. Fonts use the device’s system sans-serif stack.</p></div>`;
}
