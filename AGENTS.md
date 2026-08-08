# AGENTS.md — 반도체 Failure 예측 프로젝트 작업 가이드

> 이 문서는 opencode가 이 프로젝트에서 작업할 때 반드시 먼저 읽고 따라야 할 규칙과 워크플로를 정의합니다.

## 1. 프로젝트 개요

반도체 공정/측정 수치 데이터로 제품 failure를 예측하는 ML 파이프라인 프로젝트.

핵심 가치: **연구 태스크를 확장 가능한 구조로 관리**한다. 새 예측 문제가 필요하면 빌트인이 아닌
`scripts/new_task.py` 스캐폴드로 추가하고, 이를 Airflow `ml_research_loop` DAG에서 자동 실행한다.

## 2. 디렉터리 구조

```
semiconductor_failure_prediction/
├── scripts/new_task.py          # 새 연구 태스크 자동 생성 (스캐폴드 CLI)
├── research/
│   ├── tasks_registry.py        # 태스크 레지스트리 (빌트인) + tasks_extra.json 로드
│   ├── tasks_extra.json         # 스캐폴드로 추가된 태스크 (런타임 등록 저장)
│   ├── failure_prediction/      # 빌트인 분류 태스크
│   │   ├── experiment_runner.py # 단일 파이프라인 (에이전트가 여기를 튜닝)
│   │   ├── program.md           # 연구 지침서
│   │   └── results/
│   ├── quality_regression/      # 빌트인 회귀 태스크
│   ├── datasets/                # 등록된 dataset 저장소 (research.db 가 인덱스)
│   ├── inbox/                   # 새 데이터 투입 폴더
│   └── research.db              # dataset/실험 기록 SQLite
├── airflow/dags/ml_research_loop.py  # 자율 연구 루프 DAG (매일 자정)
├── src/data_manager.py         # dataset 등록/로드 API
├── src/research_store.py       # 실험 기록/최고 점수 API
└── Makefile                    # 운영 명령 모음
```

## 3. 새 연구 태스크를 추가하는 법 (스캐폴드)

사용자가 "새 태스크"를 요청하면 아래 CLI를 사용한다. 반드시 수동으로 폴더/파일을 만들지 말 것.

```bash
# 기 등록 dataset 사용
python scripts/new_task.py <task_id> --dataset <dataset_name> --target <target_col> [--note "..."]

# inbox의 새 CSV를 dataset으로 등록하면서 태스크 생성
python scripts/new_task.py <task_id> --inbox <file.csv> --target <target_col> [--note "..."]

# make 로도 가능
make new-task TASK=<task_id> DATASET=<dataset_name> TARGET=<target_col> NOTE="..."
```

**스캐폴드가 하는 일:**
1. dataset 유효성/컬럼 검증
2. `research/<task_id>/` + `experiment_runner.py` + `program.md` + `results/` 생성
3. target 값 유형으로 분류/회귀 자동 판정 (score: 분류=score/F1×PR-AUC, 회귀=r2)
4. `research/tasks_extra.json`에 기록 → registry 로드 → Airflow 재파싱 시 DAG 자동 인식

**검증 방법:**
```bash
python research/<task_id>/experiment_runner.py     # 단독 실행 확인
airflow dags show ml_research_loop                 # 새 태스크 4개 태스크 표시 확인
```

## 4. 태스크 구성 요소 (반드시 준수)

| 항목 | 역할 |
|------|------|
| `experiment_runner.py` | 단일 파이프라인. `python research/<task_id>/experiment_runner.py` 로 실행 |
| `get_config()` | 하이퍼파라미터를 이 dict에 담음 (에이전트 튜닝 지점) |
| `run_experiment()` | 데이터 로드→전처리→학습→평가, `{"config","metrics","score","kind"}` 반환 |
| `_run_and_save()` | 결과를 `results/run_<id>/metrics.json` + `runner_snapshot.py` 로 저장 |
| `program.md` | 사람이 연구 방향/평가 지표 작성 |

**score 정의(변경 시 registry의 `score_name`과 일치시킬 것):**
- 분류: `score = F1 × PR-AUC`
- 회귀: `score = R²`

## 5. 데이터셋 (data_manager)

- 등록: `research/inbox/`에 CSV/parquet를 넣고 `scan_inbox()`로 감지, `register_file()` 등록
- 조회/로드: `get_dataset(name)`, `load_dataset(name) -> (X, y)`
- 기등록 dataset 확인:
```bash
python -m src.data_manager
```

## 6. 실험 실행 경로

| 경로 | 명령 | 대상 |
|------|------|------|
| 로컬 실행 | `python research/<task_id>/experiment_runner.py` | 단일 태스크 즉시 실행 |
| Airflow 수동 | `make research-task TASK=<task_id>` | conf로 특정 태스크만 |
| Airflow 전체 | `make research` | 등록된 모든 태스크 |
| Airflow 스케줄 | `ml_research_loop` (매일 00:00 UTC) | 자동 |

**스냅샷 규칙**: 실험 결과 폴더에 `runner_snapshot.py` 저장됨. 학습에 쓰인 코드를 남겨 재현 가능하게 한다.

## 7. 이 프로젝트에서 코딩할 때

- 기존 스타일 유지: 결과 `json` 저장, `research.db` 기록은 `src.research_store` 사용
- 에이전트(ml-researcher)의 튜닝은 `get_config()`를 수정하는 방식으로만 함
- 다른 태스크의 runner를 복제하지 않고, 새 스킬/새 태스크가 필요하면 스캐폴드를 사용

## 8. 커밋 시 유의

- `scripts/`와 `research/tasks_registry.py` 및 `Makefile`은 소스이므로 커밋 대상
- `research/**/results/`, `research/research.db`, `airflow/` 운영 산출물은 gitignore 대상 (커밋 금지)
- `tasks_extra.json` 은 프로젝트 정의(사용자 등록 task)라면 커밋 OK, 임시 테스트만 생성됐던 경우 제거 후 커밋

## 9. 다음 세션이 이어할 여지 (TODO)

이 문서는 스캐폴드 기반 워크플로의 기반을 기록했다. 다음 세션에서 검토할 항목:
- [ ] `scripts/new_task.py` 의 태스크 삭제(`unregister_task`) CLI 지원
- [ ] 템플릿 선택 옵션 (baseline뿐 아니라 XGBoost/LGBM 등)
- [ ] `program.md` 생성시 연구 스프린트 시작 템플릿 추가
- [ ] 연구 에이전트의 결정 기록(feedback 루프) 문서화
