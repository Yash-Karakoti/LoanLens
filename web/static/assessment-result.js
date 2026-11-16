/** Render a real prediction and its probability-space SHAP explanation. */
import { icon, escapeHTML, percent, decimal, notice } from "./components.js";
export function resultHTML(result) {
  const rejected = result.prediction === "Rejected";
  const explanation = result.explanation;
  const contributions = [...(explanation?.contributions || [])]
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 3);
  const largest = Math.max(
    ...contributions.map((item) => Math.abs(item.value)),
    0.000001,
  );
  return `<div class="result-top"><div class="decision-label">Historical approval suggestion</div><div class="decision ${rejected ? "rejected" : ""}"><span class="decision-symbol">${icon(rejected ? "close" : "check")}</span><span>${escapeHTML(result.prediction)}</span></div><p class="decision-caption">A screening suggestion for a human reviewer.</p><div class="score-row"><div><span>Approval model score</span><strong>${percent(result.probability)}</strong></div><div><span>Active threshold</span><strong>${decimal(result.threshold, 2)}</strong></div></div><div class="score-track" style="--threshold:${result.threshold * 100}%"><span style="width:${result.probability * 100}%"></span></div><div class="score-key"><span>0%</span><span>Threshold marked</span><span>100%</span></div></div>
  ${result.missing_fields.length ? `<div class="result-reasons">${notice(`${result.missing_fields.length} missing model fields used values learned from training data. No new financial facts were collected.`, "warn")}</div>` : ""}
  ${explanation ? `<div class="result-reasons"><h3>What contributed to this score?</h3><ul class="reason-list">${explanation.reasons.map((reason) => `<li>${icon("spark")}<span>${escapeHTML(reason)}</span></li>`).join("")}</ul>${contributions.map((item) => `<div class="contribution-row"><div class="contribution-top"><span>${escapeHTML(item.feature)}</span><strong>${item.value > 0 ? "+" : ""}${(item.value * 100).toFixed(2)} pp</strong></div><div class="contribution-bar ${item.value < 0 ? "negative" : ""}"><span style="width:${(Math.abs(item.value) / largest) * 100}%"></span></div></div>`).join("")}</div><details class="shap-details"><summary>Inspect the SHAP waterfall</summary><img class="shap-image" src="${escapeHTML(explanation.image)}" alt="Actual SHAP waterfall: feature contributions from the training baseline to this applicant's approval score"><p class="small" style="margin-top:10px">Training background score: ${percent(explanation.base_value)}. Associations are not causes.</p></details>` : `<div class="result-reasons">${notice("Prediction available without a SHAP explanation.")}</div>`}
  <p class="result-disclaimer">The score is not a probability of repayment or a bank commitment. Verify documents before any lending decision.</p>`;
}
