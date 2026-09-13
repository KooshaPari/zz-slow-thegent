"""Tests for speculative execution strategies (WP-5001).

Tests for SpeculativeConfig, compute_adaptive_timeout,
select_speculative_providers, and should_terminate_early.
"""


from thegent.orchestration.strategies.speculative_strategies import (
    SpeculativeConfig,
    SpeculativeStrategy,
    compute_adaptive_timeout,
    select_speculative_providers,
    should_terminate_early,
)


class TestSpeculativeStrategy:
    """Tests for SpeculativeStrategy enum."""

    def test_race_first_value(self) -> None:
        """Verify RACE_FIRST enum value."""
        assert SpeculativeStrategy.RACE_FIRST.value == "race_first"

    def test_race_best_value(self) -> None:
        """Verify RACE_BEST enum value."""
        assert SpeculativeStrategy.RACE_BEST.value == "race_best"

    def test_adaptive_timeout_value(self) -> None:
        """Verify ADAPTIVE_TIMEOUT enum value."""
        assert SpeculativeStrategy.ADAPTIVE_TIMEOUT.value == "adaptive_timeout"

    def test_cost_quality_tradeoff_value(self) -> None:
        """Verify COST_QUALITY_TRADEOFF enum value."""
        assert SpeculativeStrategy.COST_QUALITY_TRADEOFF.value == "cost_quality_tradeoff"

    def test_early_termination_value(self) -> None:
        """Verify EARLY_TERMINATION enum value."""
        assert SpeculativeStrategy.EARLY_TERMINATION.value == "early_termination"


class TestSpeculativeConfig:
    """Tests for SpeculativeConfig dataclass."""

    def test_default_providers_is_empty(self) -> None:
        """Verify default providers is an empty list (from default_factory)."""
        config = SpeculativeConfig()

        # The default_factory=list provides an empty list
        # __post_init__ only replaces None, not empty list
        assert config.providers == []

    def test_custom_providers(self) -> None:
        """Verify custom providers are preserved."""
        config = SpeculativeConfig(providers=["custom1", "custom2"])

        assert config.providers == ["custom1", "custom2"]

    def test_none_providers_becomes_default(self) -> None:
        """Verify None providers becomes default list."""
        # Explicitly passing None should trigger __post_init__
        config = SpeculativeConfig(providers=None)
        assert config.providers == ["free", "claude", "gemini"]

    def test_custom_strategy(self) -> None:
        """Verify custom strategy can be set."""
        config = SpeculativeConfig(strategy=SpeculativeStrategy.RACE_BEST)

        assert config.strategy == SpeculativeStrategy.RACE_BEST

    def test_custom_timeout(self) -> None:
        """Verify custom timeout can be set."""
        config = SpeculativeConfig(timeout_ms=10000)

        assert config.timeout_ms == 10000

    def test_custom_historical_values(self) -> None:
        """Verify custom historical values can be set."""
        config = SpeculativeConfig(
            historical_latency_p95_ms=3000.0,
            historical_quality_avg=0.95,
        )

        assert config.historical_latency_p95_ms == 3000.0
        assert config.historical_quality_avg == 0.95


class TestComputeAdaptiveTimeout:
    """Tests for compute_adaptive_timeout function."""

    def test_uses_historical_p95_with_multiplier(self) -> None:
        """Verify historical p95 is used with safety multiplier."""
        result = compute_adaptive_timeout(
            historical_p95_ms=2000.0,
            base_timeout_ms=5000,
            safety_multiplier=1.5,
        )

        # 2000 * 1.5 = 3000, which is less than base 5000, so return 5000
        assert result == 5000

    def test_returns_historical_when_larger_than_base(self) -> None:
        """Verify historical * multiplier is returned when larger than base."""
        result = compute_adaptive_timeout(
            historical_p95_ms=5000.0,
            base_timeout_ms=5000,
            safety_multiplier=1.5,
        )

        # 5000 * 1.5 = 7500, which is larger than base 5000
        assert result == 7500

    def test_respects_custom_safety_multiplier(self) -> None:
        """Verify custom safety multiplier is used."""
        result = compute_adaptive_timeout(
            historical_p95_ms=2000.0,
            base_timeout_ms=5000,
            safety_multiplier=2.0,
        )

        # 2000 * 2.0 = 4000, still less than base 5000
        assert result == 5000

    def test_high_multiplier_exceeds_base(self) -> None:
        """Verify high multiplier can exceed base."""
        result = compute_adaptive_timeout(
            historical_p95_ms=3000.0,
            base_timeout_ms=5000,
            safety_multiplier=2.0,
        )

        # 3000 * 2.0 = 6000, which exceeds base 5000
        assert result == 6000

    def test_default_parameters(self) -> None:
        """Verify default parameters work."""
        result = compute_adaptive_timeout(1000.0)

        # 1000 * 1.5 = 1500 < 5000, so return 5000
        assert result == 5000


