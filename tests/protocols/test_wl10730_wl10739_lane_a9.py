"""Lane A9 regressions for WL-10730..WL-10739 queue, observability, and dispatch boundaries."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_cli_command_parse_phase,
    build_commit_phase,
    build_hook_registration_phase,
    build_observability_event_phase,
    build_policy_match_phase,
    build_provider_selection_phase,
    build_queue_scheduling_phase,
    build_retry_loop_phase,
    build_session_state_update_phase,
    build_sync_diff_phase,
    resolve_cli_handler_selection_target,
    resolve_commit_target,
    resolve_hook_invocation_target,
    resolve_observability_serialization_target,
    resolve_policy_enforcement_plan_target,
    resolve_session_persistence_plan_target,
    resolve_session_persistence_target,
    resolve_sync_commit_plan_target,
    resolve_terminal_outcome_target,
    resolve_workflow_guard_target,
)


def test_wl10730_plan_execution_boundary_preserves_commit_inputs() -> None:
    # @trace WL-10730
    phase = build_commit_phase("session-10730", {"status": "queued"}, "turn-10730", {"goal": "parse"})
    assert resolve_commit_target(phase) == (
        "session-10730",
        {"status": "queued"},
        "turn-10730",
        {"goal": "parse"},
    )


def test_wl10731_intake_and_fanout_boundaries_are_parseable_before_persistence() -> None:
    # @trace WL-10731
    phase = build_queue_scheduling_phase(["turn-a", "turn-b"], 101, 8)
    assert resolve_session_persistence_target(phase) == (["turn-a", "turn-b"], 101, 8)

    with pytest.raises(ValueError, match="invalid batch_size"):
        resolve_session_persistence_target(build_queue_scheduling_phase(["turn-a"], 101, 0))


def test_wl10732_telemetry_boundary_separates_event_and_serialization() -> None:
    # @trace WL-10732
    phase = build_observability_event_phase("queue", {"depth": 3}, "json")
    assert resolve_observability_serialization_target(phase) == (
        "queue",
        {"depth": 3},
        "json",
    )

    with pytest.raises(ValueError, match="invalid serialization_format"):
        resolve_observability_serialization_target(
            build_observability_event_phase("queue", {"depth": 3}, ""),
        )


def test_wl10733_provider_selection_boundaries_are_detached_from_selection_reason() -> None:
    # @trace WL-10733
    phase = build_provider_selection_phase(["primary", "secondary"], "primary", "weight")
    assert resolve_workflow_guard_target(phase) == (
        ["primary", "secondary"],
        "primary",
        "weight",
    )


def test_wl10734_policy_enforcement_boundary_enforces_rule_discovery_contract() -> None:
    # @trace WL-10734
    phase = build_policy_match_phase("policy-10734", ["allow:admin", "allow:user"], "allow")
    assert resolve_policy_enforcement_plan_target(phase) == (
        "policy-10734",
        ["allow:admin", "allow:user"],
        "allow",
    )

    with pytest.raises(ValueError, match="invalid matched_rules"):
        resolve_policy_enforcement_plan_target(build_policy_match_phase("policy-10734", [], "allow"))


def test_wl10735_sync_boundaries_split_scan_and_apply() -> None:
    # @trace WL-10735
    diff = [{"file": "src/thegent/cli/main.py", "op": "update"}]
    phase = build_sync_diff_phase(diff, "refresh sync state", "automation")
    assert resolve_sync_commit_plan_target(phase) == (
        diff,
        "refresh sync state",
        "automation",
    )

    with pytest.raises(ValueError, match="invalid commit_author"):
        resolve_sync_commit_plan_target(build_sync_diff_phase(diff, "refresh sync state", ""))


def test_wl10736_runtime_error_boundary_preserves_recoverable_terminal_state() -> None:
    # @trace WL-10736
    phase = build_retry_loop_phase(1, 4, "retry")
    assert resolve_terminal_outcome_target(phase) == (1, 4, "retry")

    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(5, 4, "terminal"))


def test_wl10737_hook_delivery_boundary_keeps_trigger_and_payload_separate() -> None:
    # @trace WL-10737
    phase = build_hook_registration_phase(
        "before-hook",
        {"scope": "global"},
        {"session": "10737"},
    )
    assert resolve_hook_invocation_target(phase) == (
        "before-hook",
        {"scope": "global"},
        {"session": "10737"},
    )

    with pytest.raises(ValueError, match="invalid hook_name"):
        resolve_hook_invocation_target(build_hook_registration_phase("", {"scope": "global"}, {"session": "x"}))


def test_wl10738_session_lifecycle_boundary_uses_queued_state_and_revision_contract() -> None:
    # @trace WL-10738
    phase = build_session_state_update_phase("session-10738", {"status": "claimed"}, 44)
    assert resolve_session_persistence_plan_target(phase) == (
        "session-10738",
        {"status": "claimed"},
        44,
    )

    with pytest.raises(ValueError, match="invalid persistence_revision"):
        resolve_session_persistence_plan_target(
            build_session_state_update_phase("session-10738", {"status": "claimed"}, -1),
        )


def test_wl10739_cli_command_boundary_preserves_raw_parse_and_handler_targets() -> None:
    # @trace WL-10739
    phase = build_cli_command_parse_phase("run queue sync", ["run", "queue", "sync"], "run_handler")
    assert resolve_cli_handler_selection_target(phase) == (
        "run queue sync",
        ["run", "queue", "sync"],
        "run_handler",
    )

    with pytest.raises(ValueError, match="invalid parsed token"):
        resolve_cli_handler_selection_target(
            build_cli_command_parse_phase("run queue sync", ["run", 42], "run_handler")
        )
