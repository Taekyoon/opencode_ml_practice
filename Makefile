# Airflow 데모 실행 자동화
# 사용법: make <target>

AIRFLOW_HOME_CMD = AIRFLOW_HOME=$(PWD)/airflow

.PHONY: init dags db seed scheduler webserver ui stop clean demo new-task wiki-lint archive test

## Airflow DB 초기화 + 관리자 계정 (admin/admin)
init:
	$(AIRFLOW_HOME_CMD) airflow db init
	$(AIRFLOW_HOME_CMD) airflow users create \
	  --username admin --firstname Admin --lastname User \
	  --role Admin --email admin@example.com --password admin || true

## 모의 데이터 생성 (DB)
seed:
	python -c "from mock.mock_utils import insert_daily_data; [print(d, '->', insert_daily_data(d, n_samples=1500)) for d in ['2026-08-05','2026-08-06','2026-08-07','2026-08-08']]"

## DAG 파싱 실패 여부 확인
dags:
	$(AIRFLOW_HOME_CMD) airflow dags list-import-errors
	$(AIRFLOW_HOME_CMD) airflow dags list | grep -E "ml_research_loop|semiconductor"

## 스케줄러 백그라운드 시작
scheduler:
	mkdir -p airflow/logs
	nohup $(AIRFLOW_HOME_CMD) airflow scheduler > airflow/logs/scheduler.out 2>&1 &
	@echo "scheduler PID: $$!"

## Web UI (http://localhost:8080, admin/admin)
ui:
	mkdir -p airflow/logs
	nohup $(AIRFLOW_HOME_CMD) airflow webserver -p 8080 > airflow/logs/webserver.out 2>&1 &
	@echo "Web UI : http://localhost:8080"

## DAG 수동 트리거 (오늘 실행)
trigger:
	$(AIRFLOW_HOME_CMD) airflow dags trigger daily_semiconductor_pipeline

## 아카이브된 레거시 실험 코드 보기 (experiments/, semiconductor_experiments DAG)
##  → archive/code/experiments/, archive/code/semiconductor_experiments_dag.py
archive:
	@echo "아카이브 관련 파일:"
	@find archive -type f | sort

## 자율 연구 루프 실행 (에이전트가 수정한 runner 실행)
research:
	$(AIRFLOW_HOME_CMD) airflow dags trigger ml_research_loop

## 특정 task만 자율 연구 루프 실행 (TASK=failure_prediction quality_regression)
research-task:
	$(AIRFLOW_HOME_CMD) airflow dags trigger ml_research_loop -c '{"task": "$(TASK)"}'

## 자율 연구 루프를 로컬에서 직접 실행 (Airflow 없이, task별 runner)
research-local:
	python research/failure_prediction/experiment_runner.py
	@echo "실험 결과: research/failure_prediction/results/run_*/metrics.json"

## 새 연구 태스크 생성 (스캐폴드)
##   make new-task TASK=maintenance_cost DATASET=lab_sensor_data TARGET=failure NOTE="설명"
##   (기 등록 dataset이 없으면 inbox 등록: cp data/synthetic_data.csv research/inbox/ 후
##    python scripts/new_task.py TASK --inbox synthetic_data.csv --target failure)
new-task:
	python scripts/new_task.py $(TASK) --dataset $(DATASET) --target $(TARGET) --note "$(NOTE)"

## 실험 기록 위키 건강 검진 (broken link/고아/미등록/오래된 데이터)
wiki-lint:
	python scripts/wiki_lint.py

## inbox에 있는 새 데이터 확인 + 등록
inbox:
	python -m src.data_manager

## inbox 데이터 등록 (FILE=파일명)
inbox-register:
	python -c "from src.data_manager import register_file; print(register_file('$(FILE)'))"

## 연구 실험 기록 확인
research-log:
	python -m src.research_store

## 최신 실험 리포트 확인
research-report:
	@cat research/reports/report_*.md 2>/dev/null || echo "아직 리포트 없음"

## 백엔드 프로세스 중지 (scheduler/webserver, master 전용)
stop:
	pkill -f "airflow scheduler" || true
	pkill -f "airflow webserver" || true

## 유닛 테스트 실행 (tests/)
test:
	python -m pytest tests/ -q

## 전체 데모: 초기화 → 시드 → 스케줄러+UI 시작
demo: init seed scheduler ui
	@echo "데모 준비 완료 → http://localhost:8080 (admin/admin)"
	$(AIRFLOW_HOME_CMD) airflow dags unpause daily_semiconductor_pipeline --yes || true