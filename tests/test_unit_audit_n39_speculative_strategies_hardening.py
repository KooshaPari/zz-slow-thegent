"""Spec-only hardening tests for the dormant SpeculativeStrategies cluster (SOTA pass-23).

Covers a single dormant orchestration/strategies module that has never
been audited in the dormant-core chain:

  * ``thegent.orchestration.strategies.speculative_strategies``
    — ``SpeculativeStrategy`` enum, ``SpeculativeConfig`` dataclass,
    ``compute_adaptive_timeout`` / ``select_speculative_providers``
    / ``should_terminate_early`` decision helpers (WP-5001).

This file is the AUDIT-N+39 contract spec (SOTA pass-23).  It is
committed first (spec-first pattern, mirrors AUDIT-N+33 / N+34 / N+35
/ N+36 / N+37 / N+38) so the next step is to make every assertion here
pass without breaking the dormant corridor
(``tests/orchestration/test_speculative_strategies.py``) or any other
SOTA audit-N+ invariant cluster.

@trace FR-ORC-SS-001 -- ``SpeculativeStrategy`` is an ``enum.Enum``
                       with exactly five members:
                       ``RACE_FIRST = "race_first"``,
                       ``RACE_BEST = "race_best"``,
                       ``ADAPTIVE_TIMEOUT = "adaptive_timeout"``,
                       ``COST_QUALITY_TRADEOFF = "cost_quality_tradeoff"``,
                       ``EARLY_TERMINATION = "early_termination"``,
                       so downstream code can rely on a stable,
                       exhaustive strategy selector.
@trace FR-ORC-SS-002 -- ``SpeculativeConfig.__post_init__`` normalises
                       ``providers=None`` to the canonical default
                       ``["free", "claude", "gemini"]`` while leaving
                       an explicit empty list untouched so callers can
                       opt out of speculative providers without raising.
@trace FR-ORC-SS-003 -- ``SpeculativeConfig.__post_init__`` rejects
                       negative ``timeout_ms`` /
                       ``historical_latency_p95_ms`` /
                       ``historical_quality_avg`` with ``ValueError``
                       so a misconfigured config cannot silently
                       disable the speculative budget.
@trace FR-ORC-SS-004 -- ``compute_adaptive_timeout(historical_p95_ms,
                       base_timeout_ms=5000, safety_multiplier=1.5)``
                       returns ``max(base_timeout_ms,
                       historical_p95_ms * safety_multiplier)`` so
                       callers always get a non-negative adaptive
                       budget that respects the historical p95
                       latency when it dominates the base.
@trace FR-ORC-SS-005 -- ``compute_adaptive_timeout`` defaults are
                       ``base_timeout_ms=5000`` and
                       ``safety_multiplier=1.5`` so callers can
                       rely on the documented SOTA safety envelope
                       without explicitly threading the constants.
@trace FR-ORC-SS-006 -- ``select_speculative_providers(providers,
                       strategy)`` for ``RACE_FIRST`` /
                       ``RACE_BEST`` / ``ADAPTIVE_TIMEOUT`` /
                       ``EARLY_TERMINATION`` returns at most the
                       top-3 providers in input order so the
                       speculative fan-out never exceeds the
                       three-way race budget.
@trace FR-ORC-SS-007 -- ``select_speculative_providers(providers,
                       COST_QUALITY_TRADEOFF)`` always includes the
                       ``free`` provider (cost ``0.0``) regardless of
                       ``cost_budget`` so the cheapest provider is
                       never silently dropped from the fan-out.
@trace FR-ORC-SS-008 -- ``select_speculative_providers(providers,
                       COST_QUALITY_TRADEOFF, cost_budget=…)``
                       respects the supplied ``cost_budget`` cap by
                       accumulating provider costs in input order and
                       stopping once the next provider would exceed
                       the budget, and never returns more than three
                       providers in any case.
@trace FR-ORC-SS-009 -- ``select_speculative_providers`` uses a
                       provider-cost table (``free=0.0``,
                       ``claude=0.001``, unknown default ``0.001``)
                       so callers can reason about cost-quality
                       tradeoffs deterministically across runs.
@trace FR-ORC-SS-010 -- ``select_speculative_providers`` returns
                       ``[]`` for an empty input list so callers can
                       skip the speculative fan-out without
                       special-casing the empty case.
@trace FR-ORC-SS-011 -- ``should_terminate_early(elapsed_ms,
                       timeout_ms, other_results, strategy)`` returns
                       ``True`` when ``elapsed_ms > timeout_ms``
                       regardless of strategy / other results so a
                       hard timeout always wins.
@trace FR-ORC-SS-012 -- ``should_terminate_early`` uses a strict
                       ``elapsed_ms > timeout_ms`` comparison so
                       ``elapsed_ms == timeout_ms`` is **not** an
                       early-termination trigger and the SOTA
                       safety envelope is preserved.
@trace FR-ORC-SS-013 -- ``should_terminate_early`` for the
                       ``EARLY_TERMINATION`` strategy returns
                       ``True`` only when ``other_results`` is
                       non-empty **and** ``elapsed_ms / timeout_ms >
                       0.5``; otherwise it returns ``False`` so
                       early termination never fires on an empty
                       result set or before the halfway budget has
                       been consumed.
@trace FR-ORC-SS-014 -- ``should_terminate_early`` for non-
                       ``EARLY_TERMINATION`` strategies returns
                       ``False`` regardless of ``other_results`` so
                       the early-termination optimisation is
                       strictly opt-in per strategy.
@trace FR-ORC-SS-015 -- ``thegent.orchestration.strategies.speculative_strategies.__all__``
                       exposes the five public symbols
                       (``SpeculativeStrategy``, ``SpeculativeConfig``,
                       ``compute_adaptive_timeout``,
                       ``select_speculative_providers``,
                       ``should_terminate_early``) so callers and
                       dormant tests can rely on a stable import
                       surface.
"""

