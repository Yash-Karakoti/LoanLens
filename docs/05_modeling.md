# Model development

The experiment compares five classifiers on the same raw training partition. Every model receives the same validation, imputation, feature engineering and encoding chain. The results below come from `reports/model_comparison.csv`; they are training cross-validation results, not holdout results.

## Experiment design

- Raw stratified split: 491 training applications and 123 reserved holdout applications; `random_state=42`.
- Cross-validation: five shuffled stratified folds with seed 42.
- Search: `RandomizedSearchCV`, four sampled hyperparameter settings per model/imbalance strategy, `refit="f1"`.
- Selection: highest mean approval-class F1; mean ROC-AUC breaks ties. The model name and strategy provide a deterministic final sort order.
- Class imbalance: compare balanced weighting against SMOTENC for every classifier. Weighting and oversampling are alternatives, not combined in these candidates.
- All preprocessing fits inside each fold. No preprocessed dataset is fitted globally and reused for CV.
- The holdout does not choose the winner, search space or decision threshold.

The five algorithms are Logistic Regression, Decision Tree, Random Forest, XGBoost and LightGBM. These cover a linear baseline, one interpretable tree, bagged trees and two boosting implementations. A small dataset does not automatically favor a more complex model.

## Actual comparison

| Model | Imbalance strategy | CV F1 | F1 standard deviation | CV ROC-AUC |
| --- | --- | ---: | ---: | ---: |
| Decision Tree | class_weight | 0.869626 | 0.027836 | 0.683752 |
| Random Forest | class_weight | 0.847191 | 0.030480 | 0.771284 |
| Decision Tree | SMOTENC | 0.840002 | 0.039900 | 0.695385 |
| XGBoost | class_weight | 0.839595 | 0.050575 | 0.757217 |
| Random Forest | SMOTENC | 0.838626 | 0.035272 | 0.746775 |
| XGBoost | SMOTENC | 0.833607 | 0.046731 | 0.757862 |
| LightGBM | class_weight | 0.832232 | 0.045908 | 0.766830 |
| Logistic Regression | class_weight | 0.819096 | 0.044259 | 0.741874 |
| LightGBM | SMOTENC | 0.817626 | 0.038901 | 0.758992 |
| Logistic Regression | SMOTENC | 0.809752 | 0.043535 | 0.732852 |

The selected model is **Decision Tree with balanced class weights**, `max_depth=2`, `min_samples_leaf=5`. Its training CV approval precision is 0.784656 and recall is 0.976207. It ranks first for the specified F1 objective, although Random Forest has a higher ROC-AUC. This is an objective-dependent choice, not proof that a tree is universally superior. Fold standard deviation describes variation across these folds; it is not a confidence interval proving model differences.

## Preprocessing and SMOTENC order

The flat imbalanced-learn Pipeline contains:

```text
raw input
  -> validate and select columns
  -> median/mode imputation
  -> deterministic financial/log features
  -> numeric scaling + categorical ordinal codes
  -> SMOTENC during fit, or passthrough for class weighting
  -> one-hot encoding
  -> classifier
```

Ordinal codes temporarily identify nominal categories for SMOTENC. They are subsequently one-hot encoded so the final estimator does not interpret category order as a numeric distance. During inference the sampler is skipped; uploaded applicants are never resampled.

Logistic Regression, Decision Tree, Random Forest and LightGBM use their native `class_weight="balanced"` option. XGBoost does not expose that same option, so the small `BalancedXGBClassifier` subclass recomputes balanced sample weights from the labels passed to each `fit`. This keeps fold validation labels out of weight calculation. The wrapper uses a stable `src.train` import path so a saved winner remains loadable from the app.

SMOTENC is the mixed numeric/categorical variant of SMOTE. It avoids interpolating category identity into fractional category codes. Numeric engineered features can still become inconsistent with their original formulas after synthetic interpolation; this is a limitation of that comparison, not a claim that the synthetic rows are real applicants. Synthetic rows are never written to `data/raw`, used in EDA, or added to the holdout.

## Threshold tuning

After selection, five-fold out-of-fold approval probabilities are generated for the selected configuration using only training observations. The threshold grid is 0.00 to 1.00 inclusive in steps of 0.01, plus the next representable value above 1.0 to cover an explicit reject-all endpoint when a model emits a score of 1. The assumed scenario cost is:

```text
cost = 5 * false_approvals + 1 * false_rejections
```

These costs are illustrative review-policy units, not measured defaults or money. A false approval means a historical rejection predicted as approved. The selected experimental threshold is **0.76**. Ties favor a threshold closest to 0.5, then the lower threshold.

The final fitted tree's maximum leaf approval score is **0.6394436519258202**, below 0.76. Consequently this experimental policy rejects every applicant. Its held-out cost is **85**, worse than **58** at conventional 0.5. The app uses **0.50 by default** and exposes the failed 0.76 cost policy explicitly as an experiment. This preserves the observed failure and uses the pre-existing standard policy rather than fitting a replacement threshold to holdout labels. Even the standard policy remains an educational screening demonstration, not a validated bank decision rule.

The hyperparameters were already selected using the same training partition, so these OOF threshold scores can have selection optimism. They are not a fully nested-CV generalization estimate. The separately reserved holdout evaluates the final policy; it is never used to retune that policy.

## Artifacts and commands

```powershell
.\.venv\Scripts\python.exe -m src.train
```

- `models/best_model.joblib`: fitted preprocessing, estimator, threshold, model identity, dataset hash and package versions.
- `models/metadata.json`: readable metadata without the Python estimator object.
- `reports/model_comparison.csv`: best sampled configuration and fold metrics for each candidate.
- `reports/training_failures.json`: explicit failed candidates; the completed run recorded an empty list.
- `reports/threshold_costs.csv`: training OOF cost for every threshold.
- `data/processed/train_oof.csv`: real training IDs, true labels and OOF probabilities.
- `data/processed/split_manifest.json`: disjoint train/holdout IDs and raw-data checksum.

See [06_evaluation.md](06_evaluation.md) for held-out metrics, the majority baseline, error analysis and subgroup audit. Revisions motivated by those errors require new validation evidence rather than repeated tuning on this holdout.
