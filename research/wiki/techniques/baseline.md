---
tags: [techniques, baseline]
created: 2026-08-08
updated: 2026-08-08
---

# Baseline — 현재 베이스라인 구성

> 현재 두 태스크에서 사용 중인 기본 파이프라인 구성.
> 모든 실험의 기준점이므로 이 페이지는 항상 최신 상태를 반영한다.

## 공통 설정

| 항목 | 값 |
|------|-----|
| 데이터 | `lab_sensor_data` (5,000행) |
| 결측치 주입 | 5% (`missing_rate=0.05`) — `src.data_generation` |
| 스케일링 | StandardScaler (`scale=True`) |
| 랜덤 시드 | 42 고정 |
| 데이터/시간 예산 | 5,000행 / 5분 |

## 분류 (failure_prediction)

| 항목 | 값 |
|------|-----|
| imbalance_strategy | **none** (불균형 처리 미적용) |
| model_type | logistic |
| model_params | max_iter=1000, C=1.0 |
| threshold | 0.5 (임계값 고정) |
| 평가 | score = F1 × PR-AUC = **0.7912** |

## 회귀 (quality_regression)

| 항목 | 값 |
|------|-----|
| model_type | linear/ridge 계열 |
| 평가 | score = R² = **0.9822** |

## 결론 / 한계

- **분류**: 불균형(16.98%)을 전혀 처리하지 않은 상태 → recall(0.796)이 제한적
- **회귀**: 선형 모델로 이미 높은 R² → 비선형 개선 효과는 제한적일 수 있음

## 교차 참조

- [tasks/failure_prediction.md](../tasks/failure_prediction.md)
- [tasks/quality_regression.md](../tasks/quality_regression.md)
- [datasets/lab_sensor_data.md](../datasets/lab_sensor_data.md)