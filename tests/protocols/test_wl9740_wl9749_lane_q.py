"""Lane Q regressions for WL-9740..WL-9749."""

from __future__ import annotations

import pytest

from thegent.protocols.jsonrpc_agent_server import (
    SERVER_STATE,
    _execute_turn_cancel_resolution,
    _handle_turn_cancel_request,
    _parse_turn_cancel_request,
    _project_turn_cancel_response,
    _resolve_turn_cancel_context,
    _resolve_turn_cancel_turn,
    _route_turn_cancel_method,
    _validate_turn_cancel_projection_turn_id,
    _validate_turn_cancel_turn_state,
)


def _reset_state() -> None:
    SERVER_STATE.session_counter = 0
    SERVER_STATE.turn_counter = 0
    SERVER_STATE.approval_counter = 0
    SERVER_STATE.tool_call_counter = 0
    SERVER_STATE.sessions.clear()
    SERVER_STATE.turns.clear()
    SERVER_STATE.approvals.clear()


def _seed_in_progress_turn() -> dict[str, str | None]:
    session_id = "session-0001"
    turn_id = "turn-0001"
    SERVER_STATE.sessions[session_id] = {
        "id": session_id,
        "status": "active",
        "created_index": 1,
        "turn_ids": [turn_id],
    }
    turn = {
        "id": turn_id,
        "session_id": session_id,
        "status": "in_progress",
        "input": "lane-q",
        "approval_id": None,
        "tool_call_id": None,
    }
    SERVER_STATE.turns[turn_id] = turn
    return turn


def test_wl9740_route_turn_cancel_method_accepts_supported_method() -> None:
    # @trace WL-9740
    assert _route_turn_cancel_method("turn/cancel") == "cancel"


def test_wl9741_route_turn_cancel_method_rejects_unsupported_method() -> None:
    # @trace WL-9741
    with pytest.raises(ValueError, match="Unsupported turn cancel method"):
        _route_turn_cancel_method("turn/submit")


def test_wl9742_parse_turn_cancel_request_separates_parse_path() -> None:
    # @trace WL-9742
    _reset_state()
    turn = _seed_in_progress_turn()
    turn_id, resolved_turn, error = _parse_turn_cancel_request("turn/cancel", "req-9742", {"turn_id": turn["id"]})
    assert error is None
    assert turn_id == turn["id"]
    assert resolved_turn is turn


def test_wl9743_resolve_turn_cancel_context_preserves_terminal_error_contract() -> None:
    # @trace WL-9743
    _reset_state()
    turn = _seed_in_progress_turn()
    turn["status"] = "completed"
    turn_id, resolved_turn, error = _resolve_turn_cancel_context("req-9743", {"turn_id": turn["id"]})
    assert turn_id is None
    assert resolved_turn is None
    assert error is not None
    assert error["error"]["code"] == -32003


def test_wl9744_validate_turn_cancel_turn_state_handles_happy_and_failure_paths() -> None:
    # @trace WL-9744
    _reset_state()
    turn = _seed_in_progress_turn()
    assert _validate_turn_cancel_turn_state("req-9744", turn["id"], turn) is None
    turn["status"] = "cancelled"
    error = _validate_turn_cancel_turn_state("req-9744", turn["id"], turn)
    assert error is not None
    assert error["error"]["code"] == -32003


def test_wl9745_execute_turn_cancel_resolution_separates_execution_phase() -> None:
    # @trace WL-9745
    _reset_state()
    turn = _seed_in_progress_turn()
    _execute_turn_cancel_resolution("turn/cancel", turn)
    assert turn["status"] == "cancelled"


def test_wl9746_project_turn_cancel_response_separates_projection_phase() -> None:
    # @trace WL-9746
    _reset_state()
    turn = _seed_in_progress_turn()
    turn["status"] = "cancelled"
    payload = _project_turn_cancel_response("turn/cancel", turn["id"], turn)
    assert payload["turn"]["id"] == turn["id"]
    assert payload["turn"]["status"] == "cancelled"


def test_wl9747_validate_turn_cancel_projection_turn_id_detects_mismatch() -> None:
    # @trace WL-9747
    with pytest.raises(ValueError, match="Turn id mismatch"):
        _validate_turn_cancel_projection_turn_id("turn-expected", {"turn": {"id": "turn-actual"}})


def test_wl9748_resolve_turn_cancel_turn_boundary_missing_turn() -> None:
    # @trace WL-9748
    _reset_state()
    turn_id, turn, error = _resolve_turn_cancel_turn("req-9748", {"turn_id": "turn-404"})
    assert turn_id is None
    assert turn is None
    assert error is not None
    assert error["error"]["code"] == -32002


def test_wl9749_handle_turn_cancel_request_notification_has_side_effect_without_response() -> None:
    # @trace WL-9749
    _reset_state()
    turn = _seed_in_progress_turn()
    response = _handle_turn_cancel_request("turn/cancel", False, None, {"turn_id": turn["id"]})
    assert response is None
    assert turn["status"] == "cancelled"
