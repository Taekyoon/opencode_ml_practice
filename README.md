# opencode_ml_practice — OpenCode ML 자율 연구 튜토리얼

> **OpenCode를 배우기 위해 만든 튜토리얼 저장소입니다.**
> 반도체 failure 예측은 학습용 실습 주제로 삼았고, 저장소의 목적은
> "AI 에이전트와 함께 ML 파이프라인을 만들고 자동화하는 법"을 익히는 것입니다.

## 이 저장소가 알려주는 것

- **OpenCode** (터미널 AI 코딩 에이전트) 사용법 — 대화로 코드 작성/실행/수정
- **ML 파이프라인 기본기** — 데이터 → 전처리 → 모델 → 평가의 전체 흐름
- **자율 ML 연구 루프** — 에이전트 + Airflow DAG + 실험 기록 DB + LLM Wiki까지
- **스킬/에이전트 제작** — `.opencode/`에서 나만의 전문가를 만드는 법
- **에이전트 발전 심화 (모듈 J)** — 이벤트 기록·검증 게이트·제안→검증→적용 루프로 "에이전트를 발전시키는 법"

## 🚀 시작하기 (튜토리얼으로)

```bash
# 1. clone 후
git clone https://github.com/Taekyoon/opencode_ml_practice.git
cd opencode_ml_practice

# 2. Python 3.10+ + 의존 설치
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. 데이터 생성 (튜토리얼 예제용 가상 데이터)
python -m src.data_generation

# 4. opencode 실행 → 튜토리얼 모드 시작
opencode
#    "튜토리얼 시작해줘" 라고 입력하면 학습자 유형별 가이드가 진행됩니다.
```

## 🤖 실습(튜토리얼) 검증 모델

이 튜토리얼의 레슨·명령·결과는 다음 모델로 실습하고 검증했습니다.

| 항목 | 값 |
|------|-----|
| 모델 | **`opencode/deepseek-v4-flash-free`** |
| 모드 | 대화형 (main, 기본 에이전트) |
| 참고 | 실행 중 다른 모델로 바꾸면(예: 채팅 모델 변경) 결과 수치·해석이 조금 달라질 수 있습니다. 재현 실습에는 위 모델 권장 |

> 모델 전환: opencode 세션 내에서 `/models` 로 변경하거나 `opencode.json`의 `"model"` 필드로 기본값을 고정할 수 있습니다.

튜토리얼 상세: [docs/tutorial/README.md](docs/tutorial/README.md) · A~J 모듈 33개 레슨

| 모듈 | 내용 |
|------|------|
| **A. 기초 다지기** | 환경 세팅, 프로젝트 구조, 데이터 이해, OpenCode 시작 |
| **B. ML 파이프라인** | 전처리 → 모델 학습 → 평가 지표 → 실험 기록 → 텍스트 데이터/분류 → 웨이퍼 이미지/분류 |
| **C. 자율 연구** | experiment_runner, 태스크 스캐폴드, LLM Wiki, 위키 린트 |
| **D. Airflow** | DAG 개념, ml_research_loop 해부, 트리거/스케줄 |
| **E. AI 자동화** | 에이전트/스킬 만들기, 자율 연구 루프 종합 |
| **F. 종합 프로젝트** | 나만의 태스크로 전체 사이클 직접 실행 (수료) |
| **G. AI 가드레일 (선택 심화)** | 프롬프트 공격 탐지, 가드레일 모델·에이전트, 자유 확장 |
| **I. 이미지 AI (선택 심화)** | 웨이퍼 이미지 이상탐지, 특징 공학, 나만의 비전 태스크 |
| **J. 에이전트 발전 심화 (선택 심화)** | 실행 이벤트 기록, 검증 게이트, 제안→검증→적용 루프 — Shepherd/SkillOpt 개념 차용 |

## 📁 프로젝트 구조

```
opencode_ml_practice/
├── src/                    # 재사용 코어 모듈 (데이터/전처리/모델/평가/저장)
├── src/validation_gate.py  # 실험 결과 검증 게이트 (GateResult + 규칙, 모듈 J)
├── src/research_store.py   # 실험 기록 / 최고 점수 / 이벤트(events) API
├── research/               # 연구 작업 공간 (tasks/, wiki/, runner, research.db)
│   ├── tasks_registry.py   # 태스크 레지스트리 (빌트인 + tasks_extra.json)
│   ├── failure_prediction/ # 실습용 분류 태스크 (반도체 failure)
│   ├── quality_regression/ # 실습용 회귀 태스크
│   ├── prompt_guard/       # 프롬프트 공격 탐지 태스크 (G 모듈)
│   ├── wafer_vision/       # 웨이퍼맵 결함 분류 태스크 (B8/I 모듈)
│   └── wiki/               # LLM 위키 지식 베이스 (index/log/overview/tasks/...)
├── airflow/dags/           # ml_research_loop 자율 연구 DAG
├── scripts/                # new_task 스캐폴드 CLI, wiki_lint 검진
├── docs/tutorial/          # 대화형 튜토리얼 본체 (A~J 모듈)
├── .opencode/              # OpenCode 에이전트 / 스킬 정의
├── archive/                # 보존된 레거시 코드/문서 (아래 "보존 아카이브" 참조)
├── AGENTS.md               # AI 에이전트 작업 가이드 (필수)
└── Makefile                # make init / scheduler / research / wiki-lint 등
```

