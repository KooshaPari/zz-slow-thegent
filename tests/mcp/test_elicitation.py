"""Unit tests for FastMCP elicitation API support.

Tests cover:
- elicit_confirmation: accepted (True/False), declined, cancelled, no ctx
- elicit_choice: accepted, declined, empty options error, no ctx
- elicit_text: accepted, declined, placeholder injection, no ctx
- MCP tool wrappers: thegent_elicit_confirmation/choice/text (via register_elicitation_tools)
- Graceful fallback when ctx.elicit is absent (older FastMCP)

# @trace FR-MCP-ELICIT-001
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import orjson as json
import pytest

fastmcp = pytest.importorskip("fastmcp", reason="fastmcp required for elicitation tests")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_accepted(data: Any) -> MagicMock:
    """Create a mock AcceptedElicitation with .action='accept' and .data=data."""
    m = MagicMock()
    m.action = "accept"
    m.data = data
    return m


def _make_declined() -> MagicMock:
    """Create a mock DeclinedElicitation with .action='decline'."""
    m = MagicMock()
    m.action = "decline"
    return m


def _make_cancelled() -> MagicMock:
    """Create a mock CancelledElicitation with .action='cancel'."""
    m = MagicMock()
    m.action = "cancel"
    return m


def _make_ctx(elicit_return: Any = None, has_elicit: bool = True) -> MagicMock:
    """Build a mock FastMCP Context with ctx.elicit returning elicit_return."""
    ctx = MagicMock()
    if has_elicit:
        ctx.elicit = AsyncMock(return_value=elicit_return)
    else:
        # Simulate older FastMCP where ctx.elicit does not exist
        del ctx.elicit
    return ctx


def _json_content(result: Any) -> Any:
    """Extract parsed JSON from a ToolResult.content (handles str or list[TextContent])."""
    if isinstance(result, str):
        return json.loads(result)
    content = result.content
    if isinstance(content, str):
        return json.loads(content)
    if isinstance(content, list) and len(content) > 0:
        text = getattr(content[0], "text", str(content[0]))
        return json.loads(text)
    return json.loads(str(content))


# ---------------------------------------------------------------------------
# Tests for elicit_confirmation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestElicitConfirmation:
    """Tests for the elicit_confirmation primitive. # @trace FR-MCP-ELICIT-001"""

    @pytest.mark.asyncio
    async def test_accepted_true(self) -> None:
        """AcceptedElicitation with data=True returns True. # @trace FR-MCP-ELICIT-001"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import elicit_confirmation

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = True
        ctx = _make_ctx(elicit_return=accepted)

        result = await elicit_confirmation(ctx, "Proceed?")
        assert result is True
        ctx.elicit.assert_awaited_once_with("Proceed?", bool)

    @pytest.mark.asyncio
    async def test_accepted_false(self) -> None:
        """AcceptedElicitation with data=False returns False. # @trace FR-MCP-ELICIT-001"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import elicit_confirmation

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = False
        ctx = _make_ctx(elicit_return=accepted)

        result = await elicit_confirmation(ctx, "Delete?")
        assert result is False

    @pytest.mark.asyncio
    async def test_declined_returns_none(self) -> None:
        """DeclinedElicitation returns None. # @trace FR-MCP-ELICIT-001"""
        from fastmcp.server.context import DeclinedElicitation
        from thegent.mcp_tools_elicitation import elicit_confirmation

        declined = MagicMock(spec=DeclinedElicitation)
        declined.action = "decline"
        ctx = _make_ctx(elicit_return=declined)

        result = await elicit_confirmation(ctx, "Proceed?")
        assert result is None

    @pytest.mark.asyncio
    async def test_cancelled_returns_none(self) -> None:
        """CancelledElicitation returns None. # @trace FR-MCP-ELICIT-001"""
        from fastmcp.server.context import CancelledElicitation
        from thegent.mcp_tools_elicitation import elicit_confirmation

        cancelled = MagicMock(spec=CancelledElicitation)
        cancelled.action = "cancel"
        ctx = _make_ctx(elicit_return=cancelled)

        result = await elicit_confirmation(ctx, "Proceed?")
        assert result is None

    @pytest.mark.asyncio
    async def test_no_elicit_method_returns_none_with_warning(self) -> None:
        """Missing ctx.elicit returns None and emits a UserWarning. # @trace FR-MCP-ELICIT-001"""
        from thegent.mcp_tools_elicitation import elicit_confirmation

        ctx = MagicMock(spec=[])  # no .elicit attribute

        with pytest.warns(UserWarning, match="ctx.elicit is not available"):
            result = await elicit_confirmation(ctx, "Proceed?")
        assert result is None


