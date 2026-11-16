"""Optional live UI check: uv tool run --from playwright python tests/browser_live.py."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Check desktop/mobile workflows using an actual held-out application."""
    with (ROOT / "data/raw/train.csv").open(newline="", encoding="utf-8") as source:
        observed = {row["Loan_ID"]: row for row in csv.DictReader(source)}
    with (ROOT / "reports/holdout_predictions.csv").open(newline="", encoding="utf-8") as source:
        evidence = next(row for row in csv.DictReader(source) if row["predicted_default"] == "1" and all(observed[row["Loan_ID"]].values()))
    row = observed[evidence["Loan_ID"]]
    checks: list[str] = []
    errors: list[str] = []
    destination = ROOT / "reports/figures"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto("http://127.0.0.1:8501", wait_until="networkidle")
        assert response is not None and response.status == 200
        expect(page.get_by_role("heading", name="Clearer screening. Explainable decisions.")).to_be_visible(timeout=90000)
        expect(page.get_by_text("It rejects every possible application.", exact=False)).to_be_visible()
        checks.append("HTTP 200, title and failed-cost-policy warning")
        for label, key in [
            ("Applicant monthly income (dataset units)", "ApplicantIncome"),
            ("Co-applicant monthly income (dataset units)", "CoapplicantIncome"),
            ("Loan amount (thousands of dataset units)", "LoanAmount"),
            ("Loan term (months)", "Loan_Amount_Term"),
        ]:
            page.get_by_role("spinbutton", name=label, exact=True).fill(row[key])
        for label, value in [
            ("Credit history meets guidelines", "Yes" if float(row["Credit_History"]) == 1 else "No"),
            ("Education", row["Education"]), ("Dependents", row["Dependents"]),
            ("Property area", row["Property_Area"]), ("Self-employed", row["Self_Employed"]),
        ]:
            choice = page.get_by_role("combobox", name=label, exact=True)
            choice.fill(value)
            choice.press("ArrowDown")
            choice.press("Enter")
        page.get_by_role("button", name="Predict approval", exact=True).click()
        result = page.get_by_test_id("stMetric").filter(has_text="Historical approval suggestion")
        expect(result).to_contain_text("Approved", timeout=90000)
        expect(page.get_by_test_id("stMetric").filter(has_text="Approval model score")).to_contain_text(f"{float(evidence['probability']):.1%}")
        expect(page.get_by_text("Why this suggestion?", exact=True)).to_be_visible()
        expect(page.get_by_text("Prediction is available, but its SHAP explanation", exact=False)).to_have_count(0)
        expect(page.locator('[data-testid="stImage"] img').first).to_be_visible(timeout=90000)
        checks.append("real applicant score matches saved report; prediction and SHAP render")
        page.get_by_role("heading", name="Screening result", exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(destination / "app_prediction.png"), full_page=True)
        page.get_by_test_id("stMain").evaluate("element => element.scrollTop = 0")
        page.screenshot(path=str(destination / "app_desktop.png"), full_page=True)
        page.get_by_role("tab", name="Batch screening", exact=True).click()
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
        page.locator('input[type="file"]').set_input_files({"name": "observed_application.csv", "mimeType": "text/csv", "buffer": csv_buffer.getvalue().encode()})
        expect(page.get_by_role("button", name="Download screening results")).to_be_visible(timeout=90000)
        expect(page.get_by_test_id("stMetric").filter(has_text="Applications screened")).to_contain_text("1")
        checks.append("real CSV upload, prediction and downloadable result")
        page.get_by_role("tab", name="Model evidence", exact=True).click()
        expect(page.get_by_role("heading", name="Model evidence", exact=True)).to_be_visible()
        expect(page.get_by_text("ROC-AUC:", exact=False)).to_be_visible()
        checks.append("evidence tab renders generated metrics")
        page.set_viewport_size({"width": 390, "height": 844})
        page.get_by_role("tab", name="Single application", exact=True).click()
        expect(page.get_by_role("button", name="Predict approval", exact=True)).to_be_visible()
        assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"), "Mobile horizontal overflow"
        page.get_by_test_id("stMain").evaluate("element => element.scrollTop = 0")
        page.screenshot(path=str(destination / "app_mobile.png"), full_page=True)
        checks.append("390px mobile layout without horizontal page overflow")
        assert not errors, f"Uncaught browser errors: {errors}"
        browser.close()
    report = {"passed": True, "checks": checks, "browser_errors": errors, "real_application_id": row["Loan_ID"], "desktop": [1440, 1100], "mobile": [390, 844]}
    (ROOT / "reports/browser_check.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
