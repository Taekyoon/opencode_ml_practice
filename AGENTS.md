# AGENTS.md — 반도체 Failure 예측 프로젝트 작업 가이드

> 이 문서는 opencode가 이 프로젝트에서 작업할 때 반드시 먼저 읽고 따라야 할 규칙과 워크플로를 정의합니다.

## 1. 프로젝트 개요

반도체 공정/측정 수치 데이터로 제품 failure를 예측하는 ML 파이프라인 프로젝트.

핵심 가치: **연구 태스크를 확장 가능한 구조로 관리**한다. 새 예측 문제가 필요하면 빌트인이 아닌
`scripts/new_task.py` 스캐폴드로 추가하고, 이를 Airflow `ml_research_loop` DAG에서 자동 실행한다.

## 2. 디렉터리 구조

```
opencode_ml_practice/
├── scripts/new_task.py          # 새 연구 태스크 자동 생성 (스캐폴드 CLI)
├── research/
│   ├── tasks_registry.py        # 태스크 레지스트리 (빌트인) + tasks_extra.json 로드
│   ├── tasks_extra.json         # 스캐폴드로 추가된 태스크 (런타임 등록 저장)
│   ├── failure_prediction/      # 빌트인 분류 태스크
│   │   ├── experiment_runner.py # 단일 파이프라인 (에이전트가 여기를 튜닝)
│   │   ├── program.md           # 연구 지침서
│   │   └── results/
│   ├── quality_regression/      # 빌트인 회귀 태스크
│   ├── prompt_guard/            # 프롬프트 가드레일 태스크 (텍스트 다중 분류, 튜토리얼 모듈 G)
│   │   ├── experiment_runner.py # 텍스트 분류 파이프라인 (TF-IDF + 분류기)
│   │   ├── program.md           # 지침서
│   │   ├── predict.py           # 학습 모델로 실시간 프롬프트 판별 API
│   │   └── results/
│   ├── wafer_vision/            # 웨이퍼맵 결함 태스크 (이미지 분류, 튜토리얼 B8/I)
│   │   ├── experiment_runner.py # 이미지 파이프라인 (flatten+PCA+그래디언트+방사)
│   │   ├── program.md           # 지침서
│   │   ├── predict.py           # 학습 모델로 웨이퍼맵 결함 판별 API
│   │   └── results/
│   ├── wiki/                    # 실험 기록 지식 베이스 (index/log/overview/tasks/techniques/...)
│   ├── datasets/                # 등록된 dataset 저장소 (research.db 가 인덱스)
│   ├── inbox/                   # 새 데이터 투입 폴더
│   └── research.db              # dataset/실험 기록 SQLite
├── airflow/dags/ml_research_loop.py  # 자율 연구 루프 DAG (매일 자정)
├── src/data_manager.py         # dataset 등록/로드 API (+ text_col/img_col 지원)
├── src/text_processing.py      # 텍스트 토큰화 / TF-IDF 벡터라이저
├── src/image_processing.py     # 웨이퍼맵 특징 추출 (flatten/PCA/그래디언트/방사)
├── src/generate_wafer_images.py # 웨이퍼맵 합성 이미지 생성
├── src/wafer_data_loader.py    # WM-811K 공개 데이터셋 로더
├── src/generate_prompt_data.py # 프롬프트 합성 데이터 생성 (하드 케이스 포함)
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
- `research/wiki/` 는 지식 산출물로 커밋한다 (세션 간 공유 필수)
- `research/**/results/`, `research/research.db`, `airflow/` 운영 산출물은 gitignore 대상 (커밋 금지)
- `tasks_extra.json` 은 프로젝트 정의(사용자 등록 task)라면 커밋 OK, 임시 테스트만 생성됐던 경우 제거 후 커밋

## 9. 실험 기록 위키 (LLM Wiki 패턴)

**핵심 원칙**: 실험 결과는 `research.db`(숫자) + `research/wiki/`(지식) 양쪽에 기록한다.
`wiki/`는 LLM이 유지하는 markdown 지식 베이스로, 세션 간 발견이 누적되는 곳이다.

### 9.1 위키 구조

```
research/wiki/
├── index.md              # 모든 페이지 목록 (content 지향, 모든 ingest 후 갱신)
├── log.md                # 연대기순 기록 (append-only)
├── overview.md           # 대시보드 — 새 세션은 이걸 먼저 읽는다
├── learning_progress.md  # 튜토리얼 진행 기록 (레슨 완료 시 갱신)
├── tasks/<task_id>.md    # 태스크별 누적 발견
├── techniques/           # 기법별 종합 (smote, scaling, model_comparison 등)
├── datasets/             # 데이터셋 분포/주의사항
└── synthesis/
    └── lessons_learned.md  # 교차 태스크 교훈 + 다음 방향
