"""Lane C regressions for WL-9870..WL-9879 on JSON-RPC dispatch decomposition."""

from __future__ import annotations

import orjson as json

from thegent.protocols import jsonrpc_agent_server as server
from thegent.protocols.jsonrpc_agent_server import (
    SERVER_STATE,
    process_jsonrpc_line_full,
)


def _reset_state() -> None:
    SERVER_STATE.session_counter = 0
    SERVER_STATE.turn_counter = 0
    SERVER_STATE.approval_counter = 0
    SERVER_STATE.tool_call_counter = 0
    SERVER_STATE.sessions.clear()
    SERVER_STATE.turns.clear()
    SERVER_STATE.approvals.clear()


def _start_session() -> str:
    response, _notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "start", "method": "session/start"})
    )
    assert response is not None
    return response["result"]["session"]["id"]


def test_wl9870_health_check_request_response_shape_is_stable() -> None:
    # @trace WL-9870
    _reset_state()
    response, notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "health", "method": "health/check"})
    )
    assert notifications == []
    assert response is not None
    assert response["result"]["status"] == "ok"
    assert response["result"]["service"] == "thegent-agent-server"
    assert response["result"]["transport"] == "stdio"


def test_wl9871_config_read_request_response_shape_is_stable() -> None:
    # @trace WL-9871
    _reset_state()
    response, notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "config", "method": "config/read"})
    )
    assert notifications == []
    assert response is not None
    assert response["result"]["server"] == "thegent-agent-server"
    assert response["result"]["transport"] == "stdio"
    assert response["result"]["supported_methods"] == sorted(server.SUPPORTED_METHODS)


def test_wl9872_static_notification_mode_suppresses_response() -> None:
    # @trace WL-9872
    _reset_state()
    response, notifications = process_jsonrpc_line_full(json.dumps({"jsonrpc": "2.0", "method": "config/read"}))
    assert response is None
    assert notifications == []


def test_wl9873_session_start_request_registers_active_session() -> None:
    # @trace WL-9873
    _reset_state()
    response, notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "start", "method": "session/start"})
    )
    assert notifications == []
    assert response is not None
    session_id = response["result"]["session"]["id"]
    assert SERVER_STATE.sessions[session_id]["status"] == "active"


def test_wl9874_session_start_notification_creates_session_without_response() -> None:
    # @trace WL-9874
    _reset_state()
    response, notifications = process_jsonrpc_line_full(json.dumps({"jsonrpc": "2.0", "method": "session/start"}))
    assert response is None
    assert notifications == []
    assert len(SERVER_STATE.sessions) == 1


def test_wl9875_resume_session_request_forces_active_status() -> None:
    # @trace WL-9875
    _reset_state()
    session_id = _start_session()
    SERVER_STATE.sessions[session_id]["status"] = "paused"
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "resume",
                "method": "session/resume",
                "params": {"session_id": session_id},
            }
        )
    )
    assert notifications == []
    assert response is not None
    assert SERVER_STATE.sessions[session_id]["status"] == "active"


def test_wl9876_session_list_response_preserves_created_index_order() -> None:
    # @trace WL-9876
    _reset_state()
    first = _start_session()
    second = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "list", "method": "session/list"})
    )
    assert notifications == []
    assert response is not None
    assert [item["id"] for item in response["result"]["sessions"]] == [first, second]


def test_wl9877_session_read_response_projects_turn_entries() -> None:
    # @trace WL-9877
    _reset_state()
    session_id = _start_session()
    submit_response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "x"},
            }
        )
    )
    assert submit_response is not None
    turn_id = submit_response["result"]["turn"]["id"]
    read_response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "read",
                "method": "session/read",
                "params": {"session_id": session_id},
            }
        )
    )
    assert read_response is not None
    assert any(item["id"] == turn_id for item in read_response["result"]["turns"])
    assert notifications == []


def test_wl9878_resume_missing_session_returns_not_found_error() -> None:
    # @trace WL-9878
    _reset_state()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "resume",
                "method": "session/resume",
                "params": {"session_id": "session-404"},
            }
        )
    )
    assert notifications == []
    assert response is not None
    assert response["error"]["code"] == -32001


def test_wl9879_turn_submit_notification_keeps_side_effects_without_response() -> None:
    # @trace WL-9879
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "lane-c"},
            }
        )
    )
    assert response is None
    assert notifications
    turn_id = SERVER_STATE.sessions[session_id]["turn_ids"][0]
    assert SERVER_STATE.turns[turn_id]["status"] == "completed"