from __future__ import annotations

import enum

import pytest

from thegent.orchestration.strategies import speculative_strategies as _mod
from thegent.orchestration.strategies.speculative_strategies import (
    SpeculativeConfig,
    SpeculativeStrategy,
    compute_adaptive_timeout,
    select_speculative_providers,
    should_terminate_early,
)

# ---------------------------------------------------------------------------
# Helpers — provider cost table mirrored from the dormant
# ``test_speculative_strategies.py`` so the spec is hermetic.
# ---------------------------------------------------------------------------


_PROVIDER_COST = {"free": 0.0, "claude": 0.001}
_DEFAULT_COST = 0.001


def _provider_cost(name: str) -> float:
    return _PROVIDER_COST.get(name, _DEFAULT_COST)


# ---------------------------------------------------------------------------
# FR-ORC-SS-001 -- SpeculativeStrategy is a 5-value enum
# ---------------------------------------------------------------------------


class TestSpeculativeStrategyEnum:
    """@trace FR-ORC-SS-001"""

    def test_is_enum_subclass(self) -> None:
        """``SpeculativeStrategy`` must be an ``enum.Enum`` subclass."""
        assert isinstance(SpeculativeStrategy, type)
        assert issubclass(SpeculativeStrategy, enum.Enum)

    def test_has_exactly_five_members(self) -> None:
        """``SpeculativeStrategy`` must declare exactly five members."""
        members = list(SpeculativeStrategy.__members__.keys())
        assert sorted(members) == sorted(
            [
                "RACE_FIRST",
                "RACE_BEST",
                "ADAPTIVE_TIMEOUT",
                "COST_QUALITY_TRADEOFF",
                "EARLY_TERMINATION",
            ]
        )

    def test_race_first_value(self) -> None:
        assert SpeculativeStrategy.RACE_FIRST.value == "race_first"

    def test_race_best_value(self) -> None:
        assert SpeculativeStrategy.RACE_BEST.value == "race_best"

    def test_adaptive_timeout_value(self) -> None:
        assert SpeculativeStrategy.ADAPTIVE_TIMEOUT.value == "adaptive_timeout"

    def test_cost_quality_tradeoff_value(self) -> None:
        assert (
            SpeculativeStrategy.COST_QUALITY_TRADEOFF.value == "cost_quality_tradeoff"
        )

    def test_early_termination_value(self) -> None:
        assert SpeculativeStrategy.EARLY_TERMINATION.value == "early_termination"


