# Research Wiki — Index

> 실험/개발 기록의 내용 중심 목록. 카테고리별 페이지와 한 줄 요약.
> 이 파일은 모든 실험(ingest) 후 갱신된다.

최종 갱신: 2026-08-08

## System (특수 파일)

- [overview.md](overview.md) — 프로젝트 대시보드 (세션 진입점)
- [log.md](log.md) — 연대기순 활동 기록 (append-only)

## Tasks (태스크별 발견사항)

- [tasks/failure_prediction.md](tasks/failure_prediction.md) — 분류 태스크 누적 발견 (현재 베이스라인 score=0.7912)
- [tasks/quality_regression.md](tasks/quality_regression.md) — 회귀 태스크 누적 발견 (현재 베이스라인 R²=0.9822)

## Techniques (기법별 종합)

- [techniques/baseline.md](techniques/baseline.md) — 현재 베이스라인 구성 (logistic/ridge + StandardScaler)
- [techniques/imbalance_handling.md](techniques/imbalance_handling.md) — 불균형 처리 기법 계획 (SMOTE 등 미시험)
- [techniques/model_comparison.md](techniques/model_comparison.md) — 모델별 비교 (아직 미시험)

## Datasets (데이터셋)

- [datasets/lab_sensor_data.md](datasets/lab_sensor_data.md) — 5,000행, failure 비율 16.98%, 특성 8개

## Synthesis (교차 종합)

- [synthesis/lessons_learned.md](synthesis/lessons_learned.md) — 전체 교훈 + 다음 실험 방향