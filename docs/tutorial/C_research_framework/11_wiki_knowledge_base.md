# C3. 위키 지식 베이스 — 실험 발견을 누적하는 곳

## 학습 목표
- 위키(`research/wiki/`)가 왜 필요한지 안다
- 위키의 문서 구조와 역할을 이해한다
- 실험 후 위키를 갱신하는 규칙(Ingest)을 따라 한다

## 배경 지식

### 문제: 결과 숫자만으로는 부족하다
`research.db`에는 score 같은 숫자가 기록된다. 하지만 "왜 점수가 올랐는지"
"어느 데이터셋에서 안 통했다"는 **구조화되지 않은 지식**은 DB에 담기기 어렵다.

**위키 패턴**: 사람 대신 **LLM이 유지하는 마크다운 지식 기반**을 갖는 것.
이 프로젝트의 `research/wiki/`가 그 역할이다.

### 위키 구조

```
research/wiki/
├── index.md                     # 모든 페이지 목록 (지향 목차)
├── log.md                       # 연대기순 기록 (append-only)
├── overview.md                  # 대시보드 — 세션 시작 시 먼저 읽는다
├── tasks/<task_id>.md           # 태스크별 누적 발견
├── techniques/                  # 기법별 종합 (smote, scaling, ...)
├── datasets/                    # 데이터셋 분포/주의사항
└── synthesis/lessons_learned.md # 교차 태스크 교훈 + 다음 방향
```

### Ingest 규칙 (새 실험 후 반드시)
AGENTS.md §9.2의 순서:
1. `research.db`에서 최신 run 확인
2. `tasks/<task_id>.md` 갱신 — 최고 결과 테이블에 추가, 발견 1줄
3. 기법을 썼다면 `techniques/<기법>.md`에도 맥락과 함께
4. `log.md`에 append: `## [날짜] ingest | task | run | score`
5. `index.md` 갱신

## 따라하기

### 1단계: 위키 둘러보기
```bash
ls -R research/wiki/
cat research/wiki/overview.md
cat research/wiki/tasks/failure_prediction.md
```

### 2단계: "현재 최고 결과" 테이블 읽기
`tasks/failure_prediction.md` 최상단 테이블을 확인한다.
여기에는 가장 최근 실험의 score가 최상단에 유지된다.

### 3단계: log 형식 확인
```bash
cat research/wiki/log.md
```

### 4단계: 위키를 유지하는 규칙 이해
이 프로젝트의 AGENTS.md §9.2를 읽고, 실험 후 어떤 내용을 위키에 남기는지 확인한다.
opencode에게 "위키 갱신 규칙"을 물어보고, 실제 갱신이 어떻게 이루어지는지 살펴본다.

> 이 레슨의 목적은 "위키란 무엇인가"를 이해하는 것이다. 실제로 에이전트가
> 페이지를 만들고 갱신하는 실습은 E3에서 한다.

## 이해 확인

1. `research.db`(숫자)와 `research/wiki/`(지식)은 무엇이 다른가?
2. `log.md`가 append-only인 이유는 무엇인가?
3. 새 실험 후 위키를 갱신하는 순서 5단계는?

## opencode에게 물어보세요
```
research/wiki 의 overview.md와 tasks/failure_prediction.md를 읽고,
지금까지 이 태스크에 알려진 것을 3줄로 요약해줘. 그리고 다음 실험으로 무엇을
시도해야 할지도 알려줘.
```

## 다음 레슨
[C4. 위키 검진](12_wiki_lint.md) — 위키가 상식적으로 유지되는지 자동 검사한다.