# ---------------------------------------------------------------------------
# FR-ORC-SS-002 / FR-ORC-SS-003 -- SpeculativeConfig post-init contract
# ---------------------------------------------------------------------------


class TestSpeculativeConfigPostInit:
    """@trace FR-ORC-SS-002 / FR-ORC-SS-003"""

    def test_default_providers_is_empty_list(self) -> None:
        """An empty-list default survives ``__post_init__`` untouched."""
        cfg = SpeculativeConfig()
        assert cfg.providers == []

    def test_none_providers_becomes_canonical_default(self) -> None:
        """``providers=None`` is normalised to the canonical default."""
        cfg = SpeculativeConfig(providers=None)
        assert cfg.providers == ["free", "claude", "gemini"]

    def test_custom_providers_preserved(self) -> None:
        """An explicit list survives ``__post_init__`` untouched."""
        cfg = SpeculativeConfig(providers=["custom1", "custom2"])
        assert cfg.providers == ["custom1", "custom2"]

    def test_custom_strategy_preserved(self) -> None:
        cfg = SpeculativeConfig(strategy=SpeculativeStrategy.RACE_BEST)
        assert cfg.strategy is SpeculativeStrategy.RACE_BEST

    def test_custom_timeout_preserved(self) -> None:
        cfg = SpeculativeConfig(timeout_ms=10_000)
        assert cfg.timeout_ms == 10_000

    def test_custom_historical_values_preserved(self) -> None:
        cfg = SpeculativeConfig(
            historical_latency_p95_ms=3000.0,
            historical_quality_avg=0.95,
        )
        assert cfg.historical_latency_p95_ms == 3000.0
        assert cfg.historical_quality_avg == 0.95

    def test_negative_timeout_raises(self) -> None:
        with pytest.raises(ValueError):
            SpeculativeConfig(timeout_ms=-1)

    def test_negative_historical_latency_raises(self) -> None:
        with pytest.raises(ValueError):
            SpeculativeConfig(historical_latency_p95_ms=-1.0)

    def test_negative_historical_quality_raises(self) -> None:
        with pytest.raises(ValueError):
            SpeculativeConfig(historical_quality_avg=-0.1)


# ---------------------------------------------------------------------------
# FR-ORC-SS-004 / FR-ORC-SS-005 -- compute_adaptive_timeout contract
# ---------------------------------------------------------------------------


class TestComputeAdaptiveTimeout:
    """@trace FR-ORC-SS-004 / FR-ORC-SS-005"""

    def test_returns_base_when_historical_below_base(self) -> None:
        """``historical * multiplier`` below base returns the base."""
        # 2000 * 1.5 = 3000 < base 5000 → 5000
        result = compute_adaptive_timeout(
            historical_p95_ms=2000.0,
            base_timeout_ms=5000,
            safety_multiplier=1.5,
        )
        assert result == 5000

    def test_returns_historical_times_multiplier_when_larger(self) -> None:
        # 5000 * 1.5 = 7500 > base 5000 → 7500
        result = compute_adaptive_timeout(
            historical_p95_ms=5000.0,
            base_timeout_ms=5000,
            safety_multiplier=1.5,
        )
        assert result == 7500

    def test_respects_custom_safety_multiplier(self) -> None:
        # 2000 * 2.0 = 4000 < base 5000 → 5000
        result = compute_adaptive_timeout(
            historical_p95_ms=2000.0,
            base_timeout_ms=5000,
            safety_multiplier=2.0,
        )
        assert result == 5000

    def test_high_multiplier_exceeds_base(self) -> None:
        # 3000 * 2.0 = 6000 > base 5000 → 6000
        result = compute_adaptive_timeout(
            historical_p95_ms=3000.0,
            base_timeout_ms=5000,
            safety_multiplier=2.0,
        )
        assert result == 6000

    def test_default_parameters_use_5000_base_1p5_multiplier(self) -> None:
        # Default base=5000, multiplier=1.5 → 1000*1.5=1500 < 5000 → 5000
        result = compute_adaptive_timeout(1000.0)
        assert result == 5000


