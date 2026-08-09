---
tags: [technique, anomaly_detection]
created: 2026-08-09
updated: 2026-08-09
---

# 이상탐지(Anomaly Detection)

> 정상 클래스만 학습해 비정상(결함)을 가려내는 접근. wafer_vision 의 선택 평가 항목.

## 적용 사례

### wafer_vision (WM-811K, 2026-08-09)

- 정상 클래스: `none` (라벨 행 85%)
- 모델: IsolationForest (n_estimators=200, contamination=0.1), 154차원 feature
- train: 정상(none)만 26,731 → test 전체(118,595) 대상 `decision_function` 점수
- **ROC-AUC 0.785** — 무작위(0.5)보다 확실히 유의하나, 결함 클래스별 편차 큼

## 관찰

- 이상탐지는 라벨 불균형의 직접 맞춤이 아니므로 분류(macro-F1)보다 점수가 안정적.
- 다만 정상 패턴이 매우 다양하면(결함이 정상처럼 보이는 경우) ROC-AUC도 한계가 있다.
- 실제 라인 적용이라면 정상 공정 조건만으로 고장 샘플을 우선 스크리닝하는 용도로 유용.

## 다음 후보

- [ ] OneClassSVM 비교 (config `anomaly_model`)
- [ ] feature 도메인 확장 후 재평가 (결함 위치 주변 민감도)
- [ ] contamination 튜닝 (정상 비율 85%에 맞춰 0.1 → 0.15 스윕)

## 교차 참조

- [tasks/wafer_vision.md](../tasks/wafer_vision.md)
- [datasets/wm811k.md](../datasets/wm811k.md)