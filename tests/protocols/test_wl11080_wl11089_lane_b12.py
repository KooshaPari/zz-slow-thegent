"""Lane B12 regressions for WL-11080..WL-11089 on turn/submit response validation and shaping."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


def test_wl11080_extract_turn_submit_response_request_id_allows_none_when_notification() -> None:
    # @trace WL-11080
    phase = server._build_turn_submit_response_phase(False, None, {"id": "turn-1"}, None)
    assert server._extract_turn_submit_response_request_id(phase, False) is None


def test_wl11081_extract_turn_submit_response_request_id_rejects_none_when_required() -> None:
    # @trace WL-11081
    phase = server._build_turn_submit_response_phase(True, None, {"id": "turn-1"}, None)
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id(phase, True)


def test_wl11082_extract_turn_submit_response_request_id_rejects_boolean_when_required() -> None:
    # @trace WL-11082
    phase = server._build_turn_submit_response_phase(True, True, {"id": "turn-1"}, None)
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id(phase, True)


def test_wl11083_extract_turn_submit_response_approval_payload_accepts_none() -> None:
    # @trace WL-11083
    phase = server._build_turn_submit_response_phase(True, "req-11083", {"id": "turn-1"}, None)
    assert server._extract_turn_submit_response_approval_payload(phase) is None


def test_wl11084_extract_turn_submit_approval_payload_diff_accepts_string() -> None:
    # @trace WL-11084
    payload = {"id": "approval-1", "status": "requested", "diff": "--- a\\n+++ b"}
    assert server._extract_turn_submit_approval_payload_diff(payload) == "--- a\\n+++ b"


def test_wl11085_validate_turn_submit_approval_payload_accepts_valid_payload() -> None:
    # @trace WL-11085
    payload = {"id": "approval-1", "status": "requested", "diff": None}
    server._validate_turn_submit_approval_payload(payload)


def test_wl11086_validate_turn_submit_approval_payload_rejects_missing_id() -> None:
    # @trace WL-11086
    payload = {"status": "requested", "diff": None}
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._validate_turn_submit_approval_payload(payload)


def test_wl11087_validate_turn_submit_approval_payload_rejects_missing_status() -> None:
    # @trace WL-11087
    payload = {"id": "approval-1", "diff": None}
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._validate_turn_submit_approval_payload(payload)


def test_wl11088_build_turn_submit_result_payload_flat_includes_approval_when_present() -> None:
    # @trace WL-11088
    turn = {
        "id": "turn-1",
        "session_id": "session-1",
        "status": "needs_approval",
        "input": "x",
        "approval_id": "approval-1",
        "tool_call_id": None,
    }
    approval = {"id": "approval-1", "status": "requested", "diff": "--- a\n+++ b"}

    result = server._build_turn_submit_result_payload_flat(turn, approval)

    assert result["turn"]["id"] == "turn-1"
    assert result["approval"] == approval


def test_wl11089_build_turn_submit_success_response_includes_approval_when_present() -> None:
    # @trace WL-11089
    response = server._build_turn_submit_success_response(
        True,
        "req-11089",
        {
            "id": "turn-1",
            "session_id": "session-1",
            "status": "needs_approval",
            "input": "x",
            "approval_id": "approval-1",
            "tool_call_id": None,
        },
        {"id": "approval-1", "status": "requested", "diff": "--- a\n+++ b"},
    )

    assert response is not None
    assert response["result"]["turn"]["id"] == "turn-1"
    assert response["result"]["approval"]["id"] == "approval-1"
