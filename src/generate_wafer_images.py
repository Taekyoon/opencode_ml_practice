"""반도체 웨이퍼 불량 이미지 태스크를 위한 가상 웨이퍼맵 생성.

컨셉: 웨이퍼맵(wafer map)이란 반도체 제조 공정 후 각 칩(die)의 검사
합격/불량 여부를 2차원 지도로 표현한 것이다. 이 모듈은 불량 패턴을
가진 웨이퍼맵을 합성으로 만들어 "이미지 분류"의 입력 데이터로 쓴다.

이미지 규격: 32×32 그레이스케일 (0=웨이퍼 밖, 1~15=양품 셀 노이즈, 255=결함)
- 웨이퍼 외곽은 원형 마스크로 처리해 실제 웨이퍼 형상을 흉내 낸다.
- contamination(오염)은 반투명 얼룩으로 64~153 범위(결함 255와 구분).

클래스 분포(교육용 균형 분포 — 실전에서는 normal이 90% 이상일 수 있음):
    normal         50%   양품 (불량 셀이 거의 없음)
    scratch        12%   스크래치 (선형 긁힘)
    particle       12%   파티클 (이물질, 산발적 점들)
    crack          12%   크랙 (가는 균열 선)
    contamination  14%   오염 (넓은 영역의 얼룩)

생성 규칙: 시드 고정 → 동일 스크립트로 언제든 같은 데이터를 재현한다.
"""
import os

import numpy as np

RANDOM_SEED = 42

IMAGE_SIZE = 32
CLASS_RATIO = {
    "normal": 0.50,
    "scratch": 0.12,
    "particle": 0.12,
    "crack": 0.12,
    "contamination": 0.14,
}


def _wafer_mask(size: int = IMAGE_SIZE, radius_ratio: float = 0.45) -> np.ndarray:
    """웨이퍼 원형 형상 마스크. 중심을 기준으로 원 내부=1, 외부=0."""
    center = (size - 1) / 2.0
    radius = radius_ratio * size
    yy, xx = np.mgrid[0:size, 0:size]
    dist = np.sqrt((xx - center) ** 2 + (yy - center) ** 2)
    return (dist <= radius).astype(np.float32)


def _random_line_points(size, rng, n_points):
    """이미지 내부를 지나는 임의의 꺾인 선 좌표 (n_points × 2)."""
    pts = np.stack(
        [rng.uniform(0, size, n_points), rng.uniform(0, size, n_points)], axis=1
    )
    return pts


def _draw_line(img, p0, p1, thickness=1.0, value=255.0, rng=None):
    """두 점 사이를 샘플링하며 두께(thickness)만큼 브러시로 칠한다."""
    x0, y0 = p0
    x1, y1 = p1
    dist = max(np.hypot(x1 - x0, y1 - y0), 1e-6)
    n_steps = max(int(dist * 2), 2)
    jitter = rng.uniform(-0.3, 0.3, n_steps) if rng is not None else 0
    for t in np.linspace(0, 1, n_steps):
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        if rng is not None:
            x += jitter[int(t * (n_steps - 1))]
            y += jitter[int(t * (n_steps - 1))] * 0.3
        x_min = int(max(0, round(x - thickness)))
        x_max = int(min(img.shape[1] - 1, round(x + thickness)))
        y_min = int(max(0, round(y - thickness)))
        y_max = int(min(img.shape[0] - 1, round(y + thickness)))
        img[y_min : y_max + 1, x_min : x_max + 1] = value
    return img


def _draw_circle(img, cx, cy, radius, value=255.0):
    y_min = max(0, int(round(cy - radius)))
    y_max = min(img.shape[0] - 1, int(round(cy + radius)))
    x_min = max(0, int(round(cx - radius)))
    x_max = min(img.shape[1] - 1, int(round(cx + radius)))
    yy, xx = np.mgrid[y_min : y_max + 1, x_min : x_max + 1]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    img[y_min : y_max + 1, x_min : x_max + 1] = np.where(
        dist <= radius, value, img[y_min : y_max + 1, x_min : x_max + 1]
    )
    return img


