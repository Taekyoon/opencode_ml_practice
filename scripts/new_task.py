#!/usr/bin/env python3
"""새 자율 연구 태스크 자동 생성 스캐폴더.

사용법:
    python scripts/new_task.py <task_id> --dataset <dataset_name> --target <target_col> [--note "..."]
    python scripts/new_task.py <task_id> --inbox <inbox_file.csv> --target <target_col> [--note "..."]

동작:
1. 데이터셋 확인 (기 등록 dataset 또는 inbox에서 이번에 등록)
2. research/<task_id>/ 폴더 생성:
   - experiment_runner.py  (분류/회귀 공통 템플릿)
   - program.md            (연구 지침서 초안)
   - results/              (실험 결과 폴더)
3. research/tasks_extra.json 에 task 등록 (Airflow 재파싱 시 자동 인식)

이후 ml-researcher 에이전트가 runner를 튜닝하거나,
로컬에서 `python research/<task_id>/experiment_runner.py` 로 직접 실행한다.
"""

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import data_manager  # noqa: E402
from research.tasks_registry import ExperimentTask, register_task  # noqa: E402

RESEARCH_DIR = os.path.join(PROJECT_ROOT, "research")

# ---------------------------------------------------------------------------
# runner 템플릿 (자리표: __TASK_ID__, __DATASET__, __TARGET__)
# ---------------------------------------------------------------------------
RUNNER_TEMPLATE = '''"""자율 ML 연구 단일 파이프라인 (task: __TASK_ID__).

스캐폴드(scripts/new_task.py)로 자동 생성된 초기 베이스라인.
ml-researcher 에이전트가 이 파일을 수정하여 성능을 개선한다.

출력: research/__TASK_ID__/results/run_<id>/ {metrics.json, runner_snapshot.py}
실행: python research/__TASK_ID__/experiment_runner.py
"""

import copy
import json
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

RESULTS_DIR = os.path.join(TASK_DIR, "results")

from src.data_manager import load_dataset  # noqa: E402


# =============================================================================
# [에이전트 수정 영역] 설정
# =============================================================================
def get_config() -> dict:
    return {
        "dataset": "__DATASET__",
        "target_col": "__TARGET__",
        # 분류 예시
        "model_type": "logistic",
        "model_params": {"max_iter": 1000, "C": 1.0},
        # 회귀 예시: model_type="ridge", model_params={"alpha": 1.0}
        "imbalance_strategy": "none",   # none | smote
        "scale": True,
    }


# =============================================================================
# [에이전트 수정 영역] 모델 / 로직
# =============================================================================
def build_classifier(model_type, params):
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
        max_iter=params.get("max_iter", 1000),
        C=params.get("C", 1.0),
        random_state=42,
    )


def build_regressor(model_type, params):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression, Ridge

    if model_type == "ridge":
        return Ridge(alpha=params.get("alpha", 1.0), random_state=42)
    if model_type == "random_forest":
        return RandomForestRegressor(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", None),
            random_state=42,
            n_jobs=-1,
        )
    return LinearRegression()


def run_experiment(config=None) -> dict:
    """실험 실행 → {"config", "metrics", "score", "kind"} 반환."""
    if config is None:
        config = copy.deepcopy(get_config())

    t0 = time.time()
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    # 1. 데이터 로드
    X, y = load_dataset(config["dataset"])
    target = config.get("target_col")
    if target is not None and target in X.columns:
        y = X[target]
        X = X.drop(columns=[target])
    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)

    # 2. 분류/회귀 자동 판정
    import numpy as _np
    arr = _np.asarray(y)
    uniq = _np.unique(arr)
    is_regression = not (len(uniq) <= 20)  # 클래스 수 <=20 → 분류
    kind = "regression" if is_regression else "classification"

    # 3. 전처리 (스케일링)
    if config.get("scale", True):
        X = pd.DataFrame(StandardScaler().fit_transform(X), columns=X.columns)

    # 4. 분할
    if is_regression:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )

    # 5. 학습/평가
    if is_regression:
        from sklearn.metrics import mean_absolute_error, r2_score
        from sklearn.metrics import mean_squared_error

        model = build_regressor(config.get("model_type", "ridge"), config.get("model_params", {}))
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_true = _np.asarray(y_test)
        r2 = float(r2_score(y_true, y_pred))
        metrics = {
            "target_col": target,
            "r2": r2,
            "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
            "mae": float(mean_absolute_error(y_true, y_pred)),
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "elapsed_sec": round(time.time() - t0, 2),
        }
        score = round(r2, 4)
    else:
        from sklearn.metrics import (accuracy_score, auc, f1_score,
                                     precision_recall_curve, precision_score,
                                     recall_score, roc_auc_score)

        model = build_classifier(config.get("model_type", "logistic"), config.get("model_params", {}))
        model.fit(X_train, y_train)
        y_proba = model.predict_proba(X_test)[:, 1]
        y_pred = (y_proba >= 0.5).astype(int)
        y_true = _np.asarray(y_test)

        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        prec, rec, _ = precision_recall_curve(y_true, y_proba)
        pr_auc = float(auc(rec, prec))
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": f1,
            "pr_auc": pr_auc,
            "roc_auc": float(roc_auc_score(y_true, y_proba)),
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "elapsed_sec": round(time.time() - t0, 2),
        }
        score = round(f1 * pr_auc, 4)

    return {"config": config, "metrics": metrics, "score": score, "kind": kind}


def _run_and_save() -> dict:
    run_id = "run_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESULTS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)

    result = run_experiment()
    saveable = {
        "config": result["config"],
        "metrics": result["metrics"],
        "score": result["score"],
        "kind": result["kind"],
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
'''


