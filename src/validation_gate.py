"""실험 결과 검증 게이트 모듈 (점수 기반 판정).

- `GateCheck`: 개별 검증 규칙 하나의 결과 (이름 / 통과 여부 / 근거 / 심각도)
- `GateResult`: 전체 게이트 판정 (error급 규칙이 모두 통과해야 accept)

핵심 원칙 (모듈 G 안전 + SkillOpt validation-gate 개념 차용):
1. 점수가 올랐다고 "개선됐다"고 판단하지 않는다. 근거(checks)를 남긴다.
2. 게이트는 최적화 대상(런너의 score 계산)과 독립이어야 한다.
3. 규칙은 metrics.json에 있는 값만으로 판정한다 (지표 게이트 한정).
4. 에이전트가 "지표 정의를 수정해 게이트를 우회"하지 못하게,
   게이트 규칙은 src/ 고정 모듈로 두고 에이전트는 rules 추가만 허용한다.

사용 예:
    from src.validation_gate import evaluate_gate
    result = evaluate_gate(metrics_dict)   # 규칙은 metrics 값을 기준으로만 판정
    if not result.accepted:
        print("기각:", result.reason)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GateCheck:
    """검증 규칙 하나의 결과."""

    name: str
    passed: bool
    reason: str
    severity: str = "error"  # 'error' | 'warning'


@dataclass
class GateResult:
    """전체 검증 판정 결과."""

    accepted: bool
    checks: list[GateCheck] = field(default_factory=list)

    @property
    def reason(self) -> str:
        """기각 사유(또는 통과 문구)를 한 줄로 요약한다."""
        failed = [c for c in self.checks if not c.passed and c.severity == "error"]
        if not failed:
            warnings = [c.reason for c in self.checks if c.severity == "warning"]
            return "; ".join(warnings) if warnings else "all checks passed"
        return "; ".join(c.reason for c in failed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "checks": [
                {"name": c.name, "passed": c.passed, "reason": c.reason, "severity": c.severity}
                for c in self.checks
            ],
        }


def _check_overfitting(metrics: dict) -> GateCheck:
    """과적합 검사: train-test F1 갭이 0.15를 넘으면 기각.

    분류: train_f1 - f1, 또는 멀티클래스 트레이너의 train_macro_f1 - macro_f1.
    회귀: train_r2 - r2. 필수 지표가 없으면 warning(미판정)으로 둔다.
    """
    if "train_f1" in metrics and "f1" in metrics:
        gap = metrics["train_f1"] - metrics["f1"]
        return GateCheck(
            name="overfitting",
            passed=gap <= 0.15,
            reason=f"train-test f1 gap {gap:.3f} (limit 0.15)",
        )
    if "train_macro_f1" in metrics and "macro_f1" in metrics:
        gap = metrics["train_macro_f1"] - metrics["macro_f1"]
        return GateCheck(
            name="overfitting",
            passed=gap <= 0.15,
            reason=f"train-test macro_f1 gap {gap:.3f} (limit 0.15)",
        )
    if "train_r2" in metrics and "r2" in metrics:
        gap = metrics["train_r2"] - metrics["r2"]
        return GateCheck(
            name="overfitting",
            passed=gap <= 0.15,
            reason=f"train-test r2 gap {gap:.3f} (limit 0.15)",
        )
    return GateCheck(
        name="overfitting",
        passed=True,
        reason="train 지표 없음 — 과적합 미판정",
        severity="warning",
    )


def _check_threshold_collapse(metrics: dict) -> GateCheck:
    """임계값 붕괴: recall=1.0 이면서 precision 급락 → 예측 판정이 무의미."""
    recall = metrics.get("recall")
    precision = metrics.get("precision")
    if recall is not None and precision is not None:
        collapse = recall >= 1.0 and precision < 0.3
        return GateCheck(
            name="threshold_collapse",
            passed=not collapse,
            reason=(
                f"recall={recall:.2f} / precision={precision:.2f} — "
                "모든 양성 예측이 잘못 붙어 있음" if collapse else "ok"
            ),
        )
    return GateCheck(
        name="threshold_collapse",
        passed=True,
        reason="재현율/정밀도 미기재 — 미판정",
        severity="warning",
    )


def _check_random_model(metrics: dict) -> GateCheck:
    """무의미 모델: PR-AUC가 0.5 이하면 랜덤 수준."""
    pr_auc = metrics.get("pr_auc")
    if pr_auc is not None:
        return GateCheck(
            name="random_model",
            passed=pr_auc > 0.5,
            reason=f"pr_auc={pr_auc:.3f} (random ≈ 0.5)",
        )
    return GateCheck(
        name="random_model",
        passed=True,
        reason="pr_auc 미기록 — 미판정",
        severity="warning",
    )


def _check_elapsed(metrics: dict) -> GateCheck:
    """비정상 지연: 180초 초과 시 warning (인프라 병목 신호)."""
    elapsed = metrics.get("elapsed_sec")
    if elapsed is None:
        return GateCheck(name="elapsed", passed=True, reason="미기록", severity="warning")
    if elapsed > 180:
        return GateCheck(
            name="elapsed",
            passed=True,
            reason=f"elapsed {elapsed:.0f}s — 과도한 지연",
            severity="warning",
        )
    return GateCheck(name="elapsed", passed=True, reason=f"{elapsed:.1f}s", severity="warning")


RULES = [
    _check_overfitting,
    _check_threshold_collapse,
    _check_random_model,
    _check_elapsed,
]


def evaluate_gate(metrics: dict, config: dict = None) -> GateResult:
    """metrics.json dict를 받아 전체 규칙을 적용하고 GateResult를 반환한다.

    accepted = 에러 심각도 규칙 전부 통과 (warning은 식별만).
    """
    checks = [rule(metrics) for rule in RULES]
    accepted = all(c.passed for c in checks if c.severity == "error")
    return GateResult(accepted=accepted, checks=checks)


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            payload = json.load(f)
        m = payload.get("metrics")
    else:
        m = {"f1": 0.7, "train_f1": 0.98, "recall": 1.0, "precision": 0.1, "pr_auc": 0.45}
    r = evaluate_gate(m)
    print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False))