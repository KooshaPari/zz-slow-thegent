"""Lane X regressions for WL-9760..WL-9769 on approval resolution phased routing."""

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
                    "input": "lane-x",
                    "requires_approval": True,
                    "unified_diff": "--- a/x\n+++ a/x\n@@ -1 +1 @@\n-old\n+new\n",
                },
            }
        )
    )
    assert response is not None
    return response["result"]["turn"]["id"], response["result"]["approval"]["id"]


def test_wl9760_discovery_routes_grant_and_reject_methods() -> None:
    # @trace WL-9760
    assert server._discover_approval_resolution_route("approval/grant") == "grant"
    assert server._discover_approval_resolution_route("approval/reject") == "reject"


def test_wl9761_binding_exposes_parse_execute_project_for_approval_routes() -> None:
    # @trace WL-9761
    binding = server._bind_approval_resolution_phases("grant")
    assert set(binding) == {"parse", "execute", "project"}


def test_wl9762_parse_phase_resolves_requested_approval_context() -> None:
    # @trace WL-9762
    _reset_state()
    session_id = _start_session()
    _turn_id, approval_id = _submit_turn(session_id)
    binding = server._bind_approval_resolution_phases("grant")
    parsed_approval_id, approval, turn, error = (
        server._parse_approval_resolution_with_binding(
            "req", {"approval_id": approval_id}, binding
        )
    )
    assert error is None
    assert parsed_approval_id == approval_id
    assert approval is not None
    assert turn is not None


def test_wl9763_parse_phase_preserves_missing_approval_boundary() -> None:
    # @trace WL-9763
    _reset_state()
    approval_id, approval, turn, error = server._resolve_approval_resolution_context(
        "req", {"approval_id": "approval-404"}
    )
    assert approval_id == "approval-404"
    assert approval is None
    assert turn is None
    assert error is not None
    assert error["error"]["code"] == -32005


def test_wl9764_success_dispatch_executes_grant_and_returns_projection() -> None:
    # @trace WL-9764
    _reset_state()
    session_id = _start_session()
    turn_id, approval_id = _submit_turn(session_id)
    approval = SERVER_STATE.approvals[approval_id]
    turn = SERVER_STATE.turns[turn_id]
    binding = server._bind_approval_resolution_phases("grant")
    notifications: list[dict[str, object]] = []
    response = server._dispatch_approval_resolution_success(
        True, "req", approval_id, approval, turn, "grant", binding, notifications
    )
    assert response is not None
    assert response["result"]["approval"]["status"] == "granted"
    assert response["result"]["turn"]["status"] == "completed"
    assert len(notifications) >= 3


def test_wl9765_recovery_dispatch_returns_parse_error_payload() -> None:
    # @trace WL-9765
    parse_error = server._error_response(
        "req", server.JsonRpcError(-32005, "Approval not found")
    )
    assert server._dispatch_approval_resolution_recovery(parse_error) == parse_error


def test_wl9766_execute_phase_reject_updates_state_and_emits_turn_completed() -> None:
    # @trace WL-9766
    _reset_state()
    session_id = _start_session()
    turn_id, approval_id = _submit_turn(session_id)
    approval = SERVER_STATE.approvals[approval_id]
    turn = SERVER_STATE.turns[turn_id]
    notifications: list[dict[str, object]] = []
    server._execute_approval_resolution("reject", approval, turn, notifications)
    assert approval["status"] == "rejected"
    assert turn["status"] == "rejected"
    assert notifications[-1]["method"] == "turn/completed"


def test_wl9767_project_phase_rejects_approval_id_mismatch() -> None:
    # @trace WL-9767
    _reset_state()
    with pytest.raises(ValueError, match="Approval id mismatch"):
        server._project_approval_resolution_result(
            "approval-expected",
            {"id": "approval-actual", "status": "requested"},
            {
                "id": "turn-1",
                "session_id": "session-1",
                "status": "awaiting_approval",
                "input": "x",
                "approval_id": "approval-actual",
                "tool_call_id": None,
            },
        )


def test_wl9768_handler_orchestrates_grant_happy_and_failure_paths() -> None:
    # @trace WL-9768
    _reset_state()
    notifications: list[dict[str, object]] = []
    failure = server._handle_approval_resolution_request(
        "approval/grant", True, "req-f", {"approval_id": "approval-404"}, notifications
    )
    assert failure is not None
    assert failure["error"]["code"] == -32005

    session_id = _start_session()
    _turn_id, approval_id = _submit_turn(session_id)
    success = server._handle_approval_resolution_request(
        "approval/grant", True, "req-s", {"approval_id": approval_id}, notifications
    )
    assert success is not None
    assert success["result"]["approval"]["status"] == "granted"


def test_wl9769_notification_approval_grant_has_side_effect_without_response() -> None:
    # @trace WL-9769
    _reset_state()
    session_id = _start_session()
    turn_id, approval_id = _submit_turn(session_id)
    grant_response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "approval/grant",
                "params": {"approval_id": approval_id},
            }
        )
    )
    assert grant_response is None
    assert len(notifications) >= 3
    assert SERVER_STATE.approvals[approval_id]["status"] == "granted"
    assert SERVER_STATE.turns[turn_id]["status"] == "completed"
