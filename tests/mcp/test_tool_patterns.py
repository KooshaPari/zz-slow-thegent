"""Tests for FastMCP reusable tool patterns.

Covers:
- confirm_before_action: proceeds on yes, raises ToolAborted on no
- confirm_before_action: no ctx runs without confirmation (fail-open)
- progress_with_fallback: ctx.report_progress called at each step
- progress_with_fallback: fallback dict returned on unexpected exception
- choice_with_retry: retries on declined/invalid selection
- choice_with_retry: raises ToolAborted after max retries exhausted
- retry_on_error: retries specified number of times then re-raises
- retry_on_error: does not retry on non-matching exception types
- ToolAborted: is an Exception subclass

# @trace FR-MCP-PATTERNS-001
# @trace FR-MCP-PATTERNS-002
# @trace FR-MCP-PATTERNS-003
# @trace FR-MCP-PATTERNS-004
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

fastmcp = pytest.importorskip("fastmcp", reason="fastmcp required for tool pattern tests")


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


def _make_ctx(
    elicit_return: Any = None,
    has_elicit: bool = True,
    has_report_progress: bool = True,
) -> MagicMock:
    """Build a mock FastMCP Context with configurable attributes."""
    ctx = MagicMock()
    if has_elicit:
        ctx.elicit = AsyncMock(return_value=elicit_return)
    else:
        del ctx.elicit
    if has_report_progress:
        ctx.report_progress = AsyncMock(return_value=None)
        ctx.info = AsyncMock(return_value=None)
    else:
        del ctx.report_progress
    return ctx


# ---------------------------------------------------------------------------
# Tests for ToolAborted
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestToolAborted:
    """Tests for the ToolAborted exception class. # @trace FR-MCP-PATTERNS-001"""

    def test_tool_aborted_is_exception(self) -> None:
        """ToolAborted is a subclass of Exception. # @trace FR-MCP-PATTERNS-001"""
        from thegent.mcp_tool_patterns import ToolAborted

        assert issubclass(ToolAborted, Exception)

    def test_tool_aborted_message(self) -> None:
        """ToolAborted carries the message. # @trace FR-MCP-PATTERNS-001"""
        from thegent.mcp_tool_patterns import ToolAborted

        exc = ToolAborted("User said no")
        assert "User said no" in str(exc)

    def test_tool_aborted_can_be_caught_as_exception(self) -> None:
        """ToolAborted is catchable as a plain Exception. # @trace FR-MCP-PATTERNS-001"""
        from thegent.mcp_tool_patterns import ToolAborted

        with pytest.raises(ToolAborted):
            raise ToolAborted("abort!")


