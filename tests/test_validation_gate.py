"""src/validation_gate — 규칙·evaluate_gate·CLI 단위 테스트."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.validation_gate import GateCheck, GateResult, RULES, evaluate_gate

ROOT = Path(__file__).resolve().parents[1]


def _metrics(**kw) -> dict:
    """기본적으로 게이트를 통과하는 healthy metrics."""
    base = {
        "accuracy": 0.9,
        "precision": 0.85,
        "recall": 0.82,
        "f1": 0.83,
        "train_accuracy": 0.95,
        "train_f1": 0.91,
        "train_precision": 0.9,
        "train_recall": 0.89,
        "roc_auc": 0.95,
        "pr_auc": 0.9,
        "elapsed_sec": 1.2,
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------------------
# 규칙 개별 확인
# ---------------------------------------------------------------------------

class TestOverfitting:
    def test_gap_within_limit_passes(self):
        m = _metrics(train_f1=0.91, f1=0.86)  # gap 0.05
        c = _first_check(m, "overfitting")
        assert c.passed, c.reason

    def test_gap_over_limit_rejects(self):
        m = _metrics(train_f1=1.0, f1=0.74)  # gap 0.26
        c = _first_check(m, "overfitting")
        assert not c.passed
        assert "0.260" in c.reason

    def test_gap_just_under_limit_passes(self):
        m = _metrics(train_f1=0.94, f1=0.80)  # gap 0.14 → 통과
        c = _first_check(m, "overfitting")
        assert c.passed, c.reason

    def test_gap_just_over_limit_rejects(self):
        m = _metrics(train_f1=0.90, f1=0.70)  # gap 0.20 → 기각
        c = _first_check(m, "overfitting")
        assert not c.passed, c.reason

    def test_regression_branch(self):
        m = _metrics().copy()
        for k in ("train_f1", "f1", "train_accuracy", "train_precision", "train_recall", "precision", "recall"):
            m.pop(k, None)
        m["train_r2"] = 0.9
        m["r2"] = 0.6  # 회귀 갭 0.3
        c = _first_check(m, "overfitting")
        assert not c.passed
        assert "r2 gap" in c.reason

    def test_missing_train_flags_warning(self):
        m = _metrics().copy()
        m.pop("train_f1")
        c = _first_check(m, "overfitting")
        assert c.passed and c.severity == "warning"

    def test_missing_recall_precision_warning(self):
        m = _metrics().copy()
        m.pop("recall")
        m.pop("precision")
        c = _first_check(m, "threshold_collapse")
        assert c.passed and c.severity == "warning"

    def test_missing_pr_auc_warning(self):
        m = _metrics().copy()
        m.pop("pr_auc")
        c = _first_check(m, "random_model")
        assert c.passed and c.severity == "warning"


class TestThresholdCollapse:
    def test_collapse_rejects(self):
        m = _metrics(recall=1.0, precision=0.1)
        c = _first_check(m, "threshold_collapse")
        assert not c.passed

    def test_normal_passes(self):
        m = _metrics(recall=0.9, precision=0.85)
        c = _first_check(m, "threshold_collapse")
        assert c.passed

    def test_recall_below_1_not_collapse(self):
        m = _metrics(recall=0.99, precision=0.1)  # recall<1.0 → 붕괴 아님
        c = _first_check(m, "threshold_collapse")
        assert c.passed


class TestRandomModel:
    def test_pr_auc_below_0_5_rejects(self):
        m = _metrics(pr_auc=0.45)
        c = _first_check(m, "random_model")
        assert not c.passed

    def test_at_0_5_borderline_rejects(self):
        m = _metrics(pr_auc=0.5)
        c = _first_check(m, "random_model")
        assert not c.passed, "0.5 이면 랜덤 수준"

    def test_above_0_5_passes(self):
        m = _metrics(pr_auc=0.51)
        c = _first_check(m, "random_model")
        assert c.passed


class TestElapsed:
    def test_fast_passes_warning(self):
        c = _first_check(_metrics(elapsed_sec=1.2), "elapsed")
        assert c.passed and c.severity == "warning"

    def test_slow_is_warning_not_error(self):
        c = _first_check(_metrics(elapsed_sec=500), "elapsed")
        assert c.passed and c.severity == "warning"  # 기각하지 않는다
        assert "500s" in c.reason

    def test_missing_is_warning(self):
        m = _metrics().copy()
        m.pop("elapsed_sec")
        c = _first_check(m, "elapsed")
        assert c.passed and c.severity == "warning"


# ---------------------------------------------------------------------------
# evaluate_gate 전체 판정
# ---------------------------------------------------------------------------

class TestEvaluateGate:
    def test_healthy_accepted(self):
        r = evaluate_gate(_metrics())
        assert r.accepted
        assert len(r.checks) == len(RULES)

    def test_appended_rule_registered_and_runs(self):
        # J2 4단계가 가르치는 "RULES.append()로 규칙 추가" 계약을 보호
        def _probe(metrics: dict) -> GateCheck:
            return GateCheck(name="probe_rule", passed=True, reason="ok", severity="warning")

        before = list(RULES)
        RULES.append(_probe)
        try:
            r = evaluate_gate(_metrics())
            assert len(r.checks) == len(before) + 1
            assert any(c.name == "probe_rule" for c in r.checks)
        finally:
            RULES[:] = before
        assert len(RULES) == len(before)

    def test_error_rule_fail_rejects(self):
        r = evaluate_gate(_metrics(train_f1=1.0, f1=0.70))
        assert not r.accepted
        assert all(c.name != "overfitting" or not c.passed for c in r.checks)

    def test_warning_only_still_accepted(self):
        r = evaluate_gate(_metrics(elapsed_sec=999))
        assert r.accepted
        assert any(c.name == "elapsed" and c.severity == "warning" for c in r.checks)

    def test_exact_limit_015_passes(self):
        # 0.95-0.80은 근사 계산에서 0.14999… → 0.15 한계 바로 아래로 통과
        r = evaluate_gate(_metrics(train_f1=0.95, f1=0.80))
        c = next(c for c in r.checks if c.name == "overfitting")
        assert c.passed, c.reason

    def test_limit_adjacent_above_rejects(self):
        # 0.9501-0.80 → 0.15009... → 한계 초과로 기각
        r = evaluate_gate(_metrics(train_f1=0.9501, f1=0.80))
        c = next(c for c in r.checks if c.name == "overfitting")
        assert not c.passed, c.reason

    def test_config_arg_ignored(self):
        # config 인자는 예약이지만 규칙은 metrics만 본다
        r1 = evaluate_gate(_metrics(train_f1=1.0, f1=0.7))
        r2 = evaluate_gate(_metrics(train_f1=1.0, f1=0.7), {"model_type": "any"})
        assert r1.to_dict() == r2.to_dict()


# ---------------------------------------------------------------------------
# GateResult API
# ---------------------------------------------------------------------------

class TestGateResult:
    def test_reason_includes_informational_warnings(self):
        # elapsed는 정보용 규칙이라 통과해도 reason에 소요시간이 남는다
        r = evaluate_gate(_metrics())
        assert "1.2s" in r.reason

    def test_reason_lists_failures(self):
        r = evaluate_gate(_metrics(train_f1=1.0, f1=0.7, recall=1.0, precision=0.1))
        assert "train-test" in r.reason

    def test_warnings_in_reason_when_passed(self):
        r = evaluate_gate(_metrics(elapsed_sec=300))
        assert "300s" in r.reason

    def test_to_dict_shape(self):
        d = evaluate_gate(_metrics()).to_dict()
        assert set(d) == {"accepted", "reason", "checks"}
        assert isinstance(d["checks"], list)
        assert set(d["checks"][0]) == {"name", "passed", "reason", "severity"}


# ---------------------------------------------------------------------------
# CLI 진입점 (python -m src.validation_gate <metrics.json>)
# ---------------------------------------------------------------------------

class TestCli:
    def test_smoke_offline_default(self):
        proc = subprocess.run(
            [sys.executable, "-m", "src.validation_gate"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert isinstance(data["checks"], list)

    def test_reads_metrics_file(self, tmp_path):
        p = tmp_path / "m.json"
        p.write_text(json.dumps({"metrics": _metrics(train_f1=1.0, f1=0.7)}))
        proc = subprocess.run(
            [sys.executable, "-m", "src.validation_gate", str(p)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert proc.returncode == 0
        assert json.loads(proc.stdout)["accepted"] is False


def _first_check(metrics: dict, name: str) -> GateCheck:
    r = evaluate_gate(metrics)
    checks = [c for c in r.checks if c.name == name]
    assert len(checks) == 1, f"규칙 {name!r}이 {len(checks)}개"
    return checks[0]