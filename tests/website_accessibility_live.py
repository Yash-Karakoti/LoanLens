"""Run the external axe engine against real rendered website routes."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Check WCAG A/AA rules without adding the audit engine to the website."""
    engine = Path(tempfile.gettempdir()) / "loanlens-axe.min.js"
    if not engine.exists():
        raise FileNotFoundError("Place the published axe-core engine at the temporary path documented in WEBSITE_HANDOFF.md.")
    checks = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        for path in ["/", "/workspace", "/assessment", "/batch", "/evidence", "/methodology", "/references"]:
            page.goto("http://127.0.0.1:8000" + path, wait_until="networkidle")
            expect(page.locator("main h1")).to_be_visible()
            page.add_script_tag(path=str(engine))
            result = page.evaluate("""async () => {
              const result = await axe.run(document, {runOnly: {type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
              return {engine_version: result.testEngine.version, violations: result.violations.map(rule => ({id:rule.id, impact:rule.impact, description:rule.description, nodes:rule.nodes.map(node=>({target:node.target, summary:node.failureSummary}))})), passed_rules:result.passes.length, manual_review_rules:result.incomplete.length};
            }""")
            checks.append({"route": path, **result})
        browser.close()
    report = {"passed": not any(row["violations"] for row in checks), "checks": checks, "limit": "Automated axe checks do not replace a formal accessibility or assistive-technology audit."}
    (ROOT / "reports/website_accessibility.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    assert report["passed"], "Automated accessibility violations remain"


if __name__ == "__main__":
    main()
