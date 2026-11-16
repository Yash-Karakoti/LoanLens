"""Regression-check async UI state using delayed real API responses."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def check_late_example(page: Page, base: str) -> None:
    """A reset while a genuine example request is pending must remain a reset."""
    pending = []
    page.goto(base + "/assessment", wait_until="networkidle")
    page.route("**/api/example", lambda route: pending.append(route))
    button = page.get_by_role("button", name="Load real example", exact=True)
    button.click()
    expect(button).to_be_disabled()
    page.get_by_role("button", name="Clear application", exact=True).click()
    assert pending
    pending.pop(0).continue_()
    expect(button).to_be_enabled(timeout=30000)
    assert page.locator("#ApplicantIncome").input_value() == "", "Late example overwrote the cleared draft"


def check_batch_overlap(page: Page, base: str, example: dict) -> None:
    """An old real batch response must not clear a newer request's busy state."""
    page.goto(base + "/batch", wait_until="networkidle")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(example["applicant"]))
    writer.writeheader()
    writer.writerow(example["applicant"])
    content = buffer.getvalue().encode()
    pending = []
    page.route("**/api/batch?policy=standard", lambda route: pending.append(route))
    upload = page.get_by_label("Application CSV", exact=True)
    submit = page.locator("#screen-batch")
    upload.set_input_files({"name": "first_real_example.csv", "mimeType": "text/csv", "buffer": content})
    submit.click()
    expect(page.locator("#screen-batch")).to_be_disabled()
    upload.set_input_files({"name": "second_real_example.csv", "mimeType": "text/csv", "buffer": content})
    submit.click()
    expect(page.locator("#screen-batch")).to_be_disabled()
    assert len(pending) == 2
    try:
        with page.expect_response(lambda response: "/api/batch?policy=standard" in response.url) as old_response:
            pending.pop(0).continue_()
        old_response.value.finished()
        page.wait_for_timeout(100)
        assert page.locator("#screen-batch").is_disabled(), "Older batch cleared the newer request's loading state"
    finally:
        if pending:
            pending.pop(0).continue_()
    expect(page.get_by_role("heading", name="Screening results", exact=True)).to_be_visible(timeout=30000)
    expect(page.locator("#screen-batch")).to_be_enabled()


def check_evidence_focus(page: Page, base: str) -> None:
    """Keyboard activation must focus the replacement selected policy button."""
    page.goto(base + "/evidence", wait_until="networkidle")
    button = page.get_by_role("button", name="Cost experiment 0.76", exact=True)
    button.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("button", name="Cost experiment 0.76", exact=True)).to_be_focused(timeout=2000)


def main() -> None:
    """Exercise each race independently; report real failures without fake results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.url.rstrip("/")
    example = json.load(urlopen(base + "/api/example"))
    outcomes = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for name, function in [
            ("late_example_reset", lambda page: check_late_example(page, base)),
            ("overlapping_batch_state", lambda page: check_batch_overlap(page, base, example)),
            ("keyboard_evidence_policy_focus", lambda page: check_evidence_focus(page, base)),
        ]:
            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            try:
                function(page)
                outcomes.append({"name": name, "passed": True})
            except Exception as error:
                outcomes.append({"name": name, "passed": False, "error": str(error)})
            finally:
                page.close()
        browser.close()
    report = {"passed": all(row["passed"] for row in outcomes), "checks": outcomes, "responses": "Genuine API responses delayed at the browser boundary; no replacement model data"}
    (ROOT / "reports/website_state_check.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    assert report["passed"], "Website state regressions failed"


if __name__ == "__main__":
    main()
