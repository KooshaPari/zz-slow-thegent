"""Lane A11 regressions for WL-10750..WL-10759 boundary contracts."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_cli_command_parse_phase,
    build_cli_dispatch_phase,
    build_hook_invocation_phase,
    build_hook_registration_phase,
    build_observability_event_phase,
    build_provider_selection_phase,
    build_queue_priority_phase,
    build_retry_loop_phase,
    build_session_state_update_phase,
    build_sync_commit_phase,
    build_sync_diff_phase,
    build_workflow_guard_phase,
    resolve_cli_handler_selection_target,
    resolve_hook_invocation_target,
    resolve_observability_serialization_target,
    resolve_observability_target,
    resolve_policy_enforcement_target,
    resolve_queue_execution_target,
    resolve_retry_outcome_target,
    resolve_session_persistence_plan_target,
    resolve_sync_commit_plan_target,
    resolve_terminal_outcome_target,
    resolve_workflow_execution_target,
    resolve_workflow_guard_target,
)


def test_wl10750_policy_enforcement_keeps_discovery_inputs_separate_from_execution() -> None:
    # @trace WL-10750
    phase = build_hook_invocation_phase("policy.guard", "reg-10750", {"action": "allow"})
    assert resolve_policy_enforcement_target(phase) == (
        "policy.guard",
        "reg-10750",
        {"action": "allow"},
    )

    invalid_phase = build_hook_invocation_phase("policy.guard", "reg-10750", {"action": "allow"})
    invalid_phase["payload"] = "bad"
    with pytest.raises(ValueError, match="invalid payload"):
        resolve_policy_enforcement_target(invalid_phase)


def test_wl10751_sync_reliability_separates_scan_records_and_apply_mutation() -> None:
    # @trace WL-10751
    phase = build_sync_diff_phase(
        [{"file": "src/thegent/automation/workflow.py"}],
        "refresh sync state",
        "lane-a11",
    )
    assert resolve_sync_commit_plan_target(phase) == (
        [{"file": "src/thegent/automation/workflow.py"}],
        "refresh sync state",
        "lane-a11",
    )

    with pytest.raises(ValueError, match="invalid commit_message"):
        resolve_sync_commit_plan_target(build_sync_diff_phase([{"file": "x"}], "", "lane-a11"))


def test_wl10752_runtime_error_branching_keeps_recoverable_and_terminal_states_explicit() -> None:
    # @trace WL-10752
    phase = build_retry_loop_phase(2, 5, "recoverable")
    assert resolve_terminal_outcome_target(phase) == (2, 5, "recoverable")

    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(7, 5, "terminal"))


def test_wl10753_hook_delivery_keeps_trigger_registration_separate_from_callsite_payload() -> None:
    # @trace WL-10753
    phase = build_hook_registration_phase("before_execute", {"scope": "project"}, {"origin": "runner"})
    assert resolve_hook_invocation_target(phase) == (
        "before_execute",
        {"scope": "project"},
        {"origin": "runner"},
    )

    invalid_phase = build_hook_registration_phase(
        "before_execute",
        {"scope": "project"},
        {"origin": "runner"},
    )
    invalid_phase["invocation_payload"] = "bad"
    with pytest.raises(ValueError, match="invalid invocation_payload"):
        resolve_hook_invocation_target(invalid_phase)


def test_wl10754_session_lifecycle_claim_transition_and_persistence_remain_split() -> None:
    # @trace WL-10754
    phase = build_session_state_update_phase("session-10754", {"status": "claimed"}, 12)
    assert resolve_session_persistence_plan_target(phase) == (
        "session-10754",
        {"status": "claimed"},
        12,
    )

    with pytest.raises(ValueError, match="invalid persistence_revision"):
        resolve_session_persistence_plan_target(
            build_session_state_update_phase("session-10754", {"status": "claimed"}, -1)
        )


def test_wl10755_cli_behavior_keeps_schema_parse_and_dispatch_handling_separate() -> None:
    # @trace WL-10755
    parse_phase = build_cli_command_parse_phase("queue push", ["queue", "push"], "queue_handler")
    dispatch_phase = build_cli_dispatch_phase("queue push", {"priority": "high"}, "queue_handler")

    assert resolve_cli_handler_selection_target(parse_phase) == (
        "queue push",
        ["queue", "push"],
        "queue_handler",
    )
    assert resolve_retry_outcome_target(dispatch_phase) == (
        "queue push",
        {"priority": "high"},
        "queue_handler",
    )


def test_wl10756_orchestration_determinism_separates_plan_guards_from_execution() -> None:
    # @trace WL-10756
    phase = build_workflow_guard_phase("workflow-10756", {"preflight": True, "quota": True}, "execute")
    assert resolve_workflow_execution_target(phase) == (
        "workflow-10756",
        {"preflight": True, "quota": True},
        "execute",
    )

    with pytest.raises(ValueError, match="guard check failed"):
        resolve_workflow_execution_target(
            build_workflow_guard_phase("workflow-10756", {"preflight": True, "quota": False}, "execute")
        )


def test_wl10757_queue_throughput_keeps_intake_order_and_worker_window_contracts() -> None:
    # @trace WL-10757
    phase = build_queue_priority_phase("p1", ["turn-1", "turn-2"], 4)
    assert resolve_queue_execution_target(phase) == ("p1", ["turn-1", "turn-2"], 4)

    with pytest.raises(ValueError, match="invalid dispatch_window"):
        resolve_queue_execution_target(build_queue_priority_phase("p1", ["turn-1"], 0))


def test_wl10758_telemetry_separates_metric_collection_from_emitter_lifecycle() -> None:
    # @trace WL-10758
    event_phase = build_observability_event_phase("queue.depth", {"depth": 2}, "json")
    emit_phase = build_sync_commit_phase([{"file": "metrics.log"}], "commit-10758", False)
    assert resolve_observability_serialization_target(event_phase) == (
        "queue.depth",
        {"depth": 2},
        "json",
    )
    assert resolve_observability_target(emit_phase) == (
        [{"file": "metrics.log"}],
        "commit-10758",
        False,
    )


def test_wl10759_provider_selection_keeps_fallback_and_primary_paths_separate() -> None:
    # @trace WL-10759
    phase = build_provider_selection_phase(["primary", "fallback"], "fallback", "quota-exceeded")
    assert resolve_workflow_guard_target(phase) == (
        ["primary", "fallback"],
        "fallback",
        "quota-exceeded",
    )

    with pytest.raises(ValueError, match="invalid selected_provider"):
        resolve_workflow_guard_target(build_provider_selection_phase(["primary"], "", "quota-exceeded"))
