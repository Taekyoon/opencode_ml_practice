# E2. 스킬 만들기 — 문제 해결 지식을 패키지로 만들기

## 학습 목표
- 스킬(skill)이 에이전트와 어떻게 다른지 안다
- `SKILL.md`의 구조를 이해한다
- **직접 스킬을 만들어 보는 과정을 완주한다**

## 배경 지식

### 에이전트 vs 스킬
| | 에이전트 | 스킬 |
|---|---|---|
| 관점 | "누가" 일하나 (역할) | "무엇을 할 줄 아나" (기능) |
| 형태 | `.opencode/agents/*.md` | `.opencode/skills/<이름>/SKILL.md` |
| 예 | ml-researcher(연구원 역할) | imbalanced-data-specialist(불균형 해결 기능) |

정리하자면 **에이전트가 "불균형 데이터 문제가 있다"고 판단하면 스킬을 호출해 해결**한다.
`semiconductor-failure-predictor.md` 에이전트가 `imbalanced-data-specialist` 스킬을 어떻게 부르는지 확인해보자.

### 스킬의 구조
하나의 스킬은 폴더로 구성된다:

```
.opencode/skills/<skill-name>/
├── SKILL.md                     # 설명서 (핵심)
└── (선택) src/, tests/ 등      # 실제 코드
```

`SKILL.md`에는:
- **frontmatter**: name, description(언제 쓰는지), metadata
- **본문**: 사용 예시 코드, API, 규칙, 주의사항

> 스킬의 description이 중요하다. opencode가 "지금 이 스킬이 필요한가?"를
> 이 설명만 보고 판단한다.

## 따라하기 — 자신만의 스킬 만들기

이번 실습은 "python 스크립트로 데이터 살펴보는" 작은 스킬을 만들어
스킬의 수명(생성 → 사용 → 검증 → 삭제)을 온전히 경험한다.

### 1단계: 기존 스킬 구조 참고
```bash
ls .opencode/skills/imbalanced-data-specialist/
cat .opencode/skills/imbalanced-data-specialist/SKILL.md
```

### 2단계: 새 스킬 폴더 만들기
```bash
mkdir -p .opencode/skills/eda-snapshot
```

### 3단계: SKILL.md 작성
`.opencode/skills/eda-snapshot/SKILL.md`를 아래 내용으로 작성한다:

```markdown
---
name: eda-snapshot
description: Quickly summarize a tabular dataset (shape, missing, distribution) before modeling
---

## What I do
Prints a compact summary table for a pandas DataFrame:
1. rows / columns
2. dtypes (% per column type)
3. missing values per column
4. target distribution (if provided)

## Usage
```python
import pandas as pd
df = pd.read_csv("data/synthetic_data.csv")
print(df.shape)
print(df.isna().sum())
print(df["failure"].value_counts(normalize=True))
```

## Notes for the agent
- Run before any modeling to catch data issues early.
```

> **참고**: SKILL.md 는 "설명서"다. 코드(예: 실제 함수)를 반드시 넣을 필요는
> 없고, 이 파일을 읽은 에이전트가 본문대로 실전 코드를 작성/실행한다.

### 4단계: 활용(동작) 코드 추가 (선택)
간단한 함수를 만들어 `<skill>/src/`에 두어도 된다. 지금은 설명서만으로 충분히 작동한다.

### 5단계: 스킬이 발동되는지 확인
opencode에게 부탁한다:
```
data/synthetic_data.csv 를 방금 만든 eda-snapshot 스킬로 요약해줘.
```
스킬이 "호출"되어 요약을 돌려주면 성공.

### 6단계: (마무리) 삭제
실습용 스킬은 지운다 (진짜 프로젝트 스킬이 어지럽혀지지 않게):
```bash
rm -rf .opencode/skills/eda-snapshot
```

> **실무 팁**: 스킬은 작게, 이름을 동작으로 짓는다.
> "imbalanced-data-specialist"는 행동이 선명하다. "data-helper" 같은 건 너무 넓어서
> 에이전트가 언제 써야 할지 판단하기 어렵다.

## 이해 확인

1. 에이전트와 스킬의 역할 차이를 한 줄로 설명
2. SKILL.md의 `description` 프런트매터가 왜 중요한가?
3. 스킬 이름을 잘 짓는 예/나쁜 예를 하나씩

## opencode에게 물어보세요
```
.opencode/skills/imbalanced-data-specialist/SKILL.md 를 읽고
이 스킬의 동작 원리(불균형 처리·임계값 최적화)를 설명해줘.
그리고 스킬 하나를 직접 만들고 싶은데 어떤 프로세스를 따라가면 되는지 알려줘.
```

## 다음 레슨
[E3. 자율 연구 루프](18_autonomous_research_loop.md) — DAG+runner+위키+에이전트가 결합한다.