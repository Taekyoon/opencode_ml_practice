# C2. 새 태스크 만들기 — 스캐폴드 CLI

## 학습 목표
- 스캐폴드가 "새 태스크"를 안전하게 만드는 이유를 안다
- `scripts/new_task.py`의 인자와 동작을 이해한다
- 실제로 새 태스크를 만들어 삭제하는 연습을 한다

## 배경 지식

### 왜 스캐폴드를 쓰는가?
새 예측 문제가 생겼을 때 파일을 수동으로 만들면 실수가 나온다:
- 폴더 구조가 다를 수 있음
- 레지스트리 등록을 까먹음
- 분류/회귀 판정이 잘못됨

`scripts/new_task.py`는 **검증 + 생성 + 등록**을 한 번에 한다:
1. dataset 존재/컬럼 검증
2. `research/<task_id>/` 폴더·runner·program·results 생성
3. target 값 유형으로 분류/회귀 자동 판정
4. `tasks_extra.json`에 등록 → registry가 로드 → Airflow가 자동 인식

> 이 프로젝트의 "확장 가능한 구조"의 핵심이다.
> 새 태스크를 추가하는 방법이 표준화되어 있기 때문이다.

## 따라하기

### 1단계: 현재 등록된 태스크 확인
```bash
python research/tasks_registry.py
```
출력 예:
```
[research] 등록된 태스크:
  failure_prediction: 반도체 failure 예측 (분류, 불균형 대응) (score=score)
  quality_regression: 제품 두께(thickness) 예측 (회귀) (score=r2)
```

### 2단계: 스캐폴드 지침 읽기
```bash
python scripts/new_task.py --help
```

### 3단계: 실행해보기 (연습용 — 잠깐 만들고 지울 것이다)
```bash
python scripts/new_task.py demo_task --dataset lab_sensor_data --target failure --note "튜토리얼 연습"
```
출력에서 `kind: classification` 판정을 확인한다.
> 대상 컬럼이 2개 값(0/1)뿐이므로 분류로 판정되는 것.

### 4단계: 생성물 확인
```bash
ls research/demo_task/
cat research/demo_task/program.md
```
- `program.md`는 연구 지침서 초안 (사람이 보완)
- `experiment_runner.py`는 범용 템플릿

### 5단계: 실행해보기
```bash
python research/demo_task/experiment_runner.py
```
`research/demo_task/results/run_*/metrics.json`가 생성되고 DB에 기록된다.

### 6단계: 정리 (실습 후 삭제)
연습용 태스크이므로 지운다:
```bash
rm -rf research/demo_task
python - <<'PY'
import json, os
from research import tasks_registry as tr
extra_path = tr.EXTRA_TASKS_FILE
if os.path.exists(extra_path):
    data = json.load(open(extra_path))
    data.pop("demo_task", None)
    json.dump(data, open(extra_path, "w"), indent=2, ensure_ascii=False)
print(tr.list_tasks())
PY
```

> **실무 팁**: 임시 테스트로 만든 태스크는 커밋하기 전에 꼭 제거한다.
> AGENTS.md(섹션 8): "tasks_extra.json 은 ... 임시 테스트만 생성됐던 경우 제거 후 커밋"

## 이해 확인

1. 스캐폴드 사용 시 자동으로 수행해주는 3가지는?
2. 분류/회귀 판정 기준은 무엇인가? (target 값의 개수)
3. 왜 반드시 CLI로 만들어야 하는가?

## opencode에게 물어보세요
```
scripts/new_task.py의 오류 처리(검증) 단계들을 정리해줘.
어떤 실수를 미리 막아주는지.
```

## 다음 레슨
[C3. 위키 지식 베이스](11_wiki_knowledge_base.md) — 실험에서 발견한 것을 기록하는 곳.