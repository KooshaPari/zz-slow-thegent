"""Lane A3 regressions for WL-10670..WL-10679 boundary slicing helpers."""

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


def test_wl10670_provider_selection_separates_rule_evaluation_from_final_selection() -> None:
    # @trace WL-10670
    phase = build_provider_rule_evaluation_phase({"openai": 12, "anthropic": 9}, "weighted", "openai")
    assert resolve_provider_final_selection_target(phase) == (
        {"openai": 12, "anthropic": 9},
        "weighted",
        "openai",
    )


def test_wl10671_workflow_progression_separates_guard_checks_from_execution() -> None:
    # @trace WL-10671
    phase = build_workflow_guard_phase("wf-1", {"has-session": True, "has-policy": True}, "submit-turn")
    assert resolve_workflow_execution_target(phase) == (
        "wf-1",
        {"has-session": True, "has-policy": True},
        "submit-turn",
    )


def test_wl10672_hook_reliability_separates_registration_from_invocation() -> None:
    # @trace WL-10672
    registration_options = {"timeout_ms": 3000}
    invocation_payload = {"session_id": "s-1"}
    phase = build_hook_registration_phase("before_turn_submit", registration_options, invocation_payload)
    assert resolve_hook_invocation_target(phase) == (
        "before_turn_submit",
        registration_options,
        invocation_payload,
    )


def test_wl10673_policy_gating_separates_matching_from_enforcement() -> None:
    # @trace WL-10673
    phase = build_policy_match_phase("p-1", ["allow:team", "deny:none"], "allow")
    assert resolve_policy_enforcement_plan_target(phase) == (
        "p-1",
        ["allow:team", "deny:none"],
        "allow",
    )


def test_wl10674_queue_scheduling_separates_priority_from_execution() -> None:
    # @trace WL-10674
    phase = build_queue_priority_phase("high", ["t-1", "t-2"], 5)
    assert resolve_queue_execution_target(phase) == ("high", ["t-1", "t-2"], 5)


def test_wl10675_session_consistency_separates_state_updates_from_persistence() -> None:
    # @trace WL-10675
    changes = {"last_turn_id": "t-2", "status": "active"}
    phase = build_session_state_update_phase("s-1", changes, 4)
    assert resolve_session_persistence_plan_target(phase) == ("s-1", changes, 4)


def test_wl10676_sync_integrity_separates_diff_generation_from_commit() -> None:
    # @trace WL-10676
    records = [{"id": "d-1"}]
    phase = build_sync_diff_phase(records, "sync commit", "codex")
    assert resolve_sync_commit_plan_target(phase) == (records, "sync commit", "codex")


def test_wl10677_observability_separates_events_from_serialization() -> None:
    # @trace WL-10677
    payload = {"latency_ms": 42}
    phase = build_observability_event_phase("turn_submit_completed", payload, "json")
    assert resolve_observability_serialization_target(phase) == (
        "turn_submit_completed",
        payload,
        "json",
    )


def test_wl10678_cli_dispatch_separates_parse_from_handler_selection() -> None:
    # @trace WL-10678
    phase = build_cli_command_parse_phase("session resume --id s-1", ["session", "resume"], "resume_handler")
    assert resolve_cli_handler_selection_target(phase) == (
        "session resume --id s-1",
        ["session", "resume"],
        "resume_handler",
    )


def test_wl10679_error_semantics_separates_retry_loops_from_terminal_outcomes() -> None:
    # @trace WL-10679
    phase = build_retry_loop_phase(2, 5, "success")
    assert resolve_terminal_outcome_target(phase) == (2, 5, "success")
    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(6, 5, "failed"))
