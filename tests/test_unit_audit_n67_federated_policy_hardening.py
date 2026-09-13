# AUDIT-N+67: federated_policy hardening tests
"""Tests for federated_policy.py hardening — FR-GOV-FP-001 through FR-GOV-FP-022."""

from __future__ import annotations

import threading
from pathlib import Path

from thegent.governance.federated_policy import (
    FederatedPolicyEngine,
    PolicyRule,
    PolicyScope,
)


# ---------------------------------------------------------------------------
# FR-GOV-FP-001: PolicyScope has exactly 3 members
# ---------------------------------------------------------------------------
class TestFRGovFP001PolicyScopeMemberCount:
    def test_has_exactly_three_members(self) -> None:
        assert len(PolicyScope) == 3


# ---------------------------------------------------------------------------
# FR-GOV-FP-002: PolicyScope.LOCAL.value == 1
# ---------------------------------------------------------------------------
class TestFRGovFP002LocalValue:
    def test_local_value_is_one(self) -> None:
        assert PolicyScope.LOCAL.value == 1


# ---------------------------------------------------------------------------
# FR-GOV-FP-003: PolicyScope.REGIONAL.value == 2
# ---------------------------------------------------------------------------
class TestFRGovFP003RegionalValue:
    def test_regional_value_is_two(self) -> None:
        assert PolicyScope.REGIONAL.value == 2


# ---------------------------------------------------------------------------
# FR-GOV-FP-004: PolicyScope.GLOBAL.value == 3
# ---------------------------------------------------------------------------
class TestFRGovFP004GlobalValue:
    def test_global_value_is_three(self) -> None:
        assert PolicyScope.GLOBAL.value == 3


# ---------------------------------------------------------------------------
# FR-GOV-FP-005: PolicyRule.create() creates correct instance
# ---------------------------------------------------------------------------
class TestFRGovFP005CreateInstance:
    def test_create_returns_correct_instance(self) -> None:
        rule = PolicyRule.create(
            rule_id="r1",
            scope=PolicyScope.LOCAL,
            condition="enabled",
            action="allow",
            priority=10,
            namespace="team-a",
        )
        assert rule.rule_id == "r1"
        assert rule.scope == PolicyScope.LOCAL
        assert rule.condition == "enabled"
        assert rule.action == "allow"
        assert rule.priority == 10
        assert rule.namespace == "team-a"


# ---------------------------------------------------------------------------
# FR-GOV-FP-006: PolicyRule ordering by priority
# ---------------------------------------------------------------------------
class TestFRGovFP006Ordering:
    def test_rules_sorted_by_priority(self) -> None:
        r_low = PolicyRule.create("r1", PolicyScope.LOCAL, "c", "a", priority=1)
        r_mid = PolicyRule.create("r2", PolicyScope.LOCAL, "c", "a", priority=50)
        r_high = PolicyRule.create("r3", PolicyScope.LOCAL, "c", "a", priority=100)
        rules = [r_high, r_low, r_mid]
        assert sorted(rules) == [r_low, r_mid, r_high]


# ---------------------------------------------------------------------------
# FR-GOV-FP-007: PolicyRule.create() default namespace is 'global'
# ---------------------------------------------------------------------------
class TestFRGovFP007DefaultNamespace:
    def test_default_namespace_is_global(self) -> None:
        rule = PolicyRule.create("r1", PolicyScope.LOCAL, "c", "a", priority=1)
        assert rule.namespace == "global"


# ---------------------------------------------------------------------------
# FR-GOV-FP-008: FederatedPolicyEngine default_namespace is 'global'
# ---------------------------------------------------------------------------
class TestFRGovFP008EngineDefaultNamespace:
    def test_engine_default_namespace(self) -> None:
        engine = FederatedPolicyEngine()
        assert engine.default_namespace == "global"


# ---------------------------------------------------------------------------
# FR-GOV-FP-009: register() stores rule in correct namespace
# ---------------------------------------------------------------------------
class TestFRGovFP009RegisterStores:
    def test_register_stores_in_correct_namespace(self) -> None:
        engine = FederatedPolicyEngine()
        rule = PolicyRule.create("r1", PolicyScope.LOCAL, "c", "a", priority=1, namespace="ns-a")
        engine.register(rule)
        assert "ns-a" in engine._namespaces
        assert engine._namespaces["ns-a"]["r1"] is rule


