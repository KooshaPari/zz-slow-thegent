# MIGRATION NOTE: Migrate to cliproxyapi-plusplus Go SDK
# DEPRECATED: This module is now a thin shim for backward compatibility only.
# All new development should use the decomposed modules in:
#   - thegent.adapters.driven.cliproxy_http         # HTTP client adapter
#   - thegent.adapters.driven.cliproxy_ttft         # GW-38 TTFT tracker
#   - thegent.adapters.driven.cliproxy_headers      # GW-20/35/36/43/48/49 headers
#   - thegent.adapters.driven.cliproxy_anthropic_bridge  # GW-43 /v1/messages bridge
#   - thegent.adapters.driven.cliproxy_models_metadata   # GW-46/47 model list
#   - thegent.adapters.driven.cliproxy_openrouter   # OR-08 attribution
#   - thegent.adapters.driven.cliproxy_proxy_handlers   # OR-08/11/13 streaming
#   - thegent.adapters.driven.cliproxy_proxy_router # /v1/* dispatch
#   - thegent.adapters.driven.cliproxy_ws           # WS /v1/responses bridge
#   - thegent.use_cases.manage_cliproxy             # Business logic
#
# Migration status: COMPLETE for L1 hardening pass. The shim now contains
# only the Starlette app factory and the AdapterRegistry registration.
"""CLIProxy adapter shim: exposes /v1/responses (HTTP + WebSocket) for Codex compatibility.

DEPRECATED: This module is now a thin re-export shim. New code should use
the decomposed modules listed in the migration note above.

cliproxyapi++ (kooshapari fork) may not implement /v1/responses. This adapter:
- Proxies all /v1/* to the backend
- For POST /v1/responses: tries backend first; on 404, translates to /v1/chat/completions
- For WebSocket /v1/responses: bridges WS to HTTP streaming (SSE)
"""

from __future__ import annotations

import logging

from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute

# --- decomposed module imports ----------------------------------------------
from thegent.adapters.driven.cliproxy_proxy_router import proxy_handler
from thegent.adapters.driven.cliproxy_ws import websocket_responses_handler
from thegent.adapters.ports import AdapterRegistry

# --- existing decomposed siblings (kept for compatibility) ------------------
from thegent.cliproxy_models_transform import (
    transform_models_response,
)
from thegent.cliproxy_request_transform import (
    _extract_delta_content,
)
from thegent.cliproxy_request_transform import (
    _responses_to_chat_completions as _request_transform_to_chat_completions,
)
from thegent.cliproxy_request_transform import (
    build_openrouter_passthrough_body as _build_openrouter_passthrough_body,
)
from thegent.config import ThegentSettings

_log = logging.getLogger(__name__)


# --- backward-compatible wrappers (legacy surface) ---------------------------
class _LegacyModelsTransformResult(bytes):
    """Legacy test compatibility object that supports both old and new unpack protocols."""

    _full_body: bytes
    _etag: str

    def __new__(cls, compact_body: bytes, full_body: bytes, etag: str):
        obj = super().__new__(cls, compact_body)
        obj._full_body = full_body
        obj._etag = etag
        return obj

    def __iter__(self):
        yield self._full_body
        yield self._etag


def _transform_models_response(content: bytes | memoryview, *, inject_openrouter: bool = False) -> bytes | None:
    """Return the legacy adapter helper output as response bytes only."""
    import orjson as json

    try:
        raw = bytes(content) if isinstance(content, memoryview) else content
        parsed = json.loads(raw.decode(errors="replace"))
        if isinstance(parsed, dict) and "models" in parsed and parsed.get("object") != "list" and "data" not in parsed:
            return None

        transformed = transform_models_response(content, inject_openrouter=inject_openrouter)
        if transformed is None:
            return None
        full_body, etag = transformed

        parsed = json.loads(full_body.decode())
        models = parsed.get("models", [])
        if not isinstance(models, list):
            return None
        compact_models = [{"id": model.get("id")} for model in models if isinstance(model, dict) and model.get("id")]
        compact_body = json.dumps({"models": compact_models}).decode().encode()
        return _LegacyModelsTransformResult(compact_body, full_body, etag)
    except (TypeError, json.JSONDecodeError):
        return None


def build_openrouter_passthrough_body(body: dict) -> dict:
    """Compatibility export for old cliproxy tests and callers."""
    return _build_openrouter_passthrough_body(body)


def _responses_to_chat_completions(body: dict) -> dict:
    """Compatibility wrapper with legacy message formatting.

    NOTE: This is the historical shim-level name; callers expect the legacy
    message-collapse behaviour on top of the upstream request_transform.
    """

    collapse_text_content: list[bool] = []
    input_messages = body.get("input")
    if isinstance(input_messages, list):
        for msg in input_messages:
            collapse = False
            if isinstance(msg, dict):
                raw_content = msg.get("content")
                if (
                    isinstance(raw_content, list)
                    and len(raw_content) == 1
                    and isinstance(raw_content[0], dict)
                    and raw_content[0].get("type") == "text"
                    and "text" in raw_content[0]
                    and len(raw_content[0]) == 2
                ):
                    collapse = True
            collapse_text_content.append(collapse)

    transformed = _request_transform_to_chat_completions(body)
    messages = transformed.get("messages")
    if isinstance(messages, list):
        normalized: list[dict] = []
        for idx, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if isinstance(content, list) and (
                idx < len(collapse_text_content)
                and collapse_text_content[idx]
                and len(content) == 1
                and isinstance(content[0], dict)
                and content[0].get("type") == "text"
                and "text" in content[0]
                and len(content[0]) == 2
            ):
                message["content"] = content[0].get("text", "")
            normalized.append(message)
        transformed["messages"] = normalized
    return transformed


def _chat_completions_to_responses(chunk: dict) -> dict | None:
    """Compatibility wrapper: legacy output shape for adapter callers."""
    text = _extract_delta_content(chunk)
    if not text:
        return None
    return {
        "type": "response.output_item.added",
        "response_id": "resp_legacy",
        "item_id": "item_legacy",
        "output_index": 0,
        "item": {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
        },
    }


# --- Starlette app factory + adapter registration ----------------------------
def create_adapter_app(backend_url: str) -> Starlette:
    """Create the adapter Starlette app."""
    if ThegentSettings().debug:
        _log.setLevel(logging.DEBUG)
    app = Starlette(
        routes=[
            Route("/{path:path}", proxy_handler, methods=["GET", "POST", "OPTIONS"]),
            WebSocketRoute("/v1/responses", websocket_responses_handler),
        ],
    )
    app.state.backend_url = backend_url.rstrip("/")
    return app


# Register with unified adapter registry
class CliproxyAdapter:
    """HTTP proxy adapter for cliproxy"""

    def __init__(self, backend_url: str = "http://127.0.0.1:8318/v1"):
        self._app = create_adapter_app(backend_url)

    def call(self, request=None, **kwargs) -> dict:
        """Proxy request through adapter"""
        return {"status": "ready", "backend": self._app.state.backend_url}

    @property
    def app(self):
        return self._app


AdapterRegistry.register("cliproxy", CliproxyAdapter())
