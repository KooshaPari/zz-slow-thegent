"""Tests for WL-033 OpenRouter P2 tasks: OR-17, OR-18, OR-19.

Coverage:
- @trace OR-17  Forward x-session-id, x-anthropic-beta, Streaming-Options headers
- @trace OR-18  Native Responses API forwarding for OpenRouter (bypass LiteLLM transform)
- @trace OR-19  Capture openrouter-generation-id from SSE and store in generation_id_store.jsonl
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import orjson as json
import pytest

# ---------------------------------------------------------------------------
# Async iterator helpers (same pattern as existing test file)
# ---------------------------------------------------------------------------


class _AsyncGenFromChunks:
    """Async iterator that yields MagicMock objects wrapping chunk dicts."""

    def __init__(self, chunks: list[dict[str, Any]]) -> None:
        self._chunks = chunks
        self._idx = 0

    def __aiter__(self) -> _AsyncGenFromChunks:
        return self

    async def __anext__(self) -> MagicMock:
        if self._idx >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._idx]
        self._idx += 1
        return MagicMock(**{"model_dump.return_value": chunk})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chat_chunk(content: str | None, finish_reason: str | None = None) -> dict[str, Any]:
    delta: dict[str, Any] = {}
    if content is not None:
        delta["content"] = content
    choice: dict[str, Any] = {"delta": delta}
    if finish_reason is not None:
        choice["finish_reason"] = finish_reason
    return {"choices": [choice]}


def _make_responses_body(
    model: str = "gpt-4o",
    stream: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "input": [{"type": "message", "role": "user", "content": "Hello"}],
        "stream": stream,
    }
    body.update(kwargs)
    return body


# ---------------------------------------------------------------------------
# OR-17: _extract_forward_headers — unit tests (no Starlette TestClient needed)
# ---------------------------------------------------------------------------


class TestExtractForwardHeaders:
    """@trace OR-17"""

    def test_extracts_x_session_id(self) -> None:
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_forward_headers,
        )

        captured: dict[str, str] = {}

        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Route

        async def endpoint(req) -> Response:  # noqa: ANN001
            captured.update(_extract_forward_headers(req))
            return Response("ok")

        app = Starlette(routes=[Route("/", endpoint)])
        client = TestClient(app)
        client.get("/", headers={"x-session-id": "sess-abc123"})
        assert captured == {"x-session-id": "sess-abc123"}

    def test_extracts_x_anthropic_beta(self) -> None:
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_forward_headers,
        )

        captured: dict[str, str] = {}

        async def endpoint(req) -> Response:  # noqa: ANN001
            captured.update(_extract_forward_headers(req))
            return Response("ok")

        app = Starlette(routes=[Route("/", endpoint)])
        client = TestClient(app)
        client.get("/", headers={"x-anthropic-beta": "max-tokens-3-5"})
        assert captured == {"x-anthropic-beta": "max-tokens-3-5"}

    def test_extracts_streaming_options(self) -> None:
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_forward_headers,
        )

        captured: dict[str, str] = {}

        async def endpoint(req) -> Response:  # noqa: ANN001
            captured.update(_extract_forward_headers(req))
            return Response("ok")

        app = Starlette(routes=[Route("/", endpoint)])
        client = TestClient(app)
        client.get("/", headers={"streaming-options": "include_usage"})
        assert captured == {"streaming-options": "include_usage"}

    def test_extracts_all_three_headers_simultaneously(self) -> None:
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_forward_headers,
        )

        captured: dict[str, str] = {}

        async def endpoint(req) -> Response:  # noqa: ANN001
            captured.update(_extract_forward_headers(req))
            return Response("ok")

        app = Starlette(routes=[Route("/", endpoint)])
        client = TestClient(app)
        client.get(
            "/",
            headers={
                "x-session-id": "sess-1",
                "x-anthropic-beta": "beta-val",
                "streaming-options": "opt-val",
            },
        )
        assert captured == {
            "x-session-id": "sess-1",
            "x-anthropic-beta": "beta-val",
            "streaming-options": "opt-val",
        }

    def test_non_whitelisted_headers_are_not_extracted(self) -> None:
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_forward_headers,
        )

        captured: dict[str, str] = {}

        async def endpoint(req) -> Response:  # noqa: ANN001
            captured.update(_extract_forward_headers(req))
            return Response("ok")

        app = Starlette(routes=[Route("/", endpoint)])
        client = TestClient(app)
        client.get("/", headers={"Authorization": "Bearer sk-secret", "x-custom-thing": "val"})
        assert captured == {}

    def test_empty_headers_returns_empty_dict(self) -> None:
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_forward_headers,
        )

        captured: dict[str, str] = {}

        async def endpoint(req) -> Response:  # noqa: ANN001
            captured.update(_extract_forward_headers(req))
            return Response("ok")

        app = Starlette(routes=[Route("/", endpoint)])
        client = TestClient(app)
        client.get("/")
        assert captured == {}


# ---------------------------------------------------------------------------
# OR-17: forwarded headers reach router.acompletion (non-streaming)
# ---------------------------------------------------------------------------


class TestOR17HeadersForwardedToRouter:
    """@trace OR-17"""

    @pytest.mark.asyncio
    async def test_x_session_id_forwarded_as_extra_headers(self) -> None:
        """x-session-id from request must appear in extra_headers kwarg to acompletion."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_choice = MagicMock()
        mock_choice.message.content = "response text"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.id = "resp-001"
        mock_response.model = "gpt-4o"
        mock_response.usage = None

        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        body = json.dumps(_make_responses_body(model="gpt-4o"))

        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "x-session-id": "sess-xyz",
                },
            )

        mock_router.acompletion.assert_awaited_once()
        call_kwargs = mock_router.acompletion.call_args.kwargs
        assert "extra_headers" in call_kwargs
        assert call_kwargs["extra_headers"]["x-session-id"] == "sess-xyz"

    @pytest.mark.asyncio
    async def test_x_anthropic_beta_forwarded_as_extra_headers(self) -> None:
        """x-anthropic-beta from request must appear in extra_headers kwarg to acompletion."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_choice = MagicMock()
        mock_choice.message.content = "ok"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.id = "r1"
        mock_response.model = "gpt-4o"
        mock_response.usage = None

        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        body = json.dumps(_make_responses_body(model="gpt-4o"))

        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "x-anthropic-beta": "max-tokens-3-5",
                },
            )

        call_kwargs = mock_router.acompletion.call_args.kwargs
        assert call_kwargs["extra_headers"]["x-anthropic-beta"] == "max-tokens-3-5"

    @pytest.mark.asyncio
    async def test_streaming_options_forwarded_as_extra_headers(self) -> None:
        """Streaming-Options from request must appear in extra_headers for streaming call."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        chunks = [_make_chat_chunk("Hi")]
        captured_kwargs: dict[str, Any] = {}

        def capturing_acompletion(**kwargs: Any) -> Any:
            captured_kwargs.update(kwargs)
            return _AsyncGenFromChunks(chunks)

        mock_router = MagicMock()
        mock_router.acompletion = capturing_acompletion

        body = json.dumps(_make_responses_body(model="gpt-4o", stream=True))

        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "streaming-options": "include_usage",
                },
            )

        assert "extra_headers" in captured_kwargs
        assert captured_kwargs["extra_headers"]["streaming-options"] == "include_usage"

    @pytest.mark.asyncio
    async def test_no_whitelisted_headers_means_no_extra_headers_key(self) -> None:
        """When no whitelisted headers present, extra_headers must NOT appear in acompletion."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_choice = MagicMock()
        mock_choice.message.content = "ok"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.id = "r2"
        mock_response.model = "gpt-4o"
        mock_response.usage = None

        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        body = json.dumps(_make_responses_body(model="gpt-4o"))

        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        call_kwargs = mock_router.acompletion.call_args.kwargs
        assert "extra_headers" not in call_kwargs


# ---------------------------------------------------------------------------
# OR-18: _is_native_responses_capable
# ---------------------------------------------------------------------------


class TestIsNativeResponsesCapable:
    """@trace OR-18"""

    def test_openrouter_is_capable(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _is_native_responses_capable,
        )

        assert _is_native_responses_capable("openrouter") is True

    def test_openrouter_case_insensitive(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _is_native_responses_capable,
        )

        assert _is_native_responses_capable("OpenRouter") is True

    def test_other_providers_not_capable(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _is_native_responses_capable,
        )

        for provider in ("gpt-4o", "anthropic", "cursor", "gemini", "litellm", ""):
            assert _is_native_responses_capable(provider) is False, f"Expected False for provider={provider!r}"


# ---------------------------------------------------------------------------
# OR-18: _extract_provider_from_model
# ---------------------------------------------------------------------------


class TestExtractProviderFromModel:
    """@trace OR-18"""

    def test_slash_notation_extracts_provider(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_provider_from_model,
        )

        assert _extract_provider_from_model("openrouter/gpt-4o") == "openrouter"

    def test_nested_slash_extracts_first_segment(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_provider_from_model,
        )

        assert _extract_provider_from_model("openrouter/anthropic/claude-opus-4-6") == "openrouter"

    def test_no_slash_returns_empty_string(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_provider_from_model,
        )

        assert _extract_provider_from_model("gpt-4o") == ""

    def test_empty_string_returns_empty_string(self) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _extract_provider_from_model,
        )

        assert _extract_provider_from_model("") == ""


# ---------------------------------------------------------------------------
# OR-18: native responses forwarding — request bypasses LiteLLM transform
# ---------------------------------------------------------------------------


class TestOR18NativeResponsesForwarding:
    """@trace OR-18"""

    @pytest.mark.asyncio
    async def test_openrouter_model_bypasses_litellm_transform(self) -> None:
        """When model is 'openrouter/...', the request must bypass LiteLLM and call httpx directly."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock()

        fake_response_content = json.dumps({"id": "r-native", "object": "response", "status": "completed"})

        mock_httpx_resp = MagicMock()
        mock_httpx_resp.content = fake_response_content
        mock_httpx_resp.status_code = 200
        mock_httpx_resp.headers = {"Content-Type": "application/json"}

        # Create mock client instance BEFORE patching
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_httpx_resp)
        mock_client_instance.post.return_value = mock_httpx_resp
        mock_client_instance.is_closed = False

        body = json.dumps(_make_responses_body(model="openrouter/gpt-4o"))

        # Reset the module-level _http_client to ensure fresh client
        import thegent.utils.routing_impl.litellm_responses_handler as handler

        handler._http_client = None

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test-key"}),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler._get_http_client",
                return_value=mock_client_instance,
            ),
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        # LiteLLM router must NOT have been called
        mock_router.acompletion.assert_not_awaited()
        # httpx must have been called with the OpenRouter endpoint
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert "openrouter.ai" in call_args.args[0]
        # Response must be passed through
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_native_forwarding_injects_api_key_and_attribution_headers(
        self,
    ) -> None:
        """Direct native forward must include Authorization, HTTP-Referer and X-Title headers."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_router = MagicMock()
        mock_httpx_resp = MagicMock()
        mock_httpx_resp.content = b'{"status":"ok"}'
        mock_httpx_resp.status_code = 200
        mock_httpx_resp.headers = {}

        # Create mock client instance BEFORE patching
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_httpx_resp)
        mock_client_instance.post.return_value = mock_httpx_resp
        mock_client_instance.is_closed = False

        body = json.dumps(_make_responses_body(model="openrouter/claude-opus-4-6"))

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-real-key"}),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler._get_http_client",
                return_value=mock_client_instance,
            ),
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        sent_headers = mock_client_instance.post.call_args.kwargs["headers"]
        assert sent_headers.get("Authorization") == "Bearer sk-real-key"
        assert sent_headers.get("HTTP-Referer") == "https://thegent.dev"
        assert sent_headers.get("X-Title") == "thegent"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_native_forwarding_respects_streaming_preference(self) -> None:
        """When the provider returns streaming, the handler should NOT attempt SSE transformation."""
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_router = MagicMock()
        mock_router.model_alias_map = {"openrouter/xyz": "anthropic/claude-3-5-sonnet"}

        mock_httpx_resp = MagicMock()
        mock_httpx_resp.content = b"event: message\ndata: hello"
        mock_httpx_resp.status_code = 200
        mock_httpx_resp.headers = {"content-type": "text/event-stream"}

        # Create mock client instance BEFORE patching
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_httpx_resp)
        mock_client_instance.post.return_value = mock_httpx_resp
        mock_client_instance.is_closed = False

        body = json.dumps(_make_responses_body(model="openrouter/xyz", stream=True))

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-key"}),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler._get_http_client",
                return_value=mock_client_instance,
            ),
        ):
            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "x-session-id": "sess-native",
                },
            )

        sent_headers = mock_client_instance.post.call_args.kwargs["headers"]
        assert sent_headers.get("x-session-id") == "sess-native"

    @pytest.mark.asyncio
    async def test_non_openrouter_model_uses_litellm_transform(self) -> None:
        """When model is NOT openrouter/..., the LiteLLM path must still be used."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        mock_choice = MagicMock()
        mock_choice.message.content = "ok from litellm"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.id = "r3"
        mock_response.model = "gpt-4o"
        mock_response.usage = None

        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(return_value=mock_response)

        body = json.dumps(_make_responses_body(model="gpt-4o"))

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        # LiteLLM must have been called
        mock_router.acompletion.assert_awaited_once()
        # httpx must NOT have been called
        mock_client_cls.assert_not_called()


