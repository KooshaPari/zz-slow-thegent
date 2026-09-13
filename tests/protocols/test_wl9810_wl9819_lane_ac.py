"""Lane AC regressions for WL-9810..WL-9819 on turn/submit phase-plan flow."""

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


def test_wl9810_phase_plan_separates_parse_from_execution_state() -> None:
    # @trace WL-9810
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan("req", {"session_id": session_id, "input": "ac"})
    assert plan["parse_error"] is None
    assert plan["session_id"] == session_id
    assert plan["requires_approval"] is False
    assert plan["approval_diff"] is None


def test_wl9811_parse_error_resolution_returns_session_validation_error() -> None:
    # @trace WL-9811
    _reset_state()
    plan = server._build_turn_submit_phase_plan("req", {"session_id": "session-404", "input": "ac"})
    parse_error = server._resolve_turn_submit_parse_error(plan)
    assert parse_error is not None
    assert parse_error["error"]["code"] == -32001


def test_wl9812_emit_response_policy_is_explicit_for_sync_and_async() -> None:
    # @trace WL-9812
    assert server._turn_submit_should_emit_response(True) is True
    assert server._turn_submit_should_emit_response(False) is False


def test_wl9813_execution_target_resolution_returns_typed_tuple() -> None:
    # @trace WL-9813
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan("req", {"session_id": session_id, "input": "ac"})
    parsed_session_id, session, user_input, requires_approval, approval_diff = (
        server._resolve_turn_submit_execution_target(plan)
    )
    assert parsed_session_id == session_id
    assert isinstance(session, dict)
    assert user_input == "ac"
    assert requires_approval is False
    assert approval_diff is None


def test_wl9814_execution_target_resolution_fails_for_unresolved_state() -> None:
    # @trace WL-9814
    with pytest.raises(ValueError, match="Turn submit execution target unresolved"):
        server._resolve_turn_submit_execution_target(
            {"session_id": None, "session": None, "user_input": None, "requires_approval": None, "approval_diff": None}
        )


def test_wl9815_notification_submit_applies_side_effects_without_response() -> None:
    # @trace WL-9815
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {"jsonrpc": "2.0", "method": "turn/submit", "params": {"session_id": session_id, "input": "ac"}}
        )
    )
    assert response is None
    assert len(notifications) >= 4
    turn_id = SERVER_STATE.sessions[session_id]["turn_ids"][0]
    assert SERVER_STATE.turns[turn_id]["status"] == "completed"


def test_wl9816_plan_rejects_non_boolean_requires_approval() -> None:
    # @trace WL-9816
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan(
        "req", {"session_id": session_id, "input": "ac", "requires_approval": "yes"}
    )
    parse_error = server._resolve_turn_submit_parse_error(plan)
    assert parse_error is not None
    assert parse_error["error"]["data"]["reason"] == "requires_approval_must_be_boolean"


def test_wl9817_started_notifications_are_emitted_before_completion() -> None:
    # @trace WL-9817
    _reset_state()
    session_id = _start_session()
    _response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "ac"},
            }
        )
    )
    assert notifications[0]["method"] == "turn/started"
    assert notifications[1]["method"] == "item/agentMessage/delta"
    assert notifications[-1]["method"] == "turn/completed"


def test_wl9818_non_approval_execution_moves_turn_to_completed() -> None:
    # @trace WL-9818
    _reset_state()
    session_id = _start_session()
    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "ac"},
            }
        )
    )
    assert response is not None
    turn = response["result"]["turn"]
    assert turn["status"] == "completed"
    assert turn["tool_call_id"] is not None


def test_wl9819_parse_failure_does_not_mutate_turn_state() -> None:
    # @trace WL-9819
    _reset_state()
    session_id = _start_session()
    turn_count_before = len(SERVER_STATE.turns)
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": 42},
            }
        )
    )
    assert response is not None
    assert response["error"]["data"]["reason"] == "input_must_be_string"
    assert notifications == []
    assert len(SERVER_STATE.turns) == turn_count_before
