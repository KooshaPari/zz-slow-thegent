# @trace WL-202 B90-W2-B1
"""Tests for anti-flap status hysteresis (WL-202).

Validates the hysteresis gate prevents rapid status oscillation
within and across sync cycles.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from thegent.integrations.status_hysteresis import (
    HysteresisConfig,
    HysteresisGate,
)


@pytest.mark.requirement("WL-202")
def test_hysteresis_config_defaults():
    """Test HysteresisConfig uses correct defaults."""
    config = HysteresisConfig()
    assert config.min_stable_cycles == 2
    assert config.cooldown_seconds == 300


@pytest.mark.requirement("WL-202")
def test_hysteresis_config_custom():
    """Test HysteresisConfig with custom values."""
    config = HysteresisConfig(min_stable_cycles=3, cooldown_seconds=600)
    assert config.min_stable_cycles == 3
    assert config.cooldown_seconds == 600


@pytest.mark.requirement("WL-202")
def test_no_history_allows_transition():
    """Test that items with no transition history allow transitions."""
    gate = HysteresisGate()

    # First transition should always be allowed
    assert gate.should_apply_transition("WL-100", "IN_PROGRESS") is True


@pytest.mark.requirement("WL-202")
def test_cooldown_blocks_same_status_transition():
    """Test that cooldown prevents rapid re-transition to same status."""
    config = HysteresisConfig(cooldown_seconds=300)
    gate = HysteresisGate(config)

    # Record a transition to IN_PROGRESS
    gate.record_transition("WL-200", "OPEN", "IN_PROGRESS")

    # Immediately trying the same transition should be blocked
    assert gate.should_apply_transition("WL-200", "IN_PROGRESS") is False


@pytest.mark.requirement("WL-202")
def test_cooldown_expires():
    """Test that cooldown expires after the configured period."""
    config = HysteresisConfig(cooldown_seconds=300)
    gate = HysteresisGate(config)

    # Record a transition
    gate.record_transition("WL-300", "OPEN", "IN_PROGRESS")

    # Should be blocked immediately
    assert gate.should_apply_transition("WL-300", "IN_PROGRESS") is False

    # Simulate time passing by manually manipulating the timestamp
    # (In real usage, the cooldown would naturally expire)
    # For testing, we'll create a new gate with fresh state to represent "after cooldown"
    gate2 = HysteresisGate(config)
    gate2._transition_history["WL-300"] = [gate._transition_history["WL-300"][0]]
    # Manually set old timestamp
    old_record = gate2._transition_history["WL-300"][0]
    old_record.timestamp = datetime.now(UTC) - timedelta(seconds=400)

    # After expiry, should be allowed
    assert gate2.should_apply_transition("WL-300", "IN_PROGRESS") is True


@pytest.mark.requirement("WL-202")
def test_different_target_allowed_after_transition():
    """Test that different target status is allowed after transition."""
    gate = HysteresisGate()

    gate.record_transition("WL-400", "OPEN", "IN_PROGRESS")

    # Different target should be allowed (even immediately)
    assert gate.should_apply_transition("WL-400", "REVIEW") is True


@pytest.mark.requirement("WL-202")
def test_flapping_detection_prevents_oscillation():
    """Test that flapping detection prevents rapid back-and-forth oscillation."""
    config = HysteresisConfig(min_stable_cycles=2, cooldown_seconds=60)
    gate = HysteresisGate(config)

    # Simulate flapping: OPEN -> IN_PROGRESS -> OPEN -> IN_PROGRESS
    gate.record_transition("WL-500", "OPEN", "IN_PROGRESS")
    gate.record_transition("WL-500", "IN_PROGRESS", "OPEN")
    gate.record_transition("WL-500", "OPEN", "IN_PROGRESS")

    # Now trying to go back to OPEN should be blocked (flapping)
    assert gate.should_apply_transition("WL-500", "OPEN") is False


@pytest.mark.requirement("WL-202")
def test_multiple_items_independent_state():
    """Test that different work items maintain independent hysteresis state."""
    gate = HysteresisGate()

    gate.record_transition("WL-600", "OPEN", "IN_PROGRESS")
    gate.record_transition("WL-601", "OPEN", "REVIEW")

    # WL-600 should block IN_PROGRESS (due to cooldown)
    assert gate.should_apply_transition("WL-600", "IN_PROGRESS") is False

    # WL-601 should allow IN_PROGRESS (no history of this)
    assert gate.should_apply_transition("WL-601", "IN_PROGRESS") is True

    # WL-601 should block REVIEW (due to cooldown)
    assert gate.should_apply_transition("WL-601", "REVIEW") is False


@pytest.mark.requirement("WL-202")
def test_record_transition_updates_history():
    """Test that record_transition properly updates internal history."""
    gate = HysteresisGate()

    gate.record_transition("WL-700", "OPEN", "IN_PROGRESS")

    # Verify the history was recorded
    assert "WL-700" in gate._transition_history
    assert len(gate._transition_history["WL-700"]) == 1
    record = gate._transition_history["WL-700"][0]
    assert record.from_status == "OPEN"
    assert record.to_status == "IN_PROGRESS"


@pytest.mark.requirement("WL-202")
def test_complex_state_machine_flow():
    """Test complex state transitions across multiple states."""
    gate = HysteresisGate()

    # Normal flow: OPEN -> IN_PROGRESS -> REVIEW -> DONE
    gate.record_transition("WL-800", "OPEN", "IN_PROGRESS")
    assert gate.should_apply_transition("WL-800", "REVIEW") is True

    gate.record_transition("WL-800", "IN_PROGRESS", "REVIEW")
    assert gate.should_apply_transition("WL-800", "DONE") is True

    gate.record_transition("WL-800", "REVIEW", "DONE")

    # Trying to go back to REVIEW should be blocked
    assert gate.should_apply_transition("WL-800", "REVIEW") is False
