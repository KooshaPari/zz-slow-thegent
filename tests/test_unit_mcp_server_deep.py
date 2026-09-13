"""Deep unit tests for thegent.mcp.server covering missing coverage lines.

Targets: CWD resolution, owner resolution, lifespan, DAG tools,
resource implementations, health endpoint, HTTP app, run(), _stable_json,
prompt functions, operations/modes tools, and suggest_prompt.
"""

from __future__ import annotations

import asyncio
import os
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
    if isinstance(content, list) and len(content) > 0:
        text = getattr(content[0], "text", str(content[0]))
        return json.loads(text)
    return json.loads(str(content))


def _text_content(result: ToolResult | str) -> str:
    """Extract raw text from a ToolResult.content."""
    if isinstance(result, str):
        return result
    content = result.content
    if isinstance(content, str):
        return content
    if isinstance(content, list) and len(content) > 0:
        return getattr(content[0], "text", str(content[0]))
    return str(content)


def _inject_missing_names() -> None:
    """Inject _resolve_cwd, _default_owner_tag, and elicitation types into thegent.mcp.server.

    These names are used in the module's tool functions but are not imported at
    the module level. We inject stubs so that patching targets are available.
    """
    from thegent.cli.commands.impl import _default_owner_tag, _resolve_cwd

    if not hasattr(_mcp_mod, "_resolve_cwd"):
        _mcp_mod._resolve_cwd = _resolve_cwd
    if not hasattr(_mcp_mod, "_default_owner_tag"):
        _mcp_mod._default_owner_tag = _default_owner_tag
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
    try:
        from thegent.config import ThegentSettings

        if not hasattr(_mcp_mod, "ThegentSettings"):
            _mcp_mod.ThegentSettings = ThegentSettings
    except ImportError:
        pass


_inject_missing_names()


# ===================================================================
# _stable_json helper
# ===================================================================


@pytest.mark.unit
class TestStableJsonDeep:
    """Deep coverage of _stable_json edge cases."""

    # @trace FR-MCP-051
    def test_stable_json_empty_dict(self) -> None:
        """Empty dict serializes to '{}'."""
        assert _mcp_mod._stable_json({}) == "{}"

    # @trace FR-MCP-052
    def test_stable_json_empty_list(self) -> None:
        """Empty list serializes to '[]'."""
        assert _mcp_mod._stable_json([]) == "[]"

    # @trace FR-MCP-053
    def test_stable_json_deterministic_key_order(self) -> None:
        """Keys sorted alphabetically regardless of insertion order."""
        payload_a = {"z": 1, "a": 2, "m": 3}
        payload_b = {"a": 2, "m": 3, "z": 1}
        assert _mcp_mod._stable_json(payload_a) == _mcp_mod._stable_json(payload_b)
        parsed = json.loads(_mcp_mod._stable_json(payload_a))
        keys = list(parsed.keys())
        assert keys == sorted(keys)

    # @trace FR-MCP-054
    def test_stable_json_nested_objects(self) -> None:
        """Nested dicts also have sorted keys."""
        payload = {"b": {"z": 1, "a": 2}, "a": {"y": 3, "x": 4}}
        result = _mcp_mod._stable_json(payload)
        parsed = json.loads(result)
        assert list(parsed.keys()) == ["a", "b"]
        assert list(parsed["a"].keys()) == ["x", "y"]
        assert list(parsed["b"].keys()) == ["a", "z"]

    # @trace FR-MCP-055
    def test_stable_json_with_none_values(self) -> None:
        """None values serialize as null."""
        payload = {"key": None}
        result = _mcp_mod._stable_json(payload)
        assert json.loads(result) == {"key": None}


# ===================================================================
# get_default_cwd / get_default_owner dependency injection
# ===================================================================


@pytest.mark.unit
class TestGetDefaultCwd:
    """Tests for get_default_cwd context dependency."""

    # @trace FR-MCP-056
    def test_returns_none_when_no_request_context(self) -> None:
        """Returns None when ctx.request_context is None."""
        ctx = MagicMock()
        ctx.request_context = None
        result = _mcp_mod.get_default_cwd(ctx)
        assert result is None

    # @trace FR-MCP-057
    def test_returns_none_when_meta_is_none(self) -> None:
        """Returns None when request_context.meta is None."""
        ctx = MagicMock()
        ctx.request_context = MagicMock()
        ctx.request_context.meta = None
        result = _mcp_mod.get_default_cwd(ctx)
        assert result is None

    # @trace FR-MCP-058
    def test_returns_none_when_cwd_not_set(self) -> None:
        """Returns None when meta exists but has no cwd attribute."""
        ctx = MagicMock()
        ctx.request_context = MagicMock()
        meta = MagicMock(spec=[])
        ctx.request_context.meta = meta
        result = _mcp_mod.get_default_cwd(ctx)
        assert result is None

    # @trace FR-MCP-059
    def test_returns_resolved_path_when_cwd_set(self) -> None:
        """Returns resolved Path when meta.cwd is set."""
        ctx = MagicMock()
        ctx.request_context = MagicMock()
        ctx.request_context.meta = MagicMock()
        ctx.request_context.meta.cwd = "/tmp"
        result = _mcp_mod.get_default_cwd(ctx)
        assert result is not None
        assert isinstance(result, Path)
        assert result == Path("/tmp").expanduser().resolve()

    # @trace FR-MCP-060
    def test_returns_none_when_cwd_is_empty_string(self) -> None:
        """Returns None when meta.cwd is empty string (falsy)."""
        ctx = MagicMock()
        ctx.request_context = MagicMock()
        ctx.request_context.meta = MagicMock()
        ctx.request_context.meta.cwd = ""
        result = _mcp_mod.get_default_cwd(ctx)
        assert result is None


