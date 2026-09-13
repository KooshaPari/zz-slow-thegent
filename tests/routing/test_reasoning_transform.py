"""Tests for GW-40: Unified reasoning interface.

# @trace FR-REQEXT-040
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.reasoning_transform import (
    THINKING_BUDGET,
    ReasoningEffort,
    apply_anthropic_reasoning,
    apply_gemini_reasoning,
    apply_openai_reasoning,
    apply_reasoning_for_provider,
    extract_reasoning_effort,
)


@pytest.mark.requirement("FR-REQEXT-040")
def test_extract_reasoning_effort_from_reasoning_object() -> None:
    body = {"reasoning": {"effort": "high"}}
    assert extract_reasoning_effort(body) == ReasoningEffort.HIGH


@pytest.mark.requirement("FR-REQEXT-040")
def test_extract_reasoning_effort_from_flat_key() -> None:
    body = {"reasoning_effort": "medium"}
    assert extract_reasoning_effort(body) == ReasoningEffort.MEDIUM


@pytest.mark.requirement("FR-REQEXT-040")
def test_extract_reasoning_effort_from_variant_key() -> None:
    """Variant parameter is used by OpenWork/Cursor for codex models."""
    body = {"variant": "high"}
    assert extract_reasoning_effort(body) == ReasoningEffort.HIGH


@pytest.mark.requirement("FR-REQEXT-040")
def test_extract_reasoning_effort_from_variant_low() -> None:
    """Variant parameter supports low/medium/high values."""
    body = {"variant": "low"}
    assert extract_reasoning_effort(body) == ReasoningEffort.LOW


@pytest.mark.requirement("FR-REQEXT-040")
def test_extract_reasoning_effort_invalid_variant() -> None:
    """Invalid variant values return None."""
    body = {"variant": "invalid"}
    assert extract_reasoning_effort(body) is None


@pytest.mark.requirement("FR-REQEXT-040")
def test_extract_reasoning_effort_priority() -> None:
    """reasoning_effort takes priority over variant."""
    body = {"reasoning_effort": "low", "variant": "high"}
    assert extract_reasoning_effort(body) == ReasoningEffort.LOW


@pytest.mark.requirement("FR-REQEXT-040")
def test_extract_reasoning_effort_missing() -> None:
    body = {"model": "gpt-4o"}
    assert extract_reasoning_effort(body) is None


@pytest.mark.requirement("FR-REQEXT-040")
def test_extract_reasoning_effort_invalid_value() -> None:
    body = {"reasoning": {"effort": "extreme"}}
    assert extract_reasoning_effort(body) is None


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_anthropic_reasoning_adds_thinking() -> None:
    body = {"model": "claude-opus-4-6", "reasoning": {"effort": "high"}}
    result = apply_anthropic_reasoning(body, ReasoningEffort.HIGH)
    assert result["thinking"] == {"type": "enabled", "budget_tokens": 10000}


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_anthropic_reasoning_removes_reasoning_key() -> None:
    body = {"model": "claude-opus-4-6", "reasoning": {"effort": "high"}}
    result = apply_anthropic_reasoning(body, ReasoningEffort.HIGH)
    assert "reasoning" not in result


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_anthropic_reasoning_does_not_mutate() -> None:
    body = {"model": "claude-opus-4-6", "reasoning": {"effort": "high"}}
    original = dict(body)
    apply_anthropic_reasoning(body, ReasoningEffort.HIGH)
    assert body == original


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_openai_reasoning_adds_effort() -> None:
    body = {"model": "gpt-4o", "reasoning": {"effort": "low"}}
    result = apply_openai_reasoning(body, ReasoningEffort.LOW)
    assert result["reasoning_effort"] == "low"


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_openai_reasoning_removes_reasoning_key() -> None:
    body = {"model": "gpt-4o", "reasoning": {"effort": "medium"}}
    result = apply_openai_reasoning(body, ReasoningEffort.MEDIUM)
    assert "reasoning" not in result


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_gemini_reasoning_adds_thinking_config() -> None:
    body = {"model": "gemini-2.0-flash", "reasoning": {"effort": "medium"}}
    result = apply_gemini_reasoning(body, ReasoningEffort.MEDIUM)
    assert result["thinking_config"] == {"thinking_budget": 5000}


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_reasoning_for_provider_anthropic() -> None:
    body = {"model": "claude-opus-4-6", "reasoning": {"effort": "high"}}
    result = apply_reasoning_for_provider(body, "anthropic")
    assert "thinking" in result
    assert result["thinking"]["type"] == "enabled"
    assert result["thinking"]["budget_tokens"] == THINKING_BUDGET[ReasoningEffort.HIGH]
    assert "reasoning" not in result


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_reasoning_for_provider_openai() -> None:
    body = {"model": "gpt-4o", "reasoning": {"effort": "low"}}
    result = apply_reasoning_for_provider(body, "openai")
    assert result["reasoning_effort"] == "low"
    assert "reasoning" not in result


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_reasoning_for_provider_codex() -> None:
    """Codex uses OpenAI-compatible API, should apply reasoning_effort."""
    body = {"model": "gpt-5.3-codex", "variant": "high"}
    result = apply_reasoning_for_provider(body, "codex")
    assert result["reasoning_effort"] == "high"
    assert "reasoning" not in result
    assert "variant" not in result


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_reasoning_for_provider_codex_with_reasoning() -> None:
    """Codex provider handles reasoning object correctly."""
    body = {"model": "gpt-5.3-codex", "reasoning": {"effort": "medium"}}
    result = apply_reasoning_for_provider(body, "codex")
    assert result["reasoning_effort"] == "medium"
    assert "reasoning" not in result


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_reasoning_for_provider_gemini() -> None:
    body = {"model": "gemini-pro", "reasoning": {"effort": "high"}}
    result = apply_reasoning_for_provider(body, "google")
    assert "thinking_config" in result
    assert result["thinking_config"]["thinking_budget"] == THINKING_BUDGET[ReasoningEffort.HIGH]
    assert "reasoning" not in result


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_reasoning_for_provider_unknown_strips() -> None:
    body = {"model": "some-model", "reasoning": {"effort": "medium"}}
    result = apply_reasoning_for_provider(body, "unknown_provider")
    assert "reasoning" not in result
    assert "thinking" not in result
    assert "reasoning_effort" not in result
    assert "thinking_config" not in result


@pytest.mark.requirement("FR-REQEXT-040")
def test_apply_reasoning_for_provider_no_reasoning_returns_unchanged() -> None:
    body = {"model": "gpt-4o", "temperature": 0.7}
    result = apply_reasoning_for_provider(body, "openai")
    assert result is body


@pytest.mark.requirement("FR-REQEXT-040")
def test_thinking_budget_values() -> None:
    assert THINKING_BUDGET[ReasoningEffort.HIGH] == 10000
    assert THINKING_BUDGET[ReasoningEffort.MEDIUM] == 5000
    assert THINKING_BUDGET[ReasoningEffort.LOW] == 1000
