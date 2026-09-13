"""Lane A4 regressions for WL-10680..WL-10689 boundary slicing helpers."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_observability_event_phase,
    build_policy_match_phase,
    build_retry_loop_phase,
    build_session_state_update_phase,
    build_workflow_guard_phase,
    resolve_observability_serialization_target,
    resolve_policy_enforcement_plan_target,
    resolve_session_persistence_plan_target,
    resolve_terminal_outcome_target,
    resolve_workflow_execution_target,
)


def test_wl10680_workflow_progression_separates_guard_checks_and_execution() -> None:
    # @trace WL-10680
    guard_results = {"session_exists": True, "policy_loaded": True}
    phase = build_workflow_guard_phase("wf-progress", guard_results, "dispatch")
    assert resolve_workflow_execution_target(phase) == (
        "wf-progress",
        guard_results,
        "dispatch",
    )


def test_wl10681_policy_gating_separates_matching_and_enforcement_paths() -> None:
    # @trace WL-10681
    rules = ["allow:default", "require:approval"]
    phase = build_policy_match_phase("policy-10681", rules, "allow")
    assert resolve_policy_enforcement_plan_target(phase) == (
        "policy-10681",
        rules,
        "allow",
    )


def test_wl10682_session_consistency_separates_state_updates_and_persistence() -> None:
    # @trace WL-10682
    state_changes = {"last_action": "dispatch", "status": "active"}
    phase = build_session_state_update_phase("session-10682", state_changes, 9)
    assert resolve_session_persistence_plan_target(phase) == (
        "session-10682",
        state_changes,
        9,
    )


def test_wl10683_observability_separates_events_from_serialization() -> None:
    # @trace WL-10683
    payload = {"event": "dispatch_started", "ts": 1708656000}
    phase = build_observability_event_phase("lane-a4-observe", payload, "json")
    assert resolve_observability_serialization_target(phase) == (
        "lane-a4-observe",
        payload,
        "json",
    )


def test_wl10684_error_semantics_separates_retry_loops_and_terminal_outcomes() -> None:
    # @trace WL-10684
    phase = build_retry_loop_phase(1, 3, "running")
    assert resolve_terminal_outcome_target(phase) == (1, 3, "running")


def test_wl10685_workflow_progression_fails_when_guard_blocks_execution() -> None:
    # @trace WL-10685
    phase = build_workflow_guard_phase("wf-blocked", {"session_exists": False}, "dispatch")
    with pytest.raises(ValueError, match="Workflow execution target unresolved"):
        resolve_workflow_execution_target(phase)


def test_wl10686_policy_gating_rejects_empty_ruleset() -> None:
    # @trace WL-10686
    phase = build_policy_match_phase("policy-10686", [], "allow")
    with pytest.raises(ValueError, match="Policy enforcement plan target unresolved"):
        resolve_policy_enforcement_plan_target(phase)


def test_wl10687_session_consistency_rejects_negative_persistence_revision() -> None:
    # @trace WL-10687
    phase = build_session_state_update_phase("session-10687", {"status": "clean"}, -1)
    with pytest.raises(ValueError, match="Session persistence plan target unresolved"):
        resolve_session_persistence_plan_target(phase)


def test_wl10688_observability_rejects_unknown_serialization_format() -> None:
    # @trace WL-10688
    phase = build_observability_event_phase("lane-a4-observe", {"status": "ok"}, "")
    with pytest.raises(ValueError, match="Observability serialization target unresolved"):
        resolve_observability_serialization_target(phase)


def test_wl10689_error_semantics_rejects_terminal_outcome_with_excess_attempts() -> None:
    # @trace WL-10689
    phase = build_retry_loop_phase(5, 3, "failed")
    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(phase)
