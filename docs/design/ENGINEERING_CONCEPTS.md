# 엔지니어링 개념 정리 — 하네스 / 루프 / 그래프 공학

> 목적: 에이전트 자동화 시스템을 설계·해부할 때 쓰는 세 가지 관점
> (하네스·루프·그래프)을 정의하고, 이 프로젝트(`opencode_ml_practice`)의
> 실제 구조에 매핑한다.
> 선수: D2(DAG 해부) · E3(자율 연구 루프) · J1~J3(에이전트 발전 심화) 이수.
> 상태: 학습·설계 참고 문서 (튜토리얼 보충 자료로도 사용)

## 1. 하네스 공학 (Harness Engineering)

### 정의

**"에이전트가 어떤 환경에서 실행되는가"를 설계하는 것.**

하네스는 에이전트의 **실행 런타임**이다. 같은 "스킬"이라도 하네스가 다르면
에이전트가 가진 도구·인증·파일 접근·대화 방식이 달라지므로 동작이 완전히
달라진다. 그래서 하네스 선택은 "어떤 도구를 쓸까"보다 **"에이전트에게 어떤
능력을 부여할까"**의 문제다.

> **용어**: 좁은 의미의 하네스 = 모델을 호출·도구를 연결하는 **실행 래퍼**
> (SkillOpt의 backend). 넓은 의미 = 그 래퍼를 포함한 에이전트 실행 환경 전체
> (CLI/인증/파일 접근). 이 문서는 **넓은 의미**를 쓴다.

| 하네스 | 층위 | 예시 사용처 | 특징 |
|--------|------|-------------|------|
| opencode | 제품/런타임 | 이 프로젝트 | 대화형 CLI, `.opencode/agents/*.md`로 에이전트·스킬 정의 |
| claude CLI | CLI 도구 | Shepherd | `~/.local/bin/claude`, subscription_login 인증 |
| GitHub Copilot | 제품/런타임 | 에디터 통합 | 자율 에이전트 모드 (SkillOpt 백엔드는 아님) |
| codex (codex_exec) | 백엔드 어댑터 | SkillOpt | API 키 필요, OpenAI 코드 실행 하네스 |

### 이 프로젝트에서

- 실행 하네스는 **opencode**. 학습자는 `opencode`를 켜고 "튜토리얼 시작해줘"라고
  입력해 대화형으로 에이전트(ml-researcher 등)를 호출한다.
- 에이전트가 **수정하는 파일**은 `research/<task>/experiment_runner.py` 단일 파일이고,
  **실행하는 경로**는 Airflow DAG(`make research`)다.
- Shepherd/SkillOpt 조사(`INSTALL_LOG.md`)에서 **하네스 비호환**이 도입 거부의 핵심
  근거였다: SkillOpt의 실측 백엔드는 `azure_openai / codex / claude / qwen / minimax`
  뿐이라 **opencode가 없어** 바로 도입할 수 없었다.

> **확인**: 터미널에서 `opencode`를 실행해 대화형 하네스가 뜨는지 본다.

## 2. 루프 공학 (Loop Engineering)

### 정의

**"실행 결과가 다음 실행에 어떻게 영향을 미치는가"를 설계하는 것.**

단일 실행은 루프가 아니다. 루프가 되려면 **결과가 입력으로 돌아와야** 한다.
핵심 질문은 "**뭘 닫을 것인가**"이며, 닫는 피드백의 종류에 따라 시스템의
발전 방식이 달라진다.

| 루프 | 이 프로젝트에서 | 닫히는 점 |
|------|----------------|-----------|
| **자율 연구 루프** | `사용자(가설) → 에이전트 → DAG → runner → DB → 위키 → 에이전트 보고 → 다음 가설` | 에이전트가 DB/위키를 읽고 다음 가설을 결정 |
| **제안→검증→적용 루프** (J3) | `get_config() → run_experiment() → evaluate_gate() → record_experiment() / gate_rejected` | 기각 사유는 `events`에만 남는다 — 다음 제안 반영은 에이전트가 `get_events()`를 읽어야 성립 (**자동화 미구현**) |
| **검증 게이트** (J2) | `metrics → GateResult → accepted/rejected` | **게이트 통과 시에만 `record_experiment()` 호출** (J3 수동 사이클 한정 — DAG 파이프라인 미연동) |
| **위키 ingest 루프** (AGENTS.md §9) | `research.db → tasks(자동) → log(자동) → techniques/index(수동)` | 숫자가 지식으로 변환되고, 지식이 다음 실험 방향 결정 |

