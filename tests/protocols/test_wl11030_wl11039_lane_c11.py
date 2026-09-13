"""Lane C11 regressions for WL-11030..WL-11039 on turn/submit response payload helpers."""

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


def _turn_payload() -> dict[str, object]:
    return {
        "id": "turn-1",
        "session_id": "session-1",
        "status": "completed",
        "input": "x",
        "approval_id": None,
        "tool_call_id": "toolcall-0001",
    }


def test_wl11030_build_turn_submit_result_payload_flat_keeps_turn_only() -> None:
    # @trace WL-11030
    payload = server._build_turn_submit_result_payload_flat(_turn_payload(), None)
    assert payload == {"turn": _turn_payload()}


def test_wl11031_build_turn_submit_result_payload_flat_appends_approval_when_present() -> None:
    # @trace WL-11031
    approval_payload = {"id": "approval-1", "status": "requested", "diff": "---"}
    payload = server._build_turn_submit_result_payload_flat(_turn_payload(), approval_payload)
    assert payload["turn"] == _turn_payload()
    assert payload["approval"] == approval_payload


def test_wl11032_build_turn_submit_response_resolution_phase_returns_input_shapes() -> None:
    # @trace WL-11032
    response_phase = server._build_turn_submit_response_phase(
        True,
        "req",
        _turn_payload(),
        {"id": "approval-1", "status": "requested", "diff": ""},
    )
    values = server._build_turn_submit_response_resolution_phase(response_phase)
    assert values[0] is True
    assert values[1] == "req"
    assert values[2] == _turn_payload()
    assert values[3] == {"id": "approval-1", "status": "requested", "diff": ""}


def test_wl11033_resolve_turn_submit_response_approval_fields_preserves_none() -> None:
    # @trace WL-11033
    assert server._resolve_turn_submit_response_approval_fields(None) == (
        None,
        None,
        None,
    )


def test_wl11034_resolve_turn_submit_response_target_rejects_missing_turn() -> None:
    # @trace WL-11034
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(
            server._build_turn_submit_response_phase(True, "req", turn=None, approval_payload=None)  # type: ignore[arg-type]
        )


def test_wl11035_resolve_turn_submit_response_target_rejects_bad_request_id_when_required() -> None:
    # @trace WL-11035
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(
            server._build_turn_submit_response_phase(True, {"id": 1}, _turn_payload(), None)
        )  # type: ignore[arg-type]


def test_wl11036_extract_turn_submit_approval_payload_diff_accepts_none() -> None:
    # @trace WL-11036
    assert (
        server._extract_turn_submit_approval_payload_diff({"id": "approval-1", "status": "requested", "diff": None})
        is None
    )


def test_wl11037_extract_turn_submit_approval_payload_diff_rejects_non_string() -> None:
    # @trace WL-11037
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_diff({"id": "approval-1", "status": "requested", "diff": 123})


def test_wl11038_build_turn_submit_success_response_uses_integer_request_id() -> None:
    # @trace WL-11038
    response = server._build_turn_submit_success_response(True, 101, _turn_payload(), None)
    assert response is not None
    assert response["id"] == 101
    assert response["result"]["turn"] == _turn_payload()


def test_wl11039_resolve_turn_submit_response_target_rejects_bool_request_id_when_required() -> None:
    # @trace WL-11039
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(
            server._build_turn_submit_response_phase(True, True, _turn_payload(), None)
        )
