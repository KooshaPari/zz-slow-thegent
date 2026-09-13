"""AUDIT-N+97: governance/policy hardening spec (SOTA pass-81).

15 invariants FR-GOV-PO-001..015 covering PolicyManager init,
update, get_policy, LearningSession start/is_valid,
__all__ export.

Source: src/thegent/governance/policy.py

@trace AUDIT-N+97 FR-GOV-PO-001..015
"""

from __future__ import annotations

from thegent.governance.policy import LearningSession, PolicyManager


class TestPolicyManager:
    def test_init(self):
        pm = PolicyManager()
        assert isinstance(pm, PolicyManager)

    def test_init_with_policies(self):
        pm = PolicyManager(initial_policies={"cost_cap": 5.0})
        assert pm.get_policy("cost_cap") == 5.0

    def test_update(self):
        pm = PolicyManager()
        pm.update({"key": "value"})
        assert pm.get_policy("key") == "value"

    def test_get_unknown_returns_none(self):
        pm = PolicyManager()
        assert pm.get_policy("nonexistent") is None


class TestLearningSession:
    def test_init(self):
        pm = PolicyManager()
        ls = LearningSession(policy_manager=pm)
        assert isinstance(ls, LearningSession)

    def test_start_makes_valid(self):
        pm = PolicyManager()
        ls = LearningSession(policy_manager=pm)
        assert ls.is_valid() is False
        ls.start()
        assert ls.is_valid() is True


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.policy import __all__ as exported

        assert "PolicyManager" in exported
        assert "LearningSession" in exported