## ⚙️ 자율 연구 프레임워크 사용법

튜토리얼 수료 후에는 아래 프레임워크로 자유롭게 연구합니다:

```bash
make research-task TASK=failure_prediction   # 특정 태스크 즉시 실행 (Airflow)
make research                                # 등록된 전체 태스크 실행
python scripts/new_task.py <task> --dataset <ds> --target <col>  # 새 태스크 스캐폴드
make wiki-lint                               # 위키 지식 베이스 건강 검진
```

자세한 규칙/워크플로: [AGENTS.md](AGENTS.md)

## 🧪 실습 데이터 (학습용 예제)

가상 반도체 공정 데이터 `data/synthetic_data.csv` (5,000행)

| 항목 | 값 |
|------|------|
| 불량률 | 약 16.7% (불량 837 / 합격 4163) |
| 베이스라인 | 로지스틱 회귀 + StandardScaler |
| Accuracy / Precision | 95.1% / 89.9% |
| Recall / F1 | 79.6% / 84.4% |
| AUC-ROC | 0.986 |

> 실제 산업 데이터가 아닌 **학습용 합성 데이터**입니다.
> 실습 구조는 실제 반도체 품질 분석과 동일한 파이프라인(특성 공학·불균형 대응 가능)을 따릅니다.

## 🗄️ 보존 아카이브 (archive/)

한때 사용하던 초기 실험 코드와 기록 문서를 삭제하지 않고 `archive/`에 보존한다.
읽기 전용이며, 새 기능은 여기에 넣지 않는다. 운영 표준은 `research/<task_id>/`
태스크 프레임워크와 `airflow/dags/ml_research_loop.py` 자율 연구 루프이다.

| 경로 | 내용 | 대체 |
|------|------|------|
| `archive/code/experiments/` | 초기 실험 스위트 (`run_baseline/run_imbalance/run_extreme/run_scalability`) | `research/<task>/experiment_runner.py` |
| `archive/code/semiconductor_experiments_dag.py` | 4개 실험을 병렬 실행하던 Airflow DAG | `airflow/dags/ml_research_loop.py` |
| `archive/docs/` | 초기 대화 로그, 전략, 스킬 계획, 회고록 | `research/wiki/` (지식 표준) |

- 실행 산출물(`archive/code/experiments/results/`, `summary.json`)은 보존만 하며 git에는 추적하지 않는다.
- `make archive` 로 보존 파일 목록 확인, 상세는 [archive/README.md](archive/README.md)

## 📚 참고

- **OpenCode** 도움말: [https://opencode.ai](https://opencode.ai)
- 튜토리얼 학습자 유형: OpenCode 초보 / ML 초보 / ML 실무자 / AI 자동화 학습자
- 진행 기록: `research/wiki/learning_progress.md` (OpenCode가 자동 갱신)

## 라이선스

이 프로젝트는 MIT 라이선스로 배포됩니다. 자세한 내용은 [LICENSE](LICENSE)를 참조하세요.

## 인용 및 레퍼런스

이 프로젝트는 다음 연구/도구에서 데이터와 개념을 사용했습니다.

### 데이터셋

- **WM-811K Wafer Map Dataset**
  Wu, M.-J., Jang, J.-S. R., & Chen, J.-L. (2015). "Wafer Map Failure Pattern Recognition and Similarity Ranking for Large-Scale Data Sets." *IEEE Transactions on Semiconductor Manufacturing*, 28(1), 1-12.
  DOI: [10.1109/TSM.2014.2364237](https://doi.org/10.1109/TSM.2014.2364237)
  출처: [Kaggle](https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map) | [MIR Lab](http://mirlab.org/dataSet/public/)
  라이선스: CC0 (퍼블릭 도메인)

### 개념 차용

- **Shepherd** (MIT) — 이벤트 기록, changeset 컨셉
- **SkillOpt** (MIT) — 게이트/검증(GateResult), rollout-reflect-gate 루프 컨셉
- **Karpathy LLM Wiki** — 위키 lint 컨셉의 영감

### 도구

- [opencode](https://opencode.ai) — 에이전트 런타임 하네스
- [Apache Airflow](https://airflow.apache.org) — DAG 오케스트레이션
- [scikit-learn](https://scikit-learn.org) — ML 파이프라인
- [imbalanced-learn](https://imbalanced-learn.org) — 불균형 처리