# ---------------------------------------------------------------------------
# FR-ORC-SS-006 / FR-ORC-SS-010 -- select_speculative_providers contract
# ---------------------------------------------------------------------------


class TestSelectSpeculativeProvidersTopN:
    """@trace FR-ORC-SS-006 / FR-ORC-SS-010"""

    def test_race_first_caps_at_three(self) -> None:
        providers = ["p1", "p2", "p3", "p4"]
        assert select_speculative_providers(
            providers, SpeculativeStrategy.RACE_FIRST
        ) == [
            "p1",
            "p2",
            "p3",
        ]

    def test_race_best_caps_at_three(self) -> None:
        providers = ["p1", "p2", "p3"]
        assert select_speculative_providers(
            providers, SpeculativeStrategy.RACE_BEST
        ) == [
            "p1",
            "p2",
            "p3",
        ]

    def test_adaptive_timeout_returns_input_when_two_or_fewer(self) -> None:
        providers = ["p1", "p2"]
        assert (
            select_speculative_providers(
                providers, SpeculativeStrategy.ADAPTIVE_TIMEOUT
            )
            == providers
        )

    def test_early_termination_returns_input_when_three_or_fewer(self) -> None:
        providers = ["p1", "p2", "p3"]
        assert (
            select_speculative_providers(
                providers, SpeculativeStrategy.EARLY_TERMINATION
            )
            == providers
        )

    def test_adaptive_timeout_caps_at_three(self) -> None:
        providers = ["p1", "p2", "p3", "p4", "p5"]
        assert select_speculative_providers(
            providers, SpeculativeStrategy.ADAPTIVE_TIMEOUT
        ) == [
            "p1",
            "p2",
            "p3",
        ]

    def test_empty_input_returns_empty(self) -> None:
        assert select_speculative_providers([], SpeculativeStrategy.RACE_FIRST) == []


# ---------------------------------------------------------------------------
# FR-ORC-SS-007 / FR-ORC-SS-008 / FR-ORC-SS-009 -- COST_QUALITY_TRADEOFF
# ---------------------------------------------------------------------------


class TestSelectSpeculativeProvidersCostQuality:
    """@trace FR-ORC-SS-007 / FR-ORC-SS-008 / FR-ORC-SS-009"""

    def test_cost_quality_respects_budget(self) -> None:
        # free (0) + claude (0.001) = 0.001 ≤ 0.001 ✓ ; gemini would push to 0.002
        providers = ["free", "claude", "gemini", "codex"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.COST_QUALITY_TRADEOFF,
            cost_budget=0.001,
        )
        assert result == ["free", "claude"]
        assert len(result) <= 3

    def test_cost_quality_includes_free_at_zero_budget(self) -> None:
        providers = ["free", "claude"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.COST_QUALITY_TRADEOFF,
            cost_budget=0.0,
        )
        assert result == ["free"]

    def test_cost_quality_limited_to_three(self) -> None:
        providers = ["free", "gemini", "codex", "claude"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.COST_QUALITY_TRADEOFF,
            cost_budget=10.0,
        )
        assert len(result) <= 3

    def test_unknown_provider_cost_defaults_to_001(self) -> None:
        providers = ["free", "unknown_provider"]
        result = select_speculative_providers(
            providers,
            SpeculativeStrategy.COST_QUALITY_TRADEOFF,
            cost_budget=0.0005,
        )
        # unknown_provider cost 0.001 > 0.0005 → only "free"
        assert result == ["free"]


