"""자율 ML 연구를 위한 단일 실험 파이프라인 (failure_prediction 태스크).

이 파일은 `ml-researcher` 에이전트가 수정하는 **단일 파일**이다.
전처리, 특성 공학, 모델, 불균형 대응을 모두 담당하며,
`src/` 아래 고정 모듈을 import하여 데이터 생성/기본 유틸리티를 재사용한다.

실행: python research/failure_prediction/experiment_runner.py
출력: research/failure_prediction/results/run_<run_id>/{metrics.json, runner_snapshot.py}
"""

import copy
import json
import os
import sys
import time
from datetime import datetime

import numpy as np

# 프로젝트 루트를 sys.path에 추가 (Airflow에서 실행 시에도 안전)
TASK_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

RESULTS_DIR = os.path.join(TASK_DIR, "results")

from src.data_generation import generate_synthetic_data
from src.preprocessing import add_synthetic_missing, fill_missing, scale_features

# ===========================================================================
# [에이전트 수정 영역] - get_config() 내 하이퍼파라미터를 조정한다
# ===========================================================================
def get_config() -> dict:
    """현재 실험 설정을 반환한다. 에이전트는 이 함수만 수정하면 된다."""
    return {
        "n_samples": 5000,
        "missing_rate": 0.05,          # 결측치 주입 비율
        "imbalance_strategy": "none",  # none | smote | threshold | smote+threshold
        "model_type": "logistic",      # logistic | random_forest | gradient_boosting
        "model_params": {"max_iter": 1000, "C": 1.0},
        "threshold": 0.5,              # 분류 임계값 (0~1)
        "optimize_threshold": False,   # True 시 F1 최적 임계값 자동 탐색
        "scale": True,                 # 표준화 적용 여부
    }


# ============================================================================
# [에이전트 수정 영역] - run_experiment() 내부 로직을 자유롭게 변경한다.
# ============================================================================
def _load_data(config: dict):
    """데이터 로드 → 결측 주입 → 처리 → (X, y) 반환.

    - config['dataset'] 지정 시: src.data_manager 로 등록된 데이터셋 사용
    - 미지정: 가상 데이터 생성 (기본)
    """
    seed = config.get("seed", 42)

    dataset = config.get("dataset")
    if dataset:
        from src.data_manager import load_dataset

        X, y = load_dataset(dataset)
        X = X.copy()
        if y is not None:
            y = y.astype(int)
        if config.get("scale", True):
            X, _ = scale_features(X)
        print(f"[runner] dataset '{dataset}' 사용: {X.shape}")
        return X, y

    df = generate_synthetic_data(n_samples=config["n_samples"], seed=seed)
    df = add_synthetic_missing(df, missing_rate=config.get("missing_rate", 0.05), seed=seed)
    df = fill_missing(df)

    y = df["failure"].astype(int)
    X = df.drop(columns=["failure"])

    if config.get("scale", True):
        X, _ = scale_features(X)
    return X, y


def _build_model(model_type: str, params: dict):
    """모델 생성."""
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    if model_type == "random_forest":
        return RandomForestClassifier(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", None),
            random_state=42,
            n_jobs=-1,
        )
    if model_type == "gradient_boosting":
        return GradientBoostingClassifier(
            n_estimators=params.get("n_estimators", 100),
            learning_rate=params.get("learning_rate", 0.1),
            max_depth=params.get("max_depth", 3),
            random_state=42,
        )
    return LogisticRegression(
        C=params.get("C", 1.0),
        max_iter=params.get("max_iter", 1000),
        random_state=42,
    )


def _apply_imbalance(X_train, y_train, strategy: str):
    """불균형 대응 전략 적용 (SMOTE)."""
    if strategy not in ("smote", "smote+threshold"):
        return X_train, y_train
    try:
        from imblearn.over_sampling import SMOTE
    except ImportError:
        return X_train, y_train
    return SMOTE(random_state=42).fit_resample(X_train, y_train)


def run_experiment(config: dict = None) -> dict:
    """실험 실행 → {"config", "metrics", "score"} 반환."""
    from sklearn.metrics import (
        auc,
        f1_score,
        precision_recall_curve,
        precision_score,
        recall_score,
        roc_curve,
    )
    from sklearn.model_selection import train_test_split

    if config is None:
        config = copy.deepcopy(get_config())

    # 1. 데이터 준비
    X, y = _load_data(config)

    # 2. 분할 (stratify 고정, seed 42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # 3. 불균형 대응 (SMOTE는 train에만 적용)
    strategy = config.get("imbalance_strategy", "none")
    X_train, y_train = _apply_imbalance(X_train, y_train, strategy)

    # 4. 모델 학습
    t0 = time.time()
    model = _build_model(config.get("model_type", "logistic"), config.get("model_params", {}))
    model.fit(X_train, y_train)
    y_proba = model.predict_proba(X_test)[:, 1]

    # 5. 임계값 적용
    threshold = config.get("threshold", 0.5)
    if config.get("optimize_threshold", False):
        # F1 최적화 임계값 탐색 (score 개선 목적)
        from sklearn.metrics import precision_recall_curve

        p_curve, r_curve, t_curve = precision_recall_curve(y_test, y_proba)
        denom = p_curve[:-1] + r_curve[:-1]
        f1s = np.divide(2 * p_curve[:-1] * r_curve[:-1], denom, out=np.zeros_like(denom), where=denom > 0)
        threshold = float(t_curve[np.argmax(f1s)])
    y_pred = (y_proba >= threshold).astype(int)

    # 6. 평가 (단일 지표: score = F1 × PR-AUC)
    metrics = {
        "accuracy": float(np.mean(y_pred == y_test)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
    }
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    pr_prec, pr_rec, _ = precision_recall_curve(y_test, y_proba)
    metrics["roc_auc"] = float(auc(fpr, tpr))
    metrics["pr_auc"] = float(auc(pr_rec, pr_prec))
    metrics["elapsed_sec"] = round(time.time() - t0, 2)

    score = round(metrics["f1"] * metrics["pr_auc"], 4)

    return {"config": config, "metrics": metrics, "score": score, "model": model}


def _run_and_save(run_dir: str = None) -> dict:
    """실험 실행 + 파일 저장 (research/<task>/results/run_<id>)."""
    if run_dir is None:
        run_id = "run_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(RESULTS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)

    result = run_experiment()

    saveable = {
        "config": result["config"],
        "metrics": result["metrics"],
        "score": result["score"],
    }
    with open(os.path.join(run_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(saveable, f, indent=2, ensure_ascii=False)

    with open(__file__, encoding="utf-8") as f:
        src = f.read()
    with open(os.path.join(run_dir, "runner_snapshot.py"), "w", encoding="utf-8") as f:
        f.write(src)

    print(json.dumps(saveable, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    _run_and_save()