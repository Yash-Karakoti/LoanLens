/** Memory-only CSV processing, real results, and a safe server-generated export. */
import {
  icon,
  escapeHTML,
  percent,
  decimal,
  request,
  notice,
  empty,
  downloadCSV,
} from "./components.js";

export function batchPage(main, evidence) {
  main.innerHTML = `<div class="page-heading"><div><h1>Batch screening</h1><p>A consistent first pass across a CSV of applications.</p></div><a class="button outline" href="/api/template" download>${icon("download")}Download CSV template</a></div>
  <div class="batch-layout"><section class="panel upload-panel"><div class="policy-box"><label for="batch-policy">Screening policy</label><select class="policy-select" id="batch-policy"><option value="standard">Standard screening · 0.50</option><option value="cost">Failed cost experiment · ${decimal(evidence?.model.cost_threshold ?? 0.76, 2)}</option></select><div id="batch-policy-warning" class="policy-warning"></div></div>
  <label class="upload-zone" id="drop-zone" for="csv-file"><span class="upload-icon">${icon("batch")}</span><strong><span class="upload-link">Choose a CSV</span> or drop it here</strong><p>Up to 1,000 applications · 5 MB · UTF-8</p><input id="csv-file" type="file" accept=".csv,text/csv" aria-label="Application CSV"></label><div class="upload-filename" id="upload-filename" aria-live="polite">${icon("file")}No file selected</div><div class="upload-bottom"><span class="quiet-label">${icon("shield")}Processed in memory. Never saved.</span><button class="button primary" id="screen-batch" disabled>${icon("spark")}Screen applications</button></div><div id="batch-error" aria-live="polite" style="margin-top:15px"></div></section>
  <aside class="panel batch-guide"><h2>Ready your application file</h2><p>Use the template to keep field names consistent with the trained pipeline.</p><ul class="check-list"><li>${icon("check")}Include every template column, even when some values are blank.</li><li>${icon("check")}Income uses monthly dataset units. Loan amount is in thousands.</li><li>${icon("check")}Loan terms are in months; credit history is 0 or 1.</li><li>${icon("check")}Blank model values use training-only imputation.</li></ul><div class="notice compact">${icon("info")}<div>A batch suggestion is not a final lending decision. Each application needs human review.</div></div></aside></div>
  <div id="batch-results" class="batch-results" aria-live="polite">${empty("No batch has been screened yet", "Upload a CSV to review approval suggestions and download the results.", "batch")}</div>`;
  const input = main.querySelector("#csv-file"),
    drop = main.querySelector("#drop-zone"),
    submit = main.querySelector("#screen-batch"),
    errorBox = main.querySelector("#batch-error"),
    resultBox = main.querySelector("#batch-results"),
    policy = main.querySelector("#batch-policy");
  let selectedFile = null,
    result = null,
    page = 0,
    revision = 0;
  const pageSize = 20;
  function clearResults() {
    result = null;
    page = 0;
    revision++;
    submit.disabled = !selectedFile;
    submit.innerHTML = `${icon("spark")}Screen applications`;
    resultBox.innerHTML = empty(
      "No batch has been screened yet",
      "Upload a CSV to review approval suggestions and download the results.",
      "batch",
    );
  }
  function chooseFile(file) {
    clearResults();
    errorBox.innerHTML = "";
    selectedFile = null;
    submit.disabled = true;
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      errorBox.innerHTML = notice("Upload a CSV smaller than 5 MB.", "error");
      return;
    }
    selectedFile = file;
    submit.disabled = false;
    main.querySelector("#upload-filename").innerHTML =
      `${icon("file")}<span>${escapeHTML(file.name)} · ${(file.size / 1024).toFixed(1)} KB</span>`;
  }
  input.addEventListener("change", () => chooseFile(input.files[0]));
  for (const eventName of ["dragenter", "dragover"])
    drop.addEventListener(eventName, (event) => {
      event.preventDefault();
      drop.classList.add("drag-over");
    });
  for (const eventName of ["dragleave", "drop"])
    drop.addEventListener(eventName, (event) => {
      event.preventDefault();
      drop.classList.remove("drag-over");
    });
  drop.addEventListener("drop", (event) =>
    chooseFile(event.dataTransfer.files[0]),
  );
  policy.addEventListener("change", () => {
    clearResults();
    main.querySelector("#batch-policy-warning").innerHTML =
      policy.value === "cost"
        ? notice(
            "The saved cost scenario rejects every applicant. It is a documented failed experiment; standard 0.50 is the default policy.",
            "warn",
          )
        : "";
  });
  function renderResults() {
    const summary = result.summary,
      rows = result.rows.slice(page * pageSize, (page + 1) * pageSize),
      pages = Math.ceil(result.rows.length / pageSize);
    resultBox.innerHTML = `<section class="panel"><div class="panel-heading"><h2>Screening results</h2><button class="button outline" id="download-batch">${icon("download")}Download results</button></div><div class="panel-body"><div class="batch-stats"><div>Applications<strong>${summary.total}</strong></div><div>Approved suggestions<strong>${summary.approved}</strong></div><div>Rejected suggestions<strong>${summary.rejected}</strong></div></div><p class="small" style="margin-top:14px">${summary.policy === "standard" ? "Standard screening" : "Failed cost scenario"} · Threshold ${decimal(summary.threshold, 2)} · Rows ${page * pageSize + 1}–${Math.min((page + 1) * pageSize, result.rows.length)}</p></div><div class="table-scroll"><table><caption class="sr-only">Actual screened application results</caption><thead><tr><th scope="col">Application</th><th scope="col" class="numeric">Income</th><th scope="col" class="numeric">Loan amount¹</th><th scope="col">Property</th><th scope="col">Suggestion</th><th scope="col" class="numeric">Approval score</th></tr></thead><tbody>${rows.map((row, index) => `<tr><td>${escapeHTML(row.Loan_ID ?? `Row ${page * pageSize + index + 1}`)}</td><td class="numeric">${escapeHTML(row.ApplicantIncome ?? "Missing")}</td><td class="numeric">${escapeHTML(row.LoanAmount ?? "Missing")}</td><td>${escapeHTML(row.Property_Area ?? "Missing")}</td><td><span class="badge ${row.prediction === "Approved" ? "success" : "warn"}">${escapeHTML(row.prediction)}</span></td><td class="numeric">${percent(row.probability)}</td></tr>`).join("")}</tbody></table></div><div class="pagination"><span>Page ${page + 1} of ${pages} · ¹ Thousands of dataset units</span><div class="pagination-buttons"><button class="button outline" id="previous-page" ${page === 0 ? "disabled" : ""}>Previous</button><button class="button outline" id="next-page" ${page + 1 === pages ? "disabled" : ""}>Next</button></div></div></section>${notice("Model scores describe historical approval patterns, not repayment probabilities. Review each applicant’s source documents.")}`;
    resultBox
      .querySelector("#download-batch")
      .addEventListener("click", () =>
        downloadCSV(result.csv, "loanlens-screening-results.csv"),
      );
    resultBox.querySelector("#previous-page").addEventListener("click", () => {
      page--;
      renderResults();
    });
    resultBox.querySelector("#next-page").addEventListener("click", () => {
      page++;
      renderResults();
    });
  }
  submit.addEventListener("click", async () => {
    if (!selectedFile) return;
    clearResults();
    const current = revision;
    errorBox.innerHTML = "";
    submit.disabled = true;
    submit.innerHTML =
      '<span class="spinner" aria-hidden="true"></span>Screening applications…';
    resultBox.innerHTML =
      '<div class="panel" style="padding:25px" role="status" aria-label="Screening batch"><div class="skeleton text"></div><div class="skeleton block" style="height:150px;margin-top:20px"></div></div>';
    try {
      const response = await request(
        `/api/batch?policy=${encodeURIComponent(policy.value)}`,
        {
          method: "POST",
          headers: { "Content-Type": "text/csv" },
          body: selectedFile,
        },
      );
      if (!resultBox.isConnected || current !== revision) return;
      result = response;
      page = 0;
      renderResults();
    } catch (error) {
      if (!errorBox.isConnected || current !== revision) return;
      clearResults();
      errorBox.innerHTML = notice(escapeHTML(error.message), "error");
    } finally {
      if (submit.isConnected && current === revision) {
        submit.disabled = !selectedFile;
        submit.innerHTML = `${icon("spark")}Screen applications`;
      }
    }
  });
}