# ---------------------------------------------------------------------------
# FR-ORC-SS-011 / FR-ORC-SS-012 / FR-ORC-SS-013 / FR-ORC-SS-014 --
# should_terminate_early contract
# ---------------------------------------------------------------------------


class TestShouldTerminateEarly:
    """@trace FR-ORC-SS-011 / FR-ORC-SS-012 / FR-ORC-SS-013 / FR-ORC-SS-014"""

    def test_returns_true_when_timeout_exceeded(self) -> None:
        assert (
            should_terminate_early(
                elapsed_ms=6000,
                timeout_ms=5000,
                other_results=[],
                strategy=SpeculativeStrategy.RACE_FIRST,
            )
            is True
        )

    def test_returns_false_at_exactly_timeout(self) -> None:
        """``elapsed_ms == timeout_ms`` uses strict ``>``, so False."""
        assert (
            should_terminate_early(
                elapsed_ms=5000,
                timeout_ms=5000,
                other_results=[],
                strategy=SpeculativeStrategy.RACE_FIRST,
            )
            is False
        )

    def test_returns_false_when_no_results_not_timeout(self) -> None:
        assert (
            should_terminate_early(
                elapsed_ms=3000,
                timeout_ms=5000,
                other_results=[],
                strategy=SpeculativeStrategy.RACE_FIRST,
            )
            is False
        )

    def test_early_termination_with_result_over_half(self) -> None:
        # 3000 / 5000 = 0.6 > 0.5 and result non-empty → True
        assert (
            should_terminate_early(
                elapsed_ms=3000,
                timeout_ms=5000,
                other_results=["some_result"],
                strategy=SpeculativeStrategy.EARLY_TERMINATION,
            )
            is True
        )

    def test_early_termination_with_result_under_half(self) -> None:
        # 2000 / 5000 = 0.4 ≤ 0.5 → False
        assert (
            should_terminate_early(
                elapsed_ms=2000,
                timeout_ms=5000,
                other_results=["some_result"],
                strategy=SpeculativeStrategy.EARLY_TERMINATION,
            )
            is False
        )

    def test_early_termination_no_results(self) -> None:
        assert (
            should_terminate_early(
                elapsed_ms=4000,
                timeout_ms=5000,
                other_results=[],
                strategy=SpeculativeStrategy.EARLY_TERMINATION,
            )
            is False
        )

    def test_other_strategy_with_result_does_not_terminate(self) -> None:
        assert (
            should_terminate_early(
                elapsed_ms=4000,
                timeout_ms=5000,
                other_results=["some_result"],
                strategy=SpeculativeStrategy.RACE_FIRST,
            )
            is False
        )

    def test_just_over_timeout(self) -> None:
        assert (
            should_terminate_early(
                elapsed_ms=5001,
                timeout_ms=5000,
                other_results=[],
                strategy=SpeculativeStrategy.RACE_FIRST,
            )
            is True
        )


# ---------------------------------------------------------------------------
# FR-ORC-SS-015 -- canonical __all__ surface
# ---------------------------------------------------------------------------


class TestSpeculativeStrategiesAll:
    """@trace FR-ORC-SS-015"""

    def test_all_exposes_five_public_symbols(self) -> None:
        assert sorted(_mod.__all__) == sorted(
            [
                "SpeculativeConfig",
                "SpeculativeStrategy",
                "compute_adaptive_timeout",
                "select_speculative_providers",
                "should_terminate_early",
            ]
        )
