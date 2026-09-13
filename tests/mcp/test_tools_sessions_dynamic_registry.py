from __future__ import annotations

import orjson as json
import pytest

import thegent.mcp.server as mcp_server

tools_sessions = mcp_server._server_tools_sessions


def _noop_send_impl(session_id: str, message: str, msg_type: str) -> tuple[bool, str]:
    return True, f"{session_id}:{msg_type}:{message}"


def test_dynamic_tool_register_list_and_invoke_flow() -> None:
    tools_sessions.reset_dynamic_registry_for_tests()

    register = tools_sessions.session_send_impl(
        session_id="sess-1",
        message=json.dumps(
            {
                "name": "lookup_weather",
                "description": "Weather lookup",
                "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}},
            }
        ),
        msg_type="dynamic_tool_register",
        send_impl=_noop_send_impl,
    )
    register_data = json.loads(register)
    assert register_data["success"] is True
    assert register_data["registered"]["name"] == "lookup_weather"

    listed = tools_sessions.session_send_impl(
        session_id="sess-1",
        message="{}",
        msg_type="dynamic_tool_list",
        send_impl=_noop_send_impl,
    )
    list_data = json.loads(listed)
    assert [tool["name"] for tool in list_data["tools"]] == ["lookup_weather"]

    invoked = tools_sessions.session_send_impl(
        session_id="sess-1",
        message=json.dumps({"name": "lookup_weather", "arguments": {"city": "SF"}}).decode(),
        msg_type="dynamic_tool_invoke",
        send_impl=_noop_send_impl,
    )
    invoke_data = json.loads(invoked)
    assert invoke_data["success"] is True
    assert invoke_data["event"]["event"] == "tool_call_requested"
    assert invoke_data["event"]["sessionId"] == "sess-1"
    assert invoke_data["event"]["name"] == "lookup_weather"
    assert invoke_data["event"]["arguments"] == {"city": "SF"}
    assert invoke_data["event"]["timeoutSeconds"] == 30.0
    assert "requestedAt" in invoke_data["event"]
    assert "expiresAt" in invoke_data["event"]

    completed = tools_sessions.session_send_impl(
        session_id="sess-1",
        message=json.dumps(
            {"callId": invoke_data["event"]["callId"], "output": {"temperature_c": 22}, "success": True}
        ),
        msg_type="dynamic_tool_complete",
        send_impl=_noop_send_impl,
    )
    complete_data = json.loads(completed)
    assert complete_data["success"] is True
    assert complete_data["event"]["event"] == "tool_call_completed"
    assert complete_data["event"]["callId"] == invoke_data["event"]["callId"]
    assert complete_data["event"]["success"] is True
    assert complete_data["event"]["output"] == {"temperature_c": 22}


def test_dynamic_tool_invoke_requires_json_object_arguments() -> None:
    tools_sessions.reset_dynamic_registry_for_tests()
    tools_sessions.session_send_impl(
        session_id="sess-2",
        message=json.dumps({"name": "alpha", "description": "alpha tool", "input_schema": {"type": "object"}}).decode(),
        msg_type="dynamic_tool_register",
        send_impl=_noop_send_impl,
    )
    with pytest.raises(ValueError, match="arguments must be a JSON object"):
        tools_sessions.session_send_impl(
            session_id="sess-2",
            message=json.dumps({"name": "alpha", "arguments": "bad"}).decode(),
            msg_type="dynamic_tool_invoke",
            send_impl=_noop_send_impl,
        )


def test_dynamic_tool_invoke_rejects_non_numeric_timeout() -> None:
    tools_sessions.reset_dynamic_registry_for_tests()
    tools_sessions.session_send_impl(
        session_id="sess-2b",
        message=json.dumps({"name": "alpha", "description": "alpha tool", "input_schema": {"type": "object"}}).decode(),
        msg_type="dynamic_tool_register",
        send_impl=_noop_send_impl,
    )
    with pytest.raises(ValueError, match="timeout_seconds must be numeric"):
        tools_sessions.session_send_impl(
            session_id="sess-2b",
            message=json.dumps({"name": "alpha", "arguments": {"x": "ok"}, "timeout_seconds": "abc"}).decode(),
            msg_type="dynamic_tool_invoke",
            send_impl=_noop_send_impl,
        )


