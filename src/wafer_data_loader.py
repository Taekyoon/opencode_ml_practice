"""WM-811K(반도체 웨이퍼맵 공개 데이터셋) 로더/전처리.

WM-811K는 TSMC가 제공한 실제 반도체 라인에서 수집된 811,457장의 웨이퍼맵을
담은 데이터셋이다. 이 중 172,950장에 수동 라벨이 붙어 있다.

DataFrame 구조 (LSWMD.pkl — pandas pickle):
    waferMap      : 2차원 list (셀 값 0=웨이퍼 밖, 1=양품, 2=불량)
    failureType   : 라벨 문자열 (Center/Donut/Edge-Loc/Edge-Ring/Loc/Random/Scratch/Near-full, none)
    lotName, waferIndex, trie(학습/테스트 구분), dieSize 등 부가 정보

다운로드(직접):
    https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map
    파일을 research/datasets/ 혹은 data/WM811K/ 에 둔다.

이 모듈은 pickle 을 읽어 32×32 그레이스케일 uint8 배열 + 라벨로 정규화한다.
"""
import os

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_PICKLE = os.path.join(PROJECT_ROOT, "data", "WM811K", "LSWMD_811.pkl")

OUTSIDE, GOOD, DEFECT = 0, 1, 2  # WM-811K 셀 값 의미

# 라벨 → 그레이스케일 강도 (불량 셀=255, 양품=128, 외부=0)
INTENSITY = {OUTSIDE: 0.0, GOOD: 128.0, DEFECT: 255.0}

RANDOM_SEED = 42


def resize_nearest(img: np.ndarray, size: int = 32) -> np.ndarray:
    """numpy-only nearest-neighbor 리사이즈. 크기가 다른 웨이퍼맵을 size×size로 맞춘다."""
    src_y = np.linspace(0, img.shape[0] - 1, size)
    src_x = np.linspace(0, img.shape[1] - 1, size)
    idx_y = np.clip(np.round(src_y).astype(int), 0, img.shape[0] - 1)
    idx_x = np.clip(np.round(src_x).astype(int), 0, img.shape[1] - 1)
    return img[np.ix_(idx_y, idx_x)]


def wafer_map_to_image(wafer_map, size: int = 32) -> np.ndarray:
    """WM-811K 셀 배열(0/1/2) → 32×32 그레이스케일 uint8 변환."""
    arr = np.asarray(wafer_map, dtype=np.float32)
    img = np.zeros_like(arr, dtype=np.float32)
    for cell_val, intensity in INTENSITY.items():
        img[arr == cell_val] = intensity
    return resize_nearest(img, size=size).astype(np.uint8)


def find_wm811k_pickle(candidates: list[str] = None) -> str:
    """LSW891.pkl 후보 경로를 찾는다. 없으면 FileNotFoundError."""
    if candidates is None:
        candidates = [
            DEFAULT_PICKLE,
            os.path.join(PROJECT_ROOT, "data", "WM811K", "LSWMD_891.pkl"),
            os.path.join(PROJECT_ROOT, "data", "WM811K", "LSW811.pkl"),
            os.path.join(PROJECT_ROOT, "data", "WM811K", "LSWMD.pkl"),
        ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        "WM-811K 데이터셋 파일을 찾을 수 없습니다. Kaggle에서 LSWMD_891.pkl 을 "
        f"다운로드해 다음 위치에 놓으세요: {DEFAULT_PICKLE}\n"
        "get: https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map"
    )


def load_wm811k(
    pickle_path: str = None,
    size: int = 32,
    max_samples: int = None,
    labeled_only: bool = True,
    seed: int = RANDOM_SEED,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """WM-811K 를 (images, labels, info)로 로드한다.

    Returns:
        images : (N, size, size) uint8 배열
        labels : (N,) 문자열 라벨 배열 (라벨이 없는 none 도 포함 가능)
        info   : {n_total, n_labeled, labeled_ratio, class_distribution}
    """
    path = find_wm811k_pickle(pickle_path)
    import pandas as pd

    df = pd.read_pickle(path)
    if "waferMap" not in df.columns:
        raise ValueError(f"waferMap 컬럼이 없습니다. 컬럼: {list(df.columns)}")

    has_failure = "failure" in df.columns
    fail = df["failure"] if has_failure else None

    if labeled_only and has_failure:
        labeled = fail.notna() & (fail.astype(str).str.strip() != "")
        df = df[labeled]

    if max_samples is not None and len(df) > max_samples:
        idx = np.random.default_rng(seed).choice(len(df), max_samples, replace=False)
        df = df.iloc[idx]

    images = [wafer_map_to_image(m, size=size) for m in df["waferMap"].tolist()]
    images = np.stack(images).astype(np.uint8)

    labels = None
    if has_failure and fail is not None:
        labels = fail.loc[df.index].fillna("none").astype(str).str.strip().to_numpy()
        labels = np.where(labels == "", "none", labels)

    class_dist = (
        df["failure"].fillna("none").astype(str).value_counts().to_dict() if has_failure else {}
    )
    info = {
        "n": int(len(df)),
        "n_labeled": int(len(df)),
        "labeled_ratio": round(len(df) / len(fail), 4) if (has_failure and len(fail)) else 1.0,
        "class_distribution": class_dist,
    }
    return images, labels, info


if __name__ == "__main__":
    try:
        imgs, labs, info = load_wm811k(max_samples=500)
        print("WM-811K 로드 성공:", info)
    except FileNotFoundError as e:
        print(e)