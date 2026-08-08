"""로지스틱 회귀 기반 반도체 failure 예측 모델."""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42


def split_data(X, y, test_size: float = 0.2, seed: int = RANDOM_SEED):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=seed
    )
    print(f"데이터 분할: train {X_train.shape[0]} / test {X_test.shape[0]}")
    print(f"  train 불량률: {y_train.mean():.1%}, test 불량률: {y_test.mean():.1%}")
    return X_train, X_test, y_train, y_test


def train_logistic_regression(X_train, y_train, C: float = 1.0, seed: int = RANDOM_SEED):
    """C는 정규화 강도의 역수. 작을수록 강한 정규화."""
    model = LogisticRegression(C=C, max_iter=1000, random_state=seed)
    model.fit(X_train, y_train)
    print(f"모델 학습 완료 (정규화 강도 C={C})")
    return model


if __name__ == "__main__":
    from src.preprocessing import load_data, preprocess

    df = load_data()
    X, y, scaler = preprocess(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    model = train_logistic_regression(X_train, y_train)
    print("\n학습된 계수:")
    for col, coef in zip(X.columns, model.coef_[0]):
        print(f"  {col}: {coef:.4f}")