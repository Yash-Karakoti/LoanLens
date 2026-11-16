# Run and deploy the custom website

The primary website is a same-origin FastAPI application with native HTML/CSS/JavaScript assets. Python loads the existing fitted model and calculates actual SHAP explanations. No frontend build, Node runtime, external font/CDN, database or API key is required for the website.

## Local Windows setup

From the project directory:

```powershell
Set-Location 'D:\Koding\Housing Loan Approval Prediction'
uv pip install --python .venv\Scripts\python.exe -r requirements-lock.txt
.\.venv\Scripts\python.exe -m web
```

Open **http://127.0.0.1:8000** for the public homepage. The default bind address is loopback. The pages `/workspace`, `/assessment`, `/batch`, `/evidence`, `/methodology` and `/references` also support direct navigation and refresh. API documentation is at `/api/docs`; readiness is at `/api/health`. Fonts and the illustrative WebP hero are bundled local assets.

If the raw CSV is absent after cloning, download it before using real examples, explanations or building the image:

```powershell
.\.venv\Scripts\python.exe -m src.download_data
```

The loader verifies the original checksum. It never overwrites an existing raw CSV. Models and generated reports are already part of this local project; use the original pipeline instructions to regenerate them if needed.

The legacy Streamlit interface remains available separately:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/app.py --server.headless true --server.address 127.0.0.1
```

## Container path for later hosting

The Dockerfile targets Python 3.12 and Linux amd64. `requirements-web.txt` is a separate, resolved runtime lock; it omits Jupyter, pytest, Streamlit and Windows-specific notebook dependencies. The installed model-library versions match the artifact metadata. CPU-only XGBoost supplies the same Python module without unnecessary GPU dependencies, as documented by [XGBoost's installation guide](https://xgboost.readthedocs.io/en/latest/install.html#minimal-installation-cpu-only).

```powershell
docker build --platform linux/amd64 -t loanlens-local:website .
docker run --rm --name loanlens-website -p 127.0.0.1:8001:8000 loanlens-local:website
```

Open **http://127.0.0.1:8001** for the container version. The native local server can remain on 8000 while testing the container on 8001. Stop this named container with `docker stop loanlens-website`; do not stop unrelated containers.

The image runs as a non-root user, binds to `0.0.0.0` inside its container, has a model-readiness health check, and verifies the raw/model binding during build. It includes the trusted local model, required public background data, aggregate evidence and static website files. Uploads and prediction results are processed in memory; they are not saved as application history. Access logging is disabled by the entry point.

For a hosting service that supplies its listening port, set `PORT` and retain `WEB_HOST=0.0.0.0`. `python -m web` reads both variables. Use the container command as the start command and `/api/health` for health checks. A static-only host cannot run the Python model; the frontend and API should share the same Python/container service unless an explicit separate-origin design is later implemented.

The image is prepared for later deployment; no cloud account, domain, public registry push or hosting subscription is created by this work. The deployment verification actually run is recorded in `HOMEPAGE_HANDOFF.md` and `reports/website_verification.json`. The earlier `WEBSITE_HANDOFF.md` describes the superseded dashboard-only design.

## Runtime and data boundaries

- JSON and CSV uploads are bounded to 5 MB by bytes actually received, including requests without Content-Length. CSVs also have a 1,000-row limit, duplicate-header detection and shared model-input validation.
- CSV output neutralizes formula-like cells and headers. Only known aggregate figures are exposed; raw dataset files, fitted artifacts, arbitrary reports and filesystem paths are not downloadable through the API.
- Standard 0.50 is the default policy. The saved 0.76 cost scenario is retained as a failed experiment; it rejects all possible inputs for this fitted tree. Neither the model nor threshold is refitted by the website.
- No login or durable applicant store is implemented. Keep the present demonstration restricted to educational/public-demo inputs. Real applicant use would require access control, justified data handling, operational limits and independent lending validation before exposure.
- Background data come from the recorded public dataset. Its redistribution license is not independently established; do not assume that a public source permits publishing an image containing those data. Review that before distributing the container publicly.

## Verification commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q
uv tool run --from playwright python tests/website_browser_live.py
```

The live browser script expects the website server on port 8000. It uses actual project data and checks working routes, real prediction/explanation output, batch processing and responsive rendering. It is a separate verification tool, not an application dependency.
