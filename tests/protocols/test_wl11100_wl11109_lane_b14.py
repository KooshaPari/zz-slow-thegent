"""Lane B14 regressions for WL-11100..WL-11109 on turn/submit planning, side-effects, and commit flow."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


@pytest.fixture(autouse=True)
def _reset_server_state() -> None:
    original = server.SERVER_STATE
    server.SERVER_STATE = server.InMemoryJsonRpcState()
    try:
        yield
    finally:
        server.SERVER_STATE = original


def test_wl11100_build_turn_submit_phase_plan_rejects_non_string_input() -> None:
    # @trace WL-11100
    session = server._build_session_start_record()
    plan = server._build_turn_submit_phase_plan(
        "req-11100",
        {"session_id": session["id"], "input": 7},
    )
    assert plan == {"parse_error": server._error_response("req-11100", server._invalid_params("input_must_be_string"))}


def test_wl11101_build_turn_submit_phase_plan_rejects_non_bool_requires_approval() -> None:
    # @trace WL-11101
    session = server._build_session_start_record()
    plan = server._build_turn_submit_phase_plan(
        "req-11101",
        {"session_id": session["id"], "input": "hello", "requires_approval": "yes"},
    )
    assert plan == {
        "parse_error": server._error_response("req-11101", server._invalid_params("requires_approval_must_be_boolean"))
    }


def test_wl11102_build_turn_submit_phase_plan_requires_diff_when_approval_enabled() -> None:
    # @trace WL-11102
    session = server._build_session_start_record()
    plan = server._build_turn_submit_phase_plan(
        "req-11102",
        {"session_id": session["id"], "input": "hello", "requires_approval": True},
    )
    assert plan == {
        "parse_error": server._error_response(
            "req-11102",
            server._invalid_params("diff_required_when_requires_approval"),
        )
    }


def test_wl11103_handle_turn_submit_request_returns_parse_failure_response() -> None:
    # @trace WL-11103
    session = server._build_session_start_record()
    notifications: list[dict[str, object]] = []

    response = server._handle_turn_submit_request(
        True,
        "req-11103",
        {"session_id": session["id"], "input": []},
        notifications,
    )

    assert response == server._error_response("req-11103", server._invalid_params("input_must_be_string"))
    assert notifications == []


def test_wl11104_handle_turn_submit_request_notification_path_commits_and_emits_events() -> None:
    # @trace WL-11104
    session = server._build_session_start_record()
    notifications: list[dict[str, object]] = []

    response = server._handle_turn_submit_request(
        False,
        None,
        {"session_id": session["id"], "input": "hello"},
        notifications,
    )

    assert response is None
    assert len(session["turn_ids"]) == 1
    turn_id = session["turn_ids"][0]
    turn = server.SERVER_STATE.turns[turn_id]
    assert turn["status"] == "completed"
    assert turn["tool_call_id"] is not None
    methods = [item["method"] for item in notifications]
    assert methods == [
        "turn/started",
        "item/agentMessage/delta",
        "item/toolCall/started",
        "item/toolCall/completed",
        "turn/completed",
    ]


def test_wl11105_handle_turn_submit_request_response_path_returns_approval_payload() -> None:
    # @trace WL-11105
    session = server._build_session_start_record()
    notifications: list[dict[str, object]] = []

    response = server._handle_turn_submit_request(
        True,
        "req-11105",
        {
            "session_id": session["id"],
            "input": "hello",
            "requires_approval": True,
            "diff": "--- a\n+++ b",
        },
        notifications,
    )

    assert response is not None
    assert response["id"] == "req-11105"
    approval = response["result"]["approval"]
    assert approval["status"] == "requested"
    turn = response["result"]["turn"]
    assert turn["status"] == "awaiting_approval"
    assert turn["approval_id"] == approval["id"]
    assert notifications[-1]["method"] == "approval/requested"


def test_wl11106_apply_turn_submit_side_effects_completes_when_approval_not_required() -> None:
    # @trace WL-11106
    notifications: list[dict[str, object]] = []
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "hello",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }

    approval_payload = server._apply_turn_submit_side_effects(
        "session-1",
        "turn-1",
        turn,
        "hello",
        False,
        None,
        notifications,
    )

    assert approval_payload is None
    assert turn["status"] == "completed"
    assert turn["tool_call_id"] is not None


def test_wl11107_apply_turn_submit_side_effects_returns_approval_payload_when_required() -> None:
    # @trace WL-11107
    notifications: list[dict[str, object]] = []
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "input": "hello",
        "status": "in_progress",
        "approval_id": None,
        "tool_call_id": None,
    }

    approval_payload = server._apply_turn_submit_side_effects(
        "session-1",
        "turn-1",
        turn,
        "hello",
        True,
        "--- a\n+++ b",
        notifications,
    )

    assert approval_payload is not None
    assert approval_payload["status"] == "requested"
    assert turn["status"] == "awaiting_approval"
    assert turn["approval_id"] == approval_payload["id"]


def test_wl11108_build_turn_submit_execution_plan_initializes_in_progress_turn() -> None:
    # @trace WL-11108
    turn_id, turn = server._build_turn_submit_execution_plan("session-1", "hello")

    assert turn_id == turn["id"]
    assert turn["status"] == "in_progress"
    assert turn["approval_id"] is None
    assert turn["tool_call_id"] is None


def test_wl11109_commit_turn_submit_plan_persists_turn_and_session_link() -> None:
    # @trace WL-11109
    session = server._build_session_start_record()
    turn_id, turn = server._build_turn_submit_execution_plan(session["id"], "hello")

    server._commit_turn_submit_plan(turn_id, turn, session)

    assert server.SERVER_STATE.turns[turn_id] == turn
    assert session["turn_ids"] == [turn_id]
