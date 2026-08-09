"""학습된 웨이퍼맵 분류 모델을 이용한 실전 예측 모듈.

`research/wafer_vision/experiment_runner.py` 가 실행되면 학습 상태가
`research/wafer_vision/models/latest_wafer.pkl` 에 저장된다.
이 모듈은 그 pickle 을 불러와 새 웨이퍼맵 이미지의 결함 유형을 판별한다.

사용 예:
    from research.wafer_vision.predict import predict_wafer
    label, conf = predict_wafer(img_32x32)
    print(label, conf)
"""

import glob
import os
import sys

import numpy as np

TASK_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

_LOADED = None


def load_model(model_path: str = None) -> dict:
    """저장된 모델/PCA/클래스 목록/특성 설정을 로드한다."""
    global _LOADED
    if _LOADED is not None:
        return _LOADED
    import joblib

    if model_path:
        path = model_path
    else:
        matches = glob.glob(os.path.join(TASK_DIR, "models", "latest_wafer.pkl"))
        if not matches:
            raise FileNotFoundError(
                "웨이퍼맵 모델이 없습니다. 먼저 experiment_runner 를 실행하세요: "
                "python research/wafer_vision/experiment_runner.py"
            )
        path = matches[0]
    _LOADED = joblib.load(path)
    return _LOADED


def predict_wafer(wafer: np.ndarray, model_path: str = None) -> tuple[str, dict]:
    """웨이퍼맵 한 장의 결함 라벨과 신뢰도(클래스별 확률)를 반환한다.

    wafer: (H, W) 또는 (32, 32) uint8 배열. 학습 리사이즈 크기와 맞지 않으면
        `src.wafer_data_loader.resize_nearest` 로 32×32 로 맞춘다.

    Returns:
        (예측 라벨, {클래스: 확률} 사전)
    """
    from src.image_processing import transform_features

    bundle = load_model(model_path)
    model = bundle["model"]
    pca = bundle["pca"]
    classes = bundle["classes"]
    feat_cfg = bundle.get("feature") or {}

    img = np.asarray(wafer)
    if img.ndim == 3:
        img = img[0]
    if img.shape != (32, 32):
        from src.wafer_data_loader import resize_nearest

        img = resize_nearest(img, size=32)
    img = img.astype(np.uint8)
    if img.dtype != np.uint8:
        img = np.clip(img, 0, 255).astype(np.uint8)

    X = transform_features(np.stack([img]), pca, feat_cfg)
    proba = model.predict_proba(X)[0]
    label_idx = int(model.predict(X)[0])
    probs = {str(c): round(float(p), 4) for c, p in zip(classes, proba)}
    return str(classes[label_idx]), probs


def is_anomaly(wafer: np.ndarray, model_path: str = None) -> tuple[str, float]:
    """정상(normal/none) 확률로 비정상 여부를 판단한다.

    Returns:
        (판정, 정상임의 신뢰도) — 예측 라벨이 정상이면 ("normal", 확률),
        아니면 ("abnormal", 확률)
    """
    label, probs = predict_wafer(wafer, model_path=model_path)
    normal = "normal" if "normal" in probs else "none"
    conf = probs.get(normal, 0.0)
    return ("normal" if label == normal else "abnormal"), conf


if __name__ == "__main__":
    from src.generate_wafer_images import generate_synthetic_wafers

    imgs, _ = generate_synthetic_wafers(n_samples=5)
    for i in range(5):
        label, conf = predict_wafer(imgs[i])
        top = max(conf, key=conf.get)
        print(f"{label:14s} (확신 {conf[top]:.0%}) | sample#{i}")