class TestSelectSpeculativeProviders:
    """Tests for select_speculative_providers function."""

    def test_race_first_returns_top_providers(self) -> None:
        """Verify RACE_FIRST returns top providers."""
        providers = ["provider1", "provider2", "provider3", "provider4"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.RACE_FIRST,
        )

        assert result == ["provider1", "provider2", "provider3"]

    def test_race_best_returns_top_providers(self) -> None:
        """Verify RACE_BEST returns top providers."""
        providers = ["provider1", "provider2", "provider3"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.RACE_BEST,
        )

        assert result == ["provider1", "provider2", "provider3"]

    def test_cost_quality_tradeoff_respects_budget(self) -> None:
        """Verify COST_QUALITY_TRADEOFF respects budget."""
        providers = ["free", "claude", "gemini", "codex"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.COST_QUALITY_TRADEOFF,
            cost_budget=0.001,  # Should fit free + claude
        )

        # free=0.0, claude=0.001
        # With budget 0.001: free (0) + claude (0.001) = 0.001 <= 0.001 ✓
        # gemini would push to 0.0011 > 0.001
        assert result == ["free", "claude"]
        assert len(result) <= 3

    def test_cost_quality_tradeoff_includes_free(self) -> None:
        """Verify COST_QUALITY_TRADEOFF always includes free."""
        providers = ["free", "claude"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.COST_QUALITY_TRADEOFF,
            cost_budget=0.0,
        )

        # Free has 0 cost, should always be included
        assert result == ["free"]

    def test_cost_quality_limited_to_three(self) -> None:
        """Verify COST_QUALITY_TRADEOFF limits to 3 providers."""
        providers = ["free", "gemini", "codex", "claude"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.COST_QUALITY_TRADEOFF,
            cost_budget=10.0,  # High budget to include all
        )

        assert len(result) <= 3

    def test_adaptive_timeout_returns_top_providers(self) -> None:
        """Verify ADAPTIVE_TIMEOUT returns top providers."""
        providers = ["provider1", "provider2"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.ADAPTIVE_TIMEOUT,
        )

        assert result == providers

    def test_early_termination_returns_top_providers(self) -> None:
        """Verify EARLY_TERMINATION returns top providers."""
        providers = ["provider1", "provider2", "provider3"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.EARLY_TERMINATION,
        )

        assert result == providers

    def test_unknown_provider_cost_defaults_to_001(self) -> None:
        """Verify unknown provider cost defaults to 0.001."""
        providers = ["free", "unknown_provider"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.COST_QUALITY_TRADEOFF,
            cost_budget=0.0005,  # Only free should fit
        )

        # unknown_provider costs 0.001, which exceeds 0.0005
        assert result == ["free"]

    def test_empty_providers_returns_empty(self) -> None:
        """Verify empty providers returns empty list."""
        result = select_speculative_providers(
            [],
            SpeculativeStrategy.RACE_FIRST,
        )

        assert result == []


class TestShouldTerminateEarly:
    """Tests for should_terminate_early function."""

    def test_returns_true_when_timeout_exceeded(self) -> None:
        """Verify True when elapsed exceeds timeout."""
        result = should_terminate_early(
            elapsed_ms=6000,
            timeout_ms=5000,
            other_results=[],
            strategy=SpeculativeStrategy.RACE_FIRST,
        )

        assert result is True

    def test_returns_false_when_no_results_not_timeout(self) -> None:
        """Verify False when no results and not timed out."""
        result = should_terminate_early(
            elapsed_ms=3000,
            timeout_ms=5000,
            other_results=[],
            strategy=SpeculativeStrategy.RACE_FIRST,
        )

        assert result is False

    def test_early_termination_with_result_over_half(self) -> None:
        """Verify EARLY_TERMINATION with result at > 50% timeout."""
        result = should_terminate_early(
            elapsed_ms=3000,  # 60% of 5000
            timeout_ms=5000,
            other_results=["some_result"],
            strategy=SpeculativeStrategy.EARLY_TERMINATION,
        )

        assert result is True

    def test_early_termination_with_result_under_half(self) -> None:
        """Verify EARLY_TERMINATION with result at < 50% timeout."""
        result = should_terminate_early(
            elapsed_ms=2000,  # 40% of 5000
            timeout_ms=5000,
            other_results=["some_result"],
            strategy=SpeculativeStrategy.EARLY_TERMINATION,
        )

        assert result is False

    def test_early_termination_no_results(self) -> None:
        """Verify EARLY_TERMINATION with no results returns False."""
        result = should_terminate_early(
            elapsed_ms=4000,
            timeout_ms=5000,
            other_results=[],
            strategy=SpeculativeStrategy.EARLY_TERMINATION,
        )

        assert result is False

    def test_other_strategy_with_result(self) -> None:
        """Verify other strategies don't terminate early with results."""
        result = should_terminate_early(
            elapsed_ms=4000,
            timeout_ms=5000,
            other_results=["some_result"],
            strategy=SpeculativeStrategy.RACE_FIRST,
        )

        assert result is False

    def test_exactly_at_timeout(self) -> None:
        """Verify exactly at timeout returns False (uses > not >=)."""
        result = should_terminate_early(
            elapsed_ms=5000,
            timeout_ms=5000,
            other_results=[],
            strategy=SpeculativeStrategy.RACE_FIRST,
        )

        # The function uses > not >=, so exactly at timeout is False
        assert result is False

    def test_just_over_timeout(self) -> None:
        """Verify just over timeout returns True."""
        result = should_terminate_early(
            elapsed_ms=5001,
            timeout_ms=5000,
            other_results=[],
            strategy=SpeculativeStrategy.RACE_FIRST,
        )

        assert result is True
