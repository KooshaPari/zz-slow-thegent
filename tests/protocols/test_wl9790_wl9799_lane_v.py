"""Lane V regressions for WL-9790..WL-9799 on turn/cancel helper boundaries."""

from __future__ import annotations

from thegent.protocols import jsonrpc_agent_server as server
from thegent.protocols.jsonrpc_agent_server import SERVER_STATE


def _reset_state() -> None:
    SERVER_STATE.session_counter = 0
    SERVER_STATE.turn_counter = 0
    SERVER_STATE.approval_counter = 0
    SERVER_STATE.tool_call_counter = 0
    SERVER_STATE.sessions.clear()
    SERVER_STATE.turns.clear()
    SERVER_STATE.approvals.clear()


def test_wl9790_turn_cancel_recovery_suppression_decision() -> None:
    # @trace WL-9790
    parse_error = server._error_response("req", server.JsonRpcError(-32003, "Turn already terminal"))
    assert server._should_suppress_turn_cancel_recovery_response(False, parse_error) is True
    assert server._should_suppress_turn_cancel_recovery_response(True, parse_error) is False


def test_wl9791_turn_cancel_recovery_error_code_extraction() -> None:
    # @trace WL-9791
    parse_error = server._error_response("req", server.JsonRpcError(-32003, "Turn already terminal"))
    assert server._extract_turn_cancel_recovery_error_code(parse_error) == -32003
    assert server._extract_turn_cancel_recovery_error_code({"error": {"code": "x"}}) is None


def test_wl9792_turn_approval_id_resolution_requires_string() -> None:
    # @trace WL-9792
    assert server._resolve_turn_approval_id({"approval_id": "approval-1"}) == "approval-1"
    assert server._resolve_turn_approval_id({"approval_id": 12}) is None
    assert server._resolve_turn_approval_id({}) is None


def test_wl9793_requested_approval_lookup_isolated_from_global_state() -> None:
    # @trace WL-9793
    _reset_state()
    SERVER_STATE.approvals["approval-1"] = {"id": "approval-1", "status": "requested"}
    found = server._resolve_requested_approval("approval-1")
    missing = server._resolve_requested_approval("approval-404")
    assert found is not None
    assert found["id"] == "approval-1"
    assert missing is None


def test_wl9794_requested_approval_status_predicate() -> None:
    # @trace WL-9794
    assert server._is_requested_approval_status({"status": "requested"}) is True
    assert server._is_requested_approval_status({"status": "approved"}) is False


def test_wl9795_mark_approval_cancelled_mutates_status() -> None:
    # @trace WL-9795
    approval = {"id": "approval-1", "status": "requested"}
    server._mark_approval_as_cancelled(approval)
    assert approval["status"] == "cancelled"


def test_wl9796_cancel_turn_requested_approval_preserves_non_requested_status() -> None:
    # @trace WL-9796
    _reset_state()
    turn = {"id": "turn-1", "approval_id": "approval-1", "status": "in_progress"}
    SERVER_STATE.approvals["approval-1"] = {"id": "approval-1", "status": "approved"}
    server._cancel_turn_requested_approval(turn)
    assert SERVER_STATE.approvals["approval-1"]["status"] == "approved"


def test_wl9797_cancel_turn_requested_approval_skips_missing_approval() -> None:
    # @trace WL-9797
    _reset_state()
    turn = {"id": "turn-1", "approval_id": "approval-missing", "status": "in_progress"}
    server._cancel_turn_requested_approval(turn)
    assert SERVER_STATE.approvals == {}


def test_wl9798_build_turn_cancel_result_serializes_turn_payload() -> None:
    # @trace WL-9798
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "status": "cancelled",
        "created_index": 1,
        "input": "lane-v",
        "approval_id": None,
    }
    result = server._build_turn_cancel_result(turn)
    assert result["id"] == "turn-1"
    assert result["status"] == "cancelled"


def test_wl9799_build_turn_cancel_projection_wraps_result_helper() -> None:
    # @trace WL-9799
    turn = {
        "id": "turn-9",
        "session_id": "session-9",
        "status": "cancelled",
        "created_index": 9,
        "input": "lane-v",
        "approval_id": None,
    }
    payload = server._build_turn_cancel_projection_payload(turn)
    assert payload["turn"]["id"] == "turn-9"
    assert payload["turn"]["status"] == "cancelled"
