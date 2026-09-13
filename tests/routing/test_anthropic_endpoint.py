"""Tests for GW-43: Native Anthropic /v1/messages endpoint helpers.

Coverage:
- anthropic_messages_to_chat_completions: basic conversion, system prepend,
  stream passthrough, no-system case, optional fields
- anthropic_response_to_messages_format: basic format, usage mapping,
  stop_reason, empty choices

# @trace FR-REQEXT-043
"""

from __future__ import annotations

import pytest

from thegent.cliproxy_adapter import (
    anthropic_messages_to_chat_completions,
    anthropic_response_to_messages_format,
)

# ---------------------------------------------------------------------------
# anthropic_messages_to_chat_completions
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_messages_to_chat_completions_basic() -> None:
    """Basic request without system or optional fields converts correctly."""
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": "Hello"}],
    }
    result = anthropic_messages_to_chat_completions(body)

    assert result["model"] == "claude-sonnet-4-6"
    assert result["max_tokens"] == 2048
    assert result["messages"] == [{"role": "user", "content": "Hello"}]
    # Optional fields should not be present when not in input
    assert "stream" not in result
    assert "temperature" not in result


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_messages_to_chat_completions_with_system() -> None:
    """System string is prepended as a system role message."""
    body = {
        "model": "claude-haiku-4-5",
        "max_tokens": 512,
        "system": "You are a helpful assistant.",
        "messages": [{"role": "user", "content": "What is 2+2?"}],
    }
    result = anthropic_messages_to_chat_completions(body)

    assert result["messages"][0] == {"role": "system", "content": "You are a helpful assistant."}
    assert result["messages"][1] == {"role": "user", "content": "What is 2+2?"}
    assert len(result["messages"]) == 2


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_messages_to_chat_completions_stream_preserved() -> None:
    """stream=True is passed through to the result dict."""
    body = {
        "model": "claude-opus-4-6",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "Tell me a story"}],
        "stream": True,
    }
    result = anthropic_messages_to_chat_completions(body)

    assert result["stream"] is True


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_messages_to_chat_completions_no_system() -> None:
    """Without a system field, messages list is unchanged."""
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Reply"},
            {"role": "user", "content": "Follow-up"},
        ],
    }
    result = anthropic_messages_to_chat_completions(body)

    assert len(result["messages"]) == 3
    assert result["messages"][0]["role"] == "user"


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_messages_to_chat_completions_optional_fields() -> None:
    """temperature and top_p are forwarded when present."""
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 256,
        "messages": [{"role": "user", "content": "Hi"}],
        "temperature": 0.7,
        "top_p": 0.9,
    }
    result = anthropic_messages_to_chat_completions(body)

    assert result["temperature"] == 0.7
    assert result["top_p"] == 0.9


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_messages_to_chat_completions_default_max_tokens() -> None:
    """When max_tokens is absent, defaults to 1024."""
    body = {
        "model": "claude-haiku-4-5",
        "messages": [{"role": "user", "content": "Ping"}],
    }
    result = anthropic_messages_to_chat_completions(body)

    assert result["max_tokens"] == 1024


# ---------------------------------------------------------------------------
# anthropic_response_to_messages_format
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_response_to_messages_format_basic() -> None:
    """Basic chat completions response converts to Anthropic messages format."""
    response = {
        "id": "chatcmpl-abc123",
        "model": "claude-sonnet-4-6",
        "choices": [
            {
                "message": {"role": "assistant", "content": "Hello there!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    result = anthropic_response_to_messages_format(response)

    assert result["id"] == "chatcmpl-abc123"
    assert result["type"] == "message"
    assert result["role"] == "assistant"
    assert result["model"] == "claude-sonnet-4-6"
    assert result["content"] == [{"type": "text", "text": "Hello there!"}]
    assert result["stop_reason"] == "end_turn"
    assert result["stop_sequence"] is None


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_response_to_messages_format_usage_mapping() -> None:
    """prompt_tokens maps to input_tokens, completion_tokens to output_tokens."""
    response = {
        "id": "chatcmpl-xyz",
        "model": "claude-opus-4-6",
        "choices": [
            {
                "message": {"role": "assistant", "content": "Done."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 42, "completion_tokens": 17},
    }
    result = anthropic_response_to_messages_format(response)

    assert result["usage"]["input_tokens"] == 42
    assert result["usage"]["output_tokens"] == 17


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_response_to_messages_format_stop_reason() -> None:
    """finish_reason='stop' maps to stop_reason='end_turn'; others pass through."""
    response_stop = {
        "id": "r1",
        "model": "m",
        "choices": [{"message": {"content": ""}, "finish_reason": "stop"}],
        "usage": {},
    }
    result_stop = anthropic_response_to_messages_format(response_stop)
    assert result_stop["stop_reason"] == "end_turn"

    response_length = {
        "id": "r2",
        "model": "m",
        "choices": [{"message": {"content": ""}, "finish_reason": "length"}],
        "usage": {},
    }
    result_length = anthropic_response_to_messages_format(response_length)
    assert result_length["stop_reason"] == "length"


@pytest.mark.requirement("FR-REQEXT-043")
def test_anthropic_response_to_messages_format_empty_choices() -> None:
    """Empty choices list produces empty content text and end_turn stop_reason."""
    response = {
        "id": "r3",
        "model": "claude-haiku-4-5",
        "choices": [],
        "usage": {"prompt_tokens": 5, "completion_tokens": 0},
    }
    result = anthropic_response_to_messages_format(response)

    assert result["content"] == [{"type": "text", "text": ""}]
    assert result["stop_reason"] == "end_turn"
    assert result["usage"]["input_tokens"] == 5
    assert result["usage"]["output_tokens"] == 0
