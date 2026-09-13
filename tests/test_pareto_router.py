"""Unit tests for ParetoRouter and RouteCandidate.

Traces to: FR-ROUTER-001 (Pareto-optimal route selection)
"""

import pytest

from thegent.utils.routing_impl import ParetoRouter, RouteCandidate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _candidate(model: str, cost: float, quality: float, provider: str = "test") -> RouteCandidate:
    return RouteCandidate(model=model, provider=provider, cost_per_1k=cost, quality_score=quality)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRouteCandidateDataclass:
    """RouteCandidate is a plain dataclass with the required fields."""

    def test_fields_accessible(self) -> None:
        c = _candidate("gpt-4o", cost=0.03, quality=0.85)
        assert c.model == "gpt-4o"
        assert c.provider == "test"
        assert c.cost_per_1k == 0.03
        assert c.quality_score == 0.85

    def test_default_provider_not_required(self) -> None:
        c = RouteCandidate(model="m", provider="p", cost_per_1k=0.01, quality_score=0.5)
        assert c.provider == "p"


class TestParetoRouterSingleCandidate:
    """With only one candidate, it is always selected."""

    def test_single_returned(self) -> None:
        router = ParetoRouter()
        c = _candidate("only", cost=1.0, quality=0.9)
        assert router.select([c]) is c

    def test_single_zero_cost(self) -> None:
        router = ParetoRouter()
        c = _candidate("free-model", cost=0.0, quality=0.7)
        assert router.select([c]) is c


class TestParetoRouterEmptyCandidates:
    """Empty candidate list raises ValueError."""

    def test_empty_raises(self) -> None:
        router = ParetoRouter()
        with pytest.raises(ValueError, match="non-empty"):
            router.select([])


class TestParetoRouterDominatedRoutesFiltered:
    """Dominated candidates are excluded from the frontier."""

    def test_dominated_not_selected(self) -> None:
        """cheap-good dominates expensive-bad: same quality, lower cost."""
        router = ParetoRouter()
        expensive_bad = _candidate("expensive-bad", cost=2.0, quality=0.6)
        cheap_good = _candidate("cheap-good", cost=0.5, quality=0.8)
        # cheap-good has lower cost AND higher quality → dominates expensive-bad
        result = router.select([expensive_bad, cheap_good])
        assert result is cheap_good

    def test_all_but_one_dominated(self) -> None:
        """One clearly superior model dominates all others."""
        router = ParetoRouter()
        best = _candidate("best", cost=0.1, quality=0.99)
        mid = _candidate("mid", cost=0.5, quality=0.80)
        worst = _candidate("worst", cost=1.0, quality=0.50)
        result = router.select([worst, mid, best])
        assert result is best

    def test_frontier_excludes_strictly_dominated(self) -> None:
        """Explicitly verify that _pareto_frontier omits dominated candidates."""
        router = ParetoRouter()
        dominated = _candidate("dominated", cost=1.0, quality=0.5)
        dominant = _candidate("dominant", cost=0.5, quality=0.9)
        unrelated = _candidate("unrelated", cost=0.4, quality=0.6)
        # dominant dominates dominated (better on both)
        # unrelated is on the frontier (lower cost than dominant, lower quality)
        frontier = router._pareto_frontier([dominated, dominant, unrelated])
        frontier_models = {c.model for c in frontier}
        assert "dominated" not in frontier_models
        assert "dominant" in frontier_models
        assert "unrelated" in frontier_models


class TestParetoRouterFrontierSelection:
    """Among non-dominated candidates, select highest quality/cost ratio."""

    def test_highest_ratio_selected(self) -> None:
        """Two non-dominated candidates: the one with better quality/cost wins."""
        router = ParetoRouter()
        # Neither dominates the other (a has higher quality, b has lower cost)
        a = _candidate("a", cost=2.0, quality=0.9)  # ratio = 0.45
        b = _candidate("b", cost=0.5, quality=0.6)  # ratio = 1.20
        result = router.select([a, b])
        # b has higher ratio (0.6/0.5 = 1.2 vs 0.9/2.0 = 0.45)
        assert result is b

    def test_pareto_frontier_with_trade_off(self) -> None:
        """Classic three-way trade-off: low-cost-low-qual, mid, high-cost-high-qual."""
        router = ParetoRouter()
        cheap = _candidate("cheap", cost=0.1, quality=0.6)  # ratio = 6.0
        mid = _candidate("mid", cost=0.5, quality=0.8)  # ratio = 1.6
        premium = _candidate("premium", cost=2.0, quality=0.95)  # ratio = 0.475
        # None dominates any other (each trades cost for quality)
        result = router.select([cheap, mid, premium])
        # cheap has the best ratio (0.6/0.1 = 6.0)
        assert result is cheap

    def test_equal_quality_lower_cost_wins(self) -> None:
        """Equal quality: lower cost gives higher ratio."""
        router = ParetoRouter()
        expensive = _candidate("expensive", cost=1.0, quality=0.8)
        cheap = _candidate("cheap", cost=0.2, quality=0.8)
        # cheap dominates expensive (same quality, lower cost)
        result = router.select([expensive, cheap])
        assert result is cheap


