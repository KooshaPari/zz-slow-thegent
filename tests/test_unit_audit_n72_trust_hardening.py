"""Hardening invariants for ``governance.trust`` — AUDIT-N+72.

15 invariants FR-GOV-TR-001 .. FR-GOV-TR-015 covering
TrustLevel enum, TrustBoundaryChecker (init, get_agent_trust,
evaluate_routing, check_data_flow, cache).

Source: src/thegent/governance/trust.py

@trace AUDIT-N+72  FR-GOV-TR-001..015
"""

from __future__ import annotations

import logging

import pytest

from thegent.governance.trust import (
    TrustBoundaryChecker,
    TrustLevel,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


class _FakeSettings:
    """Minimal stand-in for ThegentSettings."""


def _make_checker(cache_ttl_sec: int = 300) -> TrustBoundaryChecker:
    return TrustBoundaryChecker(_FakeSettings(), cache_ttl_sec=cache_ttl_sec)


# ---------------------------------------------------------------------------
# FR-GOV-TR-001
# ---------------------------------------------------------------------------


class TestFRGOVTR001TrustLevelMemberCount:
    def test_exactly_four_members(self) -> None:
        assert len(TrustLevel) == 4


# ---------------------------------------------------------------------------
# FR-GOV-TR-002
# ---------------------------------------------------------------------------


class TestFRGOVTR002TrustLevelValues:
    def test_external_is_zero(self) -> None:
        assert TrustLevel.EXTERNAL == 0

    def test_partner_is_one(self) -> None:
        assert TrustLevel.PARTNER == 1

    def test_internal_is_two(self) -> None:
        assert TrustLevel.INTERNAL == 2

    def test_strict_is_three(self) -> None:
        assert TrustLevel.STRICT == 3


# ---------------------------------------------------------------------------
# FR-GOV-TR-003
# ---------------------------------------------------------------------------


class TestFRGOVTR003TrustLevelOrdering:
    def test_external_lt_partner(self) -> None:
        assert TrustLevel.EXTERNAL < TrustLevel.PARTNER

    def test_partner_lt_internal(self) -> None:
        assert TrustLevel.PARTNER < TrustLevel.INTERNAL

    def test_internal_lt_strict(self) -> None:
        assert TrustLevel.INTERNAL < TrustLevel.STRICT


# ---------------------------------------------------------------------------
# FR-GOV-TR-004
# ---------------------------------------------------------------------------


class TestFRGOVTR004TrustBoundaryCheckerInit:
    def test_creates_instance(self) -> None:
        checker = _make_checker()
        assert isinstance(checker, TrustBoundaryChecker)

    def test_stores_settings(self) -> None:
        settings = _FakeSettings()
        checker = TrustBoundaryChecker(settings)
        assert checker.settings is settings


# ---------------------------------------------------------------------------
# FR-GOV-TR-005
# ---------------------------------------------------------------------------


class TestFRGOVTR005GetAgentTrustKnown:
    def test_interactive_agent_is_internal(self) -> None:
        checker = _make_checker()
        assert checker.get_agent_trust("interactive_agent") == TrustLevel.INTERNAL

    def test_copilot_is_external(self) -> None:
        checker = _make_checker()
        assert checker.get_agent_trust("copilot") == TrustLevel.EXTERNAL

    def test_gemini_is_external(self) -> None:
        checker = _make_checker()
        assert checker.get_agent_trust("gemini") == TrustLevel.EXTERNAL


# ---------------------------------------------------------------------------
# FR-GOV-TR-006
# ---------------------------------------------------------------------------


class TestFRGOVTR006GetAgentTrustUnknownReturnsExternal:
    def test_unknown_agent_returns_external(self) -> None:
        checker = _make_checker()
        assert checker.get_agent_trust("nonexistent-agent") == TrustLevel.EXTERNAL

    def test_empty_string_returns_external(self) -> None:
        checker = _make_checker()
        assert checker.get_agent_trust("") == TrustLevel.EXTERNAL


# ---------------------------------------------------------------------------
# FR-GOV-TR-007
# ---------------------------------------------------------------------------


class TestFRGOVTR007EvaluateRoutingAllowed:
    def test_no_sensitive_keywords_allows(self) -> None:
        checker = _make_checker()
        result = checker.evaluate_routing("deploy the widget", "interactive_agent")
        assert result["allowed"] is True
        assert result["reason"] is None
        assert result["risk_score"] == 0


# ---------------------------------------------------------------------------
# FR-GOV-TR-008
# ---------------------------------------------------------------------------


class TestFRGOVTR008EvaluateRoutingDeniedSensitive:
    def test_password_denied_for_external(self) -> None:
        checker = _make_checker()
        result = checker.evaluate_routing("send the password to copilot", "copilot")
        assert result["allowed"] is False
        assert "password" in result["reason"]  # type: ignore[operator]

    def test_secret_denied_for_external(self) -> None:
        checker = _make_checker()
        result = checker.evaluate_routing("expose the secret", "gemini")
        assert result["allowed"] is False

    def test_api_key_denied_for_external(self) -> None:
        checker = _make_checker()
        result = checker.evaluate_routing("rotate api_key now", "copilot")
        assert result["allowed"] is False


# ---------------------------------------------------------------------------
# FR-GOV-TR-009
# ---------------------------------------------------------------------------


class TestFRGOVTR009EvaluateRoutingCacheHit:
    def test_second_call_returns_cached(self) -> None:
        checker = _make_checker()
        first = checker.evaluate_routing("deploy the widget", "interactive_agent")
        second = checker.evaluate_routing("deploy the widget", "interactive_agent")
        assert first is second  # same object from cache


# ---------------------------------------------------------------------------
# FR-GOV-TR-010
# ---------------------------------------------------------------------------


class TestFRGOVTR010EvaluateRoutingRiskScoreViolation:
    def test_risk_score_ten_on_violation(self) -> None:
        checker = _make_checker()
        result = checker.evaluate_routing("send password", "copilot")
        assert result["risk_score"] == 10


# ---------------------------------------------------------------------------
# FR-GOV-TR-011
# ---------------------------------------------------------------------------


class TestFRGOVTR011EvaluateRoutingAgentTrustField:
    def test_agent_trust_field_is_name_string(self) -> None:
        checker = _make_checker()
        result = checker.evaluate_routing("hello", "copilot")
        assert result["agent_trust"] == "EXTERNAL"

    def test_agent_trust_internal_for_internal_agent(self) -> None:
        checker = _make_checker()
        result = checker.evaluate_routing("hello", "interactive_agent")
        assert result["agent_trust"] == "INTERNAL"


# ---------------------------------------------------------------------------
# FR-GOV-TR-012
# ---------------------------------------------------------------------------


class TestFRGOVTR012CheckDataFlowSameLevel:
    def test_same_level_returns_true(self) -> None:
        checker = _make_checker()
        assert checker.check_data_flow("interactive_agent", "headless_agent") is True

    def test_external_to_external_returns_true(self) -> None:
        checker = _make_checker()
        assert checker.check_data_flow("copilot", "gemini") is True


# ---------------------------------------------------------------------------
# FR-GOV-TR-013
# ---------------------------------------------------------------------------


class TestFRGOVTR013CheckDataFlowHigherToLowerLogged:
    def test_higher_to_lower_logs_info(self, caplog: pytest.LogCaptureFixture) -> None:
        checker = _make_checker()
        with caplog.at_level(logging.INFO, logger="thegent.governance.trust"):
            result = checker.check_data_flow("interactive_agent", "copilot")
        assert result is True
        assert "Cross-boundary data flow" in caplog.text


# ---------------------------------------------------------------------------
# FR-GOV-TR-014
# ---------------------------------------------------------------------------


class TestFRGOVTR014CacheTTLConfigured:
    def test_cache_ttl_is_configured(self) -> None:
        checker = _make_checker(cache_ttl_sec=60)
        assert checker._cache.ttl == 60

    def test_default_ttl_is_300(self) -> None:
        checker = _make_checker()
        assert checker._cache.ttl == 300


# ---------------------------------------------------------------------------
# FR-GOV-TR-015
# ---------------------------------------------------------------------------


class TestFRGOVTR015AgentTrustMapContainsExpected:
    def test_expected_agents_present(self) -> None:
        checker = _make_checker()
        expected = {
            "interactive_agent": TrustLevel.INTERNAL,
            "headless_agent": TrustLevel.INTERNAL,
            "cursor": TrustLevel.INTERNAL,
            "copilot": TrustLevel.EXTERNAL,
            "gemini": TrustLevel.EXTERNAL,
            "quality-agent": TrustLevel.INTERNAL,
        }
        for agent, level in expected.items():
            assert checker.agent_trust_map[agent] == level

    def test_evaluate_routing_empty_prompt(self) -> None:
        checker = _make_checker()
        result = checker.evaluate_routing("", "copilot")
        assert result["allowed"] is True
        assert result["risk_score"] == 0