PROGRAM_TEMPLATE = """# __TASK_ID__ — 자율 연구 지침서

> 스캐폴드(scripts/new_task.py)로 자동 생성됨. 사람이 보완한다.

## 1. 연구 목표
- 데이터셋: `__DATASET__`
- 목표 변수: `__TARGET__`
- 태스크 종류: 자동 판정 (분류/회귀)

## 2. 평가 지표
- 분류: score = F1 × PR-AUC
- 회귀: score = R²

## 3. 반복 전략 (A/B 원칙)
1. 과거 결과 먼저 확인 (research/__TASK_ID__/results/)
2. 한번에 하나의 변수만 변경
3. 개선되면 keep, 아니면 되돌리기
4. 분류(특히 불균형)이면 PR-AUC 중심으로 판단

## 4. 실행
- 로컬: `python research/__TASK_ID__/experiment_runner.py`
- Airflow: 연구 에이전트가 자동 실행
"""


def _infer_kind(dataset: str, target: str) -> str:
    """target 컬럼 값 유형으로 분류/회귀 판정."""
    meta = data_manager.get_dataset(dataset)
    df = pd_read_csv(meta)
    if target not in df.columns:
        return "regression"
    values = df[target].dropna()
    if values.dtype.kind in "if":
        uniq = values.nunique()
        return "classification" if uniq <= 2 else "regression"
    return "classification"


def pd_read_csv(meta: dict):
    import pandas as pd

    return pd.read_csv(meta["source_file"])


def _register_from_inbox(filename: str, target: str, name: str) -> str:
    info = data_manager.register_file(filename, target_col=target, name=name)
    print(f"[new_task] inbox '{filename}' → dataset '{info['name']}' 등록됨")
    return info["name"]


def main(argv=None):
    parser = argparse.ArgumentParser(description="새 자율 연구 태스크 생성")
    parser.add_argument("task_id", help="새 태스크 이름 (폴더명)")
    parser.add_argument("--dataset", help="기 등록된 dataset 이름")
    parser.add_argument("--inbox", help="inbox 파일명으로 새 dataset 등록")
    parser.add_argument("--target", required=True, help="target 컬럼명")
    parser.add_argument("--note", default="", help="한 줄 설명")
    parser.add_argument("--overwrite", action="store_true", help="기존 폴더 덮어쓰기")
    args = parser.parse_args(argv)

    task_id = args.task_id.strip().replace(" ", "_")
    if not task_id:
        sys.exit("[error] task_id 가 비어 있음")

    # 1. 데이터셋 결정
    if args.dataset:
        dataset = args.dataset
    elif args.inbox:
        dataset = _register_from_inbox(args.inbox, args.target, name=task_id)
    else:
        sys.exit("[error] --dataset 또는 --inbox 중 하나는 반드시 지정")

    # 2. target 유효성
    try:
        meta = data_manager.get_dataset(dataset)
    except KeyError:
        names = [d["name"] for d in data_manager.list_datasets()]
        sys.exit(f"[error] dataset '{dataset}' 없음. 등록된: {names}")
    import json as _json

    feature_cols = _json.loads(meta["feature_cols"]) if isinstance(meta["feature_cols"], str) else meta["feature_cols"]
    cols = list(feature_cols) + ([meta["target_col"]] if meta["target_col"] else [])
    if args.target not in cols:
        sys.exit(f"[error] target '{args.target}' 가 dataset '{dataset}' 없음. 컬럼: {cols}")

    # 3. kind 결정
    kind = _infer_kind(dataset, args.target)
    score_name = "r2" if kind == "regression" else "score"

    # 4. 폴더 생성
    task_dir = os.path.join(RESEARCH_DIR, task_id)
    if os.path.exists(task_dir) and not args.overwrite:
        sys.exit(f"[error] research/{task_id} 이미 존재 (--overwrite 로 덮어쓰기)")
    os.makedirs(os.path.join(task_dir, "results"), exist_ok=True)

    # 5. runner / program 작성
    runner = RUNNER_TEMPLATE.replace("__TASK_ID__", task_id).replace("__DATASET__", dataset).replace("__TARGET__", args.target)
    with open(os.path.join(task_dir, "experiment_runner.py"), "w", encoding="utf-8") as f:
        f.write(runner)
    program = PROGRAM_TEMPLATE.replace("__TASK_ID__", task_id).replace("__DATASET__", dataset).replace("__TARGET__", args.target)
    with open(os.path.join(task_dir, "program.md"), "w", encoding="utf-8") as f:
        f.write(program)

    # 6. 레지스트리 등록 (tasks_extra.json 저장)
    task = ExperimentTask(
        id=task_id,
        kind=kind,
        score_name=score_name,
        runner=f"research/{task_id}/experiment_runner.py",
        program=f"research/{task_id}/program.md",
        results_dir=f"research/{task_id}/results",
        description=args.note or f"{task_id} (dataset={dataset}, target={args.target})",
    )
    register_task(task, persist=True)

    print(f"\n[new_task] '{task_id}' 생성 완료:")
    print(f"  dataset : {dataset}")
    print(f"  target  : {args.target}")
    print(f"  kind    : {kind}  (score = {score_name})")
    print(f"  runner  : research/{task_id}/experiment_runner.py")
    print(f"  실행    : python research/{task_id}/experiment_runner.py")


if __name__ == "__main__":
    main()