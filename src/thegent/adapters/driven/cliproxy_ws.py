"""WebSocket /v1/responses ↔ HTTP SSE bridge.

Extracted from cliproxy_adapter.py as part of L1 architecture hardening.

WL-001: WebSocket auth header forwarding is preserved via
extract_websocket_forward_headers. WL-005: SSE comment lines are skipped
during line-buffering.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any

import orjson as json

from thegent.cliproxy_error_utils import _make_error_body
from thegent.cliproxy_header_utils import extract_websocket_forward_headers
from thegent.cliproxy_request_transform import (
    _extract_delta_content,
    _extract_delta_tool_calls,
    _extract_usage,
    _responses_to_chat_completions,
)
from thegent.cliproxy_stream_state import ResponsesStreamState
from thegent.config import ThegentSettings

_log = logging.getLogger(__name__)


async def _try_litellm_dispatch(websocket: Any) -> bool:
    """Return True if the LiteLLM router handled the WS frame; False to fall through.

    Any exception is logged and treated as a fallback to the CLIProxy path.
    """
    settings = ThegentSettings()
    if not settings.use_litellm_router:
        return False
    try:
        from thegent.utils.routing_impl.litellm_responses_handler import (
            handle_responses_websocket,
        )

        await handle_responses_websocket(websocket)
        return True
    except Exception as exc:  # pragma: no cover - logged path
        _log.error("LiteLLM Router WebSocket handler failed: %s", exc, exc_info=True)
        return False


def _build_backend_url(backend: str) -> str:
    """Resolve the upstream /chat/completions URL from the configured backend base."""
    base = backend.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _build_request_payload(data: dict[str, Any]) -> bytes:
    """Marshal a WS frame to upstream JSON bytes; force-stream Responses requests."""
    if "input" in data:
        transformed = _responses_to_chat_completions(data)
        transformed["stream"] = True
        return json.dumps(transformed).encode()
    return json.dumps(data).encode()


async def _process_sse_chunk(
    chunk: bytes,
    *,
    buffer: bytearray,
    state: ResponsesStreamState,
) -> tuple[list[dict[str, Any]], bool]:
    """Consume one SSE chunk; return (events_to_emit, done_received)."""
    events: list[dict[str, Any]] = []
    done_received = False
    buffer.extend(chunk)
    while b"\n" in buffer:
        idx = buffer.find(b"\n")
        line = bytes(buffer[:idx])
        del buffer[: idx + 1]
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
        # GW-09: capture actual routed model from SSE chunk
        chunk_model = obj.get("model")
        if chunk_model and chunk_model != state.model:
            state.model = chunk_model
        usage = _extract_usage(obj)
        if usage:
            state.set_usage(usage)
        text = _extract_delta_content(obj)
        tool_calls = _extract_delta_tool_calls(obj)
        if text:
            events.append(state.delta_event(text))
        # GW-07: forward tool call deltas
        if tool_calls:
            events.extend(state.tool_call_delta_events(tool_calls))
    return events, done_received


def _closing_events(
    state: ResponsesStreamState,
    *,
    preamble_emitted: bool,
) -> list[dict[str, Any]]:
    """Build the closing-event sequence: preamble (if skipped) + tool done + done."""
    events: list[dict[str, Any]] = []
    if not preamble_emitted:
        events.extend(state.preamble_events())
    events.extend(state.tool_call_closing_events())
    events.extend(state.closing_events())
    return events


async def websocket_responses_handler(websocket: Any) -> None:
    """Bridge WebSocket /v1/responses to HTTP streaming. Buffers SSE by line."""
    import asyncio

    import httpx

    if await _try_litellm_dispatch(websocket):
        return

    await websocket.accept()
    backend = getattr(websocket.app.state, "backend_url", "http://127.0.0.1:8318/v1")
    url = _build_backend_url(backend)

    # Persistent connection: Codex sends multiple requests per WS connection.
    # After response.completed, the connection stays open for the next request.
    async with httpx.AsyncClient(timeout=120.0) as client:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=300.0)
            except TimeoutError:
                _log.debug("ws responses: idle timeout, closing")
                break
            except Exception as exc:
                _log.debug("ws responses: receive_json ended: %s", exc)
                break

            if not isinstance(data, dict):
                continue

            body = _build_request_payload(data)
            # Forward auth and other upstream headers; WS upgrade headers
            # carry Authorization (WL-001).
            headers = extract_websocket_forward_headers(dict(websocket.headers))

            model = data.get("model", "proxy")
            state = ResponsesStreamState(model=model)
            preamble_emitted = False
            done_received = False
            try:
                async with client.stream(
                    "POST", url, content=body, headers=headers
                ) as resp:
                    if resp.status_code != 200:
                        # GW-05 + GW-06: preserve backend error body with semantic code context
                        err_body = await resp.aread()
                        _log.warning(
                            "ws backend error %s: %s", resp.status_code, err_body[:200]
                        )
                        err_obj = _make_error_body(resp.status_code, err_body)
                        await websocket.send_json(
                            {"type": "response.failed", **err_obj}
                        )
                        continue
                    buffer = bytearray()
                    async for chunk in resp.aiter_bytes():
                        events, done_received = await _process_sse_chunk(
                            chunk, buffer=buffer, state=state
                        )
                        if not preamble_emitted and events:
                            for ev in state.preamble_events():
                                await websocket.send_json(ev)
                            preamble_emitted = True
                        for ev in events:
                            await websocket.send_json(ev)
                        if done_received:
                            break
                    # Emit closing sequence after stream ends
                    for ev in _closing_events(state, preamble_emitted=preamble_emitted):
                        await websocket.send_json(ev)
            except Exception as exc:
                _log.warning("ws responses: stream error: %s", exc)
                with contextlib.suppress(Exception):
                    await websocket.send_json(
                        {"type": "response.failed", "error": {"message": str(exc)}}
                    )

    with contextlib.suppress(Exception):
        await websocket.close(1000)
