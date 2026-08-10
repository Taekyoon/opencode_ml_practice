# J2. 검증 게이트 — "점수가 올랐다"가 곧 "개선됐다"는 아니다

## 학습 목표
- "점수가 올랐다 ≠ 개선됐다"인 경우를 예로 들 수 있다
- 판정 결과를 accept/reject 불린이 아니라 **근거가 붙은 구조체**로 남기는 이유를 안다
- 자기만의 검증 규칙을 하나 추가할 수 있다

## 배경 지식

### 점수 게임의 함정

현재 프로젝트의 `record_experiment()`는 `score >= best` 비교로 `is_best`를 판정한다. 그런데 점수만으로 판단하면 몇 가지 흔한 함정에 빠진다:

| 함정 | 예시 |
|------|------|
| **과적합** | test는 0.70이지만 train은 1.00 — 모델이 train을 외웠음 |
| **임계값 붕괴** | recall=1.0인데 precision=0.1 — "모든 걸 양성"이라고 외친 것 |
| **무의미 모델** | PR-AUC 0.45 — 랜덤 수준 |

이런 경우 점수는 "기록"될 수 있지만 "좋은 모델"은 아니다. 에이전트가 이 함정에 빠지면, 결과 표에는
점수가 쌓이지만 실제 품질은 오르지 않는다.

### GateResult: 판정을 "근거 구조체"로 남기는 이유

단순히 `accepted: True/False`를 반환하면 안 되는 이유가 둘 있다:

1. **디버깅** — "왜 기각됐는지" 이유가 없으면 에이전트는 뭘 고쳐야 할지 모른다
2. **게이트 우회 방지** — 판정 근거가 구조화되어 있으면, 지표 정의만 고쳐 게이트를 통과하는 "지표 게이밍"을 감지할 수 있다

그래서 `src/validation_gate.py`는 `GateCheck`/`GateResult` 구조체를 사용한다:

```
GateResult
├── accepted: bool          # error급 규칙이 모두 통과해야 True
└── checks: [GateCheck...]  # 개별 규칙 결과
    ├── name      # 규칙 이름 (overfitting 등)
    ├── passed    # 통과 여부
    ├── reason    # 근거 (숫자 포함)
    └── severity  # 'error' | 'warning'
```

## 따라하기

### 1단계: 플랜 — 게이트 모듈 확인

```bash
python - <<'PY'
import sys; sys.path.insert(0, '.')
from src.validation_gate import RULES
print("현재 규칙:", [r.__name__ for r in RULES])
PY
```

`src/validation_gate.py`에 4개 규칙이 이미 있다 (1단계 `RULES` 출력의 함수명과 아래 표의 `규칙` 이름 매핑에 주의):

| 규칙 (함수명) | 판정 기준 | 심각도 |
|------|-----------|--------|
| `overfitting` (`_check_overfitting`) | train-test F1/R² 갭 > 0.15 | error |
| `threshold_collapse` (`_check_threshold_collapse`) | recall>=1.0 & precision<0.3 | error |
| `random_model` (`_check_random_model`) | PR-AUC <= 0.5 | error |
| `elapsed` (`_check_elapsed`) | 180초 초과 | warning |

> `elapsed`는 **항상 passed=True**로, 기각하지 않는 정보용 규칙이다. 통과해도
> reason에 `0.3s` 같은 소요시간이 출력되므로 "언제나 경고"라고 놀라지 말 것.

### 2단계: 빌드 — 실제 러너 결과를 게이트로 판정하기

먼저 **건강한 실험**으로 게이트가 통과하는지 확인:

```bash
python research/failure_prediction/experiment_runner.py
python -m src.validation_gate "$(ls -t research/failure_prediction/results/run_*/metrics.json | head -1)"
```

> 셸 글로브(`run_*/metrics.json`)를 그대로 넘기면 `__main__`은 `sys.argv[1]`만 읽어
> **가장 오래된** run이 선택된다. `ls -t | head -1`로 최신 것을 명시적으로 고른다.

이제 **의도적으로 과적합을 유발**해서 게이트가 기각하는지 보자:

```bash
python - <<'PY'
import copy, sys; sys.path.insert(0, '.')
from research.failure_prediction import experiment_runner as runner
from src.validation_gate import evaluate_gate

# 과적합 유발: 샘플을 줄이고 깊은 RF로 train을 외우게 한다
cfg = copy.deepcopy(runner.get_config())
cfg["n_samples"] = 300
cfg["model_type"] = "random_forest"
cfg["model_params"] = {"n_estimators": 300, "max_depth": None}

result = runner.run_experiment(cfg)
gate = evaluate_gate(result["metrics"])
print("score:", result["score"])
print("accepted:", gate.accepted)
print("reason:", gate.reason)

# 3단계에서 재사용하도록 결과를 임시 파일로 덤프 (메모리 밖으로 보존)
import json
with open("/tmp/gate_reject_demo.json", "w") as fh:
    json.dump({"metrics": result["metrics"]}, fh)
PY
```

