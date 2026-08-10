# 에이전트 프레임워크 분석 — Shepherd / SkillOpt 개념의 프로젝트 적용

> 목적: 에이전트 프레임워크(Shepherd, SkillOpt)의 검증이 끝난 개념을 이 프로젝트에
> 어떻게 반영했고, 무엇을 도입하지 않았는지의 근거를 정리한다.
> 상태: **판정 완료 (2026-08-09 실측 기준)** — 실증 데이터는 `INSTALL_LOG.md` 참고.

## 1. 개요

`opencode_ml_practice`는 "ML 연구 태스크를 확장 가능한 구조로 관리"하는 자율 연구
프로젝트다. 여기서 에이전트(ml-researcher)가 실험을 자동 수행하고 결과를 쌓는다.

문제는 에이전트가 **"뭘 했는지"와 "왜 했는지"를 통제할 수 없는 상태로** 반복 학습을
돌린다는 점이었다. 두 프레임워크(Shepherd 0.3.0, SkillOpt 0.2.0)를 설치·실측해
"개념만 차용할지, 도입할지"를 판정했다.

**종합 판정**: 두 프레임워크 모두 **설치·로컬 재현은 완료**했지만 "도입(런타임 의존)"
이 아니라 **"개념 차용"**으로 이 프로젝트에 통합한다. 실데이터로 스킬을 트레이닝하는
것은 외부 유출·비용 리스크가 있어 지양한다.

| 프레임워크 | 설치 | 오프라인 | 채점(gate) | 하네스 | 도입 형태 |
|-----------|------|----------|------------|--------|-----------|
| Shepherd 0.3.0 (MIT) | ✅ | ✅ | 승인/기각/롤백 로직 | claude CLI 존재 | **이벤트 기록 + 게이트 개념** |
| SkillOpt 0.2.0 (MIT) | ✅ | ❌ (backend 요구) | 벤치마크 전용 | opencode 미지원 | **개념만 차용** (rollout→reflect→gate) |

## 2. 프레임워크 실측 요약

### Shepherd 0.3.0

- `run`이 실행의 **생명주기를 ledgering**한다: `run trace --events` → `run.lifecycle`
  이벤트, 각 실행의 **changeset**(변경된 파일·상태)과 **settlement**(retained/released)를 기록.
- `shepherd doctor claude --probe` → claude CLI 자동 인증(subscription_login) 확인.
- 즉, **"에이전트가 실행한 것의 흔적을 재구성할 수 있는지"**가 핵심 가치.

### SkillOpt 0.2.0

- 공개 API에 `GateAction`, `GateResult` (승인/기각/지연), `Edit`, `RolloutResult` 존재.
- **검증 게이트(validation gate) 개념**: 최적화 루프에서 무조건 채택하지 않고
  "통과한 것만" 채택한다.
- 그러나 `mock`/`handoff` 백엔드는 패키지에 **없어** API 키 없이는 루프 불가.
  envs도 벤치마크 전용(alfworld/docvqa 등)이라 실데이터 파이프라인과는 무관.
- `skillopt-sleep`은 지난 세션 전송 도구 → **반도체 데이터 외부 유출 위험으로 미채택**.

## 3. 개념 매핑 — 프레임워크 개념 → 프로젝트 구현

차용한 개념과 실제 구현을 대응시킨다. 인프라는 튜토리얼 **모듈 J**(J1~J3)로
코드와 함께 제공된다.

| 프레임워크 개념 | 프로젝트 구현 | 위치 |
|-----------------|--------------|------|
| Shepherd `run trace --events` (생명주기 이벤트 ledgering) | `events` 테이블 — `started`/`completed`/`failed`/`gate_rejected` | `src/research_store.py` |
| Shepherd `changeset` (변경된 경로/상태) | `runner_snapshot.py` + `run_<id>/metrics.json` (코드·결과 재현) | `research/<task>/results/` |
| Shepherd `settlement` (retained/released) | `experiments.status` (`completed`) + gate 통과 여부 | `src/research_store.py`, `src/validation_gate.py` |
| SkillOpt `GateAction`/`GateResult` (채점 구조체) | `GateCheck`/`GateResult` — `accepted` + 개별 `checks`(근거·심각도) | `src/validation_gate.py` |
| SkillOpt "통과한 것만 채택" | 게이트 통과 전 best_run 승격 금지 (규약) | **J2/J3 레슨 + AGENTS.md §4** — 파이프라인에 게이트 자동 연동은 아직 없음 |
| (두 프레임워크 공통) "왜" 남기기 | `_rationale` 메타 키 — 학습자가 config에 추가, 모델 파라미터로 미침투(팀 규약) | **J3 레슨** + `experiment_runner.py`(읽는 키가 고정돼 있어 우연히 안전) |

> **연동 수준의 현실**: `validation_gate`는 모듈·API가 준비되어 있지만, 자동 파이프라인
> (DAG 러너 실행)에는 아직 import되지 않는다. 게이트 판정·기각(`gate_rejected` 이벤트
> 포함)은 J3 레슨의 수동 사이클 코드에서 적용한다. 파이프라인 자동 연동은 후속 작업으로 둔다.

### 차용하지 않은 것

| 후보 | 미채택 사유 |
|------|-------------|
| Shepherd 런타임 의존 | 오프라인 동작은 확인됐지만 실험이 subprocess 실행 방식과 분리돼 있고, 저장 형태(자체 ledger)가 `research.db`/`results/` 규약과 중복 |
| SkillOpt skill 문자열 최적화 | ".md 스킬 → 벤치마크 배치 → 점수 최적화" 루프는 opencode 하네스 미지원 + API 키 필요 |
| SkillOpt sleep/train (세션 전송·학습) | 실데이터 외부 유출 및 토큰 비용 리스크 |
| real-time 에이전트 트레이닝 | "실데이터로 스킬을 트레이닝"은 프로젝트 규율(외부 유출 금지)과 충돌 |

## 4. 적용 결과 — 에이전트가 "발전"한다는 것의 정의

차용한 3개 축이 튜토리얼 모듈 J의 골격이 되었다:

1. **관측 (J1, 실행 이벤트 기록)** — 실패도 이벤트로 남겨 "없었던 일"을 없앤다.
   `_run_experiment`가 `started`→`completed`/`failed`를 `events`에 기록.
2. **검증 (J2, 검증 게이트)** — "점수가 올랐다 ≠ 개선됐다". 과적합/임계값 붕괴/무의미
   모델은 error 규칙으로 기각하고 근거를 구조체로 남긴다.
3. **적용 (J3, 제안→검증→적용 루프)** — 변경에 `_rationale`(왜)를 붙이고, 통과한 것만
   DB `experiments`에 채택, 기각된 것은 `gate_rejected` 이벤트로 남긴다.

이 루프가 닫혀 있어야 다음 세션의 에이전트가 (a) 과거 실패를 보고 (b) 같은 config를
반복 제안하지 않으며 (c) 근거 있는 변경만 best로 승격한다. **이것이 "에이전트를
발전시키는 법"**이며, 외부 프레임워크 없이 사내 파이프라인에 개념을 입힌 형태다.

## 5. 관련 문서

- 실증 데이터: `docs/design/INSTALL_LOG.md` (설치·CLI·판정 실측)
- 튜토리얼: `docs/tutorial/J_agent_evolution/31_execution_events.md` (J1),
  `32_validation_gate.md` (J2), `33_propose_validate_apply.md` (J3)
- 구현: `src/research_store.py` (events API), `src/validation_gate.py` (GateCheck/GateResult),
  `airflow/dags/ml_research_loop.py` (`_run_experiment` 이벤트 기록)