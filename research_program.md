# Semiconductor Failure Prediction — Autonomous Research Program

> 이 파일은 자율 실험 에이전트(`ml-researcher`)에게 연구 방향을 지시하는 **연구 지침서**이다.
> 사람이 이 파일을 반복적으로 수정하여 "연구 조직 코드"를 진화시킨다.

## 1. 연구 목표

반도체 실험실 수치 데이터의 **failure 예측 성능**을 자율적으로 개선한다.

- 최종 지표: **score = F1 × PR-AUC** (0~1, 높을수록 좋음)
- 불량 검출의 정밀도와 재현율을 모두 고려하는 불균형 데이터에 강건한 단일 점수

## 2. 제약 조건 (에이전트가 변경할 수 없음)

| 제약 | 값 | 이유 |
|---|---|---|
| 데이터 크기 | 최대 **5,000행** (고정 예산) | 실험 비교 가능성 |
| 실행 시간 | 최대 **5분** (wall clock) | 고정 시간 예산 |
| 평가 지표 | **score = F1 × PR-AUC** | 단일 비교 기준 |
| 랜덤 시드 | **42 고정** | 재현성 |
| 데이터 소스 | `src.data_generation` | 가상 실험실 데이터 |
| 기본 전처리 | `src.preprocessing` | 고정 유틸리티 |

## 3. 실험 단위

- **`experiment_runner.py`** — 에이전트가 수정하는 **단일 파일**
- 실행 방법: `python experiment_runner.py`
- 출력: `research/results/run_<run_id>/metrics.json` (run_id는 자동 생성)
- 반환 형식: `{"config": {...}, "metrics": {...}, "score": float}`

### 에이전트가 수정할 수 있는 것

- `get_config()` 내 하이퍼파라미터
- 전처리 전략 (결측 처리, 스케일링, 인코딩)
- 특성 공학 (파생 변수, 상호작용, 선택)
- 모델 알고리즘 및 파라미터 (sklearn 계열)
- 불균형 대응 (SMOTE, 임계값 최적화 등)

### 에이전트가 수정할 수 없는 것

- `src/` 아래 모든 모듈 (고정)
- 평가 지표 정의 (score 공식)
- 실험 예산

## 4. 실험 로그 형식

각 실험은 `research/results/run_<run_id>/` 아래 다음 파일을 생성한다:

- `config.json` — 실험 설정 (에이전트가 바꾼 것)
- `metrics.json` — 평가 지표 (score 포함)
- `runner_snapshot.py` — 실행 시점의 experiment_runner.py 사본

## 5. 반복 전략 (A/B 테스트 원칙)

1. **과거 결과 먼저 확인** — `research/research.db`의 experiments 테이블 조회
2. **가장 개선 여지가 큰 영역 선택** — 점수가 낮은 영역 우선
3. **한 번에 하나의 변수만 변경** — A/B 테스트 원칙
4. **개선 시 유지(keep), 미개선 시 롤백(discard)** — diff 기반
5. **모델 복잡도는 최소화** — 과적합 방지, 설명 가능성 유지

## 6. 현재 기준 (baseline)

| 지표 | 값 |
|---|---|
| F1 | 0.844 |
| PR-AUC | 0.937 |
| **score (F1×PR-AUC)** | **0.791** |
| ROC-AUC | 0.986 |

> 이 값은 `experiments/results/baseline/metrics.json`에서 확인할 수 있다.
> SMOTE + 임계값 최적화로 F1 0.867, PR-AUC 0.936 → score 0.812 달성 (기록 유지).

## 7. 우선 탐색 순서

1. **전처리 전략** — 결측 처리 방법, 스케일링 선택
2. **불균형 대응** — SMOTE/ADASYN, 임계값 최적화
3. **모델 선택** — RandomForest, GradientBoosting, XGBoost 등
4. **하이퍼파라미터** — C, max_depth, n_estimators 등
5. **특성 공학** — 상호작용, 파생 변수

## 8. 보고 형식

실험 완료 후 `research/reports/report_<date>.md` 형식으로 생성:

- 오늘 수행한 실험 수
- 각 실험의 score 변화 (이전 최고 대비)
- keep/discard 판정
- 내일 실험을 위한 제안
