/** Same-origin router and shared workspace shell. Applicant data stays in memory. */
import { icon, escapeHTML, request, notice } from "./components.js";
import { overviewPage } from "./overview.js";
import { assessmentPage } from "./assessment.js";
import { batchPage } from "./batch.js";
import { evidencePage } from "./evidence.js";
import { methodologyPage, referencesPage } from "./information.js";

const routes = {
  "/": { title: "Overview", icon: "home", render: overviewPage },
  "/assessment": {
    title: "New assessment",
    icon: "assess",
    render: assessmentPage,
  },
  "/batch": { title: "Batch screening", icon: "batch", render: batchPage },
  "/evidence": { title: "Model evidence", icon: "chart", render: evidencePage },
  "/methodology": {
    title: "Methodology",
    icon: "book",
    render: methodologyPage,
  },
  "/references": {
    title: "Design & references",
    icon: "link",
    render: referencesPage,
  },
};
const navLink = (path, route) =>
  `<a class="nav-link" href="${path}" data-route>${icon(route.icon)}<span>${route.title}</span></a>`;
document.querySelector("#app").innerHTML = `
  <button class="drawer-shade" aria-label="Close navigation" tabindex="-1"></button>
  <aside class="sidebar" id="sidebar" aria-label="Workspace navigation">
    <a class="brand" href="/" data-route><span class="brand-mark"><img src="/assets/mark.svg" alt=""></span><strong>LoanLens</strong><span class="badge">LAB</span></a>
    <button class="mobile-close" aria-label="Close navigation">${icon("close")}</button>
    <div class="workspace-switch"><a href="/" data-route>Screening</a><a href="/methodology" data-route>Research</a></div>
    <div class="nav-label">Workspace</div>
    <nav class="nav-list" aria-label="Screening">${Object.entries(routes)
      .slice(0, 4)
      .map(([path, route]) => navLink(path, route))
      .join("")}</nav>
    <div class="nav-divider"></div><div class="nav-label">Resources</div>
    <nav class="nav-list" aria-label="Resources">${Object.entries(routes)
      .slice(4)
      .map(([path, route]) => navLink(path, route))
      .join("")}</nav>
    <div class="sidebar-bottom"><div class="sidebar-help"><strong>Understand every suggestion.</strong><p>Explore how the model learns, what it measures, and where it falls short.</p><a href="/methodology" data-route>Read the project guide ${icon("arrow")}</a></div><div class="workspace-status"><span class="status-dot" id="service-dot"></span><span id="service-label">Local workspace</span></div><small>Educational decision support</small></div>
  </aside>
  <header class="topbar"><button class="mobile-menu" aria-label="Open navigation" aria-controls="sidebar" aria-expanded="false">${icon("menu")}</button><div class="breadcrumb"><span class="workspace-word">Workspace</span><span class="slash workspace-word">/</span><span class="breadcrumb-current">Overview</span></div><div class="topbar-actions"><a class="topbar-link" href="/methodology" data-route>${icon("book")}<span>Project guide</span></a><span class="mode-label">${icon("shield")}Human review required</span></div></header>
  <div class="main-wrap"><main id="main" class="workspace-main" tabindex="-1"></main></div>`;

const sidebar = document.querySelector(".sidebar");
const toggle = document.querySelector(".mobile-menu");
const shade = document.querySelector(".drawer-shade");
const mobile = window.matchMedia("(max-width:700px)");
let drawerOpen = false;
function closeDrawer(restoreFocus = true) {
  drawerOpen = false;
  sidebar.classList.remove("open");
  shade.classList.remove("open");
  toggle.setAttribute("aria-expanded", "false");
  sidebar.removeAttribute("role");
  sidebar.removeAttribute("aria-modal");
  sidebar.inert = mobile.matches;
  sidebar.setAttribute("aria-hidden", mobile.matches ? "true" : "false");
  document.querySelector(".main-wrap").inert = false;
  document.querySelector(".topbar").inert = false;
  document.body.style.overflow = "";
  if (restoreFocus && mobile.matches) toggle.focus();
}
function openDrawer() {
  drawerOpen = true;
  sidebar.inert = false;
  sidebar.setAttribute("aria-hidden", "false");
  sidebar.setAttribute("role", "dialog");
  sidebar.setAttribute("aria-modal", "true");
  sidebar.classList.add("open");
  shade.classList.add("open");
  toggle.setAttribute("aria-expanded", "true");
  document.querySelector(".main-wrap").inert = true;
  document.querySelector(".topbar").inert = true;
  document.body.style.overflow = "hidden";
  sidebar.querySelector(".mobile-close").focus();
}
toggle.addEventListener("click", openDrawer);
shade.addEventListener("click", () => closeDrawer());
sidebar
  .querySelector(".mobile-close")
  .addEventListener("click", () => closeDrawer());
