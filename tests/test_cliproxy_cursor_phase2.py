"""Unit tests for CLIProxy Cursor Phase 2 (G-CP-01 / WL-018).

Tests cover:
  - CursorTokenProvider: file discovery, caching, TTL, refresh on mtime change
  - CursorExecutorManager: rebindExecutors on token rotation
  - build_cursor_routing_config: schema generation, validation

# @trace FR-CP-002
"""

from __future__ import annotations

import time
from pathlib import (
    Path,  # noqa: TC003 -- Path used at runtime in fixture bodies and path operations
)
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thegent.utils.routing_impl.cursor_provider import (
    _TOKEN_TTL_SECONDS,
    CursorExecutorManager,
    CursorProviderConfig,
    CursorTokenProvider,
    build_cursor_routing_config,
)

# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #


@pytest.fixture
def token_file(tmp_path: Path) -> Path:
    """A temporary token file containing a valid sk-... token."""
    f = tmp_path / "session-token.txt"
    f.write_text("sk-testtoken123", encoding="utf-8")
    return f


@pytest.fixture
def provider(token_file: Path) -> CursorTokenProvider:
    return CursorTokenProvider(token_file=token_file)


# --------------------------------------------------------------------------- #
# CursorTokenProvider                                                          #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
class TestCursorTokenProvider:
    """Tests for CursorTokenProvider."""

    def test_get_token_reads_file(self, provider: CursorTokenProvider, token_file: Path) -> None:
        # @trace FR-CP-002
        token = provider.get_token()
        assert token == "sk-testtoken123"

    def test_get_token_caches_within_ttl(self, provider: CursorTokenProvider, token_file: Path) -> None:
        # @trace FR-CP-002
        t1 = provider.get_token()
        # Overwrite file; should NOT be re-read because TTL has not expired
        token_file.write_text("sk-newtoken", encoding="utf-8")
        t2 = provider.get_token()
        assert t1 == t2 == "sk-testtoken123"

    def test_get_token_refreshes_after_ttl(self, provider: CursorTokenProvider, token_file: Path) -> None:
        # @trace FR-CP-002
        provider.get_token()
        # Force TTL expiry by rewinding last_read_at
        provider._last_read_at = time.monotonic() - (_TOKEN_TTL_SECONDS + 1)
        token_file.write_text("sk-refreshed", encoding="utf-8")
        # Touch mtime so refresh detects a change
        token_file.touch()
        t2 = provider.get_token()
        assert t2 == "sk-refreshed"

    def test_is_expired_false_just_after_read(self, provider: CursorTokenProvider) -> None:
        # @trace FR-CP-002
        provider.get_token()
        assert not provider.is_expired()

    def test_is_expired_true_after_ttl(self, provider: CursorTokenProvider) -> None:
        # @trace FR-CP-002
        provider.get_token()
        provider._last_read_at = time.monotonic() - (_TOKEN_TTL_SECONDS + 1)
        assert provider.is_expired()

    def test_get_token_raises_when_file_missing(self, tmp_path: Path) -> None:
        # @trace FR-CP-002
        p = CursorTokenProvider(token_file=tmp_path / "nonexistent.txt")
        with pytest.raises(FileNotFoundError, match="Cursor token file not found"):
            p.get_token()

    def test_refresh_from_disk_returns_true_on_change(self, provider: CursorTokenProvider, token_file: Path) -> None:
        # @trace FR-CP-002
        provider.get_token()
        # Force TTL expiry then change file
        provider._last_read_at = time.monotonic() - (_TOKEN_TTL_SECONDS + 1)
        token_file.write_text("sk-changed", encoding="utf-8")
        token_file.touch()
        changed = provider._refresh_from_disk()
        assert changed
        assert provider._cached_token == "sk-changed"

    def test_refresh_from_disk_returns_false_when_unchanged(
        self, provider: CursorTokenProvider, token_file: Path
    ) -> None:
        # @trace FR-CP-002
        provider.get_token()
        provider._last_read_at = time.monotonic() - (_TOKEN_TTL_SECONDS + 1)
        # Do NOT change file contents or mtime
        changed = provider._refresh_from_disk()
        assert not changed

    def test_discover_returns_none_when_no_candidates(self, tmp_path: Path) -> None:
        # @trace FR-CP-002
        with patch("thegent.utils.routing_impl.cursor_provider._CURSOR_SERVER_TOKEN_CANDIDATES", []):
            result = CursorTokenProvider.discover()
        assert result is None

    def test_discover_returns_provider_for_first_existing_file(self, tmp_path: Path) -> None:
        # @trace FR-CP-002
        token_path = tmp_path / "cursor-token.txt"
        token_path.write_text("sk-discovered", encoding="utf-8")
        with patch(
            "thegent.utils.routing_impl.cursor_provider._CURSOR_SERVER_TOKEN_CANDIDATES",
            [token_path],
        ):
            prov = CursorTokenProvider.discover()
        assert prov is not None
        assert prov.token_file == token_path