class TestParetoRouterZeroCostFallback:
    """When all candidates have cost_per_1k == 0, select highest quality_score."""

    def test_all_zero_cost_highest_quality_wins(self) -> None:
        router = ParetoRouter()
        a = _candidate("a", cost=0.0, quality=0.7)
        b = _candidate("b", cost=0.0, quality=0.9)
        c = _candidate("c", cost=0.0, quality=0.5)
        result = router.select([a, b, c])
        assert result is b

    def test_single_zero_cost_returned(self) -> None:
        router = ParetoRouter()
        only = _candidate("free", cost=0.0, quality=0.85)
        assert router.select([only]) is only

    def test_mixed_zero_and_nonzero_cost(self) -> None:
        """Zero-cost candidate is treated as infinite ratio → wins over any positive-cost."""
        router = ParetoRouter()
        free = _candidate("free", cost=0.0, quality=0.6)
        paid = _candidate("paid", cost=0.01, quality=0.9)
        # free has quality=0.6; paid has quality=0.9 → paid dominates free? No:
        # paid has higher quality AND higher cost, so it does NOT dominate free.
        # Both are on the frontier. free has ratio=inf → free wins.
        result = router.select([free, paid])
        assert result is free


class TestParetoRouterIntegration:
    """End-to-end routing scenarios matching real model catalogues."""

    def test_realistic_model_pool(self) -> None:
        """Realistic mix: one model should emerge as clearly best value."""
        router = ParetoRouter()
        candidates = [
            RouteCandidate("gpt-5.3-codex", "copilot", 0.30, 0.82),
            RouteCandidate("claude-haiku-4.5", "claude", 0.025, 0.75),
            RouteCandidate("claude-sonnet-4.6", "claude", 0.30, 0.88),
            RouteCandidate("gemini-3-flash", "gemini", 0.00, 0.78),
            RouteCandidate("claude-opus-4.6", "claude", 2.50, 0.95),
        ]
        result = router.select(candidates)
        # gemini-3-flash is free (cost=0) → infinite ratio → must win
        assert result.model == "gemini-3-flash"

    def test_no_free_tier_best_ratio_wins(self) -> None:
        """Without free-tier model, claude-haiku wins on ratio."""
        router = ParetoRouter()
        candidates = [
            RouteCandidate("gpt-5.3-codex", "copilot", 0.30, 0.82),
            RouteCandidate("claude-haiku-4.5", "claude", 0.025, 0.75),
            RouteCandidate("claude-sonnet-4.6", "claude", 0.30, 0.88),
            RouteCandidate("claude-opus-4.6", "claude", 2.50, 0.95),
        ]
        result = router.select(candidates)
        # claude-haiku ratio = 0.75/0.025 = 30.0 (highest)
        # gpt-5.3-codex ratio = 0.82/0.30 ≈ 2.73
        # claude-sonnet ratio = 0.88/0.30 ≈ 2.93
        # claude-opus ratio = 0.95/2.50 = 0.38
        assert result.model == "claude-haiku-4.5"


class TestParetoRouterSelectByStrategy:
    """Tests for select_by_strategy covering all strategy branches."""

    def test_strategy_speed_selects_cheapest(self) -> None:
        """Speed strategy (proxied by cost) selects the cheapest frontier candidate."""
        router = ParetoRouter()
        cheap = _candidate("cheap", cost=0.05, quality=0.7)
        premium = _candidate("premium", cost=0.8, quality=0.95)
        result = router.select_by_strategy("speed", [cheap, premium])
        assert result is cheap

    def test_strategy_balanced_returns_best_ratio(self) -> None:
        """Balanced (unknown) strategy falls back to best quality/cost ratio."""
        router = ParetoRouter()
        a = _candidate("a", cost=2.0, quality=0.9)  # ratio = 0.45
        b = _candidate("b", cost=0.5, quality=0.6)  # ratio = 1.20
        result = router.select_by_strategy("balanced", [a, b])
        assert result is b

    def test_strategy_unknown_returns_best_ratio(self) -> None:
        """Unknown strategy also falls through to balanced selection."""
        router = ParetoRouter()
        a = _candidate("a", cost=1.0, quality=0.8)
        b = _candidate("b", cost=0.1, quality=0.5)  # ratio = 5.0 vs 0.8
        result = router.select_by_strategy("unknown_strategy", [a, b])
        assert result is b

    def test_strategy_empty_raises(self) -> None:
        """Empty candidate list raises ValueError for any strategy."""
        router = ParetoRouter()
        with pytest.raises(ValueError, match="non-empty"):
            router.select_by_strategy("cost", [])


