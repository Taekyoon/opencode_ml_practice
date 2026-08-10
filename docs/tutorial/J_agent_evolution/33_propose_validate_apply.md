# J3. 제안→검증→적용 — "변경을 왜 했는지"를 남기는 루프

## 학습 목표
- 제안·검증·적용이 왜 분리되어야 하는지 설명할 수 있다
- 변경 근거(`_rationale`)를 남기는 것이 왜 중요한지 안다
- 에이전트가 "왜 이 실험을 반복하는지"를 이벤트 기록에서 확인할 수 있다

## 배경 지식

### why가 빠져 있다

지금까지의 기록은 "무엇을" 했는지는 남긴다:

```json
{
  "config": {
    "model_type": "random_forest",
    "model_params": {"n_estimators": 300, "max_depth": null},
    "_rationale": "비선형 패턴 포착을 위해 RF로 교체"
  },
  "metrics": {"f1": 0.74, "train_f1": 1.0},
  "score": 0.79
}
```

그런데 이 실험을 **왜** 했는지는 어디에도 없다. `model_type`을 바꾼 이유, 기대했던 효과,
참고한 근거가 남지 않는다. 다음 세션의 에이전트(또는 사람)는 config 차이만 보고 추론해야 한다.

Shepherd/SkillOpt는 여기서 핵심 개념을 제공한다:
- **제안(Propose)** — 변경 사항을 *실행 전*에 선언한다 (결과를 모르는 상태에서)
- **검증(Validate)** — 게이트(J2)로 결과가 진짜 개선인지 확인한다
- **적용(Apply)** — 검증을 통과한 것만 채택하고, 그렇지 않은 것은 버린다

여기서 핵심 규칙: **제안에 "왜"를 붙인다.** `_rationale` 키는 이 프로젝트의
"메타 키" 규약이다. `run_experiment()`는 config에서 `_`로 시작하는 키를 **직접 무시하는
코드는 없다** — 다만 읽는 키(위 표의 `model_type`,`model_params` 등)가 고정되어 있어
최상위 `_` 키는 자연히 모델 파라미터로 새어나가지 않는다. 즉 코드가 강제하기보다
**팀 규약으로 보호**되는 값이다.

> **메타 키 규약**: `get_config()` 최상위에 `_`로 시작하는 키를 넣으면 실험 로그에
> 기록되지만 모델 파라미터로는 사용되지 않는 "왜 이 실험을 했는가"를 남기는 표준 방법이다.
> config 최상위가 아닌 `model_params` **안에는 넣지 말 것** — 거기는 그대로 모델 생성자에 전달된다.

### 중복 제안: 왜 금지인가

J1에서 봤듯, 과거 실패가 기록되지 않으면 에이전트는 같은 실수를 반복한다.
제안→검증→적용 루프에서 "이미 해본 실험"을 다시 하는 것은 낭비다.

```bash
# 이미 score=0.7912로 같은 config를 실행한 이력이 있는데,
# 동일한 config를 또 실행하면? -> 중복
```

**규칙**: 같은 `config`를 다시 제안하지 않는다. 바꿀 거면 최소 하나는 바꾼다.
과거 실행은 `research.db`의 `experiments` 테이블에서 조회 가능하다.

## 따라하기

### 1단계: 플랜 — 메타 키와 과거 이력 조회

`get_config()`에 `_rationale`을 추가하면 어떤 일이 생기는지 확인한다.

```bash
python - <<'PY'
import copy, sys; sys.path.insert(0, '.')
from research.failure_prediction import experiment_runner as runner

cfg = copy.deepcopy(runner.get_config())
cfg["_rationale"] = "모델을 random_forest로 바꿔 비선형 패턴 포착을 시도 (techniques/model_comparison.md 참고)"
cfg["model_type"] = "random_forest"

result = runner.run_experiment(cfg)
print("score:", result["score"])
print("_rationale preserved:", result["config"]["_rationale"])
PY
```

`_rationale`이 config dict에 그대로 남는다. 이제 과거 실험 이력을 조회해
"이미 같은 config를 해봤는지" 확인하는 법을 보자:

