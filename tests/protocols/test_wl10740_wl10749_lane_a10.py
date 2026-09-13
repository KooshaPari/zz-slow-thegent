"""Lane A10 regressions for WL-10740..WL-10749 around phase-boundary contracts."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_cli_command_parse_phase,
    build_hook_registration_phase,
    build_observability_event_phase,
    build_parse_phase,
    build_policy_match_phase,
    build_provider_rule_evaluation_phase,
    build_queue_scheduling_phase,
    build_retry_loop_phase,
    build_session_state_update_phase,
    build_sync_diff_phase,
    resolve_cli_handler_selection_target,
    resolve_hook_invocation_target,
    resolve_observability_serialization_target,
    resolve_parse_target,
    resolve_policy_enforcement_plan_target,
    resolve_provider_final_selection_target,
    resolve_session_persistence_plan_target,
    resolve_session_persistence_target,
    resolve_sync_commit_plan_target,
    resolve_terminal_outcome_target,
)


def test_wl10740_hook_delivery_keeps_trigger_payload_isolated() -> None:
    # @trace WL-10740
    phase = build_hook_registration_phase(
        "before_command",
        {"scope": "global"},
        {"source": "runner", "queue": "dispatch"},
    )
    assert resolve_hook_invocation_target(phase) == (
        "before_command",
        {"scope": "global"},
        {"source": "runner", "queue": "dispatch"},
    )

    with pytest.raises(ValueError, match="invalid invocation_payload"):
        resolve_hook_invocation_target(
            build_hook_registration_phase(
                "before_command",
                {"scope": "global"},
                "bad",
            )
        )


def test_wl10741_session_lifecycle_preserves_persistence_revision_contract() -> None:
    # @trace WL-10741
    phase = build_session_state_update_phase("session-10741", {"status": "claimed"}, 6)
    assert resolve_session_persistence_plan_target(phase) == (
        "session-10741",
        {"status": "claimed"},
        6,
    )

    with pytest.raises(ValueError, match="invalid persistence_revision"):
        resolve_session_persistence_plan_target(
            build_session_state_update_phase("session-10741", {"status": "claimed"}, -2)
        )


def test_wl10742_cli_command_parse_and_handler_split_remains_stable() -> None:
    # @trace WL-10742
    parse_phase = build_cli_command_parse_phase(
        "run queue sync", ["run", "queue", "sync"], "run_handler"
    )
    assert resolve_cli_handler_selection_target(parse_phase) == (
        "run queue sync",
        ["run", "queue", "sync"],
        "run_handler",
    )

    with pytest.raises(ValueError, match="invalid parsed token"):
        resolve_cli_handler_selection_target(
            build_cli_command_parse_phase("run queue sync", ["run", 99], "run_handler")
        )


def test_wl10743_orchestration_parse_target_preserves_execution_inputs() -> None:
    # @trace WL-10743
    parse_phase = build_parse_phase(
        "session-10743", "route plan", request_id="req-10743", request_has_id=True
    )
    assert resolve_parse_target(parse_phase) == (
        "session-10743",
        "route plan",
        "req-10743",
        True,
    )

    with pytest.raises(ValueError, match="invalid session_id"):
        resolve_parse_target(
            build_parse_phase("", "route plan", request_id=None, request_has_id=False)
        )


def test_wl10744_queue_scheduling_contract_keeps_intake_inputs_and_window() -> None:
    # @trace WL-10744
    phase = build_queue_scheduling_phase(["turn-1", "turn-2"], 77, 5)
    assert resolve_session_persistence_target(phase) == (["turn-1", "turn-2"], 77, 5)

    with pytest.raises(ValueError, match="invalid batch_size"):
        resolve_session_persistence_target(
            build_queue_scheduling_phase(["turn-1"], 77, 0)
        )


def test_wl10745_observability_phase_retains_event_payload_and_encoding() -> None:
    # @trace WL-10745
    event = build_observability_event_phase("queue.flush", {"count": 10}, "json")
    assert resolve_observability_serialization_target(event) == (
        "queue.flush",
        {"count": 10},
        "json",
    )

    with pytest.raises(ValueError, match="invalid serialization_format"):
        resolve_observability_serialization_target(
            build_observability_event_phase("queue.flush", {"count": 10}, "")
        )


def test_wl10746_provider_selection_path_accepts_scores_and_selected_provider() -> None:
    # @trace WL-10746
    phase = build_provider_rule_evaluation_phase(
        {"provider-a": 10, "provider-b": 8}, "fallback-first", "provider-a"
    )
    assert resolve_provider_final_selection_target(phase) == (
        {"provider-a": 10, "provider-b": 8},
        "fallback-first",
        "provider-a",
    )

    with pytest.raises(ValueError, match="selected provider missing score"):
        resolve_provider_final_selection_target(
            build_provider_rule_evaluation_phase(
                {"provider-a": 10}, "fallback-first", "provider-b"
            )
        )


def test_wl10747_policy_enforcement_plan_requires_rules_and_action() -> None:
    # @trace WL-10747
    phase = build_policy_match_phase(
        "policy-10747", ["allow:admin", "allow:user"], "block-none"
    )
    assert resolve_policy_enforcement_plan_target(phase) == (
        "policy-10747",
        ["allow:admin", "allow:user"],
        "block-none",
    )

    with pytest.raises(ValueError, match="invalid matched_rules"):
        resolve_policy_enforcement_plan_target(
            build_policy_match_phase("policy-10747", [], "block-none")
        )


def test_wl10748_sync_plan_keeps_scan_and_commit_metadata_separate() -> None:
    # @trace WL-10748
    phase = build_sync_diff_phase(
        [{"file": "src/thegent/protocols/turn_submit_boundaries.py"}],
        "refresh derived tests",
        "lane-a10",
    )
    assert resolve_sync_commit_plan_target(phase) == (
        [{"file": "src/thegent/protocols/turn_submit_boundaries.py"}],
        "refresh derived tests",
        "lane-a10",
    )

    with pytest.raises(ValueError, match="invalid commit_author"):
        resolve_sync_commit_plan_target(
            build_sync_diff_phase(
                [{"file": "src/thegent/protocols/turn_submit_boundaries.py"}],
                "refresh derived tests",
                "",
            )
        )


def test_wl10749_terminal_outcome_keeps_recoverable_and_terminal_modes() -> None:
    # @trace WL-10749
    phase = build_retry_loop_phase(2, 4, "recoverable")
    assert resolve_terminal_outcome_target(phase) == (2, 4, "recoverable")

    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(6, 4, "terminal"))
