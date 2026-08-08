"""전체 ML 실험 스위트 DAG.

지금까지 수행한 모든 실험을 Airflow 작업으로 관리한다.
- baseline: 로지스틱 회귀 파이프라인 지표
- imbalance: SMOTE + 임계값 최적화
- extreme: 극심 저불량 스트레스 테스트
- scalability: 데이터 크기별 처리/학습 시간 (5k/50k/100k)

4개 실험은 병렬로 실행되고, 마지막에 summary.json으로 통합된다.
수동 트리거 또는 make trigger-experiments 로 실행한다.
"""

import os
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

# 프로젝트 루트 참조: <루트>/airflow/dags/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments import (
    run_baseline,
    run_imbalance,
    run_extreme,
    run_scalability,
    summarize_all,
)

DEFAULT_ARGS = {
    "owner": "semiconductor-team",
    "retries": 1,
    "depends_on_past": False,
    "email_on_failure": False,
}


def _op(dag, task_id, fn, **fn_kwargs):
    def _callable():
        return fn(**fn_kwargs)

    return PythonOperator(dag=dag, task_id=task_id, python_callable=_callable)


with DAG(
    dag_id="semiconductor_experiments",
    default_args=DEFAULT_ARGS,
    schedule_interval=None,  # 수동 트리거 전용
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["semiconductor", "experiments", "ml"],
    description="모든 실험(baseline/SMOTE/극심불균형/스케일링) 실행 + 요약",
) as dag:

    t_baseline = _op(dag, "experiment_baseline", run_baseline, n_samples=5000)
    t_imbalance = _op(dag, "experiment_imbalance", run_imbalance, n_samples=5000)
    t_extreme = _op(dag, "experiment_extreme", run_extreme, n_samples=5000)
    t_scalability = _op(dag, "experiment_scalability", run_scalability,
                        sizes=(5000, 50000, 100000))

    t_summary = PythonOperator(
        dag=dag,
        task_id="experiment_summary",
        python_callable=summarize_all,
    )

    # 4개 실험 병렬 실행 후 요약
    [t_baseline, t_imbalance, t_extreme, t_scalability] >> t_summary