# ---------------------------------------------------------------------------
# Tests for confirm_before_action
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConfirmBeforeAction:
    """Tests for the confirm_before_action decorator. # @trace FR-MCP-PATTERNS-001"""

    @pytest.mark.asyncio
    async def test_proceeds_when_user_confirms(self) -> None:
        """Wrapped function runs when elicitation returns True. # @trace FR-MCP-PATTERNS-001"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tool_patterns import confirm_before_action

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = True
        ctx = _make_ctx(elicit_return=accepted)

        call_tracker: list[str] = []

        @confirm_before_action("Do the thing {name}?")
        async def my_tool(name: str, ctx: Any = None) -> str:
            call_tracker.append("called")
            return f"done: {name}"

        result = await my_tool(name="test", ctx=ctx)
        assert result == "done: test"
        assert "called" in call_tracker

    @pytest.mark.asyncio
    async def test_raises_tool_aborted_when_user_declines(self) -> None:
        """ToolAborted is raised when elicitation returns False. # @trace FR-MCP-PATTERNS-001"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tool_patterns import ToolAborted, confirm_before_action

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = False
        ctx = _make_ctx(elicit_return=accepted)

        call_tracker: list[str] = []

        @confirm_before_action("Delete {item_id}?")
        async def delete_tool(item_id: str, ctx: Any = None) -> str:
            call_tracker.append("called")
            return "deleted"

        with pytest.raises(ToolAborted):
            await delete_tool(item_id="abc-123", ctx=ctx)
        assert "called" not in call_tracker

    @pytest.mark.asyncio
    async def test_proceeds_when_elicitation_cancelled(self) -> None:
        """Cancelled elicitation (None) proceeds without confirmation (fail-open). # @trace FR-MCP-PATTERNS-001"""
        from fastmcp.server.context import DeclinedElicitation
        from thegent.mcp_tool_patterns import confirm_before_action

        declined = MagicMock(spec=DeclinedElicitation)
        declined.action = "decline"
        ctx = _make_ctx(elicit_return=declined)

        call_tracker: list[str] = []

        @confirm_before_action("Do risky thing?")
        async def risky_tool(ctx: Any = None) -> str:
            call_tracker.append("called")
            return "ran"

        result = await risky_tool(ctx=ctx)
        assert result == "ran"
        assert "called" in call_tracker

    @pytest.mark.asyncio
    async def test_no_ctx_proceeds_without_confirmation(self) -> None:
        """ctx=None runs the function without asking for confirmation. # @trace FR-MCP-PATTERNS-001"""
        from thegent.mcp_tool_patterns import confirm_before_action

        call_tracker: list[str] = []

        @confirm_before_action("Delete {resource}?")
        async def delete_tool(resource: str, ctx: Any = None) -> str:
            call_tracker.append("called")
            return f"deleted: {resource}"

        result = await delete_tool(resource="foo", ctx=None)
        assert result == "deleted: foo"
        assert "called" in call_tracker

    @pytest.mark.asyncio
    async def test_description_format_string_interpolated(self) -> None:
        """Format string uses kwargs from the decorated function. # @trace FR-MCP-PATTERNS-001"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tool_patterns import confirm_before_action

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = True
        ctx = _make_ctx(elicit_return=accepted)

        @confirm_before_action("Delete session {session_id}?")
        async def delete_session(session_id: str, ctx: Any = None) -> str:
            return "ok"

        await delete_session(session_id="sess-42", ctx=ctx)
        called_prompt = ctx.elicit.call_args[0][0]
        assert "sess-42" in called_prompt

    @pytest.mark.asyncio
    async def test_description_format_partial_missing_key_uses_raw(self) -> None:
        """Missing format key falls back to unformatted description. # @trace FR-MCP-PATTERNS-001"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tool_patterns import confirm_before_action

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = True
        ctx = _make_ctx(elicit_return=accepted)

        @confirm_before_action("Delete {nonexistent_key}?")
        async def my_tool(ctx: Any = None) -> str:
            return "ok"

        result = await my_tool(ctx=ctx)
        assert result == "ok"
        called_prompt = ctx.elicit.call_args[0][0]
        assert "Delete" in called_prompt


# ---------------------------------------------------------------------------
# Tests for progress_with_fallback
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProgressWithFallback:
    """Tests for the progress_with_fallback decorator. # @trace FR-MCP-PATTERNS-002"""

    @pytest.mark.asyncio
    async def test_report_progress_called_at_each_step(self) -> None:
        """ctx.report_progress is called once per report_step invocation. # @trace FR-MCP-PATTERNS-002"""
        from thegent.mcp_tool_patterns import progress_with_fallback

        ctx = _make_ctx()

        @progress_with_fallback(total_steps=3)
        async def my_tool(ctx: Any = None, report_step: Any = None) -> str:
            await report_step(1, "step one")
            await report_step(2, "step two")
            await report_step(3, "step three")
            return "done"

        result = await my_tool(ctx=ctx)
        assert result == "done"
        assert ctx.report_progress.await_count == 3

    @pytest.mark.asyncio
    async def test_fallback_returned_on_unexpected_exception(self) -> None:
        """Unexpected exception returns fallback dict instead of raising. # @trace FR-MCP-PATTERNS-002"""
        from thegent.mcp_tool_patterns import progress_with_fallback

        ctx = _make_ctx()

        @progress_with_fallback(total_steps=5, fallback_result="fallback_val")
        async def broken_tool(ctx: Any = None, report_step: Any = None) -> str:
            await report_step(1)
            raise RuntimeError("unexpected failure")

        result = await broken_tool(ctx=ctx)
        assert result["fallback"] is True
        assert result["result"] == "fallback_val"
        assert "unexpected failure" in result["error"]

    @pytest.mark.asyncio
    async def test_tool_aborted_propagates_through_fallback(self) -> None:
        """ToolAborted propagates without being swallowed by the fallback handler. # @trace FR-MCP-PATTERNS-002"""
        from thegent.mcp_tool_patterns import ToolAborted, progress_with_fallback

        ctx = _make_ctx()

        @progress_with_fallback(total_steps=3)
        async def tool_that_aborts(ctx: Any = None, report_step: Any = None) -> str:
            await report_step(1)
            raise ToolAborted("user aborted mid-way")

        with pytest.raises(ToolAborted):
            await tool_that_aborts(ctx=ctx)

    @pytest.mark.asyncio
    async def test_no_ctx_report_step_is_noop(self) -> None:
        """report_step is a no-op when ctx is None. # @trace FR-MCP-PATTERNS-002"""
        from thegent.mcp_tool_patterns import progress_with_fallback

        @progress_with_fallback(total_steps=5)
        async def my_tool(ctx: Any = None, report_step: Any = None) -> str:
            await report_step(1, "step 1")
            await report_step(2, "step 2")
            return "ok"

        result = await my_tool(ctx=None)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_progress_fraction_correct(self) -> None:
        """report_progress receives correct progress fraction. # @trace FR-MCP-PATTERNS-002"""
        from thegent.mcp_tool_patterns import progress_with_fallback

        ctx = _make_ctx()

        @progress_with_fallback(total_steps=4)
        async def my_tool(ctx: Any = None, report_step: Any = None) -> str:
            await report_step(2)
            return "done"

        await my_tool(ctx=ctx)
        kwargs = ctx.report_progress.call_args[1]
        assert abs(kwargs["progress"] - 0.5) < 0.01

    @pytest.mark.asyncio
    async def test_report_step_swallows_report_progress_error(self) -> None:
        """report_progress error is swallowed by report_step, not propagated. # @trace FR-MCP-PATTERNS-002"""
        from thegent.mcp_tool_patterns import progress_with_fallback

        ctx = _make_ctx()
        ctx.report_progress = AsyncMock(side_effect=OSError("network down"))

        @progress_with_fallback(total_steps=3)
        async def my_tool(ctx: Any = None, report_step: Any = None) -> str:
            await report_step(1, "step 1")
            return "ok"

        result = await my_tool(ctx=ctx)
        assert result == "ok"


