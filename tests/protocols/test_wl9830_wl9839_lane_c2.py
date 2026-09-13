"""Lane C2 regressions for WL-9830..WL-9839 on turn/submit phase resolution boundaries."""

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


def test_wl9830_parse_phase_separates_error_projection_from_execution_shape() -> None:
    # @trace WL-9830
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan("req", {"session_id": session_id, "input": "c2"})
    parse_phase = server._build_turn_submit_parse_phase(plan)
    assert parse_phase["parse_error"] is None
    assert parse_phase["session_id"] == session_id
    assert parse_phase["user_input"] == "c2"


def test_wl9831_parse_phase_preserves_parse_error_contract() -> None:
    # @trace WL-9831
    _reset_state()
    plan = server._build_turn_submit_phase_plan("req", {"session_id": "session-404", "input": "c2"})
    parse_phase = server._build_turn_submit_parse_phase(plan)
    assert parse_phase["parse_error"] is not None
    assert parse_phase["parse_error"]["error"]["code"] == -32001


def test_wl9832_execution_phase_resolves_typed_tuple_from_parse_phase() -> None:
    # @trace WL-9832
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan("req", {"session_id": session_id, "input": "c2"})
    parse_phase = server._build_turn_submit_parse_phase(plan)
    resolved = server._build_turn_submit_execution_phase(parse_phase)
    assert resolved[0] == session_id
    assert isinstance(resolved[1], dict)
    assert resolved[2] == "c2"
    assert resolved[3] is False
    assert resolved[4] is None


def test_wl9833_execution_phase_fails_loudly_on_unresolved_parse_shape() -> None:
    # @trace WL-9833
    with pytest.raises(ValueError, match="Turn submit execution target unresolved"):
        server._build_turn_submit_execution_phase(
            {"session_id": None, "session": None, "user_input": None, "requires_approval": None, "approval_diff": None}
        )


def test_wl9834_commit_resolution_phase_preserves_commit_tuple_shape() -> None:
    # @trace WL-9834
    _reset_state()
    session_id = _start_session()
    session = SERVER_STATE.sessions[session_id]
    commit_phase = server._build_turn_submit_commit_phase(session_id, session, "c2")
    turn_id, turn, resolved_session = server._build_turn_submit_commit_resolution_phase(commit_phase)
    assert turn_id == commit_phase["turn_id"]
    assert turn is commit_phase["turn"]
    assert resolved_session is session


def test_wl9835_commit_resolution_phase_fails_loudly_on_invalid_shape() -> None:
    # @trace WL-9835
    with pytest.raises(ValueError, match="Turn submit commit target unresolved"):
        server._build_turn_submit_commit_resolution_phase({"turn_id": None, "turn": None, "session": None})


def test_wl9836_side_effects_resolution_phase_preserves_execution_inputs() -> None:
    # @trace WL-9836
    _reset_state()
    session_id = _start_session()
    turn = {"id": "turn-1", "session_id": session_id, "status": "in_progress"}
    phase = server._build_turn_submit_side_effects_phase(session_id, "turn-1", turn, "c2", True, "diff")
    resolved = server._build_turn_submit_side_effects_resolution_phase(phase)
    assert resolved[0] == session_id
    assert resolved[1] == "turn-1"
    assert resolved[2] is turn
    assert resolved[3] == "c2"
    assert resolved[4] is True
    assert resolved[5] == "diff"


def test_wl9837_side_effects_resolution_phase_fails_loudly_on_invalid_shape() -> None:
    # @trace WL-9837
    with pytest.raises(ValueError, match="Turn submit side-effects target unresolved"):
        server._build_turn_submit_side_effects_resolution_phase(
            {
                "session_id": "session-1",
                "turn_id": "turn-1",
                "turn": {},
                "user_input": "c2",
                "requires_approval": "yes",
                "approval_diff": None,
            }
        )


def test_wl9838_response_resolution_phase_preserves_typed_response_contract() -> None:
    # @trace WL-9838
    turn = {"id": "turn-1"}
    response_phase = server._build_turn_submit_response_phase(
        True, "req", turn, {"id": "approval-1", "status": "requested"}
    )
    request_has_id, request_id, resolved_turn, approval_payload = server._build_turn_submit_response_resolution_phase(
        response_phase
    )
    assert request_has_id is True
    assert request_id == "req"
    assert resolved_turn is turn
    assert approval_payload is not None
    assert approval_payload["id"] == "approval-1"


def test_wl9839_handler_preserves_parse_failure_short_circuit_without_side_effects() -> None:
    # @trace WL-9839
    _reset_state()
    session_id = _start_session()
    turns_before = len(SERVER_STATE.turns)
    approvals_before = len(SERVER_STATE.approvals)
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": 123},
            }
        )
    )
    assert response is not None
    assert response["error"]["data"]["reason"] == "input_must_be_string"
    assert notifications == []
    assert len(SERVER_STATE.turns) == turns_before
    assert len(SERVER_STATE.approvals) == approvals_before
