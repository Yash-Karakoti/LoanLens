/** Small, dependency-free presentation helpers. All values come from API evidence. */
export const escapeHTML = (value = "") =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        character
      ],
  );
export const percent = (value, digits = 1) =>
  Number.isFinite(Number(value)) && value !== null
    ? `${(Number(value) * 100).toFixed(digits)}%`
    : "Unavailable";
export const decimal = (value, digits = 3) =>
  Number.isFinite(Number(value)) && value !== null
    ? Number(value).toFixed(digits)
    : "—";
export const number = (value) => Number(value ?? 0).toLocaleString("en-US");

const paths = {
  home: '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z"/><path d="M9 21v-8h6v8"/>',
  assess:
    '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>',
  batch:
    '<path d="M12 16V3m-4 4 4-4 4 4M4 14v6a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-6"/>',
  chart: '<path d="M4 3v17h17M8 15l4-5 4 2 5-7"/>',
  book: '<path d="M3 4h6a3 3 0 0 1 3 3v14a3 3 0 0 0-3-3H3Zm18 0h-6a3 3 0 0 0-3 3v14a3 3 0 0 1 3-3h6Z"/>',
  link: '<path d="m10 13 4-4m-6 7-1 1a4 4 0 0 1-6-6l4-4a4 4 0 0 1 6 0m2 2 1-1a4 4 0 0 1 6 6l-4 4a4 4 0 0 1-6 0"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  download: '<path d="M12 3v12m-4-4 4 4 4-4M4 16v4h16v-4"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  shield:
    '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v1"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  reset: '<path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/>',
  spark:
    '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"/>',
  file: '<path d="M14 3H5v18h14V8Zm0 0v5h5M8 12h8M8 16h5"/>',
  globe:
    '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c5 5 5 13 0 18-5-5-5-13 0-18"/>',
};
export const icon = (name, className = "") =>
  `<svg class="icon ${className}" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.file}</svg>`;
export const linkButton = (href, label, type = "", symbol = "arrow") =>
  `<a class="button ${type}" href="${href}" data-route>${icon(symbol)}<span>${escapeHTML(label)}</span></a>`;
export const panel = (title, content, extra = "", className = "") =>
  `<section class="panel ${className}"><div class="panel-heading"><h2>${title}</h2>${extra}</div>${content}</section>`;
export const notice = (text, type = "info") =>
  `<div class="notice ${type}" role="${type === "error" ? "alert" : "note"}">${icon(type === "success" ? "check" : "info")}<div>${text}</div></div>`;
export const empty = (title, text, symbol = "assess") =>
  `<div class="empty-state"><div class="empty-icon">${icon(symbol)}</div><h3>${title}</h3><p>${text}</p></div>`;
export const stat = (label, value, note, symbol) =>
  `<div class="stat"><div class="stat-top"><span>${label}</span>${icon(symbol)}</div><strong>${value}</strong><small>${note}</small></div>`;

export async function request(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { ...options.headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg || String(item)).join("; ")
          : "The service could not complete this request. Please try again.",
    );
  }
  return data;
}

export function downloadCSV(content, filename) {
  const url = URL.createObjectURL(
    new Blob([content], { type: "text/csv;charset=utf-8" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Render actual empirical ROC coordinates; never invent a decorative time series. */
export function rocChart(data) {
  if (!data?.fpr?.length || !data?.tpr?.length) return "";
  const width = 520,
    height = 230,
    left = 32,
    bottom = 25,
    top = 14,
    right = 15;
  const x = (value) => left + Number(value) * (width - left - right);
  const y = (value) =>
    height - bottom - Number(value) * (height - bottom - top);
  const path = data.fpr
    .map(
      (value, index) =>
        `${index ? "L" : "M"}${x(value).toFixed(2)},${y(data.tpr[index]).toFixed(2)}`,
    )
    .join(" ");
  const grids = [0, 0.25, 0.5, 0.75, 1]
    .map(
      (value) =>
        `<line x1="${left}" x2="${width - right}" y1="${y(value)}" y2="${y(value)}" class="chart-grid"/><text x="${left - 8}" y="${y(value) + 3}" text-anchor="end">${value === 0 || value === 1 ? value : ""}</text><text x="${x(value)}" y="${height - 6}" text-anchor="middle">${value}</text>`,
    )
    .join("");
  return `<svg class="roc-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Actual holdout ROC curve. Horizontal axis false positive rate, vertical axis true positive rate.">${grids}<path d="M${x(0)},${y(0)} L${x(1)},${y(1)}" class="chance-line"/><path d="${path} L${x(1)},${y(0)} L${x(0)},${y(0)}Z" class="chart-area"/><path d="${path}" class="chart-line"/></svg>`;
}

export function comparisonTable(rows, limit = rows.length) {
  return `<div class="table-scroll"><table><thead><tr><th scope="col">Algorithm</th><th scope="col">Balancing</th><th scope="col" class="numeric">CV F1</th><th scope="col" class="numeric">CV ROC-AUC</th><th scope="col">Selection</th></tr></thead><tbody>${rows
    .slice(0, limit)
    .map(
      (row, index) =>
        `<tr><td><span class="table-model">${icon(index === 0 ? "shield" : "chart")}<strong>${escapeHTML(row.model)}</strong></span></td><td><span class="muted">${row.strategy === "class_weight" ? "Class weights" : escapeHTML(row.strategy)}</span></td><td class="numeric">${decimal(row.cv_f1)}</td><td class="numeric">${decimal(row.cv_roc_auc)}</td><td>${index === 0 ? '<span class="badge selected">Selected by F1</span>' : '<span class="muted">Compared</span>'}</td></tr>`,
    )
    .join("")}</tbody></table></div>`;
}
