"""Unit tests targeting remaining uncovered lines in thegent.mcp.server.

Covers: model-first routing in thegent_run, CWD/owner elicitation branches,
progress reporting, include_contract response building, thegent_bg route policy
normalization, thegent_resolve_model_route, thegent_list_operations valid
operation path, thegent_list_modes valid mode path, thegent_dag_list accepted
elicitation.
"""

from __future__ import annotations

import asyncio
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


def _inject_missing_names() -> None:
    """Inject _resolve_cwd, _default_owner_tag, and elicitation types."""
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


def _make_ctx() -> AsyncMock:
    """Build a mock Context with all async methods pre-configured."""
    ctx = AsyncMock()
    ctx.info = AsyncMock()
    ctx.report_progress = AsyncMock()
    ctx.close_sse_stream = AsyncMock()
    ctx.elicit = AsyncMock()
    return ctx


def _make_resolved_route(
    provider: str = "claude",
    model_alias: str = "claude-sonnet-4",
    backend_type: str = "direct",
    priority: int = 0,
    schema_version: int = 1,
) -> MagicMock:
    """Build a mock ResolvedRoute."""
    rr = MagicMock()
    rr.provider = provider
    rr.model_alias = model_alias
    rr.backend_type = backend_type
    rr.priority = priority
    rr.schema_version = schema_version
    return rr


def _make_route(
    provider: str = "claude",
    model_alias: str = "claude-sonnet-4",
    backend_type: str = "direct",
    priority: int = 0,
) -> MagicMock:
    """Build a mock Route."""
    r = MagicMock()
    r.provider = provider
    r.model_alias = model_alias
    r.backend_type = backend_type
    r.priority = priority
    return r


def _make_elicitation(elicit_type: str, data: str | None = None) -> Any:
    """Create an elicitation response of the given type."""
    try:
        from fastmcp.server.context import (
            AcceptedElicitation,
            CancelledElicitation,
            DeclinedElicitation,
        )

        if elicit_type == "accepted":
            return AcceptedElicitation(data=data)
        if elicit_type == "declined":
            return DeclinedElicitation()
        if elicit_type == "cancelled":
            return CancelledElicitation()
    except (ImportError, TypeError):
        pass
    # Fallback to mock
    mock = MagicMock()
    if elicit_type == "accepted":
        mock.data = data
        if hasattr(_mcp_mod, "AcceptedElicitation"):
            mock.__class__ = _mcp_mod.AcceptedElicitation
    elif elicit_type == "declined":
        if hasattr(_mcp_mod, "DeclinedElicitation"):
            mock.__class__ = _mcp_mod.DeclinedElicitation
    elif elicit_type == "cancelled":
        if hasattr(_mcp_mod, "CancelledElicitation"):
            mock.__class__ = _mcp_mod.CancelledElicitation
    elif elicit_type == "ambiguous":
        mock.__class__ = type("UnknownElicitation", (), {})
    return mock


# ===================================================================
# thegent_run: model-first routing (lines 549-566)
# ===================================================================