# ---------------------------------------------------------------------------
# Tests for elicit_choice
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestElicitChoice:
    """Tests for the elicit_choice primitive. # @trace FR-MCP-ELICIT-002"""

    @pytest.mark.asyncio
    async def test_accepted_returns_selected_option(self) -> None:
        """AcceptedElicitation returns the chosen string. # @trace FR-MCP-ELICIT-002"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import elicit_choice

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = "claude-3"
        options = ["gpt-4", "claude-3", "gemini"]
        ctx = _make_ctx(elicit_return=accepted)

        result = await elicit_choice(ctx, "Select model:", options)
        assert result == "claude-3"
        ctx.elicit.assert_awaited_once_with("Select model:", options)

    @pytest.mark.asyncio
    async def test_declined_returns_none(self) -> None:
        """Declined elicitation returns None. # @trace FR-MCP-ELICIT-002"""
        from fastmcp.server.context import DeclinedElicitation
        from thegent.mcp_tools_elicitation import elicit_choice

        declined = MagicMock(spec=DeclinedElicitation)
        declined.action = "decline"
        ctx = _make_ctx(elicit_return=declined)

        result = await elicit_choice(ctx, "Pick one:", ["a", "b"])
        assert result is None

    @pytest.mark.asyncio
    async def test_cancelled_returns_none(self) -> None:
        """Cancelled elicitation returns None. # @trace FR-MCP-ELICIT-002"""
        from fastmcp.server.context import CancelledElicitation
        from thegent.mcp_tools_elicitation import elicit_choice

        cancelled = MagicMock(spec=CancelledElicitation)
        cancelled.action = "cancel"
        ctx = _make_ctx(elicit_return=cancelled)

        result = await elicit_choice(ctx, "Pick one:", ["a", "b"])
        assert result is None

    def test_empty_options_raises_value_error(self) -> None:
        """Empty options list raises ValueError immediately (no ctx call). # @trace FR-MCP-ELICIT-002"""
        import asyncio

        from thegent.mcp_tools_elicitation import elicit_choice

        ctx = _make_ctx()

        with pytest.raises(ValueError, match="options list must not be empty"):
            asyncio.get_event_loop().run_until_complete(elicit_choice(ctx, "Choose:", []))

    @pytest.mark.asyncio
    async def test_no_elicit_method_returns_none_with_warning(self) -> None:
        """Missing ctx.elicit returns None and emits a UserWarning. # @trace FR-MCP-ELICIT-002"""
        from thegent.mcp_tools_elicitation import elicit_choice

        ctx = MagicMock(spec=[])

        with pytest.warns(UserWarning, match="ctx.elicit is not available"):
            result = await elicit_choice(ctx, "Pick:", ["x", "y"])
        assert result is None


