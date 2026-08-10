# 반도체 Failure 예측 — ML 자율 연구 튜토리얼

> 이 튜토리얼은 **이 프로젝트 자체를 교재**로 사용합니다.
> 단순히 코드를 읽는 것이 아니라, opencode와 함께 단계별로 실행하고,
> 개념을 이해하고, 나만의 실험을 만드는 과정입니다.

---

## 이 튜토리얼은 누구를 위한 것인가?

| 학습자 유형 | 설명 | 추천 경로 |
|------------|------|----------|
| **opencode 초보자** | opencode(또는 AI 코딩 도구)를 처음 쓰는 사람 | 모듈 A → E (배우고 싶으면 C도) |
| **ML/AI 초보자** | 머신러닝 개념이 전혀 없는 사람 | A2 → B → C |
| **ML 실무자 (이론만)** | 이론은 아는데 코드 구현이 처음 | B → C (A는 빠르게) |
| **AI 자동화 학습자** | AI로 반복 작업을 자동화하고 싶은 사람 | A1 → A4 → E → C1 |

> 이 4가지가 겹치는 부분이 많습니다. 아래 목록을 보고 원하는 순서를 골라도 됩니다.

---

## 튜토리얼 목록 (33개 레슨)

### 모듈 A : 기초 다지기 (무엇을, 왜 배우나)

| 레슨 | 제목 | 배우는 것 | 시간 |
|------|------|----------|------|
| [A1](A_foundation/01_environment_setup.md) | 환경 세팅 | Python, 패키지, 첫 실행 | 15분 |
| [A2](A_foundation/02_project_walkthrough.md) | 프로젝트 둘러보기 | 디렉터리 구조, 각 모듈 역할 | 15분 |
| [A3](A_foundation/03_data_introduction.md) | 데이터 이해 | 반도체 공정 데이터란? | 20분 |
| [A4](A_foundation/04_opencode_introduction.md) | opencode 시작하기 | AI 코딩 도구와 프로젝트의 관계 | 15분 |

### 모듈 B: ML 파이프라인 (머신러닝의 뼈대)

| 레슨 | 제목 | 배우는 것 | 시간 |
|------|------|----------|------|
| [B1](B_ml_pipeline/05_preprocessing.md) | 전처리 | 결측치, 스케일링 | 15분 |
| [B2](B_ml_pipeline/06_model_training.md) | 모델 학습 | 로지스틱 회귀, train/test | 20분 |
| [B3](B_ml_pipeline/07_evaluation_metrics.md) | 평가 지표 | F1, AUC-ROC, PR-AUC | 20분 |
| [B4](B_ml_pipeline/08_experiment_records.md) | 실험 기록 | SQLite, best_run | 15분 |
| [B5](B_ml_pipeline/09_text_prompt.md) | 텍스트 데이터 | 문장 데이터, 프롬프트 데이터셋 | 20분 |
| [B6](B_ml_pipeline/10_text_classification.md) | 텍스트 분류 | TF-IDF, 텍스트 분류 러너 | 25분 |
| [B7](B_ml_pipeline/26_wafer_images.md) | 웨이퍼 이미지 | 합성 웨이퍼맵, 이미지 데이터 | 20분 |
| [B8](B_ml_pipeline/27_wafer_classification.md) | 이미지 분류 | flatten/PCA, 이미지 분류 러너 | 25분 |

### 모듈 C: 자율 연구 프레임워크 (AI가 실험하는 법)

| 레슨 | 제목 | 배우는 것 | 시간 |
|------|------|----------|------|
| [C1](C_research_framework/11_experiment_runner.md) | 실험 runner | experiment_runner.py, get_config | 20분 |
| [C2](C_research_framework/12_new_task_scaffold.md) | 새 태스크 만들기 | new_task.py, 스캐폴드 | 15분 |
| [C3](C_research_framework/13_wiki_knowledge_base.md) | 위키 지식 베이스 | LLM Wiki 패턴 | 20분 |
| [C4](C_research_framework/14_wiki_lint.md) | 위키 검진 | wiki_lint.py | 10분 |

