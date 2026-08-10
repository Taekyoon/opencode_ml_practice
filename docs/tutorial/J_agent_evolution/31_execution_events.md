# J1. 실행 이벤트 기록 — 에이전트가 "뭘 했는지" 남기기

## 학습 목표
- 실행을 "결과"가 아니라 "이벤트 시퀀스"로 보는 관점을 이해한다
- 실패한 실행이 기록되지 않으면 에이전트가 왜 같은 실수를 반복하는지 설명할 수 있다
- 기존 DB를 깨지 않고 스키마를 추가 테이블로 확장하는 방식을 설명할 수 있다

## 배경 지식

### 진짜 문제: "실패는 DB에 존재하지 않는다"

프로젝트의 DAG(`airflow/dags/ml_research_loop.py`)를 보면 실험 흐름이 이렇게 연결되어 있다:

```
prepare_data → run_experiment → evaluate_store → generate_report
```

그런데 `_run_experiment()`가 **실패하면 무슨 일이 생길까?**

```python
if proc.returncode != 0:
    raise RuntimeError(f"{task_id} runner 실패:...")
```

- `run_experiment` 태스크가 실패 → 뒤의 `evaluate_store`는 **실행되지 않는다**
- `evaluate_store`에서 `record_experiment()`가 호출되지 않으므로 **`experiments`/`best_run` 테이블 기준으로 그 실험은 아예 없다**
- 결과적으로 **실패한 실행은 "결과 기록" 속에 존재하지 않는 일이 된다**

`research_store.py`에 `status = "failed"` 코드가 있지만, 이 경로에 도달하는 호출 경로가 현재 없다. 즉 **데드코드**다. (실패를 남기려면 `record_event()`로 이벤트는 남길 수 있지만, 결과 표에는 어디에도 없다 — 그래서 이 레슨이 `events` 테이블을 다루는 것이다.)

**왜 위험한가?** 에이전트가 실패를 기억할 수 없으면, 같은 실수를 무한 반복한다:
1. 하이퍼파라미터를 바꾼다 → 실패 (에러 사유 미기록)
2. 다음 세션이 오면, 과거 실패가 없다 → 또 같은 설정을 시도한다

Shepherd의 `run trace --events`가 바로 이 문제를 해결한다. 실행의 각 단계가 "이벤트"로 기록되어, 나중에 "무엇이 왜 실패했는지"를 재구성할 수 있다.

### 이벤트 기록의 3가지 원칙
1. **실패도 기록한다** — 성공한 결과만 남기면 실패 패턴을 배울 수 없다
2. **근거를 함께 남긴다** — "무슨 일이 있었다"가 아니라 "왜인지"에 대한 단서
3. **기존 스키마를 깨지 않는다** — 마이그레이션으로 확장

## 따라하기

### 1단계: 플랜 — events 테이블 확인

이미 프로젝트에 `events` 테이블이 구현되어 있다. 구조를 확인하자:

```bash
python - <<'PY'
import sys; sys.path.insert(0, '.')
from src.research_store import get_conn   # get_conn이 _migrate_schema()를 호출해 테이블을 만든다

conn = get_conn()
for r in conn.execute("SELECT sql FROM sqlite_master WHERE name='events'"):
    print(r[0])
PY
```

> 참고: `research/research.db`는 gitignore 대상이라 새 clone에는 없지만, 위처럼
> `get_conn()`을 거치면 `_migrate_schema()`가 실행되어 `events` 테이블이 자동 생성된다.

다음 4개 컬럼이 있어야 한다:

| 컬럼 | 의미 | 예시 |
|------|------|------|
| `run_id` | 어떤 실행인지 | `run_20260810_120000` 또는 `failure_prediction_...` |
| `event_type` | 어떤 단계인지 | `started` / `completed` / `failed` |
| `timestamp` | 언제인지 | `2026-08-10T12:00:00` |
| `detail` | 세부 근거 (JSON) | 에러 메시지, 시드, 변경 내용 |

기존 `experiments` 테이블은 그대로 두고 **추가 테이블로 확장**했다는 점이 핵심이다. (마이그레이션은 `research_store.py`의 `_migrate_schema()`에서 처리)

### 2단계: 빌드 — 실험을 실행하고 이벤트 확인하기

#### (a) 정상 실행의 이벤트 보기

```bash
python research/failure_prediction/experiment_runner.py
```

이제 events 테이블을 조회해 "이 실행의 흔적"을 찾아보자:

```bash
python - <<'PY'
import sys; sys.path.insert(0, '.')
from src.research_store import get_recent_events
for e in get_recent_events(5):
    print(f"{e['timestamp'][:19]}  {e['event_type']:<10} {e['run_id'][:32]}")
print("(출력이 비어 있으면 아직 events 테이블이 비어 있다는 뜻)")
PY
```

