"""Lane A8 regressions for WL-10720..WL-10729 queue and execution boundary slicing."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_cli_command_parse_phase,
    build_hook_registration_phase,
    build_observability_event_phase,
    build_policy_match_phase,
    build_provider_selection_phase,
    build_queue_priority_phase,
    build_queue_scheduling_phase,
    build_retry_loop_phase,
    build_session_state_update_phase,
    build_sync_diff_phase,
    resolve_cli_handler_selection_target,
    resolve_hook_invocation_target,
    resolve_observability_serialization_target,
    resolve_policy_enforcement_plan_target,
    resolve_queue_execution_target,
    resolve_session_persistence_plan_target,
    resolve_session_persistence_target,
    resolve_sync_commit_plan_target,
    resolve_terminal_outcome_target,
    resolve_workflow_guard_target,
)


def test_wl10720_provider_selection_separates_fallback_and_normal_paths() -> None:
    # @trace WL-10720
    phase = build_provider_selection_phase(
        ["fallback", "primary"], "primary", "weighted"
    )
    assert resolve_workflow_guard_target(phase) == (
        ["fallback", "primary"],
        "primary",
        "weighted",
    )


def test_wl10721_policy_enforcement_separates_rule_discovery_and_action() -> None:
    # @trace WL-10721
    phase = build_policy_match_phase(
        "policy-10721", ["allow:team", "deny:none"], "allow"
    )
    assert resolve_policy_enforcement_plan_target(phase) == (
        "policy-10721",
        ["allow:team", "deny:none"],
        "allow",
    )


def test_wl10722_sync_reliability_separates_scan_and_apply() -> None:
    # @trace WL-10722
    phase = build_sync_diff_phase(
        [{"file": "src/thegent/integrations/gh_project_sync.py", "op": "update"}],
        "refresh sync state",
        "agent",
    )
    assert resolve_sync_commit_plan_target(phase) == (
        [{"file": "src/thegent/integrations/gh_project_sync.py", "op": "update"}],
        "refresh sync state",
        "agent",
    )


def test_wl10723_runtime_error_behavior_preserves_recoverable_and_terminal_branches() -> (
    None
):
    # @trace WL-10723
    phase = build_retry_loop_phase(2, 3, "retry")
    assert resolve_terminal_outcome_target(phase) == (2, 3, "retry")
    with pytest.raises(ValueError, match="invalid max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(1, 0, "retry"))


def test_wl10724_hook_delivery_separates_trigger_evaluation_and_call_site() -> None:
    # @trace WL-10724
    phase = build_hook_registration_phase(
        "wl10724-hook",
        {"event": "before_turn_submit", "async": False},
        {"trace_id": "wl10724"},
    )
    assert resolve_hook_invocation_target(phase) == (
        "wl10724-hook",
        {"event": "before_turn_submit", "async": False},
        {"trace_id": "wl10724"},
    )


def test_wl10725_session_lifecycle_separates_claim_and_persistence() -> None:
    # @trace WL-10725
    phase = build_session_state_update_phase("session-10725", {"status": "claimed"}, 17)
    assert resolve_session_persistence_plan_target(phase) == (
        "session-10725",
        {"status": "claimed"},
        17,
    )


def test_wl10726_cli_dispatch_separates_parse_and_handler_execution() -> None:
    # @trace WL-10726
    cli_phase = build_cli_command_parse_phase(
        "run lane-a8 task",
        ["run", "lane-a8", "task"],
        "lane_a8_handler",
    )
    assert resolve_cli_handler_selection_target(cli_phase) == (
        "run lane-a8 task",
        ["run", "lane-a8", "task"],
        "lane_a8_handler",
    )


def test_wl10727_orchestration_plan_and_execution_boundaries_remain_distinct() -> None:
    # @trace WL-10727
    phase = build_queue_priority_phase("high", ["turn-10727-a", "turn-10727-b"], 7)
    assert resolve_queue_execution_target(phase) == (
        "high",
        ["turn-10727-a", "turn-10727-b"],
        7,
    )


def test_wl10728_queue_throughput_separates_intake_and_worker_fanout() -> None:
    # @trace WL-10728
    phase = build_queue_scheduling_phase(["turn-10728-a", "turn-10728-b"], 41, 4)
    assert resolve_session_persistence_target(phase) == (
        ["turn-10728-a", "turn-10728-b"],
        41,
        4,
    )
    with pytest.raises(ValueError, match="invalid prioritized_turn_ids"):
        resolve_session_persistence_target(build_queue_scheduling_phase([], 41, 4))


def test_wl10729_telemetry_separates_metric_collection_and_emitter_lifecycle() -> None:
    # @trace WL-10729
    phase = build_observability_event_phase(
        "telemetry-10729", {"metric": "queue.depth", "value": 9}, "json"
    )
    assert resolve_observability_serialization_target(phase) == (
        "telemetry-10729",
        {"metric": "queue.depth", "value": 9},
        "json",
    )
    with pytest.raises(ValueError, match="invalid serialization_format"):
        resolve_observability_serialization_target(
            build_observability_event_phase(
                "telemetry-10729", {"metric": "queue.depth"}, ""
            ),
        )
