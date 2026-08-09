# I1. 이상탐지 — 정상품만 배우고 비정상을 찾는 법

> 모듈 I(이미지 AI) 시작. B7/B8에서 만든 **분류**와는 달리, 이 레슨에서는
> "정상 데이터만 학습해서 비정상을 가려내는" **이상탐지(anomaly detection)** 를
> 배운다.

## 학습 목표
- 분류(classification)와 이상탐지(anomaly detection)의 차이를 이해한다
- `wafer_vision` 러너의 `task: "anomaly"` 모드를 실행해 ROC-AUC를 확인한다
- "불량 데이터가 드문" 실전 상황에서 이상탐지가 왜 유용한지 안다

## 배경 지식

### 분류 vs 이상탐지

| 비교 | 분류 (B8) | 이상탐지 (이번 레슨) |
|------|----------|---------------------|
| 학습 데이터 | 결함 유형별 라벨 | 정상 라벨만 |
| 질문 | "어느 클래스인가?" | "정상인가?" |
| 새로운 불량 유형 | 틀리기 쉬움 | 잡아낼 수 있음 |
| 대표 지표 | F1 × PR-AUC | ROC-AUC |

### 실제 공정에서 왜 이상탐지가 필요한가
웨이퍼 공정에서는 **불량 발생이 매우 드물다**. 1,000장 중 몇 장 수준이다.
그런데 분류기는 불량이 충분히 있어야 학습되기 때문에:

1. 불량 데이터 수집이 어렵다 (클래스 불균형)
2. 공정이 바뀌면 **새로운 불량 유형**이 생기는데, 분류기는 그것을 "모른다"
3. 정상 데이터는 워낙 많아서 "정상이 어떤 것인가"는 잘 배울 수 있다

그래서 **정상 데이터만 학습 → 정상에서 멀어진 것을 이상으로 판단**하는
이상탐지가 실전에서 견고하다.

### 정상 클래스의 기준
`wafer_vision` 러너는 이상탐지 시 정상 클래스를 자동으로 고른다.
- 합성 데이터: `normal`
- WM-811K: `none` (라벨 없는 정상 웨이퍼)

정상만으로 모델을 `fit` 하고, 테스트에서 "정상/비정상" 이진으로 ROC-AUC를 계산한다.

## 따라하기

### 1단계: 플랜 (anomaly 모드 실행)
러너의 `task`를 `anomaly`로 바꿔 실행한다:
```bash
python - <<'PY'
from research.wafer_vision.experiment_runner import get_config, run_experiment

c = get_config()
c["task"] = "anomaly"
r = run_experiment(c)
m = r["metrics"]
print("분류 score:", r["score"])
print("anomaly ROC-AUC:", m["anomaly_roc_auc"], "(ref:", m["anomaly_ref_class"], ")")
PY
```
`metrics["anomaly_roc_auc"]` 값이 핵심이다.

### 2단계: 빌드 (분류 점수와 나란히 비교)
```bash
python - <<'PY'
from research.wafer_vision.experiment_runner import get_config, run_experiment
c = get_config()
c["task"] = "classification"
r = run_experiment(c)
print("분류 score:", r["score"])
print("anomaly ROC-AUC:", r["metrics"]["anomaly_roc_auc"])
PY
```

### 3단계: 검증 (해석)
합성 데이터는 정상 패턴이 균일해서 **anomaly ROC-AUC가 0.99+**로 나온다.
"정상이 대략 어떤 모양인지"를 배우면 거의 다 걸러낸다는 뜻이다.

**하지만** 이 값이 지나치게 높다는 것 자체가 합성 데이터의 한계다.
실제 WM-811K는 정상(none)의 분포가 훨씬 넓고 밝기/해상도 편차가 커서
ROC-AUC가 낮아질 수 있다.

### (선택) 4단계: 이상탐지 모델 교체
`anomaly_model`을 바꿔 보며 차이를 확인한다:
```bash
python - <<'PY'
from research.wafer_vision.experiment_runner import get_config, run_experiment
for m in ["isolation_forest", "one_class_svm"]:
    c = get_config()
    c["task"] = "anomaly"
    c["anomaly_model"] = m
    r = run_experiment(c)
    print(m, "ROC-AUC:", r["metrics"]["anomaly_roc_auc"])
PY
```

> one_class_svm은 데이터가 클수록 오래 걸릴 수 있다.

## 이해 확인
1. 분류와 이상탐지가 "학습 데이터" 측면에서 어떻게 다른가?
2. 이상탐지가 정상 데이터만 배우는데도 새 불량 유형을 잡을 수 있는 이유는?
3. ROC-AUC = 0.5 라면 성능은? 0.99 라면?

## opencode에게 물어보세요

```
wafer_vision 러너를 task: anomaly 모드로 실행했다.
ROC-AUC가 0.99로 나왔는데, 이게 분류 점수와 어떻게 다른 의미지?
metrics를 읽고 해석해줘.
```

## 다음 레슨
[I2. 특징 공학](../I_image_ai/29_feature_engineering.md)