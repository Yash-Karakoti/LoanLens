/** Public introduction with live project evidence and an optional real example. */
import {
  icon,
  escapeHTML,
  percent,
  number,
  request,
  notice,
} from "./components.js";
import { resultHTML } from "./assessment-result.js";

const routeLink = (path, label) => `<a href="${path}" data-route>${label}</a>`;
const brand = `<a class="home-brand" href="/" data-route aria-label="LoanLens home"><img src="/assets/mark.svg" alt="" width="34" height="34"><span>LoanLens<span class="home-brand-dot">.</span></span></a>`;

export function mountPublicChrome(header, footer) {
  header.innerHTML = `<header class="home-header"><div class="home-nav-container">${brand}<nav class="home-desktop-nav" aria-label="Main navigation">${routeLink("/#how-it-works", "How it works")}${routeLink("/#features", "Why LoanLens")}${routeLink("/evidence", "The model")}${routeLink("/#faq", "FAQs")}</nav><div class="home-header-actions"><a class="home-workspace-link" href="/workspace" data-route>Open workspace ${icon("arrow")}</a><a class="home-button home-button-small" href="/assessment" data-route>Start screening ${icon("arrow")}</a><button class="home-menu-toggle" type="button" aria-label="Open main menu" aria-controls="public-menu" aria-expanded="false">${icon("menu")}</button></div></div></header>
    <dialog class="home-menu-dialog" id="public-menu" aria-labelledby="public-menu-title"><div class="home-menu-top"><h2 id="public-menu-title">Explore LoanLens</h2><button type="button" class="home-menu-close" aria-label="Close main menu">${icon("close")}</button></div><nav aria-label="Mobile main navigation">${routeLink("/", "Home")}${routeLink("/#how-it-works", "How it works")}${routeLink("/#features", "Why LoanLens")}${routeLink("/evidence", "The model")}${routeLink("/#faq", "FAQs")}${routeLink("/workspace", "Open workspace")}</nav><a class="home-button" href="/assessment" data-route>Start an assessment ${icon("arrow")}</a><p>Educational screening. Human review always.</p></dialog>`;
  footer.innerHTML = `<footer class="home-footer"><div class="home-container"><div class="home-footer-top"><div class="home-footer-intro">${brand}<p>A clearer first look at housing-loan applications.<br>With the reasoning kept in view.</p><span class="home-footer-tag">${icon("shield")}Built for human review</span></div><nav aria-label="Footer screening links"><h2>Explore</h2>${routeLink("/", "Home")}${routeLink("/workspace", "Workspace")}${routeLink("/assessment", "New assessment")}${routeLink("/batch", "Batch screening")}</nav><nav aria-label="Footer project links"><h2>Understand</h2>${routeLink("/evidence", "Model evidence")}${routeLink("/methodology", "Methodology")}${routeLink("/references", "Design & references")}${routeLink("/#faq", "FAQs")}</nav></div><div class="home-footer-bottom"><span>© ${new Date().getFullYear()} LoanLens · College major project</span><p>Historical approval estimates. Not a bank, a loan offer, or a prediction of repayment.</p></div></div></footer>`;
  const dialog = header.querySelector("dialog");
  const toggle = header.querySelector(".home-menu-toggle");
  toggle.addEventListener("click", () => {
    dialog.showModal();
    toggle.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  });
  header
    .querySelector(".home-menu-close")
    .addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => {
    toggle.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  });
  dialog.addEventListener("click", (event) => {
    if (event.target.closest("a")) dialog.close();
    if (event.target === dialog) {
      const box = dialog.getBoundingClientRect();
      if (
        event.clientX < box.left ||
        event.clientX > box.right ||
        event.clientY < box.top ||
        event.clientY > box.bottom
      )
        dialog.close();
    }
  });
  window.matchMedia("(min-width:821px)").addEventListener("change", (event) => {
    if (event.matches && dialog.open) dialog.close();
  });
}

function statsHTML(data, loading = false) {
  const count = data?.dataset?.total_rows;
  const algorithms = data?.comparison?.length
    ? new Set(data.comparison.map((row) => row.model)).size
    : null;
  const accuracy = data?.metrics?.test_default?.accuracy;
  const missing = loading ? "Loading…" : "Unavailable";
  return `<div class="home-stat"><strong class="${Number.isFinite(count) ? "" : "home-stat-status"}">${Number.isFinite(count) ? number(count) : missing}</strong><span>Real applications in the dataset</span></div><div class="home-stat"><strong class="${algorithms === null ? "home-stat-status" : ""}">${algorithms ?? missing}</strong><span>Machine-learning algorithms compared</span></div><div class="home-stat"><strong class="${Number.isFinite(accuracy) ? "" : "home-stat-status"}">${Number.isFinite(accuracy) ? percent(accuracy) : missing}</strong><span>Holdout accuracy · standard 0.50 policy</span></div>`;
}