# ---------------------------------------------------------------------------
# Tests for choice_with_retry
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestChoiceWithRetry:
    """Tests for the choice_with_retry decorator. # @trace FR-MCP-PATTERNS-003"""

    @pytest.mark.asyncio
    async def test_valid_choice_proceeds(self) -> None:
        """Valid selection on first try proceeds with user_choice set. # @trace FR-MCP-PATTERNS-003"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tool_patterns import choice_with_retry

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = "medium"
        ctx = _make_ctx(elicit_return=accepted)

        @choice_with_retry(["low", "medium", "high"], "Select priority:")
        async def set_priority(ctx: Any = None, user_choice: Any = None) -> str:
            return f"priority={user_choice}"

        result = await set_priority(ctx=ctx)
        assert result == "priority=medium"

    @pytest.mark.asyncio
    async def test_retries_on_declined_selection(self) -> None:
        """Declined selection triggers retry until valid selection or abort. # @trace FR-MCP-PATTERNS-003"""
        from fastmcp.server.context import AcceptedElicitation, DeclinedElicitation
        from thegent.mcp_tool_patterns import choice_with_retry

        declined = MagicMock(spec=DeclinedElicitation)
        declined.action = "decline"
        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = "high"

        ctx = _make_ctx()
        ctx.elicit = AsyncMock(side_effect=[declined, accepted])

        @choice_with_retry(["low", "medium", "high"], "Pick:", max_retries=2)
        async def my_tool(ctx: Any = None, user_choice: Any = None) -> str:
            return f"choice={user_choice}"

        result = await my_tool(ctx=ctx)
        assert result == "choice=high"
        assert ctx.elicit.await_count == 2

    @pytest.mark.asyncio
    async def test_raises_tool_aborted_after_max_retries(self) -> None:
        """ToolAborted raised after all retries are exhausted. # @trace FR-MCP-PATTERNS-003"""
        from fastmcp.server.context import DeclinedElicitation
        from thegent.mcp_tool_patterns import ToolAborted, choice_with_retry

        declined = MagicMock(spec=DeclinedElicitation)
        declined.action = "decline"
        ctx = _make_ctx(elicit_return=declined)

        @choice_with_retry(["a", "b", "c"], "Pick:", max_retries=2)
        async def my_tool(ctx: Any = None, user_choice: Any = None) -> str:
            return "should not reach here"

        with pytest.raises(ToolAborted):
            await my_tool(ctx=ctx)
        assert ctx.elicit.await_count == 3  # 1 initial + 2 retries

    @pytest.mark.asyncio
    async def test_no_ctx_injects_none_user_choice(self) -> None:
        """Without ctx, user_choice=None is injected and tool runs. # @trace FR-MCP-PATTERNS-003"""
        from thegent.mcp_tool_patterns import choice_with_retry

        @choice_with_retry(["x", "y"], "Pick:", max_retries=1)
        async def my_tool(ctx: Any = None, user_choice: Any = None) -> str:
            return f"choice={user_choice}"

        result = await my_tool(ctx=None)
        assert result == "choice=None"

    def test_empty_options_raises_value_error(self) -> None:
        """Empty options list raises ValueError at decoration time. # @trace FR-MCP-PATTERNS-003"""
        from thegent.mcp_tool_patterns import choice_with_retry

        with pytest.raises(ValueError, match="options list must not be empty"):

            @choice_with_retry([], "Pick:")
            async def bad_tool(ctx: Any = None, user_choice: Any = None) -> str:
                return "x"

    @pytest.mark.asyncio
    async def test_retries_on_invalid_selection_not_in_options(self) -> None:
        """Invalid selection (not in options list) also triggers retry. # @trace FR-MCP-PATTERNS-003"""
        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tool_patterns import choice_with_retry

        invalid_accepted = MagicMock(spec=AcceptedElicitation)
        invalid_accepted.action = "accept"
        invalid_accepted.data = "invalid_option"

        valid_accepted = MagicMock(spec=AcceptedElicitation)
        valid_accepted.action = "accept"
        valid_accepted.data = "low"

        ctx = _make_ctx()
        ctx.elicit = AsyncMock(side_effect=[invalid_accepted, valid_accepted])

        @choice_with_retry(["low", "medium", "high"], "Pick:", max_retries=2)
        async def my_tool(ctx: Any = None, user_choice: Any = None) -> str:
            return f"choice={user_choice}"

        result = await my_tool(ctx=ctx)
        assert result == "choice=low"
        assert ctx.elicit.await_count == 2


