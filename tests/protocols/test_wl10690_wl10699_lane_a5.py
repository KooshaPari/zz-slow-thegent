"""Lane A5 regressions for WL-10690..WL-10699 boundary slicing helpers."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_cli_command_parse_phase,
    build_hook_registration_phase,
    build_observability_event_phase,
    build_policy_match_phase,
    build_provider_rule_evaluation_phase,
    build_queue_priority_phase,
    build_retry_loop_phase,
    build_session_state_update_phase,
    build_sync_diff_phase,
    build_workflow_guard_phase,
    resolve_cli_handler_selection_target,
    resolve_hook_invocation_target,
    resolve_observability_serialization_target,
    resolve_policy_enforcement_plan_target,
    resolve_provider_final_selection_target,
    resolve_queue_execution_target,
    resolve_session_persistence_plan_target,
    resolve_sync_commit_plan_target,
    resolve_terminal_outcome_target,
    resolve_workflow_execution_target,
)


def test_wl10690_hook_registration_and_invocation_are_separated() -> None:
    # @trace WL-10690
    registration_options = {"event": "on_submit", "async": True}
    phase = build_hook_registration_phase("hook-10690", registration_options, {"run_id": "r1"})
    assert resolve_hook_invocation_target(phase) == (
        "hook-10690",
        registration_options,
        {"run_id": "r1"},
    )


def test_wl10691_session_state_is_isolated_from_persistence_controls() -> None:
    # @trace WL-10691
    state_changes = {"status": "in_progress", "last_step": "dispatch"}
    phase = build_session_state_update_phase("session-10691", state_changes, 11)
    assert resolve_session_persistence_plan_target(phase) == (
        "session-10691",
        state_changes,
        11,
    )


def test_wl10692_cli_parse_and_handler_selection_are_separated() -> None:
    # @trace WL-10692
    phase = build_cli_command_parse_phase("dispatch now", ["dispatch", "now"], "dispatch_handler")
    assert resolve_cli_handler_selection_target(phase) == (
        "dispatch now",
        ["dispatch", "now"],
        "dispatch_handler",
    )


def test_wl10693_workflow_guard_and_execution_remain_partitioned() -> None:
    # @trace WL-10693
    guard_results = {"policy_loaded": True, "token_valid": True}
    phase = build_workflow_guard_phase("workflow-10693", guard_results, "run_step")
    assert resolve_workflow_execution_target(phase) == (
        "workflow-10693",
        guard_results,
        "run_step",
    )


def test_wl10694_queue_scheduling_priorities_are_partitioned_from_execution_window() -> None:
    # @trace WL-10694
    phase = build_queue_priority_phase("high", ["t-1", "t-2"], 9)
    assert resolve_queue_execution_target(phase) == ("high", ["t-1", "t-2"], 9)


def test_wl10695_observability_event_and_serialization_are_partitioned() -> None:
    # @trace WL-10695
    event_payload = {"name": "queued", "id": "e1"}
    phase = build_observability_event_phase("obs-10695", event_payload, "json")
    assert resolve_observability_serialization_target(phase) == (
        "obs-10695",
        event_payload,
        "json",
    )


def test_wl10696_provider_rule_evaluation_rejects_missing_provider_score() -> None:
    # @trace WL-10696
    phase = build_provider_rule_evaluation_phase({"p1": 10, "p2": 5}, "weighted", "p3")
    with pytest.raises(ValueError, match="selected provider missing score"):
        resolve_provider_final_selection_target(phase)


def test_wl10697_policy_match_rejects_empty_rules() -> None:
    # @trace WL-10697
    phase = build_policy_match_phase("policy-10697", [], "deny")
    with pytest.raises(ValueError, match="invalid matched_rules"):
        resolve_policy_enforcement_plan_target(phase)


def test_wl10698_sync_commit_rejects_invalid_author() -> None:
    # @trace WL-10698
    phase = build_sync_diff_phase(
        [{"file": "x.py", "op": "add"}],
        "",
        "alice",
    )
    with pytest.raises(ValueError, match="invalid commit_message"):
        resolve_sync_commit_plan_target(phase)


def test_wl10699_retry_loop_rejects_negative_attempt_count() -> None:
    # @trace WL-10699
    phase = build_retry_loop_phase(-1, 3, "failed")
    with pytest.raises(ValueError, match="invalid attempt_count"):
        resolve_terminal_outcome_target(phase)
