"""Unit tests for MCP server tools and resources.

Tests cover all @mcp.tool() and @mcp.resource() functions defined in
thegent.mcp.server, mocking the underlying *_impl functions from cli_impl.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import orjson as json
import pytest

fastmcp = pytest.importorskip("fastmcp", reason="fastmcp required for MCP server tests")


import thegent.mcp.server as _mcp_mod

if TYPE_CHECKING:
    from fastmcp.tools.tool import ToolResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_content(result: ToolResult | str) -> Any:
    """Extract JSON from a ToolResult.content (handles list[TextContent] or str)."""
    if isinstance(result, str):
        return json.loads(result)
    content = result.content
    if isinstance(content, str):
        return json.loads(content)
    # fastmcp may wrap content in a list of TextContent objects
    if isinstance(content, list) and len(content) > 0:
        text = getattr(content[0], "text", str(content[0]))
        return json.loads(text)
    return json.loads(str(content))


def _inject_missing_names() -> None:
    """Inject _resolve_cwd, _default_owner_tag, and elicitation types into thegent.mcp.server.

    These names are used in the module's tool functions but are not imported at
    the module level. We inject stubs so that ``@patch(..., create=True)`` is
    not needed and patching targets are available.
    """
    from thegent.cli.commands.impl import _default_owner_tag, _resolve_cwd

    if not hasattr(_mcp_mod, "_resolve_cwd"):
        _mcp_mod._resolve_cwd = _resolve_cwd  # type: ignore[attr-defined]
    if not hasattr(_mcp_mod, "_default_owner_tag"):
        _mcp_mod._default_owner_tag = _default_owner_tag  # type: ignore[attr-defined]
    # Inject elicitation sentinel types used in isinstance checks
    try:
        from fastmcp.server.context import (
            AcceptedElicitation,
            CancelledElicitation,
            DeclinedElicitation,
        )

        for name, cls in [
            ("AcceptedElicitation", AcceptedElicitation),
            ("DeclinedElicitation", DeclinedElicitation),
            ("CancelledElicitation", CancelledElicitation),
        ]:
            if not hasattr(_mcp_mod, name):
                setattr(_mcp_mod, name, cls)
    except ImportError:
        pass
    # ThegentSettings is imported inline; inject so patch targets resolve
    try:
        from thegent.config import ThegentSettings

        if not hasattr(_mcp_mod, "ThegentSettings"):
            _mcp_mod.ThegentSettings = ThegentSettings  # type: ignore[attr-defined]
    except ImportError:
        pass


_inject_missing_names()


# ===================================================================
# MCP TOOLS
# ===================================================================


@pytest.mark.unit
class TestThegentRun:
    """Tests for the thegent_run MCP tool."""

    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl")
    async def test_run_basic_with_agent(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        # @trace FR-MCP-001
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "done",
            "stderr": "",
            "timed_out": False,
        }
        from thegent.mcp.server import thegent_run

        ctx = AsyncMock()
        ctx.info = AsyncMock()
        ctx.report_progress = AsyncMock()
        ctx.close_sse_stream = AsyncMock()
        result = await thegent_run(
            prompt="hello world",
            agent="claude",
            cd="/tmp/test",
            ctx=ctx,
            default_cwd=Path("/tmp/test"),
        )
        data = _json_content(result)
        assert data["exit_code"] == 0
        assert data["stdout"] == "done"
        mock_run_impl.assert_called_once()

    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl")
    async def test_run_with_model_and_agent(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        # @trace FR-MCP-002
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "model-run",
            "stderr": "",
            "timed_out": False,
        }
        from thegent.mcp.server import thegent_run

        ctx = AsyncMock()
        ctx.info = AsyncMock()
        ctx.report_progress = AsyncMock()
        ctx.close_sse_stream = AsyncMock()
        with patch("thegent.config.ThegentSettings") as mock_settings:
            mock_settings.return_value.default_routing = "prefer_direct"
            with patch(
                "thegent.models.resolve_route",
                return_value=("claude", "claude-sonnet-4"),
            ):
                result = await thegent_run(
                    prompt="test model routing",
                    agent="claude",
                    model="claude-sonnet-4",
                    cd="/tmp/test",
                    ctx=ctx,
                    default_cwd=Path("/tmp/test"),
                )
        data = _json_content(result)
        assert data["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_run_no_agent_no_model_returns_error(self) -> None:
        # @trace FR-MCP-003
        from thegent.mcp.server import thegent_run

        ctx = AsyncMock()
        ctx.info = AsyncMock()
        result = await thegent_run(
            prompt="no agent given",
            agent=None,
            model=None,
            ctx=ctx,
            default_cwd=Path("/tmp/test"),
        )
        data = _json_content(result)
        assert data["exit_code"] == 1
        assert "error" in data

    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl", side_effect=RuntimeError("agent crash"))
    async def test_run_impl_exception_propagates(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        # @trace FR-MCP-004
        from thegent.mcp.server import thegent_run

        ctx = AsyncMock()
        ctx.info = AsyncMock()
        ctx.report_progress = AsyncMock()
        ctx.close_sse_stream = AsyncMock()
        with pytest.raises(RuntimeError, match="agent crash"):
            await thegent_run(
                prompt="crash test",
                agent="claude",
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )

    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl")
    async def test_run_with_timeout_and_mode(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        # @trace FR-MCP-005
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "timed_out": False,
        }
        from thegent.mcp.server import thegent_run

        ctx = AsyncMock()
        ctx.info = AsyncMock()
        ctx.report_progress = AsyncMock()
        ctx.close_sse_stream = AsyncMock()
        result = await thegent_run(
            prompt="custom timeout",
            agent="gemini",
            mode="full",
            timeout=300,
            cd="/tmp/test",
            ctx=ctx,
            default_cwd=Path("/tmp/test"),
        )
        data = _json_content(result)
        assert data["exit_code"] == 0
        call_args = mock_run_impl.call_args
        assert call_args.kwargs.get("mode") == "full"  # mode kwarg
        assert call_args.kwargs.get("timeout") == 300  # timeout kwarg


@pytest.mark.unit
class TestThegentBg:
    """Tests for the thegent_bg MCP tool."""

    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server._default_owner_tag", return_value="test-owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_basic(self, mock_bg_impl: MagicMock, mock_owner: MagicMock, mock_cwd: MagicMock) -> None:
        # @trace FR-MCP-006
        mock_bg_impl.return_value = {
            "session_id": "abc-123",
            "log_path": "/tmp/log",
            "owner": "test-owner",
        }
        from thegent.mcp.server import thegent_bg

        ctx = AsyncMock()
        ctx.info = AsyncMock()
        result = await thegent_bg(
            agent="claude",
            prompt="background task",
            cd="/tmp/test",
            ctx=ctx,
            default_cwd=Path("/tmp/test"),
            default_owner=None,
        )
        data = _json_content(result)
        assert data["session_id"] == "abc-123"
        mock_bg_impl.assert_called_once()

    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server._default_owner_tag", return_value="fallback-owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_with_explicit_owner(
        self, mock_bg_impl: MagicMock, mock_owner: MagicMock, mock_cwd: MagicMock
    ) -> None:
        # @trace FR-MCP-007
        mock_bg_impl.return_value = {
            "session_id": "def-456",
            "log_path": "/tmp/log",
            "owner": "my-owner",
        }
        from thegent.mcp.server import thegent_bg

        ctx = AsyncMock()
        ctx.info = AsyncMock()
        result = await thegent_bg(
            agent="cursor",
            prompt="owned task",
            owner="my-owner",
            cd="/tmp/test",
            ctx=ctx,
            default_cwd=Path("/tmp/test"),
            default_owner=None,
        )
        data = _json_content(result)
        assert data["owner"] == "my-owner"

    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server._default_owner_tag", return_value="auto-owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_with_model_and_include_contract(
        self, mock_bg_impl: MagicMock, mock_owner: MagicMock, mock_cwd: MagicMock
    ) -> None:
        # @trace FR-MCP-008
        mock_bg_impl.return_value = {
            "session_id": "ghi-789",
            "log_path": "/tmp/log",
            "owner": "auto-owner",
        }
        from thegent.mcp.server import thegent_bg

        ctx = AsyncMock()
        ctx.info = AsyncMock()
        with patch("thegent.models.resolve_route_contract", return_value=None):
            with patch("thegent.models.route_contract", return_value={}):
                result = await thegent_bg(
                    agent="claude",
                    prompt="contract task",
                    model="claude-sonnet-4",
                    include_contract=True,
                    cd="/tmp/test",
                    ctx=ctx,
                    default_cwd=Path("/tmp/test"),
                    default_owner=None,
                )
        data = _json_content(result)
        assert "routing" in data


@pytest.mark.unit
class TestThegentStatus:
    """Tests for the thegent_status MCP tool."""

    @patch("thegent.mcp.server.status_impl")
    def test_status_returns_session_info(self, mock_status: MagicMock) -> None:
        # @trace FR-MCP-009
        mock_status.return_value = {
            "session_id": "s1",
            "status": "running",
            "pid": 1234,
        }
        from thegent.mcp.server import thegent_status

        result = thegent_status(session_id="s1")
        data = _json_content(result)
        assert data["session_id"] == "s1"
        assert data["status"] == "running"
        mock_status.assert_called_once_with(session_id="s1", include_contract=False)

    @patch("thegent.mcp.server.status_impl")
    def test_status_with_include_contract(self, mock_status: MagicMock) -> None:
        # @trace FR-MCP-010
        mock_status.return_value = {
            "session_id": "s2",
            "status": "done",
            "contract": {"model": "x"},
        }
        from thegent.mcp.server import thegent_status

        result = thegent_status(session_id="s2", include_contract=True)
        data = _json_content(result)
        assert data["session_id"] == "s2"
        mock_status.assert_called_once_with(session_id="s2", include_contract=True)

    @patch("thegent.mcp.server.status_impl")
    def test_status_nonexistent_session(self, mock_status: MagicMock) -> None:
        # @trace FR-MCP-011
        mock_status.return_value = {"error": "Session not found"}
        from thegent.mcp.server import thegent_status

        result = thegent_status(session_id="nonexistent")
        data = _json_content(result)
        assert "error" in data


@pytest.mark.unit
class TestThegentStop:
    """Tests for the thegent_stop MCP tool."""

    @patch("thegent.mcp.server.stop_impl")
    def test_stop_session(self, mock_stop: MagicMock) -> None:
        # @trace FR-MCP-012
        mock_stop.return_value = {"session_id": "s1", "status": "stopped"}
        from thegent.mcp.server import thegent_stop

        result = thegent_stop(session_id="s1")
        data = _json_content(result)
        assert data["status"] == "stopped"
        mock_stop.assert_called_once_with(session_id="s1", force=False)

    @patch("thegent.mcp.server.stop_impl")
    def test_stop_session_force(self, mock_stop: MagicMock) -> None:
        # @trace FR-MCP-013
        mock_stop.return_value = {"session_id": "s1", "status": "killed"}
        from thegent.mcp.server import thegent_stop

        result = thegent_stop(session_id="s1", force=True)
        data = _json_content(result)
        assert data["status"] == "killed"
        mock_stop.assert_called_once_with(session_id="s1", force=True)

    @patch("thegent.mcp.server.stop_impl")
    def test_stop_returns_error_for_unknown(self, mock_stop: MagicMock) -> None:
        # @trace FR-MCP-014
        mock_stop.return_value = {"error": "No such session"}
        from thegent.mcp.server import thegent_stop

        result = thegent_stop(session_id="missing")
        data = _json_content(result)
        assert "error" in data


@pytest.mark.unit
class TestThegentPs:
    """Tests for the thegent_ps MCP tool."""

    @patch("thegent.mcp.server.ps_impl")
    def test_ps_lists_sessions(self, mock_ps: MagicMock) -> None:
        # @trace FR-MCP-015
        mock_ps.return_value = [{"session_id": "s1", "status": "running"}]
        from thegent.mcp.server import thegent_ps

        result = thegent_ps()
        data = _json_content(result)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["session_id"] == "s1"

    @patch("thegent.mcp.server.ps_impl")
    def test_ps_with_owner_filter(self, mock_ps: MagicMock) -> None:
        # @trace FR-MCP-016
        mock_ps.return_value = [{"session_id": "s2", "owner": "alice"}]
        from thegent.mcp.server import thegent_ps

        thegent_ps(owner="alice")
        mock_ps.assert_called_once_with(owner="alice", all=False, include_contract=False)

    @patch("thegent.mcp.server.ps_impl")
    def test_ps_all_sessions(self, mock_ps: MagicMock) -> None:
        # @trace FR-MCP-017
        mock_ps.return_value = [
            {"session_id": "s1", "status": "done"},
            {"session_id": "s2", "status": "running"},
        ]
        from thegent.mcp.server import thegent_ps

        result = thegent_ps(all=True)
        data = _json_content(result)
        assert len(data) == 2
        mock_ps.assert_called_once_with(owner=None, all=True, include_contract=False)


@pytest.mark.unit
class TestThegentInspect:
    """Tests for the thegent_inspect MCP tool."""

    @patch("thegent.mcp.server.inspect_impl")
    def test_inspect_single_session(self, mock_inspect: MagicMock) -> None:
        # @trace FR-MCP-018
        mock_inspect.return_value = {"sessions": [{"session_id": "s1", "status": "running", "logs": "log data"}]}
        from thegent.mcp.server import thegent_inspect

        result = thegent_inspect(session_ids=["s1"])
        data = _json_content(result)
        assert data["sessions"][0]["session_id"] == "s1"
        mock_inspect.assert_called_once_with(
            session_ids=["s1"],
            owner=None,
            tail=50,
            stderr=False,
            include_contract=False,
        )

    @patch("thegent.mcp.server.inspect_impl")
    def test_inspect_by_owner(self, mock_inspect: MagicMock) -> None:
        # @trace FR-MCP-019
        mock_inspect.return_value = {
            "sessions": [
                {"session_id": "s1", "status": "done"},
                {"session_id": "s2", "status": "running"},
            ]
        }
        from thegent.mcp.server import thegent_inspect

        result = thegent_inspect(owner="bob", tail=100)
        data = _json_content(result)
        assert len(data["sessions"]) == 2
        mock_inspect.assert_called_once_with(
            session_ids=[], owner="bob", tail=100, stderr=False, include_contract=False
        )

    @patch("thegent.mcp.server.inspect_impl")
    def test_inspect_with_stderr(self, mock_inspect: MagicMock) -> None:
        # @trace FR-MCP-020
        mock_inspect.return_value = {"sessions": [{"session_id": "s1", "stderr_logs": "err"}]}
        from thegent.mcp.server import thegent_inspect

        thegent_inspect(session_ids=["s1"], stderr=True)
        mock_inspect.assert_called_once_with(
            session_ids=["s1"], owner=None, tail=50, stderr=True, include_contract=False
        )


@pytest.mark.unit
class TestThegentLogs:
    """Tests for the thegent_logs MCP tool."""

    @patch("thegent.mcp.server.logs_impl")
    def test_logs_basic(self, mock_logs: MagicMock) -> None:
        # @trace FR-MCP-021
        mock_logs.return_value = "line 1\nline 2\nline 3"
        from thegent.mcp.server import thegent_logs

        result = thegent_logs(session_id="s1")
        content = result.content
        if isinstance(content, list):
            content = getattr(content[0], "text", str(content[0]))
        assert "line 1" in content
        mock_logs.assert_called_once_with(session_id="s1", tail=None, stderr=False)

    @patch("thegent.mcp.server.logs_impl")
    def test_logs_with_tail(self, mock_logs: MagicMock) -> None:
        # @trace FR-MCP-022
        mock_logs.return_value = "last line"
        from thegent.mcp.server import thegent_logs

        thegent_logs(session_id="s1", tail=10)
        mock_logs.assert_called_once_with(session_id="s1", tail=10, stderr=False)

    @patch("thegent.mcp.server.logs_impl")
    def test_logs_stderr(self, mock_logs: MagicMock) -> None:
        # @trace FR-MCP-023
        mock_logs.return_value = "stderr output"
        from thegent.mcp.server import thegent_logs

        thegent_logs(session_id="s1", stderr=True)
        mock_logs.assert_called_once_with(session_id="s1", tail=None, stderr=True)


@pytest.mark.unit
class TestThegentWait:
    """Tests for the thegent_wait MCP tool."""

    @patch("thegent.mcp.server.wait_impl")
    def test_wait_completes(self, mock_wait: MagicMock) -> None:
        # @trace FR-MCP-024
        mock_wait.return_value = {"session_id": "s1", "status": "done", "exit_code": 0}
        from thegent.mcp.server import thegent_wait

        result = thegent_wait(session_id="s1")
        data = _json_content(result)
        assert data["status"] == "done"
        assert data["exit_code"] == 0

    @patch("thegent.mcp.server.wait_impl")
    def test_wait_with_timeout(self, mock_wait: MagicMock) -> None:
        # @trace FR-MCP-025
        mock_wait.return_value = {"session_id": "s1", "status": "timed_out"}
        from thegent.mcp.server import thegent_wait

        result = thegent_wait(session_id="s1", timeout=60)
        mock_wait.assert_called_once_with(session_id="s1", timeout=60)
        data = _json_content(result)
        assert data["status"] == "timed_out"


@pytest.mark.unit
class TestThegentDagList:
    """Tests for the thegent_dag_list MCP tool."""

    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/project"))
    @patch("thegent.mcp.server.dag_list_impl")
    async def test_dag_list_basic(self, mock_dag_list: MagicMock, mock_cwd: MagicMock) -> None:
        # @trace FR-MCP-026
        mock_dag_list.return_value = {
            "frontmatter": {"project": "test"},
            "tasks": [
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "do stuff",
                    "status": "pending",
                }
            ],
        }
        from thegent.mcp.server import thegent_dag_list

        ctx = AsyncMock()
        ctx.elicit = AsyncMock()
        result = await thegent_dag_list(cd="/tmp/project", ctx=ctx, default_cwd=Path("/tmp/project"))
        data = _json_content(result)
        assert "tasks" in data
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "T1"

    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/project"))
    @patch("thegent.mcp.server.dag_list_impl")
    async def test_dag_list_empty(self, mock_dag_list: MagicMock, mock_cwd: MagicMock) -> None:
        # @trace FR-MCP-027
        mock_dag_list.return_value = {"frontmatter": {}, "tasks": []}
        from thegent.mcp.server import thegent_dag_list

        ctx = AsyncMock()
        result = await thegent_dag_list(cd="/tmp/project", ctx=ctx, default_cwd=Path("/tmp/project"))
        data = _json_content(result)
        assert data["tasks"] == []


@pytest.mark.unit
class TestThegentSuggestPrompt:
    """Tests for the thegent_suggest_prompt MCP tool."""

    @pytest.mark.asyncio
    async def test_suggest_prompt_with_sampling(self) -> None:
        # @trace FR-MCP-028
        from thegent.mcp.server import thegent_suggest_prompt

        ctx = AsyncMock()
        sample_result = MagicMock()
        sample_result.text = "Refined: implement auth module with JWT"
        ctx.sample = AsyncMock(return_value=sample_result)
        result = await thegent_suggest_prompt(raw_prompt="add auth", ctx=ctx)
        data = _json_content(result)
        assert data["suggested_prompt"] == "Refined: implement auth module with JWT"
        assert data["sampling_used"] is True

    @pytest.mark.asyncio
    async def test_suggest_prompt_sampling_unavailable(self) -> None:
        # @trace FR-MCP-029
        from thegent.mcp.server import thegent_suggest_prompt

        ctx = AsyncMock()
        ctx.sample = AsyncMock(side_effect=RuntimeError("no sampling support"))
        result = await thegent_suggest_prompt(raw_prompt="add auth", ctx=ctx)
        data = _json_content(result)
        assert data["suggested_prompt"] == "add auth"
        assert data["sampling_used"] is False


@pytest.mark.unit
class TestThegentCreateWbs:
    """Tests for the thegent_create_wbs MCP prompt."""

    def test_create_wbs_basic(self) -> None:
        # @trace FR-MCP-030
        from thegent.mcp.server import thegent_create_wbs

        result = thegent_create_wbs(feature="user authentication")
        assert "WBS" in result
        assert "user authentication" in result

    def test_create_wbs_with_scope(self) -> None:
        # @trace FR-MCP-031
        from thegent.mcp.server import thegent_create_wbs

        result = thegent_create_wbs(feature="payment gateway", scope="backend only")
        assert "payment gateway" in result
        assert "backend only" in result


# ===================================================================
# MCP RESOURCES
# ===================================================================


@pytest.mark.unit
class TestResourceSessions:
    """Tests for the resource_sessions MCP resource."""

    @patch("thegent.mcp.server.ps_impl")
    def test_resource_sessions_returns_json(self, mock_ps: MagicMock) -> None:
        # @trace FR-MCP-032
        mock_ps.return_value = [{"session_id": "s1", "status": "running"}]
        from thegent.mcp.server import resource_sessions

        raw = resource_sessions()
        data = json.loads(raw)
        assert isinstance(data, list)
        assert data[0]["session_id"] == "s1"
        mock_ps.assert_called_once_with(owner=None, all=True, include_contract=False)

    @patch("thegent.mcp.server.ps_impl")
    def test_resource_sessions_with_contract(self, mock_ps: MagicMock) -> None:
        # @trace FR-MCP-033
        mock_ps.return_value = [{"session_id": "s1", "contract": {"model": "x"}}]
        from thegent.mcp.server import resource_sessions

        raw = resource_sessions(include_contract=True)
        data = json.loads(raw)
        assert "contract" in data[0]
        mock_ps.assert_called_once_with(owner=None, all=True, include_contract=True)


@pytest.mark.unit
class TestResourceDag:
    """Tests for the resource_dag MCP resource."""

    @patch("thegent.mcp.server.dag_list_impl")
    def test_resource_dag_returns_json(self, mock_dag: MagicMock) -> None:
        # @trace FR-MCP-034
        mock_dag.return_value = {"frontmatter": {"project": "x"}, "tasks": []}
        from thegent.mcp.server import resource_dag

        raw = resource_dag()
        data = json.loads(raw)
        assert "frontmatter" in data
        assert "tasks" in data
        mock_dag.assert_called_once_with(cd=None)


@pytest.mark.unit
class TestResourceModels:
    """Tests for the resource_models MCP resource."""

    @patch("thegent.mcp.server.list_models_impl")
    def test_resource_models_all(self, mock_models: MagicMock) -> None:
        # @trace FR-MCP-035
        mock_models.return_value = {"claude": ["sonnet", "opus"], "gemini": ["flash"]}
        from thegent.mcp.server import resource_models

        raw = resource_models()
        data = json.loads(raw)
        assert "claude" in data
        assert "gemini" in data
        mock_models.assert_called_once_with(provider=None, include_contract=False)

    @patch("thegent.mcp.server.list_models_impl")
    def test_resource_models_filtered(self, mock_models: MagicMock) -> None:
        # @trace FR-MCP-036
        mock_models.return_value = {"gemini": ["flash", "pro"]}
        from thegent.mcp.server import resource_models

        raw = resource_models(provider="gemini")
        data = json.loads(raw)
        assert "gemini" in data
        mock_models.assert_called_once_with(provider="gemini", include_contract=False)


@pytest.mark.unit
class TestResourceSessionContractHealthReport:
    """Tests for the resource_session_contract_health_report MCP resource."""

    @patch("thegent.mcp.server.session_contract_health_report_impl")
    def test_health_report_resource(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-037
        mock_impl.return_value = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_report",
            "status": "healthy",
            "total": 5,
            "healthy_count": 5,
            "unhealthy_count": 0,
        }
        from thegent.mcp.server import resource_session_contract_health_report

        raw = resource_session_contract_health_report()
        data = json.loads(raw)
        assert data["status"] == "healthy"
        assert data["schema_version"] == "health-schema-v1"
        mock_impl.assert_called_once()

    @patch("thegent.mcp.server.session_contract_health_report_impl")
    def test_health_report_resource_with_params(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-038
        mock_impl.return_value = {"status": "degraded", "total": 3}
        from thegent.mcp.server import resource_session_contract_health_report

        resource_session_contract_health_report(owner="alice", strict=True, top_blocked=10)
        mock_impl.assert_called_once_with(
            owner="alice",
            all=False,
            strict=True,
            top_blocked=10,
            policy_profile=None,
            no_worse_than_baseline=False,
            regression_tolerance=0.0,
        )


@pytest.mark.unit
class TestResourceSessionContractHealthGate:
    """Tests for the resource_session_contract_health_gate MCP resource."""

    @patch("thegent.mcp.server.session_contract_health_gate_impl")
    def test_health_gate_resource(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-039
        mock_impl.return_value = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_gate",
            "pass": True,
            "status": "pass",
            "total": 10,
            "healthy_count": 10,
        }
        from thegent.mcp.server import resource_session_contract_health_gate

        raw = resource_session_contract_health_gate()
        data = json.loads(raw)
        assert data["pass"] is True
        assert data["status"] == "pass"

    @patch("thegent.mcp.server.session_contract_health_gate_impl")
    def test_health_gate_resource_with_policy(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-040
        mock_impl.return_value = {"pass": False, "status": "fail"}
        from thegent.mcp.server import resource_session_contract_health_gate

        resource_session_contract_health_gate(policy_profile="strict_ci", min_healthy_ratio=0.95)
        mock_impl.assert_called_once_with(
            owner=None,
            all=False,
            strict=False,
            min_healthy_ratio=0.95,
            policy_profile="strict_ci",
            no_worse_than_baseline=False,
            regression_tolerance=0.0,
        )


@pytest.mark.unit
class TestResourceObserveSummary:
    """Tests for the resource_observe_summary MCP resource."""

    @patch("thegent.mcp.server.observe_summary_impl")
    def test_observe_summary_resource(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-041
        mock_impl.return_value = {
            "payload_type": "observe_summary",
            "status": "healthy",
            "kpis": {"total_events": 100},
            "drift": {"within_budget": True},
            "escalation": {"backlog_count": 0},
        }
        from thegent.mcp.server import resource_observe_summary

        raw = resource_observe_summary()
        data = json.loads(raw)
        assert data["status"] == "healthy"
        assert data["kpis"]["total_events"] == 100
        mock_impl.assert_called_once()

    @patch("thegent.mcp.server.observe_summary_impl")
    def test_observe_summary_resource_custom_params(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-042
        mock_impl.return_value = {
            "status": "degraded",
            "kpis": {},
            "drift": {},
            "escalation": {},
        }
        from thegent.mcp.server import resource_observe_summary

        resource_observe_summary(
            limit=50,
            drift_window=25,
            structural_budget_pct=3.0,
            semantic_budget_pct=7.0,
            provider="claude",
            trend_samples=5,
            top_escalations=20,
        )
        mock_impl.assert_called_once_with(
            limit=50,
            drift_window=25,
            structural_budget_pct=3.0,
            semantic_budget_pct=7.0,
            provider="claude",
            trend_samples=5,
            top_escalations=20,
        )


# ===================================================================
# MCP TOOL - Health Gate/Report/Trend Tools (sync wrappers)
# ===================================================================


@pytest.mark.unit
class TestThegentSessionContractHealthGateTool:
    """Tests for the thegent_session_contract_health_gate MCP tool."""

    @patch("thegent.mcp.server.session_contract_health_gate_impl")
    def test_health_gate_tool_pass(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-043
        mock_impl.return_value = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_gate",
            "pass": True,
            "status": "pass",
            "total": 5,
            "healthy_count": 5,
            "unhealthy_count": 0,
            "blocked_count": 0,
        }
        from thegent.mcp.server import thegent_session_contract_health_gate

        result = thegent_session_contract_health_gate()
        data = _json_content(result)
        assert data["pass"] is True
        assert result.meta["status"] == "pass"

    @patch("thegent.mcp.server.session_contract_health_gate_impl")
    def test_health_gate_tool_fail(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-044
        mock_impl.return_value = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_gate",
            "pass": False,
            "status": "fail",
            "total": 10,
            "healthy_count": 7,
            "unhealthy_count": 3,
            "blocked_count": 3,
        }
        from thegent.mcp.server import thegent_session_contract_health_gate

        result = thegent_session_contract_health_gate()
        data = _json_content(result)
        assert data["pass"] is False
        assert result.meta["unhealthy_count"] == 3


@pytest.mark.unit
class TestThegentSessionContractHealthReportTool:
    """Tests for the thegent_session_contract_health_report MCP tool."""

    @patch("thegent.mcp.server.session_contract_health_report_impl")
    def test_health_report_tool(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-045
        mock_impl.return_value = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_report",
            "status": "healthy",
            "total": 8,
            "healthy_count": 8,
            "unhealthy_count": 0,
            "blocked_count": 0,
        }
        from thegent.mcp.server import thegent_session_contract_health_report

        result = thegent_session_contract_health_report()
        data = _json_content(result)
        assert data["status"] == "healthy"
        assert result.meta["total"] == 8

    # @trace FR-MCP-069
    @patch("thegent.mcp.server.session_contract_health_report_impl")
    def test_health_report_tool_meta_envelope(self, mock_impl: MagicMock) -> None:
        """Meta block contains all _contract_health_meta fields."""
        mock_impl.return_value = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_report",
            "status": "healthy",
            "total": 12,
            "healthy_count": 10,
            "unhealthy_count": 2,
            "blocked_count": 1,
            "policy_profile": "strict_ci",
            "decision_reasons": ["blocked"],
            "top_blocked_count": 5,
            "blocked_sessions_cap": 25,
        }
        from thegent.mcp.server import thegent_session_contract_health_report

        result = thegent_session_contract_health_report()
        meta = result.meta
        assert meta["status"] == "healthy"
        assert meta["total"] == 12
        assert meta["healthy_count"] == 10
        assert meta["unhealthy_count"] == 2
        assert meta["blocked_count"] == 1
        assert meta["policy_profile"] == "strict_ci"
        assert meta["decision_reasons"] == ["blocked"]
        assert meta["top_blocked_count"] == 5
        assert meta["blocked_sessions_cap"] == 25

    # @trace FR-MCP-070
    @patch("thegent.mcp.server.session_contract_health_report_impl")
    def test_health_report_tool_error_envelope(self, mock_impl: MagicMock) -> None:
        """MCPBudgetExceeded returns error _ToolResult."""
        from thegent.mcp.server.mcp_perf_gates import MCPBudgetExceeded

        mock_impl.side_effect = MCPBudgetExceeded("tool_invoke_ms", 120.0, 100.0)
        from thegent.mcp.server import thegent_session_contract_health_report

        result = thegent_session_contract_health_report()
        assert "MCP budget exceeded" in result.content
        assert result.structured_content == {}
        assert result.meta == {}

    # @trace FR-MCP-071
    @patch("thegent.mcp.server.session_contract_health_report_impl")
    def test_health_report_tool_param_passthrough(self, mock_impl: MagicMock) -> None:
        """All params pass through to impl correctly."""
        mock_impl.return_value = {
            "status": "healthy",
            "total": 3,
            "healthy_count": 3,
        }
        from thegent.mcp.server import thegent_session_contract_health_report

        thegent_session_contract_health_report(
            session_id="s-123",
            policy_profile="strict_ci",
            strict=True,
            min_healthy_ratio=0.95,
            owner="alice",
            all=True,
            top_blocked=15,
        )
        call_kwargs = mock_impl.call_args[1]
        assert call_kwargs["policy_profile"] == "strict_ci"
        assert call_kwargs["strict"] is True
        assert call_kwargs["min_healthy_ratio"] == 0.95
        assert call_kwargs["owner"] == "alice"
        assert call_kwargs["all"] is True
        assert call_kwargs["top_blocked"] == 15

    # @trace FR-MCP-072
    @patch("thegent.mcp.server.session_contract_health_report_impl")
    def test_health_report_tool_structured_content(self, mock_impl: MagicMock) -> None:
        """structured_content matches the raw impl payload."""
        raw_payload = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_report",
            "status": "healthy",
            "total": 5,
            "healthy_count": 5,
            "unhealthy_count": 0,
            "blocked_count": 0,
        }
        mock_impl.return_value = raw_payload
        from thegent.mcp.server import thegent_session_contract_health_report

        result = thegent_session_contract_health_report()
        assert result.structured_content == raw_payload


@pytest.mark.unit
class TestThegentObserveSummaryTool:
    """Tests for the thegent_observe_summary MCP tool."""

    @patch("thegent.mcp.server.observe_summary_impl")
    def test_observe_summary_tool(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-046
        mock_impl.return_value = {
            "payload_type": "observe_summary",
            "payload_schema_version": "observe-summary-schema-v1",
            "status": "healthy",
            "kpis": {
                "total_events": 200,
                "fallback_rate": 0.02,
                "structural_drift_pct": 1.0,
                "semantic_drift_pct": 2.0,
            },
            "drift": {
                "within_budget": True,
                "structural_rate_pct": 1.0,
                "semantic_rate_pct": 2.0,
                "structural_budget_pct": 5.0,
                "semantic_budget_pct": 10.0,
            },
            "escalation": {
                "backlog_count": 3,
                "past_sla_count": 1,
                "top_escalations_count": 2,
                "provider": None,
            },
            "alerts": [],
            "trend_summary": {"enabled": False},
            "generated_query": {"trend_samples": 0},
        }
        from thegent.mcp.server import thegent_observe_summary

        result = thegent_observe_summary()
        data = _json_content(result)
        assert data["status"] == "healthy"
        assert result.meta["kpi_total_events"] == 200
        assert result.meta["drift_within_budget"] is True
        assert result.meta["backlog_count"] == 3


@pytest.mark.unit
class TestThegentListAgentsTool:
    """Tests for the thegent_list_agents MCP tool."""

    @patch("thegent.mcp.server.list_agents_impl")
    def test_list_agents(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-047
        mock_impl.return_value = [
            {"name": "claude", "backend": "claude"},
            {"name": "cursor", "backend": "cursor"},
        ]
        from thegent.mcp.server import thegent_list_agents

        result = thegent_list_agents()
        data = _json_content(result)
        assert isinstance(data, list)
        assert len(data) == 2
        names = [a["name"] for a in data]
        assert "claude" in names


@pytest.mark.unit
class TestThegentListModelsTool:
    """Tests for the thegent_list_models MCP tool."""

    @patch("thegent.mcp.server.list_models_impl")
    def test_list_models_all(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-048
        mock_impl.return_value = {"claude": ["sonnet", "opus"], "gemini": ["flash"]}
        from thegent.mcp.server import thegent_list_models

        result = thegent_list_models()
        data = _json_content(result)
        assert "claude" in data
        mock_impl.assert_called_once_with(provider=None, include_contract=False, by_model=False)

    @patch("thegent.mcp.server.list_models_impl")
    def test_list_models_by_provider(self, mock_impl: MagicMock) -> None:
        # @trace FR-MCP-049
        mock_impl.return_value = {"gemini": ["flash", "pro"]}
        from thegent.mcp.server import thegent_list_models

        result = thegent_list_models(provider="gemini")
        data = _json_content(result)
        assert "gemini" in data
        mock_impl.assert_called_once_with(provider="gemini", include_contract=False, by_model=False)


@pytest.mark.unit
class TestStableJson:
    """Tests for the _stable_json helper used by MCP tools."""

    def test_stable_json_sorts_keys(self) -> None:
        # @trace FR-MCP-050
        from thegent.mcp.server import _stable_json

        result = _stable_json({"z": 1, "a": 2, "m": 3})
        parsed = json.loads(result)
        keys = list(parsed.keys())
        assert keys == ["a", "m", "z"]

    def test_stable_json_handles_nested(self) -> None:
        # @trace FR-MCP-050
        from thegent.mcp.server import _stable_json

        result = _stable_json({"b": {"z": 1, "a": 2}, "a": 1})
        parsed = json.loads(result)
        assert list(parsed.keys()) == ["a", "b"]
        assert list(parsed["b"].keys()) == ["a", "z"]
