"""자율 ML 연구를 위한 단일 회귀 파이프라인 (quality_regression 태스크).

이 파일은 `ml-researcher` 에이전트가 수정하는 단일 파일이다.
반도체 두께(thickness)를 예측하는 회귀 모델을 다룬다.

실행: python research/quality_regression/experiment_runner.py
출력: research/quality_regression/results/run_<id>/{metrics.json, runner_snapshot.py}
"""

import copy
import json
import os
import sys
import time
from datetime import datetime

import numpy as np

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

RESULTS_DIR = os.path.join(TASK_DIR, "results")

from src.data_generation import generate_synthetic_data


# ===========================================================================
# [에이전트 수정 영역] - get_config()
# ===========================================================================
def get_config() -> dict:
    """현재 실험 설정. 에이전트는 이 함수를 수정한다."""
    return {
        "n_samples": 5000,
        "model_type": "ridge",          # ridge | linear | random_forest
        "model_params": {"alpha": 1.0},
        "use_scaling": True,            # 표준화 적용 여부
        "target": "thickness",
        "exclude_cols": ["failure"],    # 타깃/라벨 제외
    }


# ============================================================================
# [에이전트 수정 영역] - run_experiment() 내부 로직
# ============================================================================
def _build_model(model_type: str, params: dict):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression, Ridge

    if model_type == "ridge":
        return Ridge(alpha=params.get("alpha", 1.0), random_state=42)
    if model_type == "linear":
        return LinearRegression()
    if model_type == "random_forest":
        return RandomForestRegressor(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", None),
            random_state=42,
            n_jobs=-1,
        )
    return Ridge(alpha=1.0, random_state=42)


def run_experiment(config: dict = None) -> dict:
    """실험 실행 → {"config", "metrics", "score", "kind"} 반환."""
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split

    if config is None:
        config = copy.deepcopy(get_config())

    seed = config.get("seed", 42)
    t0 = time.time()

    # 1. 데이터
    dataset = config.get("dataset")
    if dataset:
        from src.data_manager import load_dataset

        X, y = load_dataset(dataset)
        if y is None:
            raise ValueError(f"dataset '{dataset}' 에 target 컬럼이 없습니다.")
        df = X.join(y)
    else:
        df = generate_synthetic_data(n_samples=config["n_samples"], seed=seed)

    target = config.get("target_col", config.get("target", "thickness"))
    exclude = config.get("features_cols_exclude", ["failure"])
    feature_cols = [c for c in df.columns if c not in exclude and c != target]

    y = df[target].values
    X = df[feature_cols].values

    # 2. 분할 (seed 유지)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)

    # 3. 표준화 (train 에만 fit — 테스트 누수 방지)
    if config.get("use_features", True):
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler().fit(X_train)
        X_train = scaler.transform(X_train)
        X_test = scaler.transform(X_test)

    # 4. 학습
    model = _build_model(config.get("model_type", "ridge"), config.get("model_params", {}))
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_train_pred = model.predict(X_train)

    # 5. 평가
    train_time = round(time.time() - t0, 2)
    r2 = float(r2_score(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    train_r2 = float(r2_score(y_train, y_train_pred))
    train_rmse = float(np.sqrt(mean_squared_error(y_train, y_train_pred)))

    metrics = {
        "r2": r2,
        "rmse": rmse,
        "mae": mae,
        "train_r2": train_r2,
        "train_rmse": train_rmse,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "target": target,
        "features": feature_cols,
        "elapsed_sec": train_time,
    }
    score = round(r2, 4)  # 단일 지표: R²

    return {"config": config, "metrics": metrics, "score": score, "kind": "regression", "model": model}


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

    print(json.dumps(saveable, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    _run_and_save()