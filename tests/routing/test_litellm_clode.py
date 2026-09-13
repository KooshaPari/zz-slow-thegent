"""Integration tests for LiteLLM clode route wiring in the MCP HTTP server.

Verifies that:
- POST /v1/responses is registered on the Starlette app returned by http_app()
- The route delegates to handle_responses_request via LiteLLM Router
- Non-streaming and streaming (SSE) response formats are correct
- WebSocket /v1/responses/ws is registered and delegates to handle_responses_websocket
- Error handling propagates correctly through the wired routes

FR traceability:
- @trace FR-ROUTE-001  Request routing: /v1/responses registered on MCP http_app
- @trace FR-ROUTE-002  Non-streaming Responses API format
- @trace FR-ROUTE-003  Streaming SSE Responses API format
- @trace FR-ROUTE-004  Error handling with correct HTTP status codes
- @trace FR-ROUTE-005  WebSocket /v1/responses/ws route
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import orjson as json
import pytest  # noqa: F401 -- collected by pytest; needed for mark decorators
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.testclient import TestClient

# ---------------------------------------------------------------------------
# Async-iterator helpers (shared with handler tests)
# ---------------------------------------------------------------------------


class _AsyncGenFromChunks:
    """Async iterator yielding MagicMock objects wrapping chunk dicts."""

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


class _AsyncGenRaise:
    """Async iterator that immediately raises on first call."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def __aiter__(self) -> _AsyncGenRaise:
        return self

    async def __anext__(self) -> MagicMock:
        raise self._exc


# ---------------------------------------------------------------------------
# Fixtures / factories
# ---------------------------------------------------------------------------


def _make_mock_router(content: str = "Hello from LiteLLM") -> MagicMock:
    """Return a mock LiteLLM Router with acompletion returning content."""
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    router = MagicMock()
    router.acompletion = AsyncMock(return_value=mock_response)
    return router


def _make_responses_body(
    model: str = "gpt-4o",
    content: str = "Hello",
    stream: bool = False,
) -> dict[str, Any]:
    return {
        "model": model,
        "input": [{"type": "message", "role": "user", "content": content}],
        "stream": stream,
    }


def _make_streaming_mock_router(chunks: list[dict[str, Any]]) -> MagicMock:
    """Return a mock LiteLLM Router that yields SSE chunks."""
    router = MagicMock()
    router.acompletion = lambda **kwargs: _AsyncGenFromChunks(chunks)
    return router


def _make_chunk(content: str | None, finish_reason: str | None = None) -> dict[str, Any]:
    delta: dict[str, Any] = {}
    if content is not None:
        delta["content"] = content
    choice: dict[str, Any] = {"delta": delta}
    if finish_reason is not None:
        choice["finish_reason"] = finish_reason
    return {"choices": [choice]}


def _build_isolated_app() -> tuple[Starlette, MagicMock]:
    """Build a minimal Starlette app with /v1/responses wired, plus a mock router.

    Used for integration tests that verify route wiring without the full
    MCP server bootstrap overhead.
    """
    from thegent.utils.routing_impl.litellm_responses_handler import (
        handle_responses_request,
        handle_responses_websocket,
    )

    mock_router = _make_mock_router()
    app = Starlette(
        routes=[
            Route("/v1/responses", handle_responses_request, methods=["POST"]),
            WebSocketRoute("/v1/responses/ws", handle_responses_websocket),
        ]
    )
    return app, mock_router


# ---------------------------------------------------------------------------
# FR-ROUTE-001: Route registration on MCP http_app
# ---------------------------------------------------------------------------