### 이 프로젝트에서

모듈 J(J1~J3)의 핵심은 "**에이전트가 같은 실수를 반복하지 않도록 루프를 닫는 것**"이다.
이벤트 기록이 없으면 (a) 실패가 보이지 않고 (b) 같은 config를 반복 제안하고
(c) 근거 없는 변경이 best에 오른다. 루프 공학은 "어떤 피드백이 어떤 형태로
돌아오는가"를 설계하는 것이다.

주의: 현재 **게이트·기각 피드백은 자동으로 닫혀 있지 않다.** 게이트 판정은 J3
수동 사이클에서만 일어나고 DAG 파이프라인에는 연동돼 있지 않다(아래 그래프 §3과
AGENT_FRAMEWORKS_ANALYSIS 참고).

> **확인**: `make research-log`로 DB 요약(최고 score)을 보고 루프의 산출물을 확인한다.

## 3. 그래프 공학 (Graph Engineering)

### 정의

**"작업 간 의존성과 실행 순서를 어떤 구조로 배치할 것인가"를 설계하는 것.**

그래프는 루프 실행의 **물리적 구조**다. 같은 작업이라도 그래프 위상에 따라
병렬성·장애 전파·실험 우선순위가 달라진다. DAG(Directed Acyclic Graph)는
"방향성이 있고 사이클이 없는" 그래프로, 실행 오케스트레이션의 기본형이다.

> 이 절에서 **"태스크"는 연구 태스크(task_id, 예: `failure_prediction`)** 를 가리키고,
> DAG 노드는 `<task_id>_prepare` 형식의 **Airflow 태스크**다 (D2 표기와 동일).

| 그래프 구조 | 이 프로젝트에서 | 의미 |
|-------------|----------------|------|
| **선형** | `prepare → run → eval → report` (연구 태스크 내부 4단계) | 단순하지만 병렬성 없음 |
| **병렬 다중 태스크** | `failure_prediction ∥ quality_regression ∥ prompt_guard ∥ wafer_vision` | 4개 연구 태스크가 독립적으로 병렬 실행 |
| **선택적 분기** | `conf['task']` 지정 시 해당 태스크만 실행 | 그래프는 고정, 대상 아닌 태스크는 `_guard()`가 skip 처리하고 하류로 전파 |

### 이 프로젝트에서

`airflow/dags/ml_research_loop.py`가 DAG 형태로 4개 연구 태스크의 의존성을 정의한다.
각 연구 태스크는 `>>`로 연결된 4단계 선형 그래프를 가지지만, **연구 태스크 간에는
의존성이 없어 병렬 실행**된다. 그래프 공학은 "같은 실험을 어떤 순서로, 어디까지
병렬로, 장애 시 어디를 건너뛸 것인가"를 결정한다.

> **확인**: Airflow UI의 Graph 뷰에서 DAG의 위상(분기·병렬)을 본다.

## 4. 세 개념의 관계

| 관점 | 핵심 질문 | 연결 | 한 줄 요약 |
|------|-----------|------|------------|
| **하네스** | 어디서 실행되는가? | 에이전트의 실행 환경 결정 | 실행 환경 (도구/런타임) |
| **루프** | 결과가 어떻게 돌아오는가? | 하네스 안에서 반복되는 사이클 | 피드백이 닫히는 사이클 (반복/발전) |
| **그래프** | 작업을 어떤 순서로 배치하는가? | 루프 실행의 물리적 구조 | 작업 의존성의 구조 (순서/병렬성) |

**한 줄 요약**: 하네스는 **어디서**, 루프는 **무엇이 되돌아오는지**, 그래프는
**어떤 순서로** 실행되는지를 다룬다. 세 관점이 겹치지 않는다.

## 5. 관련 문서

- 에이전트 프레임워크 조사: [AGENT_FRAMEWORKS_ANALYSIS.md](AGENT_FRAMEWORKS_ANALYSIS.md)
- 설치·실측 로그: [INSTALL_LOG.md](INSTALL_LOG.md)
- 튜토리얼 J 모듈: [J1](../tutorial/J_agent_evolution/31_execution_events.md) ·
  [J2](../tutorial/J_agent_evolution/32_validation_gate.md) ·
  [J3](../tutorial/J_agent_evolution/33_propose_validate_apply.md)
- 자율 연구 루프: [E3](../tutorial/E_ai_automation/20_autonomous_research_loop.md)
- DAG 구조: [D2](../tutorial/D_infrastructure/16_dag_anatomy.md)