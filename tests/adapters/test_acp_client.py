"""Tests for ACPClient HTTP adapter.

# @trace FR-ACP-001

Uses unittest.mock to stub httpx.AsyncClient without a live network.
Mirrors the pattern established in tests/memory/test_supermemory_client.py.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from thegent.adapters.acp_client import (
    ACPClient,
    ACPClientError,
    ACPResult,
    ACPServerUnreachableError,
    _is_retryable,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(status_code: int = 200, json_body: Any = None) -> MagicMock:
    """Build a fake httpx.Response-like mock.

    Args:
        status_code: HTTP status code to simulate.
        json_body:   JSON payload returned by response.json().

    Returns:
        A MagicMock shaped like an httpx.Response.
    """
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.text = ""
    resp.json.return_value = json_body or {}
    if not resp.is_success:
        http_err = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
        resp.raise_for_status.side_effect = http_err
    else:
        resp.raise_for_status.return_value = None
    return resp


def _patch_client(post_response: MagicMock, get_response: MagicMock | None = None) -> Any:
    """Return a patch context manager for httpx.AsyncClient.

    Args:
        post_response: Mock response returned by client.post().
        get_response:  Mock response returned by client.get() (defaults to 200 OK).

    Returns:
        Tuple of (context_manager, mock_client_instance).
    """
    if get_response is None:
        get_response = _mock_response(200, {})

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=post_response)
    mock_client.get = AsyncMock(return_value=get_response)
    ctx = patch(
        "thegent.adapters.acp_client.httpx.AsyncClient",
        return_value=mock_client,
    )
    return ctx, mock_client


# ---------------------------------------------------------------------------
# _is_retryable
# ---------------------------------------------------------------------------


class TestIsRetryable:
    """Unit tests for the _is_retryable predicate."""

    def _status_error(self, status_code: int) -> httpx.HTTPStatusError:
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status_code
        return httpx.HTTPStatusError(f"HTTP {status_code}", request=MagicMock(), response=resp)

    def test_429_is_retryable(self) -> None:
        """HTTP 429 Too Many Requests is retryable."""
        assert _is_retryable(self._status_error(429)) is True

    def test_503_is_retryable(self) -> None:
        """HTTP 503 Service Unavailable is retryable."""
        assert _is_retryable(self._status_error(503)) is True

    def test_500_not_retryable(self) -> None:
        """HTTP 500 Internal Server Error is NOT retryable."""
        assert _is_retryable(self._status_error(500)) is False

    def test_404_not_retryable(self) -> None:
        """HTTP 404 Not Found is NOT retryable."""
        assert _is_retryable(self._status_error(404)) is False

    def test_400_not_retryable(self) -> None:
        """HTTP 400 Bad Request is NOT retryable."""
        assert _is_retryable(self._status_error(400)) is False

    def test_connect_error_is_retryable(self) -> None:
        """ConnectError (unreachable host) is retryable."""
        assert _is_retryable(httpx.ConnectError("connection refused")) is True

    def test_read_timeout_is_retryable(self) -> None:
        """ReadTimeout is retryable."""
        assert _is_retryable(httpx.ReadTimeout("timed out")) is True

    def test_remote_protocol_error_is_retryable(self) -> None:
        """RemoteProtocolError (e.g. server hung up) is retryable."""
        assert _is_retryable(httpx.RemoteProtocolError("peer closed")) is True

    def test_value_error_not_retryable(self) -> None:
        """Generic ValueError is NOT retryable."""
        assert _is_retryable(ValueError("bad value")) is False

    def test_runtime_error_not_retryable(self) -> None:
        """Generic RuntimeError is NOT retryable."""
        assert _is_retryable(RuntimeError("something broke")) is False


# ---------------------------------------------------------------------------
# ACPResult dataclass
# ---------------------------------------------------------------------------


class TestACPResult:
    """Unit tests for the ACPResult dataclass."""

    def test_fields_stored_correctly(self) -> None:
        """All fields are stored and accessible."""
        r = ACPResult(success=True, result="hello", agent_id="remote-1", elapsed_ms=42.5)
        assert r.success is True
        assert r.result == "hello"
        assert r.agent_id == "remote-1"
        assert r.elapsed_ms == 42.5

    def test_failure_result(self) -> None:
        """success=False is expressible."""
        r = ACPResult(success=False, result="", agent_id="unknown", elapsed_ms=0.0)
        assert r.success is False


# ---------------------------------------------------------------------------
# ACPClient construction
# ---------------------------------------------------------------------------


class TestACPClientConstruction:
    """Tests for ACPClient construction."""

    def test_default_base_url(self) -> None:
        """Default base URL is http://localhost:8080."""
        client = ACPClient()
        assert client._base_url == "http://localhost:8080"

    def test_default_agent_id(self) -> None:
        """Default agent_id is 'thegent'."""
        client = ACPClient()
        assert client._agent_id == "thegent"

    def test_custom_base_url_stored(self) -> None:
        """Custom base URL is stored (trailing slash stripped)."""
        client = ACPClient(base_url="http://example.com:9000/")
        assert client._base_url == "http://example.com:9000"

    def test_custom_agent_id_stored(self) -> None:
        """Custom agent_id is stored."""
        client = ACPClient(agent_id="my-agent")
        assert client._agent_id == "my-agent"

    def test_trailing_slash_stripped(self) -> None:
        """Trailing slash on base_url is stripped."""
        client = ACPClient(base_url="http://host:1234/")
        assert not client._base_url.endswith("/")


