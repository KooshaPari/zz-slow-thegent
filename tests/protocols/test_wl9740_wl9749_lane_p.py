"""Lane P regressions for WL-9740..WL-9749 on turn/cancel split flow."""

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


def _submit_turn(session_id: str, *, requires_approval: bool = False) -> str:
    params: dict[str, object] = {"session_id": session_id, "input": "lane-p"}
    if requires_approval:
        params["requires_approval"] = True
        params["unified_diff"] = "--- a/x\n+++ b/x\n@@\n-old\n+new\n"
    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": params,
            }
        )
    )
    assert response is not None
    return response["result"]["turn"]["id"]


def test_wl9740_parse_helper_requires_turn_id() -> None:
    # @trace WL-9740
    turn_id, error = server._parse_turn_cancel_turn_id({})
    assert turn_id is None
    assert error is not None
    assert error.data == {"reason": "turn_id_required"}


def test_wl9741_lookup_helper_returns_existing_turn() -> None:
    # @trace WL-9741
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id)
    turn = server._lookup_turn_for_cancel(turn_id)
    assert turn is not None
    assert turn["id"] == turn_id


def test_wl9742_resolve_target_returns_not_found_payload() -> None:
    # @trace WL-9742
    _reset_state()
    turn_id, turn, error = server._resolve_turn_cancel_target(
        "x", {"turn_id": "turn-404"}
    )
    assert turn_id == "turn-404"
    assert turn is None
    assert error is not None
    assert error["error"]["code"] == -32002


def test_wl9743_handler_respects_notification_mode() -> None:
    # @trace WL-9743
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)

    response, notifications = server._handle_turn_cancel(
        False, "ignored", {"turn_id": turn_id}
    )
    assert response is None
    assert notifications == []
    assert SERVER_STATE.turns[turn_id]["status"] == "cancelled"


def test_wl9744_terminal_validator_returns_error_payload() -> None:
    # @trace WL-9744
    error = server._validate_turn_state_for_cancel("turn-1", {"status": "completed"})
    assert error is not None
    assert error["error"]["code"] == -32003


def test_wl9745_mark_cancelled_changes_status_only() -> None:
    # @trace WL-9745
    turn = {"status": "awaiting_approval"}
    server._mark_turn_cancelled(turn)
    assert turn["status"] == "cancelled"


def test_wl9746_cancel_requested_approval_updates_only_requested() -> None:
    # @trace WL-9746
    _reset_state()
    SERVER_STATE.approvals["approval-1"] = {"id": "approval-1", "status": "requested"}
    SERVER_STATE.approvals["approval-2"] = {"id": "approval-2", "status": "granted"}

    server._cancel_requested_approval_for_turn({"approval_id": "approval-1"})
    server._cancel_requested_approval_for_turn({"approval_id": "approval-2"})

    assert SERVER_STATE.approvals["approval-1"]["status"] == "cancelled"
    assert SERVER_STATE.approvals["approval-2"]["status"] == "granted"


def test_wl9747_execute_turn_cancel_applies_status_and_approval_cleanup() -> None:
    # @trace WL-9747
    _reset_state()
    SERVER_STATE.approvals["approval-1"] = {"id": "approval-1", "status": "requested"}
    turn = {"status": "in_progress", "approval_id": "approval-1"}
    server._execute_turn_cancel(turn)
    assert turn["status"] == "cancelled"
    assert SERVER_STATE.approvals["approval-1"]["status"] == "cancelled"


def test_wl9748_build_response_projects_serialized_turn() -> None:
    # @trace WL-9748
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "status": "cancelled",
        "input": "x",
        "approval_id": None,
        "tool_call_id": None,
    }
    response = server._build_turn_cancel_response(True, "req-1", turn)
    assert response is not None
    assert response["result"]["turn"]["id"] == "turn-1"
    assert response["result"]["turn"]["status"] == "cancelled"


def test_wl9749_full_handler_preserves_happy_and_failure_paths() -> None:
    # @trace WL-9749
    _reset_state()
    bad_response, bad_notifications = server._handle_turn_cancel(
        True, "req-a", {"turn_id": "turn-404"}
    )
    assert bad_response is not None
    assert bad_response["error"]["code"] == -32002
    assert bad_notifications == []

    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    ok_response, ok_notifications = server._handle_turn_cancel(
        True, "req-b", {"turn_id": turn_id}
    )
    assert ok_response is not None
    assert ok_response["result"]["turn"]["status"] == "cancelled"
    assert ok_notifications == []
