# D1. Airflow 기초 — DAG, 태스크, Operator

## 학습 목표
- Airflow가 왜 실험 자동화에 필요한지 안다
- DAG / Task / Operator / 스케줄러의 역할을 이해한다
- 이 프로젝트의 Airflow 환경이 어떻게 구성되어 있는지 확인한다

## 배경 지식

### 로컬 실행의 한계
지금까지 `python research/.../experiment_runner.py`로 실험을 돌렸다.
수작업이다 보니:
- 정시(매일 자정)에 돌지 않는다
- 여러 태스크를 순서대로/병렬로 관리하기 어렵다
- 실패했을 때 자동 재시도가 없다
- 기록/리포트가 매번 수동

**Airflow**는 이런 워크플로우(작업 흐름)를 코드로 정의하고 스케줄·실행·모니터링하는 도구다.

### 핵심 개념
| 용어 | 설명 |
|------|------|
| **DAG** | 방향성 있는 작업 그래프 (어떤 일을 어떤 순서로) |
| **Task** (Operator 인스턴스) | DAG 안의 노드 하나 (실행 단위) |
| **PythonOperator** | Python 함수를 실행하는 기본 Operator |
| **스케줄러** | DAG를 시간에 따라 실행하는 백그라운드 프로세스 |
| **XCom** | 태스크간 작은 데이터 공유 (예: 실행 결과 전달) |
| **스케줄 간격** | `"0 0 * * *"` = 매일 자정 (cron 표현) |

> 실험 workflow를 Airflow로 돌리면: **매일 자동 실행 + 실패 시 재시도 + 리포트 자동 생성**이 된다.

## 따라하기

### 1단계: 실행 환경 확인
```bash
airflow version
```
설치 안 되어 있으면:
```bash
pip install apache-airflow
```
> 설치가 무겁다면, 이 레슨과 D2는 코드만 읽고 확인해도 된다.
> D3에서 실행한다.

### 2단계: Airflow 홈 구성 확인
```bash
ls airflow/          # airflow.db, dags/, logs/ 등
ls airflow/dags/     # 여기 있는 py 파일만 DAG로 인식
```

### 3단계: 스케줄러 시작 (백그라운드)
```bash
make scheduler
```
`airflow scheduler` 프로세가 뜬다. 이 프로세가 DAG를 주기적으로 파싱하고 실행을 예약한다.

### 4단계: DAG 목록 확인
```bash
make dags
```
`ml_research_loop`가 보이는지 확인한다.

## 이해 확인

1. DAG과 Operator의 관계는?
2. 로컬 실행 대신 Airflow의 이점 3개는?
3. `schedule_interval="0 0 * * *"`은 언제 실행되는가?

## opencode에게 물어보세요
```
이 프로젝트의 Airflow 설정 폴더 구조를 설명하고,
airflow dags list 명령으로 어떤 DAG가 있는지 확인해줘.
```

## 다음 레슨
[D2. DAG 해부](16_dag_anatomy.md) — `ml_research_loop` DAG를 뜯어본다.