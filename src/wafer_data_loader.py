"""WM-811K(반도체 웨이퍼맵 공개 데이터셋) 로더/전처리.

WM-811K는 TSMC가 제공한 실제 반도체 라인에서 수집된 811,457장의 웨이퍼맵을
담은 데이터셋이다. 이 중 172,950장에 수동 라벨이 붙어 있다.

DataFrame 구조 (LSWMD.pkl — pandas pickle):
    waferMap       : 2차원 list/ndarray (셀 값 0=웨이퍼 밖, 1=양품, 2=불량)
    failureType    : 결함 라벨 (Center/Donut/Edge-Loc/Edge-Ring/Loc/Random/Scratch/
                     Near-full/none, 라벨 없음=None). 값이 numpy 배열로 한 겹 감싸
                     저장되어 있어([['none']]) 여기서 펼쳐서 사용한다.
    trianTestLabel : 'Training'/'Test' (train/test 공식 분리)
    lotName/waferIndex/dieSize 등 부가 정보

다운로드(직접):
    - Kaggle: https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map
    - HuggingFace: https://huggingface.co/datasets/lslattery/wafer-defect-detection
    파일을 data/WM811K/ 에 둔다.

이 모듈은 pickle 을 읽어 32×32 그레이스케일 uint8 배열 + 라벨로 정규화한다.
"""
import math
import os

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_PICKLE = os.path.join(PROJECT_ROOT, "data", "WM811K", "LSWMD_811.pkl")

# 컬럼 호환: LSWMD.pkl 실데이터는 failureType, 구버전/스크립트는 failure/label 일 수 있음
LABEL_COLUMN_CANDIDATES = ["failureType", "failure", "label"]

TRAIN_COLUMN = "trianTestLabel"

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


def _as_label(value):
    """WM-811K 라벨 셀 값([[none]]처럼 중첩 배열로 감싸 있음)을 문자열로 펼친다.

    - 배열([['Center']])이면 안쪽 스칼라까지 한 겹씩 풀어낸다
    - NaN/None → None (라벨 없음)
    - 그 외 → strip 된 문자열
    """
    while isinstance(value, (list, tuple, np.ndarray)):
        if len(value) == 0:
            return None
        value = value[0]
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    return str(value)


def find_wm811k_pickle(candidates: list[str] = None) -> str:
    """LSWMD.pkl 후보 경로를 찾는다. 없으면 FileNotFoundError."""
    if candidates is None:
        candidates = [
            DEFAULT_PICKLE,
            os.path.join(PROJECT_ROOT, "data", "WM811K", "LSWMD_891.pkl"),
            os.path.join(PROJECT_ROOT, "data", "WM811K", "LSWMD.pkl"),
        ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        "WM-811K 데이터셋 파일을 찾을 수 없습니다. 아래 위치에 놓으세요:\n"
        f"  {DEFAULT_PICKLE}\n"
        "출처: https://www.kaggle.com/datasets/qingyi/wm811k-wafer-map "
        "(또는 HuggingFace lslattery/wafer-defect-detection)"
    )


def load_wm811k(
    pickle_path: str = None,
    size: int = 32,
    max_samples: int = None,
    labeled_only: bool = True,
    seed: int = RANDOM_SEED,
    use_trian_split: bool = True,
) -> tuple:
    """WM-811K 를 로드한다.

    Returns:
        기본: (images, labels, info)
            images : (N, size, size) uint8
            labels : (N,) 문자열 라벨 ('none' = 라벨 있음/정상 웨이퍼)
            info   : {n, n_total, n_labeled, class_distribution, ...}

        use_trian_split=True 이고 실제 데이터셋(trianTestLabel 사용 가능)이면:
            (X_train, y_train, X_test, y_test, info)
            info 에 train/test 분포가 각각 담긴다.
    """
    import pandas as pd

    path = find_wm811k_pickle(pickle_path)
    df = pd.read_pickle(path)
    if "waferMap" not in df.columns:
        raise ValueError(
            f"waferMap 컬럼이 없습니다. 컬럼: {list(df.columns)}\n"
            f"이 파일({path})은 WM-811K 포맷이 아닐 수 있습니다."
        )

    fail_col = next((c for c in LABEL_COLUMN_CANDIDATES if c in df.columns), None)
    fail = df[fail_col].map(_as_label) if fail_col else None
    labeled_mask = fail.notna() if fail is not None else np.ones(len(df), dtype=bool)

    trian = df[TRAIN_COLUMN].map(_as_label) if TRAIN_COLUMN in df.columns else None
    has_trian = trian is not None and bool((trian == "Training").sum()) and bool(
        (trian == "Test").sum()
    )

    n_total = int(len(df))
    n_labeled = int(labeled_mask.sum()) if fail is not None else n_total

    if labeled_only and fail is not None:
        df = df[labeled_mask]
        fail = fail[labeled_mask]
        if trian is not None:
            trian = trian[labeled_mask]

    if max_samples is not None and len(df) > max_samples:
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(df), max_samples, replace=False)
        df = df.iloc[idx]
        fail = fail.iloc[idx] if fail is not None else None
        trian = trian.iloc[idx] if trian is not None else None

    def _images(rows) -> np.ndarray:
        imgs = [wafer_map_to_image(m, size=size) for m in rows["waferMap"].tolist()]
        return np.stack(imgs).astype(np.uint8)

    def _dist(s):
        return s.value_counts().to_dict() if s is not None else {}

    if has_trian:
        train_mask = (trian == "Training").to_numpy()
        test_mask = (trian == "Test").to_numpy()
        train_df = df.iloc[train_mask]
        test_df = df.iloc[test_mask]
        y_tr = fail.to_numpy()[train_mask]
        y_te = fail.to_numpy()[test_mask]
        info = {
            "n": int(len(df)),
            "n_total": n_total,
            "n_labeled": n_labeled,
            "n_train": int(len(train_df)),
            "n_test": int(len(test_df)),
            "trian_split": True,
            "class_distribution": _dist(fail),
            "train_class_distribution": _dist(fail[train_mask]),
            "test_class_distribution": _dist(fail[test_mask]),
        }
        return _images(train_df), y_tr, _images(test_df), y_te, info

    images = _images(df)
    labels = fail.to_numpy() if fail is not None else None
    info = {
        "n": int(len(df)),
        "n_total": n_total,
        "n_labeled": n_labeled,
        "trian_split": False,
        "class_distribution": _dist(fail),
    }
    return images, labels, info


if __name__ == "__main__":
    try:
        data = load_wm811k()
        if len(data) == 5:
            x_tr, y_tr, x_te, y_te, info = data
            print("WM-811K 로드 성공 (공식 train/test split):", info)
        else:
            imgs, labs, info = data
            print("WM-811K 로드 성공:", {k: v for k, v in info.items()})
    except FileNotFoundError as e:
        print(e)
        raise SystemExit(1)