"""Lane K Wave-80 regressions for WL-9690..WL-9699."""

from __future__ import annotations

import pytest

from thegent.protocols.jsonrpc_agent_server import (
    SERVER_STATE,
    _build_turn_cancel_projection_payload,
    _cancel_turn_requested_approval,
    _execute_turn_cancel,
    _mark_turn_as_cancelled,
    _resolve_turn_cancel_context,
    _resolve_turn_cancel_turn,
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


def _seed_session() -> str:
    session_id = "session-0001"
    SERVER_STATE.sessions[session_id] = {
        "id": session_id,
        "status": "active",
        "created_index": 1,
        "turn_ids": [],
    }
    return session_id


def test_wl9690_resolve_turn_cancel_turn_requires_turn_id() -> None:
    # @trace WL-9690
    _reset_state()
    turn_id, turn, error = _resolve_turn_cancel_turn("req-9690", {})
    assert turn_id is None
    assert turn is None
    assert error is not None
    assert error["error"]["data"]["reason"] == "turn_id_required"


def test_wl9691_resolve_turn_cancel_turn_finds_existing_turn() -> None:
    # @trace WL-9691
    _reset_state()
    session_id = _seed_session()
    turn = {
        "id": "turn-0001",
        "session_id": session_id,
        "input": "ship",
        "status": "in_progress",
        "approval_id": None,
    }
    SERVER_STATE.turns[turn["id"]] = turn
    turn_id, resolved_turn, error = _resolve_turn_cancel_turn("req-9691", {"turn_id": turn["id"]})
    assert error is None
    assert turn_id == turn["id"]
    assert resolved_turn is turn


def test_wl9692_validate_turn_cancel_turn_state_allows_in_progress() -> None:
    # @trace WL-9692
    _reset_state()
    terminal_error = _validate_turn_cancel_turn_state(
        "req-9692",
        "turn-0001",
        {"id": "turn-0001", "status": "in_progress"},
    )
    assert terminal_error is None


def test_wl9693_validate_turn_cancel_turn_state_blocks_terminal() -> None:
    # @trace WL-9693
    _reset_state()
    terminal_error = _validate_turn_cancel_turn_state(
        "req-9693",
        "turn-0001",
        {"id": "turn-0001", "status": "completed"},
    )
    assert terminal_error is not None
    assert terminal_error["error"]["code"] == -32003


def test_wl9694_mark_turn_as_cancelled_updates_status_only() -> None:
    # @trace WL-9694
    _reset_state()
    turn = {"id": "turn-0001", "status": "in_progress"}
    _mark_turn_as_cancelled(turn)
    assert turn["status"] == "cancelled"


def test_wl9695_cancel_turn_requested_approval_updates_requested_only() -> None:
    # @trace WL-9695
    _reset_state()
    session_id = _seed_session()
    turn = {
        "id": "turn-0001",
        "session_id": session_id,
        "status": "in_progress",
        "approval_id": "approval-0001",
    }
    SERVER_STATE.approvals["approval-0001"] = {
        "id": "approval-0001",
        "turn_id": "turn-0001",
        "session_id": session_id,
        "status": "requested",
        "diff": "x",
    }
    _cancel_turn_requested_approval(turn)
    assert SERVER_STATE.approvals["approval-0001"]["status"] == "cancelled"


def test_wl9696_execute_turn_cancel_runs_cancel_and_approval_cleanup() -> None:
    # @trace WL-9696
    _reset_state()
    session_id = _seed_session()
    turn = {
        "id": "turn-0001",
        "session_id": session_id,
        "status": "in_progress",
        "approval_id": "approval-0001",
    }
    SERVER_STATE.approvals["approval-0001"] = {
        "id": "approval-0001",
        "turn_id": "turn-0001",
        "session_id": session_id,
        "status": "requested",
        "diff": "x",
    }
    _execute_turn_cancel(turn)
    assert turn["status"] == "cancelled"
    assert SERVER_STATE.approvals["approval-0001"]["status"] == "cancelled"


def test_wl9697_build_turn_cancel_projection_payload_serializes_turn() -> None:
    # @trace WL-9697
    _reset_state()
    payload = _build_turn_cancel_projection_payload(
        {
            "id": "turn-0001",
            "session_id": "session-0001",
            "status": "cancelled",
            "input": "ship",
            "approval_id": None,
            "tool_call_id": None,
        }
    )
    assert payload["turn"]["id"] == "turn-0001"
    assert payload["turn"]["status"] == "cancelled"


def test_wl9698_validate_turn_cancel_projection_turn_id_rejects_mismatch() -> None:
    # @trace WL-9698
    _reset_state()
    with pytest.raises(ValueError, match="Turn id mismatch"):
        _validate_turn_cancel_projection_turn_id(
            "turn-expected",
            {"turn": {"id": "turn-actual"}},
        )


def test_wl9699_resolve_turn_cancel_context_uses_split_parse_and_state_checks() -> None:
    # @trace WL-9699
    _reset_state()
    session_id = _seed_session()
    turn = {
        "id": "turn-0001",
        "session_id": session_id,
        "status": "in_progress",
        "input": "ship",
        "approval_id": None,
    }
    SERVER_STATE.turns[turn["id"]] = turn
    turn_id, resolved_turn, error = _resolve_turn_cancel_context("req-9699", {"turn_id": turn["id"]})
    assert error is None
    assert turn_id == turn["id"]
    assert resolved_turn is turn
