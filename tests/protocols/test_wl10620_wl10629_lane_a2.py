"""Lane A2 regressions for WL-10620..WL-10629 boundary slicing helpers."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_cli_dispatch_phase,
    build_hook_invocation_phase,
    build_provider_selection_phase,
    build_queue_scheduling_phase,
    build_sync_commit_phase,
    resolve_observability_target,
    resolve_policy_enforcement_target,
    resolve_retry_outcome_target,
    resolve_session_persistence_target,
    resolve_workflow_guard_target,
)


def test_wl10620_provider_selection_build_keeps_rule_evaluation_separate() -> None:
    # @trace WL-10620
    phase = build_provider_selection_phase(["openai", "anthropic"], "openai", "priority-rule")
    assert phase["candidate_providers"] == ["openai", "anthropic"]
    assert phase["selected_provider"] == "openai"
    assert phase["selection_reason"] == "priority-rule"


def test_wl10621_workflow_guard_resolver_preserves_progression_contract() -> None:
    # @trace WL-10621
    phase = build_provider_selection_phase(["openai"], "openai", "single-provider")
    assert resolve_workflow_guard_target(phase) == (
        ["openai"],
        "openai",
        "single-provider",
    )


def test_wl10622_hook_invocation_build_separates_registration_from_call_payload() -> None:
    # @trace WL-10622
    payload = {"session_id": "s-1"}
    phase = build_hook_invocation_phase("before_turn_submit", "reg-1", payload)
    assert phase["hook_name"] == "before_turn_submit"
    assert phase["registration_id"] == "reg-1"
    assert phase["payload"] is payload


def test_wl10623_policy_enforcement_resolver_fails_loudly_for_invalid_registration() -> None:
    # @trace WL-10623
    with pytest.raises(ValueError, match="Policy enforcement target unresolved"):
        resolve_policy_enforcement_target({"hook_name": "before_turn_submit", "registration_id": "", "payload": {}})


def test_wl10624_queue_scheduling_build_separates_priority_from_execution_batch() -> None:
    # @trace WL-10624
    phase = build_queue_scheduling_phase(["t-1", "t-2"], 12, 2)
    assert phase["prioritized_turn_ids"] == ["t-1", "t-2"]
    assert phase["scheduler_epoch"] == 12
    assert phase["batch_size"] == 2


def test_wl10625_session_persistence_resolver_preserves_state_update_contract() -> None:
    # @trace WL-10625
    phase = build_queue_scheduling_phase(["t-1"], 13, 1)
    assert resolve_session_persistence_target(phase) == (["t-1"], 13, 1)


def test_wl10626_sync_commit_build_separates_diff_generation_from_commit() -> None:
    # @trace WL-10626
    records = [{"id": "d-1"}]
    phase = build_sync_commit_phase(records, "commit-1", False)
    assert phase["diff_records"] is records
    assert phase["commit_id"] == "commit-1"
    assert phase["dry_run"] is False


def test_wl10627_observability_resolver_fails_loudly_on_invalid_commit_shape() -> None:
    # @trace WL-10627
    with pytest.raises(ValueError, match="Observability target unresolved"):
        resolve_observability_target({"diff_records": [], "commit_id": "", "dry_run": False})


def test_wl10628_cli_dispatch_build_separates_parse_from_handler_selection() -> None:
    # @trace WL-10628
    args = {"session_id": "s-1"}
    phase = build_cli_dispatch_phase("session.resume", args, "resume_handler")
    assert phase["parsed_command"] == "session.resume"
    assert phase["command_args"] is args
    assert phase["selected_handler"] == "resume_handler"


def test_wl10629_retry_outcome_resolver_fails_loudly_on_invalid_handler() -> None:
    # @trace WL-10629
    with pytest.raises(ValueError, match="Retry outcome target unresolved"):
        resolve_retry_outcome_target(
            {
                "parsed_command": "session.resume",
                "command_args": {},
                "selected_handler": "",
            }
        )
