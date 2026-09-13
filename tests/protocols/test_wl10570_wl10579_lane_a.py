"""Lane A regressions for WL-10570..WL-10579 turn/submit phase boundaries."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_commit_phase,
    build_parse_phase,
    build_response_phase,
    build_side_effects_phase,
    resolve_commit_target,
    resolve_parse_target,
    resolve_response_target,
    resolve_side_effects_target,
)


def test_wl10570_parse_phase_keeps_boundary_payload_explicit() -> None:
    # @trace WL-10570
    phase = build_parse_phase(
        "session-1", "hello", request_id="req-1", request_has_id=True
    )
    assert phase["session_id"] == "session-1"
    assert phase["user_input"] == "hello"
    assert phase["request_id"] == "req-1"
    assert phase["request_has_id"] is True


def test_wl10571_parse_target_resolution_is_typed_and_stable() -> None:
    # @trace WL-10571
    phase = build_parse_phase(
        "session-1", "hello", request_id="req-1", request_has_id=True
    )
    assert resolve_parse_target(phase) == ("session-1", "hello", "req-1", True)


def test_wl10572_parse_target_fails_loudly_on_invalid_shape() -> None:
    # @trace WL-10572
    with pytest.raises(ValueError, match="parse target unresolved"):
        resolve_parse_target(
            {
                "session_id": "",
                "user_input": "hello",
                "request_id": "req-1",
                "request_has_id": True,
            }  # type: ignore[arg-type]
        )


def test_wl10573_commit_phase_keeps_mutation_payload_isolated() -> None:
    # @trace WL-10573
    session = {"id": "session-1", "turn_ids": []}
    turn = {"id": "turn-1", "status": "in_progress"}
    phase = build_commit_phase("session-1", session, "turn-1", turn)
    assert phase["session_id"] == "session-1"
    assert phase["session"] is session
    assert phase["turn"] is turn
    assert session["turn_ids"] == []


def test_wl10574_commit_target_resolution_is_typed() -> None:
    # @trace WL-10574
    session = {"id": "session-1", "turn_ids": []}
    turn = {"id": "turn-1", "status": "in_progress"}
    phase = build_commit_phase("session-1", session, "turn-1", turn)
    session_id, resolved_session, turn_id, resolved_turn = resolve_commit_target(phase)
    assert session_id == "session-1"
    assert resolved_session is session
    assert turn_id == "turn-1"
    assert resolved_turn is turn


def test_wl10575_commit_target_fails_loudly_on_invalid_shape() -> None:
    # @trace WL-10575
    with pytest.raises(ValueError, match="commit target unresolved"):
        resolve_commit_target(
            {
                "session_id": "session-1",
                "session": {},
                "turn_id": "turn-1",
                "turn": None,
            }
        )


def test_wl10576_side_effects_phase_keeps_approval_contract_explicit() -> None:
    # @trace WL-10576
    turn = {"id": "turn-1", "status": "in_progress"}
    phase = build_side_effects_phase("session-1", "turn-1", turn, "hello", True, "diff")
    assert phase["requires_approval"] is True
    assert phase["approval_diff"] == "diff"


def test_wl10577_side_effects_target_resolution_preserves_fields() -> None:
    # @trace WL-10577
    turn = {"id": "turn-1", "status": "in_progress"}
    phase = build_side_effects_phase("session-1", "turn-1", turn, "hello", False, None)
    assert resolve_side_effects_target(phase) == (
        "session-1",
        "turn-1",
        turn,
        "hello",
        False,
        None,
    )


def test_wl10578_response_phase_preserves_turn_and_approval_payload() -> None:
    # @trace WL-10578
    turn = {"id": "turn-1"}
    approval_payload = {"id": "approval-1"}
    phase = build_response_phase(True, "req-1", turn, approval_payload)
    assert phase["request_has_id"] is True
    assert phase["request_id"] == "req-1"
    assert phase["turn"] is turn
    assert phase["approval_payload"] is approval_payload


def test_wl10579_response_target_fails_loudly_on_invalid_shape() -> None:
    # @trace WL-10579
    with pytest.raises(ValueError, match="response target unresolved"):
        resolve_response_target(
            {
                "request_has_id": True,
                "request_id": "req-1",
                "turn": {"id": "turn-1"},
                "approval_payload": "bad",
            }
        )
