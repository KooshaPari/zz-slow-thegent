"""Lane C10 regressions for WL-11010..WL-11019 on turn/submit input validation and response helpers."""

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


def test_wl11010_build_turn_submit_phase_plan_rejects_missing_session_id() -> None:
    # @trace WL-11010
    _reset_state()
    plan = server._build_turn_submit_phase_plan("req", {})
    assert plan["parse_error"]["error"]["data"]["reason"] == "session_id_required"


def test_wl11011_build_turn_submit_phase_plan_rejects_non_string_session_id() -> None:
    # @trace WL-11011
    _reset_state()
    plan = server._build_turn_submit_phase_plan("req", {"session_id": 123})
    assert plan["parse_error"]["error"]["data"]["reason"] == "session_id_required"


def test_wl11012_build_turn_submit_phase_plan_rejects_non_string_input() -> None:
    # @trace WL-11012
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan(
        "req", {"session_id": session_id, "input": 17}
    )
    assert plan["parse_error"]["error"]["data"]["reason"] == "input_must_be_string"


def test_wl11013_build_turn_submit_phase_plan_rejects_non_bool_requires_approval_flag() -> (
    None
):
    # @trace WL-11013
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan(
        "req",
        {"session_id": session_id, "requires_approval": "yes", "unified_diff": "diff"},
    )
    assert (
        plan["parse_error"]["error"]["data"]["reason"]
        == "requires_approval_must_be_boolean"
    )


def test_wl11014_build_turn_submit_side_effects_target_keeps_optional_missing_approval_diff() -> (
    None
):
    # @trace WL-11014
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "in_progress",
    }
    resolved = server._resolve_turn_submit_side_effects_target(
        {
            "session_id": "session-1",
            "turn_id": "turn-1",
            "turn": turn,
            "user_input": "x",
            "requires_approval": False,
            "approval_diff": None,
        }
    )
    assert resolved == ("session-1", "turn-1", turn, "x", False, None)


def test_wl11015_extract_turn_submit_response_request_id_rejects_bool_request_id_when_expected() -> (
    None
):
    # @trace WL-11015
    response_phase = server._build_turn_submit_response_phase(
        True, True, {"id": "turn-1"}, None
    )
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id(
            response_phase, request_has_id=True
        )


def test_wl11016_extract_turn_submit_response_request_id_accepts_numeric_request_id() -> (
    None
):
    # @trace WL-11016
    response_phase = server._build_turn_submit_response_phase(
        True, 11.5, {"id": "turn-1"}, None
    )
    assert (
        server._extract_turn_submit_response_request_id(
            response_phase, request_has_id=True
        )
        == 11.5
    )


def test_wl11017_build_turn_submit_success_response_preserves_float_request_id() -> (
    None
):
    # @trace WL-11017
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "status": "completed",
        "input": "x",
        "approval_id": None,
        "tool_call_id": "toolcall-0001",
    }
    response = server._build_turn_submit_success_response(True, 11.5, turn, None)
    assert response is not None
    assert response["id"] == 11.5
    assert response["result"]["turn"] == turn
    assert "approval" not in response["result"]


def test_wl11018_handle_turn_submit_parse_failure_returns_exact_error_payload() -> None:
    # @trace WL-11018
    parse_error = {
        "error": {
            "code": -32602,
            "message": "Invalid params",
            "data": {"reason": "input_must_be_string"},
        }
    }
    assert server._handle_turn_submit_parse_failure(parse_error) == parse_error


def test_wl11019_resolve_turn_submit_response_target_rejects_non_dict_approval_payload_shape() -> (
    None
):
    # @trace WL-11019
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(
            server._build_turn_submit_response_phase(
                True, "req", {"id": "turn-1"}, approval_payload="bad"
            )
        )
