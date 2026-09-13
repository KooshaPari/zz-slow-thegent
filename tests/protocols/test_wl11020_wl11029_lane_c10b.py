"""Lane C10b regressions for WL-11020..WL-11029 on turn/submit planning and response field resolution."""

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


def test_wl11020_resolve_turn_submit_parse_error_returns_error_payload() -> None:
    # @trace WL-11020
    parse_error = {"error": "oops"}
    assert server._resolve_turn_submit_parse_error({"parse_error": parse_error}) == parse_error


def test_wl11021_resolve_turn_submit_parse_error_returns_none_for_missing_payload() -> None:
    # @trace WL-11021
    assert server._resolve_turn_submit_parse_error({}) is None
    assert server._resolve_turn_submit_parse_error({"parse_error": None}) is None


def test_wl11022_build_turn_submit_parse_phase_rejects_missing_approval_diff_only_when_needed() -> None:
    # @trace WL-11022
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan(
        "req", {"session_id": session_id, "input": "x", "requires_approval": False}
    )
    parse_phase = server._build_turn_submit_parse_phase(plan)
    assert parse_phase["requires_approval"] is False
    assert parse_phase["approval_diff"] is None
    assert parse_phase["session_id"] == session_id


def test_wl11023_build_turn_submit_execution_phase_returns_execution_target() -> None:
    # @trace WL-11023
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan("req", {"session_id": session_id, "input": "x"})
    parse_phase = server._build_turn_submit_parse_phase(plan)
    session_id_out, session_out, user_input_out, requires_approval_out, approval_diff_out = (
        server._build_turn_submit_execution_phase(parse_phase)
    )
    assert session_id_out == session_id
    assert session_out["id"] == session_id
    assert user_input_out == "x"
    assert requires_approval_out is False
    assert approval_diff_out is None


def test_wl11024_build_turn_submit_execution_target_rejects_invalid_plan_shape() -> None:
    # @trace WL-11024
    with pytest.raises(ValueError, match="Turn submit execution target unresolved"):
        server._resolve_turn_submit_execution_target(
            {
                "session_id": 1,
                "session": {},
                "user_input": "x",
                "requires_approval": False,
                "approval_diff": None,
            }
        )


def test_wl11025_build_turn_submit_commit_phase_keeps_turn_shape() -> None:
    # @trace WL-11025
    session = {"id": "session-1", "turn_ids": []}
    commit_phase = server._build_turn_submit_commit_phase("session-1", session, "x")
    assert commit_phase["session"] == session
    assert commit_phase["turn"]["session_id"] == "session-1"
    assert commit_phase["turn"]["input"] == "x"
    assert commit_phase["turn"]["status"] == "in_progress"
    resolved = server._build_turn_submit_commit_resolution_phase(commit_phase)
    assert resolved[2] == session


def test_wl11026_resolve_turn_submit_commit_target_rejects_invalid_fields() -> None:
    # @trace WL-11026
    with pytest.raises(ValueError, match="Turn submit commit target unresolved"):
        server._resolve_turn_submit_commit_target({"turn_id": 7, "turn": {}})


def test_wl11027_build_turn_submit_side_effects_phase_keeps_optional_fields() -> None:
    # @trace WL-11027
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }
    side_effects_phase = server._build_turn_submit_side_effects_phase("session-1", "turn-1", turn, "x", False, None)
    assert side_effects_phase["approval_diff"] is None
    assert side_effects_phase["requires_approval"] is False
    assert side_effects_phase["user_input"] == "x"


def test_wl11028_build_turn_submit_side_effects_target_rejects_bad_turn_id() -> None:
    # @trace WL-11028
    with pytest.raises(ValueError, match="Turn submit side-effects target unresolved"):
        server._resolve_turn_submit_side_effects_target(
            {
                "session_id": "session-1",
                "turn_id": 5,
                "turn": {"id": "turn-1"},
                "user_input": "x",
                "requires_approval": False,
                "approval_diff": None,
            }
        )


def test_wl11029_resolve_turn_submit_response_approval_fields_allows_empty_diff() -> None:
    # @trace WL-11029
    fields = server._resolve_turn_submit_response_approval_fields({"id": "approval-1", "status": "requested"})
    assert fields == ("approval-1", "requested", None)