def test_dynamic_tool_complete_requires_non_empty_call_id() -> None:
    tools_sessions.reset_dynamic_registry_for_tests()
    with pytest.raises(ValueError, match="non-empty callId"):
        tools_sessions.session_send_impl(
            session_id="sess-3",
            message=json.dumps({"callId": " ", "output": {}, "success": True}).decode(),
            msg_type="dynamic_tool_complete",
            send_impl=_noop_send_impl,
        )


def test_dynamic_tool_complete_failure_roundtrip_includes_error_payload() -> None:
    tools_sessions.reset_dynamic_registry_for_tests()
    tools_sessions.session_send_impl(
        session_id="sess-4",
        message=json.dumps(
            {"name": "lookup_weather", "description": "weather tool", "input_schema": {"type": "object"}}
        ),
        msg_type="dynamic_tool_register",
        send_impl=_noop_send_impl,
    )
    invoked = tools_sessions.session_send_impl(
        session_id="sess-4",
        message=json.dumps({"name": "lookup_weather", "arguments": {"city": "SF"}}).decode(),
        msg_type="dynamic_tool_invoke",
        send_impl=_noop_send_impl,
    )
    call_id = json.loads(invoked)["event"]["callId"]
    completed = tools_sessions.session_send_impl(
        session_id="sess-4",
        message=json.dumps(
            {"callId": call_id, "success": False, "error": {"code": "tool_error", "message": "upstream timeout"}}
        ),
        msg_type="dynamic_tool_complete",
        send_impl=_noop_send_impl,
    )
    data = json.loads(completed)
    assert data["success"] is True
    assert data["event"]["event"] == "tool_call_completed"
    assert data["event"]["callId"] == call_id
    assert data["event"]["success"] is False
    assert data["event"]["output"] is None
    assert data["event"]["error"] == {"code": "tool_error", "message": "upstream timeout"}


def test_dynamic_tool_complete_failure_requires_error_or_output() -> None:
    tools_sessions.reset_dynamic_registry_for_tests()
    tools_sessions.session_send_impl(
        session_id="sess-5",
        message=json.dumps(
            {"name": "lookup_weather", "description": "weather tool", "input_schema": {"type": "object"}}
        ),
        msg_type="dynamic_tool_register",
        send_impl=_noop_send_impl,
    )
    invoked = tools_sessions.session_send_impl(
        session_id="sess-5",
        message=json.dumps({"name": "lookup_weather", "arguments": {"city": "SF"}}).decode(),
        msg_type="dynamic_tool_invoke",
        send_impl=_noop_send_impl,
    )
    call_id = json.loads(invoked)["event"]["callId"]
    with pytest.raises(ValueError, match="requires error or output"):
        tools_sessions.session_send_impl(
            session_id="sess-5",
            message=json.dumps({"callId": call_id, "success": False}).decode(),
            msg_type="dynamic_tool_complete",
            send_impl=_noop_send_impl,
        )


def test_dynamic_tool_complete_rejects_expired_call(monkeypatch: pytest.MonkeyPatch) -> None:
    tools_sessions.reset_dynamic_registry_for_tests()
    tools_sessions.session_send_impl(
        session_id="sess-6",
        message=json.dumps(
            {"name": "lookup_weather", "description": "weather tool", "input_schema": {"type": "object"}}
        ),
        msg_type="dynamic_tool_register",
        send_impl=_noop_send_impl,
    )

    monotonic_values = iter([200.0, 200.0, 200.2, 200.2])
    monkeypatch.setattr("thegent.mcp.dynamic_tools.time.monotonic", lambda: next(monotonic_values))
    invoked = tools_sessions.session_send_impl(
        session_id="sess-6",
        message=json.dumps({"name": "lookup_weather", "arguments": {"city": "SF"}, "timeout_seconds": 0.1}).decode(),
        msg_type="dynamic_tool_invoke",
        send_impl=_noop_send_impl,
    )
    call_id = json.loads(invoked)["event"]["callId"]
    with pytest.raises(ValueError, match="dynamic tool call expired"):
        tools_sessions.session_send_impl(
            session_id="sess-6",
            message=json.dumps({"callId": call_id, "success": True, "output": {"ok": True}}).decode(),
            msg_type="dynamic_tool_complete",
            send_impl=_noop_send_impl,
        )
