"""로지스틱 회귀 모델 평가 및 시각화."""

import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_curve,
)

matplotlib.use("Agg")  # GUI 없이 이미지 파일로 저장
matplotlib.rcParams["font.family"] = "Apple SD Gothic Neo"
matplotlib.rcParams["axes.unicode_minus"] = False
PLOT_DIR = "plots"

os.makedirs(PLOT_DIR, exist_ok=True)


def evaluate(model, X_test, y_test, plot_dir: str = PLOT_DIR):
    """테스트셋에서 분류 지표 계산 및 시각화 이미지를 저장한다."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    print("=" * 40)
    print("모델 평가 결과 (로지스틱 회귀)")
    print("=" * 40)
    print(f"정확도(Accuracy)   : {acc:.4f} ({acc:.1%})")
    print(f"정밀도(Precision)  : {prec:.4f} ({prec:.1%})")
    print(f"재현율(Recall)     : {rec:.4f} ({rec:.1%})")
    print(f"F1-score           : {f1:.4f} ({f1:.1%})")

    # ROC-AUC
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    roc_auc = auc(fpr, tpr)
    print(f"AUC-ROC            : {roc_auc:.4f}")

    # ------------------------------------------------------------------
    # 1) 혼동 행렬
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1], labels=["합격(0)", "불량(1)"])
    ax.set_yticks([0, 1], labels=["합격(0)", "불량(1)"])
    ax.set_xlabel("예측 라벨")
    ax.set_ylabel("실제 라벨")
    ax.set_title("혼동 행렬 (Confusion Matrix)")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, cm[i, j], ha="center", va="center", color="black", fontsize=16)
    plt.colorbar(im, ax=ax)
    cm_path = os.path.join(plot_dir, "confusion_matrix.png")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=100)
    plt.close()
    print(f"\n[저장] {cm_path}")

    # ------------------------------------------------------------------
    # 2) ROC 커브
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, label=f"로지스틱 회귀 (AUC={roc_auc:.3f})", lw=2)
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="무작위 추정")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC 커브")
    ax.legend(loc="lower right")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    roc_path = os.path.join(plot_dir, "roc_curve.png")
    plt.tight_layout()
    plt.savefig(roc_path, dpi=100)
    plt.close()
    print(f"[저장] {roc_path}")

    # ------------------------------------------------------------------
    # 3) PR 커브 (클래스 불균형 대상에 유용)
    prec_curve, rec_curve, _ = precision_recall_curve(y_test, y_proba)
    pr_auc = auc(rec_curve, prec_curve)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(rec_curve, prec_curve, lw=2, label=f"PR AUC={pr_auc:.3f}")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall 커브")
    ax.legend(loc="upper right")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.05)
    pr_path = os.path.join(plot_dir, "precision_recall_curve.png")
    plt.tight_layout()
    plt.savefig(pr_path, dpi=100)
    plt.close()
    print(f"[저장] {pr_path}")

    # ------------------------------------------------------------------
    # 4) 특성 계수 가시화
    coefs = model.coef_[0]
    features = model.feature_names_in_ if hasattr(model, "feature_names_in_") else None
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(range(len(coefs)), coefs, color=["b" if c > 0 else "r" for c in coefs])
    ax.set_yticks(range(len(coefs)))
    ax.set_yticklabels(features if features is not None else range(len(coefs)))
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("로그-오즈 계수")
    ax.set_title("특성 중요도 (Logistic 계수)")
    coef_path = os.path.join(plot_dir, "feature_coefficients.png")
    plt.tight_layout()
    plt.savefig(coef_path, dpi=100)
    plt.close()
    print(f"[저장] {coef_path}")

    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1, "auc": roc_auc}


if __name__ == "__main__":
    from src.model import split_data, train_logistic_regression
    from src.preprocessing import load_data, preprocess

    df = load_data()
    X, y, scaler = preprocess(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    model = train_logistic_regression(X_train, y_train)
    evaluate(model, X_test, y_test)