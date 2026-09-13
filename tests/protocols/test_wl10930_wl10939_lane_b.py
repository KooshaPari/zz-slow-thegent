"""Lane B regressions for WL-10930..WL-10939 on turn/submit response contracts."""

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


def test_wl10930_build_turn_submit_response_phase_preserves_values() -> None:
    # @trace WL-10930
    turn = {"id": "turn-1"}
    phase = server._build_turn_submit_response_phase(True, "req-1", turn, None)
    assert phase["request_has_id"] is True
    assert phase["request_id"] == "req-1"
    assert phase["turn"] == turn
    assert phase["approval_payload"] is None


def test_wl10931_resolve_turn_submit_response_target_without_approval() -> None:
    # @trace WL-10931
    turn = {"id": "turn-1"}
    phase = server._build_turn_submit_response_phase(False, None, turn, None)
    request_has_id, request_id, resolved_turn, approval_payload = (
        server._resolve_turn_submit_response_target(phase)
    )
    assert request_has_id is False
    assert request_id is None
    assert resolved_turn is turn
    assert approval_payload is None


def test_wl10932_validate_turn_submit_approval_payload_accepts_valid_payload() -> None:
    # @trace WL-10932
    payload = {"id": "approval-1", "status": "requested", "diff": "--- a\n+++ b\n"}
    server._validate_turn_submit_approval_payload(payload)


def test_wl10933_validate_turn_submit_approval_payload_rejects_missing_id() -> None:
    # @trace WL-10933
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._validate_turn_submit_approval_payload(
            {"status": "requested", "diff": "x"}
        )


def test_wl10934_validate_turn_submit_approval_payload_rejects_missing_status() -> None:
    # @trace WL-10934
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._validate_turn_submit_approval_payload({"id": "approval-1", "diff": "x"})


def test_wl10935_validate_turn_submit_approval_payload_rejects_non_string_diff() -> (
    None
):
    # @trace WL-10935
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._validate_turn_submit_approval_payload(
            {"id": "approval-1", "status": "requested", "diff": 123}
        )


def test_wl10936_resolve_turn_submit_response_target_rejects_non_dict_approval_payload() -> (
    None
):
    # @trace WL-10936
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(
            server._build_turn_submit_response_phase(
                True, "req", {"id": "turn-1"}, "bad"
            )
        )


def test_wl10937_handle_turn_submit_request_returns_turn_without_approval() -> None:
    # @trace WL-10937
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit-1",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "lane-b"},
            }
        )
    )
    assert response is not None
    assert response["result"]["turn"]["status"] == "completed"
    assert "approval" not in response["result"]
    assert len(notifications) >= 4


def test_wl10938_handle_turn_submit_request_returns_approval_when_required() -> None:
    # @trace WL-10938
    _reset_state()
    session_id = _start_session()
    response, _notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "submit-2",
                "method": "turn/submit",
                "params": {
                    "session_id": session_id,
                    "input": "lane-b",
                    "requires_approval": True,
                    "unified_diff": "--- a\n+++ b\n@@\n-old\n+new\n",
                },
            }
        )
    )
    assert response is not None
    approval_payload = response["result"]["approval"]
    server._validate_turn_submit_approval_payload(approval_payload)
    assert approval_payload["status"] == "requested"
    assert response["result"]["turn"]["status"] == "awaiting_approval"


def test_wl10939_turn_submit_notification_only_path_emits_side_effects_without_response() -> (
    None
):
    # @trace WL-10939
    _reset_state()
    session_id = _start_session()
    response, notifications = process_jsonrpc_line_full(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "turn/submit",
                "params": {"session_id": session_id, "input": "lane-b"},
            }
        )
    )
    assert response is None
    assert len(notifications) >= 4
    assert notifications[0]["method"] == "turn/started"
    assert notifications[-1]["method"] == "turn/completed"
