"""Tests for GW-61: Semantic load balancing.

All tests tagged with @pytest.mark.requirement("FR-AROUTE-061").

# @trace FR-AROUTE-061
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.semantic_lb import (
    ModelCapability,
    SemanticLoadBalancer,
    semantic_route,
)

# ---------------------------------------------------------------------------
# Deterministic mock embedding provider
# ---------------------------------------------------------------------------


class _MockProvider:
    """Returns pre-set embeddings for known texts, deterministic unit vectors otherwise."""

    def __init__(self, embeddings: dict[str, list[float]]) -> None:
        self._embeddings = embeddings

    def embed(self, text: str) -> list[float]:
        if text in self._embeddings:
            return self._embeddings[text]
        # Return a fixed orthogonal vector for unknown texts
        return [0.0, 0.0, 1.0]

    def is_available(self) -> bool:
        return True


def _unit(x: float, y: float, z: float) -> list[float]:
    """Return a 3-component unit vector."""
    import math

    norm = math.sqrt(x * x + y * y + z * z)
    return [x / norm, y / norm, z / norm]


# Two clearly similar (aligned) and one orthogonal vector
_VEC_CODE = _unit(1.0, 0.0, 0.0)  # coding direction
_VEC_CHAT = _unit(0.0, 1.0, 0.0)  # chat direction
_VEC_ORTH = _unit(0.0, 0.0, 1.0)  # orthogonal


def _coding_capabilities() -> list[ModelCapability]:
    return [
        ModelCapability(model="code-model", description="coding desc", provider="openai", tags=["coding"]),
        ModelCapability(model="chat-model", description="chat desc", provider="anthropic", tags=["chat"]),
    ]


def _coding_provider() -> _MockProvider:
    return _MockProvider(
        {
            "coding desc": _VEC_CODE,
            "chat desc": _VEC_CHAT,
            "write a python function": _VEC_CODE,  # clearly coding
            "tell me a joke": _VEC_CHAT,  # clearly chat
        }
    )


# ---------------------------------------------------------------------------
# Test 1: selects best match
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-061")
def test_semantic_lb_selects_best_match() -> None:
    """Coding prompt routes to coding model."""
    caps = _coding_capabilities()
    provider = _coding_provider()
    lb = SemanticLoadBalancer(caps, provider=provider)

    result = lb.route("write a python function")
    assert result is not None
    assert result.selected_model == "code-model"


# ---------------------------------------------------------------------------
# Test 2: empty capabilities returns None
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-061")
def test_semantic_lb_empty_capabilities_returns_none() -> None:
    """Empty capabilities list returns None."""
    lb = SemanticLoadBalancer([], provider=_coding_provider())
    result = lb.route("any prompt")
    assert result is None


# ---------------------------------------------------------------------------
# Test 3: single capability always selected
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-061")
def test_semantic_lb_single_capability() -> None:
    """Single capability is always selected."""
    caps = [ModelCapability(model="only-model", description="coding desc", provider="openai")]
    lb = SemanticLoadBalancer(caps, provider=_coding_provider())
    result = lb.route("write a python function")
    assert result is not None
    assert result.selected_model == "only-model"


# ---------------------------------------------------------------------------
# Test 4: scores contains all models
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-061")
def test_semantic_lb_scores_all_models() -> None:
    """Result.scores has an entry for every registered model."""
    caps = _coding_capabilities()
    provider = _coding_provider()
    lb = SemanticLoadBalancer(caps, provider=provider)

    result = lb.route("write a python function")
    assert result is not None
    assert set(result.scores.keys()) == {"code-model", "chat-model"}
    assert all(isinstance(v, float) for v in result.scores.values())


# ---------------------------------------------------------------------------
# Test 5: min_similarity filters out all results
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-061")
def test_semantic_lb_min_similarity_filters() -> None:
    """min_similarity=1.1 causes None return (no vector achieves > 1.0 similarity)."""
    caps = _coding_capabilities()
    provider = _coding_provider()
    lb = SemanticLoadBalancer(caps, provider=provider, min_similarity=1.1)

    result = lb.route("write a python function")
    assert result is None


# ---------------------------------------------------------------------------
# Test 6: add_capability is reflected in routing
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-061")
def test_add_capability() -> None:
    """Adding a capability after init is reflected in route."""
    provider = _MockProvider(
        {
            "reasoning desc": _unit(0.9, 0.1, 0.0),
            "do complex reasoning": _unit(0.9, 0.1, 0.0),
            "coding desc": _VEC_CODE,
        }
    )
    lb = SemanticLoadBalancer(
        [ModelCapability(model="code-model", description="coding desc", provider="openai")],
        provider=provider,
    )

    new_cap = ModelCapability(model="reason-model", description="reasoning desc", provider="anthropic")
    lb.add_capability(new_cap)

    result = lb.route("do complex reasoning")
    assert result is not None
    assert result.selected_model == "reason-model"


# ---------------------------------------------------------------------------
# Test 7: get_capabilities returns all
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-061")
def test_get_capabilities() -> None:
    """get_capabilities() returns all registered capabilities."""
    caps = _coding_capabilities()
    lb = SemanticLoadBalancer(caps, provider=_coding_provider())
    retrieved = lb.get_capabilities()
    assert len(retrieved) == 2
    models = {c.model for c in retrieved}
    assert "code-model" in models
    assert "chat-model" in models


# ---------------------------------------------------------------------------
# Test 8: semantic_route convenience function
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-061")
def test_semantic_route_convenience() -> None:
    """One-shot semantic_route function works."""
    caps = _coding_capabilities()
    provider = _coding_provider()
    result = semantic_route("write a python function", caps, provider=provider)
    assert result is not None
    assert result.selected_model == "code-model"


# ---------------------------------------------------------------------------
# Test 9: provider is returned for winner
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-AROUTE-061")
def test_semantic_lb_provider_returned() -> None:
    """Winner's provider field is in the result."""
    caps = _coding_capabilities()
    provider = _coding_provider()
    lb = SemanticLoadBalancer(caps, provider=provider)

    result = lb.route("write a python function")
    assert result is not None
    assert result.provider == "openai"

    result2 = lb.route("tell me a joke")
    assert result2 is not None
    assert result2.provider == "anthropic"
