# B4. 실험 기록 — 연구 DB와 최고 점수 추적

## 학습 목표
- 실험 결과가 왜 기록되어야 하는지 안다
- SQLite(`research.db`)의 역할과 사용법을 이해한다
- `src.research_store` API를 직접 호출해본다

## 배경 지식

### 왜 실험을 기록하는가?
실험은 혼자서 메모장에 남기기엔 너무 비싸다.
- "어떤 설정이 몇 점이었지?"
- "지난주에 시도한게 베스트인데?"

여러 설정을 시도하다 보면 **어떤 조합이 최고였는지**를 곧바로 알 수 없게 된다.
`research.db`(SQLite 파일)가 이 불확실함을 해소한다.

### 이 프로젝트의 실험 테이블
`src/research_store.py` 스키마 참조:

| 테이블 | 용도 | 특징 |
|--------|------|------|
| `experiments` | 모든 실험 실행 기록 | 설정(config_json)·지표(metrics_json)·score·run_id |
| `best_run` | 태스크별 최고 기록 1줄 | task_id가 UNIQUE, 최고 score 갱신 |

> 스키마에는 이 밖에 `events` 테이블이 있다. "실패한 실행까지 기록"하는 용도로
> **모듈 J(J1)의 주제**이므로 지금은 넘어간다.

**score**: 프로젝트의 표준 점수 (분류 = F1 × PR-AUC, 회귀 = R²)
`record_experiment()`는 score가 태스크 최고면 `best_run`과 `is_best` 플래그를 갱신한다.

## 따라하기

### 1단계: (전제) 베이스라인 실험 먼저 실행
`research.db`가 최소 1회의 실험 기록을 가져야 결과가 보인다.
아직 `research/failure_prediction/results/`에 없으면 **먼저 베이스라인을 실행**한다:

```bash
python research/failure_prediction/experiment_runner.py
```
> 이 레슨이 "코드 실행" 프로젝트라면 위 명령으로 baseline을 먼저 만들어야 이후 DB 조회가 의미있다.

### 2단계: 저장된 기록 확인
```bash
python -m src.research_store
```
출력 예:
```
등록된 태스크별 요약:
  failure_prediction: 1회 실험, 최고 score=0.7912
```

### 3단계: dataset/experiments API 직접 쓰기
```bash
python - <<'PY'
from src.research_store import get_all_experiments, get_best_score

runs = get_all_experiments(task_id="failure_prediction", limit=3)
for r in runs:
    print(f"  {r['run_id']} | score={r['score']} | {r['status']}")

print("최고 점수:", get_best_score("failure_prediction"))
PY
```

### 4단계: 기록의 구성 요소 이해
각 실행(run)은 다음을 저장한다:
- `run_id`: 고유 실행 번호 (예: `run_20260601_000000`)
- `config_json`: 모델·하이퍼파라미터 설정
- `metrics_json`: accuracy/precision/recall/f1/...
- `score`: 표준 점수 (F1 × PR-AUC)
- `runner_snapshot`: 학습에 쓰인 코드 자체 (재현 용)
- `elapsed_sec`: 소요 시간

> `runner_snapshot`을 저장하는 **이유**: 실험 코드가 그대로 보존되므로
> 결과의 재현(reproducibility)이 가능하고, 설정과 상관없는 "이 코드가 왕"이라는 의심이 사라진다.

### 5단계: score가 개선될 때 자동 best 갱신해보기
운영 DB(`research.db`)를 더럽히지 않도록 **임시 DB**로 두 번 기록해
`best_run` 변화를 확인한다:
```bash
python - <<'PY'
import os
from src.research_store import record_experiment, get_best_score

db = "research/tmp_b4_demo.db"
record_experiment(run_id="demo_trial_1", config={"x": 1}, metrics={"f1": 0.5, "pr_auc": 0.6}, score=0.30, db_path=db)
print("best:", get_best_score("failure_prediction", db_path=db))
record_experiment(run_id="demo_trial_2", config={"x": 2}, metrics={"f1": 0.8, "pr_auc": 0.9}, score=0.72, db_path=db)
print("최고 기록 갱신:", get_best_score("failure_prediction", db_path=db))
os.remove(db)   # 임시 DB 삭제 (운영 DB와 분리)
PY
```
`record_experiment()`는 score가 태스크 최고이면 내부적으로 `is_best` 플래그와
`best_run`을 갱신한다 (별도 함수 호출 불필요). 두 번째 기록(0.72 > 0.30)으로 갱신이
일어난 것을 확인한다.

## 이해 확인

1. `runner_snapshot`을 저장하는 이유는 무엇인가?
2. `best_run` 테이블의 task_id에 UNIQUE가 있는 이유는?
3. 기록된 score와 wiki 기록은 어떻게 다른가? (모듈 C에서 답)

## opencode에게 물어보세요
```
research/research.db 의 스키마를 설명하고, experiments와 best_run의 관계를
정규화 관점에서 설명해줘. 그리고 실험 이력이 쌓이면 어떤 분석이 가능할지 알려줘.
```

## 다음 레슨
[B5. 텍스트 데이터](09_text_prompt.md) — 이번엔 수치가 아닌 문장 데이터를 다뤄본다.