# ---------------------------------------------------------------------------
# Tests for elicit_text
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestElicitText:
    """Tests for the elicit_text primitive. # @trace FR-MCP-ELICIT-003"""

    @pytest.mark.asyncio
    async def test_accepted_returns_text(self) -> None:
        """AcceptedElicitation with str data returns the string. # @trace FR-MCP-ELICIT-003"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import elicit_text

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = "/home/user/project"
        ctx = _make_ctx(elicit_return=accepted)

        result = await elicit_text(ctx, "Enter working directory:")
        assert result == "/home/user/project"
        ctx.elicit.assert_awaited_once_with("Enter working directory:", str)

    @pytest.mark.asyncio
    async def test_placeholder_injected_into_prompt(self) -> None:
        """Placeholder is appended to prompt message. # @trace FR-MCP-ELICIT-003"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import elicit_text

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = "/tmp/work"
        ctx = _make_ctx(elicit_return=accepted)

        await elicit_text(ctx, "Enter path:", placeholder="/tmp/example")
        # Verify the prompt sent to ctx.elicit includes the placeholder
        called_prompt = ctx.elicit.call_args[0][0]
        assert "Enter path:" in called_prompt
        assert "/tmp/example" in called_prompt

    @pytest.mark.asyncio
    async def test_no_placeholder_prompt_unchanged(self) -> None:
        """Without placeholder, prompt is sent as-is. # @trace FR-MCP-ELICIT-003"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import elicit_text

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = "hello"
        ctx = _make_ctx(elicit_return=accepted)

        await elicit_text(ctx, "Type something:")
        called_prompt = ctx.elicit.call_args[0][0]
        assert called_prompt == "Type something:"

    @pytest.mark.asyncio
    async def test_declined_returns_none(self) -> None:
        """Declined elicitation returns None. # @trace FR-MCP-ELICIT-003"""
        from fastmcp.server.context import DeclinedElicitation
        from thegent.mcp_tools_elicitation import elicit_text

        declined = MagicMock(spec=DeclinedElicitation)
        declined.action = "decline"
        ctx = _make_ctx(elicit_return=declined)

        result = await elicit_text(ctx, "Enter value:")
        assert result is None

    @pytest.mark.asyncio
    async def test_no_elicit_method_returns_none_with_warning(self) -> None:
        """Missing ctx.elicit returns None and emits a UserWarning. # @trace FR-MCP-ELICIT-003"""
        from thegent.mcp_tools_elicitation import elicit_text

        ctx = MagicMock(spec=[])

        with pytest.warns(UserWarning, match="ctx.elicit is not available"):
            result = await elicit_text(ctx, "Enter value:")
        assert result is None


# ---------------------------------------------------------------------------
# Tests for MCP tool wrappers (registered via register_elicitation_tools)
# ---------------------------------------------------------------------------


def _build_mcp_with_elicitation_tools() -> Any:
    """Instantiate a FastMCP app with elicitation tools registered."""
    from fastmcp import FastMCP
    from thegent.mcp_tools_elicitation import register_elicitation_tools

    mcp_app = FastMCP("test-elicitation")
    register_elicitation_tools(mcp_app)
    return mcp_app


@pytest.mark.unit
class TestMCPToolConfirmation:
    """Tests for thegent_elicit_confirmation MCP tool wrapper. # @trace FR-MCP-ELICIT-004"""

    @pytest.mark.asyncio
    async def test_confirmation_accepted_true(self) -> None:
        """Tool returns confirmed=true when elicit_confirmation returns True. # @trace FR-MCP-ELICIT-004"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = True
        ctx = _make_ctx(elicit_return=accepted)

        result = await tool_fns["thegent_elicit_confirmation"](message="Deploy?", ctx=ctx)
        data = _json_content(result)
        assert data["confirmed"] is True
        assert data["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_confirmation_declined(self) -> None:
        """Tool returns confirmed=null and status declined_or_cancelled when user declines. # @trace FR-MCP-ELICIT-004"""
        from fastmcp.server.context import DeclinedElicitation
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        declined = MagicMock(spec=DeclinedElicitation)
        declined.action = "decline"
        ctx = _make_ctx(elicit_return=declined)

        result = await tool_fns["thegent_elicit_confirmation"](message="Deploy?", ctx=ctx)
        data = _json_content(result)
        assert data["confirmed"] is None
        assert data["status"] == "declined_or_cancelled"

    @pytest.mark.asyncio
    async def test_confirmation_no_ctx(self) -> None:
        """Tool returns unavailable status when ctx is None. # @trace FR-MCP-ELICIT-004"""
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        result = await tool_fns["thegent_elicit_confirmation"](message="Proceed?", ctx=None)
        data = _json_content(result)
        assert data["confirmed"] is None
        assert data["status"] == "unavailable"


