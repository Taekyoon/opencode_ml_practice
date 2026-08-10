# F1. 나만의 태스크 — 전체 사이클 종합

## 학습 목표
- 배운 전 과정을 하나의 태스크로 종합한다
- 스캐폴드 → runner → DAG → 위키의 전체 흐름을 직접 수행한다
- 튜토리얼 수료 후 어떤 능력이 생겼는지 정리한다

## 과제

지금까지 배운 것을 조합해서 **나만의 태스크**를 하나 만들어 DAG에서 실행까지 해보자.

### 시나리오
A1에서 만든 `data/synthetic_data.csv`(현재 target=failure)를 **inbox로 등록**하여
**새 목표 변수를 하나 만들어** 새 태스크를 등록한다. 예를 들면:
- 파생 변수 `stress = temperature * pressure`(불량과 관련 있어 보임)를 계산 후
- "이 파생변수로 failure를 예측하면 성능이 오르는가?"라는 가설 검증

> (본 실습은 가상이므로, 실제로 연구 방향이 의미있는지보다 "전체 사이클을
> 안내대로 한 번 돌려보는 것"이 목표다.)

## 따라하기

### 1단계: 흐름 계획
아래를 미리 정리한다:
| 항목 | 값 |
|------|-----|
| task_id | (예: `failure_stress`) |
| dataset | A1의 `synthetic_data.csv`를 inbox로 등록 |
| target | `failure` (기존) 또는 만들 컬럼 |
| score | 분류 = F1 × PR-AUC |

### 2단계: 스캐폴드로 태스크 생성
inbox에 데이터를 넣고 등록하면서 태스크를 만든다 (C2에서 배운 `--inbox` 흐름):
```bash
mkdir -p research/inbox
cp data/synthetic_data.csv research/inbox/synthetic_data.csv
python scripts/new_task.py my_stress_task --inbox synthetic_data.csv --target failure --note "튜토리얼 종합 과제"
```
`dataset : my_stress_task`(등록본), `kind: classification` 판정을 확인한다.
생성물 `research/my_stress_task/` 확인.

### 3단계: runner에 파생 변수 추가 (에이전트에게 부탁)
```
@ml-researcher
새 태스크 my_stress_task 의 experiment_runner.py 에서
X에 파생변수(예: temperature * pressure)를 추가하고 실행해줘.
```
(혼자 하신다면 `research/my_stress_task/experiment_runner.py`의
`run_experiment()` 안에서 `X["stress"] = X["pressure"] * X["temperature"]` 추가 후
`python research/my_stress_task/experiment_runner.py`)

### 4단계: DAG에 태스크 포함 확인
```bash
AIRFLOW_HOME=$(pwd)/airflow airflow dags show ml_research_loop    # my_stress_task_* 4개 task 표시
```
스케줄러가 tasks_registry를 재파싱하면 자동 반영된다.

### 5단계: 실행 + 기록
```bash
make research-task TASK=my_stress_task
make research-log        # 내 태스크의 최고 score 확인
research/wiki/tasks/my_stress_task.md   # 자동 생성 확인
```
없으면 수동으로 페이지 생성 (AGENTS.md §9.2 참고).

### 6단계: (기본기 확인) 위키 린트 통과 유지
```bash
make wiki-lint
```
내가 만든 페이지가 index.md에 없어 1번 경고(미등록)가 뜰 수 있다.
`research/wiki/index.md`에 추가해서 0 문제로 만든다.

## 축하합니다 🎉

**튜토리얼을 마쳤다.** 이제 여러분은:
- ✅ 파이썬/ML 기본 구조 (데이터 → 전처리 → 학습 → 평가)
- ✅ 실험 기록 DB + 위키 지식 관리
- ✅ 스캐폴드로 새 연구 태스크 생성
- ✅ Airflow로 자동 실행
- ✅ 에이전트·스킬로 AI 자동화
- ✅ 사용자 언어·설정 하나로 "자율 연구 루프"를 가동

여기서 멈추지 말자. 아이디어가 있으면 자연어로:
```
@ml-researcher
가설: ... 
```
DAG가 돌고, 위키에 기록되고, 내일 열어보면 리포트가 있다.
**이 프로젝트는 여러분의 것이 된다.**

튜토리얼을 수료했다면 이제 선택 심화 모듈이 기다린다:
- **G. AI 가드레일** — LLM 서비스에 안전장치(가드레일)를 붙이는 법
- **I. 이미지 AI** — 웨이퍼맵 이미지 분류·이상탐지
- **J. 에이전트 발전 심화** — 실행 이벤트·검증 게이트·제안→검증→적용 루프 (가장 높은 심화)

## 마무리 확인 문제

1. 새 태스크를 "분류"로 판정받으려면 target 컬럼 값은 몇 종류여야 하는가?
2. DAG에 새 태스크가 자동으로 나타나게 하는 메커니즘은?
3. wiki-lint가 "미등록"을 잡으면 뭐를 해주나?

## 튜토리얼 피드백

이 튜토리얼이 도움이 됐으면 프로젝트를 개선하자 —
각 레슨 헤더의 `## opencode에게 물어보세요` 질문을 바꾸거나,
새 레슨을 만들고 싶으면 그냥 추가한다.
마지막으로: 방금 만든 태스크를 지울지 유지할지는 여러분의 결정이다.

---

### (참고) 전체 모듈 복습 목차
- [모듈 A](../A_foundation/01_environment_setup.md)
- [모듈 B](../B_ml_pipeline/05_preprocessing.md)
- [모듈 C](../C_research_framework/11_experiment_runner.md)
- [모듈 D](../D_infrastructure/15_airflow_basics.md)
- [모듈 E](../E_ai_automation/18_opencode_agents.md)
- [모듈 F (수료)](21_your_own_task.md)
- [모듈 G (선택 심화)](../G_ai_safety/22_prompt_guards.md)
- [모듈 I (선택 심화)](../I_image_ai/28_anomaly_detection.md)
- [모듈 J (선택 심화)](../J_agent_evolution/31_execution_events.md)
- [처음으로](../README.md)