mobile.addEventListener("change", () => closeDrawer(false));
closeDrawer(false);
document.addEventListener("keydown", (event) => {
  if (!drawerOpen) return;
  if (event.key === "Escape") {
    event.preventDefault();
    closeDrawer();
  }
  if (event.key === "Tab") {
    const items = [...sidebar.querySelectorAll("a,button")].filter(
      (item) => item.getClientRects().length,
    );
    if (event.shiftKey && document.activeElement === items[0]) {
      event.preventDefault();
      items.at(-1).focus();
    } else if (!event.shiftKey && document.activeElement === items.at(-1)) {
      event.preventDefault();
      items[0].focus();
    }
  }
});

let evidence = null;
let evidenceError = "";
const evidencePromise = request("/api/overview")
  .then((data) => {
    evidence = data;
    return data;
  })
  .catch((error) => {
    evidenceError = error.message;
    document.querySelector("#service-label").textContent = "Model unavailable";
    document.querySelector("#service-dot").style.background = "var(--amber)";
    return null;
  });
let navigationId = 0;
async function navigate(path, focus = false) {
  const id = ++navigationId;
  const route = routes[path];
  if (!route) {
    history.replaceState(null, "", "/");
    return navigate("/", focus);
  }
  closeDrawer(false);
  document.title = `${route.title} · LoanLens`;
  document.querySelector(".breadcrumb-current").textContent = route.title;
  for (const link of sidebar.querySelectorAll("[data-route]")) {
    const active =
      link.classList.contains("nav-link") && link.getAttribute("href") === path;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  const main = document.querySelector("#main");
  main.innerHTML =
    '<div role="status" aria-label="Loading workspace"><div class="skeleton title"></div><div class="skeleton text"></div><div class="skeleton block" style="margin-top:30px"></div></div>';
  await evidencePromise;
  if (id !== navigationId) return;
  main.innerHTML = "";
  if (!evidence && ["/", "/evidence"].includes(path)) {
    main.innerHTML = `<div class="page-error"><h1>Model evidence is unavailable</h1>${notice(escapeHTML(evidenceError), "error")}<p class="small">The website is running, but the trained artifact or generated reports need attention. Run the project pipeline and restart the service.</p><button class="button outline" id="retry">Try again</button></div>`;
    main
      .querySelector("#retry")
      .addEventListener("click", () => location.reload());
  } else {
    route.render(main, evidence);
    main.insertAdjacentHTML(
      "beforeend",
      `<footer class="footer"><span>${icon("shield")}Historical approval estimates. A person makes the final decision.</span><a href="/methodology" data-route>Model scope & limitations ${icon("arrow")}</a></footer>`,
    );
  }
  window.scrollTo(0, 0);
  if (focus) main.focus({ preventScroll: true });
}
document.addEventListener("click", (event) => {
  const anchor = event.target.closest("a[data-route]");
  if (
    !anchor ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey ||
    event.button !== 0
  )
    return;
  event.preventDefault();
  const path = new URL(anchor.href).pathname;
  if (location.pathname !== path) history.pushState(null, "", path);
  navigate(path, true);
});
window.addEventListener("popstate", () => navigate(location.pathname, true));
navigate(location.pathname);
