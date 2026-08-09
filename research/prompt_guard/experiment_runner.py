"""자율 ML 연구를 위한 단일 텍스트 분류 파이프라인 (prompt_guard 태스크).

목표: 사용자 프롬프트가 공격(safe 가 아님)인지 탐지하는 가드레일 모델.
- 입력: 프롬프트 문장 (text 컬럼)
- 출력: 안전성 라벨 (safe / injection / jailbreak / extraction / manipulation)

이 파일은 `ml-researcher` 에이전트가 수정하는 단일 파일이다.
에이전트는 get_config() 만 손대는 것을 기본으로 한다.

실행: python research/prompt_guard/experiment_runner.py
출력: research/prompt_guard/results/run_<id>/{metrics.json, runner_snapshot.py}
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


# ===========================================================================
# [에이전트 수정 영역] - get_config()
# ===========================================================================
def get_config() -> dict:
    """현재 실험 설정. 에이전트는 이 함수를 수정한다."""
    return {
        "dataset": "prompt_dataset",     # data_manager에 등록된 dataset (없으면 생성 방식 사용)
        "text_col": "text",              # 본문(프롬프트) 컬럼
        "n_samples": 1500,               # dataset 미지정 시 생성할 행 수
        "seed": 42,
        "vectorizer": {"max_features": 2000, "min_df": 1, "max_df": 0.9},
        "model_type": "logistic",        # logistic | random_forest | gradient_boosting
        "model_params": {"max_iter": 1000, "C": 1.0},
        "eval_hard": True,               # 경계 사례(하드 케이스) 평가 포함 여부
    }


# ============================================================================
# [에이전트 수정 영역] - 모델 / 로직
# ============================================================================
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


def _load_data(config: dict):
    """(texts, labels) 반환. 등록 데이터셋 또는 합성 생성."""
    n_samples = config.get("n_samples", 1500)
    seed = config.get("seed", 42)
    dataset = config.get("dataset")

    if dataset:
        try:
            from src.data_manager import load_dataset

            X, y = load_dataset(dataset)
            text_col = config.get("text_col", "text")
            texts = X[text_col].tolist()
            labels = y.tolist()
            return texts, labels
        except Exception:
            # 등록이 안 된 환경(깨끗한 DB)이면 생성으로 대체
            pass

    from src.generate_prompt_data import generate_synthetic_prompts

    df = generate_synthetic_prompts(n_samples=n_samples, seed=seed)
    return df["text"].tolist(), df["label"].tolist()


def run_experiment(config: dict = None) -> dict:
    """실험 실행 → {"config", "metrics", "score", "kind"} 반환."""
    from sklearn.metrics import (accuracy_score, auc, f1_score,
                                 precision_recall_curve,
                                 precision_recall_fscore_support,
                                 precision_score, recall_score)
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder

    if config is None:
        config = copy.deepcopy(get_config())

    t0 = time.time()
    texts, labels = _load_data(config)
    seed = config.get("seed", 42)

    # 1. 라벨 인코딩 (문자열 -> 0..n-1)
    le = LabelEncoder()
    y = le.fit_transform(labels)

    # 2. 분할 (stratified — 클래스 불균형 대응)
    X_tr, X_te, y_tr, y_te = train_test_split(
        texts, y, test_size=0.2, stratify=y, random_state=seed
    )

    # 3. TF-IDF (train에만 fit — 테스트 누수 방지)
    vfit = config.get("vectorizer", {})
    vectorizer = build_tfidf_vectorizer(
        max_features=vfit.get("max_features", 2000),
        min_df=vfit.get("min_df", 1),
        max_df=vfit.get("max_df", 0.9),
    )
    matrix = vectorizer.fit_transform(X_tr)
    X_test = vectorizer.transform(X_te)

    # 4. 학습
    model = _build_classifier(config.get("model_type", "logistic"), config.get("model_params", {}))
    model.fit(matrix, y_tr)
    y_prob = model.predict_proba(X_test)
    y_pred = model.predict(X_test)
    y_tr_pred = model.predict(matrix)
    y_tr_prob = model.predict_proba(matrix)

    # 5. 평가 (멀티클래스)
    n_classes = len(le.classes_)
    accuracy = float(accuracy_score(y_te, y_pred))
    macro_prec = float(precision_score(y_te, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_te, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_te, y_pred, average="macro", zero_division=0))

    # train 지표 추가 (과적합 검증 게이트용)
    train_macro_f1 = float(f1_score(y_tr, y_tr_pred, average="macro", zero_division=0))
    train_accuracy = float(accuracy_score(y_tr, y_tr_pred))
    train_pr_aucs = []
    for c in range(n_classes):
        bin_yt = (y_tr == c).astype(int)
        prec_t, rec_t, _ = precision_recall_curve(bin_yt, y_tr_prob[:, c])
        if len(prec_t) < 2 or len(rec_t) < 2:
            continue
        train_pr_aucs.append(auc(rec_t, prec_t))
    train_pr_auc = float(sum(train_pr_aucs) / len(train_pr_aucs)) if train_pr_aucs else 0.0

    # PR-AUC: one-vs-rest 평균
    pr_aucs = []
    for c in range(n_classes):
        bin_y = (y_te == c).astype(int)
        prec, rec, _ = precision_recall_curve(bin_y, y_prob[:, c])
        if len(prec) < 2 or len(rec) < 2:
            continue
        pr_aucs.append(auc(rec, prec))
    pr_auc = float(sum(pr_aucs) / len(pr_aucs)) if pr_aucs else 0.0

    # 클래스별 정밀도/재현율 (기록용)
    per_class = {}
    (p_arr, r_arr, f_arr, _) = precision_recall_fscore_support(
        y_te, y_pred, labels=list(range(n_classes)), zero_division=0
    )
    for name, p, r, f in zip(le.classes_, p_arr, r_arr, f_arr):
        per_class[str(name)] = {"precision": round(float(p), 4), "recall": round(float(r), 4), "f1": round(float(f), 4)}

    # 6. 하드 케이스 평가 (흔히 오탐/오탐하는 경계 사례)
    hard_eval = None
    if config.get("eval_hard", True):
        from src.generate_prompt_data import generate_hard_prompts

        hard_df = generate_hard_prompts()
        hard_y = le.transform(hard_df["label"].tolist())
        hard_X = vectorizer.transform(hard_df["text"].tolist())
        hard_pred = model.predict(hard_X)
        hard_acc = float(accuracy_score(hard_y, hard_pred))
        misclassified = []
        for text, true_i, pred_i in zip(hard_df["text"].tolist(), hard_y, hard_pred):
            if int(true_i) != int(pred_i):
                misclassified.append(
                    {"text": text, "true": str(le.classes_[true_i]), "pred": str(le.classes_[pred_i])}
                )
        hard_eval = {
            "accuracy": round(hard_acc, 4),
            "n": int(len(hard_df)),
            "misclassified": misclassified,
        }

    metrics = {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "macro_f1": round(macro_f1, 4),
        "pr_auc": round(pr_auc, 4),
        "train_macro_f1": round(train_macro_f1, 4),
        "train_accuracy": round(train_accuracy, 4),
        "train_pr_auc": round(train_pr_auc, 4),
        "n_train": int(len(X_tr)),
        "n_test": int(len(X_te)),
        "n_vocab": int(matrix.shape[1]),
        "per_class": per_class,
        "label_distribution": dict(Counter(labels)),
        "hard_eval": hard_eval,
        "elapsed_sec": round(time.time() - t0, 2),
    }
    score = round(macro_f1 * pr_auc, 4)  # 분류 score = F1 × PR-AUC

    return {
        "config": config,
        "metrics": metrics,
        "score": score,
        "kind": "classification",
        "model": model,
        "vectorizer": vectorizer,
        "label_encoder": le,
    }


def build_tfidf_vectorizer(max_features=2000, min_df=1, max_df=0.9):
    from sklearn.feature_extraction.text import TfidfVectorizer

    from src.text_processing import tokenize

    return TfidfVectorizer(
        tokenizer=tokenize,
        token_pattern=None,
        lowercase=True,
        max_features=max_features,
        min_df=min_df,
        max_df=max_df,
    )


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
    """최근 학습된 모델/벡터라이저/라벨을 저장해 실전 예측(predict.py)에서 쓴다.

    run_experiment() 결과에서 판별 객체만 추출하여 TASK_DIR/models/latest_guard.pkl
    로 재현 가능하게 보관한다. research/**/models/는 gitignore 대상이다.
    """
    import joblib

    from src.text_processing import build_tfidf_vectorizer

    model = result.get("model")
    vectorizer = result.get("vectorizer")
    le = result.get("label_encoder")
    if model is None or vectorizer is None or le is None:
        return ""
    os.makedirs(os.path.join(TASK_DIR, "models"), exist_ok=True)
    path = os.path.join(TASK_DIR, "models", "latest_guard.pkl")
    joblib.dump(
        {"model": model, "vectorizer": vectorizer, "classes": list(le.classes_)},
        path,
    )
    return path


if __name__ == "__main__":
    _run_and_save()