# --------------------------------------------------------------------------- #
# CursorExecutorManager                                                        #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
class TestCursorExecutorManager:
    """Tests for CursorExecutorManager."""

    @pytest.mark.asyncio
    async def test_rebind_executors_closes_clients_on_token_change(
        self, provider: CursorTokenProvider, token_file: Path
    ) -> None:
        # @trace FR-CP-002
        provider.get_token()
        manager = CursorExecutorManager(provider=provider)
        manager._last_token = "sk-old"  # simulate stale state

        client = AsyncMock()
        client.aclose = AsyncMock()
        manager.register(client)

        count = await manager.rebind_executors()

        assert count == 1
        client.aclose.assert_awaited_once()
        assert manager._active_clients == []

    @pytest.mark.asyncio
    async def test_rebind_executors_noop_when_token_unchanged(self, provider: CursorTokenProvider) -> None:
        # @trace FR-CP-002
        token = provider.get_token()
        manager = CursorExecutorManager(provider=provider)
        manager._last_token = token  # already up to date

        client = AsyncMock()
        manager.register(client)
        count = await manager.rebind_executors()

        assert count == 0
        client.aclose.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rebind_executors_tolerates_client_aclose_error(self, provider: CursorTokenProvider) -> None:
        # @trace FR-CP-002
        manager = CursorExecutorManager(provider=provider)
        manager._last_token = "sk-stale"

        client = AsyncMock()
        client.aclose = AsyncMock(side_effect=RuntimeError("network gone"))
        manager.register(client)

        # Should not raise
        count = await manager.rebind_executors()
        assert count == 1

    def test_get_auth_headers_returns_bearer(self, provider: CursorTokenProvider) -> None:
        # @trace FR-CP-002
        manager = CursorExecutorManager(provider=provider)
        headers = manager.get_auth_headers()
        assert headers == {"Authorization": "Bearer sk-testtoken123"}

    def test_get_auth_headers_raises_when_token_empty(self, tmp_path: Path) -> None:
        # @trace FR-CP-002
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        prov = CursorTokenProvider(token_file=f)
        manager = CursorExecutorManager(provider=prov)
        with pytest.raises(RuntimeError, match="Cursor token is empty"):
            manager.get_auth_headers()

    def test_register_adds_client(self, provider: CursorTokenProvider) -> None:
        # @trace FR-CP-002
        manager = CursorExecutorManager(provider=provider)
        client = MagicMock()
        manager.register(client)
        assert client in manager._active_clients


# --------------------------------------------------------------------------- #
# CursorProviderConfig / build_cursor_routing_config                          #
# --------------------------------------------------------------------------- #


@pytest.mark.unit
class TestBuildCursorRoutingConfig:
    """Tests for build_cursor_routing_config and CursorProviderConfig."""

    def test_token_file_variant_produces_correct_block(self) -> None:
        # @trace FR-CP-002
        block = build_cursor_routing_config(
            cursor_api_url="http://127.0.0.1:3000",
            token_file="~/.cursor/session-token.txt",
        )
        assert block == {
            "cursor": [
                {
                    "cursor-api-url": "http://127.0.0.1:3000",
                    "token-file": "~/.cursor/session-token.txt",
                }
            ]
        }

    def test_auth_token_variant_produces_correct_block(self) -> None:
        # @trace FR-CP-002
        block = build_cursor_routing_config(
            cursor_api_url="http://127.0.0.1:3000",
            auth_token="${CURSOR_API_AUTH_TOKEN}",
        )
        assert block == {
            "cursor": [
                {
                    "cursor-api-url": "http://127.0.0.1:3000",
                    "auth-token": "${CURSOR_API_AUTH_TOKEN}",
                }
            ]
        }

    def test_trailing_slash_stripped_from_url(self) -> None:
        # @trace FR-CP-002
        block = build_cursor_routing_config(
            cursor_api_url="http://127.0.0.1:3000/",
            token_file="/tmp/tok.txt",
        )
        assert block["cursor"][0]["cursor-api-url"] == "http://127.0.0.1:3000"

    def test_raises_when_no_auth_provided(self) -> None:
        # @trace FR-CP-002
        with pytest.raises(ValueError, match="requires either"):
            build_cursor_routing_config(cursor_api_url="http://127.0.0.1:3000")

    def test_to_cliproxy_block_raises_when_neither_set(self) -> None:
        # @trace FR-CP-002
        cfg = CursorProviderConfig(
            cursor_api_url="http://127.0.0.1:3000",
            token_file="",
            auth_token="",
        )
        with pytest.raises(ValueError, match="requires either token_file or auth_token"):
            cfg.to_cliproxy_block()

    def test_token_file_takes_precedence_over_auth_token(self) -> None:
        # @trace FR-CP-002
        # When both are set, token_file wins (it is checked first in to_cliproxy_block)
        cfg = CursorProviderConfig(
            cursor_api_url="http://127.0.0.1:3000",
            token_file="/tmp/tok.txt",
            auth_token="auth-xyz",
        )
        block = cfg.to_cliproxy_block()
        entry = block["cursor"][0]
        assert "token-file" in entry
        assert "auth-token" not in entry