### 모듈 D: Airflow + 운영 (자동화 인프라)

| 레슨 | 제목 | 배우는 것 | 시간 |
|------|------|----------|------|
| [D1](D_infrastructure/15_airflow_basics.md) | Airflow 기초 | DAG, 태스트, Operator | 15분 |
| [D2](D_infrastructure/16_dag_anatomy.md) | DAG 해부 | ml_research_loop.py | 20분 |
| [D3](D_infrastructure/17_trigger_and_schedule.md) | 트리거/스케줄 | Airflow 실행, make | 15분 |

### 모듈 E — AI 자동화 (에이전트가 실험을 개선)

| 레슨 | 제목 | 배우는 것 | 시간 |
|------|------|----------|------|
| [E1](E_ai_automation/18_opencode_agents.md) | opencode 에이전트 | ml-researcher, 도구 | 15분 |
| [E2](E_ai_automation/19_creating_skills.md) | 스킬 만들기 | imbalanced-data-specialist | 20분 |
| [E3](E_ai_automation/20_autonomous_research_loop.md) | 자율 연구 루프 | DAG + runner + 위키 | 20분 |

### 모듈 F — 종합 프로젝트 (배운 것을 합치다)

| 레슨 | 제목 | 배우는 것 | 시간 |
|------|------|----------|------|
| [F1](F_capstone/21_your_own_task.md) | 나만의 태스크 | 전체 사이클 종합 | 20분 |

### 모듈 G — AI 가드레일 (선택 심화: LLM 안전)

| 레슨 | 제목 | 배우는 것 | 시간 |
|------|------|----------|------|
| [G1](G_ai_safety/22_prompt_guards.md) | 프롬프트 공격 이해 | 인젝션·탈취·조작 등 위협 | 15분 |
| [G2](G_ai_safety/23_building_guardrail.md) | 가드레일 성능 | 오탐/미탐, threshold 튜닝 | 25분 |
| [G3](G_ai_safety/24_agent_integration.md) | 가드레일 에이전트 | predict.py, prompt-guard | 15분 |
| [G4](G_ai_safety/25_own_guardrail.md) | 나만의 가드레일 | 자유 확장 & 마무리 | 20분 |

> 모듈 **F** 완료 = 튜토리얼 수료. 모듈 **G**는 수료 후에 듣는 선택 심화(LLM 안전)입니다.

> **모듈 H가 없는 이유**: 가드레일은 G(22~25)로, 이미지 심화는 I(28~30)로 이어지며
> H라는 모듈은 존재하지 않는다. 웨이퍼 이미지 심화(B7·B8) 파일 번호가 26·27이라
> G(25) 다음에 I(28)이 오는 것처럼 번호가 건너뛰어 보이지만, 결번은 이 파일 번호
> 간격뿐이며 학습 순서상 빈 곳은 없다.

### 모듈 I — 이미지 AI (선택 심화: 웨이퍼 비전)

| 레슨 | 제목 | 배우는 것 | 시간 |
|------|------|----------|------|
| [I1](I_image_ai/28_anomaly_detection.md) | 이상탐지 | 정상/비정상, ROC-AUC | 20분 |
| [I2](I_image_ai/29_feature_engineering.md) | 특징 공학 | PCA/그래디언트/방사 프로파일 | 25분 |
| [I3](I_image_ai/30_own_vision_task.md) | 나만의 비전 태스크 | 분류+이상탐지 자유 확장 | 20분 |

> **I** 모듈은 **B7/B8**(웨이퍼 이미지·분류)을 먼저 들은 뒤 추천합니다. 이미지 AI에
> 관심이 있다면 B7/B8 → I1 → I2 → I3 순서로 진행하세요.

### 모듈 J — 에이전트 발전 심화 (선택 심화: 관측·검증·적용)

| 레슨 | 제목 | 배우는 것 | 시간 |
|------|------|----------|------|
| [J1](J_agent_evolution/31_execution_events.md) | 실행 이벤트 기록 | 실패도 기록하는 이벤트 테이블 | 40분 |
| [J2](J_agent_evolution/32_validation_gate.md) | 검증 게이트 | 점수만으로 판단하지 않는 법 | 40분 |
| [J3](J_agent_evolution/33_propose_validate_apply.md) | 제안→검증→적용 | 변경 근거(`_rationale`)와 검증 루프 | 50분 |