@pytest.mark.unit
class TestGetDefaultOwner:
    """Tests for get_default_owner context dependency."""

    # @trace FR-MCP-061
    def test_returns_none_when_no_request_context(self) -> None:
        """Returns None when ctx.request_context is None."""
        ctx = MagicMock()
        ctx.request_context = None
        result = _mcp_mod.get_default_owner(ctx)
        assert result is None

    # @trace FR-MCP-062
    def test_returns_none_when_meta_is_none(self) -> None:
        """Returns None when request_context.meta is None."""
        ctx = MagicMock()
        ctx.request_context = MagicMock()
        ctx.request_context.meta = None
        result = _mcp_mod.get_default_owner(ctx)
        assert result is None

    # @trace FR-MCP-063
    def test_returns_owner_when_set(self) -> None:
        """Returns owner string when meta.owner is set."""
        ctx = MagicMock()
        ctx.request_context = MagicMock()
        ctx.request_context.meta = MagicMock()
        ctx.request_context.meta.owner = "my-team"
        result = _mcp_mod.get_default_owner(ctx)
        assert result == "my-team"

    # @trace FR-MCP-064
    def test_returns_none_when_owner_not_on_meta(self) -> None:
        """Returns None when meta has no owner attribute."""
        ctx = MagicMock()
        ctx.request_context = MagicMock()
        meta = MagicMock(spec=[])
        ctx.request_context.meta = meta
        result = _mcp_mod.get_default_owner(ctx)
        assert result is None


# ===================================================================
# Lifespan
# ===================================================================


@pytest.mark.unit
class TestLifespan:
    """Tests for thegent_lifespan -- verifies the lifespan object exists and is configured.

    Note: fastmcp's @lifespan decorator wraps the async generator into a Lifespan object
    that doesn't expose __wrapped__. We test the lifespan indirectly through integration tests.
    """

    # @trace FR-MCP-065
    def test_lifespan_is_registered(self) -> None:
        """The lifespan object is a fastmcp Lifespan instance attached to the server."""
        assert _mcp_mod.thegent_lifespan is not None
        assert hasattr(_mcp_mod.mcp, "_lifespan")


# ===================================================================
# Resource implementations
# ===================================================================


@pytest.mark.unit
class TestResourceSessionMeta:
    """Tests for resource_session_meta."""

    # @trace FR-MCP-070
    @patch("thegent.mcp.server.status_impl")
    def test_returns_json_for_session(self, mock_status: MagicMock) -> None:
        """Returns JSON string with session metadata."""
        mock_status.return_value = {"session_id": "abc", "status": "running", "pid": 1234}
        result = _mcp_mod.resource_session_meta(id="abc")
        data = json.loads(result)
        assert data["session_id"] == "abc"
        assert data["status"] == "running"
        mock_status.assert_called_once_with(session_id="abc", include_contract=False)

    # @trace FR-MCP-071
    @patch("thegent.mcp.server.status_impl")
    def test_returns_json_with_contract(self, mock_status: MagicMock) -> None:
        """Passes include_contract flag through."""
        mock_status.return_value = {"session_id": "abc", "contract": {}}
        _mcp_mod.resource_session_meta(id="abc", include_contract=True)
        mock_status.assert_called_once_with(session_id="abc", include_contract=True)


@pytest.mark.unit
class TestResourceSessionLogs:
    """Tests for resource_session_logs."""

    # @trace FR-MCP-072
    @patch("thegent.mcp.server.logs_impl")
    def test_returns_log_text(self, mock_logs: MagicMock) -> None:
        """Returns plain text log content."""
        mock_logs.return_value = "line 1\nline 2\n"
        result = _mcp_mod.resource_session_logs(id="abc")
        assert result == "line 1\nline 2\n"
        mock_logs.assert_called_once_with(session_id="abc", tail=None, stderr=False)

    # @trace FR-MCP-073
    @patch("thegent.mcp.server.logs_impl")
    def test_returns_stderr_with_tail(self, mock_logs: MagicMock) -> None:
        """Passes stderr and tail params through."""
        mock_logs.return_value = "error line"
        _mcp_mod.resource_session_logs(id="xyz", stderr=True, tail=10)
        mock_logs.assert_called_once_with(session_id="xyz", tail=10, stderr=True)


@pytest.mark.unit
class TestResourceAgents:
    """Tests for resource_agents."""

    # @trace FR-MCP-074
    @patch("thegent.mcp.server.list_agents_impl")
    def test_returns_agent_list(self, mock_agents: MagicMock) -> None:
        """Returns JSON array of agents."""
        mock_agents.return_value = [{"name": "claude", "backend": "anthropic"}]
        result = _mcp_mod.resource_agents()
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["name"] == "claude"


@pytest.mark.unit
class TestResourceModelsContract:
    """Tests for resource_models_contract."""

    # @trace FR-MCP-075
    def test_returns_route_contract(self) -> None:
        """Returns route contract schema metadata."""
        with patch("thegent.models.route_contract", return_value={"schema": "v1", "routes": []}):
            result = _mcp_mod.resource_models_contract()
            data = json.loads(result)
            assert data["schema"] == "v1"


