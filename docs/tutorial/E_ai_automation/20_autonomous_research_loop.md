# E3. 자율 연구 루프 — DAG + runner + 위키 + 에이전트

## 학습 목표
- 자율 연구 루프의 전체 그림을 이해한다
- 사용자가 자연어로 "가설"을 주면 에이전트→DAG→runner→wiki로 이어지는 흐름을 안다
- 성공/실패 표시를 해석한다

## 배경 지식

### 전체 그림
```
사용자 (자연어 가설)
   │
   ▼
ml-researcher 에이전트
   │ 1) inbox 데이터 등록 / 데이터 확인
   │ 2) experiment_runner.py의 get_config() 또는 로직 수정
   ▼
Airflow DAG (ml_research_loop)
   │  failure_prediction_prepare → run → eval → report
   │  (register된 task 마다 반복)
   ▼
research.db (숫자)  +  research/wiki (지식)  +  reports/ (리포트)
   │
   ▼
에이전트가 사용자에게 "가설 채택/기각" 보고
```

**핵심**: 사람이 "이렇게 바꿔보자"를 말로 하면, 에이전트가 설정을 바꾸고,
DAG가 실행하고, 결과가 DB/위키에 남고, 에이전트가 다시 보고한다.
이것이 "자율 연구"다.

## 따라하기

### 1단계: 흐름 전체를 먼저 그려보기
위 배경의 그림을 보고, 이 프로젝트의 각 파일이 어디에 해당하는지 짚어본다:
- `research/tasks_registry.py` → DAG가 "어떤 task를 돌릴지" (레지스트리)
- `airflow/dags/ml_research_loop.py` → 실행 오케스트레이션
- `research/<task>/experiment_runner.py` → 실제 학습 코드
- `research/wiki/` → 발견 기록

### 2단계: 가설을 에이전트에게 주기 (실습)
자연어로 가설을 준다:
```
@ml-researcher
가설 : failure_prediction 태스크에서 모델을 gradient_boosting 으로 바꾸면
score(F1 × PR-AUC)가 로지스틱보다 높아질 것 같아."
실행해서 비교해줘.
```
에이전트는 `experiment_runner.py`의 `get_config()`를 바꾸고 DAG를 트리거하고
결과를 보고한다.

### 3단계: 결과 확인 (DB + 위키)
```bash
make research-log        # research.db 요약 (최고 score)
cd research/failure_prediction/results && ls && cd -
cat research/wiki/tasks/failure_prediction.md   # 위키에 자동 기록
```
새 run이 `위키 "현재 최고 결과" 표`에 자동 추가되었는지 확인한다.

### 4단계: 위키에 accumulated 발견 요약
기존 `tasks/failure_prediction.md`에 이번 시도의 관찰이 반영됐는지 확인한다.
에이전트/관리자가 손으로 위키를 업데이트할 때는 Ingest 순서(AGENTS.md §9.2)를 따른다.

## 이해 확인

1. 자율 연구 루프에서 "실제 ML 학습"은 어느 파일이 수행하나?
2. DAG의 4단계 화면(D2)이 이 루프에 어떻게 맞아 떨어지는가
3. 가설이 좋은도/나쁘든 왜 DB+위키 양쪽에 기록되는가?

## opencode에게 물어보세요
```
방금 우리가 수행한 루프의 전체 여정을 단계별로 요약해줘.
가설 → runner 수정 → DAG → DB → 위키 → 보고까지 도표로 설명하고,
실패했을 때 어느 단계에서 어떻게 되었을 지 알려줘.
```

## 다음 레슨
[F1. 나만의 태스크](../F_capstone/21_your_own_task.md) — 배운 모든 것을 종합해 나만의 태스크를 만든다.