"""Tests for WL-105: Dynamic Client Tool Registration in MCP Server.

Covers:
- DynamicToolSpec dataclass construction and field access
- DynamicToolRegistry.register_dynamic_tool() stores spec per session
- DynamicToolRegistry.register_dynamic_tool() raises ValueError on blank session_id
- DynamicToolRegistry.register_dynamic_tool() raises ValueError on blank tool name
- DynamicToolRegistry.register_dynamic_tool() raises ValueError for non-dict input_schema
- DynamicToolRegistry.register_dynamic_tool() raises ValueError on duplicate tool name per session
- DynamicToolRegistry.register_dynamic_tool() allows same tool name in different sessions
- DynamicToolRegistry.list_dynamic_tools() returns empty list for unknown session
- DynamicToolRegistry.list_dynamic_tools() returns registered specs for known session
- DynamicToolRegistry.create_tool_call() raises KeyError for unknown tool name
- DynamicToolRegistry.create_tool_call() creates PendingDynamicToolCall with unique call_id
- DynamicToolRegistry.create_tool_call() stores call in pending dict
- DynamicToolRegistry.get_pending_call() returns existing pending call
- DynamicToolRegistry.get_pending_call() raises KeyError for unknown call_id
- DynamicToolRegistry.pending_calls_for_session() returns only calls for given session
- DynamicToolRegistry.resolve_tool_call() returns DynamicToolCallResult with correct fields
- DynamicToolRegistry.resolve_tool_call() removes call from pending dict
- DynamicToolRegistry.resolve_tool_call() raises KeyError for unknown call_id (fail-loud)
- DynamicToolRegistry.resolve_tool_call_for_session() raises KeyError when session_id mismatch
- DynamicToolRegistry.clear_session() removes tools and pending calls for session
- DynamicToolRegistry.tool_call_requested_event() returns correct event dict shape
- DynamicToolRegistry.tool_call_completed_event() returns correct event dict shape (success)
- DynamicToolRegistry.tool_call_completed_event() includes error key when error is set
- session_send_impl dynamic_tool_register msg_type registers tool and returns JSON
- session_send_impl dynamic_tool_list msg_type lists tools for session
- session_send_impl dynamic_tool_invoke msg_type creates call and emits event
- session_send_impl dynamic_tool_complete msg_type resolves call and emits event
- session_send_impl dynamic_tool_complete raises ValueError on empty callId
- session_send_impl dynamic_tool_complete raises ValueError when failed but no error/output
- MCP tool thegent_register_tool delegates to registry and returns JSON
- MCP tool thegent_list_dynamic_tools returns tool list for session
- MCP tool thegent_complete_tool_call resolves pending call and returns event
- MCP tool thegent_complete_tool_call raises KeyError on unknown call_id

# @trace WL-105
"""

from __future__ import annotations

import asyncio

import orjson as json
import pytest

# ---------------------------------------------------------------------------
# Import tools_sessions (dynamically loaded module, not a package).
# server.py loads it with importlib under the name
# "thegent.mcp._server_tools_sessions".  Importing thegent.mcp.server first
# ensures the module is in sys.modules under the canonical name, so both the
# MCP tool callables in server.py and the test share the same registry instance.
# ---------------------------------------------------------------------------
import thegent.mcp.server as _mcp_server  # noqa: E402 -- must run after sys.modules check
from thegent.mcp.dynamic_tools import (
    DynamicToolCallResult,
    DynamicToolRegistry,
    DynamicToolSpec,
    PendingDynamicToolCall,
)

_tools_sessions = _mcp_server._server_tools_sessions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_spec(name: str = "my_tool", description: str = "desc", schema: dict | None = None) -> DynamicToolSpec:
    return DynamicToolSpec(name=name, description=description, input_schema=schema or {"type": "object"})


def _make_registry_with_tool(session_id: str = "sess-1", tool_name: str = "my_tool") -> DynamicToolRegistry:
    reg = DynamicToolRegistry()
    reg.register_dynamic_tool(session_id, _make_spec(tool_name))
    return reg


# ---------------------------------------------------------------------------
# DynamicToolSpec
# ---------------------------------------------------------------------------


