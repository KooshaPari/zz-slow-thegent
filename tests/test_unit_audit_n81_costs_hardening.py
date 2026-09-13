"""AUDIT-N+81: governance/costs hardening spec (SOTA pass-65).

15 invariants FR-GOV-CS-001..015 covering CostCap init and check,
CostTracker session lifecycle, CostTracker auto-init guard,
BudgetAlert threshold, BudgetAlert zero-budget guard,
CostSensing check_cost_cap, CostSensing duck-type guard,
__all__ export, and deterministic behavior.

Source: src/thegent/governance/costs.py

@trace AUDIT-N+81 FR-GOV-CS-001..015
"""

from __future__ import annotations

from thegent.governance.costs import (
    BudgetAlert,
    CostCap,
    CostSensing,
    CostTracker,
)


class TestCostCap:
    def test_within_cap(self):
        cap = CostCap(max_cost=10.0)
        assert cap.check(5.0) is True

    def test_exceeds_cap(self):
        cap = CostCap(max_cost=10.0)
        assert cap.check(15.0) is False

    def test_exact_cap(self):
        cap = CostCap(max_cost=10.0)
        assert cap.check(10.0) is True

    def test_zero_cost(self):
        cap = CostCap(max_cost=10.0)
        assert cap.check(0.0) is True


class TestCostTracker:
    def test_start_and_record(self):
        ct = CostTracker()
        ct.start_session("s1")
        ct.record_cost("s1", 5.0)
        assert ct.get_session_cost("s1") == 5.0

    def test_auto_init_session(self):
        ct = CostTracker()
        ct.record_cost("s2", 3.0)
        assert ct.get_session_cost("s2") == 3.0

    def test_unknown_session_returns_zero(self):
        ct = CostTracker()
        assert ct.get_session_cost("unknown") == 0.0

    def test_is_within_budget(self):
        ct = CostTracker()
        ct.start_session("s3")
        ct.record_cost("s3", 5.0)
        assert ct.is_within_budget("s3", 10.0) is True
        assert ct.is_within_budget("s3", 3.0) is False


class TestBudgetAlert:
    def test_alert_when_exceeds_threshold(self):
        ba = BudgetAlert(threshold=0.8)
        ba.set_budget(100.0)
        assert ba.should_alert(90.0) is True

    def test_no_alert_below_threshold(self):
        ba = BudgetAlert(threshold=0.8)
        ba.set_budget(100.0)
        assert ba.should_alert(50.0) is False

    def test_zero_budget_no_alert(self):
        ba = BudgetAlert(threshold=0.8)
        ba.set_budget(0.0)
        assert ba.should_alert(100.0) is False

    def test_negative_budget_no_alert(self):
        ba = BudgetAlert(threshold=0.8)
        ba.set_budget(-10.0)
        assert ba.should_alert(5.0) is False


class TestCostSensing:
    def test_check_cost_cap_within(self):
        cs = CostSensing(slo_regulator=None)
        assert cs.check_cost_cap(5.0, 10.0) is True

    def test_check_cost_cap_exceeds(self):
        cs = CostSensing(slo_regulator=None)
        assert cs.check_cost_cap(15.0, 10.0) is False

    def test_get_cost_feedback_returns_dict(self):
        cs = CostSensing(slo_regulator=None)
        feedback = cs.get_cost_feedback("model-1")
        assert isinstance(feedback, dict)
        assert "status" in feedback

    def test_duck_type_guard_no_is_compliant(self):
        cs = CostSensing(slo_regulator=object())
        feedback = cs.get_cost_feedback("model-1")
        assert feedback["status"] == "optimal"


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.costs import __all__ as exported

        assert "CostCap" in exported
        assert "CostTracker" in exported
        assert "BudgetAlert" in exported
        assert "CostSensing" in exported
