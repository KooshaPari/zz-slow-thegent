"""Unit tests for cliproxy_adapter (Responses API <-> Chat Completions transform)."""

import orjson as json
import pytest

from thegent.cliproxy_adapter import (
    _chat_completions_to_responses,
    _map_model_for_backend,
    _responses_to_chat_completions,
    _transform_models_response,
)


@pytest.mark.unit
class TestModelMapping:
    """Tests for Codex/MiniMax model alias mapping."""

    def test_codex_minimax_m25_maps_to_minimax_m25(self) -> None:
        """codex-MiniMax-M2.5 -> minimax-m2.5 for CLIProxyAPIPlus."""
        assert _map_model_for_backend("codex-MiniMax-M2.5") == "minimax-m2.5"

    def test_codex_minimax_lowercase_maps(self) -> None:
        """codex-minimax-m2.5 -> minimax-m2.5."""
        assert _map_model_for_backend("codex-minimax-m2.5") == "minimax-m2.5"

    def test_minimax_m25_maps(self) -> None:
        """MiniMax-M2.5 -> minimax-m2.5."""
        assert _map_model_for_backend("MiniMax-M2.5") == "minimax-m2.5"

    def test_unknown_model_passthrough(self) -> None:
        """Unknown models pass through unchanged."""
        assert _map_model_for_backend("gpt-5.3-codex") == "gpt-5.3-codex"
        assert _map_model_for_backend("minimax-m2.5") == "minimax-m2.5"

    def test_claude_opus_thinking_alias_maps_to_supported_backend_id(self) -> None:
        """CLIP-BUG-02: thinking alias maps to base model ID."""
        assert _map_model_for_backend("claude-opus-4-6-thinking") == "claude-opus-4-6"


@pytest.mark.unit
class TestResponsesToChatCompletions:
    """Tests for Responses API -> Chat Completions transform."""

    def test_simple_message_transform(self) -> None:
        """Responses input with message item -> Chat Completions messages."""
        body = {
            "model": "codex-MiniMax-M2.5",
            "input": [
                {"type": "message", "role": "user", "content": [{"type": "text", "text": "Hi"}]},
            ],
            "stream": True,
        }
        out = _responses_to_chat_completions(body)
        assert out["model"] == "minimax-m2.5"
        assert out["messages"] == [{"role": "user", "content": "Hi"}]
        assert out["stream"] is True

    def test_empty_input_defaults_to_user_message(self) -> None:
        """Empty input -> single user message with empty content."""
        body = {"model": "minimax-m2.5", "input": []}
        out = _responses_to_chat_completions(body)
        assert out["messages"] == [{"role": "user", "content": ""}]

    def test_max_tokens_from_max_output_tokens(self) -> None:
        """max_output_tokens maps to max_tokens."""
        body = {"model": "x", "input": [], "max_output_tokens": 1024}
        out = _responses_to_chat_completions(body)
        assert out["max_tokens"] == 1024

    def test_strips_thinking_signatures_in_content_blocks(self) -> None:
        """CLIP-BUG-09/10: remove provider-specific signatures from content arrays."""
        body = {
            "model": "gemini-3",
            "input": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "thinking",
                            "thinking": "trace",
                            "signature": "gemini-signature",
                            "thought_signature": "\\claude#xyz",
                        }
                    ],
                }
            ],
        }
        out = _responses_to_chat_completions(body)
        part = out["messages"][0]["content"][0]
        assert "signature" not in part
        assert "thought_signature" not in part

    def test_custom_tool_is_converted_to_function_tool(self) -> None:
        """CLIP-BUG-01: custom tool payloads are translated for chat-completions backends."""
        body = {
            "model": "claude-opus-4-6-thinking",
            "input": [],
            "tools": [
                {
                    "type": "custom",
                    "name": "run_sql",
                    "description": "Run SQL query",
                    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
                }
            ],
            "tool_choice": {"type": "custom", "name": "run_sql"},
        }
        out = _responses_to_chat_completions(body)
        assert out["tools"] == [
            {
                "type": "function",
                "function": {
                    "name": "run_sql",
                    "description": "Run SQL query",
                    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                },
            }
        ]
        assert out["tool_choice"] == {"type": "function", "function": {"name": "run_sql"}}

    def test_schema_normalization_strips_unsupported_fields_and_nullable_arrays(self) -> None:
        """CLIP-BUG-03/04: normalize schema keys and nullable type arrays."""
        body = {
            "model": "claude-opus-4-6-thinking",
            "input": [],
            "tools": [
                {
                    "type": "custom",
                    "name": "save_doc",
                    "input_schema": {
                        "$id": "x",
                        "type": "object",
                        "patternProperties": {".*": {"type": "string"}},
                        "properties": {
                            "title": {"type": ["string", "null"]},
                        },
                    },
                }
            ],
        }
        out = _responses_to_chat_completions(body)
        params = out["tools"][0]["function"]["parameters"]
        assert "$id" not in params
        assert "patternProperties" not in params
        assert params["properties"]["title"] == {"type": "string", "nullable": True}

    def test_content_blocks_drop_metadata_key(self) -> None:
        """CLIP-BUG-05: metadata keys inside content blocks are not forwarded."""
        body = {
            "model": "claude-opus-4-6-thinking",
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Hello", "metadata": {"source": "x"}},
                    ],
                }
            ],
        }
        out = _responses_to_chat_completions(body)
        assert out["messages"] == [{"role": "user", "content": [{"type": "text", "text": "Hello"}]}]

    def test_preserves_messages_payload_when_input_is_missing(self) -> None:
        """CLIP-BUG-11: keep explicit messages payloads verbatim."""
        messages = [
            {"role": "assistant", "content": [{"type": "thinking", "thinking": "t", "signature": "sig-1"}]},
            {"role": "user", "content": "continue"},
        ]
        body = {"model": "claude-opus-4-6-thinking", "messages": messages}
        out = _responses_to_chat_completions(body)
        assert out["messages"] == messages

    def test_forwards_thinking_and_output_config(self) -> None:
        """CLIP-BUG-11: preserve Claude request envelope fields."""
        body = {
            "model": "claude-opus-4-6-thinking",
            "input": [],
            "thinking": {"type": "enabled", "budget_tokens": 1024},
            "output_config": {"effort": "high"},
        }
        out = _responses_to_chat_completions(body)
        assert out["thinking"] == {"type": "enabled", "budget_tokens": 1024}
        assert out["output_config"] == {"effort": "high"}

    def test_tool_choice_proxy_prefix_normalized_to_declared_tool(self) -> None:
        """CLIP-BUG-12: tool_choice.name must match tools[].name."""
        body = {
            "model": "claude-sonnet-4-6",
            "input": [{"type": "message", "role": "user", "content": "hi"}],
            "tools": [{"type": "function", "function": {"name": "write_file"}}],
            "tool_choice": {"type": "function", "function": {"name": "proxy_write_file"}},
        }
        out = _responses_to_chat_completions(body)
        assert out["tool_choice"]["function"]["name"] == "write_file"