# ---------------------------------------------------------------------------
# Tests for retry_on_error
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRetryOnError:
    """Tests for the retry_on_error decorator. # @trace FR-MCP-PATTERNS-004"""

    @pytest.mark.asyncio
    async def test_retries_specified_number_of_times(self) -> None:
        """Function is retried up to max_attempts times on matching exception. # @trace FR-MCP-PATTERNS-004"""
        from thegent.mcp_tool_patterns import retry_on_error

        attempt_counter: list[int] = [0]

        @retry_on_error(max_attempts=3, exceptions=(OSError,))
        async def flaky_tool() -> str:
            attempt_counter[0] += 1
            if attempt_counter[0] < 3:
                raise OSError("transient")
            return "success"

        result = await flaky_tool()
        assert result == "success"
        assert attempt_counter[0] == 3

    @pytest.mark.asyncio
    async def test_reraises_after_max_attempts(self) -> None:
        """Exception is re-raised after all attempts exhausted. # @trace FR-MCP-PATTERNS-004"""
        from thegent.mcp_tool_patterns import retry_on_error

        attempt_counter: list[int] = [0]

        @retry_on_error(max_attempts=2, exceptions=(ValueError,))
        async def always_fails() -> str:
            attempt_counter[0] += 1
            raise ValueError("permanent error")

        with pytest.raises(ValueError, match="permanent error"):
            await always_fails()
        assert attempt_counter[0] == 2

    @pytest.mark.asyncio
    async def test_does_not_retry_non_matching_exceptions(self) -> None:
        """Non-matching exception types are not retried. # @trace FR-MCP-PATTERNS-004"""
        from thegent.mcp_tool_patterns import retry_on_error

        attempt_counter: list[int] = [0]

        @retry_on_error(max_attempts=3, exceptions=(OSError,))
        async def raises_type_error() -> str:
            attempt_counter[0] += 1
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            await raises_type_error()
        assert attempt_counter[0] == 1

    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt_no_retry(self) -> None:
        """Successful call has exactly one attempt. # @trace FR-MCP-PATTERNS-004"""
        from thegent.mcp_tool_patterns import retry_on_error

        attempt_counter: list[int] = [0]

        @retry_on_error(max_attempts=3)
        async def always_works() -> str:
            attempt_counter[0] += 1
            return "ok"

        result = await always_works()
        assert result == "ok"
        assert attempt_counter[0] == 1

    @pytest.mark.asyncio
    async def test_max_attempts_one_means_no_retry(self) -> None:
        """max_attempts=1 means no retries occur. # @trace FR-MCP-PATTERNS-004"""
        from thegent.mcp_tool_patterns import retry_on_error

        attempt_counter: list[int] = [0]

        @retry_on_error(max_attempts=1, exceptions=(RuntimeError,))
        async def fails_once() -> str:
            attempt_counter[0] += 1
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await fails_once()
        assert attempt_counter[0] == 1

    @pytest.mark.asyncio
    async def test_multiple_exception_types_all_retried(self) -> None:
        """Multiple exception types in tuple are all retried. # @trace FR-MCP-PATTERNS-004"""
        from thegent.mcp_tool_patterns import retry_on_error

        attempt_counter: list[int] = [0]
        exc_sequence = [OSError("io"), TimeoutError("timeout"), "ok"]

        @retry_on_error(max_attempts=5, exceptions=(OSError, TimeoutError))
        async def varied_failures() -> str:
            val = exc_sequence[attempt_counter[0]]
            attempt_counter[0] += 1
            if isinstance(val, Exception):
                raise val
            return val

        result = await varied_failures()
        assert result == "ok"
        assert attempt_counter[0] == 3