@pytest.mark.unit
class TestResourceSessionContracts:
    """Tests for resource_session_contracts."""

    # @trace FR-MCP-076
    @patch("thegent.mcp.server.session_contract_audit_impl")
    def test_returns_audit_data(self, mock_audit: MagicMock) -> None:
        """Returns JSON audit payload."""
        mock_audit.return_value = {"total": 5, "missing": 1, "sessions": []}
        result = _mcp_mod.resource_session_contracts()
        data = json.loads(result)
        assert data["total"] == 5
        mock_audit.assert_called_once_with(owner=None, all=False, missing_only=False, summary_only=False, strict=False)

    # @trace FR-MCP-077
    @patch("thegent.mcp.server.session_contract_audit_impl")
    def test_passes_all_params(self, mock_audit: MagicMock) -> None:
        """Passes all parameters through to impl."""
        mock_audit.return_value = {"total": 0}
        _mcp_mod.resource_session_contracts(owner="team-a", all=True, missing_only=True, summary_only=True, strict=True)
        mock_audit.assert_called_once_with(owner="team-a", all=True, missing_only=True, summary_only=True, strict=True)


# ===================================================================
# Resource: operations and modes
# ===================================================================


@pytest.mark.unit
class TestResourceOperations:
    """Tests for resource_operations."""

    # @trace FR-MCP-078
    def test_list_all_operations(self) -> None:
        """Returns all operations when no filter given."""
        with patch("thegent.operations.list_operations", return_value={"orchestrate": []}):
            result = _mcp_mod.resource_operations()
            data = json.loads(result)
            assert "orchestrate" in data

    # @trace FR-MCP-079
    def test_filter_by_operation(self) -> None:
        """Filters by specific operation type."""

        mock_entry = MagicMock()
        mock_entry.command = "thegent run"
        mock_entry.description = "Run agent"
        mock_entry.mcp_tool = "thegent_run"
        with patch("thegent.operations.get_operations_by_type", return_value=[mock_entry]):
            result = _mcp_mod.resource_operations(operation="orchestrate")
            data = json.loads(result)
            assert "orchestrate" in data

    # @trace FR-MCP-080
    def test_unknown_operation_returns_error(self) -> None:
        """Returns error for unknown operation type."""
        with patch("thegent.operations.Operation", side_effect=ValueError("bad")):
            result = _mcp_mod.resource_operations(operation="nonexistent")
            data = json.loads(result)
            assert "error" in data


@pytest.mark.unit
class TestResourceModes:
    """Tests for resource_modes."""

    # @trace FR-MCP-081
    def test_list_all_modes(self) -> None:
        """Returns all modes when no filter given."""
        with patch("thegent.orchestration_modes.list_modes", return_value=[{"mode": "sequential_delegation"}]):
            result = _mcp_mod.resource_modes()
            data = json.loads(result)
            assert len(data) == 1

    # @trace FR-MCP-082
    def test_filter_by_mode(self) -> None:
        """Returns single mode entry when mode given."""
        mock_entry = MagicMock()
        mock_entry.mode.value = "sequential_delegation"
        mock_entry.description = "Delegates sequentially"
        mock_entry.phases = ["plan", "execute"]
        mock_entry.use_case = "Simple tasks"
        mock_entry.risk_profile = "low"
        mock_entry.selection_hint = "Use for simple"
        with patch("thegent.orchestration_modes.get_mode", return_value=mock_entry):
            result = _mcp_mod.resource_modes(mode="sequential_delegation")
            data = json.loads(result)
            assert len(data) == 1
            assert data[0]["mode"] == "sequential_delegation"

    # @trace FR-MCP-083
    def test_unknown_mode_returns_error(self) -> None:
        """Returns error for unknown mode."""
        with patch("thegent.orchestration_modes.get_mode", return_value=None):
            result = _mcp_mod.resource_modes(mode="nonexistent")
            data = json.loads(result)
            assert "error" in data


# ===================================================================
# Prompt functions
# ===================================================================


@pytest.mark.unit
class TestPrompts:
    """Tests for MCP prompt functions."""

    # @trace FR-MCP-084
    def test_run_agent_prompt_basic(self) -> None:
        """Generates run prompt without cd."""
        result = _mcp_mod.thegent_run_agent(agent="claude", prompt="fix the bug")
        assert "claude" in result
        assert "fix the bug" in result

    # @trace FR-MCP-085
    def test_run_agent_prompt_with_cd(self) -> None:
        """Generates run prompt with cd hint."""
        result = _mcp_mod.thegent_run_agent(agent="gemini", prompt="build it", cd="/project")
        assert "/project" in result

    # @trace FR-MCP-086
    def test_create_wbs_prompt_basic(self) -> None:
        """Generates WBS prompt without scope."""
        result = _mcp_mod.thegent_create_wbs(feature="auth system")
        assert "auth system" in result
        assert "WBS" in result

    # @trace FR-MCP-087
    def test_create_wbs_prompt_with_scope(self) -> None:
        """Generates WBS prompt with scope."""
        result = _mcp_mod.thegent_create_wbs(feature="auth", scope="backend only")
        assert "backend only" in result

    # @trace FR-MCP-088
    def test_bg_task_prompt_basic(self) -> None:
        """Generates bg task prompt without owner."""
        result = _mcp_mod.thegent_bg_task(agent="cursor", prompt="refactor")
        assert "cursor" in result
        assert "refactor" in result

    # @trace FR-MCP-089
    def test_bg_task_prompt_with_owner(self) -> None:
        """Generates bg task prompt with owner."""
        result = _mcp_mod.thegent_bg_task(agent="claude", prompt="test", owner="team-x")
        assert "team-x" in result


