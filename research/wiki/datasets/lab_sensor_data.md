---
tags: [datasets, lab_sensor_data]
created: 2026-08-08
updated: 2026-08-08
dataset: lab_sensor_data
---

# lab_sensor_data — 데이터셋 이해

> 등록된 dataset의 구조와 분포를 기록한다. 새 데이터셋이 추가되면 별도 페이지 생성.

## 기본 정보

| 항목 | 값 |
|------|-----|
| 이름 | lab_sensor_data |
| 행 수 | **5,000** |
| target | `failure` (0/1) |
| failure 비율 | **16.7%** (불균형) |

## 특성 (7개)

- `temperature` — 공정 온도
- `pressure` — 공정 압력
- `process_time` — 공정 시간
- `chemical_concentration` — 화학 농도
- `thickness` — 생성물 두께
- `resistivity` — 비저항
- `dopant` — 도핑 농도

> `quality_regression`은 이 중 `thickness`를 target으로 사용한다 (회귀).
> 기존에 기록된 `delta_temp` 컬럼은 실제 생성기(`src/data_generation`)에 없어
> 특성 목록에서 제거했다 (파생 변수로 만들면 새 태스크에서 사용 가능).

## 분포/주의사항

- 16.7% failure → {분류} 불균형 처리 필요 → [techniques/imbalance_handling.md](../techniques/imbalance_handling.md)
- 결측치 5% 주입 (data_generation) → 전처리에서 처리됨
- 결측치/이상치 확인 방법: `python -m src.data_manager`, `python -m src.preprocessing`

## 등록 방법 (재현)

이 dataset은 **커밋되지 않는다** (research.db/datasets는 gitignore). 원본에서 재등록:

```bash
mkdir -p research/inbox
cp data/synthetic_data.csv research/inbox/synthetic_data.csv
python scripts/new_task.py <task_id> --inbox synthetic_data.csv --target failure
```

## 원본

- raw: `research/datasets/lab_sensor_data/` (data_manager 등록본)
- 원본 합성기: `src/data_generation` (5,000행, 랜덤 시드 42)

## 교차 참조

- [tasks/failure_prediction.md](../tasks/failure_prediction.md)
- [tasks/quality_regression.md](../tasks/quality_regression.md)