# ---------------------------------------------------------------------------
# Integration: register_tool_pattern_tools registers both tools
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRegisterToolPatternTools:
    """Integration tests for register_tool_pattern_tools. # @trace FR-MCP-PATTERNS-001"""

    def test_registration_succeeds(self) -> None:
        """register_tool_pattern_tools completes without raising. # @trace FR-MCP-PATTERNS-001"""
        from fastmcp import FastMCP
        from thegent.mcp_tool_patterns import register_tool_pattern_tools

        app = FastMCP("test-patterns")
        register_tool_pattern_tools(app)

    @pytest.mark.asyncio
    async def test_both_tools_registered(self) -> None:
        """Both thegent_delete_session and thegent_bulk_operation appear in registry. # @trace FR-MCP-PATTERNS-001"""
        from fastmcp import FastMCP
        from thegent.mcp_tool_patterns import register_tool_pattern_tools

        app = FastMCP("test-patterns-reg")
        register_tool_pattern_tools(app)

        tools = await app.list_tools()
        names = {t.name for t in tools}
        assert "thegent_delete_session" in names
        assert "thegent_bulk_operation" in names

    @pytest.mark.asyncio
    async def test_delete_session_confirmed(self) -> None:
        """thegent_delete_session returns deleted=true when user confirms. # @trace FR-MCP-PATTERNS-001"""
        import json

        from fastmcp.server.context import AcceptedElicitation
        from thegent.mcp_tool_patterns import register_tool_pattern_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_tool_pattern_tools(mock_mcp)

        accepted = MagicMock(spec=AcceptedElicitation)
        accepted.action = "accept"
        accepted.data = True
        ctx = _make_ctx(elicit_return=accepted)

        result = await tool_fns["thegent_delete_session"](session_id="sess-99", ctx=ctx)
        content = result.content if hasattr(result, "content") else str(result)
        if isinstance(content, list):
            text = content[0].text if hasattr(content[0], "text") else str(content[0])
        else:
            text = content
        data = json.loads(text)
        assert data["deleted"] is True
        assert data["session_id"] == "sess-99"

    @pytest.mark.asyncio
    async def test_bulk_operation_reports_progress(self) -> None:
        """thegent_bulk_operation returns processed items and calls report_progress. # @trace FR-MCP-PATTERNS-002"""
        import json

        from thegent.mcp_tool_patterns import register_tool_pattern_tools

        tool_fns: dict[str, Any] = {}
        mock_mcp = MagicMock()

        def capture_tool(**kwargs: Any) -> Any:
            def decorator(fn: Any) -> Any:
                tool_fns[fn.__name__] = fn
                return fn

            return decorator

        mock_mcp.tool = capture_tool
        register_tool_pattern_tools(mock_mcp)

        ctx = _make_ctx()

        result = await tool_fns["thegent_bulk_operation"](items=["a", "b", "c"], ctx=ctx)
        content = result.content if hasattr(result, "content") else str(result)
        if isinstance(content, list):
            text = content[0].text if hasattr(content[0], "text") else str(content[0])
        else:
            text = content
        data = json.loads(text)
        assert data["processed"] == 3
        assert ctx.report_progress.await_count == 3
