"""Tests for SupermemoryClient.

# @trace FR-MEM-001

Uses unittest.mock to stub httpx.AsyncClient without a live network.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from thegent.memory.supermemory_client import (
    MemoryEntry,
    SupermemoryAPIError,
    SupermemoryClient,
    SupermemoryConfigError,
    _is_retryable,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(status_code: int = 200, json_body: Any = None) -> MagicMock:
    """Build a fake httpx.Response-like mock."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.text = ""
    resp.json.return_value = json_body or {}
    # Make raise_for_status raise HTTPStatusError for non-2xx
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


def _patch_client(response: MagicMock) -> Any:
    """Return a context manager that patches httpx.AsyncClient to return `response`."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=response)
    mock_client.get = AsyncMock(return_value=response)
    mock_client.delete = AsyncMock(return_value=response)
    return patch(
        "thegent.memory.supermemory_client.httpx.AsyncClient",
        return_value=mock_client,
    ), mock_client


# ---------------------------------------------------------------------------
# MemoryEntry
# ---------------------------------------------------------------------------


class TestMemoryEntry:
    """Unit tests for MemoryEntry dataclass."""

    def test_from_api_dict_full(self):
        """All fields populated from API dict."""
        data = {
            "id": "mem-1",
            "content": "hello world",
            "tags": ["a", "b"],
            "created_at": "2026-02-19T00:00:00Z",
            "score": 0.95,
        }
        entry = MemoryEntry.from_api_dict(data)
        assert entry.id == "mem-1"
        assert entry.content == "hello world"
        assert entry.tags == ["a", "b"]
        assert entry.created_at == "2026-02-19T00:00:00Z"
        assert entry.score == 0.95

    def test_from_api_dict_missing_optional_fields(self):
        """Missing optional fields use defaults."""
        entry = MemoryEntry.from_api_dict({"id": "x", "content": "y"})
        assert entry.tags == []
        assert entry.created_at == ""
        assert entry.score is None

    def test_from_api_dict_null_tags(self):
        """Null tags in API response become empty list."""
        entry = MemoryEntry.from_api_dict({"id": "x", "content": "y", "tags": None})
        assert entry.tags == []


# ---------------------------------------------------------------------------
# Configuration / Construction
# ---------------------------------------------------------------------------


class TestSupermemoryClientConfig:
    """Tests for SupermemoryClient construction and configuration."""

    def test_raises_config_error_without_api_key(self, monkeypatch):
        """Missing API key raises SupermemoryConfigError immediately."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with pytest.raises(SupermemoryConfigError, match="API key"):
            SupermemoryClient(api_key=None)

    def test_raises_config_error_empty_api_key(self, monkeypatch):
        """Empty string API key (from env) raises SupermemoryConfigError."""
        monkeypatch.setenv("THGENT_SUPERMEMORY_API_KEY", "")
        with pytest.raises(SupermemoryConfigError):
            SupermemoryClient()

    def test_api_key_from_parameter(self, monkeypatch):
        """API key passed directly is accepted."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        client = SupermemoryClient(api_key="sm_test123")
        assert client._headers["x-sm-api-key"] == "sm_test123"

    def test_api_key_from_env(self, monkeypatch):
        """API key from THGENT_SUPERMEMORY_API_KEY env var is accepted."""
        monkeypatch.setenv("THGENT_SUPERMEMORY_API_KEY", "sm_env_key")
        monkeypatch.delenv("THGENT_SUPERMEMORY_BASE_URL", raising=False)
        client = SupermemoryClient()
        assert client._headers["x-sm-api-key"] == "sm_env_key"

    def test_default_base_url(self, monkeypatch):
        """Default base URL is https://api.supermemory.ai/v3."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_BASE_URL", raising=False)
        client = SupermemoryClient(api_key="sm_x")
        assert client._base_url == "https://api.supermemory.ai/v3"

    def test_custom_base_url_from_parameter(self, monkeypatch):
        """Custom base_url parameter overrides default."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_BASE_URL", raising=False)
        client = SupermemoryClient(api_key="sm_x", base_url="https://custom.example.com/v9")
        assert client._base_url == "https://custom.example.com/v9"

    def test_custom_base_url_from_env(self, monkeypatch):
        """Custom base URL from THGENT_SUPERMEMORY_BASE_URL env var."""
        monkeypatch.setenv("THGENT_SUPERMEMORY_BASE_URL", "https://env.example.com/v1")
        client = SupermemoryClient(api_key="sm_x")
        assert client._base_url == "https://env.example.com/v1"

    def test_trailing_slash_stripped_from_base_url(self, monkeypatch):
        """Trailing slash is stripped from base_url."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_BASE_URL", raising=False)
        client = SupermemoryClient(api_key="sm_x", base_url="https://example.com/v3/")
        assert client._base_url == "https://example.com/v3"


