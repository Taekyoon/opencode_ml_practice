# A2. 프로젝트 둘러보기 — 구조와 흐름 이해하기

## 학습 목표
- 이 프로젝트의 전체 디렉터리 구조를 이해한다
- 각 디렉터리가 담당하는 역할을 구분한다
- "데이터 → 학습 → 기록"의 흐름을 머릿속에 그린다

## 프로젝트 구조

```
opencode_ml_practice/
├── README.md                     # 프로젝트 소개
├── Makefile                      # 운영 명령 모음 (make로 실행)
├── AGENTS.md                     # AI 에이전트용 작업 가이드
├── requirements.txt              # 패키지 목록
├── data/                         # 원본/생성 데이터 (CSV)
├── scripts/                      # 개발 보조 도구
│   └── new_task.py               #   새 연구 태스크 자동 생성
├── src/                          # 재사용 코어 모듈
│   ├── data_generation.py        #   가상 공정 데이터 생성
│   ├── data_manager.py           #   dataset 등록/로드
│   ├── preprocessing.py          #   결측치/스케일링
│   ├── model.py                  #   모델 정의
│   ├── evaluation.py             #   평가 지표
│   ├── text_processing.py        #   텍스트 토큰화/TF-IDF (B5/B6)
│   ├── image_processing.py       #   웨이퍼 특징 추출 (B8/I)
│   ├── validation_gate.py        #   실험 검증 게이트 (J2)
│   └── research_store.py         #   실험 기록 (SQLite)
├── research/                     # 연구 작업 공간
│   ├── tasks_registry.py         #   태스크 등록소
│   ├── tasks_extra.json          #   사용자 등록 태스크
│   ├── failure_prediction/       #   빌트인 분류 태스크 (반도체 failure)
│   ├── quality_regression/       #   빌트인 회귀 태스크 (두께 예측)
│   ├── prompt_guard/             #   프롬프트 가드레일 태스크 (G 모듈)
│   ├── wafer_vision/             #   웨이퍼맵 분류 태스크 (B8/I 모듈)
│   ├── wiki/                     #   지식 베이스 (마크다운)
│   ├── datasets/                 #   등록된 데이터셋
│   ├── inbox/                    #   새 데이터 투입함
│   └── research.db               #   실험 기록 SQLite 파일
├── airflow/                      # Airflow 설정/운영
│   └── dags/ml_research_loop.py  #   자율 연구 루프 DAG
├── docs/                         # 문서
└── .opencode/                    # opencode 설정
    ├── agents/                   #   커스텀 에이전트
    └── skills/                   #   스킬
```

## 역할 정리

### 핵심 두 축: `src/`(코어) vs `research/`(연구)

| | `src/` | `research/` |
|---|---|---|
| 역할 | 바뀌지 않는 공용 기능 | 실험/개발이 일어나는 작업장 |
| 예 | 데이터 생성, 전처리, 저장 API | 태스크별 runner, 위키, 실험 결과 |
| 수정 빈도 | 낮음 (안정적) | 높음 (매일 갱신) |

> 이 구분이 **핵심 설계 원칙**이다.
> 연구자(에이전트)는 `research/`만 자유롭게 다루고, `src/`는 필요할 때만 신중히 수정한다.
> 그래야 프로젝트 전체가 흔들리지 않는다.

### 데이터가 흐르는 길 (핵심 흐름)

```
1. data/synthetic_data.csv        ← 데이터 생성 (A1에서 실행)
   │
2. src/preprocessing.py           ← 결측치 처리, 스케일링
   │
3. src/model.py                   ← 모델 학습
   │
4. src/evaluation.py              ← F1, PR-AUC 등 평가
   │
5. src/research_store.py          ← 실험 기록 DB(research.db) 저장
   │
6. research/wiki/                 ← 지식 기록 (발견한 것 정리)
```

> 나중에 모듈 C에서 이 흐름이 `experiment_runner.py` 하나로 묶여
> **자동 실행**되는 것을 보게 될 것이다.

## 따라하기

### 1단계: 실제 구조 확인
```bash
cd ~/opencode_ml_practice
ls
```

### 2단계: 주요 파일 미리보기
각 파일의 첫 부분(주석)만 읽어보자:
```bash
python -c "print(open('src/data_manager.py').read().split('\\n')[0])"
python -c "print(open('research/failure_prediction/experiment_runner.py').read().split('\\n')[0])"
```

### 3단계: Makefile 확인
```bash
cat Makefile
```
`make`로 실행 가능한 명령 목록을 확인한다.

## 이해 확인

1. `src/`와 `research/`의 역할 차이는 무엇인가?
2. 실험 결과 숫자는 어디에 저장되고, 지식(발견)은 어디에 쌓이는가?
3. 새 연구 태스크는 어느 폴더에 추가되는가?

## opencode에게 물어보세요

```
이 프로젝트의 전체 구조를 그림으로 설명해주고, 가장 중요한 설계 원칙을 알려줘.
```

## 다음 레슨
[A3. 데이터 이해](03_data_introduction.md) — 반도체 공정 데이터가 실제로 무엇을 의미하는지 본다.