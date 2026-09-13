"""Lane B9 regressions for WL-11040..WL-11049 on strict turn/submit response and request helpers."""

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


def test_wl11040_extract_turn_submit_approval_payload_id_returns_value() -> None:
    # @trace WL-11040
    assert server._extract_turn_submit_approval_payload_id({"id": "approval-1", "status": "requested"}) == "approval-1"


def test_wl11041_extract_turn_submit_approval_payload_id_rejects_empty_value() -> None:
    # @trace WL-11041
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_id({"id": "", "status": "requested"})


def test_wl11042_extract_turn_submit_approval_payload_status_returns_value() -> None:
    # @trace WL-11042
    assert (
        server._extract_turn_submit_approval_payload_status({"id": "approval-1", "status": "requested"}) == "requested"
    )


def test_wl11043_extract_turn_submit_approval_payload_status_rejects_non_string() -> None:
    # @trace WL-11043
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_status({"id": "approval-1", "status": 0})


def test_wl11044_resolve_turn_submit_response_approval_fields_rejects_empty_payload() -> None:
    # @trace WL-11044
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_approval_fields({"id": "", "status": ""})


def test_wl11045_resolve_turn_submit_response_approval_fields_accepts_none_diff() -> None:
    # @trace WL-11045
    payload = server._resolve_turn_submit_response_approval_fields(
        {"id": "approval-1", "status": "requested", "diff": None}
    )
    assert payload == ("approval-1", "requested", None)


def test_wl11046_build_turn_submit_response_phase_preserves_request_path_without_id() -> None:
    # @trace WL-11046
    phase = server._build_turn_submit_response_phase(
        False, None, {"id": "turn-1"}, {"id": "approval-1", "status": "requested"}
    )
    assert phase == {
        "request_has_id": False,
        "request_id": None,
        "turn": {"id": "turn-1"},
        "approval_payload": {"id": "approval-1", "status": "requested"},
    }


def test_wl11047_handle_turn_submit_request_with_no_request_id_suppresses_result() -> None:
    # @trace WL-11047
    _reset_state()
    session_id = _start_session()
    request = {"jsonrpc": "2.0", "method": "turn/submit", "params": {"session_id": session_id}}
    response, notifications = process_jsonrpc_line_full(json.dumps(request).decode())
    assert response is None
    assert len(notifications) >= 4
    assert notifications[0]["method"] == "turn/started"


def test_wl11048_handle_turn_submit_request_with_parse_error_returns_error_response_without_id() -> None:
    # @trace WL-11048
    _reset_state()
    request = {"jsonrpc": "2.0", "method": "turn/submit", "params": {"session_id": "does-not-exist"}}
    response, notifications = process_jsonrpc_line_full(json.dumps(request).decode())
    assert response is not None
    assert response["error"]["code"] == -32001
    assert response["error"]["message"] == "Session not found"
    assert response["error"]["data"]["session_id"] == "does-not-exist"
    assert notifications == []


def test_wl11049_extract_turn_submit_response_request_id_rejects_none_when_expected() -> None:
    # @trace WL-11049
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id(
            server._build_turn_submit_response_phase(True, None, {"id": "turn-1"}, None),
            request_has_id=True,
        )
