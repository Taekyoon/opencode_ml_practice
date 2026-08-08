---
tags: [tasks, regression]
created: 2026-08-08
updated: 2026-08-08
task: quality_regression
kind: regression
score_name: r2
dataset: lab_sensor_data
target: thickness
---

# quality_regression — 회귀 태스크 발견사항

> 이 페이지는 이 태스크의 실험에서 얻은 발견을 누적 기록한다.
> 매 실험(ingest) 후 에이전트가 갱신한다. 최고 결과는 항상 최상단 테이블에 유지.

## 현재 최고 결과

| run_id | score (R²) | RMSE | 핵심 변경사항 |
|--------|------------|------|--------------|
| run_20260808_171024 | **0.9822** | — | 베이스라인 (기록 기준) |

## 실행 이력 (최근 4회)

| run_id | score | is_best |
|--------|-------|---------|
| run_20260808_171024 | 0.9822 | ★ |
| run_20260808_170646 | 0.9822 | |
| run_20260808_145116 | 0.9822 | |
| run_20260808_145310 | 0.9822 | |

> **관찰**: 4회 모두 동일 score. 아직 변수 튜닝이 수행되지 않은 **베이스라인 단계**.
> 정확한 RMSE/MAE, config 상세는 `research.db`(src.research_store)에서 조회.

## 발견 사항

- (아직 기록된 변수 실험이 없음 — 최초 발견은 실험 후 여기에 기록)

## 시도하지 않은 것 / 다음 후보

- [ ] RandomForestRegressor, 선형 이외 모델 비교 → [techniques/model_comparison.md](../techniques/model_comparison.md)
- [ ] 다항 특성(PolynomialFeatures) + Ridge
- [ ] 이상치(outlier) 처리 (온도/비저항 극단값)

## 교차 참조

- [datasets/lab_sensor_data.md](../datasets/lab_sensor_data.md) — 특성 목록
- [techniques/baseline.md](../techniques/baseline.md) — 현재 베이스라인 구성