# ---------------------------------------------------------------------------
# ACPClient.send_task
# ---------------------------------------------------------------------------


class TestSendTask:
    """Tests for ACPClient.send_task()."""

    @pytest.fixture
    def client(self) -> ACPClient:
        return ACPClient(base_url="http://acp.test:8080", agent_id="thegent")

    @pytest.mark.asyncio
    async def test_send_task_success_returns_result(self, client: ACPClient) -> None:
        """send_task() returns an ACPResult with the agent's reply on success."""
        resp = _mock_response(200, {"result": "task done", "agent_id": "remote-agent"})
        ctx, _ = _patch_client(resp)
        with ctx:
            result = await client.send_task("do something")
        assert result.success is True
        assert result.result == "task done"
        assert result.agent_id == "remote-agent"
        assert result.elapsed_ms >= 0

    @pytest.mark.asyncio
    async def test_send_task_posts_to_tasks_endpoint(self, client: ACPClient) -> None:
        """send_task() POSTs to /tasks."""
        resp = _mock_response(200, {"result": "ok", "agent_id": "r"})
        ctx, mock_client = _patch_client(resp)
        with ctx:
            await client.send_task("my task")
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        endpoint = call_args[0][0] if call_args[0] else call_args[1].get("url", "")
        assert endpoint == "/tasks"

    @pytest.mark.asyncio
    async def test_send_task_payload_contains_task_and_agent_id(self, client: ACPClient) -> None:
        """send_task() sends task text and agent_id in the request body."""
        resp = _mock_response(200, {"result": "ok", "agent_id": "r"})
        ctx, mock_client = _patch_client(resp)
        with ctx:
            await client.send_task("analyse codebase")
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1].get("json") or (call_kwargs[0][1] if len(call_kwargs[0]) > 1 else {})
        assert payload["task"] == "analyse codebase"
        assert payload["agent_id"] == "thegent"

    @pytest.mark.asyncio
    async def test_send_task_with_context_includes_context(self, client: ACPClient) -> None:
        """send_task() includes context dict in payload when provided."""
        resp = _mock_response(200, {"result": "ok", "agent_id": "r"})
        ctx, mock_client = _patch_client(resp)
        with ctx:
            await client.send_task("task", context={"repo": "thegent", "branch": "main"})
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1].get("json") or {}
        assert payload.get("context") == {"repo": "thegent", "branch": "main"}

    @pytest.mark.asyncio
    async def test_send_task_without_context_omits_context_key(self, client: ACPClient) -> None:
        """send_task() omits context key when context=None."""
        resp = _mock_response(200, {"result": "ok", "agent_id": "r"})
        ctx, mock_client = _patch_client(resp)
        with ctx:
            await client.send_task("task")
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1].get("json") or {}
        assert "context" not in payload

    @pytest.mark.asyncio
    async def test_send_task_missing_agent_id_in_response_uses_unknown(self, client: ACPClient) -> None:
        """send_task() uses 'unknown' as agent_id when not in the response."""
        resp = _mock_response(200, {"result": "done"})
        ctx, _ = _patch_client(resp)
        with ctx:
            result = await client.send_task("task")
        assert result.agent_id == "unknown"

    @pytest.mark.asyncio
    async def test_send_task_raises_acp_client_error_on_400(self, client: ACPClient) -> None:
        """send_task() raises ACPClientError on HTTP 400."""
        resp = _mock_response(400, {"message": "bad request"})
        ctx, _ = _patch_client(resp)
        with ctx, pytest.raises(ACPClientError) as exc_info:
            await client.send_task("bad task")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_send_task_raises_acp_client_error_on_500(self, client: ACPClient) -> None:
        """send_task() raises ACPClientError on HTTP 500."""
        resp = _mock_response(500, {"message": "server error"})
        ctx, _ = _patch_client(resp)
        with ctx, pytest.raises(ACPClientError) as exc_info:
            await client.send_task("task")
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_send_task_raises_acp_client_error_on_404(self, client: ACPClient) -> None:
        """send_task() raises ACPClientError on HTTP 404."""
        resp = _mock_response(404, {"message": "not found"})
        ctx, _ = _patch_client(resp)
        with ctx, pytest.raises(ACPClientError):
            await client.send_task("task")

    @pytest.mark.asyncio
    async def test_send_task_raises_unreachable_on_connect_error(self, client: ACPClient) -> None:
        """send_task() raises ACPServerUnreachableError when server is unreachable."""
        mock_client_inst = AsyncMock()
        mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
        mock_client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_inst.post = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with (
            patch(
                "thegent.adapters.acp_client.httpx.AsyncClient",
                return_value=mock_client_inst,
            ),
            pytest.raises(ACPServerUnreachableError),
        ):
            await client.send_task("task")

    @pytest.mark.asyncio
    async def test_send_task_raises_unreachable_on_timeout(self, client: ACPClient) -> None:
        """send_task() raises ACPServerUnreachableError on read timeout."""
        mock_client_inst = AsyncMock()
        mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
        mock_client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_inst.post = AsyncMock(side_effect=httpx.ReadTimeout("timed out"))

        with (
            patch(
                "thegent.adapters.acp_client.httpx.AsyncClient",
                return_value=mock_client_inst,
            ),
            pytest.raises(ACPServerUnreachableError),
        ):
            await client.send_task("task")

    @pytest.mark.asyncio
    async def test_send_task_elapsed_ms_is_positive(self, client: ACPClient) -> None:
        """send_task() records a non-negative elapsed time."""
        resp = _mock_response(200, {"result": "ok", "agent_id": "r"})
        ctx, _ = _patch_client(resp)
        with ctx:
            result = await client.send_task("quick task")
        assert result.elapsed_ms >= 0.0