# ---------------------------------------------------------------------------
# FR-GOV-FP-010: register() replaces existing rule with same id
# ---------------------------------------------------------------------------
class TestFRGovFP010RegisterReplaces:
    def test_register_replaces_same_id(self) -> None:
        engine = FederatedPolicyEngine()
        r1 = PolicyRule.create("r1", PolicyScope.LOCAL, "c", "a", priority=1)
        r2 = PolicyRule.create("r1", PolicyScope.GLOBAL, "c", "b", priority=2)
        engine.register(r1)
        engine.register(r2)
        assert engine._namespaces["global"]["r1"] is r2
        assert engine._namespaces["global"]["r1"].action == "b"


# ---------------------------------------------------------------------------
# FR-GOV-FP-011: resolve_policies returns empty for unknown namespace
# ---------------------------------------------------------------------------
class TestFRGovFP011ResolveUnknown:
    def test_resolve_empty_for_unknown(self) -> None:
        engine = FederatedPolicyEngine()
        result = engine.resolve_policies("nonexistent.ns")
        assert result == []


# ---------------------------------------------------------------------------
# FR-GOV-FP-012: resolve_policies includes global rules
# ---------------------------------------------------------------------------
class TestFRGovFP012ResolveIncludesGlobal:
    def test_global_rules_included(self) -> None:
        engine = FederatedPolicyEngine()
        g_rule = PolicyRule.create("g1", PolicyScope.GLOBAL, "c", "a", priority=1)
        engine.register(g_rule)
        result = engine.resolve_policies("team-a")
        assert any(r.rule_id == "g1" for r in result)


# ---------------------------------------------------------------------------
# FR-GOV-FP-013: resolve_policies - higher scope overrides same rule_id
# ---------------------------------------------------------------------------
class TestFRGovFP013HigherScopeOverrides:
    def test_higher_scope_wins_on_conflict(self) -> None:
        engine = FederatedPolicyEngine()
        local_rule = PolicyRule.create("r1", PolicyScope.LOCAL, "c", "allow", priority=1, namespace="team-a")
        global_rule = PolicyRule.create("r1", PolicyScope.GLOBAL, "c", "deny", priority=1)
        engine.register(local_rule)
        engine.register(global_rule)
        result = engine.resolve_policies("team-a")
        assert len(result) == 1
        assert result[0].action == "deny"


# ---------------------------------------------------------------------------
# FR-GOV-FP-014: evaluate filters by context
# ---------------------------------------------------------------------------
class TestFRGovFP014EvaluateFilters:
    def test_evaluate_filters_by_context(self) -> None:
        engine = FederatedPolicyEngine()
        r1 = PolicyRule.create("r1", PolicyScope.GLOBAL, "feature_a", "allow", priority=1)
        r2 = PolicyRule.create("r2", PolicyScope.GLOBAL, "feature_b", "deny", priority=2)
        engine.register(r1)
        engine.register(r2)
        result = engine.evaluate("default", {"feature_a": True})
        assert len(result) == 1
        assert result[0].rule_id == "r1"


# ---------------------------------------------------------------------------
# FR-GOV-FP-015: evaluate sorts by priority
# ---------------------------------------------------------------------------
class TestFRGovFP015EvaluateSorts:
    def test_evaluate_sorts_by_priority(self) -> None:
        engine = FederatedPolicyEngine()
        r1 = PolicyRule.create("r1", PolicyScope.GLOBAL, "feat", "a", priority=100)
        r2 = PolicyRule.create("r2", PolicyScope.GLOBAL, "feat", "b", priority=10)
        r3 = PolicyRule.create("r3", PolicyScope.GLOBAL, "feat", "c", priority=50)
        engine.register(r1)
        engine.register(r2)
        engine.register(r3)
        result = engine.evaluate("default", {"feat": True})
        assert [r.rule_id for r in result] == ["r2", "r3", "r1"]


# ---------------------------------------------------------------------------
# FR-GOV-FP-016: merge combines two engines
# ---------------------------------------------------------------------------
class TestFRGovFP016MergeCombines:
    def test_merge_combines_engines(self) -> None:
        e1 = FederatedPolicyEngine()
        e2 = FederatedPolicyEngine()
        e1.register(PolicyRule.create("r1", PolicyScope.LOCAL, "c", "a", priority=1))
        e2.register(PolicyRule.create("r2", PolicyScope.LOCAL, "c", "b", priority=2))
        merged = e1.merge(e2)
        resolved = merged.resolve_policies("default")
        rule_ids = {r.rule_id for r in resolved}
        assert "r1" in rule_ids
        assert "r2" in rule_ids


