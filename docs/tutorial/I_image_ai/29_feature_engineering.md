# I2. 특징 공학 — 이미지에서 "가치 있는 숫자" 뽑아내기

> B8에서는 웨이퍼맵 → 특징 벡터 변환이 이미 `src/image_processing.py`에 구현된
> 상태였다. 이 레슨에서는 그 특징이 **왜** 그런 구성인지 뜯어보고, 직접 바꿔 보며
> 성능이 어떻게 변하는지 관찰한다.

## 학습 목표
- flatten / PCA / 그래디언트 / 방사 프로파일 각각이 "무엇을 보는지" 이해한다
- 특징 파이프라인 설정을 바꾸며 `score` 변화를 A/B로 비교한다
- 특징 공학이란 "모델에게 어떻게 보게 할지 설계"하는 것임을 안다

## 배경 지식

### 특징 공학(feature engineering)이란
ML은 원본 픽셀을 그대로 쓰기보다, **문제에 맞는 숫자 표현**을 만드는 편이 낫다.
"어떻게 보게 할지"를 설계하는 것이 특징 공학이다. `image_processing.py`는
웨이퍼맵 문제에 맞는 특징 3가지를 조합한다.

| 특징 | 차원 | 보는 것 | 어떤 결함에 유리한가 |
|------|------|---------|--------------------|
| flatten → PCA | 50 | 전체 밝기 구조 (압축) | 전반적 형태 |
| 그래디언트 | 96 | 밝기가 **바뀌는 정도** | 스크래치·크랙 (선) |
| 방사 프로파일 | 8 | 반지름별 평균 밝기 | Edge-Ring (원형) |

- **그래디언트** = "옆 픽셀과 얼마나 다른가". 밋밋한 곳은 0, 선은 큰 값.
  → 직선형 결함을 "총 변화량의 분포"로 본다.
- **방사 프로파일** = 중심에서 거리별로 평균을 낸 값.
  → 가장자리에 집중된 결함(Edge-Ring)은 반지름이 큰 쪽의 밝기가 높아진다.

### 러너에서 이들을 조절하는 법
`get_config()`의 `feature` dict:

```python
"feature": {
    "pca_components": 50,   # PCA 차원 수
    "use_gradient": True,   # 그래디언트 포함 여부
    "radial_bins": 8,       # 방사 프로파일 구간 수
},
```

## 따라하기

### 1단계: 플랜 (baseline 기록)
현재 설정의 score를 먼저 저장한다 (A/B 비교 기준):
```bash
python - <<'PY'
from research.wafer_vision.experiment_runner import get_config, run_experiment
r = run_experiment(get_config())
print("baseline score:", r["score"], "| n_features:", r["metrics"]["n_features"])
PY
```

### 2단계: 빌드 (한 변수씩 바꿔 실행)
**A/B 원칙: 한 번에 하나만.** 그래디언트를 끄면 어떻게 될까?
```bash
python - <<'PY'
from research.wafer_vision.experiment_runner import get_config, run_experiment
c = get_config()
c["feature"]["use_gradient"] = False
r = run_experiment(c)
print("no-gradient score:", r["score"], "| n_features:", r["metrics"]["n_features"])
PY
```

방사 프로파일 구간 수를 늘려 보자:
```bash
python - <<'PY'
from research.wafer_vision.experiment_runner import get_config, run_experiment
c = get_config()
c["feature"]["radial_bins"] = 16
r = run_experiment(c)
print("radial=16 score:", r["score"], "| n_features:", r["metrics"]["n_features"])
PY
```

### 3단계: 검증 (해석)
예상되는 결과의 예:
- 그래디언트를 끄면 **scratch/crack 구분이 나빠진다** (선형 결함 정보 소실)
- 방사 구간을 늘려도 합성 데이터에서는 거의 안 바뀐다 (패턴이 이미 단순함)

| 설정 | 기대 방향 |
|------|----------|
| baseline | 참고점 |
| `use_gradient=False` | 성능 하락 (선형 특징 소실) |
| `radial_bins=16` | 크게는 안 변함 or 소폭 변화 |

> 중요한 것은 "어떤 특징이 어떤 결함에 기여하는가"를 보는 눈이다.
> 실제 WM-811K에서는 Edge-Ring처럼 방사 특징이 결정적인 클래스가 있다.

## 이해 확인
1. 그래디언트 특징이 스크래치·크랙에 특히 유용한 이유는?
2. 방사 프로파일이 Edge-Ring(가장자리 결함)에 유용한 이유는?
3. PCA를 "무조건 켜는 것"이 항상 좋을까? (차원 축소의 장단점)

## opencode에게 물어보세요

```
image_processing.py의 feature_pipeline을 보고,
pca_components, use_gradient, radial_bins 각각을 바꿔가며
score가 어떻게 변하는지 실험 결과를 한글로 정리해줘.
```

## 다음 레슨
[I3. 나만의 비전 태스크](../I_image_ai/30_own_vision_task.md)