@pytest.mark.unit
class TestChatCompletionsToResponses:
    """Tests for Chat Completions SSE -> Responses API format."""

    def test_content_delta_to_output_item_added(self) -> None:
        """Chat Completions delta with content -> response.output_item.added."""
        chunk = {"choices": [{"delta": {"content": "Hello"}}]}
        out = _chat_completions_to_responses(chunk)
        assert out is not None
        assert out["type"] == "response.output_item.added"
        assert out["item"]["content"] == [{"type": "text", "text": "Hello"}]

    def test_empty_delta_returns_none(self) -> None:
        """Empty content delta -> None (skip)."""
        chunk = {"choices": [{"delta": {}}]}
        assert _chat_completions_to_responses(chunk) is None

    def test_empty_choices_returns_none(self) -> None:
        """No choices -> None."""
        assert _chat_completions_to_responses({"choices": []}) is None


@pytest.mark.unit
class TestTransformModelsResponse:
    """Tests for /v1/models response transform (data -> models for Codex)."""

    def test_data_to_models(self) -> None:
        """CLIProxy data -> Codex models."""
        raw = b'{"data":[{"id":"m1"}],"object":"list"}'
        out = _transform_models_response(raw)
        assert out is not None
        parsed = json.loads(out.decode() if isinstance(out, bytes) else out)
        assert "models" in parsed
        assert parsed["models"] == [{"id": "m1"}]
        assert "data" not in parsed

    def test_already_has_models_returns_none(self) -> None:
        """Response with models key -> no transform."""
        raw = b'{"models":[{"id":"m1"}]}'
        assert _transform_models_response(raw) is None

    def test_invalid_json_returns_none(self) -> None:
        """Invalid JSON -> None."""
        assert _transform_models_response(b"not json") is None
