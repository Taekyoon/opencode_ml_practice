# 세션 대화 기록 — 반도체 Failure 예측 프로젝트 (2026-08-08)

> 본 문서는 `semiconductor_failure_prediction` 프로젝트에서 사용자와의 대화 과정을
> 요약·기록한 것이다. 작업을 되돌아보고, 결정 사항을 추적하고, 다음 단계를 준비하는
> 데 사용한다.

---

## 1. 대화 흐름 개요

| 순서 | 주제 | 핵심 내용 |
|------|------|----------|
| 1 | 프로젝트 상태 요약 | 지금까지 작업한 이력을 정리 (가상 데이터, 전처리, 로지스틱 회귀, 평가) |
| 2 | 에이전트/스킬 구성 | 불균형 데이터 처리를 위한 Agent + Skill 구현과 사용법 |
| 3 | 1개월 시나리오 | 에이전트 협업 플로우 설계 기획 |
| 4 | 실측 데이터 변동성 관리 | 실측 데이터의 변동성 관리에 집중된 구성 제안 |
| 5 | 데이터 규모 확장 | 초반 소규모 → 후반 100배 확장 대응 |
| 6 | 실험 로그 관리 | 매 실험마다 쌓이는 로그의 체계적 관리 |
| 7 | 동작 검증 전략 | 각 환경이 제대로 동작하는지 검증하는 방법 설계 |
| 8 | 확신 수치화 | 동작 확신을 수치로 표현하는 프레임워크 |
| 9 | 종합 검토 | 현재 상태 점수화 및 개선 전략 수립 |
| 10 | 100점 전략 | 6개 항목별 점수 갭과 5단계 로드맵 |
| 11 | 전략 저장 | 확정 사항을 `docs/PROJECT_STRATEGY.md`에 저장 |
| 12 | wrap-up | 작업 정리 및 회고록 업데이트 |

---

## 2. 주요 의사결정

### 2-1. 데이터/모델

| 결정 | 내용 |
|------|------|
| 데이터 출처 | 가상 데이터 (시드 고정 42) — 실제 데이터 공유 전 파이프라인 검증 우선 |
| 문제 유형 | 이진 분류 (합격/불량) |
| 데이터 형태 | 수치형 (공정 + 측정 변수, 총 7개 특성) |
| 불량률 | 목표 10% 이상 → 최종 16.7% |
| 처리 시점 | 배치 처리 (분 단위) |
| 알고리즘 | 로지스틱 회귀 (L2, C=1.0) |
| 평가 지표 | 정확도, 정밀도, 재현율, F1, AUC-ROC, PR-AUC |

### 2-2 opencode Agent/Skill

| 결정 | 내용 |
|------|------|
| 에이전트 | `semiconductor-failure-predictor` (subagent, 전체 권한 allow) |
| 스킬 | `imbalanced-data-specialist` (analyze/sampling/threshold/evaluate 4개 API) |
| 구현 방식 | 직접 코딩, 기존 라이브러리(imbalanced-learn) 재사용 |

---

## 3. 구현된 산출물

### 3-1. src/ 파이프라인

```
src/
├── data_generation.py   # 가상 반도체 공정 데이터 생성 (5000행, 불량률 16.7%)
├── preprocessing.py     # 결측 5% 주입 → 중앙값 대체 → StandardScaler
├── model.py             # stratify 80/20 분할 + 로지스틱 회귀 학습
└── evaluation.py        # 지표 5종 + 시각화 4종 (한글 폰트 대응)
```

### 3-2. opencode 스킬 모듈 (`.opencode/`)

```
.opencode/
├── agents/semiconductor-failure-predictor.md        # 서브에이전트 정의
└── skills/imbalanced-data-specialist/
    ├── SKILL.md                                      # 스킬 설명 + API 사용법
    └── src/imbalanced_data_specialist.py            # 클래스 모듈
```

`ImbalancedDataSpecialist` API:
- `analyze_imbalance(y)` — 클래스 비율, 불균형 비율, 전략 추천
- `apply_sampling(X, y, method)` — smote/adasyn/tomek/random_under/smote_tomek/auto
- `optimize_threshold(model, X, y, metric)` — f1/recall/precision 임계값 최적화
- `evaluate_imbalanced(...)` — F1, 정밀도, 재현율, PR-AUC, ROC-AUC

### 3-3. 문서

```
docs/
├── IMBALANCED_DATA_SPECIALIST_PLAN.md   # 스킬 구현 계획 + 검증 결과
└── PROJECT_STRATEGY.md                  # 100점 달성 전략 (5단계 로드맵)
```

---

## 4. 검증 결과 (실행 기반)

### 4-1. 기존 파이프라인

실제 프로젝트 데이터 (5,000행, 불량률 16.7%) 실행 결과:

| 지표 | 값 |
|------|-----|
| 정확도 | 0.950 |
| 정밀도 | 0.893 |
| 재현율 | 0.796 |
| F1-score | 0.842 |
| AUC-ROC | 0.986 |

### 4-2. 불균형 처리 결과

