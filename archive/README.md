# archive/ — 보존된 레거시 코드/문서

> 삭제하지 않고 보관한 레거시 산출물. 읽기 전용으로 유지하며, 새 기능은 이곳에
> 넣지 않는다. 연구 태스크 프레임워크(`research/<task_id>/`, `ml_research_loop`)가
> 운영 표준이고, 여기의 내용은 과거 시점의 초기 접근을 기록한다.

## code/

| 경로 | 내용 | 대체 |
|------|------|------|
| `code/experiments/` | 초기 실험 스위트 (`run_baseline/run_imbalance/run_extreme/run_scalability`) | `research/<task>/experiment_runner.py` |
| `code/semiconductor_experiments_dag.py` | 4개 실험을 병렬 실행하던 Airflow DAG | `airflow/dags/ml_research_loop.py` |

- 원래 위치: `experiments/`, `airflow/dags/semiconductor_experiments.py`
- 아카이브 이유: research 태스크 레지스트리 기반 자율 연구 루프가 도입되면서 초기 실험
  코드와 동작이 중복되었다. 다만 동작(실험 디렉터리)은 남겨서 참고 가능하게 한다.

## docs/

| 파일 | 내용 |
|------|------|
| `CONVERSATION_LOG.md` | 초기 구축 과정 대화 로그 |
| `CONVERSATION_LOG_TASK_SCAFFOLD_WIKI.md` | 태스크 스캐폴드/위키 대화 로그 |
| `PROJECT_STRATEGY.md` | 초기 전략/요구사항 정리 |
| `IMBALANCED_DATA_SPECIALIST_PLAN.md` | 불균형 처리 스킬 계획 |
| `RETROSPECTIVE.md` | 작업 회고록 |

- 이들 문서는 위키(`research/wiki/`)가 지식 베이스의 표준이 되면서 더는 갱신하지
  않는다. 기록 목적으로 보존한다.

## 실행 산출물

`code/experiments/results/`·`summary.json` 같은 실행 산출물은 보존만 하며
git에는 추적하지 않는다(`.gitignore`의 `archive/**/results/`,
`archive/**/summary.json`).