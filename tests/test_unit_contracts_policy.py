"""Unit tests for thegent.contracts.policy -- FallbackPolicy and evaluate_fallback."""

import pytest

from tests.conftest_factories import make_fallback_policy
from thegent.contracts.policy import FallbackPolicy, evaluate_fallback


@pytest.mark.unit
class TestFallbackPolicyConstruction:
    """Tests for FallbackPolicy dataclass defaults and construction."""

    def test_defaults(self) -> None:
        # @trace FR-CTR-008
        policy = FallbackPolicy()
        assert policy.allow_plain_fallback is True
        assert policy.min_confidence_threshold == 0.4
        assert policy.max_fallback_rate == 0.3
        assert policy.strict_providers == []

    def test_factory_defaults(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy()
        assert policy.allow_plain_fallback is True
        assert policy.strict_providers == []

    def test_custom_values(self) -> None:
        # @trace FR-CTR-008
        policy = FallbackPolicy(
            allow_plain_fallback=False,
            min_confidence_threshold=0.8,
            max_fallback_rate=0.1,
            strict_providers=["copilot", "gemini"],
        )
        assert policy.allow_plain_fallback is False
        assert policy.min_confidence_threshold == 0.8
        assert policy.strict_providers == ["copilot", "gemini"]


@pytest.mark.unit
class TestEvaluateFallback:
    """Tests for evaluate_fallback()."""

    def test_valid_non_fallback_no_issues(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy()
        issues = evaluate_fallback("copilot", 0.9, is_fallback=False, policy=policy)
        assert issues == []

    def test_strict_provider_fallback_violation(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy(strict_providers=["copilot"])
        issues = evaluate_fallback("copilot", 0.9, is_fallback=True, policy=policy)
        assert any("strict" in i.lower() for i in issues)

    def test_strict_provider_non_fallback_ok(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy(strict_providers=["copilot"])
        issues = evaluate_fallback("copilot", 0.9, is_fallback=False, policy=policy)
        assert not any("strict" in i.lower() for i in issues)

    def test_low_confidence_violation(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy(min_confidence_threshold=0.5)
        issues = evaluate_fallback("copilot", 0.3, is_fallback=False, policy=policy)
        assert any("confidence" in i.lower() for i in issues)

    def test_confidence_at_threshold_no_violation(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy(min_confidence_threshold=0.4)
        issues = evaluate_fallback("copilot", 0.4, is_fallback=False, policy=policy)
        assert not any("confidence" in i.lower() for i in issues)

    def test_high_fallback_rate_violation(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy(max_fallback_rate=0.2)
        stats = {"fallback_rate": 0.5}
        issues = evaluate_fallback("copilot", 0.9, is_fallback=False, policy=policy, stats=stats)
        assert any("fallback rate" in i.lower() for i in issues)

    def test_fallback_disabled_violation(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy(allow_plain_fallback=False)
        issues = evaluate_fallback("copilot", 0.9, is_fallback=True, policy=policy)
        assert any("disabled" in i.lower() for i in issues)

    def test_fallback_enabled_no_violation(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy(allow_plain_fallback=True)
        issues = evaluate_fallback("copilot", 0.9, is_fallback=True, policy=policy)
        assert not any("disabled" in i.lower() for i in issues)

    def test_multiple_violations_combined(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy(
            allow_plain_fallback=False,
            strict_providers=["copilot"],
            min_confidence_threshold=0.8,
        )
        issues = evaluate_fallback("copilot", 0.3, is_fallback=True, policy=policy)
        assert len(issues) >= 3

    def test_no_stats_skips_rate_check(self) -> None:
        # @trace FR-CTR-008
        policy = make_fallback_policy(max_fallback_rate=0.1)
        issues = evaluate_fallback("copilot", 0.9, is_fallback=False, policy=policy, stats=None)
        assert not any("fallback rate" in i.lower() for i in issues)
