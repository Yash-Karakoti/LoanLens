# Homepage and overall UI handoff

The current website opens at **http://127.0.0.1:8000**. Its public homepage introduces the screening assistant; the operational dashboard is now `/workspace`. Assessment, batch screening, evidence, methodology and reference routes keep their existing URLs and real model behavior.

```powershell
Set-Location 'D:\Koding\Housing Loan Approval Prediction'
.\.venv\Scripts\python.exe -m web
```

The native HTML/CSS/JavaScript website runs with the same-origin FastAPI service. There is no Node build step, external font service or new UI dependency. The optional original Streamlit app remains separate. See [DEPLOYMENT.md](DEPLOYMENT.md) for the container path.

## What changed

- Added a complete public home: desktop navigation and mobile menu, split housing hero, primary assessment action, actual evidence strip, three-step process, capability explanation, an optional genuine model example, FAQ, closing action and footer.
- Rebuilt the inside pages to match the homepage: shared public header and full footer, editorial serif page titles, pill actions, sage evidence surfaces and wider content. Removed the old sidebar and its drawer code; desktop tool navigation becomes a compact six-link grid on mobile.
- Redesigned the assessment with a spacious form, sage policy area, larger fields, an illustrative housing panel and a forest result header. Batch, evidence, methodology and reference pages use the same shared spacing, surfaces and type.
- Bundled DM Sans and Instrument Serif locally with their SIL OFL licenses. The house artwork is an original illustrative concept, clearly labelled; it is not an applicant property or a model result.
- Kept seven directly refreshable routes. Home anchors work with browser history; all pages share the same keyboard-accessible public menu and Escape behavior. Tool links expose the active route with `aria-current`.
- Homepage copy and controls render independently of model-evidence loading. Live statistics enhance the page without replacing its FAQ state. Leaving an unfinished example cancels its request and prevents stale output.

## References and visible relationship

[HOMEPAGE_RESEARCH.md](HOMEPAGE_RESEARCH.md) records seven current primary sources and thirteen source captures. Better's measured **#073126 / #fffdfa / #017848** palette and pill actions are the primary visual reference. Blend informs the split hero; Habito informs the approachable numbered sequence. Heading typography, illustration, branding and content are original choices, rather than a claim of pixel-identical cloning.

Open [the current comparison board](HOMEPAGE_COMPARISON.html), [desktop homepage](../reports/figures/homepage_desktop_native.png), [mobile homepage](../reports/figures/homepage_mobile_native.png), [assessment form](../reports/figures/website_assessment_empty_native.png), [real assessment and SHAP](../reports/figures/website_assessment_native.png), [mobile assessment](../reports/figures/website_mobile_native.png), and [workspace](../reports/figures/website_overview_native.png). [HERO_ASSET.md](HERO_ASSET.md) records the exact generation prompt and WebP delivery details.

The original Mercury-only visual research and comparison remain historical, explicitly labelled. No vendor testimonials, pricing, customer counts, banking balances or business-performance claims were imported.

## Fresh verification

- **62 pytest tests passed**, zero failed/error/skipped, in **24.10 seconds**. Four upstream deprecation warnings remain visible.
- Native and Linux-container Chromium each passed the homepage's hero/anchors/FAQ/live example, assessment inference and SHAP, CSV template/upload/export, validation failures, threshold controls, history, direct refresh and mobile menus. Each passed **42 responsive checks**: seven routes at **320, 390, 577, 768, 1024 and 1440px**, including the supplied screenshot's width, with no page overflow or uncaught JavaScript errors.
- **Six asynchronous-state and keyboard regressions passed** using delayed genuine API responses. The homepage stays usable when evidence fails; late statistics preserve FAQ state; leaving a pending example prevents stale output. Existing reset, overlapping batch and evidence-focus checks also pass.
- **axe-core 4.14.0** found **zero automated violations across seven routes** under checked WCAG 2 A/AA and 2.1 A/AA tags, after correcting one inherited footer contrast issue. This is not a formal accessibility certification.
- The Linux amd64 image built and ran as **UID 10001**, with a read-only filesystem and healthy service on an environment-supplied **PORT=8080**. All **25 website source/asset/license files** matched local bytes. Windows/Linux real-example probability difference was **0.0**.
- Raw CSV and model SHA-256 digests match the pre-revision baseline. The UI revision does not refit the model or rerun the scientific experiment; its previous complete reproduction remains recorded separately.
- JavaScript syntax, Python compilation and compatibility of all **144 installed packages** passed. Original font-license texts retain upstream whitespace; application-source whitespace checks pass.

Machine evidence: [combined verification](../reports/website_verification.json), [pytest XML](../reports/website_pytest_results.xml), [native browser](../reports/website_browser_check.json), [container browser](../reports/website_container_browser_check.json), [state regressions](../reports/website_state_check.json), [accessibility](../reports/website_accessibility.json), and [raw/model baseline](../reports/homepage_baseline.json).

The temporary verification container is removed after recording evidence; its tested image remains `loanlens-local:website`. The native website is left running on port 8000. No unrelated container or user file was changed.

## Re-run checks

With the native website running:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
uv tool run --from playwright python tests/website_browser_live.py
uv tool run --from playwright python tests/website_state_live.py
uv tool run --from playwright python tests/website_accessibility_live.py
```

The accessibility script uses the external development-only engine at `$env:TEMP\loanlens-axe.min.js`; its download instructions are retained in the earlier website handoff. The browser script can target a running container with `--url http://127.0.0.1:8001 --report website_container_browser_check.json`. The combined collector `tests/verify_website.py` expects the specifically named verification container while it is running; it is not needed to use the app.

## Scope and limits

The fitted model, raw data and scientific results are unchanged. The model predicts historical approval patterns, not repayment/default or a real lending decision. The failed 0.76 cost policy remains visible; the conventional 0.50 policy remains the default.

No cloud publication, domain or paid service was created. Automated accessibility checks do not replace an assistive-technology audit. Reference sites' mobile layouts were not separately measured; LoanLens's own mobile layouts are checked directly. The unrelated pre-existing user `recipes.json` is preserved and excluded from the container context.

The environment is an unseeded uv virtual environment: use `uv pip check --python .venv/Scripts/python.exe` rather than assuming it contains pip. Four upstream SHAP/Starlette deprecation warnings remain visible in the Python test output.
