"""Lane B4 regressions for WL-10960..WL-10969 on turn/submit contract boundaries."""

from __future__ import annotations

import orjson as json

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


def test_wl10960_turn_submit_phase_plan_defaults_input_to_empty_string() -> None:
    # @trace WL-10960
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan("req", {"session_id": session_id})
    parse_phase = server._build_turn_submit_parse_phase(plan)
    assert parse_phase["parse_error"] is None
    assert parse_phase["user_input"] == ""
    assert parse_phase["requires_approval"] is False
    assert parse_phase["approval_diff"] is None


def test_wl10961_extract_required_approval_diff_prefers_unified_diff_over_diff() -> None:
    # @trace WL-10961
    _reset_state()
    approval_diff, parse_error = server._extract_required_approval_diff("req", {"unified_diff": "x", "diff": "y"})
    assert parse_error is None
    assert approval_diff == "x"


def test_wl10962_extract_required_approval_diff_supports_diff_alias() -> None:
    # @trace WL-10962
    _reset_state()
    approval_diff, parse_error = server._extract_required_approval_diff("req", {"diff": "--- diff"})
    assert parse_error is None
    assert approval_diff == "--- diff"


def test_wl10963_extract_required_approval_diff_rejects_missing_diff_when_required() -> None:
    # @trace WL-10963
    _reset_state()
    approval_diff, parse_error = server._extract_required_approval_diff("req", {})
    assert approval_diff is None
    assert parse_error is not None
    assert parse_error["error"]["data"]["reason"] == "diff_required_when_requires_approval"


def test_wl10964_extract_required_approval_diff_rejects_empty_diff_when_required() -> None:
    # @trace WL-10964
    _reset_state()
    approval_diff, parse_error = server._extract_required_approval_diff("req", {"unified_diff": "   "})
    assert approval_diff is None
    assert parse_error is not None
    assert parse_error["error"]["data"]["reason"] == "diff_must_be_non_empty_string"


def test_wl10965_turn_submit_phase_plan_rejects_non_string_approval_diff() -> None:
    # @trace WL-10965
    _reset_state()
    session_id = _start_session()
    plan = server._build_turn_submit_phase_plan(
        "req",
        {
            "session_id": session_id,
            "input": "b4",
            "requires_approval": True,
            "unified_diff": 123,
        },
    )
    assert plan["parse_error"]["error"]["data"]["reason"] == "diff_must_be_string"


def test_wl10966_turn_submit_side_effects_resolution_phase_returns_all_fields() -> None:
    # @trace WL-10966
    turn = {"id": "turn-1"}
    phase = server._build_turn_submit_side_effects_phase("session-1", "turn-1", turn, "input", True, "diff")
    resolved = server._build_turn_submit_side_effects_resolution_phase(phase)
    assert resolved == ("session-1", "turn-1", turn, "input", True, "diff")


def test_wl10967_turn_submit_response_resolution_phase_routes_request_id_policy() -> None:
    # @trace WL-10967
    turn = {"id": "turn-1"}
    response_phase = server._build_turn_submit_response_phase(True, 7, turn, None)
    resolved = server._build_turn_submit_response_resolution_phase(response_phase)
    assert resolved[0] is True
    assert resolved[1] == 7
    assert resolved[2] is turn
    assert resolved[3] is None


def test_wl10968_apply_turn_submit_side_effects_fires_started_notifications_before_payload() -> None:
    # @trace WL-10968
    notifications: list[dict[str, object]] = []
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }
    payload = server._apply_turn_submit_side_effects("session-1", "turn-1", turn, "b4", True, "diff", notifications)
    assert payload is not None
    assert notifications[0]["method"] == "turn/started"
    assert notifications[1]["method"] == "item/agentMessage/delta"
    assert notifications[2]["method"] == "approval/requested"


def test_wl10969_handle_turn_submit_request_with_invalid_session_id_returns_parse_error() -> None:
    # @trace WL-10969
    _reset_state()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit-1",
                "method": "turn/submit",
                "params": {"session_id": "missing", "input": "b4"},
            }
        )
    )
    assert response is not None
    assert response["error"]["code"] == -32001
    assert response["error"]["message"] == "Session not found"
    assert response["error"]["data"]["session_id"] == "missing"
    assert notifications == []
    assert len(SERVER_STATE.turns) == 0
