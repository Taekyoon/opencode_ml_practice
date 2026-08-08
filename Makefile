# Airflow 데모 실행 자동화
# 사용법: make <target>

AIRFLOW_HOME_CMD = AIRFLOW_HOME=$(PWD)/airflow

.PHONY: init dags db seed scheduler webserver ui stop clean demo

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
	$(AIRFLOW_HOME_CMD) airflow dags list | grep semiconductor

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

## 전체 실험 실행 (baseline + SMOTE + 극심 + 스케일링)
experiments:
	$(AIRFLOW_HOME_CMD) airflow dags trigger semiconductor_experiments
	@echo "실험 요약: cat experiments/summary.json"

## 실험을 로컬에서 직접 실행 (Airflow 없이, 검증용)
experiments-local:
	python -c "from experiments import run_baseline, run_imbalance, run_extreme, run_scalability, summarize_all; run_baseline(); run_imbalance(); run_extreme(); run_scalability(); print('요약:', summarize_all())"

## 자율 연구 루프 실행 (에이전트가 수정한 runner 실행)
research:
	$(AIRFLOW_HOME_CMD) airflow dags trigger ml_research_loop

## 자율 연구 루프를 로컬에서 직접 실행 (Airflow 없이, 검증용)
research-local:
	python experiment_runner.py
	@echo "실험 결과: cat research/results/run_*/metrics.json"

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

## 전체 데모: 초기화 → 시드 → 스케줄러+UI 시작
demo: init seed scheduler ui
	@echo "데모 준비 완료 → http://localhost:8080 (admin/admin)"
	$(AIRFLOW_HOME_CMD) airflow dags unpause daily_semiconductor_pipeline --yes || true