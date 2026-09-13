"""Lane A14 regressions for WL-10780..WL-10789 boundary contracts."""

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


def test_wl10780_orchestration_determinism_separates_plan_and_execution_boundaries() -> (
    None
):
    # @trace WL-10780
    phase = build_workflow_guard_phase(
        "workflow-10780", {"preflight": True, "quota": True}, "execute"
    )
    assert resolve_workflow_execution_target(phase) == (
        "workflow-10780",
        {"preflight": True, "quota": True},
        "execute",
    )

    with pytest.raises(ValueError, match="guard check failed"):
        resolve_workflow_execution_target(
            build_workflow_guard_phase(
                "workflow-10780", {"preflight": True, "quota": False}, "execute"
            )
        )


def test_wl10781_queue_throughput_separates_intake_and_worker_fanout_boundaries() -> (
    None
):
    # @trace WL-10781
    phase = build_queue_priority_phase("p1", ["turn-1", "turn-2"], 2)
    assert resolve_queue_execution_target(phase) == ("p1", ["turn-1", "turn-2"], 2)

    with pytest.raises(ValueError, match="invalid dispatch_window"):
        resolve_queue_execution_target(build_queue_priority_phase("p1", ["turn-1"], 0))


def test_wl10782_telemetry_separates_metric_collection_and_emitter_lifecycle() -> None:
    # @trace WL-10782
    phase = build_observability_event_phase("queue.depth", {"depth": 10}, "json")
    assert resolve_observability_serialization_target(phase) == (
        "queue.depth",
        {"depth": 10},
        "json",
    )

    invalid_phase = build_observability_event_phase(
        "queue.depth", {"depth": 10}, "json"
    )
    invalid_phase["event_payload"] = "bad"
    with pytest.raises(ValueError, match="invalid event_payload"):
        resolve_observability_serialization_target(invalid_phase)


def test_wl10783_provider_selection_separates_fallback_and_normal_paths() -> None:
    # @trace WL-10783
    phase = build_provider_selection_phase(
        ["primary", "fallback"], "primary", "highest-score"
    )
    assert resolve_workflow_guard_target(phase) == (
        ["primary", "fallback"],
        "primary",
        "highest-score",
    )

    with pytest.raises(ValueError, match="invalid selected_provider"):
        resolve_workflow_guard_target(
            build_provider_selection_phase(["primary"], "", "highest-score")
        )


def test_wl10784_policy_enforcement_separates_rule_discovery_and_action_execution() -> (
    None
):
    # @trace WL-10784
    phase = build_policy_match_phase(
        "policy-10784", ["allow:queue", "allow:sync"], "allow"
    )
    assert resolve_policy_enforcement_plan_target(phase) == (
        "policy-10784",
        ["allow:queue", "allow:sync"],
        "allow",
    )

    with pytest.raises(ValueError, match="invalid enforcement_action"):
        resolve_policy_enforcement_plan_target(
            build_policy_match_phase("policy-10784", ["allow:queue"], "")
        )


def test_wl10785_sync_reliability_separates_scan_records_and_mutation_apply_metadata() -> (
    None
):
    # @trace WL-10785
    phase = build_sync_diff_phase(
        [{"file": "src/thegent/integrations/gh_project_sync.py"}],
        "apply sync",
        "lane-a14",
    )
    assert resolve_sync_commit_plan_target(phase) == (
        [{"file": "src/thegent/integrations/gh_project_sync.py"}],
        "apply sync",
        "lane-a14",
    )

    invalid_phase = build_sync_diff_phase(
        [{"file": "src/thegent/integrations/gh_project_sync.py"}],
        "apply sync",
        "lane-a14",
    )
    invalid_phase["diff_records"] = ["bad"]
    with pytest.raises(ValueError, match="invalid diff record"):
        resolve_sync_commit_plan_target(invalid_phase)


def test_wl10786_runtime_error_behavior_separates_recoverable_and_terminal_branches() -> (
    None
):
    # @trace WL-10786
    phase = build_retry_loop_phase(2, 4, "recoverable")
    assert resolve_terminal_outcome_target(phase) == (2, 4, "recoverable")

    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(5, 4, "terminal"))


def test_wl10787_hook_delivery_separates_trigger_evaluation_and_callsite_payload() -> (
    None
):
    # @trace WL-10787
    phase = build_hook_registration_phase(
        "before_execute", {"scope": "lane-a14"}, {"turn_id": "turn-10787"}
    )
    assert resolve_hook_invocation_target(phase) == (
        "before_execute",
        {"scope": "lane-a14"},
        {"turn_id": "turn-10787"},
    )

    invalid_phase = build_hook_registration_phase(
        "before_execute", {"scope": "lane-a14"}, {"turn_id": "turn-10787"}
    )
    invalid_phase["registration_options"] = "bad"
    with pytest.raises(ValueError, match="invalid registration_options"):
        resolve_hook_invocation_target(invalid_phase)


def test_wl10788_session_lifecycle_separates_claim_transition_and_persistence_contract() -> (
    None
):
    # @trace WL-10788
    phase = build_session_state_update_phase("session-10788", {"status": "claimed"}, 9)
    assert resolve_session_persistence_plan_target(phase) == (
        "session-10788",
        {"status": "claimed"},
        9,
    )

    with pytest.raises(ValueError, match="invalid persistence_revision"):
        resolve_session_persistence_plan_target(
            build_session_state_update_phase("session-10788", {"status": "claimed"}, -1)
        )


def test_wl10789_cli_behavior_separates_schema_parse_and_handler_selection() -> None:
    # @trace WL-10789
    phase = build_cli_command_parse_phase(
        "run lane-a14", ["run", "lane-a14"], "run_handler"
    )
    assert resolve_cli_handler_selection_target(phase) == (
        "run lane-a14",
        ["run", "lane-a14"],
        "run_handler",
    )

    with pytest.raises(ValueError, match="invalid parsed token"):
        resolve_cli_handler_selection_target(
            build_cli_command_parse_phase("run lane-a14", ["run", ""], "run_handler")
        )
