# wafer_vision — 자율 연구 지침서

> 반도체 웨이퍼맵 이미지 분석 태스크. 32×32 그레이스케일 웨이퍼맵에서 결함 패턴을
> 판별한다.
> - 데이터셋: `synthetic`(합성 웨이퍼맵 2,000장) / `wm811k`(WM-811K 공개 데이터셋)
> - 목표 변수: `labels`  (normal / scratch / particle / crack / contamination)
> - 태스크 종류: **이미지 분류** (+ 선택적 이상탐지)

## 1. 배경

공정 검사에서 웨이퍼를 촬영하면, 개별 칩(die)의 양품/불량이 2차원 지도로 나타난다.
결함은 단독 불량보다 **스크래치·크랙·오염처럼 뚜렷한 패턴으로 군집**해서 나타나는
경우가 많다. 이 태스크는 **웨이퍼맵을 보고 결함 패턴을 분류**하는 모델을 만든다.
분류 기술을 이미지 입력에 적용하는 전체 파이프라인을 경험한다.

## 2. 데이터 성격

- **synthetic**: `src/generate_wafer_images.py` 가 합성 생성. 원형 웨이퍼 마스크 +
  클래스별 결함 템플릿. 균형 분포(normal 50%)이고 `data/synthetic_wafer.npz` 에 저장.
- **wm811k**: TSMC가 공개한 실제 웨이퍼맵 데이터셋(811K장). 수동 라벨 172,950장 중
  결함 유형(Center/Donut/Edge-Loc/Edge-Ring/Loc/Random/Scratch/Near-full)과
  "none"(정상)이 있다. 이상탐지 시 정상 클래스는 `none` 이다.
  - `data/WM811K/LSWMD_891.pkl` 을 Kaggle 에서 받고, `src/wafer_data_loader.py` 가
    32×32 uint8 로 정규화한다.

## 3. 평가 지표

- **분류 (기본)**: `score = F1(macro) × PR-AUC(macro)` — 여러 결함 유형을 동시에
  맞추는 종합 점수.
- **이상탐지 (선택)**: 정상(normal/none) 클래스 를 기준으로 한 ROC-AUC. "모델이
  뭘 모르는지"를 이진으로 보는 관점.

## 4. 특징 파이프라인 (이미지 → 수치)

`flatten(1024) → PCA(50) + 그래디언트(96) + 방사 프로파일(8)` = **154차원**

- **PCA**: 상관된 픽셀을 압축해 노이즈를 제거
- **그래디언트**: 픽셀 값 변화량의 히스토그램 — 선형 결함(스크래치/크랙) 검출
- **방사 프로파일**: 중심에서 반지름별 평균 밝기 — 원형 패턴(Edge-Ring 등) 검출

train 에서만 PCA fit, test/예측은 transform 만 (데이터 누수 방지).

## 5. 반복 전략 (A/B 원칙)

1. 과거 결과 먼저 확인 (`research/wafer_vision/results/`)
2. 한 번에 하나의 변수만 변경
   (모델 유형, pca_components, use_gradient, radial_bins)
3. 개선되면 keep, 아니면 되돌리기
4. 분류가 안정되면 `task:"anomaly"` 로 전환해 이상탐지 ROC-AUC 도 확보한다.

## 6. 실행

- 로컬: `python research/wafer_vision/experiment_runner.py`
- 합성 데이터 생성: `python src/generate_wafer_images.py`
- WM-811K 사용: `data/WM811K/LSWMD_891.pkl` 준비 후 `data_source: "wm811k"` 로 변경
- Airflow: 연구 에이전트가 자동 실행