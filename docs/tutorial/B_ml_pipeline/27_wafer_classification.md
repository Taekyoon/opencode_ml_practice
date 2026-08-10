# B8. 이미지 분류 — 웨이퍼맵을 특징 벡터로, 그리고 분류기로

## 학습 목표
- 이미지 픽셀을 어떻게 "숫자 벡터"로 바꾸는지(flatten + PCA) 이해한다
- 그래디언트/방사 프로파일 같은 특징이 왜 필요한지 안다
- `wafer_vision` 러너를 실행하고 결과를 해석한다

## 배경 지식

### 이미지 → 벡터: 평탄화(flatten)
ML은 숫자만 계산한다. 32×32 이미지를 모델에 넣으려면 1차원 벡터로 만들어야 한다.
가장 단순한 방법은 각 픽셀 값을 한 줄로 나열하는 **평탄화(flatten)** 다.

```
(32, 32)  →  reshape  →  (1024,)
```

이러면 1,024차원이 된다. 그런데 픽셀끼리는 서로 상관관계가 크다(붙어 있는 픽셀은
보통 비슷). 고차원을 그대로 쓰면 노이즈에 약하고 계산량이 커진다.

### 차원 축소: PCA
**PCA(주성분 분석)** 는 상관된 픽셀들을 "가장 분산이 큰 방향" 몇 개로 압축한다.
- 1,024차원 → **50차원**
- 노이즈가 줄고, 선형 모델도 잘 작동한다

### 결함에게 유리한 특징
PCA만으로는 미묘한 패턴이 지워질 수 있다. 그래서 두 가지를 더 쓴다.

| 특징 | 차원 | 잡는 것 |
|------|------|---------|
| 그래디언트 | 96 | 픽셀 값이 바뀌는 정도의 히스토그램 → 스크래치/크랙 같은 **선** |
| 방사 프로파일 | 8 | 중심에서 반지름별 평균 밝기 → Edge-Ring 같은 **원형** |

합치면 50 + 96 + 8 = **154차원**이 된다. 이 변환은 `src/image_processing.py`에 있다.

### wafer_vision 태스크
`research/wafer_vision/` 폴더에 웨이퍼맵 분류용 단일 파이프라인이 있다.
- `experiment_runner.py`: 같은 파이프라인 → 학습/평가 (합성 or WM-811K)
- `program.md`: 연구 지침서
- `predict.py`: 학습된 모델로 새 웨이퍼맵 예측

> **특징 파이프라인은 train에서만 fit 한다.** PCA는 학습 데이터에서 계산해야
> 테스트/예측에서 "미래 정보"가 새지 않는다 (데이터 누수 방지).

## 따라하기

### 1단계: 플랜 (파일 확인)
```bash
ls research/wafer_vision/
ls data/synthetic_wafer.npz
```

### 2단계: 빌드 (러너 실행)
```bash
python research/wafer_vision/experiment_runner.py
```
results/ 새 폴더에 `metrics.json` + `runner_snapshot.py`가 생긴다.
모델 pickle은 `models/latest_wafer.pkl`에 저장된다 (predict.py가 사용).

### 3단계: 검증 (지표 해석)
```bash
python - <<'PY'
import glob, json
path = sorted(glob.glob("research/wafer_vision/results/run_*/metrics.json"))[-1]
d = json.load(open(path))
m = d["metrics"]
print("score(F1×PR-AUC):", d["score"])
print("accuracy:", m["accuracy"], "| macro_f1", m["macro_f1"], "| pr_auc", m["pr_auc"])
print("이상탐지 ROC-AUC:", m["anomaly_roc_auc"])
print("클래스별 F1:", {k: v["f1"] for k, v in m["per_class"].items()})
PY
```

눈여겨 볼 것:
- **클래스별 F1 편차**: contamination은 잘 맞지만 scratch·crack이 상대적으로 낮다
  (둘 다 "선"이라 겹치기 때문).
- **anomaly ROC-AUC(≈0.99+)**: 정상만 학습한 이상탐지도 결함을 잘 가려낸다.

> 이것이 합성 데이터의 장점이자 한계다. 패턴이 뚜렷해서 점수가 높게 나오지만,
> 실제 WM-811K는 해상도/밝기 편차가 커서 성능이 달라진다.

### 4단계: WM-811K로 전환 (선택)
실제 데이터를 준비했다면 `data_source`를 바꿔 재실행한다:
```bash
python - <<'PY'
import json, copy
from research.wafer_vision.experiment_runner import get_config, run_experiment

c = get_config()
c["data_source"] = "wm811k"   # data/WM811K/LSWMD_891.pkl 필요
r = run_experiment(c)
print("score:", r["score"], "| macro_f1", r["metrics"]["macro_f1"])
PY
```

## 이해 확인
1. flatten(1024)를 PCA(50)로 줄이는 이유는 무엇일까?
2. train과 test를 나눈 후 PCA를 어느 쪽에 fit해야 할까? 그 이유는?
3. anomaly ROC-AUC가 높게 나오는 것을 보고 이를 "실전 검사에서 거부"에 어떻게 쓸 수 있을까?

## opencode에게 물어보세요

```
research/wafer_vision/results/의 가장 최근 metrics.json을 읽고,
클래스별 F1을 비교해서 왜 scratch가 crack보다 낮은지 추정해줘.
```

## 다음 레슨
모듈 C: [실험 runner 들여다보기](../C_research_framework/11_experiment_runner.md) —
이미지든 수치든 같은 프레임워크로 실험을 관리한다. (이미지 심화는 수료 후 **모듈 I**에서
이어간다: [I1. 이상 탐지](../I_image_ai/28_anomaly_detection.md))