```bash
python - <<'PY'
import sys, json; sys.path.insert(0, '.')
from src.research_store import get_all_experiments

for r in get_all_experiments(limit=10):
    cfg = json.loads(r["config_json"])
    model = cfg.get("model_type", "?")
    print(f"  {r['run_id'][:18]}  score={r['score']}  model={model}")
PY
```

### 2단계: 빌드 — 제안→검증→적용 사이클 수동 실행

이제 실제로 루프를 수동으로 한 바퀴 돌려보자. 세 함수를 조합한다:

| 단계 | 도구 | 역할 |
|------|------|------|
| 제안 | `get_config()` 수정 + `_rationale` | 변경 이유 선언 |
| 검증 | `evaluate_gate()` | 과적합 등 함정 탐지 |
| 적용/기각 | `record_experiment()` | DB 기록 + 상태 결정 |

```bash
python - <<'PY'
import copy, sys, time; sys.path.insert(0, '.')
from research.failure_prediction import experiment_runner as runner
from src.validation_gate import evaluate_gate
from src.research_store import record_experiment, record_event

# --- 제안 (with reason) ---
cfg = copy.deepcopy(runner.get_config())
cfg["_rationale"] = "smote+threshold로 불균형 대응 강화"
cfg["imbalance_strategy"] = "smote+threshold"
cfg["optimize_threshold"] = True
run_id = "run_" + time.strftime("%Y%m%d_%H%M%S")
record_event(run_id, "started", {"hypothesis": cfg["_rationale"]})

# --- 실행 ---
result = runner.run_experiment(cfg)

# --- 검증 ---
gate = evaluate_gate(result["metrics"])
print("gate accepted:", gate.accepted, "|", gate.reason)

# --- 적용/기각 ---
if gate.accepted:
    eid = record_experiment(
        run_id=run_id,
        config=result["config"],
        metrics=result["metrics"],
        score=result["score"],
        task_id="failure_prediction",
        score_name="score",
    )
    record_event(run_id, "completed", {"score": result["score"], "gate_passed": True})
    print("적용됨 (experiment id:", eid, ")")
else:
    # best_run 오염은 막되, 실패도 events로 남긴다 (J1 원칙)
    record_event(run_id, "gate_rejected", {"reason": gate.reason, "score": result["score"]})
    print("기각됨 — 사유:", gate.reason, "(gate_rejected 이벤트로 기록됨)")
PY
```

**핵심**: 게이트가 기각하면 `record_experiment()`는 호출하지 않는다 — "나쁜 실험"이
최고 기록 `best_run`에 오르는 것을 막으면서, J1의 원칙대로 기각 사유를
`gate_rejected` **이벤트**로 남겨 실패도 존재하는 일로 기록한다.

> **게이트 해석 주의**: `overfitting` 갭은 "train은 smote 후 균형셋, test는 원본 불균형셋",
> "train은 임계 0.5, test는 최적 임계"처럼 **평가 기준이 서로 달라** 과적합과 무관한 이유로
> 커질 수도, 작아질 수도 있다. 위 실행에서 `gap≈0.126`(통과)은 그 예. 갭 자체보다
> 추세와 실제 지표 조합으로 해석할 것.

### 3단계: 검증 — 이벤트로 되돌아보기

J1에서 만든 이벤트 기록으로 "이번 사이클이 어떤 제안에서 나왔는지"를 이어붙일 수 있다:

```bash
python - <<'PY'
import sys, time; sys.path.insert(0, '.')
from src.research_store import record_event, get_events

run_id = "run_demo_cycle_" + time.strftime("%Y%m%d_%H%M%S")
record_event(run_id, "started", {"hypothesis": "smote+threshold가 불균형 개선에 효과적인지"})
record_event(run_id, "completed", {"score": 0.82, "gate_passed": True})

# 기록했다면 꼭 읽어 확인한다 — "왜 이 실험을 했는지"를 재구성할 수 있어야 한다
for e in get_events(run_id):
    print(f"{e['event_type']:<10} {e['detail']}")
PY
```

`started`의 `hypothesis`와 `completed`의 `gate_passed`가 같은 `run_id`로 이어져
"어떤 제안 → 어떤 결과"가 한 줄로 재구성된다.

### 4단계: 확장 — "기록을 읽지 않으면" 실패 모드 재현

