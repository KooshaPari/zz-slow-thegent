"""Hardening invariants for ``governance.policy_federation`` — AUDIT-N+73.

15 invariants FR-GOV-PF-001 .. FR-GOV-PF-015 covering
PolicyCache (init, get, set, invalidate, namespace sweep),
GovernanceConflictResolver (resolve, _is_more_restrictive),
GovernancePolicyFederation (init, evaluate, cache, escalation,
fail-open, delegation, SLA mapping, _policy_allows, empty policies).

Source: src/thegent/governance/policy_federation.py

@trace AUDIT-N+73  FR-GOV-PF-001..015
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from thegent.governance.policy_federation import (
    GovernanceConflictResolver,
    GovernancePolicyFederation,
    PolicyCache,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# FR-GOV-PF-001
# ---------------------------------------------------------------------------


class TestFRGOVPF001PolicyCacheInitGetSetInvalidate:
    """PolicyCache round-trip: init, get miss, set, get hit, invalidate."""

    def test_get_returns_none_on_miss(self) -> None:
        cache = PolicyCache(ttl_seconds=60)
        assert cache.get("ns", "key") is None

    def test_set_then_get_returns_value(self) -> None:
        cache = PolicyCache(ttl_seconds=60)
        cache.set("ns", "key", {"allow": True})
        assert cache.get("ns", "key") == {"allow": True}

    def test_invalidate_specific_key_removes_it(self) -> None:
        cache = PolicyCache(ttl_seconds=60)
        cache.set("ns", "key", {"allow": True})
        cache.invalidate("ns", "key")
        assert cache.get("ns", "key") is None


# ---------------------------------------------------------------------------
# FR-GOV-PF-002
# ---------------------------------------------------------------------------


class TestFRGOVPF002PolicyCacheInvalidateNamespaceSweep:
    """Invalidate without policy_key sweeps all keys in the namespace."""

    def test_sweep_removes_all_namespace_keys(self) -> None:
        cache = PolicyCache(ttl_seconds=60)
        cache.set("ns", "a", {"v": 1})
        cache.set("ns", "b", {"v": 2})
        cache.set("other", "a", {"v": 3})
        cache.invalidate("ns")
        assert cache.get("ns", "a") is None
        assert cache.get("ns", "b") is None
        # Other namespace untouched
        assert cache.get("other", "a") == {"v": 3}


# ---------------------------------------------------------------------------
# FR-GOV-PF-003
# ---------------------------------------------------------------------------


class TestFRGOVPF003ConflictResolverDeeperNamespacePrecedence:
    """Deeper namespace wins when resolve_governance_conflict merges."""

    def test_deeper_overrides_shallower(self) -> None:
        resolver = GovernanceConflictResolver()
        policies = [
            {"namespace": "org", "rules": {"cost_cap": 100}},
            {"namespace": "org.project", "rules": {"cost_cap": 50}},
        ]
        result = resolver.resolve_governance_conflict(policies, "org.project")
        assert result["cost_cap"] == 50

    def test_shallower_not_lost_when_different_key(self) -> None:
        resolver = GovernanceConflictResolver()
        policies = [
            {"namespace": "org", "rules": {"sla_minutes": 120}},
            {"namespace": "org.project", "rules": {"cost_cap": 50}},
        ]
        result = resolver.resolve_governance_conflict(policies, "org.project")
        assert result["sla_minutes"] == 120
        assert result["cost_cap"] == 50


# ---------------------------------------------------------------------------
# FR-GOV-PF-004
# ---------------------------------------------------------------------------


class TestFRGOVPF004IsMoreRestrictiveCostCapLowerWins:
    """_is_more_restrictive returns True when new cost_cap is lower."""

    def test_lower_cost_cap_is_more_restrictive(self) -> None:
        resolver = GovernanceConflictResolver()
        assert resolver._is_more_restrictive("cost_cap", 30, 50) is True

    def test_higher_cost_cap_is_not_more_restrictive(self) -> None:
        resolver = GovernanceConflictResolver()
        assert resolver._is_more_restrictive("cost_cap", 80, 50) is False

    def test_equal_cost_cap_is_not_more_restrictive(self) -> None:
        resolver = GovernanceConflictResolver()
        assert resolver._is_more_restrictive("cost_cap", 50, 50) is False


# ---------------------------------------------------------------------------
# FR-GOV-PF-005
# ---------------------------------------------------------------------------


class TestFRGOVPF005IsMoreRestrictiveAllowDenyWins:
    """_is_more_restrictive returns True when new allow is False (deny)."""

    def test_deny_over_allow(self) -> None:
        resolver = GovernanceConflictResolver()
        assert resolver._is_more_restrictive("allow", False, True) is True

    def test_allow_not_over_deny(self) -> None:
        resolver = GovernanceConflictResolver()
        assert resolver._is_more_restrictive("allow", True, False) is False

    def test_unknown_key_not_more_restrictive(self) -> None:
        resolver = GovernanceConflictResolver()
        assert resolver._is_more_restrictive("unknown", "a", "b") is False


# ---------------------------------------------------------------------------
# FR-GOV-PF-006
# ---------------------------------------------------------------------------


class TestFRGOVPF006FederationInitDefaults:
    """GovernancePolicyFederation __init__ creates all components with defaults."""

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_init_creates_all_components(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        fed = GovernancePolicyFederation()
        mock_engine_cls.assert_called_once_with(namespace="default")
        mock_eq_cls.assert_called_once()
        assert fed.cache is not None
        assert fed.conflict_resolver is not None

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_init_uses_provided_engine(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        custom_engine = MagicMock()
        fed = GovernancePolicyFederation(federated_engine=custom_engine)
        mock_engine_cls.assert_not_called()
        assert fed.federated_engine is custom_engine


# ---------------------------------------------------------------------------
# FR-GOV-PF-007
# ---------------------------------------------------------------------------


class TestFRGOVPF007EvaluateCacheMissResolves:
    """Cache miss triggers federated engine resolve and caches result."""

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_cache_miss_calls_resolve(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_engine.resolve_policy.return_value = {"allow": True}
        mock_engine_cls.return_value = mock_engine

        fed = GovernancePolicyFederation()
        result = fed.evaluate_governance_policy("ns", "cost_exceeded", {"run_id": "r1"})

        assert result is True
        mock_engine.resolve_policy.assert_called_once_with(namespace="ns", policy_key="governance.cost_exceeded")


# ---------------------------------------------------------------------------
# FR-GOV-PF-008
# ---------------------------------------------------------------------------


class TestFRGOVPF008EvaluateCacheHitSkipsResolution:
    """Cache hit skips federated engine resolution entirely."""

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_cache_hit_skips_resolve(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_engine_cls.return_value = mock_engine

        fed = GovernancePolicyFederation()
        # Prime the cache
        fed.cache.set("ns", "governance.cost_exceeded", {"allow": True})

        result = fed.evaluate_governance_policy("ns", "cost_exceeded", {"run_id": "r1"})

        assert result is True
        mock_engine.resolve_policy.assert_not_called()


# ---------------------------------------------------------------------------
# FR-GOV-PF-009
# ---------------------------------------------------------------------------


class TestFRGOVPF009EvaluateDeniedAddsToEscalation:
    """Denied policy adds an entry to the escalation queue."""

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_denied_adds_escalation(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_engine.resolve_policy.return_value = {"allow": False}
        mock_engine_cls.return_value = mock_engine

        mock_eq = MagicMock()
        mock_eq_cls.return_value = mock_eq

        fed = GovernancePolicyFederation()
        result = fed.evaluate_governance_policy("ns", "cost_exceeded", {"run_id": "r-abc"})

        assert result is False
        mock_eq.add.assert_called_once()
        call_kwargs = mock_eq.add.call_args
        assert call_kwargs[1]["run_id"] == "r-abc"
        assert "Policy denied" in call_kwargs[1]["reason"]


# ---------------------------------------------------------------------------
# FR-GOV-PF-010
# ---------------------------------------------------------------------------


class TestFRGOVPF010EvaluateFailOpenOnException:
    """Exception in policy resolution returns True (fail-open)."""

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_exception_returns_true(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_engine.resolve_policy.side_effect = RuntimeError("boom")
        mock_engine_cls.return_value = mock_engine

        fed = GovernancePolicyFederation()
        result = fed.evaluate_governance_policy("ns", "cost_exceeded", {"run_id": "r1"})

        assert result is True


# ---------------------------------------------------------------------------
# FR-GOV-PF-011
# ---------------------------------------------------------------------------


class TestFRGOVPF011InvalidateCacheDelegates:
    """invalidate_cache delegates to PolicyCache.invalidate."""

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_delegates_to_cache(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        fed = GovernancePolicyFederation()
        fed.cache.set("ns", "governance.x", {"allow": True})
        fed.invalidate_cache("ns", "governance.x")
        assert fed.cache.get("ns", "governance.x") is None

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_delegates_namespace_sweep(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        fed = GovernancePolicyFederation()
        fed.cache.set("ns", "a", {"v": 1})
        fed.cache.set("ns", "b", {"v": 2})
        fed.invalidate_cache("ns")
        assert fed.cache.get("ns", "a") is None
        assert fed.cache.get("ns", "b") is None


# ---------------------------------------------------------------------------
# FR-GOV-PF-012
# ---------------------------------------------------------------------------


class TestFRGOVPF012SLAMinutePriorityMapping:
    """SLA minutes map to correct escalation priority levels."""

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_urgent_priority_for_sla_15(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_engine.resolve_policy.return_value = {"allow": False, "sla_minutes": 10}
        mock_engine_cls.return_value = mock_engine
        mock_eq = MagicMock()
        mock_eq_cls.return_value = mock_eq

        fed = GovernancePolicyFederation()
        fed.evaluate_governance_policy("ns", "action", {"run_id": "r1"})
        assert mock_eq.add.call_args[1]["priority"] == 4  # URGENT

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_high_priority_for_sla_60(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_engine.resolve_policy.return_value = {"allow": False, "sla_minutes": 30}
        mock_engine_cls.return_value = mock_engine
        mock_eq = MagicMock()
        mock_eq_cls.return_value = mock_eq

        fed = GovernancePolicyFederation()
        fed.evaluate_governance_policy("ns", "action", {"run_id": "r1"})
        assert mock_eq.add.call_args[1]["priority"] == 3  # HIGH

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_normal_priority_for_sla_240(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_engine.resolve_policy.return_value = {"allow": False, "sla_minutes": 120}
        mock_engine_cls.return_value = mock_engine
        mock_eq = MagicMock()
        mock_eq_cls.return_value = mock_eq

        fed = GovernancePolicyFederation()
        fed.evaluate_governance_policy("ns", "action", {"run_id": "r1"})
        assert mock_eq.add.call_args[1]["priority"] == 2  # NORMAL

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_low_priority_for_sla_gt_240(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_engine.resolve_policy.return_value = {"allow": False, "sla_minutes": 480}
        mock_engine_cls.return_value = mock_engine
        mock_eq = MagicMock()
        mock_eq_cls.return_value = mock_eq

        fed = GovernancePolicyFederation()
        fed.evaluate_governance_policy("ns", "action", {"run_id": "r1"})
        assert mock_eq.add.call_args[1]["priority"] == 1  # LOW


# ---------------------------------------------------------------------------
# FR-GOV-PF-013
# ---------------------------------------------------------------------------


class TestFRGOVPF013PolicyAllowsExplicitAllow:
    """_policy_allows returns value of explicit 'allow' key."""

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_explicit_allow_true(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        fed = GovernancePolicyFederation()
        assert fed._policy_allows({"allow": True}, {}) is True

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_explicit_allow_false(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        fed = GovernancePolicyFederation()
        assert fed._policy_allows({"allow": False}, {}) is False


# ---------------------------------------------------------------------------
# FR-GOV-PF-014
# ---------------------------------------------------------------------------


class TestFRGOVPF014PolicyAllowsDefaultAllow:
    """_policy_allows defaults to True when no 'allow' key present."""

    @patch("thegent.governance.policy_federation.EscalationQueue")
    @patch("thegent.governance.policy_federation.FederatedPolicyEngine")
    def test_no_allow_key_defaults_true(self, mock_engine_cls: MagicMock, mock_eq_cls: MagicMock) -> None:
        fed = GovernancePolicyFederation()
        assert fed._policy_allows({"cost_cap": 50}, {}) is True


# ---------------------------------------------------------------------------
# FR-GOV-PF-015
# ---------------------------------------------------------------------------


class TestFRGOVPF015EmptyPoliciesListResolvesEmptyDict:
    """resolve_governance_conflict with empty list returns empty dict."""

    def test_empty_policies(self) -> None:
        resolver = GovernanceConflictResolver()
        result = resolver.resolve_governance_conflict([], "any.ns")
        assert result == {}
