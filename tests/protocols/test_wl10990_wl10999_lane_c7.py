"""Lane C7 regressions for WL-10990..WL-10999 on turn/submit response wiring and request flow."""

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
    SERVER_STATE.tool_call_id_counter = 0
    SERVER_STATE.sessions.clear()
    SERVER_STATE.turns.clear()
    SERVER_STATE.approvals.clear()


def _start_session() -> str:
    response, _notifications = process_jsonrpc_line_full(
        json.dumps({"jsonrpc": "2.0", "id": "start", "method": "session/start"})
    )
    assert response is not None
    return response["result"]["session"]["id"]


def _turn_payload() -> dict[str, object]:
    return {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }


def test_wl10990_build_turn_submit_parse_phase_keeps_raw_plan_fields() -> None:
    # @trace WL-10990
    plan = {
        "parse_error": None,
        "session_id": "session-1",
        "session": {"id": "session-1"},
        "user_input": "hey",
        "requires_approval": False,
        "approval_diff": None,
    }
    parse_phase = server._build_turn_submit_parse_phase(plan)
    assert parse_phase == plan


def test_wl10991_resolve_turn_submit_execution_target_rejects_non_string_diff() -> None:
    # @trace WL-10991
    with pytest.raises(ValueError, match="Turn submit execution target unresolved"):
        server._resolve_turn_submit_execution_target(
            {
                "session_id": "session-1",
                "session": {"id": "session-1"},
                "user_input": "hello",
                "requires_approval": True,
                "approval_diff": 1,
            }
        )


def test_wl10992_resolve_turn_submit_response_approval_fields_returns_none_tuple() -> None:
    # @trace WL-10992
    fields = server._resolve_turn_submit_response_approval_fields(None)
    assert fields == (None, None, None)


def test_wl10993_build_turn_submit_success_response_includes_approval_payload() -> None:
    # @trace WL-10993
    turn = _turn_payload()
    approval_payload = {"id": "approval-1", "status": "requested", "diff": "---\n+++\n"}
    response = server._build_turn_submit_success_response(True, 11, turn, approval_payload)
    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["result"]["turn"] == turn
    assert response["result"]["approval"] == approval_payload


def test_wl10994_handle_turn_submit_request_without_id_notifies_approval_request() -> None:
    # @trace WL-10994
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "pending-approval",
                    "requires_approval": True,
                    "unified_diff": "--- a\n+++ b\n",
                },
            }
        )
    )
    assert response is None
    assert notifications[0]["method"] == "turn/started"
    assert notifications[1]["method"] == "item/agentMessage/delta"
    assert notifications[2]["method"] == "approval/requested"


def test_wl10995_resolve_turn_submit_completion_marks_turn_completed_and_adds_tool_call_id() -> None:
    # @trace WL-10995
    turn = _turn_payload()
    notifications: list[dict[str, object]] = []
    server._resolve_turn_submit_completion("session-1", "turn-1", "run", turn, notifications)
    assert turn["status"] == "completed"
    assert turn["tool_call_id"] == "toolcall-0001"
    assert notifications[-1]["method"] == "turn/completed"


def test_wl10996_build_turn_submit_side_effects_phase_preserves_required_fields() -> None:
    # @trace WL-10996
    side_effects_phase = server._build_turn_submit_side_effects_phase(
        "session-1", "turn-1", _turn_payload(), "input", True, "--- diff"
    )
    assert side_effects_phase["session_id"] == "session-1"
    assert side_effects_phase["turn_id"] == "turn-1"
    assert side_effects_phase["user_input"] == "input"
    assert side_effects_phase["requires_approval"] is True
    assert side_effects_phase["approval_diff"] == "--- diff"


def test_wl10997_handle_turn_submit_request_preserves_numeric_request_id() -> None:
    # @trace WL-10997
    _reset_state()
    session_id = _start_session()
    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "numeric-request-id"},
            }
        )
    )
    assert response is not None
    assert response["id"] == 7


def test_wl10998_resolve_turn_submit_side_effects_target_rejects_missing_turn_payload() -> None:
    # @trace WL-10998
    with pytest.raises(ValueError, match="Turn submit side-effects target unresolved"):
        server._resolve_turn_submit_side_effects_target(
            {
                "session_id": "session-1",
                "turn_id": "turn-1",
                "user_input": "x",
                "requires_approval": False,
            }
        )


def test_wl10999_extract_turn_submit_approval_payload_id_rejects_empty_string() -> None:
    # @trace WL-10999
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_id({"id": "", "status": "requested"})
