"""Unit tests for WP-3008: Escalation SLA and governance queue."""

from unittest.mock import MagicMock

import pytest

from thegent.config import ThegentSettings
from thegent.governance.escalation import (
    EscalationPriority,
    EscalationQueue,
    EscalationStatus,
)


@pytest.fixture
def mock_settings(tmp_path):
    settings = MagicMock(spec=ThegentSettings)
    settings.session_dir = tmp_path / "sessions"
    settings.session_dir.mkdir()
    return settings


def test_escalation_queue_add_and_list(mock_settings):
    """Test adding and listing items in the escalation queue."""
    queue = EscalationQueue(settings=mock_settings)

    esc_id = queue.escalate(
        run_id="run-123",
        prompt="Sensitive task",
        reason="Policy denied",
        agent="cursor",
        priority=EscalationPriority.HIGH,
    )

    assert esc_id.startswith("esc-")

    items = queue.list_items()
    assert len(items) == 1
    assert items[0].id == esc_id
    assert items[0].status == EscalationStatus.PENDING
    assert items[0].priority == EscalationPriority.HIGH


def test_escalation_queue_sorting(mock_settings):
    """Test that items are sorted by priority and deadline."""
    queue = EscalationQueue(settings=mock_settings)

    # Normal priority, long deadline
    queue.escalate("r1", "p1", "re1", "a1", priority=EscalationPriority.NORMAL, sla_minutes=100)
    # Urgent priority, short deadline
    queue.escalate("r2", "p2", "re2", "a1", priority=EscalationPriority.URGENT, sla_minutes=10)
    # High priority
    queue.escalate("r3", "p3", "re3", "a1", priority=EscalationPriority.HIGH, sla_minutes=50)

    items = queue.list_items()
    assert len(items) == 3
    assert items[0].priority == EscalationPriority.URGENT
    assert items[1].priority == EscalationPriority.HIGH
    assert items[2].priority == EscalationPriority.NORMAL


def test_escalation_queue_resolution(mock_settings):
    """Test resolving an escalation item."""
    queue = EscalationQueue(settings=mock_settings)
    esc_id = queue.escalate("run-456", "prompt", "reason", "agent")

    success = queue.resolve(esc_id, "Approved after review", "human-1")
    assert success is True

    item = queue.get_item(esc_id)
    assert item.status == EscalationStatus.RESOLVED
    assert item.resolution == "Approved after review"
    assert item.assigned_to == "human-1"


def test_escalation_queue_expiration(mock_settings):
    """Test that items expire after deadline."""
    queue = EscalationQueue(settings=mock_settings)

    # Create an item that is already expired
    esc_id = queue.escalate("run-789", "prompt", "reason", "agent", sla_minutes=-1)

    # listing should trigger expiration
    items = queue.list_items()
    assert len(items) == 1
    assert items[0].id == esc_id
    assert items[0].status == EscalationStatus.EXPIRED
