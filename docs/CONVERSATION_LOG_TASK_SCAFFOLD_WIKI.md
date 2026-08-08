# 세션 대화 기록 (2차) — 태스크 스캐폴드 CLI + 실험 기록 위키 (2026-08-08)

> `semiconductor_failure_prediction` 프로젝트 세션 [2차] 기록.
> 이 문서는 "어떤 대화를 나누어 지금의 결과(연구 태스크 확장 구조 + 위키)가 나왔는지"를
> 재구성한 것이다. 1차 세션(파이프라인+스킬+전략)은 `docs/CONVERSATION_LOG.md` 참조.

---

## 1. 대화 흐름 개요

| 순서 | 주제 | 결정/결과 |
|------|------|----------|
| 1 | 지금까지 작업 확인 | "What did we do so far?" — 1차 세션 산출물 확인 (파이프라인, 스킬, 전략, 자율 연구 루프) |
| 2 | 새 연구 태스크 추가 방식 | 사용자에 옵션 제시 → **A. 스캐폴드 CLI** 선택 |
| 3 | 스캐폴드 CLI 구현 | `scripts/new_task.py` + registry runtime 등록 + Makefile 타깃 |
| 4 | 워크플로 문서화 요구 | `AGENTS.md`에 스캐폴드 워크플로 규칙 작성 |
| 5 | 푸시 | `8d9c3de` |
| 6 | Karpathy gist 검토 | llm-wiki 패턴 선정 — 실험 기록을 "누적되는 위키"로 관리 |
| 7 | 기록 관리 계획 수립 | 3계층 매핑 + 구현 단계 제안 → **전체 구현** 선택 |
| 8 | 위키 구현 | `research/wiki/` 10개 페이지 + `wiki_lint.py` + DAG 자동 Ingest |
| 9 | 커밋/푸시 | `9148c27` |

---

## 2. 주요 대화 내용 (스토리 재구성)

### 2-1. "새 태스크를 어떻게 추가할까?" — 옵션 대화

자율 연구 루프(ml_research_loop, Airflow DAG)는 `research/tasks_registry.TASKS`를
읽어 태스크별로 실험을 돌린다. 문제는 새 예측 문제(새 태스크)를 추가할 때마다
**레지스트리 등록 + runner 생성 + 지침서 작성**을 수동으로 해야 한다는 점이었다.

사용자에게 세 가지 방향을 제시:
- **A. 스캐폴드 CLI** — `new_task.py` 하나로 실행 파일·지침서·레지스트리 등록을 자동 생성
- B. 빌트인 태스크 확장 — 레지스트리에 미리 몇 개 태스크만 추가
- C. 에이전트만 진행 — 과정 없이 자율 에이전트로만 태스크 추가

→ 사용자 선택: **A (스캐폴드 CLI)**

**구현하면서 직면한 문제와 해결:**
1. 레지스트리에 외부 태스크를 런타임 등록(JSON) 하도록 확장 → `register_task()` +
   `tasks_extra.json` 로드로 **재기동 후에도 유지**, Airflow 재파싱 시 자동 인식
2. `new_task.py` 초안의 규칙·미정의 함수 오류를 수정하며 단계적으로 완성
3. `feature_cols`가 SQLite에서 JSON 문자열로 저장됨 → `json.loads` 처리
4. 분류/회귀 자동 판정 → target 값 개수(`<=20`)로 구분

**검증:** 스캐폴드로 분류(score)와 회귀(r2) 태스크를 각각 생성해 단독 실행 확인,
`airflow dags show`에서 새 태스크 4개 자동 인식 확인.

### 2-2. "어떻게 하면 기록을 효율적으로 관리할까?" — Karpathy gist 대화

Karpathy의 gist `llm-wiki`를 검토하며 대화한 내용:

- **기존 방식**: 결과를 SQLite(숫자) + json(원시 실행)에 구조적으로 저장하지만,
  "SMOTE는 이 태스크에서 이로움이 있었나" 같은 **실험 간 연결된 발견**이 없음
- **Wiki 패턴**: 원본은 유지하고, LLM이 지속적으로 갱신·교차 참조하는 markdown 위키를
  중간 계층으로 둔다 → 세션 간 발견이 누적됨

| Karpathy 계층 | 이 프로젝트 매핑 |
|---|---|
| Raw sources | results/run_*/metrics.json, runner_snapshot.py |
| The wiki | `research/wiki/` (LLM이 유지하는 markdown 페이지) |
| Schema | `AGENTS.md`의 Wiki 유지 규칙 |
| index.md / log.md | `wiki/index.md` / `wiki/log.md` |

