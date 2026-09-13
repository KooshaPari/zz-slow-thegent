"""Lane C12 regressions for WL-11070..WL-11079 on turn/submit response extraction and emission gating."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


def test_wl11070_extract_turn_submit_response_approval_id_returns_none_for_absent_payload() -> (
    None
):
    # @trace WL-11070
    assert server._extract_turn_submit_response_approval_id(None) is None


def test_wl11071_extract_turn_submit_response_approval_status_returns_none_for_absent_payload() -> (
    None
):
    # @trace WL-11071
    assert server._extract_turn_submit_response_approval_status(None) is None


def test_wl11072_extract_turn_submit_response_approval_diff_returns_none_for_absent_payload() -> (
    None
):
    # @trace WL-11072
    assert server._extract_turn_submit_response_approval_diff(None) is None


def test_wl11073_resolve_turn_submit_response_approval_fields_returns_none_tuple_for_absent_payload() -> (
    None
):
    # @trace WL-11073
    assert server._resolve_turn_submit_response_approval_fields(None) == (
        None,
        None,
        None,
    )


def test_wl11074_extract_turn_submit_response_request_id_accepts_string_when_required() -> (
    None
):
    # @trace WL-11074
    phase = server._build_turn_submit_response_phase(
        True, "req-11074", {"id": "turn-1"}, None
    )
    assert server._extract_turn_submit_response_request_id(phase, True) == "req-11074"


def test_wl11075_extract_turn_submit_response_request_id_accepts_integer_when_required() -> (
    None
):
    # @trace WL-11075
    phase = server._build_turn_submit_response_phase(
        True, 11075, {"id": "turn-1"}, None
    )
    assert server._extract_turn_submit_response_request_id(phase, True) == 11075


def test_wl11076_build_turn_submit_success_response_returns_none_for_notification_path() -> (
    None
):
    # @trace WL-11076
    response = server._build_turn_submit_success_response(
        False,
        None,
        {
            "id": "turn-1",
            "session_id": "session-1",
            "status": "completed",
            "input": "x",
            "approval_id": None,
            "tool_call_id": None,
        },
        None,
    )
    assert response is None


def test_wl11077_resolve_turn_submit_response_target_rejects_missing_request_has_id() -> (
    None
):
    # @trace WL-11077
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(
            {"request_id": "req-11077", "turn": {"id": "turn-1"}}
        )


def test_wl11078_build_turn_submit_response_resolution_phase_rejects_missing_turn() -> (
    None
):
    # @trace WL-11078
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._build_turn_submit_response_resolution_phase(
            {
                "request_has_id": True,
                "request_id": "req-11078",
                "approval_payload": None,
            }
        )


def test_wl11079_build_turn_submit_response_phase_sets_all_expected_fields() -> None:
    # @trace WL-11079
    turn = {"id": "turn-1"}
    approval = {"id": "approval-1", "status": "requested", "diff": None}
    phase = server._build_turn_submit_response_phase(True, "req-11079", turn, approval)
    assert phase == {
        "request_has_id": True,
        "request_id": "req-11079",
        "turn": turn,
        "approval_payload": approval,
    }
