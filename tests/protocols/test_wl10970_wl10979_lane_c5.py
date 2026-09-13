"""Lane C5 regressions for WL-10970..WL-10979 on turn/submit commit + response plumbing."""

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


def test_wl10970_resolve_turn_submit_parse_error_strips_non_dict_error() -> None:
    # @trace WL-10970
    assert server._resolve_turn_submit_parse_error({"parse_error": {"error": "oops"}}) == {"error": "oops"}
    assert server._resolve_turn_submit_parse_error({"parse_error": "bad"}) is None


def test_wl10971_build_turn_submit_commit_phase_carries_session_and_input() -> None:
    # @trace WL-10971
    session_id = "session-1"
    session = {"id": session_id}
    user_input = "hello"
    plan = server._build_turn_submit_commit_phase(session_id, session, user_input)
    commit_session = plan["session"]
    assert commit_session is session
    assert plan["session"] is session


def test_wl10972_resolve_turn_submit_commit_target_returns_tuple_fields() -> None:
    # @trace WL-10972
    commit_phase = {
        "turn_id": "turn-1",
        "turn": {"id": "turn-1", "session_id": "session-1"},
        "session": {"id": "session-1"},
    }
    turn_id, turn, session = server._resolve_turn_submit_commit_target(commit_phase)
    assert turn_id == "turn-1"
    assert turn == {"id": "turn-1", "session_id": "session-1"}
    assert session == {"id": "session-1"}


def test_wl10973_resolve_turn_submit_commit_target_rejects_invalid_shape() -> None:
    # @trace WL-10973
    with pytest.raises(ValueError, match="Turn submit commit target unresolved"):
        server._resolve_turn_submit_commit_target({"turn_id": 1, "turn": "bad", "session": {"id": "session-1"}})


def test_wl10974_commit_turn_submit_plan_mutates_session_and_turns() -> None:
    # @trace WL-10974
    _reset_state()
    _start_session()
    session = next(iter(SERVER_STATE.sessions.values()))
    turn = {
        "id": "turn-1",
        "session_id": session["id"],
        "status": "in_progress",
        "input": "x",
        "approval_id": None,
        "tool_call_id": None,
    }
    assert SERVER_STATE.turns == {}
    server._commit_turn_submit_plan("turn-1", turn, session)
    assert SERVER_STATE.turns["turn-1"] is turn
    assert session["turn_ids"] == ["turn-1"]


def test_wl10975_handle_turn_submit_parse_failure_bubbles_error_payload() -> None:
    # @trace WL-10975
    parse_error = {
        "error": {
            "code": -32602,
            "message": "Invalid params",
            "data": {"reason": "input_must_be_string"},
        }
    }
    response = server._handle_turn_submit_parse_failure(parse_error)
    assert response == parse_error


def test_wl10976_handle_turn_submit_request_rejects_non_string_input() -> None:
    # @trace WL-10976
    _reset_state()
    session_id = _start_session()
    response, _notifications = process_jsonrpc_line_full(
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
    assert response["error"]["code"] == -32602
    assert response["error"]["data"]["reason"] == "input_must_be_string"


def test_wl10977_resolve_turn_submit_approval_fields_extracts_tuple() -> None:
    # @trace WL-10977
    fields = server._resolve_turn_submit_response_approval_fields(
        {"id": "approval-1", "status": "requested", "diff": "---"}
    )
    assert fields == ("approval-1", "requested", "---")


def test_wl10978_resolve_turn_submit_response_approval_fields_allows_missing_diff() -> None:
    # @trace WL-10978
    fields = server._resolve_turn_submit_response_approval_fields({"id": "approval-2", "status": "requested"})
    assert fields == ("approval-2", "requested", None)


def test_wl10979_build_turn_submit_side_effects_resolution_phase_preserves_inputs() -> None:
    # @trace WL-10979
    phase = server._build_turn_submit_side_effects_phase("session-1", "turn-1", {"id": "turn-1"}, "x", True, "--- diff")
    resolved = server._build_turn_submit_side_effects_resolution_phase(phase)
    assert resolved == ("session-1", "turn-1", {"id": "turn-1"}, "x", True, "--- diff")
