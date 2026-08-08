"""반도체 실험 데이터 일간 파이프라인 DAG (데모용, 목업 DB/알림 기반).

흐름: DB 추출 → 품질 검증 → 전처리 → 모델 학습 → 평가 → 임계값 확인 → 알림
스케줄: 매일 02:00 (cron), catchup=False
모든 데이터/모델/결과는 날짜별 디렉토리로 산출된다.
"""

import json
import os
import sys
from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score

# 프로젝트 루트를 import 경로에 추가 (mock/, src/ 접근용)
# dags 파일 위치: <루트>/airflow/dags/daily_semiconductor_pipeline.py
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, PROJECT_ROOT)

from mock.mock_utils import load_data_by_date, send_notification as _mock_notify

DEFAULT_ARGS = {
    "owner": "semiconductor-team",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "start_date": datetime(2026, 8, 1),
    "email_on_failure": False,
}

METRICS_THRESHOLD = {
    "f1": 0.80,
    "precision": 0.80,
    "recall": 0.70,
}


def extract_from_db(**context):
    """모의 DB에서 해당 날짜 데이터를 추출해 raw 디렉토리에 저장한다."""
    date = context["ds"]
    os.makedirs(f"data/raw/{date}", exist_ok=True)
    df = load_data_by_date(date)
    if df.empty:
        raise ValueError(f"{date}: 데이터 없음")
    df.to_csv(f"data/raw/{date}/raw.csv", index=False)
    print(f"[extract] {date}: {len(df)}건 추출됨")
    return len(df)


def validate_data(**context):
    """데이터 품질 검증: 결측률·이상치·클래스 비율 리포트 생성."""
    date = context["ds"]
    df = pd.read_csv(f"data/raw/{date}/raw.csv")
    numeric = df.select_dtypes(include=[np.number])
    report = {
        "date": date,
        "n_samples": len(df),
        "missing_rate": float(df.isna().sum().sum() / df.size),
        "failure_rate": float(df["failure"].mean()),
        "outlier_rate": float(
            ((np.abs(numeric - numeric.mean()) > 4 * numeric.std()).sum().sum() / df.size)
        ),
        "columns": list(df.columns),
    }
    os.makedirs(f"data/quality/{date}", exist_ok=True)
    with open(f"data/quality/{date}/report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[validate] {date}: 품질 리포트 결측률 {report['missing_rate']:.2%}")
    return report


def preprocess(**context):
    """전처리: 결측 중앙값 대체, failure 정수형 변환."""
    date = context["ds"]
    df = pd.read_csv(f"data/raw/{date}/raw.csv")
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].fillna(df[col].median())
    df["failure"] = df["failure"].astype(int)
    os.makedirs(f"data/processed/{date}", exist_ok=True)
    df.to_csv(f"data/processed/{date}/processed.csv", index=False)
    print(f"[preprocess] {date}: {len(df)}행 전처리 완료")
    return len(df)


def train_model(**context):
    """로지스틱 회귀 학습 (전체 전처리 데이터 기반)."""
    date = context["ds"]
    df = pd.read_csv(f"data/processed/{date}/processed.csv")
    X = df.drop(columns=["failure", "date"], errors="ignore")
    y = df["failure"]
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, y)
    os.makedirs(f"models/{date}", exist_ok=True)
    joblib.dump(
        {"model": model, "columns": X.columns.tolist()}, f"models/{date}/model.joblib"
    )
    print(f"[train] {date}: 모델 학습 완료")
    return {"model_path": f"models/{date}/model.joblib"}


def evaluate_model(**context):
    """평가: F1/정밀도/재현율 계산 + metrics.json 저장."""
    date = context["ds"]
    df = pd.read_csv(f"data/processed/{date}/processed.csv")
    artifacts = joblib.load(f"models/{date}/model.joblib")
    X = df[artifacts["columns"]]
    y = df["failure"]
    y_pred = artifacts["model"].predict(X)
    metrics = {
        "date": date,
        "f1": float(f1_score(y, y_pred, zero_division=0)),
        "precision": float(precision_score(y, y_pred, zero_division=0)),
        "recall": float(recall_score(y, y_pred, zero_division=0)),
        "n_samples": len(y),
    }
    os.makedirs(f"results/{date}", exist_ok=True)
    with open(f"results/{date}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[evaluate] {date}: F1={metrics['f1']:.3f}")
    return metrics


def check_threshold(**context):
    """성능 기준 충족 여부를 확인하고 로그로 남긴다."""
    date = context["ds"]
    with open(f"results/{date}/metrics.json") as f:
        metrics = json.load(f)
    ok = all(metrics[k] >= v for k, v in METRICS_THRESHOLD.items())
    status = "pass" if ok else "fail"
    print(f"[check] {date}: 기준 충족={ok} ({status})")
    return status


def send_notification(**context):
    """결과 알림 (파일 기반 목업)."""
    date = context["ds"]
    with open(f"results/{date}/metrics.json") as f:
        metrics = json.load(f)
    message = (
        f"일간 파이프라인 완료 {date}: "
        f"F1={metrics['f1']:.3f} / P={metrics['precision']:.3f} / R={metrics['recall']:.3f}"
    )
    _mock_notify(message, level="info")
    return message


with DAG(
    dag_id="daily_semiconductor_pipeline",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 2 * * *",  # 매일 02:00
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["semiconductor", "ml", "daily"],
    doc_md=__doc__,
) as dag:

    t_extract = PythonOperator(
        task_id="extract_from_db", python_callable=extract_from_db
    )
    t_validate = PythonOperator(task_id="validate_data", python_callable=validate_data)
    t_preprocess = PythonOperator(task_id="preprocess", python_callable=preprocess)
    t_train = PythonOperator(task_id="train_model", python_callable=train_model)
    t_evaluate = PythonOperator(task_id="evaluate_model", python_callable=evaluate_model)
    t_check = PythonOperator(task_id="check_threshold", python_callable=check_threshold)
    t_notify = PythonOperator(
        task_id="send_notification", python_callable=send_notification
    )

    t_extract >> t_validate >> t_preprocess >> t_train >> t_evaluate >> t_check >> t_notify