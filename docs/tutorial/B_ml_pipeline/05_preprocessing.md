# B1. 전처리 — 결측치와 스케일링

## 학습 목표
- 현실 데이터에 결측치가 생기는 이유를 안다
- 결측치 대체와 표준화(스케일링)의 의미를 이해한다
- `src/preprocessing.py`의 각 함수를 실제로 실행해본다

## 배경 지식: 왜 전처리가 필요한가?

### 결측치 (Missing Value)
실제 공정 데이터는 완벽하지 않다. 센서가 고장나거나 통신이 끊기면 측정값이 비게 된다.
모델은 `NaN`(비어 있는 값)을 계산할 수 없으므로, **대체(fill)** 해야 한다.
가장 흔한 방법 중 하나는 **중앙값(median) 대체**다.

> 이 프로젝트의 `add_synthetic_missing()`은 가상 데이터에 일부러 결측치를 넣어
> 현실적인 상황을 재현한다. (센서 오류 모사)

### 스케일링 (Scaling)
`temperature`(20~300)와 `pressure`(1~10)는 단위가 달라 값의 크기가 다르다.
로지스틱 회귀는 계수와 곱해서 계산하므로, **큰 값을 가진 변수가 지나치게 영향력이 커**진다.
**표준화(StandardScaler)**는 각 열을 "평균 0, 표준편차 1"로 만들어 공정하게 만든다.

```
x_scaled = (x - 평균) / 표준편차
```

## 따라하기

### 1단계: 전처리 파이프라인 전체 실행
```bash
python -m src.preprocessing
```
출력 예:
```
데이터 로드: 5000행, 8열
결측치 처리: 991 -> 0
전처리 완료: X (5000, 7), y 불량 비율 16.7%
```

### 2단계: 함수를 하나씩 호출해보기
```bash
python - <<'PY'
from src.preprocessing import load_data, add_synthetic_missing, fill_missing, scale_features

df = load_data()
print("원본 결측치:", df.isna().sum().sum())

df_missing = add_synthetic_missing(df, missing_rate=0.05)
print("결측 주입 후:", df_missing.isna().sum().to_dict())

df_filled = fill_missing(df_missing)
print("대체 후:", df_filled.isna().sum().sum())
PY
```

### 3단계: 스케일링 전/후 비교
```bash
python - <<'PY'
import pandas as pd
from src.preprocessing import load_data, scale_features

df = load_data()
X, _ = scale_features(df.drop(columns=["failure"]))
print("원본 temperature 평균/표준편차:")
print(df["temperature"].mean().round(2), df["temperature"].std().round(2))
print("스케일된 temperature 평균/표준편차:")
print(X["temperature"].mean().round(4), X["temperature"].std().round(4))
PY
```
표준화 후 평균이 0, 표준편차가 1에 가까워지는 것을 확인한다.

## 이해 확인

1. 왜 결측치를 처리해야 하는가? 대체하지 않으면 어떻게 되나?
2. 스케일링을 하지 않으면 어떤 변수가 문제가 되는가? (온도 vs 압력)
3. `fill_missing`이 평균이 아니라 중앙값을 쓰는 이유는 무엇일까? (힌트: 이상치)

## opencode에게 물어보세요

```
src/preprocessing.py의 missing rate를 0.05에서 0.2로 올리면 어떤 일이 일어날지 예측해봐.
그리고 experiment에 미칠 영향을 설명해줘.
```

## 다음 레슨
[B2. 모델 학습](06_model_training.md) — 전처리한 데이터로 모델을 학습한다.