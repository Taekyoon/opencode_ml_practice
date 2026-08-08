---
name: imbalanced-data-specialist
description: Handle class imbalance in semiconductor failure prediction using SMOTE/Tomek sampling and threshold optimization for recall-focused metrics
license: MIT
compatibility: opencode
metadata:
  domain: semiconductor
  library: imbalanced-learn
  priority: high
---

## What I do

This skill provides methods to analyze and resolve class imbalance in semiconductor manufacturing data, which often has very low failure rates.

### 1. Analyze class imbalance

Compute the class ratio and decide which sampling strategy fits:

```python
from src.imbalanced_data_specialist import ImbalancedDataSpecialist

specialist = ImbalancedDataSpecialist(random_state=42)
ratio = specialist.analyze_imbalance(y)   # prints class distribution + recommendation
```

### 2. Apply resampling

The following methods are available via `apply_sampling(X, y, method)`:

| method | type | used when |
|--------|------|-----------|
| `smote` | oversampling | ratio > 10 (recommended) |
| `adasyn` | oversampling | noisy minority clusters |
| `tomek` | undersampling | mild imbalance, avoid info loss |
| `random_under` | undersampling | very large datasets |
| `smote_tomek` | combined | ratio > 10 (often best) |
| `auto` | decision | chooses based on imbalance ratio |

```python
X_res, y_res = specialist.apply_sampling(X, y, method="auto")
```

### 3. Optimize decision threshold

Default `predict()` uses 0.5, but for imbalanced data the optimal cutoff is almost never 0.5. Optimize against F1 / recall / precision:

```python
best_t = specialist.optimize_threshold(model, X_test, y_test, metric="f1")
y_pred = (model.predict_proba(X_test)[:, 1] >= best_t).astype(int)
```

### 4. Imbalance-aware evaluation

```python
report = specialist.evaluate_imbalanced(y_true, y_pred, y_proba)
# prints classification_report and PR-AUC
```

## When to use me

- When failure (positive class) ratio is below ~20% of the dataset
- When recall of the failure class matters more than raw accuracy
- When F1 or PR-AUC should be the optimization target instead of accuracy
- Whenever the data pandas shows an obvious majority/minority split

## How to run the helper module

```bash
# within the project root containing src/imbalanced_data_specialist.py
pip install imbalanced-learn
python -m pytest .opencode/skills/imbalanced-data-specialist/tests -q  # optional
```

## Parameters

| parameter | default | description |
|-----------|---------|-------------|
| `random_state` | `42` | seed for reproducible resampling |
| `sampling_method` | `auto` | `smote`, `adasyn`, `tomek`, `random_under`, `smote_tomek`, `auto` |
| `threshold_metric` | `f1` | `f1`, `recall`, `precision` — objective for threshold search |

## Notes for the agent

- Do NOT forget to standardize features (StandardScaler) before SMOTE; distances are computed on raw scales.
- Evaluate on the original test set (never resample the test split).
- precision_recall_curve return order is (precision, recall, thresholds) — thresholds are the lower boundary for positive class.