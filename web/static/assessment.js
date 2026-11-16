/** Application drafts and results remain in memory; no browser storage is used. */
import {
  icon,
  escapeHTML,
  decimal,
  request,
  notice,
  empty,
} from "./components.js";
import { resultHTML } from "./assessment-result.js";
const fields = [
  "Gender",
  "Married",
  "Dependents",
  "Education",
  "Self_Employed",
  "ApplicantIncome",
  "CoapplicantIncome",
  "LoanAmount",
  "Loan_Amount_Term",
  "Credit_History",
  "Property_Area",
];
const numeric = new Set([
  "ApplicantIncome",
  "CoapplicantIncome",
  "LoanAmount",
  "Loan_Amount_Term",
  "Credit_History",
]);
let draft = Object.fromEntries(fields.map((name) => [name, null])),
  policy = "standard",
  cachedResult = null,
  exampleLabel = "";
const input = (name, label, hint, min = 0) =>
  `<div class="field"><label for="${name}">${label}</label><input id="${name}" name="${name}" type="number" inputmode="decimal" step="any" min="${min}" placeholder="Not provided" aria-describedby="${name}-hint"><small id="${name}-hint">${hint}</small></div>`;
const select = (name, label, options) =>
  `<div class="field"><label for="${name}">${label}</label><select id="${name}" name="${name}"><option value="">Not provided</option>${options
    .map((option) => {
      const [value, text] = Array.isArray(option) ? option : [option, option];
      return `<option value="${value}">${text}</option>`;
    })
    .join("")}</select></div>`;

