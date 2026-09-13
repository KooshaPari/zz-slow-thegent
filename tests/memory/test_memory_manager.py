"""Tests for MemoryManager.

# @trace FR-MEM-002

Covers:
- No-op behaviour when API key is absent
- load_context delegates to SupermemoryClient.search
- save_discovery delegates to SupermemoryClient.add
- get_session_context delegates to SupermemoryClient.search
- Error isolation (Supermemory errors do not propagate)
- Integration with run_impl (memory manager is wired but optional)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thegent.memory.memory_manager import MemoryManager
from thegent.memory.supermemory_client import MemoryEntry, SupermemoryConfigError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(entry_id: str, content: str, score: float = 0.9) -> MemoryEntry:
    return MemoryEntry(
        id=entry_id, content=content, tags=[], created_at="", score=score
    )


def _make_client_mock(
    search_result: list[MemoryEntry] | None = None,
    add_result: str = "mem-001",
) -> MagicMock:
    """Return a mock SupermemoryClient with async methods."""
    mock = MagicMock()
    mock.search = AsyncMock(return_value=search_result or [])
    mock.add = AsyncMock(return_value=add_result)
    mock.delete = AsyncMock(return_value=None)
    mock.list = AsyncMock(return_value=[])
    return mock


# ---------------------------------------------------------------------------
# No-op mode (no API key)
# ---------------------------------------------------------------------------


class TestMemoryManagerNoOp:
    """MemoryManager in no-op mode when API key is absent."""

    def test_enabled_is_false_without_api_key(self, monkeypatch):
        """enabled property is False when key is not set."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager()
        assert mgr.enabled is False

    def test_enabled_is_false_with_empty_env_key(self, monkeypatch):
        """enabled property is False when env var is an empty string."""
        monkeypatch.setenv("THGENT_SUPERMEMORY_API_KEY", "")
        mgr = MemoryManager()
        assert mgr.enabled is False

    @pytest.mark.asyncio
    async def test_load_context_returns_empty_list_without_key(self, monkeypatch):
        """load_context returns [] in no-op mode."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager()
        result = await mgr.load_context("claude")
        assert result == []

    @pytest.mark.asyncio
    async def test_save_discovery_is_silent_without_key(self, monkeypatch):
        """save_discovery does not raise in no-op mode."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager()
        # Must not raise
        await mgr.save_discovery("claude", "some discovery")

    @pytest.mark.asyncio
    async def test_get_session_context_returns_empty_string_without_key(
        self, monkeypatch
    ):
        """get_session_context returns '' in no-op mode."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager()
        result = await mgr.get_session_context("session-abc")
        assert result == ""

    def test_client_is_none_without_key(self, monkeypatch):
        """_client is None when no API key is available."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager()
        assert mgr._client is None

    def test_no_op_with_explicit_none_api_key(self, monkeypatch):
        """Passing api_key=None with no env var results in no-op mode."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager(api_key=None)
        assert mgr.enabled is False


# ---------------------------------------------------------------------------
# Enabled mode (API key present)
# ---------------------------------------------------------------------------


class TestMemoryManagerEnabled:
    """MemoryManager with API key set."""

    def test_enabled_is_true_with_api_key(self, monkeypatch):
        """enabled is True when a key is supplied."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_test123")
        assert mgr.enabled is True

    def test_enabled_is_true_from_env_key(self, monkeypatch):
        """enabled is True when THGENT_SUPERMEMORY_API_KEY is set."""
        monkeypatch.setenv("THGENT_SUPERMEMORY_API_KEY", "sm_env_key")
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager()
        assert mgr.enabled is True

    def test_config_error_on_init_disables_manager(self, monkeypatch):
        """SupermemoryConfigError during init sets enabled=False gracefully."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch(
            "thegent.memory.memory_manager.SupermemoryClient",
            side_effect=SupermemoryConfigError("bad key"),
        ):
            mgr = MemoryManager(api_key="sm_bad")
        assert mgr.enabled is False
        assert mgr._client is None


# ---------------------------------------------------------------------------
# load_context
# ---------------------------------------------------------------------------


class TestLoadContext:
    """Tests for MemoryManager.load_context()."""

    @pytest.fixture
    def mgr_with_mock(self, monkeypatch):
        """Return an enabled MemoryManager with a mocked client."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_test")
        client_mock = _make_client_mock(
            search_result=[
                _make_entry("m1", "past discovery one"),
                _make_entry("m2", "past discovery two"),
            ]
        )
        mgr._client = client_mock
        return mgr, client_mock

    @pytest.mark.asyncio
    async def test_load_context_calls_search_with_agent_id(self, mgr_with_mock):
        """load_context calls client.search with the agent_id."""
        mgr, client_mock = mgr_with_mock
        await mgr.load_context("claude")
        client_mock.search.assert_awaited_once_with("claude", limit=10)

    @pytest.mark.asyncio
    async def test_load_context_returns_content_strings(self, mgr_with_mock):
        """load_context returns list of content strings from MemoryEntry objects."""
        mgr, _ = mgr_with_mock
        result = await mgr.load_context("claude")
        assert result == ["past discovery one", "past discovery two"]

    @pytest.mark.asyncio
    async def test_load_context_returns_empty_list_when_no_results(self, monkeypatch):
        """load_context returns [] when search yields no entries."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_test")
        mgr._client = _make_client_mock(search_result=[])
        result = await mgr.load_context("antigravity")
        assert result == []

    @pytest.mark.asyncio
    async def test_load_context_handles_search_exception(self, monkeypatch):
        """load_context returns [] when client.search raises."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_test")
        client_mock = _make_client_mock()
        client_mock.search = AsyncMock(side_effect=RuntimeError("network down"))
        mgr._client = client_mock
        result = await mgr.load_context("claude")
        assert result == []

    @pytest.mark.asyncio
    async def test_load_context_no_op_without_key(self, monkeypatch):
        """load_context in no-op mode never touches the client."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager()
        # No client at all — must return [] without AttributeError
        result = await mgr.load_context("gemini")
        assert result == []


# ---------------------------------------------------------------------------
# save_discovery
# ---------------------------------------------------------------------------


class TestSaveDiscovery:
    """Tests for MemoryManager.save_discovery()."""

    @pytest.fixture
    def mgr_with_mock(self, monkeypatch):
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_test")
        client_mock = _make_client_mock()
        mgr._client = client_mock
        return mgr, client_mock

    @pytest.mark.asyncio
    async def test_save_discovery_calls_add_with_content_and_tag(self, mgr_with_mock):
        """save_discovery calls client.add(content, tags=[agent_id])."""
        mgr, client_mock = mgr_with_mock
        await mgr.save_discovery("claude", "Agent discovered X causes Y")
        client_mock.add.assert_awaited_once_with(
            "Agent discovered X causes Y", tags=["claude"]
        )

    @pytest.mark.asyncio
    async def test_save_discovery_skips_empty_content(self, mgr_with_mock):
        """save_discovery does not call add when content is empty."""
        mgr, client_mock = mgr_with_mock
        await mgr.save_discovery("claude", "")
        client_mock.add.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_save_discovery_skips_whitespace_content(self, mgr_with_mock):
        """save_discovery does not call add when content is whitespace only."""
        mgr, client_mock = mgr_with_mock
        await mgr.save_discovery("claude", "   \n  ")
        client_mock.add.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_save_discovery_handles_add_exception(self, monkeypatch):
        """save_discovery silently handles exceptions from client.add."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_test")
        client_mock = _make_client_mock()
        client_mock.add = AsyncMock(side_effect=ConnectionError("unreachable"))
        mgr._client = client_mock
        # Must not raise
        await mgr.save_discovery("claude", "some finding")

    @pytest.mark.asyncio
    async def test_save_discovery_no_op_without_key(self, monkeypatch):
        """save_discovery in no-op mode silently returns."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager()
        # Must not raise
        await mgr.save_discovery("gemini", "data point")


# ---------------------------------------------------------------------------
# get_session_context
# ---------------------------------------------------------------------------


class TestGetSessionContext:
    """Tests for MemoryManager.get_session_context()."""

    @pytest.fixture
    def mgr_with_mock(self, monkeypatch):
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_test")
        client_mock = _make_client_mock(
            search_result=[
                _make_entry("s1", "session fact one"),
                _make_entry("s2", "session fact two"),
            ]
        )
        mgr._client = client_mock
        return mgr, client_mock

    @pytest.mark.asyncio
    async def test_get_session_context_calls_search_with_session_id(
        self, mgr_with_mock
    ):
        """get_session_context calls client.search with session_id."""
        mgr, client_mock = mgr_with_mock
        await mgr.get_session_context("sess-xyz")
        client_mock.search.assert_awaited_once_with("sess-xyz", limit=5)

    @pytest.mark.asyncio
    async def test_get_session_context_returns_joined_content(self, mgr_with_mock):
        """get_session_context returns newline-joined content strings."""
        mgr, _ = mgr_with_mock
        result = await mgr.get_session_context("sess-xyz")
        assert result == "session fact one\nsession fact two"

    @pytest.mark.asyncio
    async def test_get_session_context_returns_empty_string_on_no_results(
        self, monkeypatch
    ):
        """get_session_context returns '' when search yields nothing."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_test")
        mgr._client = _make_client_mock(search_result=[])
        result = await mgr.get_session_context("sess-empty")
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_session_context_handles_exception(self, monkeypatch):
        """get_session_context returns '' when search raises."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_test")
        client_mock = _make_client_mock()
        client_mock.search = AsyncMock(side_effect=OSError("disk full"))
        mgr._client = client_mock
        result = await mgr.get_session_context("sess-bad")
        assert result == ""

    @pytest.mark.asyncio
    async def test_get_session_context_no_op_without_key(self, monkeypatch):
        """get_session_context returns '' in no-op mode."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager()
        result = await mgr.get_session_context("sess-noop")
        assert result == ""


