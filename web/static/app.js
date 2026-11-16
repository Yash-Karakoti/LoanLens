/** Same-origin router and shared workspace shell. Applicant data stays in memory. */
import { icon, escapeHTML, request, notice } from "./components.js";
import { homePage, mountPublicChrome } from "./home.js";
import { overviewPage } from "./overview.js";
import { assessmentPage } from "./assessment.js";
import { batchPage } from "./batch.js";
import { evidencePage } from "./evidence.js";
import { methodologyPage, referencesPage } from "./information.js";

const routes = {
  "/": { title: "Home", icon: "home", render: homePage },
  "/workspace": { title: "Overview", icon: "chart", render: overviewPage },
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
const toolLabels = {
  "/workspace": "Overview",
  "/assessment": "Assessment",
  "/batch": "Batch",
  "/evidence": "Evidence",
  "/methodology": "Methodology",
  "/references": "References",
};
const navLink = (path, route) =>
  `<a class="nav-link" href="${path}" data-route>${icon(route.icon)}<span>${toolLabels[path]}</span></a>`;
document.querySelector("#app").innerHTML = `
  <div id="public-header"></div>
  <section class="workspace-navigation" id="workspace-navigation" aria-label="Screening workspace">
    <div class="workspace-navigation-inner home-nav-container">
      <span class="workspace-label">Your screening workspace</span>
      <nav class="nav-list" aria-label="Workspace tools">${Object.entries(
        routes,
      )
        .filter(([path]) => path !== "/")
        .map(([path, route]) => navLink(path, route))
        .join("")}</nav>
      <span class="workspace-service"><span class="status-dot" id="service-dot"></span><span id="service-label">Loading model</span></span>
    </div>
  </section>
  <div class="main-wrap"><main id="main" class="workspace-main" tabindex="-1"></main></div>
  <div id="public-footer"></div>`;
mountPublicChrome(
  document.querySelector("#public-header"),
  document.querySelector("#public-footer"),
);

let evidence = null;
let evidenceError = "";
const evidencePromise = request("/api/overview")
  .then((data) => {
    evidence = data;
    document.querySelector("#service-label").textContent = "Model ready";
    return data;
  })
  .catch((error) => {
    evidenceError = error.message;
    document.querySelector("#service-label").textContent = "Model unavailable";
    document.querySelector("#service-dot").style.background = "var(--amber)";
    return null;
  });
let navigationId = 0;
let renderedPath = null;
let cleanupView = null;

function scrollToLocation(focus = false) {
  let hash = "";
  try {
    hash = decodeURIComponent(location.hash.slice(1));
  } catch {
    hash = "";
  }
  const target = hash ? document.getElementById(hash) : null;
  if (target) {
    target.scrollIntoView({ block: "start" });
    if (focus) {
      target.tabIndex = -1;
      target.focus({ preventScroll: true });
    }
  } else {
    window.scrollTo(0, 0);
    if (focus) document.querySelector("#main").focus({ preventScroll: true });
  }
}

async function navigate(path, focus = false) {
  const id = ++navigationId;
  const route = routes[path];
  if (!route) {
    history.replaceState(null, "", "/");
    return navigate("/", focus);
  }
  cleanupView?.();
  cleanupView = null;
  const isHome = path === "/";
  document.body.classList.toggle("is-home", isHome);
  document.querySelector("#workspace-navigation").hidden = isHome;
  document.querySelector("#public-header dialog")?.close();
  document.title = isHome
    ? "LoanLens ? A clearer look at home loans"
    : `${route.title} ? LoanLens`;
  for (const link of document.querySelectorAll(".nav-list a")) {
    const active = link.getAttribute("href") === path;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  const main = document.querySelector("#main");
  renderedPath = path;
  if (isHome) {
    cleanupView = homePage(main, evidence, evidencePromise);
    requestAnimationFrame(() => {
      if (id === navigationId) scrollToLocation(focus);
    });
    return;
  }
  main.innerHTML =
    '<div role="status" aria-label="Loading workspace"><div class="skeleton title"></div><div class="skeleton text"></div><div class="skeleton block" style="margin-top:30px"></div></div>';
  await evidencePromise;
  if (id !== navigationId) return;
  main.innerHTML = "";
  if (!evidence && ["/workspace", "/evidence"].includes(path)) {
    main.innerHTML = `<div class="page-error"><h1>Model evidence is unavailable</h1>${notice(escapeHTML(evidenceError), "error")}<p class="small">The website is running, but the trained artifact or generated reports need attention. Run the project pipeline and restart the service.</p><button class="button outline" id="retry">Try again</button></div>`;
    main
      .querySelector("#retry")
      .addEventListener("click", () => location.reload());
  } else {
    route.render(main, evidence);
  }
  requestAnimationFrame(() => {
    if (id === navigationId) scrollToLocation(focus);
  });
}
document.addEventListener("click", (event) => {
  const anchor =
    event.target instanceof Element
      ? event.target.closest("a[data-route]")
      : null;
  if (
    !anchor ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey ||
    event.button !== 0
  )
    return;
  const url = new URL(anchor.href);
  if (url.origin !== location.origin) return;
  event.preventDefault();
  if (location.pathname === url.pathname && renderedPath === url.pathname) {
    if (location.hash !== url.hash)
      history.pushState(null, "", url.pathname + url.hash);
    document.querySelector("#public-header dialog")?.close();
    scrollToLocation(true);
    return;
  }
  history.pushState(null, "", url.pathname + url.hash);
  navigate(url.pathname, true);
});
window.addEventListener("popstate", () => {
  if (renderedPath === location.pathname) scrollToLocation(true);
  else navigate(location.pathname, true);
});
navigate(location.pathname);
