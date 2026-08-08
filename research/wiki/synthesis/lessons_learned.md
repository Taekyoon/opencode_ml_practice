---
tags: [synthesis, lessons]
created: 2026-08-08
updated: 2026-08-08
---

# Lessons Learned — 교차 태스크 종합

> 태스크/기법을 가로질러 얻은 교훈과 다음 실험 방향을 기록하는 종합 페이지.
> 이 페이지가 위키의 "지식 부가가치" 코어다.

## 현재 결론 (베이스라인 단계)

1. **분류는 아직 "정답"을 모른다** — 불균형 미처리 + logistic 하나뿐.
   - 0.7912는 충분히 개선될 여지가 있음 (recall 0.796 → 목표 0.85+)
2. **회귀는 이미 우수** — 선형 모델로 R²=0.9822.
   - 개선 우선 순위는 **분류**에 두는 것이 효율적.
3. **모든 실험이 동일 score 반복 중** — 원인: 아직 변수 튜닝이 없음 (베이스라인만 계속 실행).
   - 다음 세션은 반드시 한 가지 변수만 바꿔 A/B 테스트를 시작해야 한다.

## 다음 실험 방향 (우선순위)

### failure_prediction (1순위)
1. SMOTE 적용 → imbalance_handling.md로 결과 기록
   - 기대: recall↑, PR-AUC 유지 → score 상승
2. RandomForest/GradientBoosting 비교 (`scale=False` 주의)
3. 임계값 최적화 (`optimize_threshold=True`)

### quality_regression (2순위)
4. RandomForestRegressor 한 번 시도 (비선형 확인용)
5. 이상치 확인 (temperature/resistivity 극단값)

## 실험 규율 (이 위키의 핵심)

- **한 번에 하나의 변수만** 변경 (A/B 원칙)
- 실험 후 반드시 **tasks → techniques → log → index** 순서로 wiki 갱신
- "효과 있었다/없었다"의 **맥락과 함께** 기록 (예: "SMOTE: 분류에서는 효과적, 회귀 미적용")

## 교차 참조

- [overview.md](../overview.md) — 대시보드
- [tasks/failure_prediction.md](../tasks/failure_prediction.md)
- [techniques/imbalance_handling.md](../techniques/imbalance_handling.md)