export function homePage(main, data, evidencePromise) {
  let disposed = false;
  const controller = new AbortController();
  main.innerHTML = `<div class="home-page">
    <section class="home-hero home-container" aria-labelledby="home-title"><div class="home-hero-copy"><span class="home-eyebrow"><i></i>Housing-loan screening, explained</span><h1 id="home-title">A clearer way to<br><em>screen home loans.</em></h1><p class="home-hero-description">Turn application details into an explainable first look. See the model’s suggestion, understand its reasons, and keep people at the heart of every decision.</p><div class="home-hero-actions"><a class="home-button" href="/assessment" data-route>Start an assessment ${icon("arrow")}</a><a class="home-text-action" href="/#how-it-works" data-route>See how it works <span class="home-circle-arrow">↓</span></a></div><p class="home-reassurance">${icon("shield")}An educational assistant. A human makes the final call.</p></div><figure class="home-hero-figure"><div class="home-image-wrap"><img class="home-hero-image" src="/assets/hero-housing.webp" alt="Illustrative contemporary family home framed by green trees" width="1122" height="1402" fetchpriority="high" decoding="async"><div class="home-image-note"><span>${icon("check")}</span><div><strong>More than a yes or no.</strong><p>A suggestion you can understand.</p></div></div><span class="home-image-label">A thoughtful start to the review.</span></div><figcaption>Illustrative housing scene · not an applicant property</figcaption></figure></section>
    <section class="home-evidence-band" aria-label="Actual project evidence"><div class="home-container"><div class="home-evidence-heading"><span class="home-eyebrow">Built on evidence, not promises</span><a href="/evidence" data-route>Explore the model ${icon("arrow")}</a></div><div class="home-stat-grid" id="home-evidence" aria-live="polite">${statsHTML(data, !data)}</div><p class="home-stat-note">Measured on a held-out dataset. Not a guarantee about any future application.</p></div></section>
    <section class="home-process home-container home-anchor" id="how-it-works" aria-labelledby="home-process-title"><div class="home-section-heading"><div><span class="home-eyebrow">How it works</span><h2 id="home-process-title">From the details<br>to <em>the bigger picture.</em></h2></div><p>A simple path from application information to a transparent screening suggestion.</p></div><ol class="home-steps"><li><div class="home-step-top"><span>01</span>${icon("assess")}</div><h3>Bring the details.</h3><p>Enter income, loan amount, credit history and application information. Or upload a CSV for a batch review.</p><a href="/assessment" data-route>Explore the form ${icon("arrow")}</a></li><li><div class="home-step-top"><span>02</span>${icon("chart")}</div><h3>See the suggestion.</h3><p>The saved model applies its training-time preparation and returns a historical approval score and policy-based suggestion.</p><a href="/workspace" data-route>Open the workspace ${icon("arrow")}</a></li><li><div class="home-step-top"><span>03</span>${icon("book")}</div><h3>Understand the why.</h3><p>Inspect the contributing features with SHAP, check the evidence, and bring your own judgment to the next step.</p><a href="/methodology" data-route>Read the methodology ${icon("arrow")}</a></li></ol></section>
    <section class="home-feature home-anchor" id="features" aria-labelledby="home-feature-title"><div class="home-container home-feature-grid"><div class="home-feature-copy"><span class="home-eyebrow">Why LoanLens</span><h2 id="home-feature-title">See the reasons.<br><em>Keep the judgment.</em></h2><p>A useful screening tool should tell you more than its answer. LoanLens keeps the explanation and the evidence close to the suggestion.</p><ul class="home-feature-list"><li><span>${icon("spark")}</span><div><h3>Explanations, not just labels.</h3><p>Plain-English factors and an actual SHAP waterfall show how a score differs from the training background.</p></div></li><li><span>${icon("batch")}</span><div><h3>One application or a whole file.</h3><p>Use the same trained pipeline for an individual review and a bounded CSV batch, with downloadable results.</p></div></li><li><span>${icon("shield")}</span><div><h3>The limits stay visible.</h3><p>Inspect real validation results, demographic audits and the failed cost experiment. Historical approval is not repayment risk.</p></div></li></ul><a class="home-light-link" href="/evidence" data-route>Inspect the complete evidence ${icon("arrow")}</a></div><section class="home-live-card" aria-labelledby="home-live-title"><div class="home-live-heading"><span class="home-live-badge">Real project example</span><h3 id="home-live-title">Take a closer look.</h3><p>Load a public training-set application and see the same model and explanation used in the workspace.</p><button type="button" class="home-button" id="home-try-example">Try a real example ${icon("arrow")}</button></div><div id="home-demo" class="home-demo" aria-live="polite"><div class="home-demo-empty"><div class="home-demo-icon">${icon("assess")}</div><h4>The reasoning comes with it.</h4><p>The example’s ID, score and explanation will appear here after you load it.</p><div class="home-demo-inputs"><span>${icon("check")}Income & loan</span><span>${icon("check")}Credit history</span><span>${icon("check")}Application profile</span></div></div></div></section></div></section>
    <section class="home-faq home-container home-anchor" id="faq" aria-labelledby="home-faq-title"><div class="home-faq-intro"><span class="home-eyebrow">A few things worth knowing</span><h2 id="home-faq-title">Clear answers.<br><em>No fine-print surprises.</em></h2><p>Understand what this project does—and what it cannot tell you.</p><a class="home-text-action" href="/methodology" data-route>More about the project ${icon("arrow")}</a></div><div class="home-faq-list"><details><summary>Is this an actual lending decision?</summary><p>No. LoanLens is an educational decision-support project. It learns historical approval patterns; it cannot grant a loan, guarantee approval, or measure whether someone will repay.</p></details><details><summary>What information does the model use?</summary><p>Income, loan amount and term, credit-history indicator, education, employment, dependents and property area. Gender and marital status are excluded as predictors and retained only for descriptive audits.</p></details><details><summary>What if some application details are missing?</summary><p>Blank model fields use median or mode values learned from training data. Missing fields are disclosed with the result. An entirely blank application, or demographic audit fields alone, is not enough for a prediction.</p></details><details><summary>Can I review applications in a batch?</summary><p>Yes. Use the downloadable CSV template, upload up to 1,000 applications in a file of at most 5 MB, then review and download the results. The same validation and saved model are used for every row.</p></details><details><summary>Are application details saved?</summary><p>The website processes input in memory and does not maintain an applicant database or account history. If you choose to download results, the CSV is saved by your browser on your device.</p></details><details><summary>Where can I check the model’s performance?</summary><p><a href="/evidence" data-route>Model evidence</a> shows actual held-out results, cross-validation comparisons, error counts and group audits. It also documents the failed cost-threshold policy instead of hiding that trade-off.</p></details></div></section>
    <section class="home-closing home-container"><div class="home-closing-panel"><span class="home-eyebrow">A clearer first step</span><h2>Start with the details.<br><em>Leave with the reasons.</em></h2><p>Explore a single application or bring a CSV. The model’s suggestion is the beginning of the review, not the end.</p><div class="home-closing-actions"><a class="home-button" href="/assessment" data-route>Start an assessment ${icon("arrow")}</a><a class="home-text-action" href="/batch" data-route>Screen a batch ${icon("arrow")}</a></div></div></section>
  </div>`;

  const stats = main.querySelector("#home-evidence");
  evidencePromise.then((resolved) => {
    if (!disposed && stats.isConnected) stats.innerHTML = statsHTML(resolved);
  });
  const button = main.querySelector("#home-try-example");
  const output = main.querySelector("#home-demo");
  button.addEventListener("click", async () => {
    button.disabled = true;
    button.innerHTML =
      '<span class="spinner" aria-hidden="true"></span>Loading the real example…';
    output.setAttribute("aria-busy", "true");
    output.innerHTML =
      '<div class="home-example-loading" role="status"><span class="home-demo-icon">' +
      icon("chart") +
      "</span><p>Running the saved model and calculating its explanation…</p></div>";
    try {
      const example = await request("/api/example", {
        signal: controller.signal,
      });
      const result = await request("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          applicant: example.applicant,
          policy: "standard",
          explain: true,
        }),
        signal: controller.signal,
      });
      if (disposed || !output.isConnected) return;
      output.innerHTML = `<div class="home-demo-source">${icon("check")}Real public training example · ${escapeHTML(example.loan_id)}</div><div class="home-demo-result">${resultHTML(result)}</div><a class="home-demo-next" href="/assessment" data-route>Open a full assessment ${icon("arrow")}</a>`;
    } catch (error) {
      if (error.name === "AbortError" || disposed || !output.isConnected)
        return;
      output.innerHTML = `<div class="home-demo-error">${notice(escapeHTML(error.message), "error")}<p>The website remains available. Try again when the model service is ready.</p></div>`;
    } finally {
      if (!disposed && button.isConnected) {
        button.disabled = false;
        button.innerHTML = `Try a real example ${icon("arrow")}`;
        output.removeAttribute("aria-busy");
      }
    }
  });
  return () => {
    disposed = true;
    controller.abort();
  };
}