def _build_map(label: str, rng: np.random.Generator) -> np.ndarray:
    """클래스 라벨에 해당하는 웨이퍼맵 한 장을 만든다 (0~255 float)."""
    size = IMAGE_SIZE
    mask = _wafer_mask(size)
    img = np.zeros((size, size), dtype=np.float32)
    # 웨이퍼 내부는 미세 노이즈 (양품 셀 포함)
    img = np.where(mask > 0, rng.uniform(0, 15, (size, size)), img)

    if label == "normal":
        # 결함이 거의 없음 — 노이즈만 (드물게 1~2개 작은 점 허용)
        if rng.random() < 0.2:
            cx, cy = rng.uniform(6, size - 6, 2)
            _draw_circle(img, cx, cy, radius=rng.uniform(0.5, 1.2), value=255.0)

    elif label == "scratch":
        # 직선형 긁힘 1~2개
        for _ in range(rng.integers(1, 3)):
            pts = _random_line_points(size, rng, 2)
            _draw_line(img, pts[0], pts[1], thickness=rng.uniform(0.6, 1.4), value=255.0, rng=rng)

    elif label == "particle":
        # 산발적 이물질 점들
        for _ in range(rng.integers(3, 9)):
            cx, cy = rng.uniform(4, size - 4, 2)
            _draw_circle(img, cx, cy, radius=rng.uniform(0.4, 1.5), value=255.0)

    elif label == "crack":
        # 가는 꺾인 균열 (여러 선분)
        pts = _random_line_points(size, rng, rng.integers(3, 6))
        for i in range(len(pts) - 1):
            _draw_line(img, pts[i], pts[i + 1], thickness=0.4, value=255.0, rng=rng)

    elif label == "contamination":
        # 넓은 오염 영역 (반투명 얼룩)
        for _ in range(rng.integers(1, 3)):
            cx, cy = rng.uniform(8, size - 8, 2)
            radius = rng.uniform(3.5, 7.0)
            y_min = max(0, int(round(cy - radius)))
            y_max = min(size - 1, int(round(cy + radius)))
            x_min = max(0, int(round(cx - radius)))
            x_max = min(size - 1, int(round(cx + radius)))
            yy, xx = np.mgrid[y_min : y_max + 1, x_min : x_max + 1]
            dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
            strength = rng.uniform(0.25, 0.6)
            img[y_min : y_max + 1, x_min : x_max + 1] += np.where(
                dist <= radius, strength * 255.0, 0
            )

    # 외곽(웨이퍼 밖)은 0 유지, 클리핑
    img = np.clip(img, 0, 255)
    img = np.where(mask > 0, img, 0)
    return img


def generate_wafer_map(label: str, seed: int = None) -> np.ndarray:
    """단일 웨이퍼맵 생성. label: normal/scratch/particle/crack/contamination."""
    rng = np.random.default_rng(seed)
    return _build_map(label, rng)


def generate_synthetic_wafers(n_samples: int = 2000, seed: int = RANDOM_SEED) -> tuple[np.ndarray, np.ndarray]:
    """합성 웨이퍼맵 데이터 생성.

    반환:
        images : (n_samples, 32, 32) uint8 배열
        labels : (n_samples,) 문자열 라벨 배열
    """
    rng = np.random.default_rng(seed)
    images: list[np.ndarray] = []
    labels: list[str] = []
    for label, ratio in CLASS_RATIO.items():
        n = int(round(n_samples * ratio))
        for _ in range(n):
            img = _build_map(label, rng)
            images.append(img.astype(np.uint8))
            labels.append(label)

    idx = rng.permutation(len(images))
    images = np.stack(images)[idx]
    labels = np.asarray(labels)[idx]
    return images, labels


def generate_and_save(path: str, n_samples: int = 2000, seed: int = RANDOM_SEED) -> tuple[np.ndarray, np.ndarray]:
    """NPZ로 저장 + 분포를 출력한다."""
    images, labels = generate_synthetic_wafers(n_samples=n_samples, seed=seed)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path, images=images, labels=labels)
    print(f"생성 완료: {len(images)}장 -> {path}")
    dist = {lbl: float((labels == lbl).mean()) for lbl in CLASS_RATIO}
    for label, ratio in CLASS_RATIO.items():
        print(f"  {label:14s} {ratio:6.1%}  ({int((labels == label).sum())}장)")
    return images, labels


if __name__ == "__main__":
    generate_and_save("data/synthetic_wafer.npz")