@pytest.mark.unit
class TestThegentRunModelFirst:
    """Cover model-first routing in thegent_run (model given, no agent)."""

    # @trace FR-MCP-200
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl")
    async def test_model_only_resolves_route(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        """When model is given without agent, resolve_route picks agent."""
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "timed_out": False,
        }
        ctx = _make_ctx()
        with (
            patch("thegent.config.ThegentSettings") as mock_settings_cls,
            patch("thegent.models.resolve_route", return_value=("gemini", "gemini-3-flash")),
        ):
            mock_settings_cls.return_value.default_routing = "prefer_direct"
            result = await _mcp_mod.thegent_run(
                prompt="do something",
                agent=None,
                model="gemini-3-flash",
                provider=None,
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )
        data = _json_content(result)
        assert data["exit_code"] == 0
        mock_run_impl.assert_called_once()
        call_args = mock_run_impl.call_args[0]
        assert call_args[0] == "gemini"  # agent resolved

    # @trace FR-MCP-201
    @pytest.mark.asyncio
    async def test_model_only_no_route_returns_error(self) -> None:
        """When model given but no route found, returns error."""
        ctx = _make_ctx()
        with (
            patch("thegent.config.ThegentSettings") as mock_settings_cls,
            patch("thegent.models.resolve_route", return_value=None),
        ):
            mock_settings_cls.return_value.default_routing = "prefer_direct"
            result = await _mcp_mod.thegent_run(
                prompt="do something",
                agent=None,
                model="nonexistent-model",
                provider=None,
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )
        data = _json_content(result)
        assert data["exit_code"] == 1
        assert "No route" in data["error"]

    # @trace FR-MCP-202
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl")
    async def test_model_only_with_include_contract(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        """Model-first with include_contract resolves route contract."""
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "timed_out": False,
        }
        rr = _make_resolved_route(provider="claude", model_alias="claude-sonnet-4")
        ctx = _make_ctx()
        with (
            patch("thegent.config.ThegentSettings") as mock_settings_cls,
            patch("thegent.models.resolve_route", return_value=("claude", "claude-sonnet-4")),
            patch("thegent.models.resolve_route_contract", return_value=rr),
        ):
            mock_settings_cls.return_value.default_routing = "prefer_direct"
            result = await _mcp_mod.thegent_run(
                prompt="contract test",
                agent=None,
                model="claude-sonnet-4",
                provider=None,
                include_contract=True,
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )
        data = _json_content(result)
        assert "routing" in data
        assert data["routing"]["route_contract"] is not None
        assert data["routing"]["route_contract"]["provider"] == "claude"

    # @trace FR-MCP-203
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl")
    async def test_model_only_include_contract_no_route_contract(
        self, mock_run_impl: MagicMock, mock_cwd: MagicMock
    ) -> None:
        """Model-first include_contract but resolve_route_contract returns None."""
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "timed_out": False,
        }
        ctx = _make_ctx()
        with (
            patch("thegent.config.ThegentSettings") as mock_settings_cls,
            patch("thegent.models.resolve_route", return_value=("claude", "claude-sonnet-4")),
            patch("thegent.models.resolve_route_contract", return_value=None),
        ):
            mock_settings_cls.return_value.default_routing = "prefer_direct"
            result = await _mcp_mod.thegent_run(
                prompt="no contract",
                agent=None,
                model="claude-sonnet-4",
                include_contract=True,
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )
        data = _json_content(result)
        # include_contract produces routing key but route_contract stays None in request_payload
        assert "routing" in data

    # @trace FR-MCP-204
    @pytest.mark.asyncio
    async def test_model_only_invalid_policy_defaults(self) -> None:
        """When default_routing is invalid, falls back to prefer_direct."""
        ctx = _make_ctx()
        with (
            patch("thegent.config.ThegentSettings") as mock_settings_cls,
            patch("thegent.models.resolve_route", return_value=None),
        ):
            mock_settings_cls.return_value.default_routing = "bad_policy"
            result = await _mcp_mod.thegent_run(
                prompt="bad policy test",
                agent=None,
                model="some-model",
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )
        data = _json_content(result)
        assert data["exit_code"] == 1


# ===================================================================
# thegent_run: model + agent routing failure (lines 579, 583-586)
# ===================================================================


