from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest

from thegent.integrations.conflict_ttl import (
    ConflictRecord,
    ConflictTTLManager,
)


@pytest.mark.requirement("WL-250")
class TestConflictRecord:
    """Test ConflictRecord dataclass."""

    def test_create_conflict_record_default(self) -> None:
        """Test creating a conflict record with default escalated=False."""
        now = datetime.now(UTC)
        record = ConflictRecord(conflict_id="conflict_123", created_at=now)
        assert record.conflict_id == "conflict_123"
        assert record.created_at == now
        assert record.escalated is False

    def test_create_conflict_record_with_escalated(self) -> None:
        """Test creating a conflict record with escalated=True."""
        now = datetime.now(UTC)
        record = ConflictRecord(
            conflict_id="conflict_456",
            created_at=now,
            escalated=True,
        )
        assert record.conflict_id == "conflict_456"
        assert record.escalated is True


@pytest.mark.requirement("WL-250")
class TestConflictTTLManager:
    """Test ConflictTTLManager."""

    def test_init_default_values(self) -> None:
        """Test initialization with default TTL values."""
        manager = ConflictTTLManager()
        assert manager.ttl_seconds == 86400.0  # 24 hours
        assert manager.escalation_seconds == 3600.0  # 1 hour

    def test_init_custom_values(self) -> None:
        """Test initialization with custom TTL values."""
        manager = ConflictTTLManager(ttl_seconds=7200.0, escalation_seconds=600.0)
        assert manager.ttl_seconds == 7200.0
        assert manager.escalation_seconds == 600.0

    def test_register_creates_record(self) -> None:
        """Test registering a new conflict."""
        manager = ConflictTTLManager()
        before = datetime.now(UTC)

        record = manager.register("conflict_1")

        after = datetime.now(UTC)
        assert record.conflict_id == "conflict_1"
        assert record.escalated is False
        assert before <= record.created_at <= after

    def test_register_multiple_conflicts(self) -> None:
        """Test registering multiple conflicts."""
        manager = ConflictTTLManager()
        record1 = manager.register("conflict_1")
        record2 = manager.register("conflict_2")

        assert record1.conflict_id == "conflict_1"
        assert record2.conflict_id == "conflict_2"
        assert record1 is not record2

    def test_is_expired_fresh_conflict(self) -> None:
        """Test is_expired on a fresh conflict."""
        manager = ConflictTTLManager(ttl_seconds=3600.0)
        manager.register("conflict_1")

        assert manager.is_expired("conflict_1") is False

    def test_is_expired_old_conflict(self) -> None:
        """Test is_expired on an old conflict."""
        manager = ConflictTTLManager(ttl_seconds=0.1)
        manager.register("conflict_1")

        # Wait for TTL to expire
        time.sleep(0.2)

        assert manager.is_expired("conflict_1") is True

    def test_is_expired_not_found_raises_keyerror(self) -> None:
        """Test is_expired raises KeyError if conflict not registered."""
        manager = ConflictTTLManager()

        with pytest.raises(KeyError):
            manager.is_expired("nonexistent")

    def test_needs_escalation_fresh_conflict(self) -> None:
        """Test needs_escalation on a fresh conflict."""
        manager = ConflictTTLManager(
            ttl_seconds=3600.0,
            escalation_seconds=1800.0,
        )
        manager.register("conflict_1")

        assert manager.needs_escalation("conflict_1") is False

    def test_needs_escalation_requires_escalation(self) -> None:
        """Test needs_escalation on a conflict past escalation threshold."""
        manager = ConflictTTLManager(
            ttl_seconds=3600.0,
            escalation_seconds=0.1,
        )
        manager.register("conflict_1")

        # Wait past escalation threshold
        time.sleep(0.2)

        assert manager.needs_escalation("conflict_1") is True

    def test_needs_escalation_after_already_escalated(self) -> None:
        """Test needs_escalation returns False if already escalated."""
        manager = ConflictTTLManager(
            ttl_seconds=3600.0,
            escalation_seconds=0.1,
        )
        manager.register("conflict_1")
        time.sleep(0.2)

        # Escalate it
        manager.escalate("conflict_1")

        # needs_escalation should return False now
        assert manager.needs_escalation("conflict_1") is False

    def test_needs_escalation_expired_conflict(self) -> None:
        """Test needs_escalation returns False if conflict is expired."""
        manager = ConflictTTLManager(
            ttl_seconds=0.2,
            escalation_seconds=0.1,
        )
        manager.register("conflict_1")
        time.sleep(0.3)

        # Conflict is now expired
        assert manager.needs_escalation("conflict_1") is False

    def test_needs_escalation_not_found_raises_keyerror(self) -> None:
        """Test needs_escalation raises KeyError if conflict not registered."""
        manager = ConflictTTLManager()

        with pytest.raises(KeyError):
            manager.needs_escalation("nonexistent")

    def test_escalate_marks_as_escalated(self) -> None:
        """Test escalate marks a conflict as escalated."""
        manager = ConflictTTLManager()
        manager.register("conflict_1")

        manager.escalate("conflict_1")

        # Get the record to check escalated flag
        assert manager._conflicts["conflict_1"].escalated is True

    def test_escalate_not_found_raises_keyerror(self) -> None:
        """Test escalate raises KeyError if conflict not registered."""
        manager = ConflictTTLManager()

        with pytest.raises(KeyError):
            manager.escalate("nonexistent")

    def test_expired_ids_empty(self) -> None:
        """Test expired_ids with no expired conflicts."""
        manager = ConflictTTLManager(ttl_seconds=3600.0)
        manager.register("conflict_1")
        manager.register("conflict_2")

        expired = manager.expired_ids()
        assert expired == []

    def test_expired_ids_some_expired(self) -> None:
        """Test expired_ids identifies expired conflicts."""
        manager = ConflictTTLManager(ttl_seconds=0.1)
        manager.register("conflict_1")
        time.sleep(0.2)
        manager.register("conflict_2")

        expired = manager.expired_ids()
        assert len(expired) == 1
        assert "conflict_1" in expired

    def test_expired_ids_all_expired(self) -> None:
        """Test expired_ids when all conflicts are expired."""
        manager = ConflictTTLManager(ttl_seconds=0.1)
        manager.register("conflict_1")
        manager.register("conflict_2")
        time.sleep(0.2)

        expired = manager.expired_ids()
        assert len(expired) == 2
        assert {"conflict_1", "conflict_2"} == set(expired)

    def test_workflow_register_check_escalate(self) -> None:
        """Test workflow: register, check escalation, escalate, verify."""
        manager = ConflictTTLManager(
            ttl_seconds=3600.0,
            escalation_seconds=0.1,
        )

        # Register
        record = manager.register("conflict_1")
        assert record.escalated is False

        # Fresh conflict doesn't need escalation
        assert manager.needs_escalation("conflict_1") is False

        # Wait for escalation threshold
        time.sleep(0.2)

        # Now it needs escalation
        assert manager.needs_escalation("conflict_1") is True

        # Escalate
        manager.escalate("conflict_1")

        # No longer needs escalation
        assert manager.needs_escalation("conflict_1") is False

        # Not yet expired
        assert manager.is_expired("conflict_1") is False

    def test_workflow_register_to_expiry(self) -> None:
        """Test workflow from registration through expiry."""
        manager = ConflictTTLManager(ttl_seconds=0.2, escalation_seconds=0.05)

        manager.register("conflict_1")
        assert manager.is_expired("conflict_1") is False

        time.sleep(0.1)
        assert manager.needs_escalation("conflict_1") is True
        manager.escalate("conflict_1")

        time.sleep(0.15)
        assert manager.is_expired("conflict_1") is True
        assert "conflict_1" in manager.expired_ids()