# ---------------------------------------------------------------------------
# OR-19: _append_generation_id
# ---------------------------------------------------------------------------


class TestAppendGenerationId:
    """@trace OR-19"""

    def test_creates_store_file_and_appends_record(self, tmp_path) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _append_generation_id,
        )

        store = tmp_path / ".thegent" / "generation_id_store.jsonl"

        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler._GENERATION_ID_STORE",
            store,
        ):
            _append_generation_id("req-001", "gen-abc")

        assert store.exists()
        records = [json.loads(line) for line in store.read_text().splitlines() if line]
        assert len(records) == 1
        assert records[0] == {"request_id": "req-001", "generation_id": "gen-abc"}

    def test_appends_multiple_records(self, tmp_path) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _append_generation_id,
        )

        store = tmp_path / ".thegent" / "generation_id_store.jsonl"

        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler._GENERATION_ID_STORE",
            store,
        ):
            _append_generation_id("req-001", "gen-aaa")
            _append_generation_id("req-002", "gen-bbb")
            _append_generation_id("req-003", "gen-ccc")

        records = [json.loads(line) for line in store.read_text().splitlines() if line]
        assert len(records) == 3
        assert records[0]["generation_id"] == "gen-aaa"
        assert records[1]["generation_id"] == "gen-bbb"
        assert records[2]["generation_id"] == "gen-ccc"

    def test_creates_parent_directories(self, tmp_path) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _append_generation_id,
        )

        store = tmp_path / "deep" / "nested" / "dir" / "store.jsonl"

        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler._GENERATION_ID_STORE",
            store,
        ):
            _append_generation_id("req-x", "gen-x")

        assert store.exists()

    def test_record_is_valid_json(self, tmp_path) -> None:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            _append_generation_id,
        )

        store = tmp_path / "store.jsonl"

        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler._GENERATION_ID_STORE",
            store,
        ):
            _append_generation_id("req-json", 'gen-with-"quotes"')

        line = store.read_text().strip()
        parsed = json.loads(line)  # Must not raise
        assert parsed["generation_id"] == 'gen-with-"quotes"'


