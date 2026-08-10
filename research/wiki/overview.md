---
tags: [overview, dashboard]
created: 2026-08-08
updated: 2026-08-08
---

# Research Overview — 프로젝트 대시보드

> 이 페이지는 위키의 진입점이다. 새 세션은 먼저 이 페이지를 읽는다.

## 현재 상태

- **데이터셋**: `lab_sensor_data` (5,000행, failure 비율 **16.7%**, 특성 7개), `wm811k` (웨이퍼맵 811,457행, 라벨 172,950) → [datasets/](datasets/)
- **태스크 수**: 4 (분류 3 + 회귀 1) → [tasks/](tasks/)
- **연구 단계**: **베이스라인 확정 단계** — 아직 변수 tuning 없음

## 태스크별 최고 점수

| 태스크 | 유형 | 실행 횟수 | 최고 score | 상태 |
|--------|------|----------|-----------|------|
| failure_prediction | 분류 | 6 | **0.7912** | 베이스라인만 반복 |
| quality_regression | 회귀 | 4 | **0.9822** | 베이스라인만 반복 |
| prompt_guard | 분류 | 3 | **1.0** (hard_eval 0.42) | 카테고리 수준 완벽 — 하드 케이스 한계 |
| wafer_vision | 분류 | 3 | **0.2369** (WM-811K 실데이터) | 실데이터 첫 실행 — 튜닝 여지 큼 |

## 최근 활동

- 2026-08-08: 위키 시스템 도입 (이 페이지 최초 생성)
- 2026-08-09: wafer_vision — WM-811K 실데이터로 로더/러너/예측 전 구간 검증 (score 0.2369, anomaly ROC-AUC 0.785)

## 다음 할 일 (우선순위순)

1. failure_prediction에 **불균형 처리(SMOTE)** 시도 → [techniques/imbalance_handling.md](techniques/imbalance_handling.md)
2. logistic 이외 모델 비교 (RandomForest, GradientBoosting) → [techniques/model_comparison.md](techniques/model_comparison.md)
3. wafer_vision: WM-811K 실데이터 튜닝 (클래스 불균형 대응, 특징 확장) → [tasks/wafer_vision.md](tasks/wafer_vision.md)
4. prompt_guard: 하드 케이스 오탐 줄이기 (인용/정의 맥락) → [tasks/prompt_guard.md](tasks/prompt_guard.md)
5. 교차 태스크 교훈/다음 방향 → [synthesis/lessons_learned.md](synthesis/lessons_learned.md)
6. 실험 후 이 wiki 갱신 (tasks/ 페이지 반영)

## Wiki 유지 규칙 요약

- **Ingest**: 실험 후 → tasks 페이지 갱신 → 관련 techniques 갱신 → log.md 기록 → index.md 갱신
- **Lint**: 정기 검진 (모순/고아/오래된 데이터) — `make wiki-lint`