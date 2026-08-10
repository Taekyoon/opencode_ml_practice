# D3. 트리거와 스케줄 — DAG 실행해보기

## 학습 목표
- DAG를 수동으로 트리거하는 방법을 안다
- conf로 특정 태스크만 실행하는 방법을 안다
- 결과가 research/에 반영되는 과정을 확인한다

## 배경 지식

Airflow 실행 경로는 프로젝트 Makefile로 정리되어 있다 (AGENTS.md §6):

| 경로 | 명령 | 대상 |
|------|------|------|
| Airflow 수동 | `make research-task TASK=<task_id>` | conf로 특정 태스크만 |
| Airflow 전체 | `make research` | 등록된 모든 태스크 |
| Airflow 스케줄 | `ml_research_loop` (매일 00:00 UTC) | 자동 실행 |
| 로컬 (Airflow 없이) | `python research/<task_id>/experiment_runner.py` | 검증용 |

## 따라하기

### 0단계: 사전 확인
스케줄러가 실행 중인지 확인:
```bash
pgrep -fl "airflow scheduler"
```
없으면: `make scheduler`

### 1단계: 특정 태스크만 실행 (권장 — 가볍다)
```bash
make research-task TASK=failure_prediction
```
(또는 직접: `AIRFLOW_HOME=$(pwd)/airflow airflow dags trigger ml_research_loop -c '{"task": "failure_prediction"}'`)

### 2단계: 실행 결과 확인
```bash
make research-report
cat research/reports/report_failure_prediction_*.md
```
- `score` · 개선 여부가 담긴 리포트
- `research/research.db`에 기록되고 `wiki/tasks/failure_prediction.md`에 새 run이 추가된다

### 3단계: 위키 반영 확인
```bash
grep -n "자동 기록" research/wiki/tasks/failure_prediction.md
git diff research/wiki/   # (git repo라면)
```
실행 후 `_update_wiki`가 위키에 자동으로 기록했는지 본다.

### 4단계: (선택) 전체 태스크 실행
```bash
make research
```
- 등록된 모든 태스크(현재 4개)가 각자 4단계 태스크로 들어간다.
- 실행이 오래 걸리므로 선택 사항.

### 5단계: 스케줄 간격 이해
`schedule_interval="0 0 * * *"` -- 매일 자정 UTC 실행.
수동 트리거(`trigger`)는 스케줄과 무관하게 "지금" 1회 실행한다.

## 문제 해결

| 문제 | 대응 |
|------|------|
| `Matching dags not found to trigger` | DAG 파싱 실패. `make dags`(import errors) 확인 |
| 스케줄러 안 돎 | `pgrep -fl "airflow scheduler"` → 없으면 `make scheduler` |
| 실패한 run은? | retries=1로 자동 재시도, 그래도 실패하면 UI 로그 확인 |

## 이해 확인

1. `make research-task TASK=failure_prediction`와 `make research`의 차이는?
2. 수동 트리거와 스케줄 실행의 차이
3. 실행 후 위키에 자동으로 기록되는 내용은?

## opencode에게 물어보세요
```
방금 실행한 DAG의 상태를 airflow 명령으로 확인해주고,
각 task(failure_prediction_prepare/run/eval/report)가 succeeded인지 알려줘.
```

## 다음 레슨
[모듈 E 시작하기](../E_ai_automation/18_opencode_agents.md) — 이제 모든 것을 결합한다.