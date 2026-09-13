"""Lane Z regressions for WL-9800..WL-9809 on approval resolution phase-plan flow."""

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


def _submit_turn(session_id: str) -> tuple[str, str]:
    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "lane-z",
                    "requires_approval": True,
                    "unified_diff": "--- a/z\n+++ b/z\n@@\n-old\n+new\n",
                },
            }
        )
    )
    assert response is not None
    return response["result"]["turn"]["id"], response["result"]["approval"]["id"]


def test_wl9800_phase_plan_captures_route_binding_and_context() -> None:
    # @trace WL-9800
    _reset_state()
    session_id = _start_session()
    _turn_id, approval_id = _submit_turn(session_id)
    plan = server._build_approval_resolution_phase_plan("approval/grant", "req", {"approval_id": approval_id})
    assert plan["route"] == "grant"
    assert set(plan["binding"]) == {"parse", "execute", "project"}
    assert plan["approval_id"] == approval_id
    assert isinstance(plan["approval"], dict)
    assert isinstance(plan["turn"], dict)
    assert plan["parse_error"] is None


def test_wl9801_parse_error_resolution_returns_parse_error_when_present() -> None:
    # @trace WL-9801
    _reset_state()
    plan = server._build_approval_resolution_phase_plan("approval/grant", "req", {"approval_id": "approval-404"})
    parse_error = server._resolve_approval_resolution_parse_error(plan)
    assert parse_error is not None
    assert parse_error["error"]["code"] == -32005


def test_wl9802_emit_response_policy_is_explicit_for_request_and_notification() -> None:
    # @trace WL-9802
    assert server._approval_resolution_should_emit_response(True) is True
    assert server._approval_resolution_should_emit_response(False) is False


def test_wl9803_execution_target_resolution_returns_typed_execution_tuple() -> None:
    # @trace WL-9803
    _reset_state()
    session_id = _start_session()
    _turn_id, approval_id = _submit_turn(session_id)
    plan = server._build_approval_resolution_phase_plan("approval/grant", "req", {"approval_id": approval_id})
    parsed_approval_id, approval, turn, route, binding = server._resolve_approval_resolution_execution_target(plan)
    assert parsed_approval_id == approval_id
    assert isinstance(approval, dict)
    assert isinstance(turn, dict)
    assert route == "grant"
    assert set(binding) == {"parse", "execute", "project"}


def test_wl9804_execution_target_resolution_fails_for_unresolved_plan_state() -> None:
    # @trace WL-9804
    with pytest.raises(ValueError, match="Approval resolution execution target unresolved"):
        server._resolve_approval_resolution_execution_target(
            {"approval_id": None, "approval": None, "turn": None, "route": "grant", "binding": {}}
        )


def test_wl9805_apply_execution_delegates_to_binding_execute_phase() -> None:
    # @trace WL-9805
    _reset_state()
    session_id = _start_session()
    turn_id, approval_id = _submit_turn(session_id)
    approval = SERVER_STATE.approvals[approval_id]
    turn = SERVER_STATE.turns[turn_id]
    binding = server._bind_approval_resolution_phases("grant")
    notifications: list[dict[str, object]] = []
    server._apply_approval_resolution_execution("grant", approval, turn, binding, notifications)
    assert approval["status"] == "granted"
    assert turn["status"] == "completed"
    assert len(notifications) >= 3


def test_wl9806_success_response_projection_uses_emit_policy() -> None:
    # @trace WL-9806
    _reset_state()
    session_id = _start_session()
    turn_id, approval_id = _submit_turn(session_id)
    approval = SERVER_STATE.approvals[approval_id]
    turn = SERVER_STATE.turns[turn_id]
    binding = server._bind_approval_resolution_phases("grant")
    notifications: list[dict[str, object]] = []
    server._apply_approval_resolution_execution("grant", approval, turn, binding, notifications)
    request_response = server._build_approval_resolution_success_response(
        True, "req", approval_id, approval, turn, binding
    )
    notification_response = server._build_approval_resolution_success_response(
        False, "req", approval_id, approval, turn, binding
    )
    assert request_response is not None
    assert request_response["result"]["approval"]["status"] == "granted"
    assert notification_response is None


def test_wl9807_failure_response_builder_preserves_parse_error_payload() -> None:
    # @trace WL-9807
    parse_error = server._error_response("req", server.JsonRpcError(-32005, "Approval not found"))
    assert server._build_approval_resolution_failure_response(parse_error) == parse_error


def test_wl9808_handler_uses_plan_and_failure_builder_for_parse_error_path() -> None:
    # @trace WL-9808
    _reset_state()
    response = server._handle_approval_resolution_request(
        "approval/grant", True, "req", {"approval_id": "approval-404"}, []
    )
    assert response is not None
    assert response["error"]["code"] == -32005


def test_wl9809_notification_grant_executes_side_effects_without_response() -> None:
    # @trace WL-9809
    _reset_state()
    session_id = _start_session()
    turn_id, approval_id = _submit_turn(session_id)
    grant_response, notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "method": "approval/grant", "params": {"approval_id": approval_id}})
    )
    assert grant_response is None
    assert len(notifications) >= 3
    assert SERVER_STATE.approvals[approval_id]["status"] == "granted"
    assert SERVER_STATE.turns[turn_id]["status"] == "completed"
