"""Combine actual browser, pytest, accessibility and container evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONTAINER = "loanlens-web-verify-20261116"


def read_report(name: str) -> dict:
    """Accept the UTF-8 BOM written by Windows shell tools as well as plain UTF-8."""
    return json.loads((ROOT / "reports" / name).read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    """Identify unchanged source and immutable project artifacts."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def api_prediction(base: str) -> dict:
    """Use the same genuine public training example on both runtime platforms."""
    example = json.load(urlopen(base + "/api/example"))
    payload = json.dumps({"applicant": example["applicant"], "explain": False}).encode()
    request = Request(base + "/api/predict", payload, {"Content-Type": "application/json"})
    return {"loan_id": example["loan_id"], **json.load(urlopen(request))}


def main() -> None:
    """Assert every recorded success against generated evidence and running services."""
    suites = list(ET.parse(ROOT / "reports/website_pytest_results.xml").getroot().iter("testsuite"))
    tests = sum(int(suite.get("tests", 0)) for suite in suites)
    failures = sum(int(suite.get("failures", 0)) + int(suite.get("errors", 0)) for suite in suites)
    skipped = sum(int(suite.get("skipped", 0)) for suite in suites)
    assert tests == 62 and failures == skipped == 0
    native = read_report("website_browser_check.json")
    container_browser = read_report("website_container_browser_check.json")
    accessibility = read_report("website_accessibility.json")
    state = read_report("website_state_check.json")
    assert native["passed"] and container_browser["passed"] and accessibility["passed"] and state["passed"]
    assert len(native["responsive_checks"]) == len(container_browser["responsive_checks"]) == 30
    baseline = read_report("website_baseline.json")
    assert digest(ROOT / "data/raw/train.csv") == baseline["raw_sha256"]
    assert digest(ROOT / "models/best_model.joblib") == baseline["model_sha256"]
    inspection = json.loads(subprocess.check_output(["docker", "inspect", CONTAINER], text=True))[0]
    assert inspection["State"]["Health"]["Status"] == "healthy"
    assert inspection["HostConfig"]["ReadonlyRootfs"]
    uid = int(subprocess.check_output(["docker", "exec", CONTAINER, "id", "-u"], text=True))
    assert uid != 0
    environment_port = next(value for value in inspection["Config"]["Env"] if value.startswith("PORT="))
    assert environment_port == "PORT=8080"
    code = """import hashlib,json,pathlib,platform
root=pathlib.Path('/app')
files={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (root/'web').rglob('*') if path.is_file() and path.suffix in ['.py','.js','.css','.html','.svg']}
print(json.dumps({'files':files,'raw_sha256':hashlib.sha256((root/'data/raw/train.csv').read_bytes()).hexdigest(),'model_sha256':hashlib.sha256((root/'models/best_model.joblib').read_bytes()).hexdigest(),'python':platform.python_version()}))"""
    image_data = json.loads(subprocess.check_output(["docker", "exec", CONTAINER, "python", "-c", code], text=True))
    source = {path.relative_to(ROOT).as_posix(): digest(path) for path in (ROOT / "web").rglob("*") if path.is_file() and path.suffix in [".py", ".js", ".css", ".html", ".svg"]}
    assert source == image_data["files"], "Container source differs from the verified local website"
    assert image_data["raw_sha256"] == baseline["raw_sha256"]
    assert image_data["model_sha256"] == baseline["model_sha256"]
    native_prediction = api_prediction("http://127.0.0.1:8000")
    container_prediction = api_prediction("http://127.0.0.1:8001")
    assert native_prediction["loan_id"] == container_prediction["loan_id"]
    difference = abs(native_prediction["probability"] - container_prediction["probability"])
    assert difference < 1e-12 and native_prediction["prediction"] == container_prediction["prediction"]
    report = {
        "passed": True, "pytest": {"tests": tests, "failures_and_errors": failures, "skipped": skipped},
        "native_browser": native, "container_browser": container_browser,
        "async_state_regressions": state,
        "accessibility": {"engine_version": accessibility["checks"][0]["engine_version"], "routes": len(accessibility["checks"]), "violations": sum(len(check["violations"]) for check in accessibility["checks"]), "limit": accessibility["limit"]},
        "container": {"running_during_verification": True, "image_id": inspection["Image"], "runtime_uid": uid, "read_only_filesystem": True, "health": "healthy", "port_environment_tested": 8080, "matching_source_files": len(source), "python": image_data["python"]},
        "native_python": sys.version, "raw_sha256": baseline["raw_sha256"], "model_sha256": baseline["model_sha256"],
        "raw_and_model_unchanged": True, "cross_platform_probability_difference": difference,
        "cloud_publication_performed": False,
        "verified_utc": datetime.now(timezone.utc).isoformat(),
    }
    (ROOT / "reports/website_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "tests": tests, "responsive_checks_per_runtime": 30, "axe_violations": report["accessibility"]["violations"], "cross_platform_probability_difference": difference, "container": report["container"]}, indent=2))


if __name__ == "__main__":
    main()
