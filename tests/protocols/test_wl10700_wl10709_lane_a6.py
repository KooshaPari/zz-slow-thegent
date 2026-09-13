"""Lane A6 regressions for WL-10700..WL-10709 boundary slicing helpers."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_observability_event_phase,
    build_policy_match_phase,
    build_queue_priority_phase,
    build_retry_loop_phase,
    build_session_state_update_phase,
    build_workflow_guard_phase,
    resolve_observability_serialization_target,
    resolve_policy_enforcement_plan_target,
    resolve_queue_execution_target,
    resolve_session_persistence_plan_target,
    resolve_terminal_outcome_target,
    resolve_workflow_execution_target,
)


def test_wl10700_queue_priority_is_separated_from_execution_window() -> None:
    # @trace WL-10700
    phase = build_queue_priority_phase("critical", ["w-10700-a", "w-10700-b"], 8)
    assert resolve_queue_execution_target(phase) == (
        "critical",
        ["w-10700-a", "w-10700-b"],
        8,
    )


def test_wl10701_observability_payload_is_separated_from_payload_format() -> None:
    # @trace WL-10701
    payload = {"status": "ok", "count": 2}
    phase = build_observability_event_phase("evt-10701", payload, "json")
    assert resolve_observability_serialization_target(phase) == (
        "evt-10701",
        payload,
        "json",
    )


def test_wl10702_workflow_guard_checks_precede_execution_step_resolution() -> None:
    # @trace WL-10702
    guards = {"policy": True, "queue": True}
    phase = build_workflow_guard_phase("wf-10702", guards, "execute")
    assert resolve_workflow_execution_target(phase) == ("wf-10702", guards, "execute")


def test_wl10703_session_state_update_is_bound_to_persistence_revision() -> None:
    # @trace WL-10703
    changes = {"step": "validate", "status": "ready"}
    phase = build_session_state_update_phase("session-10703", changes, 33)
    assert resolve_session_persistence_plan_target(phase) == (
        "session-10703",
        changes,
        33,
    )


def test_wl10704_retry_loop_and_terminal_outcome_are_resolved_together() -> None:
    # @trace WL-10704
    phase = build_retry_loop_phase(2, 3, "running")
    assert resolve_terminal_outcome_target(phase) == (2, 3, "running")


def test_wl10705_policy_matching_rejects_empty_ruleset() -> None:
    # @trace WL-10705
    phase = build_policy_match_phase("policy-10705", [], "deny")
    with pytest.raises(ValueError, match="invalid matched_rules"):
        resolve_policy_enforcement_plan_target(phase)


def test_wl10706_observability_rejects_missing_serialization_format() -> None:
    # @trace WL-10706
    phase = build_observability_event_phase("evt-10706", {"done": True}, "")
    with pytest.raises(ValueError, match="invalid serialization_format"):
        resolve_observability_serialization_target(phase)


def test_wl10707_workflow_execution_blocks_when_guard_failed() -> None:
    # @trace WL-10707
    guards = {"policy": True, "ready": False}
    phase = build_workflow_guard_phase("wf-10707", guards, "execute")
    with pytest.raises(ValueError, match="guard check failed"):
        resolve_workflow_execution_target(phase)


def test_wl10708_session_state_update_rejects_negative_persistence_revision() -> None:
    # @trace WL-10708
    phase = build_session_state_update_phase("session-10708", {"status": "running"}, -5)
    with pytest.raises(ValueError, match="invalid persistence_revision"):
        resolve_session_persistence_plan_target(phase)


def test_wl10709_retry_loop_rejects_attempts_beyond_maximum() -> None:
    # @trace WL-10709
    phase = build_retry_loop_phase(9, 3, "failed")
    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(phase)
