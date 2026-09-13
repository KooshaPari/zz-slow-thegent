"""Integration tests for cliproxy_adapter: Responses API bridge."""

from unittest.mock import patch

import orjson as json
import pytest

from thegent.cliproxy_adapter import (
    _process_sse_line,
    _proxy_stream,
    _responses_to_chat_completions,
    create_adapter_app,
)


@pytest.mark.integration
class TestAdapterResponsesBridge:
    """Test adapter Responses API transform pipeline."""

    def test_sse_line_transform_pipeline(self) -> None:
        """Chat Completions SSE line -> Responses API format."""
        line = b'data: {"choices":[{"delta":{"content":"Hi"}}]}\n'
        out = _process_sse_line(line, transform=True)
        assert out is not None
        assert b"response.output_item.added" in out
        assert b"Hi" in out

    def test_responses_to_chat_completions_for_backend(self) -> None:
        """Responses API body -> Chat Completions format for backend."""
        body = {
            "model": "glm-5",
            "input": [
                {"type": "message", "role": "user", "content": [{"type": "text", "text": "Hello"}]},
            ],
            "stream": True,
        }
        out = _responses_to_chat_completions(body)
        assert out["model"] == "glm-5"
        assert out["messages"] == [{"role": "user", "content": "Hello"}]
        assert out["stream"] is True

    def test_create_adapter_app_routes(self) -> None:
        """Adapter app has /v1/responses route and proxy handler."""
        app = create_adapter_app("http://127.0.0.1:8318/v1")
        assert hasattr(app, "state")
        assert app.state.backend_url == "http://127.0.0.1:8318/v1"

    def test_passthrough_stream_splits_usage_from_finish_reason(self) -> None:
        """CLIP-BUG-07: usage must be emitted in a separate SSE event from finish_reason."""
        line = (
            b'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}],'
            b'"usage":{"prompt_tokens":1,"completion_tokens":2,"total_tokens":3}}\n'
        )
        out = _process_sse_line(line, transform=False)
        assert out is not None
        events = [part for part in out.decode().split("\n\n") if part.strip()]
        assert len(events) == 2

        first = json.loads(events[0].removeprefix("data: ").strip())
        second = json.loads(events[1].removeprefix("data: ").strip())
        assert "usage" not in first
        assert first["choices"][0]["finish_reason"] == "stop"
        assert second["choices"] == []
        assert second["usage"]["total_tokens"] == 3

    @pytest.mark.asyncio
    async def test_done_marker_flushes_completion_events_immediately(self) -> None:
        """CLIP-BUG-06: [DONE] should trigger completion even if extra bytes follow."""

        class _FakeStreamResponse:
            def __init__(self, payload_chunks: list[bytes]) -> None:
                self.status_code = 200
                self._payload_chunks = payload_chunks

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return None

            async def aiter_bytes(self):
                for chunk in self._payload_chunks:
                    yield chunk

            async def aread(self) -> bytes:
                return b""

        class _FakeAsyncClient:
            def __init__(self, *args, **kwargs) -> None:
                return None

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return None

            def stream(self, method, url, content=None, headers=None):
                chunks = [
                    b'data: {"model":"gemini-3","choices":[{"delta":{"content":"Hello"}}]}\n\n',
                    b"data: [DONE]\n\n",
                    b'data: {"model":"gemini-3","choices":[{"delta":{"content":"should-not-appear"}}]}\n\n',
                ]
                return _FakeStreamResponse(chunks)

        body = json.dumps(
            {
                "model": "gemini-3",
                "input": [{"type": "message", "role": "user", "content": [{"type": "text", "text": "hi"}]}],
                "stream": True,
            }
        ).encode()

        with patch("httpx.AsyncClient", _FakeAsyncClient):
            resp = await _proxy_stream(
                body=body,
                headers={},
                backend_url="http://127.0.0.1:8318/v1",
                path="/v1/responses",
                transform_responses=True,
                model="gemini-3",
            )

            chunks: list[bytes] = []
            async for chunk in resp.body_iterator:
                chunks.append(chunk)

        payload = b"".join(chunks).decode()
        assert "response.completed" in payload
        assert "should-not-appear" not in payload
