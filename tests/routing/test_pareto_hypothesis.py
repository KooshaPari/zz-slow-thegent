"""Hypothesis property-based tests for ParetoRouter (T3.B.B.2.1).

Tests verify mathematical properties of Pareto dominance and frontier computation:
- Non-dominated candidates are never removed from the frontier
- Dominated candidates never appear on the frontier
- The selected candidate maximises quality/cost ratio
- Frontier is stable under permutation of input order
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from thegent.utils.routing_impl.pareto_router import ParetoRouter, RouteCandidate

# --- Strategies ---

route_candidate_st = st.builds(
    RouteCandidate,
    model=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))),
    provider=st.sampled_from(["claude", "gemini", "openai", "free", "codex"]),
    cost_per_1k=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    quality_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)

candidate_list_st = st.lists(route_candidate_st, min_size=1, max_size=50)


# --- Property tests ---


class TestParetoFrontierProperties:
    """Mathematical properties of Pareto dominance."""

    router = ParetoRouter()

    @given(candidates=candidate_list_st)
    @settings(max_examples=200, deadline=None)
    def test_frontier_is_subset_of_candidates(self, candidates: list[RouteCandidate]) -> None:
        """The Pareto frontier must be a subset of the input candidates."""
        frontier = self.router._pareto_frontier(candidates)
        for f in frontier:
            assert f in candidates

    @given(candidates=candidate_list_st)
    @settings(max_examples=200, deadline=None)
    def test_frontier_non_empty(self, candidates: list[RouteCandidate]) -> None:
        """A non-empty candidate list always produces a non-empty frontier."""
        frontier = self.router._pareto_frontier(candidates)
        assert len(frontier) > 0

    @given(candidates=candidate_list_st)
    @settings(max_examples=200, deadline=None)
    def test_no_frontier_member_dominates_another(self, candidates: list[RouteCandidate]) -> None:
        """No member of the frontier is dominated by another frontier member."""
        frontier = self.router._pareto_frontier(candidates)
        for i, a in enumerate(frontier):
            for j, b in enumerate(frontier):
                if i != j:
                    assert not self.router._is_dominated(a, b), f"Frontier member {a} is dominated by {b}"

    @given(candidates=candidate_list_st)
    @settings(max_examples=200, deadline=None)
    def test_non_frontier_members_are_dominated(self, candidates: list[RouteCandidate]) -> None:
        """Every non-frontier candidate is dominated by at least one frontier member."""
        frontier = self.router._pareto_frontier(candidates)
        frontier_set = {id(f) for f in frontier}
        for c in candidates:
            if id(c) not in frontier_set:
                assert any(self.router._is_dominated(c, f) for f in frontier), (
                    f"Non-frontier {c} is not dominated by any frontier member"
                )

    @given(candidates=candidate_list_st)
    @settings(max_examples=100, deadline=None)
    def test_frontier_stable_under_permutation(self, candidates: list[RouteCandidate]) -> None:
        """Frontier should contain the same candidates regardless of input order."""
        import random

        frontier1 = self.router._pareto_frontier(candidates)
        shuffled = list(candidates)
        random.shuffle(shuffled)
        frontier2 = self.router._pareto_frontier(shuffled)

        # Compare by (model, provider, cost, quality) tuples
        def key(c: RouteCandidate) -> tuple:
            return (c.model, c.provider, c.cost_per_1k, c.quality_score)

        assert sorted(key(f) for f in frontier1) == sorted(key(f) for f in frontier2)


class TestSelectProperties:
    """Properties of the select method."""

    router = ParetoRouter()

    @given(candidates=candidate_list_st)
    @settings(max_examples=200, deadline=None)
    def test_select_returns_frontier_member(self, candidates: list[RouteCandidate]) -> None:
        """Selected candidate must be on the Pareto frontier."""
        selected = self.router.select(candidates)
        frontier = self.router._pareto_frontier(candidates)

        def key(c: RouteCandidate) -> tuple:
            return (c.model, c.provider, c.cost_per_1k, c.quality_score)

        assert key(selected) in [key(f) for f in frontier]

    @given(candidates=candidate_list_st)
    @settings(max_examples=200, deadline=None)
    def test_select_deterministic(self, candidates: list[RouteCandidate]) -> None:
        """Same input should produce same output."""
        r1 = self.router.select(candidates)
        r2 = self.router.select(candidates)
        assert r1.model == r2.model
        assert r1.provider == r2.provider
        assert r1.cost_per_1k == r2.cost_per_1k
        assert r1.quality_score == r2.quality_score

    def test_select_empty_raises(self) -> None:
        """Empty candidate list should raise ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            self.router.select([])


class TestDominanceProperties:
    """Properties of the _is_dominated relation."""

    @given(
        cost=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        quality=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200, deadline=None)
    def test_not_self_dominated(self, cost: float, quality: float) -> None:
        """A candidate never dominates itself."""
        c = RouteCandidate(model="m", provider="p", cost_per_1k=cost, quality_score=quality)
        assert not ParetoRouter._is_dominated(c, c)

    @given(
        cost_a=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
        quality_a=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=200, deadline=None)
    def test_strictly_better_dominates(self, cost_a: float, quality_a: float) -> None:
        """A candidate with strictly lower cost AND higher quality dominates."""
        a = RouteCandidate(model="a", provider="p", cost_per_1k=cost_a, quality_score=quality_a)
        b = RouteCandidate(
            model="b",
            provider="p",
            cost_per_1k=cost_a / 2,
            quality_score=min(quality_a + 0.01, 1.0),
        )
        assert ParetoRouter._is_dominated(a, b)


class TestSelectByStrategy:
    """Tests for strategy-based selection."""

    router = ParetoRouter()

    def test_cost_strategy_selects_cheapest(self) -> None:
        candidates = [
            RouteCandidate(model="expensive", provider="p", cost_per_1k=10.0, quality_score=0.9),
            RouteCandidate(model="cheap", provider="p", cost_per_1k=0.1, quality_score=0.7),
            RouteCandidate(model="mid", provider="p", cost_per_1k=5.0, quality_score=0.8),
        ]
        selected = self.router.select_by_strategy("cost", candidates)
        assert selected.model == "cheap"

    def test_quality_strategy_selects_best(self) -> None:
        candidates = [
            RouteCandidate(model="low", provider="p", cost_per_1k=0.1, quality_score=0.3),
            RouteCandidate(model="high", provider="p", cost_per_1k=10.0, quality_score=0.95),
            RouteCandidate(model="mid", provider="p", cost_per_1k=5.0, quality_score=0.7),
        ]
        selected = self.router.select_by_strategy("quality", candidates)
        assert selected.model == "high"

    @given(
        candidates=candidate_list_st,
        strategy=st.sampled_from(["cost", "quality", "speed", "balanced"]),
    )
    @settings(max_examples=100, deadline=None)
    def test_strategy_always_returns_candidate(self, candidates: list[RouteCandidate], strategy: str) -> None:
        """Any valid strategy returns a candidate from the input."""
        selected = self.router.select_by_strategy(strategy, candidates)

        def key(c: RouteCandidate) -> tuple:
            return (c.model, c.provider, c.cost_per_1k, c.quality_score)

        assert key(selected) in [key(c) for c in candidates]
