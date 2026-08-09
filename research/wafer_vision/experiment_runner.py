"""자율 ML 연구를 위한 단일 웨이퍼맵 분류/이상탐지 파이프라인 (wafer_vision 태스크).

목표: 반도체 웨이퍼맵 이미지(32×32 그레이스케일)에서 결함 패턴을 판별한다.
- 입력: 웨이퍼맵 이미지 배열 (N, 32, 32) uint8 — (0=주변, 128=양품, 255=불량)
- 출력: 결함 유형 라벨 (normal/scratch/particle/crack/contamination, 또는 WM-811K 유형)

두 가지 분석 모드를 지원한다 (config["task"]):
- classification : 결함 유형 다중 클래스 분류   → score = F1(macro) × PR-AUC
- anomaly        : 일반/비정상 이진 이상탐지     → score = ROC-AUC (normal 대 기준)

데이터 소스(config["data_source"]):
- synthetic : src/generate_wafer_images 합성 데이터 (0 의존성, 기본값)
- wm811k    : WM-811K 공개 데이터셋 (Kaggle에서 다운로드 필요)

특성 파이프라인: flatten(1024) → PCA(50) + 그래디언트(96) + 방사 프로파일(8)

실행: python research/wafer_vision/experiment_runner.py
출력: research/wafer_vision/results/run_<id>/{metrics.json, runner_snapshot.py}
"""

import copy
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

RESULTS_DIR = os.path.join(TASK_DIR, "results")

NORMAL_CLASS_NAMES = ["normal"]


# ===========================================================================
# [에이전트 수정 영역] - get_config()
# ===========================================================================
def get_config() -> dict:
    """현재 실험 설정. 에이전트는 이 함수를 수정한다."""
    return {
        "data_source": "synthetic",        # synthetic | wm811k
        "n_samples": 2000,                 # synthetic 일 때 생성 행 수
        "seed": 42,
        "size": 32,                        # 웨이퍼맵 리스케일 크기
        "task": "classification",          # classification | anomaly
        "feature": {
            "pca_components": 50,
            "use_gradient": True,
            "radial_bins": 8,
        },
        "model_type": "random_forest",     # random_forest | logistic | gradient_boosting
        "model_params": {"n_estimators": 200, "max_depth": None},
        # 이상탐지가 켜져 있으면 anomaly ROC-AUC 도 함께 기록
        "eval_anomaly": True,
    }


# ============================================================================
# [에이전트 수정 영역] - 데이터 로드
# ============================================================================
def _load_data(config: dict) -> tuple:
    """(images, labels) 반환. images: (N, size, size) uint8, labels: 문자열 배열."""
    import numpy as np

    size = config.get("size", 32)

    if config.get("data_source") == "wm811k":
        from src.wafer_data_loader import load_wm811k

        images, labels, info = load_wm811k(size=size, labeled_only=True)
        return images, labels

    from src.generate_wafer_images import generate_synthetic_wafers

    images, labels = generate_synthetic_wafers(
        n_samples=config.get("n_samples", 2004), seed=config.get("seed", 42)
    )
    return images, labels


def _build_classifier(model_type: str, params: dict):
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    if model_type == "random_forest":
        return RandomForestClassifier(
            n_estimators=params.get("n_estimators", 200),
            max_depth=params.get("max_depth", None),
            random_state=42,
            n_jobs=-1,
        )
    if model_type == "gradient_boosting":
        return GradientBoostingClassifier(
            n_estimators=params.get("n_estimators", 150),
            learning_rate=params.get("learning_rate", 0.1),
            max_depth=params.get("max_depth", 3),
            random_state=42,
        )
    return LogisticRegression(
        max_iter=params.get("max_iter", 1000),
        C=params.get("C", 1.0),
        random_state=42,
        class_weight=params.get("class_weight", None),
    )


def _build_anomaly_model(model_type: str, params: dict):
    from sklearn.ensemble import IsolationForest
    from sklearn.svm import OneClassSVM

    if model_type == "one_class_svm":
        return OneClassSVM(
            nu=params.get("nu", 0.1),
            gamma=params.get("gamma", "scale"),
        )
    return IsolationForest(
        n_estimators=params.get("n_estimators", 200),
        contamination=params.get("contamination", 0.1),
        random_state=42,
        n_jobs=-1,
    )


