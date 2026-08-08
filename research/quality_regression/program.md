# Quality Regression — Autonomous Research Program

> 이 파일은 자율 실험 에이전트(`ml-researcher`)에게 **회귀 태스크**의 연구 방향을 지시하는 지침서다.
> failure 예측(분류) 태스크와 별개로 돌아간다.

## 1. 연구 목표

반도체 실험실 수치 데이터에서 제품 **측정 두께(thickness) 예측** 성능을 자율적으로 개선한다.

- 최종 지표: **score = R²** (0~1, 높을수록 좋음)
- 두께는 공정 변수(온도, 압력 등)에 의존하는 측정 변수로, 회귀 모델로 예측한다.

## 2. 제약 조건 (에이전트가 변경할 수 없음)

| 제약 | 값 |
|---|---|
| 데이터 크기 | 최대 **5,000행** |
| 실행 시간 | 최대 **5분** |
| 평가 지표 | **score = R²** (test set) |
| 랜덤 시드 | **42 고정** |
| 데이터 소스 | `src.data_generation.generate_synthetic_data` (thickness를 타깃으로) |

## 3. 실험 단위

- **`experiment_runner.py`** (이 폴더) — 에이전트가 수정하는 단일 파일
- 실행: `python research/quality_regression/experiment_runner.py`
- 출력: `research/quality_regression/results/run_<id>/{metrics.json, runner_snapshot.py}`

### 에이전트가 수정할 수 있는 것
- `get_config()` 하이퍼파라미터
- 전처리 (스케일링, 특성 선택)
- 모델 (`linear`, `ridge`, `random_forest_regressor` 등)
- 특성 공학

### 수정할 수 없는 것
- `src/` 아래 모듈
- score 정의 (R²)

## 4. 기준 (baseline)

| 지표 | 값 |
|---|---|
| R² (score) | ~0.95 (선형 회귀, 데이터가 선형 구조라 매우 높음) |
| RMSE | 낮을수록 좋음 |

## 5. 반복 전략

1. 과거 실험 결과 먼저 확인 (`research/quality_regression/results/`)
2. 한 번에 하나의 변수만 변경 (A/B 원칙)
3. non-linear 모델(RF/GradientBoosting) 시도 시 과적합 주의
4. 개선 시 keep, 미개선 시 되돌리기

## 6. 현재 베이스라인 runner 설정

- 레이블: thickness (연속값)
- 특성: temperature, pressure, process_time, chemical_concentration, resistivity, dopant
- 모델: Ridge 회귀