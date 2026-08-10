# D2. DAG 해부 — ml_research_loop 뜯어보기

## 학습 목표
- `airflow/dags/ml_research_loop.py`의 구조를 읽을 수 있다
- 태스크 간 의존성(`>>`)과 conf 선택 로직을 이해한다
- 스케줄과 재시도 설정을 안다

## 배경 지식

`ml_research_loop`는 **자율 연구 루프**다.
`research/tasks_registry.py`에 등록된 태스크를 읽어 각 태스크별로
"데이터 준비 → 실험 실행 → 평가 저장 → 리포트 생성"을 순서대로 실행한다.

### 4단계 흐름 (태스크당)
```
t_prepare >> t_run >> t_eval >> t_report
```

| 태스크 | 함수 | 역할 |
|--------|------|------|
| `{task}_prepare` | `_prepare_data` | 데이터 준비 확인 |
| `{task}_run` | `_run_experiment` | `experiment_runner.py`를 subprocess로 실행 |
| `{task}_eval` | `_evaluate_store` | 결과를 `research.db`에 기록, best 갱신 |
| `{task}_report` | `_generate_report` + `_update_wiki` | 일일 리포트 생성 + 위키 반영 |

> **흐름**: runner로 실행 → 숫자 기록(`research.db`) → 지식 기록(`wiki/`) → 리포트 파일.
> 이 4단계가 "모듈 B/C"에서 배운 것의 자동화 버전이다.

### XCom으로 데이터 전달
- `_run_experiment`가 `xcom_push(key="run_result", value=result)`로 실행 결과 전달
- `_evaluate_store`가 `ti.xcom_pull(task_ids=f"{task_id}_run", key="run_result")`로 받는다
- 즉, 태스크 간에 `metrics.json` 내용을 주고받는 것이다

### conf로 특정 태스크만 실행
```python
# airflow dags trigger ml_research_loop -c '{"task": "quality_regression"}'
def _selected_tasks(conf):
    ...
    raw = conf.get("tasks") or conf.get("task")
    return [get_task(t).id for t in raw]  # 이번 실행 대상
```
`_guard()`가 "이번 실행 대상 아님"인 태스크를 `AirflowSkipException`으로 건너뛴다.

### 스케줄 설정
```python
schedule_interval="0 0 * * *"   # 매일 00:00 UTC
start_date=datetime(2026, 8, 1)
catchup=False
retries=1
```
- `catchup=False`: 과거 시점을 따라잡아 실행하지 않음 (무의미한 재실행 방지)
- `retries=1`: 실패 시 1회 재시도

## 따라하기

### 1단계: DAG 소스 읽기
```bash
python -c "print(len(open('airflow/dags/ml_research_loop.py').readlines()), 'lines')"
```
4단계의 함수(`_prepare_data`, `_run_experiment`, `_evaluate_store`, `_generate_report`,
`_update_wiki`)를 찾아본다.

### 2단계: 등록 태스크별로 이뤄지는 구조 확인
```bash
python - <<'PY'
from research.tasks_registry import list_tasks
print("DAG 안에 생성될 태스크:", list_tasks())
PY
```
- `research`를 패키지(`research.xxx`)로 import한다. 프로젝트 루트에서 바로 실행하면 된다.

### 3단계: 스케줄 확인
```bash
AIRFLOW_HOME=$(pwd)/airflow airflow dags show ml_research_loop
```
각 task와 의존성(`>>`)이 그래프로 출력된다.
> `AIRFLOW_HOME`을 프로젝트의 `airflow/`로 꼭 지정해야 한다. 지정하지 않으면
> 기본 위치(`~/airflow`)를 봐서 DAG를 못 찾는다.

### 4단계: 특정 태스크만 실행 방법 확인 (D3에서 실행)
아래를 이해만 하고 D3에서 실행한다:
```bash
airflow dags trigger ml_research_loop -c '{"task": "quality_regression"}'
```

## 이해 확인

1. 4단계 흐름 중 "지식 기록"에 해당하는 단계는 무엇인가? (wiki)
2. `_guard`는 어떤 상황에서 skip을 만드나?
3. `catchup=False`의 의미는?

## opencode에게 물어보세요
```
ml_research_loop.py를 읽고 이 DAG가 하는 전체 일을 한 그림으로
관계와 흐름(태스크 그래프)까지 설명해줘.
```

## 다음 레슨
[D3. 트리거와 스케줄](17_trigger_and_schedule.md) — 실제로 DAG를 실행해본다.