def run_experiment(config: dict = None) -> dict:
    """실험 실행 → {"config", "metrics", "score", "kind"} 반환."""
    from sklearn.metrics import (accuracy_score, auc, f1_score,
                                 precision_recall_curve,
                                 precision_recall_fscore_support,
                                 precision_score, recall_score, roc_auc_score)
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder

    if config is None:
        config = copy.deepcopy(get_config())

    t0 = time.time()
    images, labels = _load_data(config)
    seed = config.get("seed", 42)
    task = config.get("task", "classification")

    # 라벨 인코딩 (문자열 → 0..n-1)
    le = LabelEncoder()
    y = le.fit_transform(labels)

    # 1. 특성 추출 (flatten → PCA → 그래디언트 → 방사) — train에만 fit
    from src.image_processing import feature_pipeline, transform_features

    feat_cfg = config.get("feature", {})
    X_tr_img, X_te_img, y_tr, y_te = train_test_split(
        images, y, test_size=0.2, stratify=y, random_state=seed
    )
    X_tr, pca = feature_pipeline(X_tr_img, feat_cfg)
    X_te = transform_features(X_te_img, pca, feat_cfg)

    # 2. 분류 학습
    model = _build_classifier(config.get("model_type", "random_forest"), config.get("model_params", {}))
    model.fit(X_tr, y_tr)
    y_prob = model.predict_proba(X_te)
    y_pred = model.predict(X_te)

    # 3. 분류 평가 (멀지클래스)
    n_classes = len(le.classes_)
    accuracy = float(accuracy_score(y_te, y_pred))
    macro_prec = float(precision_score(y_te, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_te, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_te, y_pred, average="macro", zero_division=0))

    pr_aucs = []
    for c in range(n_classes):
        bin_y = (y_te == c).astype(int)
        prec, rec, _ = precision_recall_curve(bin_y, y_prob[:, c])
        if len(prec) < 2 or len(rec) < 2:
            continue
        pr_aucs.append(auc(rec, prec))
    pr_auc = float(sum(pr_aucs) / len(pr_aucs)) if pr_aucs else 0.0

    per_class = {}
    (p_arr, r_arr, f_arr, _) = precision_recall_fscore_support(
        y_te, y_pred, labels=list(range(n_classes)), zero_division=0
    )
    for name, p, r, f in zip(le.classes_, p_arr, r_arr, f_arr):
        per_class[str(name)] = {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f), 4),
        }

    # 4. 이상탐지 평가 (선택): 정상 클래스만 학습 → 1=정상, 0=비정상
    anomaly = None
    if config.get("eval_anomaly", True):
        # 정상(참조) 클래스: 합성은 "normal", WM-811K는 "none"
        ref_candidates = ["normal", "none"]
        ref_name = next((c for c in ref_candidates if c in le.classes_), None)
        if ref_name is not None and len(le.classes_) > 1:
            try:
                ref_idx = list(le.classes_).index(ref_name)
                clf = _build_anomaly_model(
                    config.get("anomaly_model", "isolation_forest"),
                    config.get("anomaly_params", {"n_estimators": 200, "contamination": 0.1}),
                )
                clf.fit(X_tr[y_tr == ref_idx])
                scores = clf.decision_function(X_te)
                bin_true = (y_te == ref_idx).astype(int)
                roc = float(roc_auc_score(bin_true, scores))
                anomaly = {"ref_class": ref_name, "roc_auc": round(roc, 4), "n_ref_train": int((y_tr == ref_idx).sum())}
            except Exception:
                anomaly = None

    metrics = {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "macro_f1": round(macro_f1, 4),
        "pr_auc": round(pr_auc, 4),
        "per_class": per_class,
        "label_distribution": dict(Counter(labels)),
        "n_features": int(X_tr.shape[1]),
        "n_train": int(len(X_tr)),
        "n_test": int(len(X_te)),
        "anomaly_roc_auc": anomaly["roc_auc"] if anomaly else None,
        "anomaly_ref_class": anomaly["ref_class"] if anomaly else None,
        "elapsed_sec": round(time.time() - t0, 2),
    }

    if task == "anomaly":
        score = round(metrics["anomaly_roc_auc"] or 0.0, 4)
    else:
        score = round(macro_f1 * pr_auc, 4)  # 분류 score = F1 × PR-AUC

    return {
        "config": config,
        "metrics": metrics,
        "score": score,
        "kind": "classification",
        "model": model,
        "pca": pca,
        "label_encoder": le,
        "feature_config": feat_cfg,
    }


def _run_and_save(run_dir: str = None) -> dict:
    """실험 실행 + 결과 저장."""
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

    _export_model(result)

    print(json.dumps(saveable, indent=2, ensure_ascii=False))
    return result


def _export_model(result: dict) -> str:
    """최근 학습된 분류기/PCA/라벨을 저장해 실전 예측(predict.py)에 쓴다."""
    import joblib

    model = result.get("model")
    pca = result.get("pca")
    le = result.get("label_encoder")
    feat_cfg = result.get("feature_config")
    if model is None or pca is None or le is None:
        return ""
    os.makedirs(os.path.join(TASK_DIR, "models"), exist_ok=True)
    path = os.path.join(TASK_DIR, "models", "latest_wafer.pkl")
    joblib.dump(
        {"model": model, "pca": pca, "classes": list(le.classes_), "feature": feat_cfg},
        path,
    )
    return path


if __name__ == "__main__":
    _run_and_save()