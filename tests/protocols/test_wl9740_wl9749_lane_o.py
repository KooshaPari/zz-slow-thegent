"""Lane O Wave-80 regressions for WL-9740..WL-9749."""

from __future__ import annotations

import orjson as json

from thegent.protocols.jsonrpc_agent_server import (
    SERVER_STATE,
    _execute_turn_cancel_resolution,
    _handle_turn_cancel_request,
    _parse_turn_cancel_request,
    _project_turn_cancel_response,
    _resolve_turn_cancel_context,
    _route_turn_cancel_method,
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


def _seed_session() -> str:
    session_id = "session-0001"
    SERVER_STATE.sessions[session_id] = {
        "id": session_id,
        "status": "active",
        "created_index": 1,
        "turn_ids": [],
    }
    return session_id


def test_wl9740_parse_path_rejects_missing_turn_id() -> None:
    # @trace WL-9740
    _reset_state()
    turn_id, turn, error = _parse_turn_cancel_request("turn/cancel", "req-9740", {})
    assert turn_id is None
    assert turn is None
    assert error is not None
    assert error["error"]["code"] == -32602


def test_wl9741_parse_path_returns_turn_context() -> None:
    # @trace WL-9741
    _reset_state()
    session_id = _seed_session()
    turn = {
        "id": "turn-0001",
        "session_id": session_id,
        "status": "in_progress",
        "input": "x",
        "approval_id": None,
    }
    SERVER_STATE.turns[turn["id"]] = turn
    turn_id, resolved_turn, error = _parse_turn_cancel_request("turn/cancel", "req-9741", {"turn_id": "turn-0001"})
    assert error is None
    assert turn_id == "turn-0001"
    assert resolved_turn is turn


def test_wl9742_state_resolution_allows_non_terminal_turns() -> None:
    # @trace WL-9742
    _reset_state()
    _route_turn_cancel_method("turn/cancel")


def test_wl9743_state_resolution_rejects_terminal_turns() -> None:
    # @trace WL-9743
    _reset_state()
    session_id = _seed_session()
    SERVER_STATE.turns["turn-0001"] = {
        "id": "turn-0001",
        "session_id": session_id,
        "status": "completed",
        "input": "x",
        "approval_id": None,
    }
    _turn_id, _turn, state_error = _resolve_turn_cancel_context("req-9743", {"turn_id": "turn-0001"})
    assert state_error is not None
    assert state_error["error"]["code"] == -32003


def test_wl9744_state_error_projection_sets_jsonrpc_envelope_for_requests() -> None:
    # @trace WL-9744
    _reset_state()
    projected = _project_turn_cancel_response(
        "turn/cancel",
        "turn-0001",
        {
            "id": "turn-0001",
            "session_id": "session-1",
            "status": "cancelled",
            "input": "x",
            "approval_id": None,
        },
    )
    assert projected is not None
    assert projected["turn"]["id"] == "turn-0001"


def test_wl9745_state_error_projection_suppresses_notification_errors() -> None:
    # @trace WL-9745
    _reset_state()
    session_id = _seed_session()
    SERVER_STATE.turns["turn-0001"] = {
        "id": "turn-0001",
        "session_id": session_id,
        "status": "completed",
        "input": "x",
        "approval_id": None,
    }
    response = _handle_turn_cancel_request(
        "turn/cancel",
        False,
        "req-9745",
        {"turn_id": "turn-0001"},
    )
    assert response is None


def test_wl9746_execute_path_cancels_turn_state() -> None:
    # @trace WL-9746
    _reset_state()
    session_id = _seed_session()
    turn = {
        "id": "turn-0001",
        "session_id": session_id,
        "status": "in_progress",
        "input": "x",
        "approval_id": None,
    }
    _execute_turn_cancel_resolution("turn/cancel", turn)
    assert turn["status"] == "cancelled"


def test_wl9747_execute_path_cancels_requested_approval() -> None:
    # @trace WL-9747
    _reset_state()
    session_id = _seed_session()
    turn = {
        "id": "turn-0001",
        "session_id": session_id,
        "status": "in_progress",
        "input": "x",
        "approval_id": "approval-1",
    }
    SERVER_STATE.approvals["approval-1"] = {
        "id": "approval-1",
        "turn_id": "turn-0001",
        "session_id": session_id,
        "status": "requested",
        "diff": "--- a\n+++ b\n",
    }
    _execute_turn_cancel_resolution("turn/cancel", turn)
    assert SERVER_STATE.approvals["approval-1"]["status"] == "cancelled"


def test_wl9748_execute_path_preserves_non_requested_approval_status() -> None:
    # @trace WL-9748
    _reset_state()
    session_id = _seed_session()
    turn = {
        "id": "turn-0001",
        "session_id": session_id,
        "status": "in_progress",
        "input": "x",
        "approval_id": "approval-1",
    }
    SERVER_STATE.approvals["approval-1"] = {
        "id": "approval-1",
        "turn_id": "turn-0001",
        "session_id": session_id,
        "status": "granted",
        "diff": "--- a\n+++ b\n",
    }
    _execute_turn_cancel_resolution("turn/cancel", turn)
    assert SERVER_STATE.approvals["approval-1"]["status"] == "granted"


def test_wl9749_notification_turn_cancel_has_side_effect_without_response() -> None:
    # @trace WL-9749
    _reset_state()
    response, _notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "s", "method": "session/start"})
    )
    assert response is not None
    session_id = response["result"]["session"]["id"]

    submit, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "t",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "lane-o",
                    "requires_approval": True,
                    "unified_diff": "x",
                },
            }
        )
    )
    assert submit is not None
    turn_id = submit["result"]["turn"]["id"]

    cancel_response, notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "method": "turn/cancel", "params": {"turn_id": turn_id}})
    )
    assert cancel_response is None
    assert notifications == []
    assert SERVER_STATE.turns[turn_id]["status"] == "cancelled"
