"""Non-stream OpenRouter P1 parity tests for cliproxy adapter.

Coverage:
- OR-11: normalize error envelopes while preserving metadata.
- OR-13: retry 408/502/503 with bounded attempts for non-stream requests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import orjson as json
import pytest
from starlette.requests import Request

from thegent.cliproxy_adapter import _make_error_body, _proxy_request


def _mk_request(method: str = "POST", body: bytes = b"{}") -> Request:
    async def receive() -> dict:
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": "/v1/chat/completions",
        "raw_path": b"/v1/chat/completions",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8000),
    }
    return Request(scope, receive)


def test_make_error_body_preserves_metadata_and_code() -> None:
    raw = json.dumps(
        {
            "error": {
                "message": "provider failed",
                "metadata": {"provider_name": "openrouter", "raw_status": 503},
            }
        }
    ).encode()
    out = _make_error_body(503, raw)
    assert out["error"]["code"] == 503
    assert out["error"]["metadata"]["provider_name"] == "openrouter"
    assert out["error"]["metadata"]["raw_status"] == 503


@pytest.mark.asyncio
async def test_proxy_request_402_no_retry_normalized_error() -> None:
    req = _mk_request()
    mock_request = AsyncMock(
        return_value=httpx.Response(
            402,
            content=json.dumps({"error": {"message": "insufficient credits"}}).decode().encode(),
            headers={"content-type": "application/json"},
        )
    )
    with patch("httpx.AsyncClient.request", mock_request):
        resp = await _proxy_request(req, "https://openrouter.ai/api/v1", "/chat/completions")
    payload = json.loads(resp.body.decode())
    assert resp.status_code == 402
    assert payload["error"]["code"] == 402
    assert mock_request.await_count == 1


@pytest.mark.asyncio
async def test_proxy_request_503_retries_then_returns_normalized_error() -> None:
    req = _mk_request()
    mock_request = AsyncMock(
        side_effect=[
            httpx.Response(
                503,
                content=json.dumps({"error": {"metadata": {"provider": "openrouter"}}}).decode().encode(),
                headers={"content-type": "application/json"},
            ),
            httpx.Response(
                503,
                content=json.dumps({"error": {"metadata": {"provider": "openrouter"}}}).decode().encode(),
                headers={"content-type": "application/json"},
            ),
            httpx.Response(
                503,
                content=json.dumps({"error": {"metadata": {"provider": "openrouter"}}}).decode().encode(),
                headers={"content-type": "application/json"},
            ),
            httpx.Response(
                503,
                content=json.dumps({"error": {"metadata": {"provider": "openrouter"}}}).decode().encode(),
                headers={"content-type": "application/json"},
            ),
        ]
    )
    with patch("httpx.AsyncClient.request", mock_request), patch("asyncio.sleep", AsyncMock()) as sleep_mock:
        resp = await _proxy_request(req, "https://openrouter.ai/api/v1", "/chat/completions")
    payload = json.loads(resp.body.decode())
    assert resp.status_code == 503
    assert payload["error"]["code"] == 503
    assert payload["error"]["metadata"]["provider"] == "openrouter"
    assert mock_request.await_count == 4
    assert sleep_mock.await_count == 3


@pytest.mark.asyncio
async def test_proxy_request_502_retry_then_success() -> None:
    req = _mk_request()
    mock_request = AsyncMock(
        side_effect=[
            httpx.Response(
                502,
                content=json.dumps({"error": {"message": "temporary upstream"}}).decode().encode(),
                headers={"content-type": "application/json"},
            ),
            httpx.Response(
                200,
                content=b'{"ok": true}',
                headers={"content-type": "application/json"},
            ),
        ]
    )
    with patch("httpx.AsyncClient.request", mock_request), patch("asyncio.sleep", AsyncMock()) as sleep_mock:
        resp = await _proxy_request(req, "https://openrouter.ai/api/v1", "/chat/completions")
    payload = json.loads(resp.body.decode())
    assert resp.status_code == 200
    assert payload["ok"] is True
    assert mock_request.await_count == 2
    assert sleep_mock.await_count == 1
