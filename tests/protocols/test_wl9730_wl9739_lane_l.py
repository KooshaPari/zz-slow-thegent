"""Lane L regressions for WL-9730..WL-9739 against current JSON-RPC server contract."""

from __future__ import annotations

import orjson as json

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
    params: dict[str, object] = {"session_id": session_id, "input": "lane-l"}
    if requires_approval:
        params["requires_approval"] = True
        params["unified_diff"] = "--- a/x\n+++ b/x\n@@ -1 +1 @@\n-old\n+new\n"
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


def test_wl9730_parse_phase_rejects_missing_turn_id() -> None:
    """@trace WL-9730"""
    _reset_state()

    response, notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "c1", "method": "turn/cancel", "params": {}})
    )

    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "turn_id_required"
    assert notifications == []
    assert SERVER_STATE.turns == {}


def test_wl9731_success_path_cancels_in_progress_turn() -> None:
    """@trace WL-9731"""
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)

    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "c2",
                "method": "turn/cancel",
                "params": {"turn_id": turn_id},
            }
        )
    )

    assert response is not None
    assert response["result"]["turn"]["status"] == "cancelled"
    assert notifications == []


def test_wl9732_lookup_miss_branch_returns_turn_not_found() -> None:
    """@trace WL-9732"""
    _reset_state()

    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "c3",
                "method": "turn/cancel",
                "params": {"turn_id": "turn-9999"},
            }
        )
    )

    assert response is not None
    assert response["error"]["code"] == -32002
    assert notifications == []


def test_wl9733_dispatch_produces_serialized_turn_projection() -> None:
    """@trace WL-9733"""
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)

    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "c4",
                "method": "turn/cancel",
                "params": {"turn_id": turn_id},
            }
        )
    )

    assert response is not None
    turn = response["result"]["turn"]
    assert turn["id"] == turn_id
    assert turn["session_id"] == session_id
    assert turn["status"] == "cancelled"


def test_wl9734_terminal_turn_fails_before_state_mutation() -> None:
    """@trace WL-9734"""
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)

    first, _ = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "c5a",
                "method": "turn/cancel",
                "params": {"turn_id": turn_id},
            }
        )
    )
    assert first is not None

    second, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "c5b",
                "method": "turn/cancel",
                "params": {"turn_id": turn_id},
            }
        )
    )

    assert second is not None
    assert second["error"]["code"] == -32003
    assert notifications == []
    assert SERVER_STATE.turns[turn_id]["status"] == "cancelled"


def test_wl9735_notification_cancel_avoids_response_but_applies_effect() -> None:
    """@trace WL-9735"""
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)

    response, notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "method": "turn/cancel", "params": {"turn_id": turn_id}})
    )

    assert response is None
    assert notifications == []
    assert SERVER_STATE.turns[turn_id]["status"] == "cancelled"


def test_wl9736_recovery_branch_preserves_resolved_approval_state() -> None:
    """@trace WL-9736"""
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    approval_id = SERVER_STATE.turns[turn_id].get("approval_id")
    assert isinstance(approval_id, str)

    SERVER_STATE.approvals[approval_id]["status"] = "granted"
    SERVER_STATE.turns[turn_id]["status"] = "completed"

    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "c7",
                "method": "turn/cancel",
                "params": {"turn_id": turn_id},
            }
        )
    )

    assert response is not None
    assert response["error"]["code"] == -32003
    assert SERVER_STATE.approvals[approval_id]["status"] == "granted"


def test_wl9737_requested_approval_is_cancelled_on_turn_cancel() -> None:
    """@trace WL-9737"""
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    approval_id = SERVER_STATE.turns[turn_id].get("approval_id")
    assert isinstance(approval_id, str)

    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "c8",
                "method": "turn/cancel",
                "params": {"turn_id": turn_id},
            }
        )
    )

    assert response is not None
    assert response["result"]["turn"]["status"] == "cancelled"
    assert SERVER_STATE.approvals[approval_id]["status"] == "cancelled"


def test_wl9738_non_requested_approval_status_is_preserved() -> None:
    """@trace WL-9738"""
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    approval_id = SERVER_STATE.turns[turn_id].get("approval_id")
    assert isinstance(approval_id, str)
    SERVER_STATE.approvals[approval_id]["status"] = "rejected"

    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "c9",
                "method": "turn/cancel",
                "params": {"turn_id": turn_id},
            }
        )
    )

    assert response is not None
    assert response["result"]["turn"]["status"] == "cancelled"
    assert SERVER_STATE.approvals[approval_id]["status"] == "rejected"


def test_wl9739_invalid_params_type_fails_before_cancel_execution() -> None:
    """@trace WL-9739"""
    _reset_state()

    response, notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "c10", "method": "turn/cancel", "params": []})
    )

    assert response is not None
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "params_must_be_object"
    assert notifications == []
    assert SERVER_STATE.turns == {}
