# Custom website handoff

> Historical dashboard-only handoff. The homepage, routes and visual identity have since changed. Read [HOMEPAGE_HANDOFF.md](HOMEPAGE_HANDOFF.md) for the current implementation and fresh verification. Measurements and test counts below describe the earlier revision.

The complete custom LoanLens website is running at **http://127.0.0.1:8000**. It is the primary interface now. The original Streamlit app remains an optional alternative; the fitted model, raw data and scientific results are unchanged.

```powershell
Set-Location 'D:\Koding\Housing Loan Approval Prediction'
.\.venv\Scripts\python.exe -m web
```

The native server was left running. Use this command if the host or process has stopped. See [DEPLOYMENT.md](DEPLOYMENT.md) for fresh setup and container commands.

## What works

| Page | Behavior |
| --- | --- |
| Overview `/` | Actual dataset counts, held-out metrics, empirical ROC curve, label balance and model comparison |
| New assessment `/assessment` | Input form, labeled real training example, standard/cost policies, actual prediction, three SHAP reasons and waterfall |
| Batch screening `/batch` | File selection/drop, CSV template, bounded submission, paginated real results and safe export |
| Model evidence `/evidence` | Default/cost matrices, comparison table, error trade-offs, demographic audit and diagnostic figures |
| Methodology `/methodology` | Pipeline, assumptions, feature engineering, threshold experiment and limitations |
| Design & references `/references` | Sources and concrete design patterns used for the interface |

The site uses native HTML/CSS/JavaScript modules and same-origin FastAPI, with the existing Python prediction/explanation code. These six pages need no frontend build, Node runtime, external font or UI CDN. Applicant details and uploads remain in memory; there is no invented user account, loan book or application history.

## How closely the references match

Research covered **12 primary references**, deep Mercury/Ramp/Blend inspection and **eight source captures**. The primary visual reference is the actual [Mercury public demo](https://demo.mercury.com/dashboard); Blend informs intake grouping. Other products were compared without mixing their themes into the site.

Open [the side-by-side board](WEBSITE_COMPARISON.html), [its captured image](../reports/figures/website_reference_comparison.png), and [the full reference catalogue](WEBSITE_REFERENCES.md).

| Element | Measured LoanLens result | Reference relationship |
| --- | --- | --- |
| Sidebar | 220px | Mercury approximately 219px |
| Content / first panel | 968px / 472px at 1440px | Matches the measured widths |
| Title / line height | 28px / 36px | Matches the measured scale |
| Primary action | `#5266eb` | Matches the measured color |
| Panels / active navigation | 12px / 8px radius | Matches the reference treatment |
| Canvas | White | Matches the quiet workspace surface |

Borders retain the lavender-gray family with slightly stronger alpha **0.13**, versus the reference's **0.10**. System fonts replace proprietary Arcadia; branding, icons and content are original. Panel contents/heights follow this project's real evidence. This is a close measured adaptation, not a pixel-identical branded clone.

Actual captures: [overview](../reports/figures/website_overview_native.png), [real application and SHAP](../reports/figures/website_assessment_native.png), [mobile form](../reports/figures/website_mobile_native.png).

## Fresh verification

- **62 pytest tests passed**, **zero failed/error/skipped**; final output **49.43 seconds**. These cover the original scientific/Streamlit behavior plus website API validation, byte/row limits, real-model agreement, SHAP reconstruction, single/batch precision and JSON/CSV documentation schemas.
- Both native and Linux-container Chromium runs passed real-example prediction/SHAP, CSV template/upload/results/download, invalid inputs, duplicate-header rejection, evidence controls, back/forward and route refresh. Each run passed **30 responsive checks**: six routes at **320, 390, 768, 1024 and 1440px**. No horizontal page overflow or uncaught JavaScript errors was recorded.
- **Three delayed-response/keyboard regressions passed**: late examples cannot overwrite resets, older batches cannot reset a newer loading state, and evidence toggles retain focus. Tests delay genuine API responses rather than replacing model data.
- **axe-core 4.14.0** reported **zero automated violations on six routes** for checked WCAG 2 A/AA and 2.1 A/AA rule tags. This does not replace a formal assistive-technology audit.
- The Linux amd64 image built and ran as **UID 10001** with a read-only root filesystem. It passed health checks with **PORT=8080**, confirming support for a hosting-supplied port.
- All **15 website source files** in the image matched local bytes. Raw/model checksums remained unchanged. Windows and Linux returned the same real-example prediction, with probability difference **0.0**.
- Native Python is **3.12.13**; the tested container base supplied **3.12.16**. Model-library versions are pinned. Dependency compatibility, Python compilation, JavaScript syntax and whitespace checks passed.

Machine evidence: [combined verification](../reports/website_verification.json), [pytest XML](../reports/website_pytest_results.xml), [native browser](../reports/website_browser_check.json), [container browser](../reports/website_container_browser_check.json), [state regressions](../reports/website_state_check.json), [accessibility](../reports/website_accessibility.json).

The temporary verification container is stopped after recording evidence. Its image `loanlens-local:website` remains available locally; the native site stays running on 8000. No cloud deployment, public registry push, domain or paid hosting resource was created.

## Findings corrected

Review and failing checks found fixed-port container health, truncated batch JSON scores, stale example/reset behavior, overlapping batch loading cleanup, lost toggle focus and insufficient switch/badge contrast. Each was corrected and rechecked. Editable OpenAPI request schemas were also added for manually bounded JSON and CSV endpoints. A quoted inline PowerShell collector did not parse; it was replaced by the normal Python file `tests/verify_website.py`.

Four upstream SHAP/Starlette deprecation warnings remain in pytest output; none failed a test. No unresolved functional website blocker remains in the verified scope.

## Re-run checks

With the native server running:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
uv tool run --from playwright python tests/website_browser_live.py
uv tool run --from playwright python tests/website_state_live.py
```

The accessibility engine is separate verification tooling, not an app dependency:

```powershell
$taskAxe = Invoke-RestMethod 'https://registry.npmjs.org/axe-core/latest'
$taskAxePath = Join-Path $env:TEMP 'loanlens-axe.min.js'
Invoke-WebRequest ('https://unpkg.com/axe-core@' + $taskAxe.version + '/axe.min.js') -OutFile $taskAxePath
uv tool run --from playwright python tests/website_accessibility_live.py
```

The report retains the exact engine version used. `tests/verify_website.py` is the build-session evidence collector and expects its specifically named running verification container; it is not required to use the website.

## Limits retained

The default threshold is **0.50**. The saved **0.76** cost experiment rejects every possible applicant for this fitted tree and remains clearly labeled as a failed scenario. The model predicts historical approvals, not repayment/default outcomes. No retraining or new scientific result was invented for the website.

Public hosting is prepared and intentionally deferred. Real applicant use would require access control, appropriate data handling, independent lending validation and any required dataset redistribution rights. No external bank validation or formal assistive-technology certification is claimed.
