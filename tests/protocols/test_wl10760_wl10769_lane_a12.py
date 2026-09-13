"""Lane A12 regressions for WL-10760..WL-10769 boundary contracts."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_cli_command_parse_phase,
    build_cli_dispatch_phase,
    build_hook_registration_phase,
    build_observability_event_phase,
    build_policy_match_phase,
    build_provider_rule_evaluation_phase,
    build_queue_priority_phase,
    build_queue_scheduling_phase,
    build_retry_loop_phase,
    build_session_state_update_phase,
    build_workflow_guard_phase,
    resolve_cli_handler_selection_target,
    resolve_hook_invocation_target,
    resolve_observability_serialization_target,
    resolve_policy_enforcement_plan_target,
    resolve_provider_final_selection_target,
    resolve_queue_execution_target,
    resolve_retry_outcome_target,
    resolve_session_persistence_plan_target,
    resolve_session_persistence_target,
    resolve_terminal_outcome_target,
    resolve_workflow_execution_target,
)


def test_wl10760_queue_throughput_separates_intake_order_from_worker_fanout() -> None:
    # @trace WL-10760
    phase = build_queue_scheduling_phase(["turn-1", "turn-2"], 3, 2)
    assert resolve_session_persistence_target(phase) == (["turn-1", "turn-2"], 3, 2)

    with pytest.raises(ValueError, match="invalid batch_size"):
        resolve_session_persistence_target(build_queue_scheduling_phase(["turn-1"], 3, 0))


def test_wl10761_telemetry_separates_metric_payload_from_emitter_serialization() -> None:
    # @trace WL-10761
    phase = build_observability_event_phase("queue.depth", {"depth": 7}, "json")
    assert resolve_observability_serialization_target(phase) == ("queue.depth", {"depth": 7}, "json")

    bad_phase = build_observability_event_phase("queue.depth", {"depth": 7}, "json")
    bad_phase["event_payload"] = "bad"
    with pytest.raises(ValueError, match="invalid event_payload"):
        resolve_observability_serialization_target(bad_phase)


def test_wl10762_provider_selection_separates_strategy_scores_from_chosen_provider() -> None:
    # @trace WL-10762
    phase = build_provider_rule_evaluation_phase({"primary": 9, "fallback": 4}, "highest-score", "primary")
    assert resolve_provider_final_selection_target(phase) == (
        {"primary": 9, "fallback": 4},
        "highest-score",
        "primary",
    )

    with pytest.raises(ValueError, match="selected provider missing score"):
        resolve_provider_final_selection_target(
            build_provider_rule_evaluation_phase({"primary": 9}, "highest-score", "fallback")
        )


def test_wl10763_policy_enforcement_separates_rule_matching_from_action_execution() -> None:
    # @trace WL-10763
    phase = build_policy_match_phase("policy-63", ["allow-queue", "scope-valid"], "allow")
    assert resolve_policy_enforcement_plan_target(phase) == (
        "policy-63",
        ["allow-queue", "scope-valid"],
        "allow",
    )

    with pytest.raises(ValueError, match="invalid matched_rules"):
        resolve_policy_enforcement_plan_target(build_policy_match_phase("policy-63", [], "allow"))


def test_wl10764_sync_reliability_separates_claim_updates_from_persistence_revision() -> None:
    # @trace WL-10764
    phase = build_session_state_update_phase("session-64", {"status": "running"}, 2)
    assert resolve_session_persistence_plan_target(phase) == ("session-64", {"status": "running"}, 2)

    with pytest.raises(ValueError, match="invalid persistence_revision"):
        resolve_session_persistence_plan_target(build_session_state_update_phase("session-64", {}, -1))


def test_wl10765_runtime_error_branching_keeps_retry_counters_and_terminal_states_explicit() -> None:
    # @trace WL-10765
    phase = build_retry_loop_phase(1, 3, "recoverable")
    assert resolve_terminal_outcome_target(phase) == (1, 3, "recoverable")

    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(4, 3, "terminal"))


def test_wl10766_hook_delivery_separates_registration_options_from_invocation_payload() -> None:
    # @trace WL-10766
    phase = build_hook_registration_phase("before_execute", {"scope": "session"}, {"turn_id": "t-66"})
    assert resolve_retry_outcome_target(
        build_cli_dispatch_phase("hooks run", {"hook": phase["hook_name"]}, "hook_handler")
    ) == ("hooks run", {"hook": "before_execute"}, "hook_handler")

    bad_phase = build_hook_registration_phase("before_execute", {"scope": "session"}, {"turn_id": "t-66"})
    bad_phase["registration_options"] = "bad"
    with pytest.raises(ValueError, match="invalid registration_options"):
        resolve_hook_invocation_target(bad_phase)


def test_wl10767_session_lifecycle_separates_queue_priority_from_dispatch_window() -> None:
    # @trace WL-10767
    phase = build_queue_priority_phase("p1", ["turn-67", "turn-68"], 3)
    assert resolve_queue_execution_target(phase) == ("p1", ["turn-67", "turn-68"], 3)

    with pytest.raises(ValueError, match="invalid queued_turn_ids"):
        resolve_queue_execution_target(build_queue_priority_phase("p1", [], 3))


def test_wl10768_cli_behavior_separates_schema_token_parse_from_handler_resolution() -> None:
    # @trace WL-10768
    phase = build_cli_command_parse_phase("queue push", ["queue", "push"], "queue_handler")
    assert resolve_cli_handler_selection_target(phase) == ("queue push", ["queue", "push"], "queue_handler")

    with pytest.raises(ValueError, match="invalid parsed token"):
        resolve_cli_handler_selection_target(
            build_cli_command_parse_phase("queue push", ["queue", ""], "queue_handler")
        )


def test_wl10769_orchestration_determinism_separates_plan_guards_from_execution_step() -> None:
    # @trace WL-10769
    phase = build_workflow_guard_phase("workflow-69", {"preflight": True, "quota": True}, "execute")
    assert resolve_workflow_execution_target(phase) == (
        "workflow-69",
        {"preflight": True, "quota": True},
        "execute",
    )

    with pytest.raises(ValueError, match="guard check failed"):
        resolve_workflow_execution_target(
            build_workflow_guard_phase("workflow-69", {"preflight": True, "quota": False}, "execute")
        )
