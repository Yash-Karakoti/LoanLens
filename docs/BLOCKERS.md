# Blockers and recoveries

No unresolved blocker recorded yet. Failed operations and recovery will be appended here; after three attempts on a blocked task, stop that task and continue independent work.

## Initial training failure — recovered

The first search attempt failed for every candidate before any model fit: imbalanced-learn disallows an intermediate nested scikit-learn Pipeline (`All intermediate steps of the chain should not be Pipelines`). Confirmed the check in the installed `imblearn/pipeline.py`, then flattened the preprocessing steps into the outer imblearn Pipeline. No holdout scores existed or informed this correction. Fold-level imputer tests verify the corrected pipeline boundary.

## Built-in browser connection — fallback used

The computer-use browser connection timed out on all three attempts (open local tab, then two inventory requests). Stopped retrying that connection. Streamlit health returned HTTP 200, and Playwright is used as an independent live-browser fallback. AppTest also verifies the native Streamlit form and SHAP rendering. These browser tools are verification dependencies, not application dependencies.

## Cost-policy experiment — observed model limitation

The saved 0.76 training OOF cost threshold rejects all training OOF applicants under the assumed 5:1 costs and exceeds every leaf score of the final fitted tree. It is a failed shortlisting policy, retained honestly rather than retuned against holdout data. The UI uses fixed conventional 0.50 by default, with 0.76 available as an explicit failed scenario. See docs/06_evaluation.md for both actual results.

## Verification harness recoveries

The first live Playwright check timed out on a dropdown option selector. Keyboard selection matched the current Streamlit widget, and the complete check passed. A Windows console print of an emoji needed UTF-8; only diagnostic output was affected. A redirected PowerShell pipeline command reported an error on non-fatal notebook stderr despite its internal passed manifest. A further complete rebuild with explicit native LASTEXITCODE capture returned 0 and reproduced all results. Three upstream SHAP deprecation warnings remain in pytest output; all 43 tests passed.
