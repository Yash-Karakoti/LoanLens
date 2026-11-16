# Explainability

`src/explain.py` explains the saved model's **approval score**, using SHAP `PermutationExplainer` with an independent background masker. It explains the positive-class output of the final classifier's `predict_proba`, not its hard Approved/Rejected label and not a default-risk probability.

## Actual explanation setup

The generated `reports/shap_metadata.json` records:

- 30 real training applications as background, sampled with seed 42.
- 60 real training applications for the global summary, sampled with seed 43.
- Five forward/reverse feature permutations per explanation budget.
- Final encoded feature inputs: standardized numeric values and one-hot categorical indicators.
- Maximum observed probability reconstruction error: **1.1102230246251565e-16**.
- Exact training IDs used for the background and global sample.

No held-out applicant is used to construct the explanation baseline. The saved final estimator receives the same encoded features as the app's full pipeline; the sampler is skipped during transformation.

The numeric plot values are standardized values, not income or loan currency units. Category labels are decoded from fitted encoders to readable names. A present or absent indicator can contribute to a score; an absent indicator is not an assertion that the corresponding category is the applicant's category.

## Reading the plots

The global beeswarm, `reports/figures/shap_summary.png`, shows the distribution and direction of encoded feature contributions across the training sample. Mean absolute contributions are also recorded in metadata. A zero attribution means that this fitted model did not use that feature for the explained predictions, not that the feature is irrelevant in every lending setting.

For a single application, the waterfall starts at the background average model score and adds each feature contribution:

```text
background score + sum(SHAP contributions) = applicant model score
```

Positive values raise the model score relative to this background. Negative values lower it. Multiply a contribution by 100 to express an additive change in percentage points. Percentage points differ from a percentage change relative to the starting score.

The global sample and single-app calculations explicitly test this additivity relation with a small numeric tolerance. A failed reconstruction raises an error instead of displaying an invented explanation.

## Actual example and policy comparison

The generated SHAP example uses real training application **LP001877**:

| Item | Observed value |
| --- | ---: |
| Background score | 0.5052942326429276 |
| Applicant approval model score | 0.6394436519258202 |
| Standard threshold | 0.50 |
| Standard suggestion | Approved |
| Failed cost-experiment threshold | 0.76 |
| Cost-experiment suggestion | Rejected |

Its largest three displayed associations raise the score relative to the background: meeting the credit-history guideline indicator, loan-to-income ratio, and loan amount. The score exceeds standard 0.5 but remains below the separate cost threshold. Positive SHAP contributions can therefore coexist with a Rejected experimental suggestion; the waterfall baseline is not the decision threshold. The app defaults to conventional 0.50 because the final tree cannot produce a score as high as the experimental threshold.

The output of `explain_single(applicant_dict)` contains the same prediction and probability as `predict_frame`, a Matplotlib waterfall figure, a list of three plain-English associations, SHAP values, background score and readable feature names. The app displays these as reasons to inspect, not guaranteed actions to obtain approval.

## Limits to explain in the viva

SHAP describes a fitted model's associations. It does not establish what caused a historical bank decision, prove fairness, measure repayment, or produce a legally sufficient adverse-action notice. Correlated income, log-income and affordability features share information, so attribution may move among them.

Independent masking of encoded features can create unrealistic combinations, including incompatible one-hot categories or mismatched raw/engineered values. The method is a simple model-agnostic educational explanation with this documented limitation. Five permutations and a small background are an approximation; additivity alone does not prove each attribution is stable or causal. Missing applicant fields are imputed using training statistics, so their explanation can reflect an imputed value.

```powershell
.\.venv\Scripts\python.exe -m src.explain
.\.venv\Scripts\python.exe -m pytest tests/test_explain.py -q
```

The explanation tests check prediction agreement, additivity, three reason strings, figure generation, readable feature labels, and absence of holdout IDs or demographic predictors in the background/features. Final execution evidence is kept in [PROGRESS.md](PROGRESS.md) and [MORNING_SUMMARY.md](MORNING_SUMMARY.md).