@pytest.mark.unit
class TestThegentRunModelAndAgent:
    """Cover model + agent routing branches in thegent_run."""

    # @trace FR-MCP-205
    @pytest.mark.asyncio
    async def test_model_and_agent_no_route_shows_available(self) -> None:
        """When model+agent provided but route not found, shows available providers."""
        ctx = _make_ctx()
        mock_routes = [_make_route(provider="gemini"), _make_route(provider="copilot")]
        with (
            patch("thegent.config.ThegentSettings") as mock_settings_cls,
            patch("thegent.models.resolve_route", return_value=None),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_settings_cls.return_value.default_routing = "prefer_direct"
            mock_catalog.routes_for.return_value = mock_routes
            result = await _mcp_mod.thegent_run(
                prompt="fail route",
                agent="nonexistent-provider",
                model="claude-sonnet-4",
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )
        data = _json_content(result)
        assert data["exit_code"] == 1
        assert "not available" in data["error"]
        assert "copilot" in data["error"] or "gemini" in data["error"]

    # @trace FR-MCP-206
    @pytest.mark.asyncio
    async def test_model_and_agent_no_route_no_available(self) -> None:
        """When model+agent provided and no routes at all."""
        ctx = _make_ctx()
        with (
            patch("thegent.config.ThegentSettings") as mock_settings_cls,
            patch("thegent.models.resolve_route", return_value=None),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_settings_cls.return_value.default_routing = "prefer_direct"
            mock_catalog.routes_for.return_value = []
            result = await _mcp_mod.thegent_run(
                prompt="no routes at all",
                agent="bad-provider",
                model="bad-model",
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )
        data = _json_content(result)
        assert data["exit_code"] == 1
        assert "not available" in data["error"]

    # @trace FR-MCP-207
    @pytest.mark.asyncio
    async def test_model_and_agent_invalid_policy_defaults(self) -> None:
        """When model+agent and policy is invalid, defaults to prefer_direct."""
        ctx = _make_ctx()
        with (
            patch("thegent.config.ThegentSettings") as mock_settings_cls,
            patch("thegent.models.resolve_route", return_value=None),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_settings_cls.return_value.default_routing = "invalid_policy"
            mock_catalog.routes_for.return_value = []
            result = await _mcp_mod.thegent_run(
                prompt="bad policy with both",
                agent="provider",
                model="model",
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )
        data = _json_content(result)
        assert data["exit_code"] == 1

    # @trace FR-MCP-208
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl")
    async def test_model_and_agent_with_include_contract(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        """Model+agent with include_contract resolves route contract."""
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "timed_out": False,
        }
        rr = _make_resolved_route()
        ctx = _make_ctx()
        with (
            patch("thegent.config.ThegentSettings") as mock_settings_cls,
            patch("thegent.models.resolve_route", return_value=("claude", "claude-sonnet-4")),
            patch("thegent.models.resolve_route_contract", return_value=rr),
        ):
            mock_settings_cls.return_value.default_routing = "prefer_direct"
            result = await _mcp_mod.thegent_run(
                prompt="contract both",
                agent="claude",
                model="claude-sonnet-4",
                include_contract=True,
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )
        data = _json_content(result)
        assert "routing" in data
        assert data["routing"]["route_contract"]["provider"] == "claude"


# ===================================================================
# thegent_run: CWD elicitation branches (lines 611-625)
# ===================================================================


@pytest.mark.unit
class TestThegentRunCwdElicitation:
    """Cover CWD elicitation branches in thegent_run."""

    # @trace FR-MCP-209
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    @patch("thegent.mcp.server.run_impl")
    async def test_accepted_elicitation_continues(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        """Accepted CWD elicitation proceeds with the run."""
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "timed_out": False,
        }
        accepted = _make_elicitation("accepted", data="/tmp/elicited")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(return_value=accepted)
        result = await _mcp_mod.thegent_run(
            prompt="elicited cwd",
            agent="claude",
            cd=None,
            ctx=ctx,
            default_cwd=None,
        )
        data = _json_content(result)
        assert data["exit_code"] == 0

    # @trace FR-MCP-210
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    async def test_declined_elicitation_returns_error(self, mock_cwd: MagicMock) -> None:
        """Declined CWD elicitation returns error."""
        declined = _make_elicitation("declined")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(return_value=declined)
        result = await _mcp_mod.thegent_run(
            prompt="declined cwd",
            agent="claude",
            cd=None,
            ctx=ctx,
            default_cwd=None,
        )
        data = _json_content(result)
        assert data["exit_code"] == 1
        assert "declined" in data["error"].lower()

    # @trace FR-MCP-211
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    async def test_cancelled_elicitation_returns_error(self, mock_cwd: MagicMock) -> None:
        """Cancelled CWD elicitation returns error."""
        cancelled = _make_elicitation("cancelled")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(return_value=cancelled)
        result = await _mcp_mod.thegent_run(
            prompt="cancelled cwd",
            agent="claude",
            cd=None,
            ctx=ctx,
            default_cwd=None,
        )
        data = _json_content(result)
        assert data["exit_code"] == 1
        assert "cancelled" in data["error"].lower()

    # @trace FR-MCP-212
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    async def test_ambiguous_elicitation_returns_error(self, mock_cwd: MagicMock) -> None:
        """Ambiguous/unknown elicitation type returns error."""
        ambiguous = _make_elicitation("ambiguous")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(return_value=ambiguous)
        result = await _mcp_mod.thegent_run(
            prompt="ambiguous cwd",
            agent="claude",
            cd=None,
            ctx=ctx,
            default_cwd=None,
        )
        data = _json_content(result)
        assert data["exit_code"] == 1
        assert "Ambiguous" in data["error"]


# ===================================================================
# thegent_run: include_contract response building (lines 664-672)
# ===================================================================


@pytest.mark.unit
class TestThegentRunIncludeContract:
    """Cover include_contract response building in thegent_run."""

    # @trace FR-MCP-213
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl")
    async def test_include_contract_builds_payload(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        """include_contract=True without model still builds routing in payload."""
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "timed_out": False,
        }
        ctx = _make_ctx()
        result = await _mcp_mod.thegent_run(
            prompt="contract build",
            agent="claude",
            include_contract=True,
            cd="/tmp/test",
            ctx=ctx,
            default_cwd=Path("/tmp/test"),
        )
        data = _json_content(result)
        assert "routing" in data
        assert data["routing"]["resolved_agent"] == "claude"
        assert "extraction_schema_version" in data  # full=False by default

    # @trace FR-MCP-214
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server.run_impl")
    async def test_include_contract_full_mode_no_schema(self, mock_run_impl: MagicMock, mock_cwd: MagicMock) -> None:
        """include_contract with full=True omits extraction_schema_version."""
        mock_run_impl.return_value = {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "timed_out": False,
        }
        ctx = _make_ctx()
        result = await _mcp_mod.thegent_run(
            prompt="contract full",
            agent="claude",
            include_contract=True,
            full=True,
            cd="/tmp/test",
            ctx=ctx,
            default_cwd=Path("/tmp/test"),
        )
        data = _json_content(result)
        assert "routing" in data
        assert "extraction_schema_version" not in data


# ===================================================================
# thegent_bg: CWD elicitation (lines 727-739)
# ===================================================================


@pytest.mark.unit
class TestThegentBgCwdElicitation:
    """Cover CWD elicitation branches in thegent_bg."""

    # @trace FR-MCP-215
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    @patch("thegent.mcp.server._default_owner_tag", return_value="auto-owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_accepted_elicitation(
        self, mock_bg_impl: MagicMock, mock_owner: MagicMock, mock_cwd: MagicMock
    ) -> None:
        """Accepted CWD elicitation in bg, then owner elicitation triggers."""
        mock_bg_impl.return_value = {"session_id": "s1", "log_path": "/tmp/log", "owner": "auto-owner"}
        accepted_cwd = _make_elicitation("accepted", data="/tmp/elicited")
        accepted_owner = _make_elicitation("accepted", data="my-owner")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(side_effect=[accepted_cwd, accepted_owner])
        result = await _mcp_mod.thegent_bg(
            agent="claude",
            prompt="bg elicited",
            cd=None,
            ctx=ctx,
            default_cwd=None,
            default_owner=None,
        )
        data = _json_content(result)
        assert data["session_id"] == "s1"

    # @trace FR-MCP-216
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    async def test_bg_declined_elicitation(self, mock_cwd: MagicMock) -> None:
        """Declined CWD elicitation in bg returns error."""
        declined = _make_elicitation("declined")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(return_value=declined)
        result = await _mcp_mod.thegent_bg(
            agent="claude",
            prompt="bg declined",
            cd=None,
            ctx=ctx,
            default_cwd=None,
            default_owner=None,
        )
        data = _json_content(result)
        assert "error" in data
        assert data["exit_code"] == 1

    # @trace FR-MCP-217
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    async def test_bg_cancelled_elicitation(self, mock_cwd: MagicMock) -> None:
        """Cancelled CWD elicitation in bg returns error."""
        cancelled = _make_elicitation("cancelled")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(return_value=cancelled)
        result = await _mcp_mod.thegent_bg(
            agent="claude",
            prompt="bg cancelled",
            cd=None,
            ctx=ctx,
            default_cwd=None,
            default_owner=None,
        )
        data = _json_content(result)
        assert "error" in data
        assert data["exit_code"] == 1

    # @trace FR-MCP-218
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    async def test_bg_ambiguous_elicitation(self, mock_cwd: MagicMock) -> None:
        """Ambiguous CWD elicitation in bg returns error."""
        ambiguous = _make_elicitation("ambiguous")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(return_value=ambiguous)
        result = await _mcp_mod.thegent_bg(
            agent="claude",
            prompt="bg ambiguous",
            cd=None,
            ctx=ctx,
            default_cwd=None,
            default_owner=None,
        )
        data = _json_content(result)
        assert "error" in data
        assert data["exit_code"] == 1


# ===================================================================
# thegent_bg: route policy normalization (lines 752-759)
# ===================================================================


@pytest.mark.unit
class TestThegentBgRoutePolicy:
    """Cover route policy normalization branches in thegent_bg."""

    # @trace FR-MCP-219
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server._default_owner_tag", return_value="owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_invalid_policy_defaults(
        self, mock_bg_impl: MagicMock, mock_owner: MagicMock, mock_cwd: MagicMock
    ) -> None:
        """Invalid normalize_route_policy falls back to prefer_direct."""
        mock_bg_impl.return_value = {"session_id": "s1", "log_path": "/tmp", "owner": "owner"}
        ctx = _make_ctx()
        with patch("thegent.models.normalize_route_policy", side_effect=ValueError("bad")):
            result = await _mcp_mod.thegent_bg(
                agent="claude",
                prompt="bad routing",
                routing="invalid_policy",
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
                default_owner=None,
            )
        data = _json_content(result)
        assert data["session_id"] == "s1"

    # @trace FR-MCP-220
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server._default_owner_tag", return_value="owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_routing_param_sets_child_routing(
        self, mock_bg_impl: MagicMock, mock_owner: MagicMock, mock_cwd: MagicMock
    ) -> None:
        """When routing param is set, it propagates to routing_for_child."""
        mock_bg_impl.return_value = {"session_id": "s2", "log_path": "/tmp", "owner": "owner"}
        ctx = _make_ctx()
        with patch("thegent.models.normalize_route_policy", return_value="prefer_proxy"):
            result = await _mcp_mod.thegent_bg(
                agent="claude",
                prompt="proxy routing",
                routing="prefer_proxy",
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
                default_owner=None,
            )
        data = _json_content(result)
        assert data["session_id"] == "s2"

    # @trace FR-MCP-221
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server._default_owner_tag", return_value="owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_failover_policy_sets_flag(
        self, mock_bg_impl: MagicMock, mock_owner: MagicMock, mock_cwd: MagicMock
    ) -> None:
        """Failover policy sets failover=True and falls back to prefer_direct."""
        mock_bg_impl.return_value = {"session_id": "s3", "log_path": "/tmp", "owner": "owner"}
        ctx = _make_ctx()
        with patch("thegent.models.normalize_route_policy", return_value="failover"):
            result = await _mcp_mod.thegent_bg(
                agent="claude",
                prompt="failover routing",
                routing="failover",
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
                default_owner=None,
            )
        data = _json_content(result)
        assert data["session_id"] == "s3"
        # Verify bg_impl was called with failover=True
        call_kwargs = mock_bg_impl.call_args
        if call_kwargs[1]:
            assert call_kwargs[1].get("failover") is True


# ===================================================================
# thegent_bg: owner elicitation (lines 763-774)
# ===================================================================


@pytest.mark.unit
class TestThegentBgOwnerElicitation:
    """Cover owner elicitation branches in thegent_bg."""

    # @trace FR-MCP-222
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    @patch("thegent.mcp.server._default_owner_tag", return_value="fallback-owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_owner_declined_uses_default(
        self, mock_bg_impl: MagicMock, mock_owner_tag: MagicMock, mock_cwd: MagicMock
    ) -> None:
        """Declined owner elicitation uses _default_owner_tag."""
        mock_bg_impl.return_value = {"session_id": "s1", "log_path": "/tmp", "owner": "fallback-owner"}
        accepted_cwd = _make_elicitation("accepted", data="/tmp/elicited")
        declined_owner = _make_elicitation("declined")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(side_effect=[accepted_cwd, declined_owner])
        result = await _mcp_mod.thegent_bg(
            agent="claude",
            prompt="owner declined",
            cd=None,
            ctx=ctx,
            default_cwd=None,
            default_owner=None,
        )
        data = _json_content(result)
        assert data["session_id"] == "s1"

    # @trace FR-MCP-223
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    async def test_bg_owner_cancelled_returns_error(self, mock_cwd: MagicMock) -> None:
        """Cancelled owner elicitation returns error."""
        accepted_cwd = _make_elicitation("accepted", data="/tmp/elicited")
        cancelled_owner = _make_elicitation("cancelled")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(side_effect=[accepted_cwd, cancelled_owner])
        result = await _mcp_mod.thegent_bg(
            agent="claude",
            prompt="owner cancelled",
            cd=None,
            ctx=ctx,
            default_cwd=None,
            default_owner=None,
        )
        data = _json_content(result)
        assert "error" in data
        assert data["exit_code"] == 1

    # @trace FR-MCP-224
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    @patch("thegent.mcp.server._default_owner_tag", return_value="default-owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_owner_ambiguous_uses_default(
        self, mock_bg_impl: MagicMock, mock_owner_tag: MagicMock, mock_cwd: MagicMock
    ) -> None:
        """Ambiguous owner elicitation falls back to _default_owner_tag."""
        mock_bg_impl.return_value = {"session_id": "s1", "log_path": "/tmp", "owner": "default-owner"}
        accepted_cwd = _make_elicitation("accepted", data="/tmp/elicited")
        ambiguous_owner = _make_elicitation("ambiguous")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(side_effect=[accepted_cwd, ambiguous_owner])
        result = await _mcp_mod.thegent_bg(
            agent="claude",
            prompt="owner ambiguous",
            cd=None,
            ctx=ctx,
            default_cwd=None,
            default_owner=None,
        )
        data = _json_content(result)
        assert data["session_id"] == "s1"


# ===================================================================
# thegent_bg: include_contract route lookup (lines 788, 803-804)
# ===================================================================


@pytest.mark.unit
class TestThegentBgIncludeContract:
    """Cover include_contract route lookup in thegent_bg."""

    # @trace FR-MCP-225
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server._default_owner_tag", return_value="owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_include_contract_resolved(
        self, mock_bg_impl: MagicMock, mock_owner: MagicMock, mock_cwd: MagicMock
    ) -> None:
        """include_contract with model resolves contract successfully."""
        mock_bg_impl.return_value = {"session_id": "s1", "log_path": "/tmp", "owner": "owner"}
        rr = _make_resolved_route()
        ctx = _make_ctx()
        with (
            patch("thegent.models.resolve_route_contract", return_value=rr),
            patch("thegent.models.route_contract", return_value={"schema_version": 1}),
        ):
            result = await _mcp_mod.thegent_bg(
                agent="claude",
                prompt="contract resolved",
                model="claude-sonnet-4",
                include_contract=True,
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
                default_owner=None,
            )
        data = _json_content(result)
        assert "routing" in data

    # @trace FR-MCP-226
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    @patch("thegent.mcp.server._default_owner_tag", return_value="owner")
    @patch("thegent.mcp.server.bg_impl")
    async def test_bg_include_contract_lookup_exception(
        self, mock_bg_impl: MagicMock, mock_owner: MagicMock, mock_cwd: MagicMock
    ) -> None:
        """include_contract with model: exception in lookup still proceeds."""
        mock_bg_impl.return_value = {"session_id": "s1", "log_path": "/tmp", "owner": "owner"}
        ctx = _make_ctx()
        with patch("thegent.models.resolve_route_contract", side_effect=RuntimeError("boom")):
            result = await _mcp_mod.thegent_bg(
                agent="claude",
                prompt="contract exception",
                model="claude-sonnet-4",
                include_contract=True,
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
                default_owner=None,
            )
        data = _json_content(result)
        assert "routing" in data


# ===================================================================
# thegent_list_operations: valid operation filter (lines 1397-1398)
# ===================================================================


@pytest.mark.unit
class TestThegentListOperationsValidFilter:
    """Cover the valid operation filter path in thegent_list_operations."""

    # @trace FR-MCP-227
    def test_valid_operation_filter_returns_entries(self) -> None:
        """Filtering by a valid operation type returns entries."""

        mock_entry = MagicMock()
        mock_entry.command = "run"
        mock_entry.description = "Run foreground agent"
        mock_entry.mcp_tool = "thegent_run"
        with patch("thegent.operations.get_operations_by_type", return_value=[mock_entry]) as mock_get:
            result = _mcp_mod.thegent_list_operations(operation="orchestrate")
            data = _json_content(result)
            assert "orchestrate" in data
            entries = data["orchestrate"]
            assert len(entries) == 1
            assert entries[0]["command"] == "run"
            mock_get.assert_called_once()


# ===================================================================
# thegent_list_modes: valid mode filter (line 1420)
# ===================================================================


@pytest.mark.unit
class TestThegentListModesValidFilter:
    """Cover the valid mode filter path in thegent_list_modes."""

    # @trace FR-MCP-228
    def test_valid_mode_filter_returns_entry(self) -> None:
        """Filtering by a valid mode returns the mode entry."""
        mock_entry = MagicMock()
        mock_entry.mode.value = "review_loop"
        mock_entry.description = "Review loop mode"
        mock_entry.phases = ["planner", "operator", "reviewer"]
        mock_entry.use_case = "Governance workflows"
        mock_entry.risk_profile = "high"
        mock_entry.selection_hint = "Use for reviews"
        with patch("thegent.orchestration_modes.get_mode", return_value=mock_entry):
            result = _mcp_mod.thegent_list_modes(mode="review_loop")
            data = _json_content(result)
            assert len(data) == 1
            assert data[0]["mode"] == "review_loop"
            assert data[0]["risk_profile"] == "high"
            assert data[0]["phases"] == ["planner", "operator", "reviewer"]


# ===================================================================
# thegent_resolve_model_route (lines 1507-1557)
# ===================================================================


@pytest.mark.unit
class TestThegentResolveModelRoute:
    """Cover thegent_resolve_model_route tool."""

    # @trace FR-MCP-229
    def test_resolve_model_route_invalid_policy(self) -> None:
        """Invalid policy returns error with valid_policies list."""
        with patch("thegent.models.normalize_route_policy", side_effect=ValueError("bad")):
            result = _mcp_mod.thegent_resolve_model_route(
                model="claude-sonnet-4",
                policy="garbage_policy",
            )
        data = _json_content(result)
        assert "error" in data
        assert data["policy"] == "garbage_policy"
        assert "valid_policies" in data

    # @trace FR-MCP-230
    def test_resolve_model_route_with_route_found(self) -> None:
        """Successful route resolution returns full payload."""
        rr = _make_resolved_route(
            provider="claude",
            model_alias="claude-sonnet-4",
            backend_type="direct",
            priority=0,
            schema_version=1,
        )
        mock_route_obj = _make_route(
            provider="claude",
            model_alias="claude-sonnet-4",
            backend_type="direct",
            priority=0,
        )
        with (
            patch("thegent.models.normalize_route_policy", return_value="prefer_direct"),
            patch("thegent.models.normalize_model_id", return_value="claude-sonnet-4"),
            patch("thegent.models.resolve_route_contract", return_value=rr),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = [mock_route_obj]
            result = _mcp_mod.thegent_resolve_model_route(
                model="claude-sonnet-4",
                provider="claude",
                policy="prefer_direct",
            )
        data = _json_content(result)
        assert data["route_found"] is True
        assert data["model"] == "claude-sonnet-4"
        assert data["normalized_model"] == "claude-sonnet-4"
        assert data["policy"] == "prefer_direct"
        assert "resolved_route" in data
        assert data["resolved_route"]["provider"] == "claude"

    # @trace FR-MCP-231
    def test_resolve_model_route_no_route(self) -> None:
        """No route found returns route_found=False."""
        with (
            patch("thegent.models.normalize_route_policy", return_value="prefer_direct"),
            patch("thegent.models.normalize_model_id", return_value="unknown-model"),
            patch("thegent.models.resolve_route_contract", return_value=None),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = []
            result = _mcp_mod.thegent_resolve_model_route(
                model="unknown-model",
            )
        data = _json_content(result)
        assert data["route_found"] is False
        assert "resolved_route" not in data
        assert data["available_routes"] == []

    # @trace FR-MCP-232
    def test_resolve_model_route_multiple_available_routes(self) -> None:
        """Multiple available routes are listed and sorted."""
        rr = _make_resolved_route(provider="claude")
        routes = [
            _make_route(provider="claude", model_alias="claude-sonnet-4", priority=0),
            _make_route(provider="copilot", model_alias="claude-sonnet-4", priority=5),
        ]
        with (
            patch("thegent.models.normalize_route_policy", return_value="prefer_direct"),
            patch("thegent.models.normalize_model_id", return_value="claude-sonnet-4"),
            patch("thegent.models.resolve_route_contract", return_value=rr),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = routes
            result = _mcp_mod.thegent_resolve_model_route(
                model="claude-sonnet-4",
            )
        data = _json_content(result)
        assert len(data["available_routes"]) == 2
        assert data["route_found"] is True

    # @trace FR-MCP-233
    def test_resolve_model_route_has_execution_time(self) -> None:
        """Result meta includes execution_time_ms."""
        with (
            patch("thegent.models.normalize_route_policy", return_value="prefer_direct"),
            patch("thegent.models.normalize_model_id", return_value="m"),
            patch("thegent.models.resolve_route_contract", return_value=None),
            patch("thegent.models.ModelCatalog") as mock_catalog,
        ):
            mock_catalog.routes_for.return_value = []
            result = _mcp_mod.thegent_resolve_model_route(model="m")
        assert result.meta is not None
        assert "execution_time_ms" in result.meta


# ===================================================================
# thegent_dag_list: accepted elicitation (line 1583)
# ===================================================================


@pytest.mark.unit
class TestThegentDagListAcceptedElicitation:
    """Cover the accepted elicitation branch in thegent_dag_list."""

    # @trace FR-MCP-234
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=None)
    @patch("thegent.mcp.server.dag_list_impl")
    async def test_dag_list_accepted_elicitation(self, mock_dag: MagicMock, mock_cwd: MagicMock) -> None:
        """Accepted CWD elicitation proceeds with DAG list."""
        mock_dag.return_value = {"frontmatter": {"project": "test"}, "tasks": [{"id": "T1"}]}
        accepted = _make_elicitation("accepted", data="/tmp/project")
        ctx = _make_ctx()
        ctx.elicit = AsyncMock(return_value=accepted)
        result = await _mcp_mod.thegent_dag_list(cd=None, ctx=ctx, default_cwd=None)
        data = _json_content(result)
        assert data["tasks"] == [{"id": "T1"}]
        mock_dag.assert_called_once()


# ===================================================================
# thegent_run: progress reporting (lines 654-655, 658-659)
#
# These lines are in the while-loop polling section. They fire when
# the task takes > 10s (report_progress) or > 30s (close_sse_stream).
# We mock the run_impl to simulate a task that runs for multiple
# iterations of the while loop.
# ===================================================================


@pytest.mark.unit
class TestThegentRunProgressReporting:
    """Cover progress reporting and SSE stream closing in thegent_run."""

    # @trace FR-MCP-235
    @pytest.mark.asyncio
    @patch("thegent.mcp.server._resolve_cwd", return_value=Path("/tmp/test"))
    async def test_run_reports_progress_and_closes_sse(self, mock_cwd: MagicMock) -> None:
        """When run takes long enough, report_progress and close_sse_stream are called."""
        import time as time_mod

        ctx = _make_ctx()

        # Track how many times perf_counter is called to simulate time progression
        perf_call_count = [0]
        base_time = time_mod.perf_counter()

        def fake_perf_counter() -> float:
            perf_call_count[0] += 1
            # First call = start_time. Subsequent calls simulate 35s elapsed
            # to trigger both the 10s progress and 30s SSE close thresholds.
            if perf_call_count[0] <= 1:
                return base_time
            return base_time + 35.0

        # run_impl is called in a thread via asyncio.to_thread - must be sync
        asyncio.Event()

        def sync_run_impl(*args: Any, **kwargs: Any) -> dict[str, Any]:
            # Block briefly so the while-loop polls at least once
            import threading

            evt = threading.Event()
            evt.wait(timeout=0.05)
            return {"exit_code": 0, "stdout": "ok", "stderr": "", "timed_out": False}

        original_sleep = asyncio.sleep

        async def fast_sleep(duration: float) -> None:
            await original_sleep(0.01)

        with (
            patch("thegent.mcp.server.run_impl", side_effect=sync_run_impl),
            patch("thegent.mcp.server.time.perf_counter", side_effect=fake_perf_counter),
            patch("thegent.mcp.server.asyncio.sleep", side_effect=fast_sleep),
        ):
            result = await _mcp_mod.thegent_run(
                prompt="long task",
                agent="claude",
                cd="/tmp/test",
                ctx=ctx,
                default_cwd=Path("/tmp/test"),
            )

        data = _json_content(result)
        assert data["exit_code"] == 0
        # The fake time jumps to 35s which triggers both thresholds
        assert ctx.report_progress.call_count >= 1
        assert ctx.close_sse_stream.call_count >= 1
