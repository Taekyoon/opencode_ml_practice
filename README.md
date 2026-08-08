# 반도체 제조 제품 Failure 예측 모델

반도체 실험실 공정/측정 수치 데이터에서 제품 failure 여부를 예측하는 로지스틱 회귀 분류 모델입니다.

> 저장소: [`Taekyoon/opencode_ml_practice`](https://github.com/Taekyoon/opencode_ml_practice)

## 프로젝트 구조

```
opencode_ml_practice/
├── data/
│   └── synthetic_data.csv      # 가상 반도체 공정 데이터 (5,000행)
├── plots/
│   ├── confusion_matrix.png           # 혼동 행렬
│   ├── roc_curve.png                 # ROC 커브
│   ├── precision_recall_curve.png    # PR 커브
│   └── feature_coefficients.png       # 특성 계수
├── src/
│   ├── data_generation.py    # 가상 데이터 생성
│   ├── preprocessing.py      # 결측치/스케일링 전처리
│   ├── model.py              # 로지스틱 회귀 학습
│   └── evaluation.py          # 평가 및 시각화
├── notebooks/               # Jupyter 분석 노트북
├── requirements.txt
└── README.md
```

## 실행 방법

```bash
# 1. 의존 설치
pip install -r requirements.txt

# 2. 가상 데이터 생성 (data/synthetic_data.csv)
python -m src.data_generation

# 3. 전처리 확인
python -m src.preprocessing

# 4. 모델 학습 (계수 확인)
python -m src.model

# 5. 평가 및 시각화 (plots/ 폴더에 차트 저장)
python -m src.evaluation
```

## 특징

- **데이터**: 공정 변수(온도, 압력, 공정시간, 화학농도) + 측정 변수(두께, 비저항, 도핑농도)
- **불량률**: 약 16.7% (불량 837 / 합격 4163)
- **모델**: 로지스틱 회귀 (L2 정규화)
- **전처리**: 중앙값 결측치 대체, 표준화(StandardScaler)

## 기준 결과 (데모 데이터셋)

| 지표 | 값 |
|------|------|
| Accuracy | 95.1% |
| Precision | 89.9% |
| Recall | 79.6% |
| F1-score | 84.4% |
| AUC-ROC | 0.986 |

> 실제 반도체 데이터를 적용하면 특성 공학(공정 순서, 시간 시퀀스 등)과 도메인 지식 기반 특성 선택이 필요합니다.