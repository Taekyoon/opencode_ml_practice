# B3. 평가 지표 — F1, ROC-AUC, PR-AUC 이해하기

## 학습 목표
- 혼동 행렬(confusion matrix)의 네 칸을 이해한다
- 정확도·정밀도·재현율·F1의 차이를 안다
- 불균형 데이터에서 왜 정확도가 오해를 주는지 본다

## 배경 지식

### 혼동 행렬 (Confusion Matrix)
예측과 실제의 2×2 조합:

| | 실제 합격(0) | 실제 불량(1) |
|---|---|---|
| **예측 합격(0)** | TN (정상으로 정상) | FN (불량을 놓침 ← 문제!) |
| **예측 불량(1)** | FP (과경고) | TP (불량을 제대로 잡음) |

- **FN(위음성)**: 불량인데 합격이라고 놓침 → **불량을 밖으로 보냄** → 비용 큼!
- **FP(위양성)**: 정상인데 불량이라고 과경고 → 재작업 비용 발생

> 반도체 공정에서 FN(불량을 합격으로 통과)은 고객 불량 = 가장 치명적이다.

### 지표 정의

| 지표 | 의미 | 계산 |
|------|------|------|
| **정확도** Accuracy | 전체 중 맞힌 비율 | (TP+TN)/전체 |
| **정밀도** Precision | 불량이라 한 것 중 실제 불량 | TP/(TP+FP) |
| **재현율(민감도)** Recall | 실제 불량 중 잡은 것 | TP/(TP+FN) |
| **F1** | 정밀도·재현율의 조화평균 | 2PR/(P+R) |

**핵심**: 정확도는 "불균형 데이터에서 거짓말쟁이"다.
이 데이터는 불량이 16.7%인데 전부 "합격"으로 예측해도 정확도 83.3%. 쓸데없는 모델이다.
그래서 불량을 얼마나 놓치는지 보여주는 **Recall**과, 잘못 지목이 많은지 보여주는 **Precision**을 함께 봐야 한다. F1은 둘을 하나로 요약한다.

### ROC-AUC와 PR-AUC
로지스틱 회귀는 확률을 출력한다. "p ≥ 0.5면 불량" 판정의 임계값을 움직이면 지표가 변한다.

- **ROC 커브**: 임계값을 바꿔가며 TPR vs FPR을 그린 것. AUC = 아래 면적(1에 가까울수록 좋음)
- **PR 커브**: Precision vs Recall. **불균형 데이터에서 ROC보다 "정답에 가까운" 커브** (불량 클래스가 드물 때 ROC-AUC가 과대평가되는 문제가 있음)

### 왜 최종 점수(score)가 F1 × PR-AUC인가?
불량(1)에 집중하면서, 임계값 변화에 강건(robust)한 지표를 쓰기 위함이다.
이 프로젝트의 분류 태스크 **score = F1 × PR-AUC** (모듈 B4, C에서 다시 본다).

## 따라하기

### 1단계: 평가 실행
```bash
python -m src.evaluation
```
터미널에 지표들이 출력되고 `plots/`에 4개 이미지가 저장된다.

### 2단계: 출력 해석
출력 예:
```
정확도(Accuracy)   : 0.9510 (95.1%)
정밀도(Precision)  : 0.8986 (89.9%)
재현율(Recall)     : 0.7964 (79.6%)   <- 불량의 80%를 잡음
F1-score           : 0.8444 (84.4%)
AUC-ROC            : 0.9862   <- 커브가 왼쪽 위로 치우쳤다
```
> 표기는 로지스틱 회귀 베이스라인 실측값 기준이다. 다른 환경에서 실행하면
> 수치가 조금씩 달라질 수 있으나, 아래 함정(16.7% 불균형에서 정확도 거짓말)은 같다.

### 3단계: 혼동 행렬 열기
```bash
open plots/confusion_matrix.png
```
이미지에서 아래를 확인한다:
- FN (실제 불량인데 합격으로 잘못 예측) 의 수가 몇 개인가?
- 이를 줄이려면 어떻게 해야 할까? (모듈 C에서 SMOTE·임계값 조정으로 시도)

### 4단계: 임계값의 중요성 체험
같은 모델이라도 판정 기준(임계값)을 바꾸면 Precision/Recall이 달라진다.
```bash
python - <<'PY'
import numpy as np
from src.preprocessing import load_data, preprocess
from src.model import split_data, train_logistic_regression
from sklearn.metrics import precision_score, recall_score

X, y, scaler = preprocess(load_data())
Xtr, Xte, ytr, yte = split_data(X, y)
model = train_logistic_regression(Xtr, ytr)
proba = model.predict_proba(Xte)[:, 1]

for t in [0.3, 0.5, 0.7]:
    pred = (proba >= t).astype(int)
    print(f"임계값 {t}: precision={precision_score(yte, pred):.3f} recall={recall_score(yte, pred):.3f}")
PY
```
임계값을 낮추면 불량을 더 잡지만(recall↑) 오탐(FP)이 늘고, 임계값을 올리면 정밀도가 올라가지만 불량을 놓친다(recall↓). **트레이드오프**를 직접 체험했다.

## 이해 확인

1. 불량 16.7% 데이터에서 정확도 83%인 모델이 반드시 나쁜가? 왜?
2. FN(놓침)과 FP(과경고) 중 반도체 공정에서 어느 쪽이 더 위험한가?
3. 임계값을 낮추면 precision과 recall은 각각 어떻게 변하는가?

## opencode에게 물어보세요

```
이 프로젝트에서 왜 score를 F1 × PR-AUC로 정의했는지
failure 예측의 비대칭 비용과 연결해서 설명해줘.
하이퍼파라미터로 임계값을 조정하면 이 score가 어떻게 변할까?
```

## 다음 레슨
[B4. 실험 기록](08_experiment_records.md) — 실험 결과를 연구 DB에 남긴다.