"""Lane W regressions for WL-9760..WL-9769 on turn/cancel phase-plan flow."""

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


def _submit_turn(session_id: str, *, requires_approval: bool = False) -> str:
    params: dict[str, object] = {"session_id": session_id, "input": "lane-w"}
    if requires_approval:
        params["requires_approval"] = True
        params["unified_diff"] = "--- a/x\n+++ b/x\n@@\n-old\n+new\n"
    response, _notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "submit", "method": "turn/submit", "params": params})
    )
    assert response is not None
    return response["result"]["turn"]["id"]


def test_wl9760_build_turn_cancel_phase_plan_collects_discovery_binding_parse() -> None:
    # @trace WL-9760
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    plan = server._build_turn_cancel_phase_plan("turn/cancel", "req-9760", {"turn_id": turn_id})
    assert plan["route"] == "cancel"
    assert set(plan["binding"]) == {"parse", "execute", "project"}
    assert plan["parse_error"] is None


def test_wl9761_build_turn_cancel_phase_plan_preserves_parse_error() -> None:
    # @trace WL-9761
    _reset_state()
    plan = server._build_turn_cancel_phase_plan("turn/cancel", "req-9761", {"turn_id": "turn-missing"})
    assert plan["turn_id"] is None
    assert plan["turn"] is None
    assert plan["parse_error"] is not None
    assert plan["parse_error"]["error"]["code"] == -32002


def test_wl9762_turn_cancel_should_emit_response_tracks_request_id_presence() -> None:
    # @trace WL-9762
    assert server._turn_cancel_should_emit_response(True) is True
    assert server._turn_cancel_should_emit_response(False) is False


def test_wl9763_resolve_turn_cancel_execution_target_returns_turn_binding() -> None:
    # @trace WL-9763
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    plan = server._build_turn_cancel_phase_plan("turn/cancel", "req-9763", {"turn_id": turn_id})
    resolved_turn_id, turn, binding = server._resolve_turn_cancel_execution_target(plan)
    assert resolved_turn_id == turn_id
    assert turn["id"] == turn_id
    assert set(binding) == {"parse", "execute", "project"}


def test_wl9764_resolve_turn_cancel_execution_target_rejects_unresolved_plan() -> None:
    # @trace WL-9764
    with pytest.raises(ValueError, match="execution target unresolved"):
        server._resolve_turn_cancel_execution_target(
            {
                "binding": {"parse": object(), "execute": object(), "project": object()},
                "turn_id": None,
                "turn": None,
            }
        )


def test_wl9765_apply_turn_cancel_execution_runs_bound_execute_phase() -> None:
    # @trace WL-9765
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    turn = SERVER_STATE.turns[turn_id]
    binding = server._bind_turn_cancel_phases("cancel")
    server._apply_turn_cancel_execution(turn, binding)
    assert turn["status"] == "cancelled"


def test_wl9766_build_turn_cancel_success_response_projects_turn_for_request() -> None:
    # @trace WL-9766
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    turn = SERVER_STATE.turns[turn_id]
    binding = server._bind_turn_cancel_phases("cancel")
    server._apply_turn_cancel_execution(turn, binding)
    response = server._build_turn_cancel_success_response(True, "req-9766", turn_id, turn, binding)
    assert response is not None
    assert response["result"]["turn"]["id"] == turn_id
    assert response["result"]["turn"]["status"] == "cancelled"


def test_wl9767_build_turn_cancel_success_response_suppresses_notification_payload() -> None:
    # @trace WL-9767
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    turn = SERVER_STATE.turns[turn_id]
    binding = server._bind_turn_cancel_phases("cancel_suppress")
    server._apply_turn_cancel_execution(turn, binding)
    response = server._build_turn_cancel_success_response(False, "req-9767", turn_id, turn, binding)
    assert response is None


def test_wl9768_handle_turn_cancel_request_uses_phase_plan_for_happy_path() -> None:
    # @trace WL-9768
    _reset_state()
    session_id = _start_session()
    turn_id = _submit_turn(session_id, requires_approval=True)
    response = server._handle_turn_cancel_request("turn/cancel", True, "req-9768", {"turn_id": turn_id})
    assert response is not None
    assert response["result"]["turn"]["status"] == "cancelled"


def test_wl9769_build_turn_cancel_failure_response_preserves_terminal_notification_suppression() -> None:
    # @trace WL-9769
    parse_error = server._error_response("ignored", server.JsonRpcError(-32003, "Turn already terminal"))
    response = server._build_turn_cancel_failure_response(False, parse_error)
    assert response is None