> **관찰 포인트**: 방금 러너를 단독 실행했는데 이벤트가 **새로 추가되지 않았다.**
> (아래 결과가 빈 목록이면 DAG를 돌린 적이 아직 없어 처음부터 비어 있는 것이고,
> 이벤트가 있었다면 그 개수가 그대로다.)

그 이유는 이벤트를 남기는 곳이 러너가 아니라 **DAG(`ml_research_loop.py`)의
`_run_experiment()`** 이기 때문이다. 러너 단독 실행은 `metrics.json`만 쓰고
이벤트는 남기지 않는다. 즉 "누가 실행하느냐"에 따라 이벤트가 기록되거나 되지 않는다.

아래 (b)에서 DAG의 `_run_experiment()`를 흉내 내 시작/실패 이벤트를 직접 남겨보자.

#### (b) 실패 이벤트를 만들어 보기

이제 **일부러 실패**를 만들어 이벤트가 남는지 확인하자:

```bash
python - <<'PY'
import sys, time; sys.path.insert(0, '.')
from src.research_store import record_event

# 실행마다 고유한 run_id (재실행해도 중복 누적 방지)
run_id = f"demo_fail_run_{time.strftime('%Y%m%d_%H%M%S')}"
record_event(run_id, "started", {"task_id": "failure_prediction", "config_seed": 42})
record_event(run_id, "failed", {"returncode": 1, "stderr_tail": "ValueError: missing column 'failure'"})
print("실패 이벤트 기록 완료:", run_id)
PY
```

다시 조회해서 **실패도 이벤트로 남았는지** 확인한다:

```bash
python - <<'PY'
import sys; sys.path.insert(0, '.')
from src.research_store import get_recent_events
for e in get_recent_events(4):
    if "demo_fail_run" in e["run_id"]:
        print(f"{e['event_type']:<10} {e['detail']}")
PY
```

> **포인트**: 실패는 "없었던 일"이 아니라 "이벤트 이력"에 남는다. 이제 다음 세션의 에이전트가
> `get_recent_events()`로 조회하면 "왜 그 실험이 무시됐는지" 알 수 있다.

### 3단계: 검증 — 이벤트가 실제 DAG 실패/성공에도 남는지 확인

`airflow/dags/ml_research_loop.py`를 열어 `_run_experiment()`를 보면:

- 실행 시작 → `record_event(..., "started", {...})`
- 성공 → `record_event(run_id, "completed", {"score": ...})`
- 실패 → `record_event(fail_run_id, "failed", {"returncode": ..., "stderr_tail": ...})`

```bash
python - <<'PY'
import sys; sys.path.insert(0, '.')
from src.research_store import get_recent_events
print("최근 이벤트:", len(get_recent_events(20)), "건")
for e in get_recent_events(20)[:8]:
    print(f"  {e['event_type']:<10} {e['run_id'][:28]} {e['timestamp'][:19]}")
PY
```

### 4단계: 확장 — Shepherd의 run trace와 비교 (사이드바)

> **Shepherd 사이드바** (선택) — 오프라인 격리 환경에서 Shepherd의 이벤트 기록을 보고 비교한다.
> Shepherd는 `~/.venvs/agent-tools` 격리 venv에만 설치되어 있고, 프로젝트 런타임에는 영향을 주지 않는다.
> **`~/.venvs/agent-tools/bin/shepherd`가 없으면 이 단계는 통째로 건너뛰어도 된다** — 핵심 개념은 아래와 동일하다.

```bash
# 격리 venv에서 (프로젝트 아님)
~/.venvs/agent-tools/bin/shepherd init /tmp/shepherd-retained
cd /tmp/shepherd-retained
~/.venvs/agent-tools/bin/shepherd demo write quickstart > demo.py
~/.venvs/agent-tools/bin/python demo.py
~/.venvs/agent-tools/bin/shepherd run trace --latest --events
```

Shepherd의 `run trace --events`가 "생명주기 이벤트"를 보여주듯, 우리 이벤트 테이블도
"실행의 생명주기"를 기록한다. 개념은 같고 구현이 다르다는 점이 핵심이다.

## 이해 확인

1. 현재 DAG에서 실험 실패 시 어떤 일이 벌어지는가? (research.db 기준)
2. `status="failed"`가 "데드코드"인 이유는?
3. events 테이블을 추가할 때 기존 `experiments` 테이블은 왜 그대로 두었나?
4. 실패를 기록하지 않으면 에이전트가 왜 같은 실수를 반복하는가?

## opencode에게 물어보세요
```
airflow/dags/ml_research_loop.py와 src/research_store.py를 읽고,
실패한 실험이 events 테이블에 기록되는 경로를 추적해줘.
실패 원인(stderr)이 detail 컬럼에 남는지 확인하고,
만약 남지 않는 경우가 있다면 어떤 시나리오에서 그런지 설명해줘.
```

## 다음 레슨
[J2. 검증 게이트](32_validation_gate.md) — 점수만으로 판단하지 않는 법