export function assessmentPage(main, evidence) {
  main.innerHTML = `<div class="page-heading"><div><h1>New assessment</h1><p>Review one application. Understand the factors behind its score.</p></div><div class="page-actions"><button class="button outline" id="load-example">${icon("file")}Load real example</button><button class="button square outline" id="reset-form" aria-label="Clear application">${icon("reset")}</button></div></div>
  <div class="assessment-layout"><section class="panel form-panel" aria-labelledby="application-title"><div class="policy-box"><label for="policy">Screening policy</label><select class="policy-select" id="policy"><option value="standard">Standard screening · 0.50</option><option value="cost">Failed cost experiment · ${decimal(evidence?.model.cost_threshold ?? 0.76, 2)}</option></select><div id="policy-warning" class="policy-warning"></div></div><div id="example-source"></div><div id="form-error" aria-live="polite"></div>
  <form id="assessment-form"><section class="form-section"><div class="section-label"><span class="section-number">1</span><h2 id="application-title">Income & loan details</h2></div><div class="field-grid">${input("ApplicantIncome", "Applicant income", "Monthly dataset units")}${input("CoapplicantIncome", "Co-applicant income", "Monthly dataset units; enter 0 if none")}${input("LoanAmount", "Loan amount", "Thousands of dataset units", 0.001)}${input("Loan_Amount_Term", "Loan term", "Months", 1)}</div></section>
  <section class="form-section"><div class="section-label"><span class="section-number">2</span><h2>Application profile</h2></div><div class="field-grid">${select(
    "Credit_History",
    "Credit history",
    [
      ["1", "Meets guidelines"],
      ["0", "Does not meet guidelines"],
    ],
  )}${select("Property_Area", "Property area", ["Urban", "Semiurban", "Rural"])}${select("Education", "Education", ["Graduate", "Not Graduate"])}${select("Self_Employed", "Self-employed", ["No", "Yes"])}${select("Dependents", "Dependents", ["0", "1", "2", "3+"])}</div></section>
  <details class="optional-audit"><summary>Optional demographic audit fields</summary><p>Gender and marital status are excluded from model predictions.</p><div class="field-grid">${select("Gender", "Gender", ["Female", "Male"])}${select("Married", "Married", ["No", "Yes"])}</div></details>
  <div class="form-bottom"><span class="quiet-label">${icon("shield")}Processed in memory only</span><button class="button primary" type="submit" id="predict-button">${icon("spark")}Generate assessment</button></div><p class="form-note">Blank fields use training-only imputation. Currency metadata was not independently documented.</p></form></section>
  <aside class="result-column" aria-label="Assessment outcome"><section class="panel" id="assessment-result" aria-live="polite"></section><div class="panel review-guide"><h3>A thoughtful review, in three steps</h3><ol><li><span>1</span>Enter or load application details.</li><li><span>2</span>Compare the score with the policy threshold.</li><li><span>3</span>Inspect the explanation and verify documents.</li></ol><p>Historical approvals do not measure repayment, default risk, or non-performing assets.</p></div></aside></div>`;
  const form = main.querySelector("#assessment-form"),
    output = main.querySelector("#assessment-result"),
    submit = main.querySelector("#predict-button"),
    errorBox = main.querySelector("#form-error");
  let revision = 0,
    controller = null;
  const emptyResult = () => {
    output.innerHTML = `<div class="result-placeholder">${empty("Your assessment will appear here", "Submit details to see the score, suggestion, and model explanation.", "assess")}</div>`;
  };
  const restoreDraft = () => {
    for (const name of fields) form.elements[name].value = draft[name] ?? "";
  };
  const readDraft = () => {
    for (const name of fields) {
      const value = form.elements[name].value;
      draft[name] =
        value === "" ? null : numeric.has(name) ? Number(value) : value;
    }
  };
  const showExample = () => {
    main.querySelector("#example-source").innerHTML = exampleLabel
      ? `<div class="example-source">${icon("check")}${escapeHTML(exampleLabel)}</div>`
      : "";
  };
  const updatePolicy = () => {
    main.querySelector("#policy-warning").innerHTML =
      policy === "cost"
        ? notice(
            "This saved cost scenario rejects every applicant: its threshold exceeds the fitted tree’s maximum score. It is a failed experiment, not a recommended screening policy.",
            "warn",
          )
        : "";
  };
  const invalidate = () => {
    revision++;
    controller?.abort();
    cachedResult = null;
    errorBox.innerHTML = "";
    emptyResult();
    submit.disabled = false;
    submit.innerHTML = `${icon("spark")}Generate assessment`;
  };
  restoreDraft();
  showExample();
  main.querySelector("#policy").value = policy;
  updatePolicy();
  if (cachedResult) output.innerHTML = resultHTML(cachedResult);
  else emptyResult();
  form.addEventListener("input", () => {
    readDraft();
    exampleLabel = "";
    showExample();
    invalidate();
  });
  main.querySelector("#policy").addEventListener("change", (event) => {
    policy = event.target.value;
    invalidate();
    updatePolicy();
  });
  main.querySelector("#reset-form").addEventListener("click", () => {
    draft = Object.fromEntries(fields.map((name) => [name, null]));
    exampleLabel = "";
    form.reset();
    policy = "standard";
    main.querySelector("#policy").value = policy;
    showExample();
    invalidate();
    updatePolicy();
    form.elements.ApplicantIncome.focus();
  });
  main
    .querySelector("#load-example")
    .addEventListener("click", async (event) => {
      const button = event.currentTarget;
      const requestedRevision = revision;
      button.disabled = true;
      try {
        const data = await request("/api/example");
        if (!form.isConnected || requestedRevision !== revision) return;
        draft = { ...data.applicant };
        restoreDraft();
        exampleLabel = `Real public training example · ${data.loan_id}`;
        invalidate();
        showExample();
      } catch (error) {
        if (form.isConnected && requestedRevision === revision)
          errorBox.innerHTML = `<div class="form-error">${notice(escapeHTML(error.message), "error")}</div>`;
      } finally {
        button.disabled = false;
      }
    });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    readDraft();
    errorBox.innerHTML = "";
    cachedResult = null;
    const submittedRevision = ++revision;
    controller?.abort();
    controller = new AbortController();
    submit.disabled = true;
    submit.innerHTML =
      '<span class="spinner" aria-hidden="true"></span>Calculating assessment…';
    output.innerHTML =
      '<div style="padding:25px" role="status" aria-label="Calculating prediction and explanation"><div class="skeleton title"></div><div class="skeleton text"></div><div class="skeleton block" style="height:180px;margin-top:25px"></div><p class="small" style="margin-top:15px">Running the saved model and calculating SHAP…</p></div>';
    try {
      const result = await request("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ applicant: draft, policy, explain: true }),
        signal: controller.signal,
      });
      if (!form.isConnected || submittedRevision !== revision) return;
      cachedResult = result;
      output.innerHTML = resultHTML(result);
    } catch (error) {
      if (
        error.name === "AbortError" ||
        !form.isConnected ||
        submittedRevision !== revision
      )
        return;
      emptyResult();
      errorBox.innerHTML = `<div class="form-error">${notice(escapeHTML(error.message), "error")}</div>`;
      errorBox.scrollIntoView({ block: "nearest" });
    } finally {
      if (form.isConnected && submittedRevision === revision) {
        submit.disabled = false;
        submit.innerHTML = `${icon("spark")}Generate assessment`;
      }
    }
  });
}