**예상 결과**: `train_f1=1.0, test_f1≈0.74, gap≈0.26` → `accepted: False`
이유: `train-test f1 gap 0.263 (limit 0.15)`

### 3단계: 검증 — 기각 사유를 구조체로 확인

```bash
python - <<'PY'
import sys, json; sys.path.insert(0, '.')
from src.validation_gate import evaluate_gate

# 2단계에서 덤프한 과적합 데모 결과로 게이트 판정
metrics = json.load(open("/tmp/gate_reject_demo.json"))["metrics"]
r = evaluate_gate(metrics)
print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))
PY
```

각 규칙마다 `passed`와 `reason`이 붙어 나온다. **기각 이유가 숫자와 함께 문서화**되어
에이전트가 "다음에 뭘 바꿀지"에 대한 근거를 얻는다.
(`run_*` 폴더에는 `_run_and_save()`가 저장한 `metrics.json`이 있고, `python -m src.validation_gate <파일>`로 명령줄에서도 판정할 수 있다)

### 4단계: 확장 — 자기만의 검증 규칙 추가하기

이제 나만의 규칙을 하나 추가해보자. 예: **클래스 불균형 심각도 확인** — minority 비율이 5% 미만이면 warning.
(아직 러너는 `minority_ratio` 지표를 만들지 않으므로, 아래 확인 단계에서는 수동 dict로 검증한다)

```bash
cat >> src/validation_gate.py <<'PY'


def _check_imbalance_alert(metrics: dict) -> GateCheck:
    """(예시) minority 클래스가 과도하게 적으면 warning."""
    minority = metrics.get("minority_ratio")
    if minority is not None and minority < 0.05:
        return GateCheck(
            name="imbalance_alert",
            passed=True,  # warning — 기각하지 않는다
            reason=f"minority_ratio {minority:.3f} < 0.05 (정보용)",
            severity="warning",
        )
    return GateCheck(
        name="imbalance_alert",
        passed=True,
        reason="미기록 또는 정상 범위",
        severity="warning",
    )


RULES.append(_check_imbalance_alert)  # ★ 함수 정의 뒤에 등록 — 순서 문제 없음
PY
```

> **중요**: 규칙 함수 시그니처는 반드시 `(metrics: dict)` — `evaluate_gate()`가
> `rule(metrics)` 형태로 호출하기 때문이다(`validation_gate.py`의 `evaluate_gate` 참고).
> 그리고 등록은 `RULES = [...]` 리스트 **편집이 아니라** `RULES.append(...)`로 한다.
> `cat >>`는 파일 맨 끝(적절한 기존 `RULES` 정의 **아래**)에 코드를 붙이므로,
> "목록에 이름 추가" 방식이면 함수 정의보다 앞에서 참조해 `NameError`가 난다.

등록이 동작하는지 확인:

```bash
python - <<'PY'
import sys; sys.path.insert(0, '.')
from src.validation_gate import RULES, evaluate_gate
print("현재 규칙:", [r.__name__ for r in RULES])

# 실제 metrics로 새 규칙도 함께 판정되는지
m = {"f1": 0.8, "train_f1": 0.9, "recall": 0.9, "precision": 0.8, "pr_auc": 0.7, "minority_ratio": 0.03}
r = evaluate_gate(m)
import json
print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))
PY
```

names 끝에 `_check_imbalance_alert`가 보이고 `imbalance_alert` 체크가 warning으로 합류하면 성공이다.

## 이해 확인

1. train_f1과 f1의 갭이 크다는 것은 무슨 의미인가?
2. `accepted: False`일 때 사용자가 알 수 있어야 하는 정보는 무엇인가?
3. 게이트를 `True/False` 대신 `GateResult`라는 구조체로 만드는 이유는?
4. 지표 게이밍(metric gaming)이 왜 위험한가?

## opencode에게 물어보세요
```
src/validation_gate.py를 읽고, 현재 규칙 중 하나(예: overfitting)의 임계값을
과학적으로 정하는 방법을 제시해줘. 그리고 'sample_size'나 'class_balance'의
경고를 추가하려면 어떻게 해야 하는지 알려줘.
```

## 다음 레슨
[J3. 제안→검증→적용](33_propose_validate_apply.md) — 변경을 근거와 함께 남기고 받아들이는 루프