class TestRouteRegistration:
    """@trace FR-ROUTE-001"""

    def test_http_app_returns_app_with_add_route(self) -> None:
        """http_app() result must expose add_route (i.e., is Starlette-compatible)."""
        import thegent.mcp_server as ms

        with patch("thegent.mcp_server._get_event_store", return_value=None):
            app = ms.http_app(stateless_http=True)
        assert hasattr(app, "add_route")

    def test_http_app_returns_app_with_add_websocket_route(self) -> None:
        """http_app() result must expose add_websocket_route."""
        import thegent.mcp_server as ms

        with patch("thegent.mcp_server._get_event_store", return_value=None):
            app = ms.http_app(stateless_http=True)
        assert hasattr(app, "add_websocket_route")

    def test_responses_route_present_in_routes(self) -> None:
        """POST /v1/responses route must appear in the app route list."""
        import thegent.mcp_server as ms

        with patch("thegent.mcp_server._get_event_store", return_value=None):
            app = ms.http_app(stateless_http=True)

        paths = [getattr(r, "path", None) for r in getattr(app, "routes", [])]
        assert "/v1/responses" in paths, f"Expected /v1/responses in routes, got: {paths}"

    def test_websocket_route_present_in_routes(self) -> None:
        """WS /v1/responses/ws route must appear in the app route list."""
        import thegent.mcp_server as ms

        with patch("thegent.mcp_server._get_event_store", return_value=None):
            app = ms.http_app(stateless_http=True)

        paths = [getattr(r, "path", None) for r in getattr(app, "routes", [])]
        assert "/v1/responses/ws" in paths, f"Expected /v1/responses/ws in routes, got: {paths}"

    def test_isolated_app_responses_route_exists(self) -> None:
        """Isolated Starlette app with wired routes must accept POST /v1/responses."""
        mock_router = _make_mock_router()
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        # Route is registered — not 404/405
        assert resp.status_code != 404
        assert resp.status_code != 405


# ---------------------------------------------------------------------------
# FR-ROUTE-002: Non-streaming response format
# ---------------------------------------------------------------------------


class TestNonStreamingResponseFormat:
    """@trace FR-ROUTE-002"""

    def test_post_returns_200(self) -> None:
        """POST /v1/responses returns 200 with a mocked router."""
        mock_router = _make_mock_router("Hello clode")
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(content="Hi").decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 200

    def test_post_returns_output_array(self) -> None:
        """Non-streaming response has 'output' array."""
        mock_router = _make_mock_router("Hi there")
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        data = resp.json()
        assert "output" in data
        assert isinstance(data["output"], list)
        assert len(data["output"]) == 1

    def test_post_output_item_has_message_type(self) -> None:
        """Response output item has type='message'."""
        mock_router = _make_mock_router("Answer")
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        item = resp.json()["output"][0]
        assert item["type"] == "message"

    def test_post_output_item_role_is_assistant(self) -> None:
        """Response output item has role='assistant'."""
        mock_router = _make_mock_router("Reply")
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        item = resp.json()["output"][0]
        assert item["role"] == "assistant"

    def test_post_output_text_matches_router_response(self) -> None:
        """Text in output matches what the mocked router returned."""
        expected = "This is the LiteLLM response"
        mock_router = _make_mock_router(expected)
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        item = resp.json()["output"][0]
        assert item["content"][0]["text"] == expected

    def test_post_content_type_is_json(self) -> None:
        """Non-streaming POST /v1/responses returns Content-Type: application/json."""
        mock_router = _make_mock_router("ok")
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        assert "application/json" in resp.headers.get("content-type", "")

    def test_router_acompletion_called_with_correct_model(self) -> None:
        """Router.acompletion is called with the model from the request body."""
        mock_router = _make_mock_router()
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(model="claude-sonnet-4.5").decode()).encode()
            client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        call_kwargs = mock_router.acompletion.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4.5"

    def test_router_acompletion_called_with_messages(self) -> None:
        """Router.acompletion is called with messages converted from input."""
        mock_router = _make_mock_router()
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(content="Tell me a joke").decode()).encode()
            client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        call_kwargs = mock_router.acompletion.call_args
        messages = call_kwargs.kwargs["messages"]
        assert messages[0]["content"] == "Tell me a joke"