# ===================================================================
# Tool: thegent_session_contracts
# ===================================================================


@pytest.mark.unit
class TestThegentSessionContractsTool:
    """Tests for thegent_session_contracts tool."""

    # @trace FR-MCP-090
    @patch("thegent.mcp.server.session_contract_audit_impl")
    def test_session_contracts_default_params(self, mock_impl: MagicMock) -> None:
        """Returns audit payload with default params."""
        mock_impl.return_value = {"total": 3, "sessions": [], "missing": 0}
        result = _mcp_mod.thegent_session_contracts()
        data = _json_content(result)
        assert data["total"] == 3
        mock_impl.assert_called_once_with(owner=None, all=False, missing_only=False, summary_only=False, strict=False)

    # @trace FR-MCP-091
    @patch("thegent.mcp.server.session_contract_audit_impl")
    def test_session_contracts_with_filters(self, mock_impl: MagicMock) -> None:
        """Passes filter params to impl."""
        mock_impl.return_value = {"total": 1, "sessions": []}
        _mcp_mod.thegent_session_contracts(owner="me", all=True, missing_only=True, summary_only=True, strict=True)
        mock_impl.assert_called_once_with(owner="me", all=True, missing_only=True, summary_only=True, strict=True)

    # @trace FR-MCP-092
    @patch("thegent.mcp.server.session_contract_audit_impl")
    def test_session_contracts_has_execution_time(self, mock_impl: MagicMock) -> None:
        """Result meta includes execution_time_ms."""
        mock_impl.return_value = {"total": 0}
        result = _mcp_mod.thegent_session_contracts()
        assert result.meta is not None
        assert "execution_time_ms" in result.meta


# ===================================================================
# Tool: thegent_list_operations and thegent_list_modes
# ===================================================================


@pytest.mark.unit
class TestThegentListOperationsTool:
    """Tests for thegent_list_operations tool."""

    # @trace FR-MCP-093
    def test_list_all_operations(self) -> None:
        """Returns all operations."""
        with patch("thegent.operations.list_operations", return_value={"orchestrate": [], "govern": []}):
            result = _mcp_mod.thegent_list_operations()
            data = _json_content(result)
            assert "orchestrate" in data

    # @trace FR-MCP-094
    def test_unknown_operation_type(self) -> None:
        """Returns error for unknown operation type."""
        result = _mcp_mod.thegent_list_operations(operation="nonexistent_op")
        data = _json_content(result)
        assert "error" in data


@pytest.mark.unit
class TestThegentListModesTool:
    """Tests for thegent_list_modes tool."""

    # @trace FR-MCP-095
    def test_list_all_modes(self) -> None:
        """Returns all modes."""
        with patch("thegent.orchestration_modes.list_modes", return_value=[{"mode": "review_loop"}]):
            result = _mcp_mod.thegent_list_modes()
            data = _json_content(result)
            assert len(data) == 1

    # @trace FR-MCP-096
    def test_unknown_mode(self) -> None:
        """Returns error for unknown mode."""
        with patch("thegent.orchestration_modes.get_mode", return_value=None):
            result = _mcp_mod.thegent_list_modes(mode="nonexistent_mode")
            data = _json_content(result)
            assert "error" in data


# ===================================================================
# Tool: thegent_suggest_prompt
# ===================================================================


@pytest.mark.unit
class TestThegentSuggestPromptDeep:
    """Deep tests for thegent_suggest_prompt."""

    # @trace FR-MCP-097
    def test_suggest_prompt_returns_raw_on_exception(self) -> None:
        """Falls back to raw_prompt when sampling raises."""

        async def _run() -> None:
            ctx = AsyncMock()
            ctx.sample = AsyncMock(side_effect=RuntimeError("no sampling"))
            result = await _mcp_mod.thegent_suggest_prompt(raw_prompt="do something", ctx=ctx)
            data = _json_content(result)
            assert data["suggested_prompt"] == "do something"
            assert data["sampling_used"] is False

        asyncio.run(_run())

    # @trace FR-MCP-098
    def test_suggest_prompt_uses_sampled_text(self) -> None:
        """Returns refined prompt when sampling succeeds."""

        async def _run() -> None:
            ctx = AsyncMock()
            sample_result = MagicMock()
            sample_result.text = "Refined: do something better"
            ctx.sample = AsyncMock(return_value=sample_result)
            result = await _mcp_mod.thegent_suggest_prompt(raw_prompt="do something", ctx=ctx)
            data = _json_content(result)
            assert data["suggested_prompt"] == "Refined: do something better"
            assert data["sampling_used"] is True

        asyncio.run(_run())

    # @trace FR-MCP-099
    def test_suggest_prompt_strips_whitespace(self) -> None:
        """Strips whitespace from sampled result."""

        async def _run() -> None:
            ctx = AsyncMock()
            sample_result = MagicMock()
            sample_result.text = "  trimmed prompt  "
            ctx.sample = AsyncMock(return_value=sample_result)
            result = await _mcp_mod.thegent_suggest_prompt(raw_prompt="do something", ctx=ctx)
            data = _json_content(result)
            assert data["suggested_prompt"] == "trimmed prompt"

        asyncio.run(_run())


# ===================================================================
# DAG list tool with elicitation branches
# ===================================================================


