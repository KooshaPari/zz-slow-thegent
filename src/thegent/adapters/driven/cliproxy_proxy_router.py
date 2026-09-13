"""Proxy router — dispatches /v1/* requests to backend with transformation.

Extracted from cliproxy_adapter.py as part of L1 architecture hardening.

Routes:
- GET /v1/models  → transform models list
- POST /v1/responses → translate to chat completions
- POST /v1/chat/completions → stream or non-stream depending on body
- Other /v1/* → raw proxy

Bifrost: validates claim before proxying when enabled.
LiteLLM Router: when configured, POST /v1/responses and the WebSocket variant
are delegated to the LiteLLM Router handler instead of the legacy CLIProxy
backend path.
"""
from __future__ import annotations

import logging

import orjson as json
from starlette.requests import Request
from starlette.responses import Response

from thegent.adapters.driven.cliproxy_openrouter import _is_openrouter_backend
from thegent.adapters.driven.cliproxy_proxy_handlers import (
    _backend_path,
    _proxy_request,
    _proxy_stream,
)
from thegent.cliproxy_header_utils import sanitize_outbound_request_headers
from thegent.cliproxy_models_transform import transform_models_response
from thegent.config import ThegentSettings
from thegent.integrations.bifrost import BifrostValidationError, get_bifrost

_log = logging.getLogger(__name__)


async def proxy_handler(request: Request) -> Response:
    """Proxy /v1/* to backend. Transform /v1/responses to /v1/chat/completions."""
    # Bifrost validation
    bifrost = get_bifrost()
    if bifrost.is_enabled:
        try:
            claims = {"api_key": request.headers.get("authorization", ""), "identifier": request.client.host}
            bifrost.validate_claims(claims)
        except BifrostValidationError as e:
            return Response(
                content=json.dumps({"error": {"message": str(e)}}),
                status_code=403,
                headers={"Content-Type": "application/json"},
            )

    backend = getattr(request.app.state, "backend_url", "http://127.0.0.1:8318/v1")
    path = request.url.path or "/v1/models"

    # Check if LiteLLM Router should be used
    settings = ThegentSettings()
    use_litellm = settings.use_litellm_router

    if _log.isEnabledFor(logging.DEBUG) or __debug__:
        _log.debug("adapter request: %s %s (litellm=%s)", request.method, path, use_litellm)

    if not path.startswith("/v1/"):
        return Response("Not Found", status_code=404)

    # Route Responses API to LiteLLM Router if enabled
    if use_litellm and path == "/v1/responses" and request.method == "POST":
        try:
            from thegent.utils.routing_impl.litellm_responses_handler import (
                handle_responses_request,
            )

            return await handle_responses_request(request)
        except Exception as e:
            _log.error("LiteLLM Router handler failed: %s", e, exc_info=True)
            # Fallback to CLIProxyAPIPlus

    backend_path = _backend_path(backend, path)

    if request.method == "GET" and path in ("/v1/models", "/v1/models/"):
        resp = await _proxy_request(request, backend, backend_path)
        # Codex expects {"models": [...]}; CLIProxy returns {"data": [...], "object": "list"}
        if resp.status_code == 200 and resp.body:
            # OR-15: inject OpenRouter proxy models when the backend is OpenRouter
            result = transform_models_response(resp.body, inject_openrouter=_is_openrouter_backend(backend))
            if result is not None:
                transformed_body, etag = result
                return Response(
                    content=transformed_body,
                    status_code=200,
                    headers={
                        "Content-Type": "application/json",
                        "x-models-etag": etag,
                    },
                )
        return resp
    if request.method == "POST":
        try:
            body = await request.body()
            data = json.loads(body) if body else {}
            stream_mode = data.get("stream", False)
        except json.JSONDecodeError:
            stream_mode = False

        if path == "/v1/responses":
            # Backend often lacks /v1/responses; translate to /v1/chat/completions
            req_model = data.get("model", "proxy") if isinstance(data, dict) else "proxy"
            if data:
                _log.debug("responses transform: model=%s stream=%s", req_model, data.get("stream"))
            req_headers = sanitize_outbound_request_headers(dict(request.headers))
            return await _proxy_stream(
                body, req_headers, backend, "/chat/completions", transform_responses=True, model=req_model
            )

        if stream_mode and path == "/v1/chat/completions":
            req_headers = sanitize_outbound_request_headers(dict(request.headers))
            return await _proxy_stream(body, req_headers, backend, backend_path)
        return await _proxy_request(request, backend, backend_path)
    return await _proxy_request(request, backend, backend_path)
