# C1. 실험 runner — 단일 파일 파이프라인의 힘

## 학습 목표
- `experiment_runner.py`가 왜 "단일 파일"인지 이해한다
- `get_config()` / `run_experiment()` / `_run_and_save()` 3개 함수의 역할을 안다
- 직접 실행해 결과 파일을 확인한다

## 배경 지식

### 왜 단일 파일인가?
`src/`에 이미 전처리·모델·평가 모듈이 있는데 runner가 왜 필요한가?

**이유**: 연구는 코드를 *자주 수정*하는 작업이다. `src/`의 모듈은 "안정된 시설"이고,
실험은 "한 번 하고 뒤집어지는 프로토타입"이다. 프로토타입을 하나의 스크립트에 담으면:
- 실험마다 스냅샷(runner_snapshot) 저장이 쉽다
- 설정 변경이 한 파일 안에서 명확하다
- 에이전트가 수정할 곳이 하나로 좁혀진다

### 3개 함수 구조
```
get_config()       →  실험 설정 dict (에이전트 튜닝 지점)

run_experiment()   → config → 데이터 로드 → 학습 → 평가 → 성능 return

_run_and_save()    → 결과를 research/<task>/results/run_<id>/에 저장
```

## 따라하기

### 1단계: 실행
```bash
python research/failure_prediction/experiment_runner.py
```
출력에 `{"config": ..., "metrics": ..., "score": ...}` 가 보인다.

### 2단계: 저장물 확인
```bash
ls research/failure_prediction/results/
ls research/failure_prediction/results/run_*/ 
```
두 파일을 확인한다:
- `metrics.json` — config + metrics + score (이번 실행의 값)
- `runner_snapshot.py` — **이번 실험에 쓰인 코드의 복사본** (재현)

### 3단계: config와 score 연결
`metrics.json`을 열어 `config.model_type`(예: logistic)과 `score`를 확인한다.

### 4단계: 모델 교체 실험 (A/B 원칙)
하나의 변수만 바꿔서 개선되는지 확인한다:
```bash
python - <<'PY'
import copy
from research.failure_prediction import experiment_runner as runner

config = copy.deepcopy(runner.get_config())   # 현재 설정 복사
config["model_type"] = "random_forest"         # 모델만 변경 (A/B 원칙)
result = runner.run_experiment(config)
print("기존(기본 설정) 대신 random_forest score:", result["score"])
PY
```

> **A/B 원칙**: 한 번에 하나의 변수만 바꾼다. 여러 개를 동시에 바꾸면
> 무엇이 개선 원인인지 알 수 없다. (AGENTS.md 섹션 9.5)

## 이해 확인

1. runner를 `src/`에 두지 않고 연구 폴더에 두는 이유는?
2. `runner_snapshot.py`의 용도는?
3. `get_config()`가 "에이전트 수정 영역"인 이유는?

## opencode에게 물어보세요
```
research/failure_prediction/experiment_runner.py를 읽고,
현재 score에서 F1×PR-AUC을 올리려면 어떤 전략이 좋을지 가설을 3개 제시해줘.
각각 몇 안 되는 변수만 바꾸는 것으로 제안해줘.
```

## 다음 레슨
[C2. 새 태스크 만들기](10_new_task_scaffold.md) — 스캐폴드 CLI로 새 태스크를 추가한다.