"""Lane C14 regressions for WL-11100..WL-11109 on turn/submit response target extraction guards."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


def test_wl11100_extract_turn_submit_response_request_id_accepts_none_for_notification() -> None:
    # @trace WL-11100
    assert server._extract_turn_submit_response_request_id({"request_id": None}, False) is None


def test_wl11101_extract_turn_submit_response_request_id_rejects_none_for_request() -> None:
    # @trace WL-11101
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id({"request_id": None}, True)


def test_wl11102_extract_turn_submit_response_request_id_rejects_invalid_type_for_request() -> None:
    # @trace WL-11102
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_id({"request_id": []}, True)


def test_wl11103_extract_turn_submit_response_approval_id_returns_none_when_missing_payload() -> None:
    # @trace WL-11103
    assert server._extract_turn_submit_response_approval_id(None) is None


def test_wl11104_extract_turn_submit_response_approval_status_returns_none_when_missing_payload() -> None:
    # @trace WL-11104
    assert server._extract_turn_submit_response_approval_status(None) is None


def test_wl11105_extract_turn_submit_response_approval_diff_returns_none_when_missing_payload() -> None:
    # @trace WL-11105
    assert server._extract_turn_submit_response_approval_diff(None) is None


def test_wl11106_resolve_turn_submit_response_approval_fields_returns_full_tuple() -> None:
    # @trace WL-11106
    approval_id, approval_status, approval_diff = server._resolve_turn_submit_response_approval_fields(
        {"id": "approval-1", "status": "requested", "diff": "--- a\n+++ b"}
    )

    assert approval_id == "approval-1"
    assert approval_status == "requested"
    assert approval_diff == "--- a\n+++ b"


def test_wl11107_resolve_turn_submit_response_target_keeps_none_approval_payload() -> None:
    # @trace WL-11107
    phase = server._build_turn_submit_response_phase(True, "req-11107", {"id": "turn-1"}, None)

    request_has_id, request_id, turn, approval = server._resolve_turn_submit_response_target(phase)

    assert request_has_id is True
    assert request_id == "req-11107"
    assert turn == {"id": "turn-1"}
    assert approval is None


def test_wl11108_resolve_turn_submit_response_target_rejects_invalid_approval_id() -> None:
    # @trace WL-11108
    phase = server._build_turn_submit_response_phase(
        True,
        "req-11108",
        {"id": "turn-1"},
        {"id": "", "status": "requested", "diff": None},
    )

    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(phase)


def test_wl11109_build_turn_submit_response_resolution_phase_rejects_invalid_request_id_for_requests() -> None:
    # @trace WL-11109
    phase = server._build_turn_submit_response_phase(
        True,
        None,
        {"id": "turn-1"},
        None,
    )

    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._build_turn_submit_response_resolution_phase(phase)