```

### 9.2 Ingest 규칙 (새 실험/개발 후 반드시)

1. `research.db`에서 최신 run을 확인 (`src.research_store`)
2. `tasks/<task_id>.md` 갱신 — 최고 결과 테이블에 새 run 추가, 발견사항 1줄 기록
3. 사용한 기법이 있으면 `techniques/<기법>.md`에도 기록 (어느 태스크/조건에서 효과적인지 맥락 포함)
4. `log.md`에 append: `## [YYYY-MM-DD] ingest | <task_id> | <run_id> | score=<score>`
5. `index.md` 갱신 (페이지 추가/변경 시)

### 9.3 Query 규칙 (질문/분석 시)

1. `wiki/index.md` → 관련 페이지 탐색 → 읽고 종합
2. 가치 있는 답변/인사이트가 나오면 → 새 wiki 페이지로 파일링 (chat에만 두지 않음)

### 9.4 Lint 규칙 (정기 검진, `make wiki-lint`)

- 모순: 태스크 간 모순된 발견 → 양쪽 페이지에 맥락 명시
- 고아 페이지: index.md에 없는 위키 페이지 확인
- 오래된 데이터: score 갱신 후 7일 경과한 task 페이지 표시
- broken 링크: 내부 `../` 링크 존재 여부 확인

### 9.5 실험 규율

- **한 번에 하나의 변수만** 변경 (A/B 원칙)
- 실험 후 wiki 갱신은 **tasks → techniques → log → index** 순서
- 효과있었다/없었다를 **맥락과 함께** 기록

## 10. 튜토리얼 모드 (docs/tutorial/)

이 프로젝트는 **opencode 기반 대화형 튜토리얼** 교재이기도 하다.
사용자가 학습 의도를 드러내면 아래 튜토리얼 모드로 전환한다.

### 10.1 튜토리얼 감지 (자동)

다음 발언이 오면 튜토리얼 모드를 시작한다:
- "배우고 싶어", "튜토리얼", "레슨", "학습", "모르겠어", "설명해줘" 등
- 또는 `docs/tutorial/README.md` 를 먼저 읽거나 지목하는 경우

> 사용자가 학습 모드인지 *개발 모드*인지 불분명하면 **짧게 물어본다**:
> "지금 튜토리얼(배우기) 모드로 진행할까요, 아니면 실제 작업(개발)을 할까요?"

### 10.2 학습 유형 확인

사용자가 처음이면 4가지 학습자 유형을 보여주고 선택받는다:

| 유형 | 설명 | 추천 경로 |
|------|------|-----------|
| opencode 초보 | AI 코딩 도구가 처음 | 모듈 A → E |
| ML/AI 초보 | ML 개념이 처음 | A2 → B → C |
| ML 실무자 | 이론은 알지만 코드 구현 초보 | B → C |
| AI 자동화 학습자 | 자동화에 관심 | A1 → A4 → E → C1 |

### 10.3 레슨 진행 방식

1. `docs/tutorial/README.md` 의 목록에서 **다음 레슨**을 고른다
2. 해당 레슨을 읽는다 (마크다운 파일)
3. "따라하기"의 각 단계를 **사용자와 함께** 실행한다 — 사용자가 명령을 직접 칠 수 있게
   돕되, 어려워 하면 대신 실행해 결과를 보여준다
4. 레슨 끝 "이해 확인" 질문을 던져 사용자가 답하게 한다
5. 레슨 완료 시 `research/wiki/learning_progress.md` 를 갱신한다 (아래 규칙)

### 10.4 진행 기록 (learning_progress.md)

- 학습 진행 상황은 `research/wiki/learning_progress.md` 에 기록한다
- 형식: 완료한 레슨을 목록으로 유지 + 현재 진행 중인 레슨 1줄
- 레슨을 하나 끝낼 때마다 이 파일을 갱신한다 (다음 세션 이어가기 위함)
- 사용자가 명시적으로 "기록하지 마"라고 하지 않는 한 자동으로 갱신한다

### 10.5 튜토리얼 모드 제약

- 튜토리얼 모드에서는 **실제 파일을 마음대로 바꾸지 않는다** — 레슨에 있는
  스캐폴드/실습 명령 외에는 사용자 승인을 받는다
- 튜토리얼 실습이 끝나면 임시로 만든 파일/태스크/스킬은 정리하고 기록만 남긴다
- 학습자 질문에는 "개념 설명"에 집중하고, 불필요한 코드 재작성은 피한다

### 10.6 수료 기준

- 모듈 F(F1 종합 프로젝트) 완료 = 튜토리얼 수료
- 모듈 G(AI 가드레일, G1~G4)는 **선택 심화** — 수료 후 LLM 안전/프롬프트 분류에 관심이
  있으면 이어서 진행한다. `research/prompt_guard/` 태스크와 `prompt-guard` 에이전트가 실습 대상이다
- 모듈 I(이미지 AI, I1~I3)도 **선택 심화** — 웨이퍼맵 이미지 분류에 관심이 있으면
  B7(26)·B8(27)을 먼저 들은 뒤 진행한다. `research/wafer_vision/` 태스크와
  `wafer-vision` 에이전트가 실습 대상이다
- 수료 후엔 일반 개발 모드로 복귀한다
