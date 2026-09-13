"""Proxy request/stream handlers — forward /v1/* to backend.

Extracted from cliproxy_adapter.py as part of L1 architecture hardening.

OR-08: injects OpenRouter attribution headers.
OR-11: normalises OpenRouter JSON error envelopes.
OR-13: retries transient HTTP statuses (408/502/503) with backoff. 402 (insufficient
       credits) hard-stops on streaming paths.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import cast

import orjson as json
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import Send

from thegent.adapters.driven.cliproxy_openrouter import (
    _inject_openrouter_headers,
    _is_openrouter_backend,
)
from thegent.cliproxy_error_utils import (
    _ERROR_MESSAGES,
    _RETRY_MAX_ATTEMPTS,
    InsufficientCreditsError,
    _make_error_body,
    _RetryableStreamError,
)
from thegent.cliproxy_header_utils import (
    filter_inbound_response_headers,
    sanitize_outbound_request_headers,
)
from thegent.cliproxy_request_transform import (
    _extract_delta_content,
    _extract_delta_tool_calls,
    _extract_usage,
    _process_sse_line,
    _responses_to_chat_completions,
)
from thegent.cliproxy_stream_state import ResponsesStreamState

_log = logging.getLogger(__name__)


async def _proxy_request(
    request: Request,
    backend_url: str,
    path: str,
    *,
    transform_responses: bool = False,
) -> Response:
    """Forward request to backend. Optionally transform Responses <-> Chat Completions.

    OR-11: Normalize OpenRouter JSON error envelopes while preserving metadata.
    OR-13: Retry transient OpenRouter HTTP statuses (408/502/503) for non-streaming paths.
    """
    import asyncio

    import httpx

    body = b""
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
    url = f"{backend_url.rstrip('/')}{path}" if path.startswith("/") else f"{backend_url.rstrip('/')}/{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    headers = sanitize_outbound_request_headers(dict(request.headers))
    # OR-08: inject attribution headers for OpenRouter backends
    _inject_openrouter_headers(headers, backend_url)

    if transform_responses and body and path == "/v1/responses":
        try:
            data = json.loads(body)
            transformed = _responses_to_chat_completions(data)
            body = json.dumps(transformed).decode().encode()
            url = f"{backend_url.rstrip('/')}/v1/chat/completions"
        except (json.JSONDecodeError, KeyError) as e:
            _log.warning("responses->chat transform failed: %s", e)

    try:
        attempts = 0
        async with httpx.AsyncClient(timeout=120.0) as client:
            while True:
                resp = await client.request(
                    request.method,
                    url,
                    content=body,
                    headers=headers,
                )
                is_openrouter = _is_openrouter_backend(backend_url)
                max_attempts = _RETRY_MAX_ATTEMPTS.get(resp.status_code, 0) if is_openrouter else 0
                if max_attempts and attempts < max_attempts:
                    attempts += 1
                    delay = 2.0**attempts
                    _log.warning(
                        "OR-13 non-stream: backend %s retry %d/%d in %.0fs",
                        resp.status_code,
                        attempts,
                        max_attempts,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                break

        filtered_headers = filter_inbound_response_headers(dict(resp.headers))

        if resp.status_code >= 400 and _is_openrouter_backend(backend_url):
            # OR-11: preserve provider metadata and always provide semantic error.code.
            err_obj = _make_error_body(resp.status_code, resp.content)
            filtered_headers["Content-Type"] = "application/json"
            return Response(
                content=json.dumps(err_obj).decode().encode(),
                status_code=resp.status_code,
                headers=filtered_headers,
            )

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=filtered_headers,
        )
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        _log.error("Backend proxy (%s) unreachable: %s", backend_url, e)
        return Response(
            content=json.dumps(
                {"error": {"message": f"Backend proxy ({backend_url}) unreachable. Restart with: thegent mcp restart"}}
            ),
            status_code=503,
            headers={"Content-Type": "application/json"},
        )


async def _proxy_stream(
    body: bytes,
    headers: dict[str, str],
    backend_url: str,
    path: str,
    *,
    transform_responses: bool = False,
    model: str = "proxy",
) -> Response:
    """Stream proxy with optional response transformation. Buffers SSE by line to handle chunk boundaries.

    OR-08: Injects HTTP-Referer + X-Title when backend is OpenRouter.
    OR-13: 402 raises InsufficientCreditsError (no retry). 408/502/503 retried with backoff.
    """
    import asyncio

    import httpx

    # Track the routed model discovered from upstream SSE model field.
    routed_model = model

    class _StreamingResponseWithModel(StreamingResponse):
        """StreamingResponse that refreshes the openai-model header from upstream SSE."""

        async def stream_response(self, send: Send) -> None:  # noqa: PLR0912 -- stream startup state machine
            try:
                iterator = cast("AsyncIterator[bytes | memoryview | str]", self.body_iterator)
                first_chunk = await iterator.__anext__()
            except StopAsyncIteration:
                await send(
                    {
                        "type": "http.response.start",
                        "status": self.status_code,
                        "headers": self.raw_headers,
                    }
                )
                await send({"type": "http.response.body", "body": b"", "more_body": False})
                return

            self.headers["openai-model"] = routed_model
            await send(
                {
                    "type": "http.response.start",
                    "status": self.status_code,
                    "headers": self.raw_headers,
                }
            )
            if not isinstance(first_chunk, bytes | memoryview):
                first_chunk = first_chunk.encode(self.charset)
            await send({"type": "http.response.body", "body": first_chunk, "more_body": True})
            async for chunk in self.body_iterator:
                if not isinstance(chunk, bytes | memoryview):
                    chunk = chunk.encode(self.charset)
                await send({"type": "http.response.body", "body": chunk, "more_body": True})
            await send({"type": "http.response.body", "body": b"", "more_body": False})

    if transform_responses:
        try:
            data = json.loads(body)
            model = data.get("model", model)
            transformed = _responses_to_chat_completions(data)
            body = json.dumps(transformed).decode().encode()
        except (json.JSONDecodeError, KeyError):
            pass
        url = f"{backend_url.rstrip('/')}/chat/completions"
    else:
        url = f"{backend_url.rstrip('/')}{path}" if path.startswith("/") else f"{backend_url.rstrip('/')}/{path}"

    # OR-08: inject OpenRouter attribution headers before streaming begins
    _inject_openrouter_headers(headers, backend_url)

    async def _do_stream(attempt: int):  # noqa: PLR0912 -- streaming state machine; complexity justified
        """Inner generator for a single stream attempt."""
        nonlocal routed_model
        buffer = b""
        state = ResponsesStreamState(model=model) if transform_responses else None
        preamble_emitted = False
        done_received = False
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, content=body, headers=headers) as resp:
                if resp.status_code != 200:
                    # GW-05 + GW-06: preserve backend error body with semantic code context
                    err_body = await resp.aread()
                    _log.warning("backend stream error %s: %s", resp.status_code, err_body[:200])

                    # OR-13: 402 = InsufficientCredits — hard-stop, never retry
                    if resp.status_code == 402:
                        raise InsufficientCreditsError(_ERROR_MESSAGES.get(402, "Payment required"))

                    # OR-13: transient errors — signal caller to retry
                    max_attempts = _RETRY_MAX_ATTEMPTS.get(resp.status_code, 0)
                    if max_attempts and attempt < max_attempts:
                        raise _RetryableStreamError(resp.status_code, err_body)

                    err_obj = _make_error_body(resp.status_code, err_body)
                    yield f"data: {json.dumps(err_obj).decode()}\n\n".encode()
                    return

                async for chunk in resp.aiter_bytes():
                    buffer += chunk
                    while b"\n" in buffer or (buffer and buffer.endswith(b"\n")):
                        idx = buffer.find(b"\n")
                        if idx < 0:
                            break
                        line = buffer[:idx]
                        buffer = buffer[idx + 1 :]
                        if state is not None:
                            line = line.strip()
                            # WL-005: skip SSE comment lines (e.g. ": OPENROUTER PROCESSING")
                            if not line or line.startswith(b":"):
                                continue
                            if not line.startswith(b"data:"):
                                continue
                            data_part = line[5:].strip()
                            if not data_part:
                                continue
                            if data_part == b"[DONE]":
                                done_received = True
                                break
                            try:
                                obj = json.loads(data_part.decode(errors="replace"))
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                continue
                            # GW-09 / OR-12: capture actual routed model from SSE chunk
                            chunk_model = obj.get("model")
                            if chunk_model and chunk_model != state.model:
                                state.model = chunk_model
                                routed_model = chunk_model
                            usage = _extract_usage(obj)
                            if usage:
                                state.set_usage(usage)
                            text = _extract_delta_content(obj)
                            tool_calls = _extract_delta_tool_calls(obj)
                            if text:
                                if not preamble_emitted:
                                    for ev in state.preamble_events():
                                        yield f"data: {json.dumps(ev).decode()}\n\n".encode()
                                    preamble_emitted = True
                                yield f"data: {json.dumps(state.delta_event(text)).decode()}\n\n".encode()
                            # GW-07: forward tool call deltas
                            if tool_calls:
                                for ev in state.tool_call_delta_events(tool_calls):
                                    yield f"data: {json.dumps(ev).decode()}\n\n".encode()
                        else:
                            out = _process_sse_line(line, False)
                            if out:
                                yield out
                    if done_received:
                        break
                if buffer.strip() and state is None:
                    out = _process_sse_line(buffer, False)
                    if out:
                        yield out
                if state is not None:
                    if not preamble_emitted:
                        for ev in state.preamble_events():
                            yield f"data: {json.dumps(ev).decode()}\n\n".encode()
                    # GW-07: emit tool call done events before text closing
                    for ev in state.tool_call_closing_events():
                        yield f"data: {json.dumps(ev).decode()}\n\n".encode()
                    for ev in state.closing_events():
                        yield f"data: {json.dumps(ev).decode()}\n\n".encode()
                    yield b"data: [DONE]\n\n"

    async def _stream_with_retries(attempt: int):
        """Execute a single stream attempt and recurse on retryable failures."""
        try:
            async for chunk in _do_stream(attempt):
                yield chunk
            return
        except InsufficientCreditsError as stream_error:
            # OR-13: 402 — hard-stop, no retry
            _log.error("OR-13: insufficient credits: %s", stream_error)
            err_obj = {"error": {"message": str(stream_error), "code": 402}}
            yield f"data: {json.dumps(err_obj).decode()}\n\n".encode()
            return
        except _RetryableStreamError as stream_error:
            # OR-13: transient error — retry with exponential backoff
            next_attempt = attempt + 1
            delay = 2.0**next_attempt  # 2s, 4s, 8s
            _log.warning(
                "OR-13: backend %s on attempt %d/%d; retrying in %.0fs",
                stream_error.status_code,
                next_attempt,
                _RETRY_MAX_ATTEMPTS.get(stream_error.status_code, 1),
                delay,
            )
            await asyncio.sleep(delay)
            async for chunk in _stream_with_retries(next_attempt):
                yield chunk
            return
        except (httpx.ConnectError, httpx.ConnectTimeout) as stream_error:
            # Connection error — surface and stop
            _log.error("Backend stream connection failed: %s", stream_error)
            yield f'data: {{"error":{{"message":"Backend proxy ({url}) unreachable."}}}}\n\n'.encode()
            return

    async def stream():
        """Outer stream generator: handles OR-13 retry/error routing."""
        async for chunk in _stream_with_retries(0):
            yield chunk

    return _StreamingResponseWithModel(
        stream(),
        status_code=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "openai-model": routed_model,
        },
    )


def _backend_path(backend_url: str, request_path: str) -> str:
    """Path to append to backend base. Backend base is .../v1, so /v1/responses -> /responses."""
    base = backend_url.rstrip("/")
    if base.endswith("/v1") and request_path.startswith("/v1/"):
        return request_path[4:]  # /v1/responses -> /responses
    return request_path