> **J** 모듈은 F(수료) + C/D/E 이수 후 추천하는 **최상위 선택 심화**입니다.
> Shepherd/SkillOpt 같은 에이전트 프레임워크의 개념을 이 프로젝트 구조에 적용해
> "에이전트를 발전시키는 법"을 다룹니다. 사전 인프라(`events` 테이블, `train_*` 지표,
> `src/validation_gate.py`)가 이미 프로젝트에 구현되어 있어 그 위에서 실습합니다.

---

## 시작하기 전 준비물

- Python **3.10 이상** 설치
- 터미널(커맨드라인) 기본 사용법 (폴더 이동, 명령 실행)
- (권장) [opencode](https://opencode.ai) 설치
- (권장) 이 프로젝트를 clone한 상태

```bash
git clone https://github.com/Taekyoon/opencode_ml_practice.git
cd opencode_ml_practice
```

---

## 실습 모델

이 튜토리얼은 opencode의 다음 모델로 실습·검증했습니다.

| 항목 | 값 |
|------|-----|
| 모델 | **`opencode/deepseek-v4-flash-free`** |
| 모드 | opencode 기본 대화 모드 (main 에이전트) |
| 비고 | 다른 모델로 실습해도 됩니다. 단, 레슨 예시와 결과 수치가 미세하게 다를 수 있습니다. |

> 모델 변경 방법: opencode 세션에서 `/models` 명령을 쓰거나, 프로젝트 `opencode.json`의 `model` 필드로 고정할 수 있습니다.

---

## 학습 방식 (이 튜토리얼의 진행법)

각 레슨은 opencode와 함께 진행됩니다.

**권장 진행 (opencode + 사용자):**

1. 터미널에서 이 프로젝트 폴더를 연다
2. `opencode` 실행 후 다음 중 하나를 입력한다:
   - `나는 초보자인데 튜토리얼부터 시작하고 싶어`
   - `배우고 싶어, 어디부터 시작하지?`
3. opencode가 학습 유형을 물어보면 골라준다
4. 하나씩 레슨을 진행하면서 모르는 것은 그 자리에서 opencode에게 묻는다
5. 각 레슨의 작업이 끝나면 `research/wiki/learning_progress.md`에 기록된다

**혼자서 진행하는 경우:**

1. `docs/tutorial/README.md`에서 골라준 경로를 확인
2. 각 레슨을 읽고, 해당 파일을 먼저 연다
3. 터미널에서 명령을 실행하고 결과를 확인한다
4. 레슨 끝의 "확인 문제"를 풀어본다

> **모든 레슨에는 "opencode에게 물어보세요" 박스가 있습니다.**
> 학습 중 궁금한 점이 생기면 그대로 복사해서 물어보세요.

---

## 학습 진행 기록

학습 중 어느 레슨을 했는지 여부가 자동으로 `research/wiki/learning_progress.md`에 기록됩니다.

- 한 레슨을 끝내면 `opencode`에게 "레슨 N 완료로 기록해줘"라고 말하세요
- 다음 세션이 열려도 진행 위치를 그대로 이어갈 수 있습니다

---

## 마무리하며

이 튜토리얼의 목표는 "코드를 복사하는 것"이 아니라 **"구조를 이해하고, 직접 변형할 수 있게 되는 것"**입니다.

마지막 레슨(F1)에서 여러분이 직접 만든 태스크가 **연구 루프에 등록되어 실험을 실행**하는 모습을 보는 것으로 튜토리얼이 끝납니다. 그 다음부터는 여러분의 프로젝트입니다.

---

**보충 자료**: 에이전트 자동화의 관점(하네스·루프·그래프 공학)을 정리한
[엔지니어링 개념 문서](../design/ENGINEERING_CONCEPTS.md)를 읽으면 이 튜토리얼의
전체 구조(D2·E3·J1~J3)가 하나의 프레임워크로 묶입니다.