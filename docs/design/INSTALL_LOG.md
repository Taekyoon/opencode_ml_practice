# Shepherd / SkillOpt 설치·실행 로그

> 목적: AGENT_FRAMEWORKS_ANALYSIS.md 작성을 위한 설치·실행 실증 데이터 확보.
> 상태: **실행 완료 (2026-08-09)**

## 조사 스냅샷

| 항목 | 값 |
|------|-----|
| 날짜 | 2026-08-09 |
| OS | macOS (darwin, x86_64) |
| Python | 3.12.12 (miniconda base) |
| 격리 venv | `~/.venvs/agent-tools` |
| Shepherd | `shepherd-ai==0.3.0` (MIT) |
| SkillOpt | `skillopt==0.2.0` (MIT) |
| claude CLI | 2.1.226 (`~/.local/bin/claude`, subscription_login 인증됨) |

## 0단계: 환경 격리

```bash
python3 -m venv ~/.venvs/agent-tools
~/.venvs/agent-tools/bin/pip install -U pip
```

- base 환경 측정: `torch 2.2.2`, `numpy 1.26.4` (베이스로 고정)
- venv `pip freeze` (before): 비어있음 (36개 패키지 설치 후와 대비)

## 1단계: Shepherd 설치

```bash
~/.venvs/agent-tools/bin/pip install shepherd-ai
# → Successfully installed shepherd-ai-0.3.0 
#   (+ pygit2-1.20.0, cffi, pydantic 2.13.4, click 8.4.2, tomli-w, typing-inspection)

~/.venvs/agent-tools/bin/pip check  →  No broken requirements found.
~/.venvs/agent-tools/bin/shepherd --version →  shepherd, version 0.3.0
```

- **라이선스**: MIT (dist-info METADATA에서 확인)
- **CLI 구조**: `demo` / `doctor` / `init` / `package` / `run` / `task`
  - `run` 서브코맨드: `list`, `show`, `trace`, `changeset`, `select`, `release`, `discard`, `apply`, `start`, `repair` 등

## 2단계: Shepherd 오프라인 테스트

```bash
mkdir /tmp/shepherd-qs && cd /tmp/shepherd-qs
~/.../shepherd init /tmp/shepherd-qs
# → Initialized Shepherd workspace: /private/tmp/shepherd-qs
#   git: initialized / vcscore: created / backend: auto / adoption: worktree

~/.../shepherd demo write quickstart > world_channel.py
~/.../bin/python world_channel.py
# → {"run_ref":"run-b8c8f46763e2","status":"retained","output_state":"released",
#     "changed_paths":["SHEPHERD_QUICKSTART.txt"],"preview":"Hello from a Shepherd retained output.\n",
#     "settlement":"released"}

~/.../bin/shepherd run list
# → run-b8c8f467 retained  shepherd_generated_write_note.write_note 2026-08-09T11:25:10Z

~/.../bin/shepherd run show --latest --json   # → 대형 JSON: authority_context, launch_context, task 그림 참조
~/.../bin/shepherd run trace --latest --events
# → kinds: {'run.lifecycle': 1}, terminal_status: retained
~/.../bin/shepherd run changeset --latest
# → binding: workspace / state: released / paths: [SHEPHERD_QUICKSTART.txt]

~/.../bin/shepherd doctor claude --probe
# → ok claude-cli: /Users/seohyunwon/.local/bin/claude
#   ok claude-auth-probe: authenticated (subscription_login)
```

**판정**: 오프라인 retained-output 테스트 완전 동작. API 키 불필요. run이 ledgering·trace·changeset 전부 기록.

## 3단계: SkillOpt 설치

```bash
~/.venvs/agent-tools/bin/pip install skillopt
# → Successfully installed skillopt-0.2.0
#   신규 유입: azure-identity 1.25.3, numpy 2.5.1, openai 2.53.0, cryptography, msal, openpyxl 등 36개

~/.venvs/agent-tools/bin/pip check  →  No broken requirements found.
```

- **라이선스**: MIT
- **numpy 2.5.1 유입 확인** — venv 격리 덕에 base의 torch 2.2.2는 무변화. Claude CLI 경고가 정확했음.
- base 회귀 확인: `torch 2.2.2` / `numpy 1.26.4` 그대로.

