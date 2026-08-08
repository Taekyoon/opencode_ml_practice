"""반도체 failure 예측을 위한 데이터 전처리."""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

RANDOM_SEED = 42


def load_data(path: str = "data/synthetic_data.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"데이터 로드: {df.shape[0]}행, {df.shape[1]}열")
    return df


def add_synthetic_missing(df: pd.DataFrame, missing_rate: float = 0.05, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """특정 공정/측정 변수에 결측치를 무작위로 주입 (센서 오류 모사)."""
    rng = np.random.default_rng(seed)
    target_cols = ["temperature", "pressure", "thickness", "resistivity"]
    df = df.copy()
    for col in target_cols:
        mask = rng.random(df.shape[0]) < missing_rate
        df.loc[mask, col] = np.nan
    return df


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """결측치를 중앙값으로 대체."""
    df = df.copy()
    missing_before = df.isna().sum().sum()
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].fillna(df[col].median())
    missing_after = df.isna().sum().sum()
    print(f"결측치 처리: {missing_before} -> {missing_after}")
    return df


def scale_features(X: pd.DataFrame) -> pd.DataFrame:
    """특성을 표준화 (평균 0, 표준편차 1)."""
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
    return X_scaled, scaler


def preprocess(df: pd.DataFrame, target: str = "failure") -> tuple:
    """저장된 원본 데이터를 받아 전처리 후 (X, y, scaler) 반환."""
    df = add_synthetic_missing(df)
    df = fill_missing(df)

    y = df[target].values
    X = df.drop(columns=[target])

    X_scaled, scaler = scale_features(X)
    print(f"전처리 완료: X {X_scaled.shape}, y 불량 비율 {y.mean():.1%}")
    return X_scaled, y, scaler


if __name__ == "__main__":
    df = load_data()
    X, y, scaler = preprocess(df)
    print("\n원-핫/스케일링 확인:")
    print(X.head())