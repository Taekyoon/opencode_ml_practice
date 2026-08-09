"""실험 실행 로직 모음.

지금까지 수행한 실험들을 재현 가능한 함수로 캡슐화한다:
- baseline: 로지스틱 회귀 baseline (결측/표준화 파이프라인)
- imbalance: SMOTE 적용 + 임계값 최적화 (불균형 개선)
- extreme: 극심 저불량 스트레스 테스트
- scalability: 데이터 크기별 처리/학습 시간 측정

각 함수는 (metrics_dict) 를 반환하며, Airflow 태스크에서 호출된다.
"""

import json
import os
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    auc,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from src.data_generation import generate_synthetic_data
from src.preprocessing import add_synthetic_missing, fill_missing, scale_features

try:
    from imblearn.over_sampling import SMOTE
    _IMBALANCED_AVAILABLE = True
except ImportError:
    _IMBALANCED_AVAILABLE = False

RANDOM_SEED = 42

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERIMENT_DIR = os.path.join(BASE_DIR, "experiments", "results")


def _out_dir(name: str) -> str:
    path = os.path.join(EXPERIMENT_DIR, name)
    os.makedirs(path, exist_ok=True)
    return path


def _save_metrics(name: str, metrics: dict) -> str:
    path = os.path.join(_out_dir(name), "metrics.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[experiment:{name}] saved -> {path}")
    return path


def _standard_metrics(y_true, y_pred, y_proba=None) -> dict:
    """분류 지표 계산 (proba 제공 시 ROC/PR-AUC 포함)."""
    m = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    if y_proba is not None:
        fpr, tpr, _ = roc_curve(y_true, y_proba)
        m["roc_auc"] = float(auc(fpr, tpr))
        p, r, _ = precision_recall_curve(y_true, y_proba)
        m["pr_auc"] = float(auc(r, p))
    return m


# ---------------------------------------------------------------------------
# 데이터 준비
# ---------------------------------------------------------------------------
def _load_data(n_samples: int, seed: int) -> tuple[pd.DataFrame, pd.Series]:
    df = generate_synthetic_data(n_samples=n_samples, seed=seed)
    y = df["failure"].astype(int)
    X = df.drop(columns=["failure"])
    return X, y


def _load_preprocessed(n_samples: int, seed: int) -> tuple[pd.DataFrame, pd.Series]:
    """가상 데이터 → 결측 주입 → 중앙값 대체 → 표준화."""
    X, y = _load_data(n_samples, seed)
    X = fill_missing(add_synthetic_missing(X.join(y), seed=seed))
    y = X["failure"].astype(int)
    X = X.drop(columns=["failure"])
    X_scaled, _ = scale_features(X)
    return X_scaled, y


def _split(X, y, seed: int = RANDOM_SEED):
    return train_test_split(X, y, test_size=0.2, stratify=y, random_state=seed)


# ---------------------------------------------------------------------------
# 실험 1: baseline
# ---------------------------------------------------------------------------
def run_baseline(n_samples: int = 5000, seed: int = RANDOM_SEED) -> dict:
    X_scaled, y = _load_preprocessed(n_samples, seed)
    X_train, X_test, y_train, y_test = _split(X_scaled, y)

    model = LogisticRegression(max_iter=1000, random_state=seed)
    model.fit(X_train, y_train)
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = _standard_metrics(y_test, model.predict(X_test), y_proba)
    metrics.update({
        "experiment": "baseline",
        "n_samples": n_samples,
        "train_failure_rate": float(y_train.mean()),
        "test_failure_rate": float(y_test.mean()),
    })

    _save_metrics("baseline", metrics)
    return metrics


