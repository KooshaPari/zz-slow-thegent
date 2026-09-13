"""Tests for GW-42: OpenRouter request field passthrough.

# @trace FR-REQEXT-042
"""

from __future__ import annotations

import pytest

from thegent.cliproxy_adapter import (
    _OR_PASSTHROUGH_FIELDS,
    build_openrouter_passthrough_body,
)


@pytest.mark.requirement("FR-REQEXT-042")
def test_build_openrouter_passthrough_body_all_fields() -> None:
    body = {
        "provider": {"order": ["anthropic"]},
        "models": ["claude-opus-4-6", "gpt-4o"],
        "route": "fallback",
        "transforms": ["middle-out"],
        "reasoning": {"effort": "high"},
        "plugins": [{"id": "web"}],
        "usage": {"include": True},
        "anthropic_beta": "extended-thinking-2025-01-20",
        "model": "claude-opus-4-6",  # not in passthrough fields
    }
    result = build_openrouter_passthrough_body(body)
    assert "provider" in result
    assert "models" in result
    assert "route" in result
    assert "transforms" in result
    assert "reasoning" in result
    assert "plugins" in result
    assert "usage" in result
    assert "anthropic_beta" in result
    # Non-passthrough fields should NOT be included
    assert "model" not in result


@pytest.mark.requirement("FR-REQEXT-042")
def test_build_openrouter_passthrough_body_partial() -> None:
    body = {
        "provider": {"order": ["openai"]},
        "model": "gpt-4o",
        "temperature": 0.7,
    }
    result = build_openrouter_passthrough_body(body)
    assert result == {"provider": {"order": ["openai"]}}
    assert "model" not in result
    assert "temperature" not in result


@pytest.mark.requirement("FR-REQEXT-042")
def test_build_openrouter_passthrough_body_empty() -> None:
    body: dict = {}
    result = build_openrouter_passthrough_body(body)
    assert result == {}


@pytest.mark.requirement("FR-REQEXT-042")
def test_or_passthrough_fields_contains_provider() -> None:
    assert "provider" in _OR_PASSTHROUGH_FIELDS


@pytest.mark.requirement("FR-REQEXT-042")
def test_or_passthrough_fields_contains_models() -> None:
    assert "models" in _OR_PASSTHROUGH_FIELDS


@pytest.mark.requirement("FR-REQEXT-042")
def test_or_passthrough_fields_contains_reasoning() -> None:
    assert "reasoning" in _OR_PASSTHROUGH_FIELDS


@pytest.mark.requirement("FR-REQEXT-042")
def test_or_passthrough_fields_contains_transforms() -> None:
    assert "transforms" in _OR_PASSTHROUGH_FIELDS
