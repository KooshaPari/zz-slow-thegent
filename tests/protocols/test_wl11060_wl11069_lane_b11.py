"""Lane B11 regressions for WL-11060..WL-11069 on turn/submit response extraction and payload shaping."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


def test_wl11060_extract_turn_submit_response_request_has_id_rejects_non_bool() -> None:
    # @trace WL-11060
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_has_id({"request_has_id": "yes"})


def test_wl11061_extract_turn_submit_response_turn_rejects_non_dict() -> None:
    # @trace WL-11061
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_turn({"turn": "turn-1"})


def test_wl11062_extract_turn_submit_response_approval_payload_rejects_non_dict() -> None:
    # @trace WL-11062
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_approval_payload({"approval_payload": "bad"})


def test_wl11063_resolve_turn_submit_response_approval_fields_returns_expected_tuple() -> None:
    # @trace WL-11063
    approval_id, approval_status, approval_diff = server._resolve_turn_submit_response_approval_fields(
        {"id": "approval-1", "status": "requested", "diff": "--- a\n+++ b"}
    )
    assert approval_id == "approval-1"
    assert approval_status == "requested"
    assert approval_diff == "--- a\n+++ b"


def test_wl11064_extract_turn_submit_approval_payload_id_rejects_empty_value() -> None:
    # @trace WL-11064
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_id({"id": "", "status": "requested", "diff": None})


def test_wl11065_extract_turn_submit_approval_payload_status_rejects_empty_value() -> None:
    # @trace WL-11065
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_status({"id": "approval-1", "status": "", "diff": None})


def test_wl11066_extract_turn_submit_approval_payload_diff_accepts_none() -> None:
    # @trace WL-11066
    assert (
        server._extract_turn_submit_approval_payload_diff({"id": "approval-1", "status": "requested", "diff": None})
        is None
    )


def test_wl11067_resolve_turn_submit_response_target_allows_notification_path() -> None:
    # @trace WL-11067
    response_phase = server._build_turn_submit_response_phase(False, None, {"id": "turn-1"}, None)
    request_has_id, request_id, turn, approval_payload = server._resolve_turn_submit_response_target(response_phase)
    assert request_has_id is False
    assert request_id is None
    assert turn["id"] == "turn-1"
    assert approval_payload is None


def test_wl11068_resolve_turn_submit_response_target_rejects_malformed_approval_payload() -> None:
    # @trace WL-11068
    response_phase = server._build_turn_submit_response_phase(
        True,
        "req-11068",
        {"id": "turn-1"},
        {"id": "approval-1", "status": "requested", "diff": []},
    )
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._resolve_turn_submit_response_target(response_phase)


def test_wl11069_build_turn_submit_success_response_omits_approval_when_absent() -> None:
    # @trace WL-11069
    response = server._build_turn_submit_success_response(
        True,
        "req-11069",
        {
            "id": "turn-1",
            "session_id": "session-1",
            "status": "completed",
            "input": "x",
            "approval_id": None,
            "tool_call_id": "toolcall-1",
        },
        None,
    )
    assert response is not None
    assert response["result"]["turn"]["id"] == "turn-1"
    assert "approval" not in response["result"]