# ---------------------------------------------------------------------------
# _is_retryable
# ---------------------------------------------------------------------------


class TestIsRetryable:
    """Tests for _is_retryable helper."""

    def _make_status_error(self, status_code: int) -> httpx.HTTPStatusError:
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status_code
        return httpx.HTTPStatusError(f"HTTP {status_code}", request=MagicMock(), response=resp)

    def test_429_is_retryable(self):
        assert _is_retryable(self._make_status_error(429)) is True

    def test_503_is_retryable(self):
        assert _is_retryable(self._make_status_error(503)) is True

    def test_500_not_retryable(self):
        assert _is_retryable(self._make_status_error(500)) is False

    def test_404_not_retryable(self):
        assert _is_retryable(self._make_status_error(404)) is False

    def test_connect_error_is_retryable(self):
        assert _is_retryable(httpx.ConnectError("connection refused")) is True

    def test_timeout_is_retryable(self):
        assert _is_retryable(httpx.ReadTimeout("timed out")) is True

    def test_value_error_not_retryable(self):
        assert _is_retryable(ValueError("bad value")) is False


# ---------------------------------------------------------------------------
# add()
# ---------------------------------------------------------------------------


class TestSupermemoryClientAdd:
    """Tests for SupermemoryClient.add()."""

    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.delenv("THGENT_SUPERMEMORY_BASE_URL", raising=False)
        return SupermemoryClient(api_key="sm_test", base_url="https://api.supermemory.ai/v3")

    @pytest.mark.asyncio
    async def test_add_returns_memory_id(self, client):
        """add() returns the id from the API response."""
        resp = _mock_response(200, {"id": "mem-abc"})
        (ctx, mock_client) = _patch_client(resp)
        with ctx:
            result = await client.add("some content")
        assert result == "mem-abc"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_with_tags_sends_tags(self, client):
        """add() includes tags in the POST payload."""
        resp = _mock_response(200, {"id": "mem-xyz"})
        (ctx, mock_client) = _patch_client(resp)
        with ctx:
            await client.add("content with tags", tags=["tag1", "tag2"])
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1].get("json") or call_kwargs[0][1]
        assert payload["tags"] == ["tag1", "tag2"]

    @pytest.mark.asyncio
    async def test_add_without_tags_omits_tags_field(self, client):
        """add() without tags does not include tags in payload."""
        resp = _mock_response(200, {"id": "mem-notag"})
        (ctx, mock_client) = _patch_client(resp)
        with ctx:
            await client.add("no tags here")
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs[1].get("json") or call_kwargs[0][1]
        assert "tags" not in payload

    @pytest.mark.asyncio
    async def test_add_raises_api_error_on_400(self, client):
        """add() raises SupermemoryAPIError on a 400 response."""
        resp = _mock_response(400, {"message": "bad request"})
        (ctx, _) = _patch_client(resp)
        with ctx, pytest.raises(SupermemoryAPIError) as exc_info:
            await client.add("bad content")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_add_raises_api_error_on_500(self, client):
        """add() raises SupermemoryAPIError on a 500 response."""
        resp = _mock_response(500, {"message": "internal error"})
        (ctx, _) = _patch_client(resp)
        with ctx, pytest.raises(SupermemoryAPIError):
            await client.add("bad content")


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------


class TestSupermemoryClientSearch:
    """Tests for SupermemoryClient.search()."""

    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.delenv("THGENT_SUPERMEMORY_BASE_URL", raising=False)
        return SupermemoryClient(api_key="sm_test", base_url="https://api.supermemory.ai/v3")

    @pytest.mark.asyncio
    async def test_search_returns_memory_entries(self, client):
        """search() returns list of MemoryEntry objects."""
        api_response = {
            "results": [
                {"id": "m1", "content": "result one", "tags": ["a"], "score": 0.9},
                {"id": "m2", "content": "result two", "tags": [], "score": 0.7},
            ]
        }
        resp = _mock_response(200, api_response)
        (ctx, _) = _patch_client(resp)
        with ctx:
            results = await client.search("some query", limit=5)
        assert len(results) == 2
        assert isinstance(results[0], MemoryEntry)
        assert results[0].id == "m1"
        assert results[0].score == 0.9
        assert results[1].id == "m2"

    @pytest.mark.asyncio
    async def test_search_passes_query_and_limit(self, client):
        """search() sends q and limit as query params."""
        resp = _mock_response(200, {"results": []})
        (ctx, mock_client) = _patch_client(resp)
        with ctx:
            await client.search("my query", limit=3)
        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1].get("params") or {}
        assert params.get("q") == "my query"
        assert params.get("limit") == 3

    @pytest.mark.asyncio
    async def test_search_handles_list_response(self, client):
        """search() handles raw list API response (no 'results' key)."""
        api_response = [{"id": "m3", "content": "direct list"}]
        resp = _mock_response(200, api_response)
        (ctx, _) = _patch_client(resp)
        with ctx:
            results = await client.search("query")
        assert len(results) == 1
        assert results[0].id == "m3"

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_on_no_results(self, client):
        """search() returns empty list when API has no results."""
        resp = _mock_response(200, {"results": []})
        (ctx, _) = _patch_client(resp)
        with ctx:
            results = await client.search("nothing")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_raises_api_error_on_401(self, client):
        """search() raises SupermemoryAPIError on 401."""
        resp = _mock_response(401, {"message": "unauthorized"})
        (ctx, _) = _patch_client(resp)
        with ctx, pytest.raises(SupermemoryAPIError) as exc_info:
            await client.search("query")
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