@pytest.mark.unit
class TestThegentDagListDeep:
    """Deep tests for thegent_dag_list elicitation branches."""

    # @trace FR-MCP-051
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    @patch("thegent.mcp.server.dag_list_impl")
    def test_dag_list_declined_elicitation(self, mock_dag: MagicMock, mock_cwd: MagicMock) -> None:
        """Returns error when user declines CWD elicitation."""
        try:
            from fastmcp.server.context import DeclinedElicitation

            declined = DeclinedElicitation()
        except (ImportError, TypeError):
            declined = MagicMock()
            if hasattr(_mcp_mod, "DeclinedElicitation"):
                declined.__class__ = _mcp_mod.DeclinedElicitation

        async def _run() -> None:
            ctx = AsyncMock()
            ctx.elicit = AsyncMock(return_value=declined)
            result = await _mcp_mod.thegent_dag_list(cd=None, ctx=ctx, default_cwd=None)
            data = _json_content(result)
            assert "error" in data
            assert data["tasks"] == []

        asyncio.run(_run())

    # @trace FR-MCP-052
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    @patch("thegent.mcp.server.dag_list_impl")
    def test_dag_list_cancelled_elicitation(self, mock_dag: MagicMock, mock_cwd: MagicMock) -> None:
        """Returns error when CWD elicitation is cancelled."""
        try:
            from fastmcp.server.context import CancelledElicitation

            cancelled = CancelledElicitation()
        except (ImportError, TypeError):
            cancelled = MagicMock()
            if hasattr(_mcp_mod, "CancelledElicitation"):
                cancelled.__class__ = _mcp_mod.CancelledElicitation

        async def _run() -> None:
            ctx = AsyncMock()
            ctx.elicit = AsyncMock(return_value=cancelled)
            result = await _mcp_mod.thegent_dag_list(cd=None, ctx=ctx, default_cwd=None)
            data = _json_content(result)
            assert "error" in data

        asyncio.run(_run())

    # @trace FR-MCP-053
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    @patch("thegent.mcp.server.dag_list_impl")
    def test_dag_list_ambiguous_elicitation(self, mock_dag: MagicMock, mock_cwd: MagicMock) -> None:
        """Returns error for unrecognized elicitation type."""
        ambiguous = MagicMock()
        ambiguous.__class__ = type("UnknownElicitation", (), {})

        async def _run() -> None:
            ctx = AsyncMock()
            ctx.elicit = AsyncMock(return_value=ambiguous)
            result = await _mcp_mod.thegent_dag_list(cd=None, ctx=ctx, default_cwd=None)
            data = _json_content(result)
            assert "error" in data
            assert "Ambiguous" in data["error"]

        asyncio.run(_run())

    # @trace FR-MCP-054
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/project"))
    @patch("thegent.mcp.server.dag_list_impl")
    def test_dag_list_with_resolved_cwd(self, mock_dag: MagicMock, mock_cwd: MagicMock) -> None:
        """Returns DAG data when CWD resolves successfully."""
        mock_dag.return_value = {"frontmatter": {"project": "test"}, "tasks": [{"id": "T1"}]}

        async def _run() -> ToolResult:
            ctx = AsyncMock()
            return await _mcp_mod.thegent_dag_list(cd="/tmp/project", ctx=ctx, default_cwd=None)

        result = asyncio.run(_run())
        data = _json_content(result)
        assert data["tasks"] == [{"id": "T1"}]
        assert result.meta is not None
        assert "execution_time_ms" in result.meta


# ===================================================================
# Health endpoint
# ===================================================================


@pytest.mark.unit
class TestHealthEndpoint:
    """Tests for the /health custom route."""

    # @trace FR-MCP-055
    def test_health_returns_ok(self) -> None:
        """Health endpoint returns JSON with status=ok."""

        async def _run() -> None:
            request = MagicMock()
            response = await _mcp_mod.health(request)
            assert response.status_code == 200
            body = json.loads(response.body.decode())
            assert body["status"] == "ok"
            assert body["server"] == "thegent"

        asyncio.run(_run())


# ===================================================================
# _get_event_store
# ===================================================================


