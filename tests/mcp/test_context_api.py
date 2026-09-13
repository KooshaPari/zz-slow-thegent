"""Tests for FastMCP Context API usage in thegent MCP tools.

Covers Context API integration for:
- thegent_seed_detect  (mcp_tools_seeds.py) — ctx.info() on start/result, ctx.warning() on error
- thegent_seed_store   (mcp_tools_seeds.py) — ctx.info() on start/stored, ctx.warning() on error
- thegent_seed_list    (mcp_tools_seeds.py) — ctx.info() on start/loaded, ctx.warning() on error
- thegent_ddg_search   (mcp_server.py)      — ctx.info() on start/result
- thegent_scrape_url   (mcp_server.py)      — ctx.info() + ctx.report_progress() throughout
- thegent_dag_run      (mcp_tools_modes.py) — ctx.info() + ctx.report_progress() throughout

FR Traceability: @trace FR-MCP-CTX-001 through FR-MCP-CTX-006
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import orjson as json
import pytest

if TYPE_CHECKING:
    from pathlib import Path

fastmcp = pytest.importorskip("fastmcp", reason="fastmcp required for MCP Context API tests")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx() -> AsyncMock:
    """Create a mock FastMCP Context with all used methods."""
    ctx = AsyncMock()
    ctx.info = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.error = AsyncMock()
    ctx.report_progress = AsyncMock()
    return ctx


def _json_content(result: Any) -> Any:
    """Extract JSON from a ToolResult.content (handles list[TextContent] or str)."""
    if isinstance(result, str):
        return json.loads(result)
    content = result.content
    if isinstance(content, str):
        return json.loads(content)
    if isinstance(content, list) and len(content) > 0:
        text = getattr(content[0], "text", str(content[0]))
        return json.loads(text)
    return json.loads(str(content))


async def _get_tool_fn(mcp: Any, name: str) -> Any:
    """Retrieve the underlying function for a registered tool by name."""
    tool = await mcp.get_tool(name)
    assert tool is not None, f"Tool '{name}' not registered on mcp"
    return tool.fn


# ---------------------------------------------------------------------------
# Seed tools Context API tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSeedDetectContextApi:
    """Context API tests for thegent_seed_detect. @trace FR-MCP-CTX-001"""

    @pytest.mark.asyncio
    async def test_ctx_info_called_on_success(self) -> None:
        """ctx.info() is called at start and on result count."""
        # @trace FR-MCP-CTX-001
        from fastmcp import FastMCP
        from thegent.mcp_tools_seeds import (
            register_seed_tools,
        )

        mcp = FastMCP("test")
        with (
            patch("thegent.mcp.tools.seeds.SeedDetector") as mock_detector_cls,
            patch("thegent.mcp.tools.seeds.SeedDetector.extract_flags", return_value=[]),
        ):
            mock_detector = MagicMock()
            mock_detector.detect_seeds.return_value = []
            mock_detector_cls.return_value = mock_detector

            register_seed_tools(mcp)
            tool_fn = await _get_tool_fn(mcp, "thegent_seed_detect")

            ctx = _make_ctx()
            result = await tool_fn(text="What if we refactor this?", source="user_prompt", ctx=ctx)
            data = _json_content(result)

            assert data["count"] == 0
            assert ctx.info.call_count >= 2, "ctx.info() must be called at start and on result"

    @pytest.mark.asyncio
    async def test_ctx_info_not_called_on_empty_input(self) -> None:
        """ctx.info() is NOT called when input is empty (early return)."""
        # @trace FR-MCP-CTX-001
        from fastmcp import FastMCP
        from thegent.mcp_tools_seeds import register_seed_tools

        mcp = FastMCP("test")
        register_seed_tools(mcp)
        tool_fn = await _get_tool_fn(mcp, "thegent_seed_detect")

        ctx = _make_ctx()
        result = await tool_fn(text="", ctx=ctx)
        data = _json_content(result)
        assert "error" in data
        ctx.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_ctx_warning_called_on_exception(self) -> None:
        """ctx.warning() is called when seed detection raises an exception."""
        # @trace FR-MCP-CTX-001
        from fastmcp import FastMCP
        from thegent.mcp_tools_seeds import register_seed_tools

        mcp = FastMCP("test")
        with patch("thegent.mcp.tools.seeds.SeedDetector") as mock_detector_cls:
            mock_detector_cls.side_effect = RuntimeError("detector exploded")
            register_seed_tools(mcp)
            tool_fn = await _get_tool_fn(mcp, "thegent_seed_detect")

            ctx = _make_ctx()
            result = await tool_fn(text="Some valid text here", ctx=ctx)
            data = _json_content(result)
            assert "error" in data
            ctx.warning.assert_called_once()
            assert "detector exploded" in str(ctx.warning.call_args)

    @pytest.mark.asyncio
    async def test_ctx_none_does_not_raise(self) -> None:
        """Calling with ctx=None falls back to Python logging gracefully."""
        # @trace FR-MCP-CTX-001
        from fastmcp import FastMCP
        from thegent.mcp_tools_seeds import register_seed_tools

        mcp = FastMCP("test")
        with (
            patch("thegent.mcp.tools.seeds.SeedDetector") as mock_detector_cls,
            patch("thegent.mcp.tools.seeds.SeedDetector.extract_flags", return_value=[]),
        ):
            mock_detector = MagicMock()
            mock_detector.detect_seeds.return_value = []
            mock_detector_cls.return_value = mock_detector

            register_seed_tools(mcp)
            tool_fn = await _get_tool_fn(mcp, "thegent_seed_detect")

            # No exception when ctx=None
            result = await tool_fn(text="Consider a new approach", source="manual", ctx=None)
            data = _json_content(result)
            assert "count" in data


@pytest.mark.unit
class TestSeedStoreContextApi:
    """Context API tests for thegent_seed_store. @trace FR-MCP-CTX-002"""

    @pytest.mark.asyncio
    async def test_ctx_info_called_on_store_success(self, tmp_path: Path) -> None:
        """ctx.info() is called at start and after successful store."""
        # @trace FR-MCP-CTX-002
        from fastmcp import FastMCP
        from thegent.mcp_tools_seeds import register_seed_tools

        mcp = FastMCP("test")
        docs_dir = tmp_path / "docs" / "research"
        docs_dir.mkdir(parents=True)

        with (
            patch("thegent.mcp.tools.seeds._resolve_cwd", return_value=tmp_path),
            patch("thegent.mcp.tools.seeds.SeedStorage") as mock_storage_cls,
            patch("thegent.mcp.tools.seeds.SeedDetector") as mock_detector_cls,
        ):
            mock_storage = MagicMock()
            mock_storage.store_seed.return_value = "seed-abc123"
            mock_storage_cls.return_value = mock_storage

            mock_detector = MagicMock()
            mock_seed = MagicMock()
            mock_seed.to_dict.return_value = {"id": "seed-abc123", "text": "test seed"}
            mock_detector.detect_seeds.return_value = [mock_seed]
            mock_detector_cls.return_value = mock_detector

            register_seed_tools(mcp)
            tool_fn = await _get_tool_fn(mcp, "thegent_seed_store")

            ctx = _make_ctx()
            result = await tool_fn(text="We should add caching here", cd=str(tmp_path), ctx=ctx)
            data = _json_content(result)
            assert data.get("stored") is True
            assert ctx.info.call_count >= 2

    @pytest.mark.asyncio
    async def test_ctx_warning_on_exception(self) -> None:
        """ctx.warning() is called when store raises an exception."""
        # @trace FR-MCP-CTX-002
        from fastmcp import FastMCP
        from thegent.mcp_tools_seeds import register_seed_tools

        mcp = FastMCP("test")
        with patch("thegent.mcp.tools.seeds._resolve_cwd", side_effect=RuntimeError("storage failed")):
            register_seed_tools(mcp)
            tool_fn = await _get_tool_fn(mcp, "thegent_seed_store")

            ctx = _make_ctx()
            result = await tool_fn(text="Seed text here", ctx=ctx)
            data = _json_content(result)
            assert "error" in data
            ctx.warning.assert_called_once()


@pytest.mark.unit
class TestSeedListContextApi:
    """Context API tests for thegent_seed_list. @trace FR-MCP-CTX-003"""

    @pytest.mark.asyncio
    async def test_ctx_info_called_with_count(self, tmp_path: Path) -> None:
        """ctx.info() is called with loaded count before and after filtering."""
        # @trace FR-MCP-CTX-003
        from fastmcp import FastMCP
        from thegent.mcp_tools_seeds import register_seed_tools

        mcp = FastMCP("test")
        with (
            patch("thegent.mcp.tools.seeds._resolve_cwd", return_value=tmp_path),
            patch("thegent.mcp.tools.seeds.SeedStorage") as mock_storage_cls,
        ):
            mock_storage = MagicMock()
            mock_seed = MagicMock()
            mock_seed.status = "new"
            mock_seed.tags = ["performance"]
            mock_seed.source = "user_prompt"
            mock_seed.to_dict.return_value = {"id": "s1", "status": "new"}
            mock_storage.load_seeds.return_value = [mock_seed]
            mock_storage_cls.return_value = mock_storage

            register_seed_tools(mcp)
            tool_fn = await _get_tool_fn(mcp, "thegent_seed_list")

            ctx = _make_ctx()
            result = await tool_fn(status="new", cd=str(tmp_path), ctx=ctx)
            data = _json_content(result)
            assert data["count"] == 1
            # ctx.info called at start (with filter params) and after loading
            assert ctx.info.call_count >= 2

    @pytest.mark.asyncio
    async def test_ctx_warning_on_storage_error(self) -> None:
        """ctx.warning() is called when seed storage raises."""
        # @trace FR-MCP-CTX-003
        from fastmcp import FastMCP
        from thegent.mcp_tools_seeds import register_seed_tools

        mcp = FastMCP("test")
        with patch("thegent.mcp.tools.seeds._resolve_cwd", side_effect=OSError("disk error")):
            register_seed_tools(mcp)
            tool_fn = await _get_tool_fn(mcp, "thegent_seed_list")

            ctx = _make_ctx()
            result = await tool_fn(ctx=ctx)
            data = _json_content(result)
            assert "error" in data
            ctx.warning.assert_called_once()


# ---------------------------------------------------------------------------
# mcp_server.py Context API tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDdgSearchContextApi:
    """Context API tests for thegent_ddg_search. @trace FR-MCP-CTX-004"""

    @pytest.mark.asyncio
    async def test_ctx_info_called_before_and_after_search(self) -> None:
        """ctx.info() is called before the search (with query) and after (with count)."""
        # @trace FR-MCP-CTX-004
        import thegent.mcp_server as _mcp_mod

        ctx = _make_ctx()
        mock_results = [{"title": "Test", "url": "http://example.com", "snippet": "test"}]

        with patch("thegent.skills.research.ddg_search", return_value=mock_results):
            result = await _mcp_mod.thegent_ddg_search(
                query="fastmcp context api",
                num_results=3,
                ctx=ctx,
            )
        # content is JSON list, structured_content is {"results": [...], "count": N}
        data = _json_content(result)
        assert isinstance(data, list)
        assert len(data) == 1
        # ctx.info called at start (with query) and after (with count)
        assert ctx.info.call_count >= 2
        # Verify query appears in first info call
        first_call_args = str(ctx.info.call_args_list[0])
        assert "fastmcp context api" in first_call_args

    @pytest.mark.asyncio
    async def test_ctx_accepts_mock_context(self) -> None:
        """thegent_ddg_search accepts a mock ctx without raising."""
        # @trace FR-MCP-CTX-004
        import thegent.mcp_server as _mcp_mod

        ctx = _make_ctx()
        with patch("thegent.skills.research.ddg_search", return_value=[]):
            result = await _mcp_mod.thegent_ddg_search(query="test", num_results=1, ctx=ctx)
        data = _json_content(result)
        # content is JSON list (may be empty)
        assert isinstance(data, list)


@pytest.mark.unit
class TestScrapeUrlContextApi:
    """Context API tests for thegent_scrape_url. @trace FR-MCP-CTX-005"""

    @pytest.mark.asyncio
    async def test_ctx_report_progress_called_multiple_times(self) -> None:
        """ctx.report_progress() is called at 0/3, 1/3, 2/3, and 3/3."""
        # @trace FR-MCP-CTX-005
        import thegent.mcp_server as _mcp_mod

        ctx = _make_ctx()
        mock_result = {"content": "scraped content", "status": 200}

        with patch("thegent.skills.research.scrape_url", new_callable=AsyncMock, return_value=mock_result):
            result = await _mcp_mod.thegent_scrape_url(
                url="https://example.com",
                use_playwright=False,
                ctx=ctx,
            )
        data = _json_content(result)
        assert data.get("status") == 200
        # At least 3 progress reports
        assert ctx.report_progress.call_count >= 3

    @pytest.mark.asyncio
    async def test_ctx_info_called_before_and_after_scrape(self) -> None:
        """ctx.info() is called before scraping and after with content length."""
        # @trace FR-MCP-CTX-005
        import thegent.mcp_server as _mcp_mod

        ctx = _make_ctx()
        mock_result = {"content": "x" * 500, "status": 200}

        with patch("thegent.skills.research.scrape_url", new_callable=AsyncMock, return_value=mock_result):
            await _mcp_mod.thegent_scrape_url(
                url="https://example.com",
                use_playwright=True,
                ctx=ctx,
            )
        # info called at start (with url) and after (with content_len and elapsed)
        assert ctx.info.call_count >= 2
        second_call_args = str(ctx.info.call_args_list[1])
        assert "content_len" in second_call_args

    @pytest.mark.asyncio
    async def test_progress_values_are_sequential(self) -> None:
        """Progress values are 0, 1, 2, 3 in non-decreasing order."""
        # @trace FR-MCP-CTX-005
        import thegent.mcp_server as _mcp_mod

        ctx = _make_ctx()
        progress_calls: list[tuple[int, int]] = []

        async def capture_progress(progress: int, total: int) -> None:
            progress_calls.append((progress, total))

        ctx.report_progress = AsyncMock(side_effect=capture_progress)
        mock_result = {"content": "data"}

        with patch("thegent.skills.research.scrape_url", new_callable=AsyncMock, return_value=mock_result):
            await _mcp_mod.thegent_scrape_url(url="http://x.com", ctx=ctx)

        assert len(progress_calls) >= 3
        # All totals should be 3
        assert all(t == 3 for _, t in progress_calls)
        # Progress values should be non-decreasing
        progresses = [p for p, _ in progress_calls]
        assert progresses == sorted(progresses), "Progress values must be non-decreasing"
        assert progresses[-1] == 3, "Final progress must be 3/3"


@pytest.mark.unit
class TestDagRunContextApi:
    """Context API tests for thegent_dag_run in mcp_tools_modes. @trace FR-MCP-CTX-006"""

    @pytest.mark.asyncio
    async def test_ctx_info_and_progress_called(self) -> None:
        """ctx.info() is called with params and after run; ctx.report_progress called."""
        # @trace FR-MCP-CTX-006
        from fastmcp import FastMCP
        from thegent.mcp_tools_modes import register_modes

        mcp = FastMCP("test")
        with patch("thegent.cli.commands.impl.dag_run_impl", return_value={"spawned": ["t1", "t2"], "skipped": []}):
            register_modes(mcp)
            tool_fn = await _get_tool_fn(mcp, "thegent_dag_run")

            ctx = _make_ctx()
            result = await tool_fn(dry_run=False, task=None, ctx=ctx)
            data = _json_content(result)
            assert "spawned" in data
            # info called at start (with params) and after (spawned count)
            assert ctx.info.call_count >= 2
            # progress called at start (0/2) and end (2/2)
            assert ctx.report_progress.call_count >= 2

    @pytest.mark.asyncio
    async def test_ctx_none_does_not_raise(self) -> None:
        """Passing ctx=None to thegent_dag_run does not raise."""
        # @trace FR-MCP-CTX-006
        from fastmcp import FastMCP
        from thegent.mcp_tools_modes import register_modes

        mcp = FastMCP("test")
        with patch("thegent.cli.commands.impl.dag_run_impl", return_value={"spawned": [], "skipped": []}):
            register_modes(mcp)
            tool_fn = await _get_tool_fn(mcp, "thegent_dag_run")

            # Should not raise even with ctx=None
            result = await tool_fn(ctx=None)
            data = _json_content(result)
            assert "spawned" in data


# ---------------------------------------------------------------------------
# Context helper function tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCtxHelpers:
    """Tests for the _ctx_info / _ctx_warning helper functions."""

    @pytest.mark.asyncio
    async def test_ctx_info_with_valid_ctx(self) -> None:
        """_ctx_info calls ctx.info() when ctx is available."""
        from thegent.mcp_tools_seeds import _ctx_info

        ctx = _make_ctx()
        await _ctx_info(ctx, "test message")
        ctx.info.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_ctx_info_with_none_ctx(self) -> None:
        """_ctx_info falls back to Python logging when ctx is None."""
        from thegent.mcp_tools_seeds import _ctx_info

        with patch("thegent.mcp.tools.seeds._log") as mock_log:
            await _ctx_info(None, "fallback message")
            mock_log.info.assert_called_once_with("fallback message")

    @pytest.mark.asyncio
    async def test_ctx_warning_with_valid_ctx(self) -> None:
        """_ctx_warning calls ctx.warning() when ctx is available."""
        from thegent.mcp_tools_seeds import _ctx_warning

        ctx = _make_ctx()
        await _ctx_warning(ctx, "warn message")
        ctx.warning.assert_called_once_with("warn message")

    @pytest.mark.asyncio
    async def test_ctx_warning_falls_back_when_ctx_raises(self) -> None:
        """_ctx_warning falls back to Python logging when ctx.warning() raises."""
        from thegent.mcp_tools_seeds import _ctx_warning

        ctx = AsyncMock()
        ctx.warning = AsyncMock(side_effect=RuntimeError("ctx unavailable"))

        with patch("thegent.mcp.tools.seeds._log") as mock_log:
            await _ctx_warning(ctx, "warn message")
            mock_log.warning.assert_called_once_with("warn message")

    @pytest.mark.asyncio
    async def test_modes_ctx_info_with_valid_ctx(self) -> None:
        """_ctx_info in mcp_tools_modes calls ctx.info() when ctx is available."""
        from thegent.mcp_tools_modes import _ctx_info

        ctx = _make_ctx()
        await _ctx_info(ctx, "modes info message")
        ctx.info.assert_called_once_with("modes info message")

    @pytest.mark.asyncio
    async def test_modes_ctx_warning_with_none(self) -> None:
        """_ctx_warning in mcp_tools_modes falls back to Python logging when ctx is None."""
        from thegent.mcp_tools_modes import _ctx_warning

        with patch("thegent.mcp.tools.seeds._log") as mock_log:
            await _ctx_warning(None, "modes warn message")
            mock_log.warning.assert_called_once_with("modes warn message")
