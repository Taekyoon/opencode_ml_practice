"""웨이퍼맵 이미지를 ML 모델이 사용할 수 있는 수치 특성으로 변환한다.

ML 모델은 이미지 픽셀을 그대로 계산하지 않고, 픽셀에서 추출한 "특성 벡터"를
사용한다. 여기서는 세 가지 특성 그룹을 조합한다:

1. 평탄화(flatten) : 32×32 → 1,024차원. 픽셀 원본.
2. PCA               : 1,024차원을 주성분 50개로 압축 (노이즈 제거 + 차원 축소)
3. 그래디언트(96차)   : 픽셀 값 변화량(기울기)의 히스토그램. 선형 결함(스크래치/크랙) 검출
4. 방사 프로파일(8차) : 웨이퍼 중심에서 반지름별 평균 밝기. 원형 패턴(Edge-Ring 등) 검출

각 그룹은 (n_samples, n_features) 행렬로 나오며, 최종적으로 옆으로 붙인다.
"""
import numpy as np

from src.generate_wafer_images import IMAGE_SIZE


def flatten(images: np.ndarray) -> np.ndarray:
    """(N, 32, 32) → (N, 1024) 평탄화."""
    return images.reshape(images.shape[0], -1).astype(np.float32)


def gradient_features(images: np.ndarray, bins: int = 32) -> np.ndarray:
    """그래디언트 히스토그램. (N, 3*bins) 반환 (dx, dy, magnitude)."""
    out = []
    for img in images.astype(np.float32):
        dx = np.diff(img, axis=1, prepend=0)
        dy = np.diff(img, axis=0, prepend=0)
        mag = np.sqrt(dx**2 + dy**2)
        feats = np.concatenate(
            [
                np.histogram(dx, bins=bins, range=(-255, 255), density=True)[0],
                np.histogram(dy, bins=bins, range=(-255, 255), density=True)[0],
                np.histogram(mag, bins=bins, range=(0, 255), density=True)[0],
            ]
        )
        out.append(feats)
    return np.asarray(out, dtype=np.float32)


def radial_profile(images: np.ndarray, n_bins: int = 8) -> np.ndarray:
    """방사 프로파일. (N, n_bins) — 중심에서 반지름별 평균 밝기."""
    size = images.shape[1]
    center = (size - 1) / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.sqrt((xx - center) ** 2 + (yy - center) ** 2)
    max_r = r.max() + 1e-6
    bin_idx = np.clip((r / max_r * n_bins).astype(int), 0, n_bins - 1)

    out = []
    for img in images.astype(np.float32):
        feats = np.zeros(n_bins, dtype=np.float32)
        counts = np.zeros(n_bins, dtype=np.float32)
        np.add.at(feats, bin_idx.ravel(), img.ravel())
        np.add.at(counts, bin_idx.ravel(), 1)
        feats = np.where(counts > 0, feats / np.maximum(counts, 1), 0.0)
        out.append(feats)
    return np.asarray(out, dtype=np.float32)


def build_pca(n_components: int = 50):
    """PCA 변환기(transform)를 위한 팩토리. sklearn을 lazy import."""
    from sklearn.decomposition import PCA

    return PCA(n_components=n_components, random_state=42)


def extract_features(
    images: np.ndarray,
    pca_components: int = 50,
    use_gradient: bool = True,
    radial_bins: int = 8,
) -> np.ndarray:
    """이미지 배치 → 특성 행렬 (N, total_features).

    train 피팅을 위해 PCA 객체가 필요한 경우 fit_pca() 를 사용한다.
    예측 단계에서는 학습 시 만든 PCA 객체로 transform() 만 수행해야 한다.
    """
    flat = flatten(images)
    pca = build_pca(n_components=pca_components)
    flat_pca = pca.fit_transform(flat)
    parts = [flat_pca]
    if use_gradient:
        parts.append(gradient_features(images))
    if radial_bins > 0:
        parts.append(radial_profile(images, n_bins=radial_bins))
    return np.concatenate(parts, axis=1).astype(np.float32)


def feature_pipeline(images: np.ndarray, config: dict = None) -> tuple[np.ndarray, object]:
    """(특성 행렬, PCA 객체) 반환. fit용 — train에만 사용한다."""
    if config is None:
        config = {}
    flat = flatten(images)
    pca = build_pca(n_components=config.get("pca_components", 50))
    flat_pca = pca.fit_transform(flat)
    parts = [flat_pca]
    if config.get("use_gradient", True):
        parts.append(gradient_features(images))
    if config.get("radial_bins", 8) > 0:
        parts.append(radial_profile(images, n_bins=config.get("radial_bins", 8)))
    feats = np.concatenate(parts, axis=1).astype(np.float32)
    return feats, pca


def transform_features(images: np.ndarray, pca: object, config: dict = None) -> np.ndarray:
    """이미 fit된 PCA 로 transform 만 수행. test/예측용."""
    if config is None:
        config = {}
    flat = flatten(images)
    flat_pca = pca.transform(flat)
    parts = [flat_pca]
    if config.get("use_gradient", True):
        parts.append(gradient_features(images))
    if config.get("radial_bins", 8) > 0:
        parts.append(radial_profile(images, n_bins=config.get("radial_bins", 8)))
    return np.concatenate(parts, axis=1).astype(np.float32)


def expected_feature_size(images: np.ndarray, config: dict = None) -> int:
    """특성 행렬의 예상 차원 수."""
    if config is None:
        config = {}
    n = images.shape[0]
    total = config.get("pca_components", 50)
    if config.get("use_gradient", True):
        total += 96
    if config.get("radial_bins", 8) > 0:
        total += config.get("radial_bins", 8)
    return total


if __name__ == "__main__":
    from src.generate_wafer_images import generate_synthetic_wafers

    imgs, _ = generate_synthetic_wafers(n_samples=100)
    X, pca = feature_pipeline(imgs)
    print("특성 행렬 형태:", X.shape)
    print("예상 차원:", expected_feature_size(imgs))
