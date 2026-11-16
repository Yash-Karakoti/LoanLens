/** The overview uses measured validation results, not invented operating activity. */
import {
  icon,
  percent,
  decimal,
  number,
  stat,
  panel,
  linkButton,
  comparisonTable,
  rocChart,
} from "./components.js";

export function overviewPage(main, data) {
  const metrics = data.metrics.test_default;
  const dataset = data.dataset;
  const approved = dataset.train_approved + dataset.test_approved;
  const rejected = dataset.total_rows - approved;
  const roc = rocChart(data.charts?.roc);
  const plot =
    roc ||
    `<div class="evidence-bars">${[
      ["Accuracy", metrics.accuracy],
      ["Precision", metrics.precision],
      ["Recall", metrics.recall],
      ["F1 score", metrics.f1],
    ]
      .map(
        ([name, value]) =>
          `<div><div class="evidence-bar-label"><span>${name}</span><strong>${percent(value)}</strong></div><div class="bar-track"><span style="width:${value * 100}%"></span></div></div>`,
      )
      .join("")}</div>`;
  main.innerHTML = `
    <div class="page-heading"><div><h1>Screening overview</h1><p>A clear first look. A reason behind every suggestion.</p></div><span class="quiet-label">${icon("shield")}Educational workspace</span></div>
    <div class="action-row"><div class="page-actions">${linkButton("/assessment", "New assessment", "primary", "plus")}${linkButton("/batch", "Upload applications", "", "batch")}${linkButton("/evidence", "Explore evidence", "", "chart")}</div><span class="quiet-label">Dream Housing Finance · Dataset snapshot</span></div>
    <div class="stats-grid">${stat("Applications in dataset", number(dataset.total_rows), `${number(dataset.train_rows)} train · ${number(dataset.test_rows)} held out`, "assess")}${stat("Holdout accuracy", percent(metrics.accuracy), "Standard policy · threshold 0.50", "shield")}${stat("Approval-class F1", decimal(metrics.f1), "Precision and recall combined", "chart")}${stat("ROC-AUC", decimal(metrics.roc_auc), "Ranking across all thresholds", "spark")}</div>
    <div class="dashboard-grid">
      <section class="panel"><div class="panel-heading"><h2>Holdout performance</h2><span class="badge selected">${number(dataset.test_rows)} unseen applications</span></div><div class="metric-hero"><div><strong>${percent(metrics.accuracy)}</strong><p>Accuracy at the standard 0.50 threshold</p></div><span class="legend"><i class="legend-swatch"></i>${roc ? "ROC curve" : "Measured metrics"}</span></div><div class="chart-wrap">${plot}</div><div class="panel-footer"><span>${roc ? "False positive rate → · True positive rate ↑" : "No decorative or simulated data"}</span><a class="text-link" href="/evidence" data-route>View evaluation ${icon("arrow")}</a></div></section>
      <section class="panel"><div class="panel-heading"><h2>Dataset at a glance</h2><span class="quiet-label">Historical labels</span></div><div class="dataset-donut"><div class="donut" style="background:conic-gradient(var(--accent) 0 ${(approved / dataset.total_rows) * 100}%,#e4e7f3 0 100%)" role="img" aria-label="${approved} historically approved and ${rejected} historically rejected applications"><div class="donut-center"><strong>${number(dataset.total_rows)}</strong><span>applications</span></div></div><div class="donut-legend"><div class="donut-legend-row"><div><i class="legend-swatch"></i><span>Approved<small>Historical decision</small></span></div><strong>${number(approved)}</strong></div><div class="donut-legend-row"><div><i class="legend-swatch gray"></i><span>Rejected<small>Historical decision</small></span></div><strong>${number(rejected)}</strong></div></div></div><div class="panel-body"><dl style="margin:0"><div class="detail-row"><dt>Selected algorithm</dt><dd>${data.model.name}</dd></div><div class="detail-row"><dt>Validation protocol</dt><dd>Stratified holdout + 5-fold CV</dd></div><div class="detail-row"><dt>Model inputs</dt><dd>Financial & application features</dd></div></dl></div><div class="panel-footer"><span>Approval data, not repayment outcomes</span><a class="text-link" href="/methodology" data-route>Data notes ${icon("arrow")}</a></div></section>
    </div>
    <section class="panel"><div class="panel-heading"><h2>Algorithms, compared</h2><a class="text-link" href="/evidence" data-route>All ${data.comparison.length} candidates ${icon("arrow")}</a></div>${comparisonTable(data.comparison, 4)}<div class="panel-footer"><span>Selected using training cross-validation F1. The holdout never chose the winner.</span><span class="badge success">Frozen model</span></div></section>
    <div class="callout"><div><div class="callout-title">${icon("assess")}From application details to an explainable suggestion.</div><p>Enter one application or upload a CSV. Inspect the approval score, the threshold, and the features behind it.</p></div>${linkButton("/assessment", "Start an assessment", "outline", "arrow")}</div>`;
}