# ---------------------------------------------------------------------------
# OR-19: SSE stream captures generation_id from chunk data
# ---------------------------------------------------------------------------


class TestOR19GenerationIdCaptureFromStream:
    """@trace OR-19"""

    @pytest.mark.asyncio
    async def test_generation_id_written_when_chunk_contains_openrouter_field(self, tmp_path) -> None:
        """When a chunk contains openrouter-generation-id, it must be appended to the store."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        store = tmp_path / "store.jsonl"

        # Build a chunk with openrouter-generation-id embedded
        chunk_with_gen_id: dict[str, Any] = {
            "choices": [{"delta": {"content": "Hello"}}],
            "openrouter-generation-id": "gen-12345",
        }
        chunks = [chunk_with_gen_id, _make_chat_chunk(None, finish_reason="stop")]

        mock_router = MagicMock()
        mock_router.acompletion = lambda **kwargs: _AsyncGenFromChunks(chunks)

        body = json.dumps(_make_responses_body(model="gpt-4o", stream=True))

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler._GENERATION_ID_STORE",
                store,
            ),
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        assert store.exists(), "generation_id_store.jsonl was not created"
        records = [json.loads(line) for line in store.read_text().splitlines() if line]
        assert len(records) >= 1
        assert records[0]["generation_id"] == "gen-12345"

    @pytest.mark.asyncio
    async def test_generation_id_written_when_chunk_contains_x_generation_id_field(self, tmp_path) -> None:
        """When a chunk contains x-generation-id, it must also be appended to the store."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        store = tmp_path / "store.jsonl"

        chunk_with_gen_id: dict[str, Any] = {
            "choices": [{"delta": {"content": "World"}}],
            "x-generation-id": "xgen-99",
        }
        chunks = [chunk_with_gen_id]

        mock_router = MagicMock()
        mock_router.acompletion = lambda **kwargs: _AsyncGenFromChunks(chunks)

        body = json.dumps(_make_responses_body(model="gpt-4o", stream=True))

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler._GENERATION_ID_STORE",
                store,
            ),
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        assert store.exists()
        records = [json.loads(line) for line in store.read_text().splitlines() if line]
        assert any(r["generation_id"] == "xgen-99" for r in records)

    @pytest.mark.asyncio
    async def test_no_generation_id_in_chunks_means_no_store_write(self, tmp_path) -> None:
        """When chunks contain no generation_id fields, the store file must not be written."""
        from starlette.testclient import TestClient

        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_request,
        )

        store = tmp_path / "store.jsonl"

        chunks = [
            _make_chat_chunk("Hello"),
            _make_chat_chunk(None, finish_reason="stop"),
        ]
        mock_router = MagicMock()
        mock_router.acompletion = lambda **kwargs: _AsyncGenFromChunks(chunks)

        body = json.dumps(_make_responses_body(model="gpt-4o", stream=True))

        with (
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
                return_value=mock_router,
            ),
            patch(
                "thegent.utils.routing_impl.litellm_responses_handler._GENERATION_ID_STORE",
                store,
            ),
        ):
            from starlette.applications import Starlette
            from starlette.routing import Route

            app = Starlette(routes=[Route("/v1/responses", handle_responses_request, methods=["POST"])])
            client = TestClient(app, raise_server_exceptions=False)
            client.post(
                "/v1/responses",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        assert not store.exists(), "store should not be created when no generation_id is present"
