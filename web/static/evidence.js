/** Evaluation views display the frozen holdout and training-CV evidence verbatim. */
import {
  icon,
  escapeHTML,
  percent,
  decimal,
  stat,
  comparisonTable,
  notice,
} from "./components.js";
let selectedPolicy = "default";

function matrixHTML(matrix) {
  const [[tn, fp], [fn, tp]] = matrix;
  return `<div class="confusion-layout" role="img" aria-label="Confusion matrix: ${tn} true rejections, ${fp} false approvals, ${fn} false rejections, ${tp} true approvals"><span class="matrix-y" aria-hidden="true">Historical decision</span><div class="matrix" aria-hidden="true"><span></span><span class="matrix-axis">Rejected</span><span class="matrix-axis">Approved</span><span class="matrix-axis">Rejected</span><div class="matrix-cell correct"><strong>${tn}</strong><small>True rejection</small></div><div class="matrix-cell incorrect"><strong>${fp}</strong><small>False approval</small></div><span class="matrix-axis">Approved</span><div class="matrix-cell incorrect"><strong>${fn}</strong><small>False rejection</small></div><div class="matrix-cell correct"><strong>${tp}</strong><small>True approval</small></div><div class="matrix-x">Model suggestion →</div></div></div>`;
}

export function evidencePage(main, data) {
  const metrics = data.metrics,
    active =
      selectedPolicy === "default" ? metrics.test_default : metrics.test_tuned;
  const matrix =
    selectedPolicy === "default"
      ? metrics.confusion_matrix
      : metrics.confusion_matrix_tuned;
  const threshold =
    selectedPolicy === "default" ? 0.5 : data.model.cost_threshold;
  const plots = data.figures.filter((figure) =>
    [
      "roc_curve.png",
      "pr_curve.png",
      "shap_summary.png",
      "threshold_cost.png",
    ].includes(figure.name),
  );
  const plotTitles = {
    "roc_curve.png": "ROC curve · holdout",
    "pr_curve.png": "Precision–recall · holdout",
    "shap_summary.png": "Global feature explanations",
    "threshold_cost.png": "Cost threshold · training OOF",
  };
  main.innerHTML = `<div class="page-heading"><div><h1>Model evidence</h1><p>Real results. A frozen holdout. Every trade-off in view.</p></div><div class="toggle-row" role="group" aria-label="Evaluation policy"><button data-policy="default" aria-pressed="${selectedPolicy === "default"}">Standard 0.50</button><button data-policy="tuned" aria-pressed="${selectedPolicy === "tuned"}">Cost experiment ${decimal(data.model.cost_threshold, 2)}</button></div></div>
  <div class="stats-grid">${stat("Holdout accuracy", percent(active.accuracy), `${metrics.n_test} unseen applications`, "shield")}${stat("Approval precision", percent(active.precision), "Historically approved among suggestions", "assess")}${stat("Approval recall", percent(active.recall), "Historical approvals identified", "chart")}${stat("Approval-class F1", decimal(active.f1), "Combined precision and recall", "spark")}</div>
  ${selectedPolicy === "tuned" ? notice("This training-selected cost policy failed: its threshold exceeds every possible score from the fitted tree and rejects all applicants. It remains visible as an experiment, not a recommended policy.", "warn") : ""}
  <div class="evidence-top"><section class="panel"><div class="panel-heading"><h2>What the model got right—and wrong</h2><span class="quiet-label">Threshold ${decimal(threshold, 2)}</span></div>${matrixHTML(matrix)}<div class="panel-footer"><span>Approval is the positive class.</span><span>${active.false_approvals} false approvals · ${active.false_rejections} false rejections</span></div></section>
  <section class="panel policy-card"><h2>Why the decision threshold matters</h2><p>A training-only cost experiment assumed five units per false approval and one per false rejection. These are illustrative units, not measured money or defaults.</p><div class="policy-metrics"><div><span>Standard cost</span><strong>${metrics.test_default.cost}</strong></div><div><span>Experiment cost</span><strong>${metrics.test_tuned.cost}</strong></div><div><span>Baseline cost</span><strong>${metrics.majority_baseline.cost}</strong></div></div>${notice("The saved cost experiment rejects everyone. The website uses fixed 0.50 by default; no replacement threshold was fitted on the holdout.", "warn")}<div class="policy-compare">Always-approve baseline: accuracy ${percent(metrics.majority_baseline.accuracy)} · F1 ${decimal(metrics.majority_baseline.f1)}. Model ROC-AUC ${decimal(active.roc_auc)} is unchanged by threshold.</div></section></div>
  <section class="panel"><div class="panel-heading"><h2>Every algorithm, on the same training folds</h2><span class="quiet-label">5-fold stratified CV</span></div>${comparisonTable(data.comparison)}<div class="panel-footer"><span>Model selection uses CV F1. ROC-AUC breaks ties. Test performance never selected the winner.</span></div></section>
  <section class="panel"><div class="panel-heading"><h2>Group audit</h2><span class="quiet-label">Descriptive, not a fairness certificate</span></div><div class="panel-body"><p class="small">Gender and Married are excluded from predictors. Historical bias and proxy features can still affect outcomes. Groups below 30 rows are flagged.</p></div><div class="table-scroll"><table><caption class="sr-only">Actual and predicted approval rates by demographic group</caption><thead><tr><th scope="col">Audit field</th><th scope="col">Group</th><th scope="col" class="numeric">Rows</th><th scope="col" class="numeric">Historical approval</th><th scope="col" class="numeric">Predicted approval</th><th scope="col" class="numeric">True-positive rate</th><th scope="col">Sample note</th></tr></thead><tbody>${data.fairness.map((row) => `<tr><td>${escapeHTML(row.attribute)}</td><td>${escapeHTML(row.group)}</td><td class="numeric">${row.n}</td><td class="numeric">${percent(row.historical_approval_rate)}</td><td class="numeric">${percent(row[`predicted_approval_rate_${selectedPolicy}`])}</td><td class="numeric">${percent(row[`tpr_${selectedPolicy}`])}</td><td>${row.small_group ? '<span class="badge warn">Small group</span>' : '<span class="muted">Descriptive only</span>'}</td></tr>`).join("")}</tbody></table></div></section>
  <div class="section-intro"><h2>Inspect the generated evidence</h2><p>These plots were generated by the project’s actual evaluation and explanation code.</p></div><div class="plot-grid">${plots.map((figure) => `<section class="panel"><div class="panel-heading"><h2>${plotTitles[figure.name]}</h2><a class="text-link" href="${escapeHTML(figure.url)}" target="_blank" rel="noopener" aria-label="Open ${plotTitles[figure.name]} full size">${icon("globe")}</a></div><img class="plot-image" src="${escapeHTML(figure.url)}" alt="${plotTitles[figure.name]}, generated from the actual frozen experiment" loading="lazy"></section>`).join("")}</div>`;
  for (const button of main.querySelectorAll("[data-policy]"))
    button.addEventListener("click", () => {
      selectedPolicy = button.dataset.policy;
      const footer = main.querySelector(".footer");
      evidencePage(main, data);
      if (footer) main.append(footer);
      main.querySelector(`[data-policy="${selectedPolicy}"]`).focus({ preventScroll: true });
    });
}
