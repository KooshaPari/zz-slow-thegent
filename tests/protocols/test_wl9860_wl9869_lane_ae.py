"""Lane AE regressions for WL-9860..WL-9869 on turn/submit execution decomposition."""

from __future__ import annotations

import orjson as json
import pytest

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


def test_wl9860_build_execution_plan_creates_in_progress_turn_shape() -> None:
    # @trace WL-9860
    _reset_state()
    turn_id, turn = server._build_turn_submit_execution_plan("session-1", "hello")
    assert turn_id.startswith("turn-")
    assert turn["id"] == turn_id
    assert turn["session_id"] == "session-1"
    assert turn["status"] == "in_progress"


def test_wl9861_commit_execution_plan_registers_turn_and_session_link() -> None:
    # @trace WL-9861
    _reset_state()
    session_id = _start_session()
    session = SERVER_STATE.sessions[session_id]
    turn_id, turn = server._build_turn_submit_execution_plan(session_id, "hello")
    server._commit_turn_submit_plan(turn_id, turn, session)
    assert SERVER_STATE.turns[turn_id]["id"] == turn_id
    assert session["turn_ids"] == [turn_id]


def test_wl9862_resolve_approval_payload_requires_diff() -> None:
    # @trace WL-9862
    _reset_state()
    with pytest.raises(ValueError, match="Turn submit approval diff unresolved"):
        server._resolve_turn_submit_approval_payload("session-1", "turn-1", {"id": "turn-1"}, None, [])


def test_wl9863_resolve_completion_marks_turn_completed_and_sets_tool_call() -> None:
    # @trace WL-9863
    _reset_state()
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }
    notifications: list[dict[str, object]] = []
    server._resolve_turn_submit_completion("session-1", "turn-1", "x", turn, notifications)
    assert turn["status"] == "completed"
    assert turn["tool_call_id"] is not None


def test_wl9864_side_effects_route_to_approval_when_requested() -> None:
    # @trace WL-9864
    _reset_state()
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }
    notifications: list[dict[str, object]] = []
    payload = server._apply_turn_submit_side_effects("session-1", "turn-1", turn, "x", True, "diff", notifications)
    assert payload is not None
    assert turn["status"] == "awaiting_approval"
    assert any(item["method"] == "approval/requested" for item in notifications)


def test_wl9865_side_effects_route_to_completion_when_no_approval() -> None:
    # @trace WL-9865
    _reset_state()
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }
    notifications: list[dict[str, object]] = []
    payload = server._apply_turn_submit_side_effects("session-1", "turn-1", turn, "x", False, None, notifications)
    assert payload is None
    assert turn["status"] == "completed"
    assert any(item["method"] == "turn/completed" for item in notifications)


def test_wl9866_result_payload_contains_turn_and_optional_approval() -> None:
    # @trace WL-9866
    _reset_state()
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "completed",
        "approval_id": None,
        "tool_call_id": "tool-call-1",
    }
    without_approval = server._build_turn_submit_result_payload_flat(turn, None)
    with_approval = server._build_turn_submit_result_payload_flat(
        turn, {"id": "approval-1", "status": "requested", "diff": "d"}
    )
    assert "approval" not in without_approval
    assert with_approval["approval"]["id"] == "approval-1"


def test_wl9867_parse_failure_handler_returns_original_error_payload() -> None:
    # @trace WL-9867
    error_payload = {"jsonrpc": "2.0", "id": "req", "error": {"code": -32602}}
    assert server._handle_turn_submit_parse_failure(error_payload) is error_payload


def test_wl9868_handler_orchestrates_plan_commit_side_effects_and_response() -> None:
    # @trace WL-9868
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "ae"},
            }
        )
    )
    assert response is not None
    turn_id = response["result"]["turn"]["id"]
    assert turn_id in SERVER_STATE.turns
    assert turn_id in SERVER_STATE.sessions[session_id]["turn_ids"]
    assert notifications[0]["method"] == "turn/started"


def test_wl9869_notification_mode_preserves_side_effects_without_response() -> None:
    # @trace WL-9869
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "ae"},
            }
        )
    )
    assert response is None
    assert notifications
    turn_id = SERVER_STATE.sessions[session_id]["turn_ids"][0]
    assert SERVER_STATE.turns[turn_id]["status"] == "completed"
