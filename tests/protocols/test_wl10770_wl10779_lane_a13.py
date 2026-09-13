"""Lane A13 regressions for WL-10770..WL-10779 boundary contracts."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_cli_command_parse_phase,
    build_hook_registration_phase,
    build_observability_event_phase,
    build_policy_match_phase,
    build_provider_selection_phase,
    build_queue_priority_phase,
    build_retry_loop_phase,
    build_session_state_update_phase,
    build_sync_diff_phase,
    build_workflow_guard_phase,
    resolve_cli_handler_selection_target,
    resolve_hook_invocation_target,
    resolve_observability_serialization_target,
    resolve_policy_enforcement_plan_target,
    resolve_queue_execution_target,
    resolve_session_persistence_plan_target,
    resolve_sync_commit_plan_target,
    resolve_terminal_outcome_target,
    resolve_workflow_execution_target,
    resolve_workflow_guard_target,
)


def test_wl10770_provider_selection_separates_fallback_and_normal_paths() -> None:
    # @trace WL-10770
    phase = build_provider_selection_phase(
        ["primary", "fallback"], "fallback", "quota-exceeded"
    )
    assert resolve_workflow_guard_target(phase) == (
        ["primary", "fallback"],
        "fallback",
        "quota-exceeded",
    )

    with pytest.raises(ValueError, match="invalid selected_provider"):
        resolve_workflow_guard_target(
            build_provider_selection_phase(["primary"], "", "quota-exceeded")
        )


def test_wl10771_policy_enforcement_separates_rule_discovery_and_action_execution() -> (
    None
):
    # @trace WL-10771
    phase = build_policy_match_phase(
        "policy-10771", ["allow:queue", "allow:sync"], "allow"
    )
    assert resolve_policy_enforcement_plan_target(phase) == (
        "policy-10771",
        ["allow:queue", "allow:sync"],
        "allow",
    )

    with pytest.raises(ValueError, match="invalid enforcement_action"):
        resolve_policy_enforcement_plan_target(
            build_policy_match_phase("policy-10771", ["allow:queue"], "")
        )


def test_wl10772_sync_reliability_separates_scan_records_and_mutation_apply_metadata() -> (
    None
):
    # @trace WL-10772
    phase = build_sync_diff_phase(
        [{"file": "src/thegent/integrations/gh_project_sync.py"}],
        "apply sync",
        "lane-a13",
    )
    assert resolve_sync_commit_plan_target(phase) == (
        [{"file": "src/thegent/integrations/gh_project_sync.py"}],
        "apply sync",
        "lane-a13",
    )

    invalid_phase = build_sync_diff_phase(
        [{"file": "src/thegent/integrations/gh_project_sync.py"}],
        "apply sync",
        "lane-a13",
    )
    invalid_phase["diff_records"] = ["bad"]
    with pytest.raises(ValueError, match="invalid diff record"):
        resolve_sync_commit_plan_target(invalid_phase)


def test_wl10773_runtime_error_behavior_separates_recoverable_and_terminal_branches() -> (
    None
):
    # @trace WL-10773
    phase = build_retry_loop_phase(2, 4, "recoverable")
    assert resolve_terminal_outcome_target(phase) == (2, 4, "recoverable")

    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(5, 4, "terminal"))


def test_wl10774_hook_delivery_separates_trigger_evaluation_and_callsite_payload() -> (
    None
):
    # @trace WL-10774
    phase = build_hook_registration_phase(
        "before_execute", {"scope": "lane-a13"}, {"turn_id": "turn-10774"}
    )
    assert resolve_hook_invocation_target(phase) == (
        "before_execute",
        {"scope": "lane-a13"},
        {"turn_id": "turn-10774"},
    )

    invalid_phase = build_hook_registration_phase(
        "before_execute", {"scope": "lane-a13"}, {"turn_id": "turn-10774"}
    )
    invalid_phase["registration_options"] = "bad"
    with pytest.raises(ValueError, match="invalid registration_options"):
        resolve_hook_invocation_target(invalid_phase)


def test_wl10775_session_lifecycle_separates_claim_transition_and_persistence_contract() -> (
    None
):
    # @trace WL-10775
    phase = build_session_state_update_phase("session-10775", {"status": "claimed"}, 8)
    assert resolve_session_persistence_plan_target(phase) == (
        "session-10775",
        {"status": "claimed"},
        8,
    )

    with pytest.raises(ValueError, match="invalid persistence_revision"):
        resolve_session_persistence_plan_target(
            build_session_state_update_phase("session-10775", {"status": "claimed"}, -1)
        )


def test_wl10776_cli_behavior_separates_schema_parse_and_handler_selection() -> None:
    # @trace WL-10776
    phase = build_cli_command_parse_phase(
        "run lane-a13", ["run", "lane-a13"], "run_handler"
    )
    assert resolve_cli_handler_selection_target(phase) == (
        "run lane-a13",
        ["run", "lane-a13"],
        "run_handler",
    )

    with pytest.raises(ValueError, match="invalid parsed token"):
        resolve_cli_handler_selection_target(
            build_cli_command_parse_phase("run lane-a13", ["run", ""], "run_handler")
        )


def test_wl10777_orchestration_determinism_separates_plan_and_execution_boundaries() -> (
    None
):
    # @trace WL-10777
    phase = build_workflow_guard_phase(
        "workflow-10777", {"preflight": True, "quota": True}, "execute"
    )
    assert resolve_workflow_execution_target(phase) == (
        "workflow-10777",
        {"preflight": True, "quota": True},
        "execute",
    )

    with pytest.raises(ValueError, match="guard check failed"):
        resolve_workflow_execution_target(
            build_workflow_guard_phase(
                "workflow-10777", {"preflight": True, "quota": False}, "execute"
            )
        )


def test_wl10778_queue_throughput_separates_intake_and_worker_fanout_boundaries() -> (
    None
):
    # @trace WL-10778
    phase = build_queue_priority_phase("p1", ["turn-1", "turn-2"], 2)
    assert resolve_queue_execution_target(phase) == ("p1", ["turn-1", "turn-2"], 2)

    with pytest.raises(ValueError, match="invalid dispatch_window"):
        resolve_queue_execution_target(build_queue_priority_phase("p1", ["turn-1"], 0))


def test_wl10779_telemetry_separates_metric_collection_and_emitter_lifecycle() -> None:
    # @trace WL-10779
    phase = build_observability_event_phase("queue.depth", {"depth": 9}, "json")
    assert resolve_observability_serialization_target(phase) == (
        "queue.depth",
        {"depth": 9},
        "json",
    )

    invalid_phase = build_observability_event_phase("queue.depth", {"depth": 9}, "json")
    invalid_phase["event_payload"] = "bad"
    with pytest.raises(ValueError, match="invalid event_payload"):
        resolve_observability_serialization_target(invalid_phase)
