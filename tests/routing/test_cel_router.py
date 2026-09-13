"""Tests for GW-57: CEL-like expression routing.

All tests tagged with @pytest.mark.requirement("FR-AROUTE-057").

# @trace FR-AROUTE-057
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.cel_router import (
    CelEvalResult,
    CelEvaluator,
    CelRoute,
    compile_expression,
    eval_expression,
    evaluate_cel_routes,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**kwargs) -> dict:
    """Build a simple context dict with 'context' top-level key."""
    return {"context": kwargs}


def _route(expression: str, target: str = "target-model", name: str = "test") -> CelRoute:
    return CelRoute(expression=expression, target=target, name=name)


def _run(expression: str, ctx: dict) -> CelEvalResult:
    return evaluate_cel_routes([_route(expression)], ctx)


# ---------------------------------------------------------------------------
# Test 1: simple equality
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_simple_equality() -> None:
    """context.model == "gpt-4o" matches when model is gpt-4o."""
    ctx = _ctx(model="gpt-4o")
    result = _run('context.model == "gpt-4o"', ctx)
    assert result.matched is True
    assert result.target == "target-model"
    assert result.error == ""


# ---------------------------------------------------------------------------
# Test 2: simple inequality
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_simple_inequality() -> None:
    """context.model != "gpt-4o" matches different model."""
    ctx = _ctx(model="claude-3-5-sonnet")
    result = _run('context.model != "gpt-4o"', ctx)
    assert result.matched is True

    ctx_match = _ctx(model="gpt-4o")
    result2 = _run('context.model != "gpt-4o"', ctx_match)
    assert result2.matched is False


# ---------------------------------------------------------------------------
# Test 3: numeric comparison >
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_numeric_comparison_gt() -> None:
    """context.priority > 5 matches when priority=10."""
    ctx = _ctx(priority=10)
    result = _run("context.priority > 5", ctx)
    assert result.matched is True

    ctx_low = _ctx(priority=3)
    result2 = _run("context.priority > 5", ctx_low)
    assert result2.matched is False


# ---------------------------------------------------------------------------
# Test 4: numeric comparison <=
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_numeric_comparison_lte() -> None:
    """context.priority <= 5 matches when priority=5."""
    ctx = _ctx(priority=5)
    result = _run("context.priority <= 5", ctx)
    assert result.matched is True

    ctx_over = _ctx(priority=6)
    result2 = _run("context.priority <= 5", ctx_over)
    assert result2.matched is False


# ---------------------------------------------------------------------------
# Test 5: && operator
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_and_operator() -> None:
    """A && B is true only when both true."""
    expr = 'context.model == "gpt-4o" && context.priority > 5'

    ctx = _ctx(model="gpt-4o", priority=10)
    assert _run(expr, ctx).matched is True

    ctx2 = _ctx(model="gpt-4o", priority=3)
    assert _run(expr, ctx2).matched is False

    ctx3 = _ctx(model="claude", priority=10)
    assert _run(expr, ctx3).matched is False

    ctx4 = _ctx(model="claude", priority=3)
    assert _run(expr, ctx4).matched is False


# ---------------------------------------------------------------------------
# Test 6: || operator
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_or_operator() -> None:
    """A || B is true when either true."""
    expr = 'context.model == "gpt-4o" || context.model == "claude-3-opus"'

    ctx1 = _ctx(model="gpt-4o")
    assert _run(expr, ctx1).matched is True

    ctx2 = _ctx(model="claude-3-opus")
    assert _run(expr, ctx2).matched is True

    ctx3 = _ctx(model="gemini")
    assert _run(expr, ctx3).matched is False


# ---------------------------------------------------------------------------
# Test 7: ! operator
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_not_operator() -> None:
    """!A inverts result."""
    expr = '!(context.model == "gpt-4o")'

    ctx1 = _ctx(model="claude")
    assert _run(expr, ctx1).matched is True

    ctx2 = _ctx(model="gpt-4o")
    assert _run(expr, ctx2).matched is False


# ---------------------------------------------------------------------------
# Test 8: nested attribute access
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_nested_attr_access() -> None:
    """context.metadata.tier == "premium" traverses nested dict."""
    ctx = {"context": {"metadata": {"tier": "premium"}}}
    result = _run('context.metadata.tier == "premium"', ctx)
    assert result.matched is True

    ctx2 = {"context": {"metadata": {"tier": "free"}}}
    result2 = _run('context.metadata.tier == "premium"', ctx2)
    assert result2.matched is False


# ---------------------------------------------------------------------------
# Test 9: missing attribute → no match, no exception
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_missing_attr_returns_no_match() -> None:
    """Missing attribute -> matched=False, no exception."""
    ctx = _ctx(model="gpt-4o")
    result = _run("context.priority > 5", ctx)
    assert result.matched is False
    assert result.error == ""


# ---------------------------------------------------------------------------
# Test 10: string contains
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_string_contains() -> None:
    """context.model.contains("gpt") matches "gpt-4o"."""
    ctx = _ctx(model="gpt-4o")
    result = _run('context.model.contains("gpt")', ctx)
    assert result.matched is True

    ctx2 = _ctx(model="claude-3")
    result2 = _run('context.model.contains("gpt")', ctx2)
    assert result2.matched is False


# ---------------------------------------------------------------------------
# Test 11: string startsWith
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_string_starts_with() -> None:
    """context.model.startsWith("claude") matches "claude-3-sonnet"."""
    ctx = _ctx(model="claude-3-sonnet")
    result = _run('context.model.startsWith("claude")', ctx)
    assert result.matched is True

    ctx2 = _ctx(model="gpt-4o")
    result2 = _run('context.model.startsWith("claude")', ctx2)
    assert result2.matched is False


# ---------------------------------------------------------------------------
# Test 12: string endsWith
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_string_ends_with() -> None:
    """context.model.endsWith("turbo") matches "gpt-3.5-turbo"."""
    ctx = _ctx(model="gpt-3.5-turbo")
    result = _run('context.model.endsWith("turbo")', ctx)
    assert result.matched is True

    ctx2 = _ctx(model="gpt-4o")
    result2 = _run('context.model.endsWith("turbo")', ctx2)
    assert result2.matched is False


# ---------------------------------------------------------------------------
# Test 13: in operator
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_in_operator() -> None:
    """context.model in ["gpt-4o", "gpt-4-turbo"] matches."""
    ctx = _ctx(model="gpt-4o")
    result = _run('context.model in ["gpt-4o", "gpt-4-turbo"]', ctx)
    assert result.matched is True

    ctx2 = _ctx(model="claude-3")
    result2 = _run('context.model in ["gpt-4o", "gpt-4-turbo"]', ctx2)
    assert result2.matched is False


# ---------------------------------------------------------------------------
# Test 14: ternary expression
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_ternary_expression() -> None:
    """Ternary evaluates condition branch correctly."""
    expr = "context.priority > 5 ? true : false"
    ctx = _ctx(priority=10)
    result = _run(expr, ctx)
    assert result.matched is True

    ctx2 = _ctx(priority=2)
    result2 = _run(expr, ctx2)
    assert result2.matched is False


# ---------------------------------------------------------------------------
# Test 15: multiple routes — first match wins
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_multiple_routes_first_match() -> None:
    """First matching route wins."""
    routes = [
        CelRoute(expression='context.model == "gpt-4o"', target="route-a", name="A"),
        CelRoute(expression='context.model == "gpt-4o"', target="route-b", name="B"),
        CelRoute(expression='context.model == "claude"', target="route-c", name="C"),
    ]
    ctx = _ctx(model="gpt-4o")
    result = evaluate_cel_routes(routes, ctx)
    assert result.matched is True
    assert result.target == "route-a"
    assert result.route_name == "A"

    ctx2 = _ctx(model="claude")
    result2 = evaluate_cel_routes(routes, ctx2)
    assert result2.matched is True
    assert result2.target == "route-c"


# ---------------------------------------------------------------------------
# Test 16: invalid expression → error field set, no raise
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_invalid_expression_returns_error() -> None:
    """Syntax error -> error field set, matched=False, no exception raised."""
    routes = [CelRoute(expression="@@invalid@@", target="target", name="bad")]
    ctx = _ctx(model="anything")
    result = evaluate_cel_routes(routes, ctx)
    assert result.matched is False
    assert result.error != ""


# ---------------------------------------------------------------------------
# Test 17: compile_expression + eval_expression
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_compile_expression_caches() -> None:
    """compile_expression + eval_expression work correctly."""
    expr = 'context.model == "gpt-4o"'
    compiled = compile_expression(expr)
    assert compiled is not None

    ctx = _ctx(model="gpt-4o")
    assert eval_expression(compiled, ctx) is True

    ctx2 = _ctx(model="claude")
    assert eval_expression(compiled, ctx2) is False

    compiled2 = compile_expression(expr)
    assert eval_expression(compiled2, ctx) is True


# ---------------------------------------------------------------------------
# Test 18: CelEvaluator direct usage
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-057")
def test_cel_evaluator_direct() -> None:
    """CelEvaluator.evaluate works correctly."""
    routes = [
        CelRoute(expression='context.tier == "premium"', target="premium-model", name="premium"),
        CelRoute(expression='context.tier == "free"', target="free-model", name="free"),
    ]
    evaluator = CelEvaluator(routes)

    ctx = {"context": {"tier": "premium"}}
    result = evaluator.evaluate(ctx)
    assert result.matched is True
    assert result.target == "premium-model"
    assert result.route_name == "premium"

    ctx2 = {"context": {"tier": "free"}}
    result2 = evaluator.evaluate(ctx2)
    assert result2.matched is True
    assert result2.target == "free-model"

    ctx3 = {"context": {"tier": "enterprise"}}
    result3 = evaluator.evaluate(ctx3)
    assert result3.matched is False