이제 막 배운 개념의 반대를 재현해보자. **과거 이력을 안 보고 같은 config를 또 제안하는** 상황:
`_rationale` 같은 메타 키가 들어 있으면 단순 비교(`==`)가 오탐하므로,
`_` 메타 키를 제외한 "구성의 핵심"만 정렬 JSON 문자열로 잡아내는 헬퍼를 만든다.

```bash
python - <<'PY'
import sys, json; sys.path.insert(0, '.')
from src.research_store import get_all_experiments

def _core(cfg: dict) -> dict:
    """메타 키(_ 접두)를 뺀 실제 하이퍼파라미터 구성."""
    return {k: v for k, v in cfg.items() if not k.startswith("_")}

def is_duplicate(cfg: dict, history) -> str:
    """과거 이력 중 _rationale와 무관하게 같은 config가 있으면 기존 run_id 반환."""
    probe = json.dumps(_core(cfg), sort_keys=True, default=str)
    for r in history:
        row = json.loads(r["config_json"])
        if json.dumps(_core(row), sort_keys=True, default=str) == probe:
            return r["run_id"]
    return ""

# 방금 기록된(적용됨) experiment를 재제안하는 상황
hist = get_all_experiments(task_id="failure_prediction", limit=100)
if not hist:
    print("조회 대상 없음 — 2단계에서 gate를 통과한 실험이 없다면 먼저 실행할 것")
else:
    latest_id, latest_cfg = hist[0]["run_id"], json.loads(hist[0]["config_json"])

    # case 1: 구성 그대로, _rationale만 바꿔 재제안 → 중복 감지
    re_propose = {**latest_cfg, "_rationale": "(재제안) ground-truth 재확인"}
    d1 = is_duplicate(re_propose, hist)
    print("case1 같은 구성 재제안:", ("중복! 기존 " + d1) if d1 else "미감지(이상)")

    # case 2: 최소 하나 바꾼 다음 제안 → 새 구성
    changed = {**latest_cfg, "model_type": "gradient_boosting"}
    d2 = is_duplicate(changed, hist)
    print("case2 구성 변경 제안:", ("중복! 기존 " + d2) if d2 else "새 제안 (중복 아님)")
PY
```

case1은 **기존 `run_id`가 즉시 반환**되고, case2는 "새 제안"으로 통과한다. 이 헬퍼는
"같은 config 반복 금지" 규칙을 자동화한다 — `_rationale`(왜)가 달라도 **구성(config)이
같으면 중복**이라는 핵심을 그대로 옮긴 것이다.

> **한계 인지**: 위 헬퍼는 `experiments` 테이블만 읽어, 게이트에 기각돼 `experiments`에
> 없는 config는 중복으로 잡지 못한다. 기각 실험까지 막으려면 `get_events()`의
> `gate_rejected` 이벤트까지 이력을 확장해야 한다. (보충 자료:
> [엔지니어링 개념](../../design/ENGINEERING_CONCEPTS.md) §2 루프 공학 참고)

> **교훈**: 기록을 읽으면 반복을 피하고, 안 읽으면 같은 실험이 쌓인다.
> 에이전트가 발전한다는 것은 "과거 기록을 반영해 더 나은 제안을 만든다"는 뜻이다.

## 이해 확인

1. `_rationale`이 "메타 키"인 이유는 무엇인가? (모델 파라미터로 새어나가면?)
2. 게이트가 기각한 실험을 `record_experiment()`로 기록하지 않으면서도, J1의 "실패도 기록한다"는 원칙은 어떻게 지키는가? (`gate_rejected` 이벤트)
3. "같은 config를 반복 제안"하는 것의 문제는?
4. 이 J 모듈을 다 듣고 나서, "에이전트를 발전시킨다"는 것의 의미를 한 문장으로 말해보자

## opencode에게 물어보세요
```
research/failure_prediction/experiment_runner.py와 src/validation_gate.py를 읽고,
다음 설정으로 실험 3개를 번갈아 실행하는 자동 검증 스크립트를 짜줘:
- config A (baseline): 현재 get_config()
- config B: smote+threshold
- config C: random_forest + smote
각각 _rationale을 남기고, evaluate_gate()로 검증 후 통과한 것만 기록해줘.
```

## 다음 레슨
처음으로 → [README](../README.md) — 축하합니다! J 모듈(에이전트 발전 심화)을 완료했습니다.