# ---------------------------------------------------------------------------
# FR-ROUTE-003: Streaming SSE response format
# ---------------------------------------------------------------------------


class TestStreamingSSEResponseFormat:
    """@trace FR-ROUTE-003"""

    def test_streaming_request_returns_200(self) -> None:
        """Streaming POST /v1/responses returns 200."""
        chunks = [_make_chunk("Hello"), _make_chunk(None, "stop")]
        mock_router = _make_streaming_mock_router(chunks)
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(stream=True).decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 200

    def test_streaming_response_content_type_is_event_stream(self) -> None:
        """Streaming response has Content-Type: text/event-stream."""
        chunks = [_make_chunk("Hi")]
        mock_router = _make_streaming_mock_router(chunks)
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(stream=True).decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        assert "text/event-stream" in resp.headers.get("content-type", "")

    def test_streaming_response_cache_control_no_cache(self) -> None:
        """Streaming response has Cache-Control: no-cache."""
        mock_router = _make_streaming_mock_router([])
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(stream=True).decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        assert resp.headers.get("cache-control") == "no-cache"

    def test_streaming_response_events_have_sse_data_prefix(self) -> None:
        """Each SSE chunk starts with 'data: '."""
        chunks = [_make_chunk("A"), _make_chunk("B")]
        mock_router = _make_streaming_mock_router(chunks)
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(stream=True).decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        events = [e for e in resp.text.split("\n\n") if e.strip()]
        for event in events:
            assert event.strip().startswith("data: "), f"Event did not start with 'data: ': {event!r}"

    def test_streaming_content_events_have_correct_type(self) -> None:
        """SSE content events have type='response.output_item.added'."""
        chunks = [_make_chunk("Hello")]
        mock_router = _make_streaming_mock_router(chunks)
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(stream=True).decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        events = [e for e in resp.text.split("\n\n") if e.strip()]
        content_events = []
        for event in events:
            payload = json.loads(event.strip().removeprefix("data: "))
            if payload.get("type") == "response.output_item.added":
                content_events.append(payload)
        assert len(content_events) == 1
        assert content_events[0]["item"]["content"][0]["text"] == "Hello"

    def test_streaming_ends_with_completed_event(self) -> None:
        """Last SSE event must be type='response.completed'."""
        chunks = [_make_chunk("Hi")]
        mock_router = _make_streaming_mock_router(chunks)
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(stream=True).decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        events = [e for e in resp.text.split("\n\n") if e.strip()]
        last = json.loads(events[-1].strip().removeprefix("data: "))
        assert last == {"type": "response.completed"}

    def test_streaming_multiple_chunks_all_forwarded(self) -> None:
        """All non-empty SSE chunks are forwarded as response.output_item.added events."""
        chunks = [_make_chunk("Part1"), _make_chunk("Part2"), _make_chunk("Part3")]
        mock_router = _make_streaming_mock_router(chunks)
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(stream=True).decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        events_parsed = [json.loads(e.strip().removeprefix("data: ")) for e in resp.text.split("\n\n") if e.strip()]
        content_events = [e for e in events_parsed if e.get("type") == "response.output_item.added"]
        assert len(content_events) == 3


