"""Lane B10 regressions for WL-11050..WL-11059 on turn/submit validation and response helpers."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


def test_wl11050_validate_turn_submit_approval_payload_accepts_valid_payload() -> None:
    # @trace WL-11050
    payload = {"id": "approval-1", "status": "requested", "diff": "--- a\n+++ b\n"}
    server._validate_turn_submit_approval_payload(payload)


def test_wl11051_validate_turn_submit_approval_payload_rejects_missing_id() -> None:
    # @trace WL-11051
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._validate_turn_submit_approval_payload({"status": "requested", "diff": "---"})


def test_wl11052_validate_turn_submit_approval_payload_rejects_missing_status() -> None:
    # @trace WL-11052
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._validate_turn_submit_approval_payload({"id": "approval-1", "diff": "---"})


def test_wl11053_validate_turn_submit_approval_payload_rejects_bad_diff_type() -> None:
    # @trace WL-11053
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._validate_turn_submit_approval_payload({"id": "approval-1", "status": "requested", "diff": []})


def test_wl11054_extract_turn_submit_response_request_id_returns_request_id_for_id_path() -> None:
    # @trace WL-11054
    phase = server._build_turn_submit_response_phase(True, "req-11054", {"id": "turn-1"}, None)
    assert server._extract_turn_submit_response_request_id(phase, True) == "req-11054"


def test_wl11055_extract_turn_submit_response_request_id_allows_none_when_not_required() -> None:
    # @trace WL-11055
    phase = server._build_turn_submit_response_phase(False, None, {"id": "turn-1"}, None)
    assert server._extract_turn_submit_response_request_id(phase, False) is None


def test_wl11056_extract_turn_submit_response_request_id_rejects_non_request_id_when_required() -> None:
    # @trace WL-11056
    phase = server._build_turn_submit_response_phase(True, ["bad"], {"id": "turn-1"}, None)
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id(phase, True)


def test_wl11057_handle_turn_submit_parse_failure_passthrough() -> None:
    # @trace WL-11057
    parse_error = {"error": "bad", "code": -32001}
    assert server._handle_turn_submit_parse_failure(parse_error) == parse_error


def test_wl11058_build_turn_submit_success_response_includes_approval_payload() -> None:
    # @trace WL-11058
    approval_payload = {"id": "approval-1", "status": "requested", "diff": "---"}
    response = server._build_turn_submit_success_response(
        True,
        "req-11058",
        {
            "id": "turn-1",
            "session_id": "session-1",
            "status": "completed",
            "input": "x",
            "approval_id": None,
            "tool_call_id": None,
        },
        approval_payload,
    )
    assert response is not None
    assert response["result"]["approval"] == approval_payload


def test_wl11059_build_turn_submit_response_resolution_phase_preserves_turn_submit_payloads() -> None:
    # @trace WL-11059
    phase = server._build_turn_submit_response_phase(
        True,
        "req-11059",
        {
            "id": "turn-1",
            "session_id": "session-1",
            "status": "completed",
            "input": "x",
            "approval_id": None,
            "tool_call_id": None,
        },
        {"id": "approval-1", "status": "requested", "diff": None},
    )
    request_has_id, request_id, turn, approval_payload = server._build_turn_submit_response_resolution_phase(phase)
    assert request_has_id is True
    assert request_id == "req-11059"
    assert turn["id"] == "turn-1"
    assert approval_payload == {"id": "approval-1", "status": "requested", "diff": None}
