"""Lane C13 regressions for WL-11090..WL-11099 on turn/submit response target extraction guards."""

from __future__ import annotations

import pytest

from thegent.protocols import jsonrpc_agent_server as server


def test_wl11090_extract_turn_submit_response_request_has_id_accepts_true() -> None:
    # @trace WL-11090
    assert server._extract_turn_submit_response_request_has_id({"request_has_id": True}) is True


def test_wl11091_extract_turn_submit_response_request_has_id_rejects_non_boolean() -> None:
    # @trace WL-11091
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_request_has_id({"request_has_id": "true"})


def test_wl11092_extract_turn_submit_response_turn_rejects_non_mapping() -> None:
    # @trace WL-11092
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_turn({"turn": "turn-1"})


def test_wl11093_extract_turn_submit_response_approval_payload_rejects_non_mapping() -> None:
    # @trace WL-11093
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_response_approval_payload({"approval_payload": "bad"})


def test_wl11094_extract_turn_submit_approval_payload_id_rejects_empty_string() -> None:
    # @trace WL-11094
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_id({"id": "", "status": "requested"})


def test_wl11095_extract_turn_submit_approval_payload_status_rejects_empty_string() -> None:
    # @trace WL-11095
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_status({"id": "approval-1", "status": ""})


def test_wl11096_extract_turn_submit_approval_payload_diff_accepts_none() -> None:
    # @trace WL-11096
    assert server._extract_turn_submit_approval_payload_diff({"id": "approval-1", "status": "requested"}) is None


def test_wl11097_extract_turn_submit_approval_payload_diff_rejects_non_string() -> None:
    # @trace WL-11097
    with pytest.raises(ValueError, match="Turn submit response target unresolved"):
        server._extract_turn_submit_approval_payload_diff({"id": "approval-1", "status": "requested", "diff": 7})


def test_wl11098_resolve_turn_submit_response_target_returns_tuple_for_valid_payload() -> None:
    # @trace WL-11098
    phase = server._build_turn_submit_response_phase(
        True,
        "req-11098",
        {"id": "turn-1"},
        {"id": "approval-1", "status": "requested", "diff": "--- a\n+++ b"},
    )

    request_has_id, request_id, turn, approval = server._resolve_turn_submit_response_target(phase)

    assert request_has_id is True
    assert request_id == "req-11098"
    assert turn["id"] == "turn-1"
    assert approval is not None
    assert approval["id"] == "approval-1"


def test_wl11099_build_turn_submit_response_resolution_phase_returns_projection_tuple() -> None:
    # @trace WL-11099
    phase = server._build_turn_submit_response_phase(
        False,
        None,
        {"id": "turn-1"},
        {"id": "approval-1", "status": "requested", "diff": None},
    )

    request_has_id, request_id, turn, approval = server._build_turn_submit_response_resolution_phase(phase)

    assert request_has_id is False
    assert request_id is None
    assert turn == {"id": "turn-1"}
    assert approval == {"id": "approval-1", "status": "requested", "diff": None}
