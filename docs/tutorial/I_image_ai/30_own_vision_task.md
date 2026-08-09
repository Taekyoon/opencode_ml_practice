# I3. 나만의 비전 태스크 — 모듈 I 종합

> 모듈 I(이미지 AI) 마무리. 지금까지 배운 wafer_vision 파이프라인을 바탕으로
> **나만의 이미지 태스크**를 만들어 본다.

## 학습 목표
- B7/B8/I1/I2 에서 배운 것을 하나의 태스크로 종합한다
- `scripts/new_task.py` 스캐폴드로 나만의 태스크를 만든다
- 분류와 이상탐지를 함께 구성하는 자유 과제를 완성한다

## 배경 지식: 이미지 태스크의 구성 요소

wafer_vision 을 예로 보면 이미지 태스크는 4개의 요소로 이뤄진다:

| 구성 요소 | 역할 |
|-----------|------|
| `src/generate_wafer_images.py` | 합성 데이터 생성 (이미지·라벨) |
| `src/image_processing.py` | 이미지 → 특징 벡터 (flatten/PCA/그래디언트/방사) |
| `research/<task>/experiment_runner.py` | 학습·평가 파이프라인 |
| `research/tasks_registry.py` | 태스크 등록 (DAG 인식) |

나만의 태스크는 **이 중 하나만 바꿔도** 새 문제가 된다:
1. **데이터**: 다른 도메인의 이미지 (PCB 패턴, 배관 촬영 등)
2. **특징**: 새 도메인에 맞는 특징 추가/변경
3. **평가**: 분류 + 이상탐지 이중 구성

## 따라하기

### 1단계: 플랜 (자유 과제 고르기 — 셋 중 하나)
- **A. 새 이미지 도메인**: PCB/배관 등 도메인을 가정한 합성 이미지 생성기를
  `generate_wafer_images.py`를 참고해 만든다.
- **B. 클래스 확장**: 웨이퍼맵에 `Edge-Ring`(가장자리 결함)를 추가해 6클래스 분류를
  시도한다.
- **C. WM-811K 실데이터**: Kaggle에서 받은 `data/WM811K/LSWMD_891.pkl`로
  `data_source: "wm811k"` 실태 분류를 실행한다.

### 2단계: 빌드 (스캐폴드 실행)
스캐폴드는 `failure_prediction`처럼 이미 등록된 dataset 기반이다. 이미지 태스크의
경우 runner 에서 `src.image_processing` 를 import 해 붙인다:
```bash
python scripts/new_task.py my_vision --dataset your_dataset --target label --note "내 비전 태스크"
```
성공 시 `research/my_vision/` 에 runner·program·results/ 가 생성된다.

### 3단계: 빌드 (이미지 파이프라인 연결)
생성된 `experiment_runner.py`에 이미지 처리 3줄을 이어붙여 이미지를 특징으로 바꾼다:
```python
from src.image_processing import feature_pipeline, transform_features
X_tr, pca = feature_pipeline(train_images)
X_te = transform_features(test_images, pca)
```

### 4단계: 검증
```bash
python research/my_vision/experiment_runner.py
```
score/metric으로 분류가 동작하는지 확인하고, 이상탐지까지 붙이고 싶으면
wafer_vision 의 `task:"anomaly"` 방식을 참고한다.

## 이해 확인
1. wafer_vision 을 스캐폴드로 다시 만든다면 뭐가 생성되고 뭐가 달라지나?
2. "데이터 / 특징 / 평가" 중 하나만 바꾸는 것만으로 새 과제가 되는 까닭은?
3. I1에서 배운 "정상만 학습하는 이상탐지"와 이번 분류를 함께 쓴다면 어떻게 쓰면 좋을까?

## opencode에게 물어보세요

```
scripts/new_task.py 의 --help 를 보고, 지금 선택한 자유 과제에 맞는
데이터셋과 target 을 정해 스캐폴드 명령을 구성해줘. 실행 결과도 안내해줘.
```

## 다음 레슨
모듈 I 완료 — 이 프로젝트의 다른 모듈([C. 실험 runner](../C_research_framework/11_experiment_runner.md),
[G. 가드레일](../G_ai_safety/22_prompt_guards.md))로 이어서 학습할 수 있다.