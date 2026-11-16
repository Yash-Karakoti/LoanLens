# Blockers and recoveries

No unresolved blocker recorded yet. Failed operations and recovery will be appended here; after three attempts on a blocked task, stop that task and continue independent work.

## Initial training failure — recovered

The first search attempt failed for every candidate before any model fit: imbalanced-learn disallows an intermediate nested scikit-learn Pipeline (`All intermediate steps of the chain should not be Pipelines`). Confirmed the check in the installed `imblearn/pipeline.py`, then flattened the preprocessing steps into the outer imblearn Pipeline. No holdout scores existed or informed this correction. Fold-level imputer tests verify the corrected pipeline boundary.