# ---------------------------------------------------------------------------
# FR-GOV-FP-017: merge - higher scope wins on conflict
# ---------------------------------------------------------------------------
class TestFRGovFP017MergeHigherScopeWins:
    def test_merge_higher_scope_wins(self) -> None:
        e1 = FederatedPolicyEngine()
        e2 = FederatedPolicyEngine()
        e1.register(PolicyRule.create("r1", PolicyScope.LOCAL, "c", "allow", priority=1))
        e2.register(PolicyRule.create("r1", PolicyScope.GLOBAL, "c", "deny", priority=1))
        merged = e1.merge(e2)
        resolved = merged.resolve_policies("default")
        assert len(resolved) == 1
        assert resolved[0].action == "deny"


# ---------------------------------------------------------------------------
# FR-GOV-FP-018: merge returns new engine (not mutating inputs)
# ---------------------------------------------------------------------------
class TestFRGovFP018MergeReturnsNew:
    def test_merge_does_not_mutate_inputs(self) -> None:
        e1 = FederatedPolicyEngine()
        e2 = FederatedPolicyEngine()
        e1.register(PolicyRule.create("r1", PolicyScope.LOCAL, "c", "a", priority=1))
        e2.register(PolicyRule.create("r2", PolicyScope.LOCAL, "c", "b", priority=2))
        merged = e1.merge(e2)

        # Inputs unchanged
        assert list(e1._namespaces.get("global", {}).keys()) == ["r1"]
        assert list(e2._namespaces.get("global", {}).keys()) == ["r2"]
        assert merged is not e1
        assert merged is not e2


# ---------------------------------------------------------------------------
# FR-GOV-FP-019: thread safety - concurrent register() is safe
# ---------------------------------------------------------------------------
class TestFRGovFP019ThreadSafety:
    def test_concurrent_registers_are_safe(self) -> None:
        engine = FederatedPolicyEngine()
        errors: list[Exception] = []

        def _register(rule: PolicyRule) -> None:
            try:
                engine.register(rule)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(
                target=_register,
                args=(
                    PolicyRule.create(
                        f"r{i}",
                        PolicyScope.LOCAL,
                        "c",
                        f"action-{i}",
                        priority=i,
                    ),
                ),
            )
            for i in range(100)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(engine._namespaces.get("global", {})) == 100


# ---------------------------------------------------------------------------
# FR-GOV-FP-020: __all__ exports if present
# ---------------------------------------------------------------------------
class TestFRGovFP020Exports:
    def test_all_exports_present(self) -> None:
        mod = __import__("thegent.governance.federated_policy", fromlist=["__all__"])
        if hasattr(mod, "__all__"):
            assert "FederatedPolicyEngine" in mod.__all__
            assert "PolicyRule" in mod.__all__
            assert "PolicyScope" in mod.__all__


# ---------------------------------------------------------------------------
# FR-GOV-FP-021: _lock is RLock (re-entrant)
# ---------------------------------------------------------------------------
class TestFRGovFP021LockIsReentrant:
    def test_lock_is_rlock(self) -> None:
        import threading

        engine = FederatedPolicyEngine()
        assert isinstance(engine._lock, type(threading.RLock()))
        # Verify re-entrancy: acquiring the lock twice from the same thread should not deadlock
        with engine._lock, engine._lock:
            pass  # No deadlock = pass


# ---------------------------------------------------------------------------
# FR-GOV-FP-022: load_from_file with non-existent path returns without error
# ---------------------------------------------------------------------------
class TestFRGovFP022LoadNonExistentFile:
    def test_load_nonexistent_returns(self, tmp_path: Path) -> None:
        engine = FederatedPolicyEngine()
        engine.load_from_file(tmp_path / "does_not_exist.json")
        # Should not raise; engine state unchanged
        assert engine._namespaces == {}


# ---------------------------------------------------------------------------
# AUDIT-N+67 comment block present in source
# ---------------------------------------------------------------------------
class TestAuditCommentBlock:
    def test_audit_comment_present(self) -> None:
        source = Path(__file__).resolve().parents[1] / "src" / "thegent" / "governance" / "federated_policy.py"
        first_line = source.read_text().splitlines()[0]
        assert first_line == "# AUDIT-N+67: federated_policy hardening — all contracts verified"
