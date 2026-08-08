# 불균형 데이터 전문가 (Imbalanced Data Specialist) 구현 계획·결과 문서

## 1. 목표

반도체 실험실 수치 데이터의 failure(불량) 예측에서, 불량률이 낮은(예: 16.7%)
불균형 데이터를 다루기 위한 opencode Agent + Skill + 핵심 모듈을 구축한다.

- **가상 데이터 중심**으로 검증 (실데이터 확보 시 활용 가능)
- 4일 이내 완료 규모의 **핵심 기능 3가지**에 집중
- 기존 라이브러리(`imbalanced-learn`/`scikit-learn`) 재사용, 처음부터 구현하지 않음

## 2. 구현 방식 (결정 사항)

| 항목 | 결정 |
|------|------|
| 직접 코딩 vs 외부 도구 | 직접 코딩 (새 라이브러리 없음) |
| 알고리즘 구현 | 개선된 SMOTE/Tomek 등 기존 라이브러리 중심 |
| 핵심 기능 | 3가지 (분석 / 샘플링 / 임계값 최적화 + 평가) |
| 일정 | 가상 데이터 중심 4일 단위 |
| opencode 통합 | Agent + Skill 동시 사용 |
| Demo | 음 (설명 문서로 대체) |

## 3. 파일 구조

```
.opencode/
├── agents/
│   └── semiconductor-failure-predictor.md   # 실무 에이전트 정의
└── skills/
    └── imbalanced-data-specialist/
        ├── SKILL.md                          # 스킬 지침 (frontmatter 포함)
        └── src/
            └── imbalanced_data_specialist.py  # 핵심 모듈
```

그 외:
- `requirements.txt` — `imbalanced-learn>=0.12` 추가
- 실제 데이터 검증은 `notebooks/` 및 `src/` 파이프라인과 연동

## 4. 핵심 모듈 API

```python
from src.imbalanced_data_specialist import ImbalancedDataSpecialist

spec = ImbalancedDataSpecialist(random_state=42)

# 1. 불균형 분석
ratio = spec.analyze_imbalance(y)              # (majority/minority) 비율 반환

# 2. 샘플링 (auto/smote/adasyn/tomek/random_under/smote_tomek)
X_res, y_res = spec.apply_sampling(X_train, y_train, method="auto")

# 3. 임계값 최적화 (metric: f1/recall/precision)
best = spec.optimize_threshold(model, X_test, y_test, metric="f1")

# 4. 불균형 지향 평가 (F1/Precision/Recall + PR-AUC/ROC-AUC)
metrics = spec.evaluate_imbalanced(y_test, y_pred, y_proba)
```

## 5. 검증 결과 (실제 프로젝트 데이터, 불량률 16.7%)

| 시나리오 | F1 | Precision | Recall | PR-AUC | ROC-AUC |
|---------|-----|-----------|--------|--------|---------|
| Baseline (로지스틱 회귀) | 0.842 | 0.893 | 0.796 | 0.937 | 0.986 |
| Auto 샘플링(SMOTE) 후 | 0.832 | 0.742 | 0.946 | 0.937 | 0.986 |
| 임계값 최적화(F1 목표) | **0.865** | 0.833 | 0.898 | 0.937 | 0.986 |

- Auto 샘플링으로 Recall이 0.796 → 0.946으로 크게 상승
- 임계값 최적화로 F1이 0.842 → 0.865로 개선, Precision/Recall 균형 회복
- 극심 불균형(0.5% 양성) 스트레스 테스트에서도 모든 메서드 정상 동작

## 6. 사용법

### 에이전트 (@ 멘션으로 호출)

대화 프롬프트에 `@` 멘션을 붙여 서브에이전트를 직접 호출한다:

```
@semiconductor-failure-predictor 데이터 불균형을 분석하고 SMOTE 적용 후 F1을 최대화해줘
```

파일명(`semiconductor-failure-predictor.md`)이 곧 에이전트 이름이 된다. `@imbalanced-data-specialist`로 스킬을 직접 불러올 수도 있다.

### 모듈 직접 사용

```bash
PYTHONPATH=src:.opencode/skills/imbalanced-data-specialist python script.py
```

## 7. 향후 확장 항목

- 실데이터 통합 (RETROSPECTIVE.md의 요구사항 반영)
- 피처 엔지니어링 확장 (장비별·로트별 특성)
- 의사결정 임계값 *비즈니스 비용* 매핑 (거짓 양성/음성 비용 비율)
- 모니터링: 데이터 드리프트 감지 추가