# ---------------------------------------------------------------------------
# ACPClient.health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Tests for ACPClient.health_check()."""

    @pytest.fixture
    def client(self) -> ACPClient:
        return ACPClient(base_url="http://acp.test:8080")

    @pytest.mark.asyncio
    async def test_health_check_returns_true_on_200(self, client: ACPClient) -> None:
        """health_check() returns True when server responds with 200."""
        resp = _mock_response(200, {})
        ctx, _ = _patch_client(_mock_response(200), get_response=resp)
        with ctx:
            healthy = await client.health_check()
        assert healthy is True

    @pytest.mark.asyncio
    async def test_health_check_returns_true_on_204(self, client: ACPClient) -> None:
        """health_check() returns True for any 2xx status."""
        resp = _mock_response(204)
        resp.is_success = True
        ctx, _ = _patch_client(_mock_response(200), get_response=resp)
        with ctx:
            healthy = await client.health_check()
        assert healthy is True

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_503(self, client: ACPClient) -> None:
        """health_check() returns False when server responds with 503."""
        resp = _mock_response(503)
        ctx, _ = _patch_client(_mock_response(200), get_response=resp)
        with ctx:
            healthy = await client.health_check()
        assert healthy is False

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_connect_error(self, client: ACPClient) -> None:
        """health_check() returns False when server is unreachable."""
        mock_client_inst = AsyncMock()
        mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
        mock_client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_inst.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with patch(
            "thegent.adapters.acp_client.httpx.AsyncClient",
            return_value=mock_client_inst,
        ):
            healthy = await client.health_check()
        assert healthy is False

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_timeout(self, client: ACPClient) -> None:
        """health_check() returns False when the request times out."""
        mock_client_inst = AsyncMock()
        mock_client_inst.__aenter__ = AsyncMock(return_value=mock_client_inst)
        mock_client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_inst.get = AsyncMock(side_effect=httpx.ReadTimeout("timeout"))

        with patch(
            "thegent.adapters.acp_client.httpx.AsyncClient",
            return_value=mock_client_inst,
        ):
            healthy = await client.health_check()
        assert healthy is False

    @pytest.mark.asyncio
    async def test_health_check_hits_health_endpoint(self, client: ACPClient) -> None:
        """health_check() GETs /health."""
        resp = _mock_response(200)
        ctx, mock_client_inst = _patch_client(_mock_response(200), get_response=resp)
        with ctx:
            await client.health_check()
        mock_client_inst.get.assert_called_once_with("/health")


# ---------------------------------------------------------------------------
# ACPClientError attributes
# ---------------------------------------------------------------------------


class TestACPClientError:
    """Tests for ACPClientError exception attributes."""

    def test_status_code_stored(self) -> None:
        """ACPClientError stores the HTTP status code."""
        err = ACPClientError(404, "not found")
        assert err.status_code == 404

    def test_str_contains_status_and_message(self) -> None:
        """str(ACPClientError) includes the status code and message."""
        err = ACPClientError(500, "oops")
        assert "500" in str(err)
        assert "oops" in str(err)