@pytest.mark.unit
class TestMCPToolChoice:
    """Tests for thegent_elicit_choice MCP tool wrapper. # @trace FR-MCP-ELICIT-005"""

    @pytest.mark.asyncio
    async def test_choice_accepted(self) -> None:
        """Tool returns chosen option when accepted. # @trace FR-MCP-ELICIT-005"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = "gemini"
        ctx = _make_ctx(elicit_return=accepted)

        result = await tool_fns["thegent_elicit_choice"](message="Select model:", options=["gpt-4", "gemini"], ctx=ctx)
        data = _json_content(result)
        assert data["choice"] == "gemini"
        assert data["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_choice_empty_options_returns_error(self) -> None:
        """Empty options returns error payload without calling elicit. # @trace FR-MCP-ELICIT-005"""
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        ctx = _make_ctx()
        result = await tool_fns["thegent_elicit_choice"](message="Pick:", options=[], ctx=ctx)
        data = _json_content(result)
        assert "error" in data
        assert data["choice"] is None

    @pytest.mark.asyncio
    async def test_choice_no_ctx(self) -> None:
        """ctx=None returns unavailable status. # @trace FR-MCP-ELICIT-005"""
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        result = await tool_fns["thegent_elicit_choice"](message="Pick:", options=["a", "b"], ctx=None)
        data = _json_content(result)
        assert data["choice"] is None
        assert data["status"] == "unavailable"


@pytest.mark.unit
class TestMCPToolText:
    """Tests for thegent_elicit_text MCP tool wrapper. # @trace FR-MCP-ELICIT-006"""

    @pytest.mark.asyncio
    async def test_text_accepted(self) -> None:
        """Tool returns entered text when accepted. # @trace FR-MCP-ELICIT-006"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = "my-project"
        ctx = _make_ctx(elicit_return=accepted)

        result = await tool_fns["thegent_elicit_text"](message="Enter project name:", ctx=ctx)
        data = _json_content(result)
        assert data["text"] == "my-project"
        assert data["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_text_with_placeholder(self) -> None:
        """Placeholder is forwarded to elicit_text. # @trace FR-MCP-ELICIT-006"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = "/tmp/result"
        ctx = _make_ctx(elicit_return=accepted)

        result = await tool_fns["thegent_elicit_text"](message="Enter path:", placeholder="/tmp/example", ctx=ctx)
        data = _json_content(result)
        assert data["text"] == "/tmp/result"
        assert data["status"] == "accepted"
        # Verify the prompt passed to ctx.elicit contains the placeholder
        called_prompt = ctx.elicit.call_args[0][0]
        assert "/tmp/example" in called_prompt

    @pytest.mark.asyncio
    async def test_text_declined_returns_null(self) -> None:
        """Declined returns text=null. # @trace FR-MCP-ELICIT-006"""
        from fastmcp.server.context import DeclinedElicitation
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        declined = MagicMock(spec=DeclinedElicitation)
        declined.action = "decline"
        ctx = _make_ctx(elicit_return=declined)

        result = await tool_fns["thegent_elicit_text"](message="Enter value:", ctx=ctx)
        data = _json_content(result)
        assert data["text"] is None
        assert data["status"] == "declined_or_cancelled"

    @pytest.mark.asyncio
    async def test_text_no_ctx(self) -> None:
        """ctx=None returns unavailable status. # @trace FR-MCP-ELICIT-006"""
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_elicitation_tools(mock_mcp)

        result = await tool_fns["thegent_elicit_text"](message="Enter value:", ctx=None)
        data = _json_content(result)
        assert data["text"] is None
        assert data["status"] == "unavailable"


# ---------------------------------------------------------------------------
# Integration: register_elicitation_tools with real FastMCP instance
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRegisterElicitationTools:
    """Integration tests: register_elicitation_tools wires tools on FastMCP. # @trace FR-MCP-ELICIT-007"""

    def test_registration_succeeds(self) -> None:
        """register_elicitation_tools completes without raising. # @trace FR-MCP-ELICIT-007"""
        from fastmcp import FastMCP
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        app = FastMCP("test-reg")
        register_elicitation_tools(app)  # must not raise

    @pytest.mark.asyncio
    async def test_all_three_tools_registered(self) -> None:
        """All three elicitation tools appear in the FastMCP tool registry. # @trace FR-MCP-ELICIT-007"""
        from fastmcp import FastMCP
        from thegent.mcp_tools_elicitation import register_elicitation_tools

        app = FastMCP("test-reg2")
        register_elicitation_tools(app)

        tools = await app.list_tools()
        registered_names = {t.name for t in tools}
        assert "thegent_elicit_confirmation" in registered_names
        assert "thegent_elicit_choice" in registered_names
        assert "thegent_elicit_text" in registered_names
