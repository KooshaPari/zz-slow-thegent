"""Lane C6 regressions for WL-10980..WL-10989 on turn/submit validation and side-effect wiring."""

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


def test_wl10980_turn_submit_should_emit_response_tracks_request_id_presence() -> None:
    # @trace WL-10980
    assert server._turn_submit_should_emit_response(False) is False
    assert server._turn_submit_should_emit_response(True) is True


def test_wl10981_build_turn_submit_execution_plan_returns_id_and_turn_record() -> None:
    # @trace WL-10981
    turn_id, turn = server._build_turn_submit_execution_plan("session-1", "hello")
    assert isinstance(turn_id, str)
    assert turn_id.startswith("turn-")
    assert turn == {
        "id": turn_id,
        "session_id": "session-1",
        "input": "hello",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }


def test_wl10982_resolve_turn_submit_execution_target_rejects_bad_shape() -> None:
    # @trace WL-10982
    with pytest.raises(ValueError, match="Turn submit execution target unresolved"):
        server._resolve_turn_submit_execution_target(
            {
                "session_id": None,
                "session": {},
                "user_input": "x",
                "requires_approval": False,
            }
        )


def test_wl10983_execute_turn_submit_with_approval_stores_payload_and_notifications() -> None:
    # @trace WL-10983
    _reset_state()
    session_id = _start_session()
    turn_id, turn = server._build_turn_submit_execution_plan(session_id, "b6")
    session = next(iter(SERVER_STATE.sessions.values()))
    SERVER_STATE.turns[turn_id] = turn
    session["turn_ids"].append(turn_id)
    notifications: list[dict[str, object]] = []
    payload = server._execute_turn_submit_with_approval(
        session_id,
        turn_id,
        turn,
        "---\n+++\n",
        notifications,
    )
    assert payload == {
        "id": "approval-0001",
        "status": "requested",
        "diff": "---\n+++\n",
    }
    assert turn["status"] == "awaiting_approval"
    assert turn["approval_id"] == "approval-0001"
    assert SERVER_STATE.approvals["approval-0001"]["status"] == "requested"
    assert notifications[0]["method"] == "approval/requested"
    assert notifications[0]["params"]["approval_id"] == "approval-0001"


def test_wl10984_execute_turn_submit_without_approval_fires_no_approval_path() -> None:
    # @trace WL-10984
    _reset_state()
    notifications: list[dict[str, object]] = []
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "b6",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }
    server._execute_turn_submit_without_approval("session-1", "turn-1", "b6", turn, notifications)
    assert turn["status"] == "completed"
    assert turn["tool_call_id"] == "toolcall-0001"
    assert notifications[0]["method"] == "item/toolCall/started"
    assert notifications[1]["method"] == "item/toolCall/completed"
    assert notifications[2]["method"] == "turn/completed"


def test_wl10985_apply_turn_submit_side_effects_without_approval_returns_none_and_mutates_turn() -> None:
    # @trace WL-10985
    _reset_state()
    notifications: list[dict[str, object]] = []
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }
    approval_payload = server._apply_turn_submit_side_effects(
        "session-1", "turn-1", turn, "x", False, None, notifications
    )
    assert approval_payload is None
    assert turn["status"] == "completed"
    assert len(notifications) == 5
    assert notifications[0]["method"] == "turn/started"
    assert notifications[1]["method"] == "item/agentMessage/delta"
    assert notifications[2]["method"] == "item/toolCall/started"
    assert notifications[3]["method"] == "item/toolCall/completed"
    assert notifications[4]["method"] == "turn/completed"


def test_wl10986_apply_turn_submit_side_effects_with_approval_keeps_approval_payload_shape() -> None:
    # @trace WL-10986
    _reset_state()
    notifications: list[dict[str, object]] = []
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "x",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }
    approval_payload = server._apply_turn_submit_side_effects(
        "session-1", "turn-1", turn, "x", True, "diff", notifications
    )
    assert approval_payload == {
        "id": "approval-0001",
        "status": "requested",
        "diff": "diff",
    }
    assert turn["status"] == "awaiting_approval"
    assert turn["approval_id"] == "approval-0001"
    assert notifications[0]["method"] == "turn/started"
    assert notifications[1]["method"] == "item/agentMessage/delta"
    assert notifications[2]["method"] == "approval/requested"


def test_wl10987_resolve_turn_submit_side_effects_target_rejects_non_bool_requires_approval() -> None:
    # @trace WL-10987
    with pytest.raises(ValueError, match="Turn submit side-effects target unresolved"):
        server._resolve_turn_submit_side_effects_target(
            {
                "session_id": "session-1",
                "turn_id": "turn-1",
                "turn": {},
                "user_input": "x",
                "requires_approval": "yes",
                "approval_diff": None,
            }
        )


def test_wl10988_build_turn_submit_response_phase_rehydrates_request_route() -> None:
    # @trace WL-10988
    turn = {"id": "turn-1", "session_id": "session-1", "status": "completed"}
    approval_payload = {"id": "approval-1", "status": "requested", "diff": "diff"}
    phase = server._build_turn_submit_response_phase(True, "req-1", turn, approval_payload)
    assert phase == {
        "request_has_id": True,
        "request_id": "req-1",
        "turn": turn,
        "approval_payload": approval_payload,
    }


def test_wl10989_validate_turn_submit_approval_payload_rejects_missing_fields() -> None:
    # @trace WL-10989
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._validate_turn_submit_approval_payload({"id": "approval-1"})
    server._validate_turn_submit_approval_payload({"id": "approval-1", "status": "requested"})
    server._validate_turn_submit_approval_payload({"id": "approval-1", "status": "requested", "diff": None})