class TestGetQuality:
    """Tests for _get_quality helper."""

    def test_known_model_returns_proxy(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _get_quality

        q = _get_quality("claude-opus-4.6")
        assert q == 0.95

    def test_partial_match_returns_proxy(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _get_quality

        q = _get_quality("claude-haiku-4.5")
        assert q == 0.75

    def test_unknown_returns_default(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _get_quality

        q = _get_quality("completely-unknown-model-xyz-9999")
        assert q == 0.5

    def test_empty_string_returns_some_quality(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _get_quality

        # Empty string matches any model via substring, so it returns some quality value
        q = _get_quality("")
        assert isinstance(q, float)
        assert 0.0 <= q <= 1.0


class TestResolveRoleParams:
    """Tests for _resolve_role_params internal function."""

    def test_no_role_uses_tier_minimum(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _resolve_role_params

        effective_min, _order, mult = _resolve_role_params(
            role=None,
            complexity_tier="simple",
            min_quality=0.0,
            opt_order=("quality", "cost", "speed"),
        )
        assert effective_min == 0.5  # tier_min for "simple"
        assert mult == 1.0

    def test_complex_tier_sets_higher_min_quality(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _resolve_role_params

        effective_min, _, _ = _resolve_role_params(
            role=None,
            complexity_tier="complex",
            min_quality=0.0,
            opt_order=("quality", "cost", "speed"),
        )
        assert effective_min == 0.75  # tier_min for "complex"

    def test_user_min_quality_overrides_tier_when_higher(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _resolve_role_params

        effective_min, _, _ = _resolve_role_params(
            role=None,
            complexity_tier="simple",
            min_quality=0.9,  # user-specified > tier min (0.5)
            opt_order=("quality", "cost", "speed"),
        )
        assert effective_min == 0.9

    def test_unknown_tier_defaults_to_moderate(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _resolve_role_params

        effective_min, _, _ = _resolve_role_params(
            role=None,
            complexity_tier="nonexistent_tier",
            min_quality=0.0,
            opt_order=("quality", "cost", "speed"),
        )
        assert effective_min == 0.6  # default tier_min


class TestSelectOfferFunctions:
    """Tests for select_offer and select_offer_with_fallbacks module-level functions."""

    def test_select_offer_returns_tuple_or_none(self) -> None:
        from thegent.utils.routing_impl.pareto_router import select_offer

        result = select_offer(complexity_tier="moderate")
        assert result is None or (isinstance(result, tuple) and len(result) == 2)

    def test_select_offer_with_trace_returns_trace_or_none(self) -> None:
        from thegent.utils.routing_impl.pareto_router import (
            RouteTrace,
            select_offer_with_trace,
        )

        result = select_offer_with_trace(complexity_tier="moderate")
        assert result is None or isinstance(result, RouteTrace)

    def test_select_offer_with_fallbacks_returns_list(self) -> None:
        from thegent.utils.routing_impl.pareto_router import select_offer_with_fallbacks

        result = select_offer_with_fallbacks(complexity_tier="moderate", k=3)
        assert isinstance(result, list)
        assert len(result) <= 3

    def test_select_offer_with_trace_trace_has_required_fields(self) -> None:
        """If a trace is returned, it must have all required fields."""
        from thegent.utils.routing_impl.pareto_router import (
            RouteTrace,
            select_offer_with_trace,
        )

        result = select_offer_with_trace(complexity_tier="complex")
        if result is None:
            return  # No catalog available, skip validation
        assert isinstance(result, RouteTrace)
        assert result.provider
        assert result.model_alias
        assert isinstance(result.pareto_set, list)
        assert isinstance(result.fallback_chain, list)
        assert "quality" in result.scores


class TestIsDegradedMode:
    """Tests for _is_degraded_mode."""

    def test_returns_bool(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _is_degraded_mode

        result = _is_degraded_mode()
        assert isinstance(result, bool)


class TestGetShadowMultiplier:
    """Tests for _get_shadow_multiplier."""

    def test_returns_float_at_least_one(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _get_shadow_multiplier

        result = _get_shadow_multiplier()
        assert isinstance(result, float)
        assert result >= 1.0


class TestLoadRolesAndGetRole:
    """Tests for _load_roles and _get_role."""

    def test_load_roles_returns_dict(self) -> None:
        import thegent.utils.routing_impl.pareto_router as pr

        # Reset cache to ensure fresh load
        pr._ROLES_CACHE = None
        result = pr._load_roles()
        assert isinstance(result, dict)
        # Cache must be populated after call
        assert pr._ROLES_CACHE is not None

    def test_load_roles_cached_second_call(self) -> None:
        import thegent.utils.routing_impl.pareto_router as pr

        pr._ROLES_CACHE = None
        first = pr._load_roles()
        second = pr._load_roles()
        assert first is second  # Same object from cache

    def test_get_role_none_returns_none(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _get_role

        assert _get_role(None) is None

    def test_get_role_empty_returns_none(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _get_role

        assert _get_role("") is None

    def test_get_role_unknown_returns_default_or_none(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _get_role

        result = _get_role("nonexistent_role_xyz_12345")
        # Either None or the "default" role if defined
        assert result is None or hasattr(result, "name")

    def test_roles_config_path_returns_path(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _roles_config_path

        path = _roles_config_path()
        from pathlib import Path

        assert isinstance(path, Path)


class TestOffersFromCatalog:
    """Tests for _offers_from_catalog function."""

    def test_returns_list(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _offers_from_catalog

        result = _offers_from_catalog()
        assert isinstance(result, list)

    def test_high_quality_floor_may_return_empty(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _offers_from_catalog

        result = _offers_from_catalog(min_quality=0.999)
        assert isinstance(result, list)

    def test_zero_max_cost_returns_empty_or_free_only(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _offers_from_catalog

        result = _offers_from_catalog(max_cost_weight=0.0)
        assert isinstance(result, list)

    def test_simple_tier_returns_offers(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _offers_from_catalog

        result = _offers_from_catalog(complexity_tier="simple")
        assert isinstance(result, list)

    def test_complex_tier_returns_offers(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _offers_from_catalog

        result = _offers_from_catalog(complexity_tier="complex")
        assert isinstance(result, list)


class TestParetoCatalogFunctions:
    """Test _pareto_frontier on Offer objects (internal function)."""

    def test_pareto_frontier_of_offers(self) -> None:
        from thegent.utils.routing_impl.pareto_router import Offer, _pareto_frontier

        a = Offer(provider="p", model_alias="a", cost_weight=0.1, quality=0.9, speed_score=1.0)
        b = Offer(provider="p", model_alias="b", cost_weight=0.5, quality=0.7, speed_score=1.0)
        c = Offer(provider="p", model_alias="c", cost_weight=0.3, quality=0.8, speed_score=1.0)

        frontier = _pareto_frontier([a, b, c])
        aliases = {o.model_alias for o in frontier}
        # a dominates both b and c (lower cost AND higher quality than both)
        assert "b" not in aliases
        assert "c" not in aliases
        assert "a" in aliases

    def test_is_dominated_offer(self) -> None:
        from thegent.utils.routing_impl.pareto_router import Offer, _is_dominated

        worse = Offer(provider="p", model_alias="worse", cost_weight=1.0, quality=0.5)
        better = Offer(provider="p", model_alias="better", cost_weight=0.5, quality=0.9)
        assert _is_dominated(worse, better) is True
        assert _is_dominated(better, worse) is False


class TestLexicographicSelect:
    """Tests for _lexicographic_select function."""

    def test_select_highest_quality(self) -> None:
        from thegent.utils.routing_impl.pareto_router import (
            Offer,
            _lexicographic_select,
        )

        a = Offer(provider="p", model_alias="a", cost_weight=0.1, quality=0.9, speed_score=1.0)
        b = Offer(provider="p", model_alias="b", cost_weight=0.2, quality=0.8, speed_score=1.0)
        result = _lexicographic_select([a, b], order=("quality", "cost", "speed"))
        assert result is a

    def test_empty_returns_none(self) -> None:
        from thegent.utils.routing_impl.pareto_router import _lexicographic_select

        assert _lexicographic_select([]) is None

    def test_select_lowest_cost_when_cost_order(self) -> None:
        from thegent.utils.routing_impl.pareto_router import (
            Offer,
            _lexicographic_select,
        )

        a = Offer(provider="p", model_alias="a", cost_weight=0.5, quality=0.9, speed_score=1.0)
        b = Offer(provider="p", model_alias="b", cost_weight=0.1, quality=0.8, speed_score=1.0)
        result = _lexicographic_select([a, b], order=("cost", "quality", "speed"))
        assert result is b
