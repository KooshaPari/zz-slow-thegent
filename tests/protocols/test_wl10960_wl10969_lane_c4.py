"""Lane C4 regressions for WL-10960..WL-10969 on turn/submit response + execution edges."""

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


def test_wl10960_extract_turn_submit_response_request_id_accepts_request_has_id_false_without_id() -> None:
    # @trace WL-10960
    assert server._extract_turn_submit_response_request_id({}, request_has_id=False) is None


def test_wl10961_extract_turn_submit_response_request_id_accepts_floats_when_request_has_id_is_true() -> None:
    # @trace WL-10961
    assert server._extract_turn_submit_response_request_id({"request_id": 10.5}, request_has_id=True) == 10.5


def test_wl10962_extract_turn_submit_response_request_id_rejects_boolean_id() -> None:
    # @trace WL-10962
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id({"request_id": True}, request_has_id=True)


def test_wl10963_resolve_turn_submit_response_target_rejects_invalid_shape() -> None:
    # @trace WL-10963
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(
            {"request_has_id": True, "request_id": "req", "turn": {"id": "t"}, "approval_payload": 1}
        )


def test_wl10964_build_turn_submit_response_resolution_phase_uses_structured_return() -> None:
    # @trace WL-10964
    phase = server._build_turn_submit_response_phase(
        True, "req", {"id": "turn-1"}, {"id": "approval-1", "status": "requested"}
    )
    request_has_id, request_id, turn, approval = server._build_turn_submit_response_resolution_phase(phase)
    assert request_has_id is True
    assert request_id == "req"
    assert turn == {"id": "turn-1"}
    assert approval == {"id": "approval-1", "status": "requested"}


def test_wl10965_turn_submit_notification_with_approval_keeps_approval_and_suppresses_response() -> None:
    # @trace WL-10965
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "lane-c4",
                    "requires_approval": True,
                    "unified_diff": "--- a\n+++ b\n",
                },
            }
        )
    )
    assert response is None
    assert any(item["method"] == "approval/requested" for item in notifications)
    turn_id = SERVER_STATE.sessions[session_id]["turn_ids"][0]
    assert SERVER_STATE.turns[turn_id]["status"] == "awaiting_approval"


def test_wl10966_turn_submit_request_with_approval_returns_approval_payload() -> None:
    # @trace WL-10966
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "lane-c4",
                    "requires_approval": True,
                    "unified_diff": "--- a\n+++ b\n",
                },
            }
        )
    )
    assert response is not None
    assert response["result"]["approval"]["status"] == "requested"
    assert response["result"]["approval"]["diff"] == "--- a\n+++ b\n"
    assert any(item["method"] == "turn/started" for item in notifications)


def test_wl10967_turn_submit_approval_diff_whitespace_is_rejected() -> None:
    # @trace WL-10967
    _reset_state()
    session_id = _start_session()
    response, _ = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "lane-c4",
                    "requires_approval": True,
                    "unified_diff": "   \n  ",
                },
            }
        )
    )
    assert response is not None
    assert response["error"]["data"]["reason"] == "diff_must_be_non_empty_string"


def test_wl10968_turn_submit_without_approval_returns_completed_turn() -> None:
    # @trace WL-10968
    _reset_state()
    session_id = _start_session()
    response, _ = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "lane-c4"},
            }
        )
    )
    assert response is not None
    turn_id = response["result"]["turn"]["id"]
    assert response["result"]["turn"]["status"] == "completed"
    assert SERVER_STATE.turns[turn_id]["status"] == "completed"
    assert response["result"]["turn"]["tool_call_id"] is not None
    assert "approval" not in response["result"]


def test_wl10969_build_turn_submit_success_response_preserves_result_shape_without_mutation() -> None:
    # @trace WL-10969
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "status": "completed",
        "input": "x",
        "approval_id": None,
        "tool_call_id": "toolcall-1",
    }
    payload = server._build_turn_submit_result_payload_flat(turn, None)
    assert payload == {"turn": turn}
