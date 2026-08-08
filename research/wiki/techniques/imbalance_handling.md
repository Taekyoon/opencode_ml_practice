---
tags: [techniques, imbalance, smote]
created: 2026-08-08
updated: 2026-08-08
---

# Imbalance Handling — 불균형 처리 기법

> 분류 태스크(failure_prediction)에서 사용할 불균형 대응 기법들의 종합 페이지.
> 각 기법을 실제로 시험하면 **결과(score 변화)와 조건**을 여기에 기록한다.

## 배경

- `lab_sensor_data`의 failure 비율: **16.98%** (약 6:1 불균형)
- 베이스라인(미처리): score=0.7912, recall=0.796, precision=0.899
- 목표: **recall 유지/상승 + precision 방어** (F1×PR-AUC 최대화)

## 기법 후보 (미시험 — 계획만 기록)

| 기법 | 예상 효과 | 시험 순서 | 상태 |
|------|-----------|-----------|------|
| SMOTE (oversampling) | 소수클래스 샘플 합성으로 recall↑ | 1순위 | 미시험 |
| class_weight="balanced" | 손실 가중치 조정 | 2순위 | 미시험 |
| 임계값 최적화 | `optimize_threshold=True` (F1 최적) | 3순위 | 미시험 |
| SMOTE + 임계값 병행 | 1+3 조합 | 4순위 | 미시험 |

> 에이전트의 runner 설정: `config["imbalance_strategy"] = "smote"` 등으로 적용.
> 구현 시 스냅샷(runner_snapshot.py)에 코드가 남으므로 재현 가능해야 한다.

## 실험 기록 (시험 후 갱신)

| 날짜 | 기법 | task | score | recall | PR-AUC | 판정 |
|------|------|------|-------|--------|--------|------|
| (아직 없음) | | | | | | |

## 교차 참조

- [tasks/failure_prediction.md](../tasks/failure_prediction.md) — 분류 태스크 발견
- [datasets/lab_sensor_data.md](../datasets/lab_sensor_data.md) — 불균형 비율
- [techniques/baseline.md](../techniques/baseline.md) — 미처리 베이스라인