# ---------------------------------------------------------------------------
# FR-ROUTE-004: Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """@trace FR-ROUTE-004"""

    def test_rate_limit_error_returns_429(self) -> None:
        """Router raising 'rate limit' exception yields 429."""
        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(side_effect=Exception("rate limit exceeded"))
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 429

    def test_unknown_error_returns_500(self) -> None:
        """Unknown exception from router yields 500."""
        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(side_effect=RuntimeError("internal boom"))
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 500

    def test_error_response_body_has_error_key(self) -> None:
        """Error response body contains 'error' key with message."""
        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(side_effect=ValueError("bad request params"))
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        data = resp.json()
        assert "error" in data
        assert "message" in data["error"]

    def test_streaming_error_sends_sse_error_event(self) -> None:
        """Streaming error sends SSE 'error' event at status 200."""
        mock_router = MagicMock()
        mock_router.acompletion = lambda **kwargs: _AsyncGenRaise(RuntimeError("upstream down"))
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body(stream=True).decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 200  # SSE starts 200 even on error
        events = [e for e in resp.text.split("\n\n") if e.strip()]
        first = json.loads(events[0].strip().removeprefix("data: "))
        assert "error" in first

    def test_authentication_error_returns_401(self) -> None:
        """Router raising 'authentication failed' exception yields 401."""
        mock_router = MagicMock()
        mock_router.acompletion = AsyncMock(side_effect=Exception("authentication failed"))
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            app, _ = _build_isolated_app()
            client = TestClient(app, raise_server_exceptions=False)
            body = json.dumps(_make_responses_body().decode()).encode()
            resp = client.post("/v1/responses", content=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# FR-ROUTE-005: WebSocket /v1/responses/ws
# ---------------------------------------------------------------------------


class TestWebSocketResponsesRoute:
    """@trace FR-ROUTE-005"""

    def test_websocket_ws_route_streams_events_and_completes(self) -> None:
        """WS /v1/responses/ws streams content events and sends response.completed."""
        chunks = [_make_chunk("Hello"), _make_chunk(" world")]
        mock_router = _make_streaming_mock_router(chunks)
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            from thegent.utils.routing_impl.litellm_responses_handler import (
                handle_responses_websocket,
            )

            app = Starlette(routes=[WebSocketRoute("/v1/responses/ws", handle_responses_websocket)])
            client = TestClient(app)
            with client.websocket_connect("/v1/responses/ws") as ws:
                ws.send_json(_make_responses_body(stream=True))
                events = []
                for _ in range(10):
                    msg = ws.receive_json()
                    events.append(msg)
                    if msg.get("type") == "response.completed":
                        break

        content_events = [e for e in events if e.get("type") == "response.output_item.added"]
        completed_events = [e for e in events if e.get("type") == "response.completed"]
        assert len(content_events) == 2
        assert len(completed_events) == 1

    def test_websocket_ws_route_first_content_is_correct(self) -> None:
        """WS first content event has correct text from router chunks."""
        chunks = [_make_chunk("First chunk")]
        mock_router = _make_streaming_mock_router(chunks)
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            from thegent.utils.routing_impl.litellm_responses_handler import (
                handle_responses_websocket,
            )

            app = Starlette(routes=[WebSocketRoute("/v1/responses/ws", handle_responses_websocket)])
            client = TestClient(app)
            with client.websocket_connect("/v1/responses/ws") as ws:
                ws.send_json(_make_responses_body(stream=True))
                events = []
                for _ in range(5):
                    msg = ws.receive_json()
                    events.append(msg)
                    if msg.get("type") == "response.completed":
                        break

        content = [e for e in events if e.get("type") == "response.output_item.added"]
        assert content[0]["item"]["content"][0]["text"] == "First chunk"

    def test_websocket_ws_route_error_sends_error_message(self) -> None:
        """WS handler sends error JSON when router fails."""
        mock_router = MagicMock()
        mock_router.acompletion = lambda **kwargs: _AsyncGenRaise(ValueError("bad model"))
        with patch(
            "thegent.utils.routing_impl.litellm_responses_handler.get_litellm_router",
            return_value=mock_router,
        ):
            from thegent.utils.routing_impl.litellm_responses_handler import (
                handle_responses_websocket,
            )

            app = Starlette(routes=[WebSocketRoute("/v1/responses/ws", handle_responses_websocket)])
            client = TestClient(app)
            with client.websocket_connect("/v1/responses/ws") as ws:
                ws.send_json(_make_responses_body())
                msg = ws.receive_json()

        assert "error" in msg
        assert "bad model" in msg["error"]["message"]