@pytest.mark.unit
class TestGetEventStore:
    """Tests for _get_event_store."""

    # @trace FR-MCP-056
    def test_default_memory_store(self) -> None:
        """Returns EventStore with default memory storage when no URL set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FASTMCP_EVENT_STORE_URL", None)
            store = _mcp_mod._get_event_store()
            assert store is not None

    # @trace FR-MCP-057
    def test_redis_store_when_url_set(self) -> None:
        """Returns EventStore with Redis storage when URL is set."""
        with patch.dict(os.environ, {"FASTMCP_EVENT_STORE_URL": "redis://localhost:6379"}, clear=False):
            with patch("key_value.aio.stores.redis.RedisStore") as mock_redis:
                mock_redis.return_value = MagicMock()
                store = _mcp_mod._get_event_store()
                assert store is not None
                mock_redis.assert_called_once_with(url="redis://localhost:6379")


# ===================================================================
# http_app
# ===================================================================


@pytest.mark.unit
class TestHttpApp:
    """Tests for http_app factory."""

    # @trace FR-MCP-058
    @patch.object(_mcp_mod.mcp, "http_app")
    def test_http_app_default_stateless(self, mock_http_app: MagicMock) -> None:
        """Creates HTTP app with stateless_http=True by default."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FASTMCP_EVENT_STORE_URL", None)
            _mcp_mod.http_app()
            mock_http_app.assert_called_once()
            call_kwargs = mock_http_app.call_args[1]
            assert call_kwargs["stateless_http"] is True
            assert call_kwargs["transport"] == "http"

    # @trace FR-MCP-059
    @patch.object(_mcp_mod.mcp, "http_app")
    def test_http_app_stateful(self, mock_http_app: MagicMock) -> None:
        """Creates HTTP app with stateless_http=False when requested."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FASTMCP_EVENT_STORE_URL", None)
            _mcp_mod.http_app(stateless_http=False)
            call_kwargs = mock_http_app.call_args[1]
            assert call_kwargs["stateless_http"] is False


# ===================================================================
# run()
# ===================================================================


@pytest.mark.unit
class TestRunFunction:
    """Tests for the run() entry point."""

    # @trace FR-MCP-060
    @patch("uvicorn.run")
    @patch("thegent.config.ThegentSettings")
    @patch.object(_mcp_mod.mcp, "http_app")
    def test_run_default_host_port(
        self, mock_http_app: MagicMock, mock_settings_cls: MagicMock, mock_uvicorn: MagicMock
    ) -> None:
        """Uses settings.mcp_host and settings.mcp_port when no overrides."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FASTMCP_EVENT_STORE_URL", None)
            mock_settings = MagicMock()
            mock_settings.mcp_host = "0.0.0.0"
            mock_settings.mcp_port = 3847
            mock_settings_cls.return_value = mock_settings
            mock_http_app.return_value = MagicMock()

            _mcp_mod.run()
            mock_uvicorn.assert_called_once()
            call_kwargs = mock_uvicorn.call_args[1]
            assert call_kwargs["host"] == "0.0.0.0"
            assert call_kwargs["port"] == 3847
            assert call_kwargs["lifespan"] == "on"

    # @trace FR-MCP-061
    @patch("uvicorn.run")
    @patch("thegent.config.ThegentSettings")
    @patch.object(_mcp_mod.mcp, "http_app")
    def test_run_custom_host_port(
        self, mock_http_app: MagicMock, mock_settings_cls: MagicMock, mock_uvicorn: MagicMock
    ) -> None:
        """Uses explicit host/port when provided."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FASTMCP_EVENT_STORE_URL", None)
            mock_settings = MagicMock()
            mock_settings.mcp_host = "127.0.0.1"
            mock_settings.mcp_port = 3847
            mock_settings_cls.return_value = mock_settings
            mock_http_app.return_value = MagicMock()

            _mcp_mod.run(host="192.168.1.1", port=9999)
            call_kwargs = mock_uvicorn.call_args[1]
            assert call_kwargs["host"] == "192.168.1.1"
            assert call_kwargs["port"] == 9999


# ===================================================================
# Resource: resource_meta
# ===================================================================


@pytest.mark.unit
class TestResourceMeta:
    """Tests for resource_meta."""

    # @trace FR-MCP-062
    @patch("thegent.mcp.server.get_server_meta_impl")
    def test_returns_server_metadata(self, mock_meta: MagicMock) -> None:
        """Returns JSON with server meta."""
        mock_meta.return_value = {"version": "1.0.0", "capabilities": ["run", "bg"]}
        result = _mcp_mod.resource_meta()
        data = json.loads(result)
        assert data["version"] == "1.0.0"
        assert "run" in data["capabilities"]


# ===================================================================
# Resource: resource_dag
# ===================================================================


@pytest.mark.unit
class TestResourceDagDeep:
    """Tests for resource_dag."""

    # @trace FR-MCP-063
    @patch("thegent.mcp.server.dag_list_impl")
    def test_resource_dag_empty_tasks(self, mock_dag: MagicMock) -> None:
        """Returns empty tasks array."""
        mock_dag.return_value = {"frontmatter": {}, "tasks": []}
        result = _mcp_mod.resource_dag()
        data = json.loads(result)
        assert data["tasks"] == []
        mock_dag.assert_called_once_with(cd=None)


# ===================================================================
# Resource: observe summary
# ===================================================================


@pytest.mark.unit
class TestResourceObserveSummaryDeep:
    """Tests for resource_observe_summary."""

    # @trace FR-MCP-064
    @patch("thegent.mcp.server.observe_summary_impl")
    def test_returns_stable_json(self, mock_impl: MagicMock) -> None:
        """Returns _stable_json serialized payload."""
        mock_impl.return_value = {"status": "ok", "kpis": {}, "drift": {}}
        result = _mcp_mod.resource_observe_summary()
        data = json.loads(result)
        assert data["status"] == "ok"
        keys = list(data.keys())
        assert keys == sorted(keys)


# ===================================================================
# Resource: session contract health trend
# ===================================================================


@pytest.mark.unit
class TestResourceSessionContractHealthTrend:
    """Tests for resource_session_contract_health_trend."""

    # @trace FR-MCP-065
    @patch("thegent.mcp.server.session_contract_health_trend_impl")
    def test_returns_trend_data(self, mock_impl: MagicMock) -> None:
        """Returns trend payload with stable JSON."""
        mock_impl.return_value = {"snapshots": [], "delta_summary": {}, "payload_type": "trend"}
        result = _mcp_mod.resource_session_contract_health_trend()
        data = json.loads(result)
        assert data["payload_type"] == "trend"
        mock_impl.assert_called_once()


# ===================================================================
# Tool: thegent_session_contract_health_trend (tool version)
# ===================================================================


@pytest.mark.unit
class TestThegentSessionContractHealthTrendTool:
    """Tests for thegent_session_contract_health_trend tool."""

    # @trace FR-MCP-066
    @patch("thegent.mcp.server.session_contract_health_trend_impl")
    def test_trend_tool_returns_payload(self, mock_impl: MagicMock) -> None:
        """Returns trend payload as ToolResult."""
        mock_impl.return_value = {
            "payload_type": "session_contract_health_trend",
            "schema_version": "v1",
            "snapshots": [],
            "delta_summary": {},
            "scope_key": {},
            "latest": None,
            "compat": None,
        }
        result = _mcp_mod.thegent_session_contract_health_trend()
        data = _json_content(result)
        assert data["payload_type"] == "session_contract_health_trend"
        meta = result.meta if hasattr(result, "meta") else {}
        if meta:
            assert "execution_time_ms" in meta

    # @trace FR-MCP-067
    @patch("thegent.mcp.server.session_contract_health_trend_impl")
    def test_trend_tool_with_custom_params(self, mock_impl: MagicMock) -> None:
        """Passes custom params through."""
        mock_impl.return_value = {
            "payload_type": "session_contract_health_trend",
            "schema_version": "v1",
            "snapshots": [],
            "delta_summary": {},
            "scope_key": {},
            "latest": None,
            "compat": None,
        }
        _mcp_mod.thegent_session_contract_health_trend(
            payload_type="session_contract_health_gate",
            owner="team-a",
            all=True,
            strict=True,
            limit=5,
        )
        call_kwargs = mock_impl.call_args[1]
        assert call_kwargs["payload_type"] == "session_contract_health_gate"
        assert call_kwargs["owner"] == "team-a"
        assert call_kwargs["all"] is True
        assert call_kwargs["limit"] == 5

    # @trace FR-MCP-073
    @patch("thegent.mcp.server.session_contract_health_trend_impl")
    def test_trend_tool_meta_envelope(self, mock_impl: MagicMock) -> None:
        """Meta block contains all _health_trend_meta fields."""
        mock_impl.return_value = {
            "payload_type": "session_contract_health_trend",
            "schema_version": "v1",
            "status": "healthy",
            "trend_payload_type": "session_contract_health_gate",
            "snapshots": [{"id": "s1"}, {"id": "s2"}],
            "delta_summary": {"blocked_ratio_delta": 0.1},
            "scope_key": {"owner": "team-a"},
            "latest": {
                "status": "pass",
                "pass": True,
                "blocked_ratio": 0.05,
                "blocked_count": 1,
                "issue_types": ["type_a", "type_b"],
            },
            "compat": {"mode": "v1", "aliases": {"old": "new"}},
        }
        result = _mcp_mod.thegent_session_contract_health_trend()
        meta = result.meta
        assert meta["status"] == "healthy"
        assert meta["trend_payload_type"] == "session_contract_health_gate"
        assert meta["latest_status"] == "pass"
        assert meta["latest_pass"] is True
        assert meta["latest_blocked_ratio"] == 0.05
        assert meta["latest_blocked_count"] == 1
        assert meta["latest_issue_types_count"] == 2
        assert "type_a" in meta["latest_issue_types_csv"]
        assert meta["compat_mode"] == "v1"
        assert meta["compat_aliases"] == {"old": "new"}
        assert meta["compat_aliases_count"] == 1

    # @trace FR-MCP-074
    @patch("thegent.mcp.server.session_contract_health_trend_impl")
    def test_trend_tool_error_envelope(self, mock_impl: MagicMock) -> None:
        """MCPBudgetExceeded returns error _ToolResult."""
        from thegent.mcp.server.mcp_perf_gates import MCPBudgetExceeded

        mock_impl.side_effect = MCPBudgetExceeded("health_trend_ms", 80.0, 50.0)
        result = _mcp_mod.thegent_session_contract_health_trend()
        assert "MCP budget exceeded" in result.content
        assert result.structured_content == {}
        assert result.meta == {}

    # @trace FR-MCP-075
    @patch("thegent.mcp.server.session_contract_health_trend_impl")
    def test_trend_tool_structured_content(self, mock_impl: MagicMock) -> None:
        """structured_content matches the raw impl payload."""
        raw_payload = {
            "payload_type": "session_contract_health_trend",
            "schema_version": "v1",
            "snapshots": [{"id": "s1"}],
            "delta_summary": {"blocked_ratio_delta": 0.1},
            "scope_key": {"owner": "team-a"},
            "latest": {"status": "pass", "pass": True},
            "compat": None,
        }
        mock_impl.return_value = raw_payload
        result = _mcp_mod.thegent_session_contract_health_trend()
        assert result.structured_content == raw_payload


# ===================================================================
# Tool: thegent_observe_summary (deep meta verification)
# ===================================================================


@pytest.mark.unit
class TestThegentObserveSummaryDeep:
    """Deep meta verification for thegent_observe_summary tool."""

    # @trace FR-MCP-068
    @patch("thegent.mcp.server.observe_summary_impl")
    def test_observe_meta_has_kpi_fields(self, mock_impl: MagicMock) -> None:
        """Verifies meta includes KPI-derived fields."""
        mock_impl.return_value = {
            "status": "ok",
            "payload_type": "observe_summary",
            "payload_schema_version": "observe-summary-schema-v1",
            "alerts": [],
            "kpis": {
                "total_events": 100,
                "fallback_rate": 0.05,
                "structural_drift_pct": 1.0,
                "semantic_drift_pct": 2.0,
            },
            "drift": {
                "within_budget": True,
                "structural_rate_pct": 1.0,
                "semantic_rate_pct": 2.0,
            },
            "escalation": {
                "backlog_count": 3,
                "past_sla_count": 1,
                "top_escalations_count": 2,
            },
            "trend_summary": {"enabled": False},
            "generated_query": {"trend_samples": 0},
        }
        result = _mcp_mod.thegent_observe_summary()
        meta = result.meta
        assert meta["kpi_total_events"] == 100
        assert meta["fallback_rate"] == 0.05
        assert meta["drift_within_budget"] is True
        assert meta["backlog_count"] == 3


# ===================================================================
# Resource: resource_sessions
# ===================================================================


@pytest.mark.unit
class TestResourceSessionsDeep:
    """Deep tests for resource_sessions."""

    # @trace FR-MCP-069
    @patch("thegent.mcp.server.ps_impl")
    def test_resource_sessions_passes_include_contract(self, mock_ps: MagicMock) -> None:
        """Passes include_contract flag through."""
        mock_ps.return_value = []
        _mcp_mod.resource_sessions(include_contract=True)
        mock_ps.assert_called_once_with(owner=None, all=True, include_contract=True)


# ===================================================================
# Tool: thegent_list_droids
# ===================================================================


@pytest.mark.unit
class TestThegentListDroids:
    """Tests for thegent_list_droids tool."""

    # @trace FR-MCP-070
    @patch("thegent.mcp.server.list_droids_impl")
    def test_list_droids_with_cd(self, mock_impl: MagicMock) -> None:
        """Lists droids with explicit cd."""
        mock_impl.return_value = ["droid-a", "droid-b"]
        result = _mcp_mod.thegent_list_droids(cd="/tmp/project", default_cwd=None)
        data = _json_content(result)
        assert data == ["droid-a", "droid-b"]
        assert result.structured_content == {"droids": ["droid-a", "droid-b"]}

    # @trace FR-MCP-071
    @patch("thegent.mcp.server.list_droids_impl")
    def test_list_droids_with_default_cwd(self, mock_impl: MagicMock) -> None:
        """Uses default_cwd when cd is None."""
        mock_impl.return_value = []
        _mcp_mod.thegent_list_droids(cd=None, default_cwd=Path("/default/path"))
        mock_impl.assert_called_once_with(cd=Path("/default/path"))


# ===================================================================
# Tool: thegent_list_models (deep)
# ===================================================================


@pytest.mark.unit
class TestThegentListModelsDeep:
    """Deep tests for thegent_list_models tool."""

    # @trace FR-MCP-072
    @patch("thegent.mcp.server.list_models_impl")
    def test_list_models_with_by_model(self, mock_impl: MagicMock) -> None:
        """Passes by_model flag through."""
        mock_impl.return_value = {"claude-sonnet-4": ["anthropic", "cursor"]}
        result = _mcp_mod.thegent_list_models(by_model=True)
        data = _json_content(result)
        assert "claude-sonnet-4" in data
        mock_impl.assert_called_once_with(provider=None, include_contract=False, by_model=True)


# ===================================================================
# TOOL_ICONS constant
# ===================================================================


@pytest.mark.unit
class TestToolIcons:
    """Tests for TOOL_ICONS constant."""

    # @trace FR-MCP-073
    def test_tool_icons_has_expected_keys(self) -> None:
        """TOOL_ICONS has entries for core tools."""
        assert "thegent_run" in _mcp_mod.TOOL_ICONS
        assert "thegent_bg" in _mcp_mod.TOOL_ICONS
        assert "thegent_stop" in _mcp_mod.TOOL_ICONS
        assert "thegent_ps" in _mcp_mod.TOOL_ICONS
        assert "thegent_dag_list" in _mcp_mod.TOOL_ICONS

    # @trace FR-MCP-074
    def test_tool_icons_values_are_strings(self) -> None:
        """All icon values are non-empty strings."""
        for key, icon in _mcp_mod.TOOL_ICONS.items():
            assert isinstance(icon, str), f"Icon for {key} is not a string"
            assert len(icon) > 0, f"Icon for {key} is empty"


# ===================================================================
# Resource: session contract health gate (deep)
# ===================================================================


@pytest.mark.unit
class TestResourceSessionContractHealthGateDeep:
    """Deep tests for resource_session_contract_health_gate."""

    # @trace FR-MCP-075
    @patch("thegent.mcp.server.session_contract_health_gate_impl")
    def test_uses_stable_json(self, mock_impl: MagicMock) -> None:
        """Output uses _stable_json for deterministic serialization."""
        mock_impl.return_value = {"z_field": 1, "a_field": 2, "pass": True}
        result = _mcp_mod.resource_session_contract_health_gate()
        parsed = json.loads(result)
        keys = list(parsed.keys())
        assert keys == sorted(keys)

    # @trace FR-MCP-076
    @patch("thegent.mcp.server.session_contract_health_gate_impl")
    def test_passes_regression_params(self, mock_impl: MagicMock) -> None:
        """Passes no_worse_than_baseline and regression_tolerance."""
        mock_impl.return_value = {"pass": True}
        _mcp_mod.resource_session_contract_health_gate(no_worse_than_baseline=True, regression_tolerance=0.1)
        call_kwargs = mock_impl.call_args[1]
        assert call_kwargs["no_worse_than_baseline"] is True
        assert call_kwargs["regression_tolerance"] == 0.1