# ---------------------------------------------------------------------------
# Integration: run_impl wires MemoryManager (static verification)
# ---------------------------------------------------------------------------


class TestRunImplMemoryIntegration:
    """Verify MemoryManager is wired into run_impl without running real agents."""

    def test_run_impl_source_imports_memory_manager(self):
        """run_impl body references MemoryManager import from memory_manager module."""
        import inspect

        from thegent.cli.commands import impl as cli_impl

        src = inspect.getsource(cli_impl.run_impl)
        assert "MemoryManager" in src, "run_impl must instantiate MemoryManager"
        assert "memory_manager" in src, (
            "run_impl must import from memory_manager module"
        )

    def test_run_impl_source_calls_load_context(self):
        """run_impl body calls load_context on the MemoryManager instance."""
        import inspect

        from thegent.cli.commands import impl as cli_impl

        src = inspect.getsource(cli_impl.run_impl)
        assert "load_context" in src, "run_impl must call load_context"

    def test_run_impl_source_calls_save_discovery(self):
        """run_impl body calls save_discovery after a successful run."""
        import inspect

        from thegent.cli.commands import impl as cli_impl

        src = inspect.getsource(cli_impl.run_impl)
        assert "save_discovery" in src, "run_impl must call save_discovery"

    def test_run_impl_source_checks_enabled_before_memory_ops(self):
        """run_impl guards memory ops behind the enabled property check."""
        import inspect

        from thegent.cli.commands import impl as cli_impl

        src = inspect.getsource(cli_impl.run_impl)
        assert "_mem_mgr.enabled" in src, "run_impl must gate memory ops on enabled"

    def test_memory_manager_no_op_when_constructed_without_key(self, monkeypatch):
        """MemoryManager instantiated without API key is a no-op (enabled=False)."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        mgr = MemoryManager()
        assert not mgr.enabled
        assert mgr._client is None

    @pytest.mark.asyncio
    async def test_memory_manager_full_round_trip_with_mock_client(self, monkeypatch):
        """Full round trip: load_context then save_discovery via mocked client."""
        monkeypatch.delenv("THGENT_SUPERMEMORY_API_KEY", raising=False)
        with patch("thegent.memory.memory_manager.SupermemoryClient"):
            mgr = MemoryManager(api_key="sm_rt_test")

        entries = [
            _make_entry("e1", "prior result A"),
            _make_entry("e2", "prior result B"),
        ]
        client_mock = _make_client_mock(search_result=entries, add_result="new-id")
        mgr._client = client_mock

        # Simulate agent lifecycle: load context, then save a new discovery
        ctx = await mgr.load_context("codex")
        assert ctx == ["prior result A", "prior result B"]
        await mgr.save_discovery("codex", "Discovered that Y implies Z")
        client_mock.add.assert_awaited_once_with(
            "Discovered that Y implies Z", tags=["codex"]
        )
