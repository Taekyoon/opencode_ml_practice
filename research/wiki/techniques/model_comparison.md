---
tags: [techniques, models]
created: 2026-08-08
updated: 2026-08-08
---

# Model Comparison — 모델별 성능 비교

> 태스크에서 시험한 모델들의 종합 비교 페이지.
> 각 모델을 시험하면 최고 score만 여기에 요약하고, 상세는 tasks 페이지에 기록한다.

## 분류 모델 후보 (failure_prediction)

현재 베이스라인: **logistic** → score=0.7912

| 모델 | score | F1 | PR-AUC | 시험 여부 |
|------|-------|-----|--------|-----------|
| LogisticRegression | 0.7912 | 0.844 | 0.937 | ✅ 시험됨 |
| RandomForest | — | — | — | 미시험 |
| GradientBoosting | — | — | — | 미시험 |

## 회귀 모델 후보 (quality_regression)

현재 베이스라인: **linear/ridge 계열** → score(R²)=0.9822

| 모델 | R² | 시험 여부 |
|------|-----|-----------|
| LinearRegression / Ridge | 0.9822 | ✅ 시험됨 |
| RandomForestRegressor | — | 미시험 |
| 다항 특성 + Ridge | — | 미시험 |

## 시험 순서 제안

1. 분류: class_weight 조정 없이 RandomForest/GradientBoosting 먼저 (트리 모델은 스케일 불필요 → `scale=False` 주의)
2. 회귀: RandomForestRegressor (선형은 이미 높은 R² → 비선형 개선 확인용)

## 교차 참조

- [tasks/failure_prediction.md](../tasks/failure_prediction.md)
- [tasks/quality_regression.md](../tasks/quality_regression.md)
- [techniques/baseline.md](../techniques/baseline.md)