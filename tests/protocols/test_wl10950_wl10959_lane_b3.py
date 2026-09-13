"""Lane B3 regressions for WL-10950..WL-10959 on turn/submit response payload contracts."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


def _turn_payload() -> dict[str, object]:
    return {
        "id": "turn-1",
        "session_id": "session-1",
        "status": "completed",
        "input": "hello",
        "approval_id": None,
        "tool_call_id": "toolcall-1",
    }


def test_wl10950_resolve_turn_submit_response_target_preserves_numeric_request_id() -> None:
    # @trace WL-10950
    phase = server._build_turn_submit_response_phase(True, 7, _turn_payload(), None)
    request_has_id, request_id, _turn, _approval = server._resolve_turn_submit_response_target(phase)
    assert request_has_id is True
    assert request_id == 7


def test_wl10951_resolve_turn_submit_response_target_preserves_string_request_id() -> None:
    # @trace WL-10951
    phase = server._build_turn_submit_response_phase(True, "req-7", _turn_payload(), None)
    request_has_id, request_id, _turn, _approval = server._resolve_turn_submit_response_target(phase)
    assert request_has_id is True
    assert request_id == "req-7"


def test_wl10952_resolve_turn_submit_response_target_allows_none_request_id_for_notifications() -> None:
    # @trace WL-10952
    phase = server._build_turn_submit_response_phase(False, None, _turn_payload(), None)
    request_has_id, request_id, _turn, _approval = server._resolve_turn_submit_response_target(phase)
    assert request_has_id is False
    assert request_id is None


def test_wl10953_build_turn_submit_success_response_suppresses_notification_response() -> None:
    # @trace WL-10953
    response = server._build_turn_submit_success_response(False, "ignored", _turn_payload(), None)
    assert response is None


def test_wl10954_build_turn_submit_success_response_returns_result_envelope_for_request() -> None:
    # @trace WL-10954
    response = server._build_turn_submit_success_response(True, "req-1", _turn_payload(), None)
    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == "req-1"


def test_wl10955_build_turn_submit_result_payload_flat_omits_approval_when_not_present() -> None:
    # @trace WL-10955
    payload = server._build_turn_submit_result_payload_flat(_turn_payload(), None)
    assert "approval" not in payload


def test_wl10956_build_turn_submit_result_payload_flat_includes_approval_when_present() -> None:
    # @trace WL-10956
    approval_payload = {
        "id": "approval-1",
        "status": "requested",
        "diff": "--- a\n+++ b\n",
    }
    payload = server._build_turn_submit_result_payload_flat(_turn_payload(), approval_payload)
    assert payload["approval"] == approval_payload


def test_wl10957_extract_turn_submit_approval_payload_diff_allows_missing_diff() -> None:
    # @trace WL-10957
    assert server._extract_turn_submit_approval_payload_diff({"id": "approval-1", "status": "requested"}) is None


def test_wl10958_extract_turn_submit_approval_payload_id_rejects_empty_string() -> None:
    # @trace WL-10958
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_id({"id": "", "status": "requested"})


def test_wl10959_extract_turn_submit_approval_payload_status_rejects_empty_string() -> None:
    # @trace WL-10959
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_status({"id": "approval-1", "status": ""})
