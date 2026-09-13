"""Property-based tests for Pareto routing.

FR-ROUTING-001: The selected model must not be dominated by any other feasible model.

Uses Hypothesis to verify Pareto invariants hold across arbitrary candidate sets.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from thegent.utils.routing_impl import ParetoRouter, RouteCandidate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _candidate(
    model: str,
    cost: float,
    quality: float,
    provider: str = "test",
) -> RouteCandidate:
    return RouteCandidate(
        model=model, provider=provider, cost_per_1k=cost, quality_score=quality
    )


def _is_dominated_by(a: RouteCandidate, b: RouteCandidate) -> bool:
    """Return True if b strictly dominates a."""
    cost_ok = b.cost_per_1k <= a.cost_per_1k
    quality_ok = b.quality_score >= a.quality_score
    strictly_better = b.cost_per_1k < a.cost_per_1k or b.quality_score > a.quality_score
    return cost_ok and quality_ok and strictly_better


_candidate_st = st.builds(
    RouteCandidate,
    model=st.text(min_size=1, max_size=20),
    provider=st.sampled_from(["claude", "gemini", "codex", "openai", "test"]),
    cost_per_1k=st.floats(
        min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
    ),
    quality_score=st.floats(
        min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
    ),
)

_nonempty_candidates_st = st.lists(_candidate_st, min_size=1, max_size=15)
_multi_candidates_st = st.lists(_candidate_st, min_size=2, max_size=15)


@pytest.mark.requirement("FR-ROUTING-001")
@given(candidates=_nonempty_candidates_st)
@settings(max_examples=500)
def test_pareto_selected_not_dominated(candidates: list[RouteCandidate]) -> None:
    """Selected model must not be dominated by any other candidate in the input list."""
    router = ParetoRouter()
    selected = router.select(candidates)

    for other in candidates:
        if other is selected:
            continue
        assert not _is_dominated_by(selected, other), (
            f"Selected {selected} is dominated by {other}. Violates FR-ROUTING-001."
        )


@pytest.mark.requirement("FR-ROUTING-001")
@given(candidates=_nonempty_candidates_st)
@settings(max_examples=500)
def test_pareto_selected_is_from_input_list(candidates: list[RouteCandidate]) -> None:
    """Selected candidate must be an element of the input list by identity."""
    router = ParetoRouter()
    selected = router.select(candidates)
    assert any(selected is c for c in candidates), (
        f"Selected {selected} is not an object from the input list."
    )


@pytest.mark.requirement("FR-ROUTING-001")
@given(candidates=_nonempty_candidates_st)
@settings(max_examples=300)
def test_pareto_frontier_all_non_dominated(candidates: list[RouteCandidate]) -> None:
    """Every candidate on the Pareto frontier must not be dominated by any other candidate."""
    router = ParetoRouter()
    frontier = router.get_optimal_providers(candidates)
    for f in frontier:
        for other in candidates:
            if other is f:
                continue
            assert not _is_dominated_by(f, other), (
                f"Frontier member {f} is dominated by {other}."
            )


@pytest.mark.requirement("FR-ROUTING-001")
@given(candidates=_nonempty_candidates_st)
@settings(max_examples=300)
def test_pareto_frontier_nonempty(candidates: list[RouteCandidate]) -> None:
    """The Pareto frontier must never be empty when candidates is non-empty."""
    router = ParetoRouter()
    frontier = router.get_optimal_providers(candidates)
    assert len(frontier) >= 1


@pytest.mark.requirement("FR-ROUTING-001")
@given(candidates=_nonempty_candidates_st)
@settings(max_examples=300)
def test_pareto_select_is_on_frontier(candidates: list[RouteCandidate]) -> None:
    """The selected candidate must be on the Pareto frontier."""
    router = ParetoRouter()
    selected = router.select(candidates)
    frontier = router.get_optimal_providers(candidates)
    frontier_ids = {id(c) for c in frontier}
    assert id(selected) in frontier_ids, (
        f"Selected {selected} is not on the Pareto frontier."
    )


@pytest.mark.requirement("FR-ROUTING-001")
@given(
    candidates=_multi_candidates_st,
    strategy=st.sampled_from(["cost", "quality", "balanced"]),
)
@settings(max_examples=300)
def test_pareto_strategy_select_not_dominated(
    candidates: list[RouteCandidate], strategy: str
) -> None:
    """select_by_strategy must also return a non-dominated candidate."""
    router = ParetoRouter()
    selected = router.select_by_strategy(strategy, candidates)
    for other in candidates:
        if other is selected:
            continue
        assert not _is_dominated_by(selected, other), (
            f"Strategy '{strategy}' selected dominated candidate: {selected} dominated by {other}."
        )


@pytest.mark.requirement("FR-ROUTING-001")
@given(candidates=_nonempty_candidates_st)
@settings(max_examples=200)
def test_pareto_select_deterministic(candidates: list[RouteCandidate]) -> None:
    """Calling select() twice returns same or equivalent result."""
    router = ParetoRouter()
    first = router.select(candidates)
    second = router.select(candidates)
    assert first is second or (
        first.model == second.model
        and first.provider == second.provider
        and first.cost_per_1k == second.cost_per_1k
        and first.quality_score == second.quality_score
    ), f"Non-deterministic: got {first} then {second}"


@pytest.mark.requirement("FR-ROUTING-001")
def test_pareto_empty_raises() -> None:
    router = ParetoRouter()
    with pytest.raises(ValueError, match="non-empty"):
        router.select([])


@pytest.mark.requirement("FR-ROUTING-001")
def test_pareto_single_candidate_is_selected() -> None:
    router = ParetoRouter()
    c = _candidate("only", cost=0.5, quality=0.8)
    assert router.select([c]) is c


@pytest.mark.requirement("FR-ROUTING-001")
def test_pareto_dominated_candidate_not_selected() -> None:
    router = ParetoRouter()
    dominant = _candidate("dominant", cost=0.1, quality=0.9)
    dominated = _candidate("dominated", cost=0.5, quality=0.7)
    result = router.select([dominant, dominated])
    assert result is dominant


@pytest.mark.requirement("FR-ROUTING-001")
def test_pareto_zero_cost_candidate_wins_on_quality() -> None:
    router = ParetoRouter()
    a = _candidate("a", cost=0.0, quality=0.7)
    b = _candidate("b", cost=0.0, quality=0.9)
    result = router.select([a, b])
    assert result is b


@pytest.mark.requirement("FR-ROUTING-001")
def test_pareto_strategy_cost_selects_cheapest_from_frontier() -> None:
    router = ParetoRouter()
    cheap = _candidate("cheap", cost=0.05, quality=0.7)
    expensive = _candidate("expensive", cost=0.8, quality=0.95)
    result = router.select_by_strategy("cost", [cheap, expensive])
    assert result is cheap


@pytest.mark.requirement("FR-ROUTING-001")
def test_pareto_strategy_quality_selects_best_quality_from_frontier() -> None:
    router = ParetoRouter()
    cheap = _candidate("cheap", cost=0.05, quality=0.7)
    premium = _candidate("premium", cost=0.8, quality=0.95)
    result = router.select_by_strategy("quality", [cheap, premium])
    assert result is premium


@pytest.mark.requirement("FR-ROUTING-001")
def test_pareto_frontier_excludes_dominated() -> None:
    router = ParetoRouter()
    dominant = _candidate("dominant", cost=0.1, quality=0.9)
    dominated = _candidate("dominated", cost=0.5, quality=0.7)
    middle = _candidate("middle", cost=0.2, quality=0.85)
    frontier = router.get_optimal_providers([dominant, dominated, middle])
    frontier_models = {c.model for c in frontier}
    assert "dominated" not in frontier_models
    assert "dominant" in frontier_models
    # middle is dominated by dominant (lower cost AND higher quality), so correctly excluded
