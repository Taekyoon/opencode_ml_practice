---
tags: [tasks, classification, imbalance]
created: 2026-08-08
updated: 2026-08-08
task: failure_prediction
kind: classification
score_name: score
dataset: lab_sensor_data
target: failure
---

# failure_prediction — 분류 태스크 발견사항

> 이 페이지는 이 태스크의 실험에서 얻은 발견을 누적 기록한다.
> 매 실험(ingest) 후 에이전트가 갱신한다. 최고 결과는 항상 최상단 테이블에 유지.

## 현재 최고 결과

| run_id | score (F1×PR-AUC) | F1 | PR-AUC | 핵심 변경사항 |
|--------|-------------------|-----|--------|--------------|
| run_20260809_090033 | **0.7912** | 0.8444444444444444 | 0.9369439556258663 | 2026-08-09 (자동 기록) |
| run_20260808_170640 | **0.7912** | 0.8444 | 0.9369 | 베이스라인 (기록 기준) |

## 실행 이력 (최근 6회)

| run_id | score | is_best |
|--------|-------|---------|
| run_20260808_170640 | 0.7912 | ★ |
| run_20260808_145111 | 0.7912 | |
| run_20260808_145305 | 0.7912 | |
| run_20260808_141932 | 0.7912 | |
| run_20260808_141924 | 0.7912 | |
| run_20260808_141755 | 0.7912 | |

> **관찰**: 6회 모두 동일 score. 아직 변수 튜닝이 수행되지 않은 **베이스라인 단계**.
> 최근 실행의 `config_json`/`metrics_json` 상세는 `research.db`(src.research_store)에서 조회 가능.

## 발견 사항

- (아직 기록된 변수 실험이 없음 — 최초 발견은 실험 후 여기에 기록)

## 시도하지 않은 것 / 다음 후보

- [ ] **SMOTE** 기반 불균형 처리 → [techniques/imbalance_handling.md](../techniques/imbalance_handling.md)
- [ ] class_weight="balanced" (로지스틱/트리 공통)
- [ ] RandomForest, GradientBoosting 모델 비교 → [techniques/model_comparison.md](../techniques/model_comparison.md)
- [ ] 상호정보(MI) 기반 특성 선택

## 교차 참조

- [datasets/lab_sensor_data.md](../datasets/lab_sensor_data.md) — 불균형 16.98%
- [techniques/baseline.md](../techniques/baseline.md) — 현재 베이스라인 구성