class TestSupermemoryClientDelete:
    """Tests for SupermemoryClient.delete()."""

    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.delenv("THGENT_SUPERMEMORY_BASE_URL", raising=False)
        return SupermemoryClient(api_key="sm_test", base_url="https://api.supermemory.ai/v3")

    @pytest.mark.asyncio
    async def test_delete_sends_delete_request(self, client):
        """delete() calls DELETE /memories/{id}."""
        resp = _mock_response(200, {})
        (ctx, mock_client) = _patch_client(resp)
        with ctx:
            await client.delete("mem-123")
        mock_client.delete.assert_called_once_with("/memories/mem-123")

    @pytest.mark.asyncio
    async def test_delete_returns_none_on_success(self, client):
        """delete() returns None on successful deletion."""
        resp = _mock_response(204, {})
        resp.is_success = True
        resp.raise_for_status.return_value = None
        (ctx, _) = _patch_client(resp)
        with ctx:
            result = await client.delete("mem-456")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_raises_api_error_on_404(self, client):
        """delete() raises SupermemoryAPIError when memory not found."""
        resp = _mock_response(404, {"message": "not found"})
        (ctx, _) = _patch_client(resp)
        with ctx, pytest.raises(SupermemoryAPIError) as exc_info:
            await client.delete("nonexistent")
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# list()
# ---------------------------------------------------------------------------


class TestSupermemoryClientList:
    """Tests for SupermemoryClient.list()."""

    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.delenv("THGENT_SUPERMEMORY_BASE_URL", raising=False)
        return SupermemoryClient(api_key="sm_test", base_url="https://api.supermemory.ai/v3")

    @pytest.mark.asyncio
    async def test_list_returns_memory_entries(self, client):
        """list() returns all memory entries."""
        api_response = {
            "memories": [
                {"id": "m1", "content": "entry one", "tags": ["t1"]},
                {"id": "m2", "content": "entry two", "tags": ["t2"]},
            ]
        }
        resp = _mock_response(200, api_response)
        (ctx, _) = _patch_client(resp)
        with ctx:
            entries = await client.list()
        assert len(entries) == 2
        assert entries[0].id == "m1"
        assert entries[1].id == "m2"

    @pytest.mark.asyncio
    async def test_list_with_tags_sends_tags_param(self, client):
        """list() sends tags as comma-separated query param."""
        resp = _mock_response(200, {"memories": []})
        (ctx, mock_client) = _patch_client(resp)
        with ctx:
            await client.list(tags=["alpha", "beta"])
        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1].get("params") or {}
        assert params.get("tags") == "alpha,beta"

    @pytest.mark.asyncio
    async def test_list_without_tags_omits_tags_param(self, client):
        """list() without tags doesn't include tags in params."""
        resp = _mock_response(200, {"memories": []})
        (ctx, mock_client) = _patch_client(resp)
        with ctx:
            await client.list()
        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1].get("params") or {}
        assert "tags" not in params

    @pytest.mark.asyncio
    async def test_list_handles_list_response(self, client):
        """list() handles raw list response without 'memories' key."""
        api_response = [{"id": "m5", "content": "raw list entry"}]
        resp = _mock_response(200, api_response)
        (ctx, _) = _patch_client(resp)
        with ctx:
            entries = await client.list()
        assert len(entries) == 1
        assert entries[0].id == "m5"

    @pytest.mark.asyncio
    async def test_list_raises_api_error_on_403(self, client):
        """list() raises SupermemoryAPIError on forbidden."""
        resp = _mock_response(403, {"message": "forbidden"})
        (ctx, _) = _patch_client(resp)
        with ctx, pytest.raises(SupermemoryAPIError) as exc_info:
            await client.list()
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Error message and exception attributes
# ---------------------------------------------------------------------------


class TestSupermemoryAPIError:
    """Tests for SupermemoryAPIError attributes."""

    def test_status_code_attribute(self):
        """SupermemoryAPIError stores status_code."""
        err = SupermemoryAPIError(404, "not found")
        assert err.status_code == 404

    def test_str_contains_status_and_message(self):
        """SupermemoryAPIError str includes status code and message."""
        err = SupermemoryAPIError(500, "oops")
        assert "500" in str(err)
        assert "oops" in str(err)
