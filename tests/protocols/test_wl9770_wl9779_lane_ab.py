"""Lane AB regressions for WL-9770..WL-9779 on approval phase separation."""

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


def _submit_approval_turn(session_id: str) -> tuple[str, str]:
    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "lane-ab",
                    "requires_approval": True,
                    "unified_diff": "--- a/ab\n+++ a/ab\n@@ -1 +1 @@\n-old\n+new\n",
                },
            }
        )
    )
    assert response is not None
    return response["result"]["turn"]["id"], response["result"]["approval"]["id"]


def test_wl9770_parse_phase_builder_carries_parse_and_execution_fields() -> None:
    # @trace WL-9770
    plan = {
        "parse_error": None,
        "approval_id": "approval-1",
        "approval": {"id": "approval-1", "status": "requested", "turn_id": "turn-1"},
        "turn": {
            "id": "turn-1",
            "status": "awaiting_approval",
            "session_id": "session-1",
            "input": "x",
        },
        "route": "grant",
        "binding": server._bind_approval_resolution_phases("grant"),
    }
    parse_phase = server._build_approval_resolution_parse_phase(plan)
    assert parse_phase["parse_error"] is None
    assert parse_phase["approval_id"] == "approval-1"
    assert parse_phase["route"] == "grant"


def test_wl9771_parse_phase_builder_preserves_parse_error_contract() -> None:
    # @trace WL-9771
    parse_error = server._error_response(
        "req", server.JsonRpcError(-32602, "invalid params")
    )
    plan = {
        "parse_error": parse_error,
        "approval_id": None,
        "approval": None,
        "turn": None,
        "route": "grant",
        "binding": server._bind_approval_resolution_phases("grant"),
    }
    parse_phase = server._build_approval_resolution_parse_phase(plan)
    assert parse_phase["parse_error"] == parse_error


def test_wl9772_execution_phase_builder_resolves_typed_target_tuple() -> None:
    # @trace WL-9772
    parse_phase = {
        "parse_error": None,
        "approval_id": "approval-1",
        "approval": {"id": "approval-1", "status": "requested", "turn_id": "turn-1"},
        "turn": {
            "id": "turn-1",
            "status": "awaiting_approval",
            "session_id": "session-1",
            "input": "x",
        },
        "route": "grant",
        "binding": server._bind_approval_resolution_phases("grant"),
    }
    approval_id, approval, turn, route, binding = (
        server._build_approval_resolution_execution_phase(parse_phase)
    )
    assert approval_id == "approval-1"
    assert approval["id"] == "approval-1"
    assert turn["id"] == "turn-1"
    assert route == "grant"
    assert callable(binding["execute"])


def test_wl9773_execution_phase_builder_fails_on_unresolved_payload() -> None:
    # @trace WL-9773
    with pytest.raises(
        ValueError, match="Approval resolution execution target unresolved"
    ):
        server._build_approval_resolution_execution_phase(
            {
                "parse_error": None,
                "approval_id": None,
                "approval": None,
                "turn": None,
                "route": "grant",
                "binding": server._bind_approval_resolution_phases("grant"),
            }
        )


def test_wl9774_execution_path_mutates_grant_state_via_binding() -> None:
    # @trace WL-9774
    _reset_state()
    session_id = _start_session()
    turn_id, approval_id = _submit_approval_turn(session_id)
    approval = SERVER_STATE.approvals[approval_id]
    turn = SERVER_STATE.turns[turn_id]
    notifications: list[dict[str, object]] = []
    server._apply_approval_resolution_execution(
        "grant",
        approval,
        turn,
        server._bind_approval_resolution_phases("grant"),
        notifications,
    )
    assert approval["status"] == "granted"
    assert turn["status"] == "completed"
    assert len(notifications) >= 3


def test_wl9775_execution_path_mutates_reject_state_via_binding() -> None:
    # @trace WL-9775
    _reset_state()
    session_id = _start_session()
    turn_id, approval_id = _submit_approval_turn(session_id)
    approval = SERVER_STATE.approvals[approval_id]
    turn = SERVER_STATE.turns[turn_id]
    notifications: list[dict[str, object]] = []
    server._apply_approval_resolution_execution(
        "reject",
        approval,
        turn,
        server._bind_approval_resolution_phases("reject"),
        notifications,
    )
    assert approval["status"] == "rejected"
    assert turn["status"] == "rejected"
    assert notifications[-1]["method"] == "turn/completed"


def test_wl9776_projection_phase_builds_serialized_payload() -> None:
    # @trace WL-9776
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "status": "completed",
        "created_index": 1,
        "input": "lane-ab",
        "approval_id": "approval-1",
        "tool_call_id": "tool-call-1",
    }
    approval = {"id": "approval-1", "status": "granted", "turn_id": "turn-1"}
    payload = server._apply_approval_resolution_projection(
        "approval-1", approval, turn, server._bind_approval_resolution_phases("grant")
    )
    assert payload["approval"]["id"] == "approval-1"
    assert payload["approval"]["status"] == "granted"
    assert payload["turn"]["id"] == "turn-1"


def test_wl9777_projection_phase_fails_on_approval_id_mismatch() -> None:
    # @trace WL-9777
    with pytest.raises(ValueError, match="Approval id mismatch"):
        server._apply_approval_resolution_projection(
            "approval-expected",
            {"id": "approval-actual", "status": "granted", "turn_id": "turn-1"},
            {
                "id": "turn-1",
                "session_id": "session-1",
                "status": "completed",
                "created_index": 1,
                "input": "lane-ab",
                "approval_id": "approval-actual",
                "tool_call_id": None,
            },
            server._bind_approval_resolution_phases("grant"),
        )


def test_wl9778_handler_uses_parse_and_execution_phases_for_happy_path() -> None:
    # @trace WL-9778
    _reset_state()
    session_id = _start_session()
    _turn_id, approval_id = _submit_approval_turn(session_id)
    notifications: list[dict[str, object]] = []
    response = server._handle_approval_resolution_request(
        "approval/grant", True, "req", {"approval_id": approval_id}, notifications
    )
    assert response is not None
    assert response["result"]["approval"]["status"] == "granted"


def test_wl9779_handler_returns_parse_failure_without_execution_side_effects() -> None:
    # @trace WL-9779
    _reset_state()
    notifications: list[dict[str, object]] = []
    response = server._handle_approval_resolution_request(
        "approval/grant", True, "req", {"approval_id": "approval-404"}, notifications
    )
    assert response is not None
    assert response["error"]["code"] == -32005
    assert notifications == []