| 시나리오 | F1 | Precision | Recall | PR-AUC | ROC-AUC |
|---------|-----|-----------|--------|--------|---------|
| Baseline (no resample) | 0.842 | 0.893 | 0.796 | 0.937 | 0.986 |
| Auto(SMOTE) 후 | 0.832 | 0.742 | 0.946 | 0.937 | 0.986 |
| 임계값 최적화 후 | 0.865 | 0.833 | 0.898 | 0.937 | 0.986 |

결과: F1이 0.842 → 0.865로 개선, Recall은 SMOTE 적용 시 0.796 → 0.946으로 크게 상승함.
극심 저불량 불균형(0.5%) 스트레스 테스트에서도 모든 메서드가 정상 동작함.

---

## 5. 100점 전략 (확정·저장됨)

- 경로: `docs/PROJECT_STRATEGY.md`

| 항목 | 현재 | 목표 |
|------|------|------|
| 기능 완성도 | 70 | 100 |
| 코드 품질 | 65 | 100 |
| 테스트 커버리지 | 0 | 100 |
| 문서화 | 75 | 100 |
| 확장성 | 20 | 100 |
| 운영 편의성 | 40 | 100 |

**종합: 45/100 (D)** → 94/100 이상 목표.

### 확정 사항

| 항목 | 결정 |
|------|------|
| Phase 순서 | 기반 → 품질 → 테스트 → 확장 → 운영 |
| 테스트 커버리지 | 90% |
| 확장성 기술 | polars (pandas → polars 전환) |
| 운영 도구 | Docker |
| 문서 도구 | MkDocs |

### 5단계 로드맵

```
Phase 1: 기반 다지기    (패키지/CLI/에러 처리/.gitignore)
Phase 2: 코드 품질       (타입 힌트/로깅/ruff·mypy)
Phase 3: 테스트 체계   (unit/integration/skills/performance, 90%)
Phase 4: 확장성      (polars/파티셔닝/실험 추적)
Phase 5: 운영 완성    (Docker/모니터링/MkDocs/로그 아카이브)
```

---

## 6. 설계 논의 요약 (시나리오 단계)

### 6-1 에이전트 협업 플로우 (1달 시나리오)

- 서브에이전트 4+2: semiconductor-failure-predictor(모델), data-quality-monitor(데이터 품질),
  process-control-specialist(SPC/Cpk), drift-detection-engineer(드리프트),
  data-platform-engineer(확장), experiment-tracker(실험 추적) 등이 협업.
- 패턴: Build(오케스트레이터) → 병렬 subagent 호출 → Build가 통합 리포트.

### 6-2 실측 데이터 변동성 관리

- 데이터 품질 점수, Cpk(공정안정성), PSI(분포 변화), 모델 성능 유지율 등의 지표 체계를
  통해 실측 데이터 변동성을 정량적으로 관리.
- 안정/불안정 구간 분류, 드리프트 감지 시 자동 재학습 트리거.

### 6-3 데이터 확장 100배

- 초반(5,000행) → 중반(50,000행, polars) → 후반(500,000+, 분산 처리).
- 파티셔닝(시간/장비/로트), 실험 추적 버전관리, 자동 스케일링 파이프라인.

### 6-4 실험 로그 관리

- 로그 유형: 실험 메타·학습·평가·데이터 품질·드리프트·에러·배포 로그.
- 패턴: `logs/experiments/<YYYY-MM-DD>_<실험ID>/` 구조 + 메타 JSON 스키마.
- 보관 정책: 실험/평가 ~영구, 데이터 품질 1년, 드리프트 6개월, 에러 3개월.

### 6-5 검증 체계

- 5계층: 단위 → 스킬 → 협업 → 성능(확장) → 시스템 (전체).
- 자동 검증: 변경 시 단위/스킬, 주 1회 통합·검증, 배포 전 전체 시스템.
- 동작 확신 수치화: 종합 확신 점수 = 정확성×0.3 + 일관성×0.25 + 재현성×0.25 + 안정성×0.2.

---

## 7. 아직 남은 작업 (Next Move)

1. Phase 1 실행: `__init__.py`, `pyproject.toml`, `src/main.py`, `config.py`,
   `config.yaml`, `.gitignore` 구축.
2. 각 모듈에 에러 처리 + 타입 힌트 전면 적용.
3. unit/integration/skills/performance 테스트 구축 → 커버리지 90% 이상.
4. polars 전환 및 확장성 대응, 실험 추적 도입.
5. Docker 기반 운영, MkDocs 문서 사이트.
6. 위 Phase를 진행하면서 실측 데이터 변동성 관리 지표,
   확장(100배), 로그 관리 등 요구사항을 실제 구현에 반영.

---

## 8. 참고 파일

- `RETROSPECTIVE.md` — 작업 의미 회고 기록
- `docs/PROJECT_STRATEGY.md` — 100점 달성 로드맵
- `docs/IMBALANCED_DATA_SPECIALIST_PLAN.md` — 불균형 전문 스킬 계획
- `README.md` — 프로젝트 실행 방법, 성능 요약

---

## 9. 다음 세션(2차) 기록 안내

2차 세션(태스크 스캐폴드 CLI + 실험 기록 위키)의 대화·의사결정·산출물은
`docs/CONVERSATION_LOG_TASK_SCAFFOLD_WIKI.md`에 기록되어 있다.