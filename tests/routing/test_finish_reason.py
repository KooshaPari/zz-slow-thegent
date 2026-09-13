"""Tests for GW-49: normalize_finish_reason and inject_native_finish_reason.

# @trace FR-REQEXT-049
"""

from __future__ import annotations

import pytest

from thegent.cliproxy_adapter import (
    inject_native_finish_reason,
    normalize_finish_reason,
)

# ---------------------------------------------------------------------------
# normalize_finish_reason tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-REQEXT-049")
def test_normalize_finish_reason_openai_stop() -> None:
    """GW-49: OpenAI 'stop' normalizes to 'stop' (identity)."""
    assert normalize_finish_reason("stop") == "stop"


@pytest.mark.requirement("FR-REQEXT-049")
def test_normalize_finish_reason_anthropic_end_turn() -> None:
    """GW-49: Anthropic 'end_turn' normalizes to 'stop'."""
    assert normalize_finish_reason("end_turn") == "stop"


@pytest.mark.requirement("FR-REQEXT-049")
def test_normalize_finish_reason_anthropic_max_tokens() -> None:
    """GW-49: Anthropic 'max_tokens' normalizes to 'length'."""
    assert normalize_finish_reason("max_tokens") == "length"


@pytest.mark.requirement("FR-REQEXT-049")
def test_normalize_finish_reason_gemini_stop() -> None:
    """GW-49: Gemini 'STOP' normalizes to 'stop'."""
    assert normalize_finish_reason("STOP") == "stop"


@pytest.mark.requirement("FR-REQEXT-049")
def test_normalize_finish_reason_gemini_safety() -> None:
    """GW-49: Gemini 'SAFETY' normalizes to 'content_filter'."""
    assert normalize_finish_reason("SAFETY") == "content_filter"


@pytest.mark.requirement("FR-REQEXT-049")
def test_normalize_finish_reason_tool_use() -> None:
    """GW-49: Anthropic 'tool_use' normalizes to 'tool_calls'."""
    assert normalize_finish_reason("tool_use") == "tool_calls"


@pytest.mark.requirement("FR-REQEXT-049")
def test_normalize_finish_reason_unknown() -> None:
    """GW-49: unknown finish reason defaults to 'stop'."""
    assert normalize_finish_reason("totally_unknown_reason") == "stop"


@pytest.mark.requirement("FR-REQEXT-049")
def test_normalize_finish_reason_none() -> None:
    """GW-49: None finish reason defaults to 'stop'."""
    assert normalize_finish_reason(None) == "stop"


# ---------------------------------------------------------------------------
# inject_native_finish_reason tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-REQEXT-049")
def test_inject_native_finish_reason_adds_native() -> None:
    """GW-49: inject_native_finish_reason sets native_finish_reason to original value."""
    body = {
        "choices": [
            {"finish_reason": "stop", "message": {"content": "hello"}},
        ]
    }
    result = inject_native_finish_reason(body)
    choice = result["choices"][0]
    assert choice["native_finish_reason"] == "stop"
    assert choice["finish_reason"] == "stop"


@pytest.mark.requirement("FR-REQEXT-049")
def test_inject_native_finish_reason_normalizes_anthropic_end_turn() -> None:
    """GW-49: 'end_turn' from Anthropic becomes native_finish_reason='end_turn', finish_reason='stop'."""
    body = {
        "choices": [
            {"finish_reason": "end_turn", "message": {"content": "done"}},
        ]
    }
    result = inject_native_finish_reason(body)
    choice = result["choices"][0]
    assert choice["native_finish_reason"] == "end_turn"
    assert choice["finish_reason"] == "stop"


@pytest.mark.requirement("FR-REQEXT-049")
def test_inject_native_finish_reason_no_choices_returns_unchanged() -> None:
    """GW-49: body with no 'choices' key is returned unchanged."""
    body = {"model": "gpt-4o", "usage": {"prompt_tokens": 10}}
    result = inject_native_finish_reason(body)
    assert result == body
    assert "choices" not in result


@pytest.mark.requirement("FR-REQEXT-049")
def test_inject_native_finish_reason_does_not_mutate() -> None:
    """GW-49: original body and choice dicts must not be mutated."""
    original_choice = {"finish_reason": "end_turn", "index": 0}
    body = {"choices": [original_choice]}
    original_body_id = id(body)
    original_choice_id = id(original_choice)

    result = inject_native_finish_reason(body)

    # Returned objects are new copies
    assert id(result) != original_body_id
    assert id(result["choices"][0]) != original_choice_id
    # Original unchanged
    assert "native_finish_reason" not in original_choice
    assert original_choice["finish_reason"] == "end_turn"


@pytest.mark.requirement("FR-REQEXT-049")
def test_inject_native_finish_reason_multiple_choices() -> None:
    """GW-49: multiple choices are each transformed independently."""
    body = {
        "choices": [
            {"finish_reason": "end_turn", "index": 0},
            {"finish_reason": "max_tokens", "index": 1},
            {"finish_reason": "tool_use", "index": 2},
        ]
    }
    result = inject_native_finish_reason(body)
    choices = result["choices"]
    assert len(choices) == 3

    assert choices[0]["native_finish_reason"] == "end_turn"
    assert choices[0]["finish_reason"] == "stop"

    assert choices[1]["native_finish_reason"] == "max_tokens"
    assert choices[1]["finish_reason"] == "length"

    assert choices[2]["native_finish_reason"] == "tool_use"
    assert choices[2]["finish_reason"] == "tool_calls"
