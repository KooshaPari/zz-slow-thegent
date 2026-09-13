"""Lane A7 regressions for WL-10710..WL-10719 queue and retry boundary slicing."""

from __future__ import annotations

import pytest

from thegent.protocols.turn_submit_boundaries import (
    build_queue_priority_phase,
    build_retry_loop_phase,
    resolve_queue_execution_target,
    resolve_terminal_outcome_target,
)


def test_wl10710_queue_priority_is_separated_from_dispatch_window() -> None:
    # @trace WL-10710
    phase = build_queue_priority_phase("critical", ["turn-1", "turn-2"], 12)
    assert resolve_queue_execution_target(phase) == (
        "critical",
        ["turn-1", "turn-2"],
        12,
    )


def test_wl10711_retry_loop_rejects_over_max_attempts() -> None:
    # @trace WL-10711
    with pytest.raises(ValueError, match="attempt_count exceeds max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(8, 4, "failed"))


def test_wl10712_queue_priority_rejects_blank_bucket() -> None:
    # @trace WL-10712
    phase = build_queue_priority_phase("", ["turn-3"], 5)
    with pytest.raises(ValueError, match="invalid priority_bucket"):
        resolve_queue_execution_target(phase)


def test_wl10713_retry_loop_rejects_empty_terminal_outcome() -> None:
    # @trace WL-10713
    with pytest.raises(ValueError, match="invalid terminal_outcome"):
        resolve_terminal_outcome_target(build_retry_loop_phase(1, 3, ""))


def test_wl10714_queue_priority_rejects_invalid_turn_id() -> None:
    # @trace WL-10714
    phase = build_queue_priority_phase("normal", ["turn-4", 42], 5)
    with pytest.raises(ValueError, match="invalid queued turn_id"):
        resolve_queue_execution_target(phase)


def test_wl10715_retry_loop_returns_terminal_outcome_tuple() -> None:
    # @trace WL-10715
    phase = build_retry_loop_phase(0, 6, "running")
    assert resolve_terminal_outcome_target(phase) == (0, 6, "running")


def test_wl10716_queue_priority_rejects_empty_turn_ids() -> None:
    # @trace WL-10716
    phase = build_queue_priority_phase("normal", [], 4)
    with pytest.raises(ValueError, match="invalid queued_turn_ids"):
        resolve_queue_execution_target(phase)


def test_wl10717_retry_loop_rejects_non_positive_max_attempts() -> None:
    # @trace WL-10717
    with pytest.raises(ValueError, match="invalid max_attempts"):
        resolve_terminal_outcome_target(build_retry_loop_phase(1, 0, "retry"))


def test_wl10718_queue_priority_rejects_non_positive_dispatch_window() -> None:
    # @trace WL-10718
    phase = build_queue_priority_phase("low", ["turn-7"], 0)
    with pytest.raises(ValueError, match="invalid dispatch_window"):
        resolve_queue_execution_target(phase)


def test_wl10719_retry_loop_rejects_negative_attempt_count() -> None:
    # @trace WL-10719
    with pytest.raises(ValueError, match="invalid attempt_count"):
        resolve_terminal_outcome_target(build_retry_loop_phase(-2, 3, "error"))
