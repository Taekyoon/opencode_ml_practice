# E1. opencode 에이전트 — 프로젝트의 AI 연구원

## 학습 목표
- 에이전트(agent)가 무엇인지 안다
- `.opencode/agents/`의 구조(프런트매터 + 본문)를 이해한다
- 이 프로젝트의 `ml-researcher` 에이전트가 무엇을 하는지 안다

## 배경 지식

### 에이전트란?
에이전트는 opencode에게 주는 **부전공(전문화)** 정의다.
"이 프로젝트에 대한 지시만 담은 역할 카드"라고 할 수 있다.

- **어떤 도구**(read, edit, bash...)를 쓸 수 있는지
- **어떤 규칙**을 지킬지
- **어떤 워크플로우**(단계 순서)를 따를지

이 프로젝트의 `.opencode/agents/`에 4개 에이전트가 있다:
- `ml-researcher.md` — 자율 ML 연구원 (DAG와 협업). 사용자가 보고 위키를 갱신
- `semiconductor-failure-predictor.md` — 분류 모델링 엔지니어 (subagent)
- `prompt-guard.md` — LLM 프롬프트 가드레일 (모듈 G에서 실습)
- `wafer-vision.md` — 웨이퍼맵 비전 (모듈 I에서 실습)

### 에이전트 파일 구조 (frontmatter + body)
frontmatter는 **두 계열**이 섞여 있다. 먼저 `semiconductor-failure-predictor.md` 예:

```yaml
---
description: Builds failure-classification models ...
mode: subagent            # subagent = 독립 실행 용, primary = 메인과 공존
permission:
  read: allow
  edit: allow
  bash: allow
  glob: allow
  grep: allow
  skill: allow
---
```

반면 `ml-researcher.md`·`prompt-guard.md`·`wafer-vision.md`는 `tools:` 목록으로 쓴다:

```yaml
---
name: ml-researcher
description: 자율 ML 연구 에이전트 ...
tools:
  - read
  - edit
  - write
  - bash
  - glob
  - grep
---
```

| frontmatter 항목 | 의미 |
|-----------------|------|
| `description` | opencode가 어떤 상황에서 이 에이전트를 부를지 판단할 설명 |
| `mode` | `subagent`(용도별 분리 실행) / `primary`(메인과 공존) — 예시 파일에만 있음 |
| `permission` | read/edit/bash/skill 등 도구 허용 범위 (`tools:` 목록과 같은 의미) |
| 본문(마크다운) | 역할, 임무, 규칙, 실행 순서 |

> `tools:`(허용할 도구 목록)와 `permission:`(도구별 allow/deny 맵)은 표현만 다를 뿐
> 같은 일을 한다. 새 에이전트 작성 시 프로젝트 기존 파일의 스타일을 따른다.

> **핵심 원칙**: 에이전트는 욕심내지 않는다. "중요한 것 하나씩" 지킵시다.
> 예를 들어 ml-researcher는 research/만 만지고, src/는 신중히, program.md는 수정하지 않는다.

## 따라하기

### 1단계: 네 에이전트 비교
```bash
cat .opencode/agents/ml-researcher.md
cat .opencode/agents/semiconductor-failure-predictor.md
cat .opencode/agents/prompt-guard.md
cat .opencode/agents/wafer-vision.md
```
앞 두 개(`tools:` vs `permission:` frontmatter)와, 가드레일/비전 에이전트가 쓰는
도구 목록을 비교해본다.

### 2단계: 실제로 부르기
```
@semiconductor-failure-predictor 실습해줘: src/preprocessing.py에서 실데를 정리하고 싶어.
```
(에이전트를 부르면 "subagent"로 실행되며 자기 역할대로 응답한다)

### 3단계: ml-researcher에게 위키 요약 요청
```
@ml-researcher 위키를 검토해서 지금 가장 할 만한 실험이 뭔지 알려줘.
```
연구원 에이전트가 위키를 뒤져 가설을 제시하면 성공.

### 4단계: (참고) 에이전트 파일 만들기 규칙
새 에이전트가 필요하면 본문을 참고해 `.opencode/agents/<이름>.md`를 만들거나
opencode에게 "에이전트를 만들어줘"라고 지시한다. 이 레슨은 읽기 수준이므로
직접 만드는 실습은 E3에서 한다.

## 이해 확인

1. `description`이 왜 중요한가? (에이전트 선택의 기준)
2. `subagent`(또는 `primary`)와 일반 대화의 차이는?
3. 에이전트를 "너무 많은 걸 하는 종합 에이전트"로 만들면 왜 안 좋은가?

## opencode에게 물어보세요

```
.opencode/agents/ 폴더의 에이전트들을 읽고, 각각 언제 누가 부르면 되는지
비교 정리해줘. 그리고 내가 우리 프로젝트에 맞는 에이전트를 하나 더 만들고 싶으면
어떤 걸 만들면 좋을지 추천해줘.
```

## 다음 레슨
[E2. 스킬 만들기](19_creating_skills.md) — 반복 문제 해결을 위한 전문 스킬을 만든다.