## 4단계: SkillOpt 기본 동작

```bash
~/.../bin/python -c "import skillopt; print(skillopt.__version__)" → 0.2.0
# public API: BatchSpec, Edit, GateAction, GateResult, Patch, RolloutResult, SlowUpdateResult,
#             datasets, evaluation, types
```

- **CLI**: `skillopt-train` / `skillopt-eval` / `skillopt-sleep` 3개.
  - `skillopt-sleep`는 로컬 에이전트 과거 세션 트랜스크립트를 수집·전송하는 도구 — **반도체 데이터 외부 유출 위험으로 미실행·미채택** (Claude CLI 경고와 동일 결론).
- **backends**: azure_openai / codex(codex_exec) / claude(claude_chat, claude_code_exec) / qwen / minimax.
  - **mock/handoff 백엔드**: 설치 패키지에서는 발견되지 않음 (릴리즈 0.2.0 기준). API 키 없이는 루프를 돌릴 수 없음.
- **envs**: `alfworld`, `docvqa`, `livemathematicianbench`, `officeqa`, `searchqa`, `spreadsheetbench` — **벤치마크 전용**, custom env는 `_template`(env_template.py / loader_template.py)으로 파이썬 어댑터 작성 필요.
- `skillopt-eval --help`: `--skill SKILL`로 쓸 스킬(마크다운 경로) 지정, `--split`/`--backend` 등.

## 5단계: SkillOpt ↔ `.opencode/agents/*.md` 변환 타당성 검토

### 대상 에이전트 파일
- `.opencode/agents/ml-researcher.md` (name/description/tools 프론트매터 → opencode 에이전트 스키마)
- `.opencode/agents/semiconductor-failure-predictor.md` (description/mode/permission 프론트매터)
- `.opencode/agents/prompt-guard.md`, `.opencode/agents/wafer-vision.md`

### 3층 비호환 판정

| 층위 | 기존 파일 | SkillOpt | 판정 |
|------|-----------|----------|------|
| 개념 | 리소스 등록 sub-agent 프론트매터 | **단일 skill `.md` 롤아웃 학습** | ❌ |
| 포맷 | `name/description/tools` (여러 도구, mode) | `skill_content:` 문자열 + EnvAdapter | ❌ |
| 하네스 | opencode | claude(codex/codex_exec)/qwen/minimax 등 — **opencode 없음** | ❌ |

**결론**: `.opencode/agents/*.md`는 오퍼레이터 프로비저닝 문서. SkillOpt는 "벤치마크 문제 → skill 문자열 최적화". 직접 1:1 맵핑 불가. 단, skill이 pure-.md라면 기존 agent 본문을 재사용한 "시드 스킬 수동 작성"은 가능.

## 6단계: 종합 판정 표

| 프레임워크 | 설치 | 오프라인 | 채점(gate) | 하네스 | 이 프로젝트 통합 형태 |
|-----------|------|----------|------------|--------|------------------------|
| Shepherd 0.3.0 (MIT) | ✅ | ✅ (static provider) | 승인/기각/롤백 로직 | claude CLI 존재 | 실행 이벤트 기록·검증 게이트 |
| SkillOpt 0.2.0 (MIT) | ✅ | ❌ (backend 요구) | 벤치마크 전용 | opencode 미지원 | 개념만 차용 (rollout→reflect→gate) |

## 참고 (Claude CLI 검토 요청)

- Shepherd: 설치·오프라인 데모·`run show --json`까지 전부 실측 완료; claude CLI 자동 인증(subscription_login)도 확인됨. 실제 에이전트 full run은 `shepherd task start claude ...`로 1회 명시적으로 실행하는 방식.
- SkillOpt: 벤치마크 태스크가 없으면 루프를 돌릴 수 없음. mock/handoff 백엔드는 0.2.0 패키지에 없어 실 LLM 호출만 가능. 토큰 예산 주의(주간 소진 임박) → 실습은 시뮬레이션으로만.
- 최종 결정근거: 두 패키지 모두 설치·로컬 재현은 완수했지만, "도입"이 아니라 "개념 차용" 의 근거 자료로 사용. 실데이터로 스킬을 트레이닝하는 것은 외부 유출·비용 리스크가 있어 지양한다.