# ---------------------------------------------------------------------------
# 실험 2: 불균형 SMOTE + 임계값 최적화
# ---------------------------------------------------------------------------
def run_imbalance(n_samples: int = 5000, seed: int = RANDOM_SEED) -> dict:
    X_scaled, y = _load_preprocessed(n_samples, seed)
    X_train, X_test, y_train, y_test = _split(X_scaled, y)

    base = LogisticRegression(max_iter=1000, random_state=seed)
    base.fit(X_train, y_train)
    base_metrics = _standard_metrics(y_test, base.predict(X_test), base.predict_proba(X_test)[:, 1])

    result = {
        "experiment": "imbalance_smote",
        "baseline": base_metrics,
    }

    if not _IMBALANCED_AVAILABLE:
        result["note"] = "imbalanced-learn 미설치로 SMOTE 생략"
        _save_metrics("imbalanced", result)
        return result

    X_res, y_res = SMOTE(random_state=seed).fit_resample(X_train, y_train)
    model = LogisticRegression(max_iter=1000, random_state=seed)
    model.fit(X_res, y_res)
    proba = model.predict_proba(X_test)[:, 1]

    # 임계값 최적화 (F1 목표)
    p, r, thresholds = precision_recall_curve(y_test, proba)
    denom = p[:-1] + r[:-1]
    f1s = np.divide(2 * p[:-1] * r[:-1], denom, out=np.zeros_like(denom), where=denom > 0)
    best_t = float(thresholds[np.argmax(f1s)])
    y_pred_opt = (proba >= best_t).astype(int)

    smote_metrics = _standard_metrics(y_test, y_pred_opt, proba)
    smote_metrics.update({
        "best_threshold": best_t,
        "train_failure_rate_after_smote": float(y_res.mean()),
        "improvement_f1_vs_baseline": round(smote_metrics["f1"] - base_metrics["f1"], 4),
    })
    result.update(smote_metrics)

    _save_metrics("imbalanced", result)
    return result


# ---------------------------------------------------------------------------
# 실험 3: 극심 저불량 스트레스 테스트
# ---------------------------------------------------------------------------
def run_extreme(n_samples: int = 5000, seed: int = RANDOM_SEED) -> dict:
    X_scaled, y = _load_preprocessed(n_samples, seed)
    X_train, X_test, y_train, y_test = _split(X_scaled, y)
    failure_rate = float(y.mean())

    base = LogisticRegression(max_iter=1000, random_state=seed)
    base.fit(X_train, y_train)
    base_metrics = _standard_metrics(y_test, base.predict(X_test), base.predict_proba(X_test)[:, 1])

    result = {
        "experiment": "extreme",
        "failure_rate": failure_rate,
        "n_samples": n_samples,
        "baseline": base_metrics,
    }

    if _IMBALANCED_AVAILABLE and y_train.sum() >= 2 and (y_train == 0).sum() >= 2:
        X_res, y_res = SMOTE(random_state=seed).fit_resample(X_train, y_train)
        sm = LogisticRegression(max_iter=1000, random_state=seed).fit(X_res, y_res)
        proba = sm.predict_proba(X_test)[:, 1]
        sm_metrics = _standard_metrics(y_test, sm.predict(X_test), proba)
        p, r, thresholds = precision_recall_curve(y_test, proba)
        denom = p[:-1] + r[:-1]
        f1s = np.divide(2 * p[:-1] * r[:-1], denom, out=np.zeros_like(denom), where=denom > 0)
        best_t = float(thresholds[np.argmax(f1s)])
        sm_opt = _standard_metrics(y_test, (proba >= best_t).astype(int), proba)
        result["smote"] = sm_metrics
        result["smote_optimized_threshold"] = sm_opt
        result["best_threshold"] = best_t

    _save_metrics("extreme", result)
    return result


# ---------------------------------------------------------------------------
# 실험 4: 데이터 크기 스케일링 (확장성)
# ---------------------------------------------------------------------------
def run_scalability(sizes=(5000, 50000, 100000), seed: int = RANDOM_SEED) -> dict:
    runs = []
    for n in sizes:
        t0 = time.time()
        X, y = _load_preprocessed(n, seed)
        t_load = time.time() - t0

        t0 = time.time()
        X_train, X_test, y_train, y_test = _split(X, y)
        model = LogisticRegression(max_iter=1000, random_state=seed)
        model.fit(X_train, y_train)
        t_train = time.time() - t0

        y_proba = model.predict_proba(X_test)[:, 1]
        m = _standard_metrics(y_test, model.predict(X_test), y_proba)
        runs.append({
            "n_samples": n,
            "load_time_sec": round(t_load, 3),
            "train_time_sec": round(t_train, 3),
            "f1": m["f1"],
            "roc_auc": m["roc_auc"],
        })

    result = {"experiment": "scalability", "runs": runs}
    _save_metrics("scalability", result)
    return result


# ---------------------------------------------------------------------------
# 종합 요약
# ---------------------------------------------------------------------------
def summarize_all() -> str:
    """실행된 모든 실험의 metrics.json 을 합쳐 summary.json 을 만든다."""
    rows = []
    if not os.path.isdir(EXPERIMENT_DIR):
        return ""
    for folder in sorted(os.listdir(EXPERIMENT_DIR)):
        path = os.path.join(EXPERIMENT_DIR, folder, "metrics.json")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            rows.append(json.load(f))
    summary_path = os.path.join(BASE_DIR, "experiments", "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"[experiment:summary] {len(rows)}개 실험 요약 -> {summary_path}")
    return summary_path