class TestDynamicToolSpec:
    """DynamicToolSpec dataclass construction and field access. # @trace WL-105"""

    def test_fields_accessible(self):
        # @trace WL-105
        spec = DynamicToolSpec(name="tool_a", description="does stuff", input_schema={"type": "object"})
        assert spec.name == "tool_a"
        assert spec.description == "does stuff"
        assert spec.input_schema == {"type": "object"}

    def test_frozen_raises_on_mutation(self):
        # @trace WL-105
        spec = _make_spec()
        with pytest.raises((AttributeError, TypeError)):
            spec.name = "changed"  # type: ignore[misc]

    def test_empty_input_schema_dict_allowed(self):
        # @trace WL-105
        spec = DynamicToolSpec(name="bare", description="bare tool", input_schema={})
        assert spec.input_schema == {}


# ---------------------------------------------------------------------------
# DynamicToolRegistry.register_dynamic_tool
# ---------------------------------------------------------------------------


class TestRegisterDynamicTool:
    """register_dynamic_tool validation and storage. # @trace WL-105"""

    def test_registers_and_returns_spec(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        spec = _make_spec("calc")
        result = reg.register_dynamic_tool("sess-1", spec)
        assert result is spec

    def test_blank_session_id_raises(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        with pytest.raises(ValueError, match="session_id"):
            reg.register_dynamic_tool("   ", _make_spec())

    def test_blank_tool_name_raises(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        with pytest.raises(ValueError, match="name"):
            reg.register_dynamic_tool("sess-1", DynamicToolSpec(name="  ", description="x", input_schema={}))

    def test_non_dict_schema_raises(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        with pytest.raises((ValueError, TypeError)):
            reg.register_dynamic_tool(  # type: ignore[arg-type]
                "sess-1",
                DynamicToolSpec(name="t", description="d", input_schema="bad"),  # type: ignore[arg-type]
            )

    def test_duplicate_tool_name_raises(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        reg.register_dynamic_tool("sess-1", _make_spec("dupe"))
        with pytest.raises(ValueError, match="already registered"):
            reg.register_dynamic_tool("sess-1", _make_spec("dupe"))

    def test_same_tool_name_different_sessions_allowed(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        reg.register_dynamic_tool("sess-1", _make_spec("shared"))
        reg.register_dynamic_tool("sess-2", _make_spec("shared"))
        assert len(reg.list_dynamic_tools("sess-1")) == 1
        assert len(reg.list_dynamic_tools("sess-2")) == 1

    def test_multiple_tools_per_session(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        reg.register_dynamic_tool("sess-1", _make_spec("tool_a"))
        reg.register_dynamic_tool("sess-1", _make_spec("tool_b"))
        names = {t.name for t in reg.list_dynamic_tools("sess-1")}
        assert names == {"tool_a", "tool_b"}


# ---------------------------------------------------------------------------
# DynamicToolRegistry.list_dynamic_tools
# ---------------------------------------------------------------------------


class TestListDynamicTools:
    """list_dynamic_tools returns correct results. # @trace WL-105"""

    def test_empty_for_unknown_session(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        assert reg.list_dynamic_tools("unknown") == []

    def test_returns_registered_specs(self):
        # @trace WL-105
        reg = _make_registry_with_tool("sess-1", "my_tool")
        tools = reg.list_dynamic_tools("sess-1")
        assert len(tools) == 1
        assert tools[0].name == "my_tool"

    def test_does_not_return_other_session_tools(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        reg.register_dynamic_tool("sess-a", _make_spec("tool_a"))
        reg.register_dynamic_tool("sess-b", _make_spec("tool_b"))
        names_a = {t.name for t in reg.list_dynamic_tools("sess-a")}
        assert "tool_b" not in names_a


# ---------------------------------------------------------------------------
# DynamicToolRegistry.create_tool_call
# ---------------------------------------------------------------------------


class TestCreateToolCall:
    """create_tool_call lifecycle. # @trace WL-105"""

    def test_raises_for_unknown_tool(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        with pytest.raises(KeyError, match="not registered"):
            reg.create_tool_call("sess-1", "no_such_tool", {})

    def test_returns_pending_call(self):
        # @trace WL-105
        reg = _make_registry_with_tool()
        call = reg.create_tool_call("sess-1", "my_tool", {"x": 1})
        assert isinstance(call, PendingDynamicToolCall)
        assert call.name == "my_tool"
        assert call.arguments == {"x": 1}
        assert call.session_id == "sess-1"

    def test_call_id_is_unique(self):
        # @trace WL-105
        reg = _make_registry_with_tool()
        call_a = reg.create_tool_call("sess-1", "my_tool", {})
        call_b = reg.create_tool_call("sess-1", "my_tool", {})
        assert call_a.call_id != call_b.call_id

    def test_call_stored_in_pending(self):
        # @trace WL-105
        reg = _make_registry_with_tool()
        call = reg.create_tool_call("sess-1", "my_tool", {})
        fetched = reg.get_pending_call(call.call_id)
        assert fetched.call_id == call.call_id


# ---------------------------------------------------------------------------
# DynamicToolRegistry.get_pending_call
# ---------------------------------------------------------------------------


class TestGetPendingCall:
    """get_pending_call access. # @trace WL-105"""

    def test_raises_for_unknown_call_id(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        with pytest.raises(KeyError, match="unknown dynamic call id"):
            reg.get_pending_call("does-not-exist")

    def test_returns_correct_call(self):
        # @trace WL-105
        reg = _make_registry_with_tool()
        call = reg.create_tool_call("sess-1", "my_tool", {"y": 2})
        fetched = reg.get_pending_call(call.call_id)
        assert fetched.arguments == {"y": 2}


# ---------------------------------------------------------------------------
# DynamicToolRegistry.pending_calls_for_session
# ---------------------------------------------------------------------------


class TestPendingCallsForSession:
    """pending_calls_for_session isolation. # @trace WL-105"""

    def test_returns_only_session_calls(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        reg.register_dynamic_tool("sess-1", _make_spec("tool_1"))
        reg.register_dynamic_tool("sess-2", _make_spec("tool_2"))
        call_a = reg.create_tool_call("sess-1", "tool_1", {})
        reg.create_tool_call("sess-2", "tool_2", {})
        calls_1 = reg.pending_calls_for_session("sess-1")
        assert len(calls_1) == 1
        assert calls_1[0].call_id == call_a.call_id


# ---------------------------------------------------------------------------
# DynamicToolRegistry.resolve_tool_call
# ---------------------------------------------------------------------------


class TestResolveToolCall:
    """resolve_tool_call fail-loud contract. # @trace WL-105"""

    def test_returns_result_with_output(self):
        # @trace WL-105
        reg = _make_registry_with_tool()
        call = reg.create_tool_call("sess-1", "my_tool", {})
        result = reg.resolve_tool_call(call.call_id, output="done", success=True)
        assert isinstance(result, DynamicToolCallResult)
        assert result.output == "done"
        assert result.success is True
        assert result.call_id == call.call_id

    def test_removes_from_pending(self):
        # @trace WL-105
        reg = _make_registry_with_tool()
        call = reg.create_tool_call("sess-1", "my_tool", {})
        reg.resolve_tool_call(call.call_id, output="x", success=True)
        with pytest.raises(KeyError):
            reg.get_pending_call(call.call_id)

    def test_raises_for_unknown_call_id(self):
        # @trace WL-105 -- fail-loud: no silent handling of unknown call ids
        reg = DynamicToolRegistry()
        with pytest.raises(KeyError, match="unknown dynamic call id"):
            reg.resolve_tool_call("ghost-call", output=None, success=False)

    def test_failure_result(self):
        # @trace WL-105
        reg = _make_registry_with_tool()
        call = reg.create_tool_call("sess-1", "my_tool", {})
        result = reg.resolve_tool_call(call.call_id, output=None, success=False, error="timeout")
        assert result.success is False
        assert result.error == "timeout"


# ---------------------------------------------------------------------------
# DynamicToolRegistry.resolve_tool_call_for_session
# ---------------------------------------------------------------------------


class TestResolveToolCallForSession:
    """resolve_tool_call_for_session session isolation. # @trace WL-105"""

    def test_raises_on_session_mismatch(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        reg.register_dynamic_tool("sess-owner", _make_spec("t"))
        call = reg.create_tool_call("sess-owner", "t", {})
        with pytest.raises(KeyError, match="does not belong to session"):
            reg.resolve_tool_call_for_session(
                session_id="sess-other",
                call_id=call.call_id,
                output="x",
                success=True,
            )

    def test_resolves_with_matching_session(self):
        # @trace WL-105
        reg = _make_registry_with_tool("sess-1")
        call = reg.create_tool_call("sess-1", "my_tool", {})
        result = reg.resolve_tool_call_for_session(
            session_id="sess-1",
            call_id=call.call_id,
            output="ok",
            success=True,
        )
        assert result.success is True


# ---------------------------------------------------------------------------
# DynamicToolRegistry.clear_session
# ---------------------------------------------------------------------------


class TestClearSession:
    """clear_session removes all state for the session. # @trace WL-105"""

    def test_clears_tools(self):
        # @trace WL-105
        reg = _make_registry_with_tool("sess-1")
        reg.clear_session("sess-1")
        assert reg.list_dynamic_tools("sess-1") == []

    def test_clears_pending_calls(self):
        # @trace WL-105
        reg = _make_registry_with_tool("sess-1")
        call = reg.create_tool_call("sess-1", "my_tool", {})
        reg.clear_session("sess-1")
        with pytest.raises(KeyError):
            reg.get_pending_call(call.call_id)

    def test_clear_unknown_session_is_noop(self):
        # @trace WL-105
        reg = DynamicToolRegistry()
        reg.clear_session("never-existed")  # must not raise


# ---------------------------------------------------------------------------
# Event shape helpers
# ---------------------------------------------------------------------------


class TestEventHelpers:
    """tool_call_requested_event and tool_call_completed_event shapes. # @trace WL-105"""

    def test_requested_event_shape(self):
        # @trace WL-105
        reg = _make_registry_with_tool()
        call = reg.create_tool_call("sess-1", "my_tool", {"k": "v"})
        event = DynamicToolRegistry.tool_call_requested_event(call)
        assert event["event"] == "tool_call_requested"
        assert event["callId"] == call.call_id
        assert event["sessionId"] == "sess-1"
        assert event["name"] == "my_tool"
        assert event["arguments"] == {"k": "v"}

    def test_completed_event_success_shape(self):
        # @trace WL-105
        result = DynamicToolCallResult(call_id="cid-1", output="result text", success=True)
        event = DynamicToolRegistry.tool_call_completed_event(result)
        assert event["event"] == "tool_call_completed"
        assert event["callId"] == "cid-1"
        assert event["output"] == "result text"
        assert event["success"] is True
        assert "error" not in event

    def test_completed_event_failure_includes_error(self):
        # @trace WL-105
        result = DynamicToolCallResult(call_id="cid-2", output=None, success=False, error="timeout")
        event = DynamicToolRegistry.tool_call_completed_event(result)
        assert event["success"] is False
        assert event["error"] == "timeout"


# ---------------------------------------------------------------------------
# session_send_impl dynamic_tool_* msg_type integration
# ---------------------------------------------------------------------------


class TestSessionSendImplDynamicTools:
    """session_send_impl routing for dynamic tool msg_types. # @trace WL-105"""

    def setup_method(self):
        _tools_sessions.reset_dynamic_registry_for_tests()

    def _send(self, session_id: str, message: str, msg_type: str) -> dict:
        def _fake_send(sid, msg, msg_type="reprompt"):
            return True, "ok"

        raw = _tools_sessions.session_send_impl(
            session_id=session_id,
            message=message,
            msg_type=msg_type,
            send_impl=_fake_send,
        )
        return json.loads(raw)

    def test_register_returns_success(self):
        # @trace WL-105
        payload = json.dumps(
            {
                "name": "calc",
                "description": "a calculator",
                "input_schema": {"type": "object"},
            }
        ).decode()
        result = self._send("sess-1", payload, "dynamic_tool_register")
        assert result["success"] is True
        assert result["registered"]["name"] == "calc"

    def test_list_returns_registered_tools(self):
        # @trace WL-105
        reg_payload = json.dumps({"name": "t1", "description": "t1", "input_schema": {}}).decode()
        self._send("sess-1", reg_payload, "dynamic_tool_register")
        result = self._send("sess-1", "{}", "dynamic_tool_list")
        assert result["success"] is True
        assert any(t["name"] == "t1" for t in result["tools"])

    def test_invoke_creates_pending_call_event(self):
        # @trace WL-105
        reg_payload = json.dumps({"name": "lookup", "description": "lookup", "input_schema": {}}).decode()
        self._send("sess-1", reg_payload, "dynamic_tool_register")
        invoke_payload = json.dumps({"name": "lookup", "arguments": {"q": "hello"}}).decode()
        result = self._send("sess-1", invoke_payload, "dynamic_tool_invoke")
        assert result["success"] is True
        assert result["event"]["event"] == "tool_call_requested"
        assert result["event"]["name"] == "lookup"

    def test_complete_resolves_pending_call(self):
        # @trace WL-105
        reg_payload = json.dumps({"name": "fetch", "description": "fetch", "input_schema": {}}).decode()
        self._send("sess-1", reg_payload, "dynamic_tool_register")
        invoke_payload = json.dumps({"name": "fetch", "arguments": {}}).decode()
        invoke_result = self._send("sess-1", invoke_payload, "dynamic_tool_invoke")
        call_id = invoke_result["event"]["callId"]
        complete_payload = json.dumps({"callId": call_id, "output": "fetched!", "success": True}).decode()
        result = self._send("sess-1", complete_payload, "dynamic_tool_complete")
        assert result["success"] is True
        assert result["event"]["event"] == "tool_call_completed"
        assert result["event"]["output"] == "fetched!"

    def test_complete_empty_call_id_raises(self):
        # @trace WL-105
        payload = json.dumps({"callId": "", "output": "x", "success": True}).decode()
        with pytest.raises(ValueError, match="callId"):
            self._send("sess-1", payload, "dynamic_tool_complete")

    def test_complete_failed_no_error_raises(self):
        # @trace WL-105
        reg_payload = json.dumps({"name": "bad_tool", "description": "bad", "input_schema": {}}).decode()
        self._send("sess-1", reg_payload, "dynamic_tool_register")
        invoke_payload = json.dumps({"name": "bad_tool", "arguments": {}}).decode()
        invoke_result = self._send("sess-1", invoke_payload, "dynamic_tool_invoke")
        call_id = invoke_result["event"]["callId"]
        complete_payload = json.dumps({"callId": call_id, "success": False}).decode()
        with pytest.raises(ValueError):
            self._send("sess-1", complete_payload, "dynamic_tool_complete")


# ---------------------------------------------------------------------------
# MCP tool callables (direct async invocation)
# ---------------------------------------------------------------------------


class TestMCPToolCallables:
    """Direct async invocation of the MCP tool functions. # @trace WL-105"""

    def setup_method(self):
        _tools_sessions.reset_dynamic_registry_for_tests()

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_thegent_register_tool_returns_json(self):
        # @trace WL-105
        from thegent.mcp.server import thegent_register_tool

        raw = self._run(
            thegent_register_tool(
                session_id="sess-x",
                name="weather",
                description="get weather",
                input_schema={
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                },
            )
        )
        result = json.loads(raw)
        assert result["success"] is True
        assert result["registered"]["name"] == "weather"

    def test_thegent_list_dynamic_tools_returns_tools(self):
        # @trace WL-105
        from thegent.mcp.server import thegent_list_dynamic_tools, thegent_register_tool

        self._run(
            thegent_register_tool(
                session_id="sess-y",
                name="echo",
                description="echoes",
                input_schema={},
            )
        )
        raw = self._run(thegent_list_dynamic_tools(session_id="sess-y"))
        result = json.loads(raw)
        assert result["session_id"] == "sess-y"
        assert any(t["name"] == "echo" for t in result["tools"])

    def test_thegent_complete_tool_call_resolves(self):
        # @trace WL-105
        from thegent.mcp.server import thegent_complete_tool_call, thegent_register_tool

        self._run(
            thegent_register_tool(
                session_id="sess-z",
                name="action",
                description="does action",
                input_schema={},
            )
        )
        call = _tools_sessions._dynamic_registry.create_tool_call("sess-z", "action", {})
        raw = self._run(
            thegent_complete_tool_call(
                session_id="sess-z",
                call_id=call.call_id,
                output="completed",
                success=True,
            )
        )
        result = json.loads(raw)
        assert result["success"] is True
        assert result["event"]["event"] == "tool_call_completed"
        assert result["event"]["output"] == "completed"

    def test_thegent_complete_tool_call_unknown_id_raises(self):
        # @trace WL-105 -- fail-loud: unknown call_id must raise, not return default
        from thegent.mcp.server import thegent_complete_tool_call

        with pytest.raises(KeyError):
            self._run(
                thegent_complete_tool_call(
                    session_id="sess-z",
                    call_id="ghost-id-999",
                    output="x",
                    success=True,
                )
            )
