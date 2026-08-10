---
tags: [tasks, image_classification, anomaly_detection]
created: 2026-08-09
updated: 2026-08-09
task: wafer_vision
kind: classification
score_name: macro_f1 * pr_auc
dataset: wm811k
target: failureType
---

# wafer_vision — 웨이퍼맵 결함 분류/이상탐지 발견사항

> 반도체 웨이퍼맵(32×32 그레이스케일)에서 결함 패턴을 판별한다.
> 합성 데이터(synthetic)와 공개 데이터셋 WM-811K 를 모두 지원한다.
> 이 페이지는 실험에서 얻은 발견을 누적 기록한다.

## 현재 최고 결과

| run_id | score (F1×PR-AUC) | macro-F1 | PR-AUC | ROC-AUC(anomaly) | 데이터 |
|--------|--------------------|----------|--------|------------------|--------|
| run_20260810_090050 | **0.8357** | — | 0.9416 | 2026-08-10 (자동 기록) |
| run_20260809_145944 | **0.2369** | 0.4516 | 0.5246 | 0.7852 | **WM-811K 실데이터** |
| (이전) | **0.8357** | 0.8875 | 0.9416 | 0.9975 | 합성 (synthetic) |

> **관찰**: WM-811K 실데이터는 합성보다 훨씬 어렵다. 라벨 불균형(noise≈85%)과
> 유사 패턴(Loc/Edge-Loc, Scratch) 탓에 macro-F1이 크게 낮다. 이건 **첫 실데이터
> 실행**이며, feature 파이프라인/모델 튜닝 여지가 크다.

## 실행 이력

| run_id | score | 데이터 | 비고 |
|--------|-------|--------|------|
| run_20260809_145944 | 0.2369 | WM-811K | 실데이터 공식 train/test split, RF |
| run_20260714 (모임) | 0.5571 | WM-811K 모임 | 실데이터 로드 전 모임 검증 |
| (이전 합성) | 0.8357 | 합성 | feature 파이프라인 검증 |

## 발견 사항

- **WM-811K 로더**: 공식 pickle은 컬럼 `waferMap/dieSize/lotName/waferIndex/trianTestLabel/failureType`이고,
  `failureType`·`triaInTestLabel` 값이 `[['none']]`처럼 중첩 배열로 저장되어 있다.
  `_as_label()`로 단일 값으로 펼쳐야 한다. 공식 train/test split(`trianTestLabel`)을
  사용하면 `use_trian_split=True` 로 5-튜플 `(X_tr, y_tr, X_te, y_te, info)`를 돌려받는다.
- **공식 split이 랜덤 split보다 정답**: test 셋에만 있는 클래스 분포 붙어 있음. `Center` 등
  소수 클래스는 train/test 분포가 극단적으로 갈려 평가가 엄격함.
- **클래스 불균형**: `none`(정상)이 라벨 행 85% 차지. 분류에서는 인기치 못한 `Loc`/`Scratch`/
  `Edge-Loc` pr=0.05~0.10 수준 — 샘플별 결함 지향한 feature 가 더 필요함.
- **anomaly 태스크**: 정상 `none`만 학습한 IsolationForest ROC-AUC 0.785. 분류보다 강건하지만
  결함 사이즈/위치 다변화에는 한계.

## 시도하지 않은 것 / 다음 후보

- [ ] 클래스 불균형 대응 (class_weight, SMOTE, 클래스별 오버샘플링)
- [ ] 특징 확장: HOG, 주파수(G職業/2D FFT) 도메인, 결함 밀도/중심통계
- [ ] LogisticRegression/GradientBoosting 모델 비교 → [techniques/model_comparison.md](../techniques/model_comparison.md)
- [ ] `none` 행 제외하고 결함 클래스만으로 분류(불균형 줄이기)
- [ ] 64×64 리사이즈 등 해상도 스윕

## 교차 참조

- [datasets/wm811k.md](../datasets/wm811k.md) — 데이터셋 분포/주의사항
- [techniques/anomaly_detection.md](../techniques/anomaly_detection.md) — 이상탐지 기법