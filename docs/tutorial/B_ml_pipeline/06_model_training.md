# B2. 모델 학습 — 로지스틱 회귀와 train/test 분할

## 학습 목표
- 로지스틱 회귀가 분류 문제에서 어떻게 작동하는지 이해한다
- train/test 분할이 왜 필요한지 안다
- `src/model.py`를 실행해 모델을 학습한다

## 배경 지식

### 분류 vs 회귀
| | 회귀 (Regression) | 분류 (Classification) |
|---|---|---|
| 예측값 | 숫자 (연속) | 범주 (0/1 등) |
| 예 | 수율(%) 예측 | 불량 여부 예측 |
| 지표 | R² | F1, 정확도 |

우리의 태스크는 **불량(failure) 여부**를 맞히는 문제이므로 **분류**다.

### 로지스틱 회귀
이름에 "회귀"가 있지만 **분류 모델**이다.

```
p = 1 / (1 + e^(-(w·x + b)))
```

- 입력 변수 x에 가중치 w를 곱해 합산 → **logit**
- 시그모이드로 0~1 사이 확률 p로 변환
- p ≥ 0.5(임계값)면 불량(1), 아니면 합격(0)으로 판정

A3에서 봤던 데이터 생성의 logit 계산과 **같은 원리**다. 데이터를 만든 사람이 "온도↑·압력↓이면 불량" 규칙을 심었으니, 로지스틱 회귀가 그 규칙을 학습할 수 있다.

### train/test 분할
모델이 **문제를 외우는 것**(과적합, overfitting)을 막기 위해 데이터를 둘로 나눈다.

- **train**: 모델이 학습하는 데이터 (80%)
- **test**: 학습에 안 쓴 데이터로 실력 측정 (20%)

> `stratify=y`: train/test 양쪽의 불량 비율이 원본과 같도록 유지한다.
> 불량이 16.7%인데 우연히 train에만 다 몰리면 학습이 왜곡된다.

## 따라하기

### 1단계: 분할 함수 확인
`src/model.py`의 `split_data()`를 읽는다.
```bash
python -c "import inspect, src.model as m; print(inspect.getsource(m.split_data))"
```
`stratify=y, random_state=42`를 확인한다. random_state를 고정해야 **같은 결과가 재현**된다.

### 2단계: 전처리 → 분할 → 학습 전체 실행
```bash
python -m src.model
```
출력 예:
```
데이터 로드: 5000행, 8열
결측치 처리: 991 -> 0
전처리 완료: X (5000, 7), y 불량 비율 16.7%
데이터 분할: train 4000 / test 1000
  train 불량률: 16.7%, test 불량률: 16.7%
모델 학습 완료 (정규화 강도 C=1.0)
학습된 계수:
  temperature: 0.XXXX
  pressure: -0.XXXX
  ...
```

### 3단계: 계수의 의미 읽기
`temperature`의 계수가 **양수**라면 온도가 높을수록 불량 확률이 올라간다.
`pressure`의 계수가 **음수**라면 압력이 낮을수록 불량이다.
→ A3에서 확인한 데이터 생성 규칙과 방향이 일치하는지 비교한다.

### 4단계: 직접 변형해보기 (C 값)
`C`는 정규화 강도의 역수다. C를 작게 하면 계수가 0에 수렴하려 한다.
```bash
python - <<'PY'
from src.model import split_data, train_logistic_regression
from src.preprocessing import load_data, preprocess

X, y, scaler = preprocess(load_data())
X_train, X_test, y_train, y_test = split_data(X, y)
for C in [0.01, 1.0, 100.0]:
    model = train_logistic_regression(X_train, y_train, C=C)
    print(f"  C={C}: 계수 합({sum(abs(c) for c in model.coef_[0]):.3f})")
PY
```
C가 클수록 계수가 커지는 것을 관찰한다.

## 이해 확인

1. 왜 test 데이터는 학습에 절대 사용하면 안 되는가?
2. `stratify=y`가 필요한 이유는?
3. 계수가 양수/음수라는 것이 무슨 의미인가?

## opencode에게 물어보세요

```
temperature 계수가 양수인 이유를 data_generation.py의 logit 공식과 연결지어 설명해줘.
```

## 다음 레슨
[B3. 평가 지표](07_evaluation_metrics.md) — 모델이 얼마나 잘 맞히는지 측정한다.