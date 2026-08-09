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

`src/validation_gate.py`에 4개 규칙이 이미 있다:

| 규칙 | 판정 기준 | 심각도 |
|------|-----------|--------|
| `overfitting` | train-test F1/R² 갭 > 0.15 | error |
| `threshold_collapse` | recall>=1.0 & precision<0.3 | error |
| `random_model` | PR-AUC <= 0.5 | error |
| `elapsed` | 180초 초과 | warning |

### 2단계: 빌드 — 실제 러너 결과를 게이트로 판정하기

먼저 **건강한 실험**으로 게이트가 통과하는지 확인:

```bash
python research/failure_prediction/experiment_runner.py
python -m src.validation_gate research/failure_prediction/results/run_*/metrics.json
```

> 마지막 `run_*` 폴더를 명시하거나, 끝의 metrics.json을 지정하면 된다.
> 셸 확장으로 여러 파일이 전달되면 첫 번째만 쓰이니, 최신 것 하나를 지정하자.

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
PY
```

**예상 결과**: `train_f1=1.0, test_f1≈0.74, gap≈0.26` → `accepted: False`
이유: `train-test f1 gap 0.263 (limit 0.15)`

### 3단계: 검증 — 기각 사유를 구조체로 확인

```bash
python - <<'PY'
import sys, json, glob; sys.path.insert(0, '.')
from src.validation_gate import evaluate_gate

# 최신 실패 실험의 metrics.json으로 게이트 판정
f = sorted(glob.glob("research/failure_prediction/results/run_*/metrics.json"))[-1]
metrics = json.load(open(f))["metrics"]
r = evaluate_gate(metrics)
print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))
PY
```

각 규칙마다 `passed`와 `reason`이 붙어 나온다. **기각 이유가 숫자와 함께 문서화**되어
에이전트가 "다음에 뭘 바꿀지"에 대한 근거를 얻는다.

### 4단계: 확장 — 자기만의 검증 규칙 추가하기

이제 나만의 규칙을 하나 추가해보자. 예: **클래스 불균형 심각도 확인** — minority 비율이 5% 미만이면 warning.

```bash
# src/validation_gate.py에 함수를 추가 (복사용)
cat >> src/validation_gate.py <<'PY'

def _check_imbalance_alert(config: dict) -> GateCheck:
    """(예시) minority 클래스가 과도하게 적으면 warning."""
    return GateCheck(
        name="imbalance_alert",
        passed=True,
        reason="모니터링용 규칙 (과도한 불균형 시 재검토 권장)",
        severity="warning",
    )
PY
```

> 참고: `RULES` 목록에 등록해야 실행된다. 수정 후 `python -m src.validation_gate`로 통합 동작을 확인한다.

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
[J3. 제안→검증→적용](33_propose_validate_apply.md) — 변경 근거를 남기고 롤백이 가능한 루프