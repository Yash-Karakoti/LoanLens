"""Check the real website with Playwright: run through its separate uv tool env."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Verify real inference, navigation, exports, invalid inputs and screen sizes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--report", default="website_browser_check.json")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    example = json.load(urlopen(base + "/api/example"))
    truth_request = Request(base + "/api/predict", json.dumps({"applicant": example["applicant"], "explain": False}).encode(), {"Content-Type": "application/json"})
    truth = json.load(urlopen(truth_request))
    checks: list[str] = []
    errors: list[str] = []
    screen_checks: list[dict] = []
    figures = ROOT / "reports/figures"
    tag = "container" if ":8001" in base else "native"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base, wait_until="networkidle")
        expect(page.get_by_role("heading", name="Screening overview", exact=True)).to_be_visible()
        expect(page.get_by_text("614", exact=True).first).to_be_visible()
        expect(page.get_by_text("88.6%", exact=True).first).to_be_visible()
        expect(page.locator("svg.roc-chart")).to_be_visible()
        design = page.evaluate("""() => {
          const s = selector => getComputedStyle(document.querySelector(selector));
          return {sidebar_width: document.querySelector('.sidebar').getBoundingClientRect().width,
            title_size: s('h1').fontSize, title_line_height: s('h1').lineHeight,
            primary_color: s('.button.primary').backgroundColor,
            panel_radius: s('.panel').borderRadius, panel_border: s('.panel').borderColor,
            main_background: s('body').backgroundColor,
            active_nav_radius: s('.nav-link.active').borderRadius,
            content_width: document.querySelector('.workspace-main').getBoundingClientRect().width - parseFloat(s('.workspace-main').paddingLeft) - parseFloat(s('.workspace-main').paddingRight),
            first_panel_width: document.querySelector('.dashboard-grid .panel').getBoundingClientRect().width};
        }""")
        assert design["sidebar_width"] == 220
        assert design["title_size"] == "28px" and design["title_line_height"] == "36px"
        assert design["primary_color"] == "rgb(82, 102, 235)"
        assert design["panel_radius"] == "12px" and design["active_nav_radius"] == "8px"
        assert design["main_background"] == "rgb(255, 255, 255)"
        assert design["content_width"] == 968
        page.screenshot(path=str(figures / f"website_overview_{tag}.png"), full_page=True)
        checks.append("reference tokens: 220px rail, 28/36 title, #5266eb action, 12px panels, 8px nav, white canvas")
        page.get_by_role("link", name="New assessment", exact=True).last.click()
        expect(page).to_have_url(base + "/assessment")
        page.get_by_role("button", name="Load real example", exact=True).click()
        expect(page.locator("#example-source")).to_contain_text(example["loan_id"])
        with page.expect_response(lambda response: response.url == base + "/api/predict" and response.request.method == "POST", timeout=120000) as response_info:
            page.get_by_role("button", name="Generate assessment", exact=True).click()
        assert response_info.value.status == 200
        result = response_info.value.json()
        assert abs(result["probability"] - truth["probability"]) < 1e-12
        expect(page.locator("#assessment-result .decision")).to_contain_text(truth["prediction"])
        expect(page.locator("#assessment-result .score-row")).to_contain_text(f"{truth['probability']:.1%}")
        page.get_by_text("Inspect the SHAP waterfall", exact=True).click()
        image = page.locator("img.shap-image")
        expect(image).to_be_visible()
        assert image.evaluate("image => image.complete && image.naturalWidth > 0")
        reconstruction = result["explanation"]["base_value"] + sum(item["value"] for item in result["explanation"]["contributions"])
        assert abs(reconstruction - result["probability"]) < 1e-6
        page.screenshot(path=str(figures / f"website_assessment_{tag}.png"), full_page=True)
        checks.append("labeled real training example: rendered score agrees with model API; additive SHAP PNG and reasons")
        page.locator("#policy").select_option("cost")
        expect(page.locator("#policy-warning")).to_contain_text("rejects every applicant")
        expect(page.locator("#assessment-result .decision")).to_have_count(0)
        page.get_by_role("button", name="Generate assessment", exact=True).click()
        expect(page.locator("#assessment-result .decision")).to_contain_text("Rejected", timeout=120000)
        expect(page.locator("#assessment-result .score-row")).to_contain_text("0.76")
        page.get_by_role("button", name="Clear application", exact=True).click()
        page.get_by_role("button", name="Generate assessment", exact=True).click()
        expect(page.locator("#form-error").get_by_role("alert")).to_be_visible(timeout=60000)
        expect(page.locator("#assessment-result .decision")).to_have_count(0)
        checks.append("cost policy failure is visible; policy changes and invalid submissions clear stale results")
        page.locator('.nav-list a[href="/batch"]').click()
        expect(page).to_have_url(base + "/batch")
        with page.expect_download() as template_info:
            page.get_by_role("link", name="Download CSV template", exact=True).click()
        assert template_info.value.suggested_filename.endswith(".csv")
        content = io.StringIO()
        row = {"Loan_ID": example["loan_id"], **example["applicant"]}
        writer = csv.DictWriter(content, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
        page.get_by_label("Application CSV", exact=True).set_input_files({"name": "real_training_example.csv", "mimeType": "text/csv", "buffer": content.getvalue().encode()})
        page.get_by_role("button", name="Screen applications", exact=True).click()
        expect(page.get_by_role("heading", name="Screening results", exact=True)).to_be_visible(timeout=60000)
        expect(page.locator("#batch-results tbody")).to_contain_text(example["loan_id"])
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download results", exact=True).click()
        exported = Path(download_info.value.path()).read_text(encoding="utf-8-sig")
        assert "probability" in exported and example["loan_id"] in exported
        checks.append("actual CSV upload, real result table, blank template and prediction export")
        page.get_by_label("Application CSV", exact=True).set_input_files({"name": "duplicate_test.csv", "mimeType": "text/csv", "buffer": b"ApplicantIncome,ApplicantIncome\n1,2\n"})
        page.get_by_role("button", name="Screen applications", exact=True).click()
        expect(page.locator("#batch-error")).to_contain_text("Duplicate column", timeout=60000)
        expect(page.get_by_role("button", name="Download results", exact=True)).to_have_count(0)
        checks.append("duplicate-header CSV rejected with visible error and no stale downloadable result")
        page.locator('.nav-list a[href="/evidence"]').click()
        expect(page.get_by_role("heading", name="Model evidence", exact=True)).to_be_visible()
        expect(page.locator(".matrix-cell")).to_have_count(4)
        page.get_by_role("button", name="Cost experiment 0.76", exact=True).click()
        expect(page.locator(".matrix-cell").filter(has_text="False rejection")).to_contain_text("85")
        page.get_by_role("button", name="Standard 0.50", exact=True).click()
        expect(page.locator(".matrix-cell").filter(has_text="False approval")).to_contain_text("11")
        checks.append("evidence policy controls render actual default and failed-cost confusion counts")
        page.go_back()
        expect(page).to_have_url(base + "/batch")
        page.go_forward()
        expect(page).to_have_url(base + "/evidence")
        page.reload(wait_until="networkidle")
        expect(page.get_by_role("heading", name="Model evidence", exact=True)).to_be_visible()
        checks.append("browser back/forward and direct route refresh preserve working navigation")
        for width, height in [(320, 850), (390, 844), (768, 1024), (1024, 900), (1440, 1100)]:
            page.set_viewport_size({"width": width, "height": height})
            for path in ["/", "/assessment", "/batch", "/evidence", "/methodology", "/references"]:
                page.goto(base + path, wait_until="networkidle")
                expect(page.locator("main h1")).to_be_visible()
                assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"), f"Horizontal page overflow: {width}px {path}"
                screen_checks.append({"width": width, "route": path, "horizontal_overflow": False})
            if width == 390:
                page.goto(base + "/assessment", wait_until="networkidle")
                page.get_by_role("button", name="Open navigation", exact=True).click()
                expect(page.locator("#sidebar")).to_have_attribute("aria-modal", "true")
                page.keyboard.press("Escape")
                expect(page.get_by_role("button", name="Open navigation", exact=True)).to_be_focused()
                page.screenshot(path=str(figures / f"website_mobile_{tag}.png"), full_page=True)
                checks.append("mobile navigation opens as a focus-managed dialog; Escape restores focus")
        assert page.evaluate("Object.keys(localStorage).length") == 0
        assert not errors, f"Uncaught JavaScript errors: {errors}"
        browser.close()
    report = {"passed": True, "base_url": base, "real_application_id": example["loan_id"], "checks": checks, "design_measurements": design, "responsive_checks": screen_checks, "uncaught_javascript_errors": errors}
    (ROOT / "reports" / args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