→ 사용자는 **전체(위키구조 + 초기 페이지 + 규칙 + DAG 연동) 한 번에** 선택

### 2-3. 위키 구현 시점의 관찰

- 기존 실험 기록 조사: failure_prediction 6회, quality_regression 4회 **모두 동일한
  베이스라인 score** → "베이스라인 단계, 변주 미시도"가 위키에 명확히 기록되어야 함
- 위키 초기 페이지에 현재 최고(0.7912 / 0.9822)와 다음 후보(SMOTE·모델 비교)를 반영

---

## 3. 주요 의사결정(2차)

| 결정 | 내용 |
|------|------|
| 새 태스크 추가 방식 | 스캐폴드 CLI(`scripts/new_task.py`) — 수동 파일 생성 금지 |
| 외부 태스크 저장 | `research/tasks_extra.json` (런타임 등록, 재기동 유지, DAG 자동 인식) |
| 실험 기록 방식 | SQLite(구조) + 위키(지식) 병행 |
| 위키 구조 | index/log/overview + tasks/techniques/datasets/synthesis |
| 위키 정기 검진 | `make wiki-lint` (broken link·고아·미등록·오래된 데이터) |
| DAG 연동 | `_generate_report()` 이후 `_update_wiki()` 자동 호출 |

---

## 4. 산출물(검증 결과)

| 산출물 | 경로 |
|--------|------|
| 새 태스크 스캐폴드 CLI | `scripts/new_task.py` |
| 레지스트리 런타임 등록 | `research/tasks_registry.py` (`register_task`) |
| 외부 태스크 구성 | `research/tasks_extra.json` (동적) |
| 태스크 추가 Make 타깃 | `Makefile` (`make new-task`) |
| 지식 베이스 구조 | `research/wiki/` (index/log/overview/tasks/techniques/datasets/synthesis) |
| 위키 린트 | `scripts/wiki_lint.py` (Make `wiki-lint`) |
| DAG 자동 Ingest | `airflow/dags/ml_research_loop.py` (`_update_wiki`) |
| 워크플로 가이드 | `AGENTS.md` (스캐폴드 + 섹션9 Wiki 유지 규칙) |
| 본 문서 | `docs/CONVERSATION_LOG_TASK_SCAFFOLD_WIKI.md` |

**즉 검증:**
- 스캐폴드로 분류/회귀 태스크 생성 → runner 단독 실행 (분류 score 0.7636, 회귀 R² 0.9816)
- `make new-task`/`make wiki-lint` 정상 동작
- `airflow dags show`에서 새 태스크 자동 인식, import 오류 없음
- `wiki_lint.py`: broken link·고아·미등록·내부 링크 오류 0건

---

## 5. Git 커밋 내역

| 커밋 | 내용 |
|------|------|
| `8d9c3de` | 태스크 스캐폴드 CLI + 런타임 등록 + 작업 가이드 문서화 |
| `9148c27` | 실험 기록 위키 도입 (LLM Wiki 패턴) + DAG 자동 Ingest |

---

## 6. 현재 상태 & 앞으로 할 일

### 현재 상태

- 연구 태스크 확장 프로세스 확립: `new_task.py` → 실행 → 위키 갱신
- 실험 기록이 SQLite + 위키 양쪽에 남는 2중 체계
- 위키: 10개 페이지, 베이스라인 단계 상태 명시 (분류 0.7912 / 회귀 0.9822)

### 남은 작업 (위키 기반의 다음 실험)

1. failure_prediction: **SMOTE** → 위키 `tasks/`와 `imbalance_handling.md` 기록
2. 모델 비교(RandomForest / GradientBoosting, `scale=False` 주의)
3. 임계값 최적화 / `optimize_threshold=True`
4. 회귀는 R² 0.9822 → 비선형 확인용 RandomForestRegressor 1회 시도
5. 실험 후 위키 Ingest 규칙(9.2)대로 갱신

---

## 7. 참고 파일

- `docs/CONVERSATION_LOG.md` — 1차 세션 기록(파이프라인·전략)
- `AGENTS.md` — 스캐폴드 워크플로 + 위키 유지 규칙
- `research/wiki/overview.md` — 현재 대시보드(진입점)
- `docs/PROJECT_STRATEGY.md` — 100점 로드맵