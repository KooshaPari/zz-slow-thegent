"""Tests for thegent.integrations.decision_journal — Local decision journal for audit.

@trace WL-203
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.integrations.decision_journal import DecisionJournal, JournalEntry


class TestJournalEntry:
    """Test JournalEntry dataclass. @trace WL-203"""

    @pytest.mark.requirement("WL-203")
    def test_create_entry(self) -> None:
        """Can create a JournalEntry with all fields."""
        entry = JournalEntry(
            entry_id="entry_1",
            cycle_id="cycle_1",
            wl_id="WL-123",
            decision="status_changed",
            rationale="User requested change",
            before_state={"status": "pending"},
            after_state={"status": "completed"},
            timestamp="2026-02-22T12:00:00+00:00",
            replayable=True,
        )

        assert entry.entry_id == "entry_1"
        assert entry.cycle_id == "cycle_1"
        assert entry.wl_id == "WL-123"
        assert entry.decision == "status_changed"
        assert entry.rationale == "User requested change"
        assert entry.before_state == {"status": "pending"}
        assert entry.after_state == {"status": "completed"}
        assert entry.replayable is True

    @pytest.mark.requirement("WL-203")
    def test_create_entry_factory(self) -> None:
        """JournalEntry.create_entry factory generates ID and timestamp."""
        entry = JournalEntry.create_entry(
            cycle_id="cycle_1",
            wl_id="WL-456",
            decision="priority_updated",
            rationale="Auto-prioritized",
            before_state={"priority": "low"},
            after_state={"priority": "high"},
            replayable=True,
        )

        assert entry.entry_id  # Should be auto-generated
        assert len(entry.entry_id) == 8
        assert entry.timestamp  # Should be auto-generated
        assert "T" in entry.timestamp  # ISO format


class TestDecisionJournal:
    """Test DecisionJournal operations. @trace WL-203"""

    @pytest.fixture
    def journal(self, tmp_path: Path) -> DecisionJournal:
        """Provide a DecisionJournal with tmp journal file."""
        journal_file = tmp_path / "journal.jsonl"
        return DecisionJournal(journal_file=journal_file)

    @pytest.mark.requirement("WL-203")
    def test_append_and_read(self, journal: DecisionJournal) -> None:
        """Can append entries and read them back."""
        entry1 = JournalEntry(
            entry_id="e1",
            cycle_id="c1",
            wl_id="WL-1",
            decision="created",
            rationale="Initial",
            before_state={},
            after_state={"status": "new"},
            timestamp="2026-02-22T12:00:00+00:00",
            replayable=True,
        )

        journal.append(entry1)
        entries = journal.read_all()

        assert len(entries) == 1
        assert entries[0].entry_id == "e1"
        assert entries[0].decision == "created"

    @pytest.mark.requirement("WL-203")
    def test_append_multiple(self, journal: DecisionJournal) -> None:
        """Can append multiple entries in sequence."""
        entries_to_add = [
            JournalEntry.create_entry("c1", f"WL-{i}", "decision", "reason", {}, {})
            for i in range(3)
        ]

        for entry in entries_to_add:
            journal.append(entry)

        read_entries = journal.read_all()
        assert len(read_entries) == 3

    @pytest.mark.requirement("WL-203")
    def test_read_all_empty(self, journal: DecisionJournal) -> None:
        """read_all returns empty list for nonexistent journal."""
        entries = journal.read_all()
        assert entries == []

    @pytest.mark.requirement("WL-203")
    def test_read_replayable(self, journal: DecisionJournal) -> None:
        """read_replayable returns only entries with replayable=True."""
        entry_replayable = JournalEntry.create_entry(
            "c1", "WL-1", "change", "reason", {}, {}, replayable=True
        )
        entry_not_replayable = JournalEntry.create_entry(
            "c1", "WL-2", "manual", "manual edit", {}, {}, replayable=False
        )

        journal.append(entry_replayable)
        journal.append(entry_not_replayable)

        replayable = journal.read_replayable()
        assert len(replayable) == 1
        assert replayable[0].decision == "change"

    @pytest.mark.requirement("WL-203")
    def test_replay_entry(self, journal: DecisionJournal) -> None:
        """Can retrieve a specific entry by ID for replay."""
        entry = JournalEntry.create_entry("c1", "WL-1", "update", "reason", {}, {})
        journal.append(entry)

        retrieved = journal.replay_entry(entry.entry_id)
        assert retrieved.entry_id == entry.entry_id
        assert retrieved.decision == "update"

    @pytest.mark.requirement("WL-203")
    def test_replay_entry_not_found(self, journal: DecisionJournal) -> None:
        """replay_entry raises ValueError for missing entry."""
        with pytest.raises(ValueError, match="not found"):
            journal.replay_entry("nonexistent")

    @pytest.mark.requirement("WL-203")
    def test_journal_persistence_format(self, tmp_path: Path) -> None:
        """Journal entries are stored as JSONL (one JSON per line)."""
        journal_file = tmp_path / "journal.jsonl"
        journal = DecisionJournal(journal_file=journal_file)

        entry1 = JournalEntry.create_entry("c1", "WL-1", "dec1", "r1", {}, {})
        entry2 = JournalEntry.create_entry("c1", "WL-2", "dec2", "r2", {}, {})

        journal.append(entry1)
        journal.append(entry2)

        # Check file format
        lines = journal_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

        # Each line should be valid JSON
        import json

        for line in lines:
            data = json.loads(line)
            assert "entry_id" in data
            assert "decision" in data

    @pytest.mark.requirement("WL-203")
    def test_journal_handles_corrupt_lines(self, tmp_path: Path) -> None:
        """read_all skips corrupt JSON lines."""
        journal_file = tmp_path / "journal.jsonl"
        journal = DecisionJournal(journal_file=journal_file)

        # Manually write mixed valid and corrupt lines
        valid_entry = JournalEntry.create_entry("c1", "WL-1", "dec", "r", {}, {})
        import json

        journal_file.write_text(
            json.dumps(
                {
                    "entry_id": valid_entry.entry_id,
                    "cycle_id": "c1",
                    "wl_id": "WL-1",
                    "decision": "dec",
                    "rationale": "r",
                    "before_state": {},
                    "after_state": {},
                    "timestamp": valid_entry.timestamp,
                    "replayable": True,
                }
            ).decode()
            + "\n"
            + "{ invalid json }\n"
            + json.dumps(
                {
                    "entry_id": "e2",
                    "cycle_id": "c1",
                    "wl_id": "WL-2",
                    "decision": "dec2",
                    "rationale": "r2",
                    "before_state": {},
                    "after_state": {},
                    "timestamp": "2026-02-22T12:01:00+00:00",
                    "replayable": True,
                }
            ).decode()
            + "\n",
            encoding="utf-8",
        )

        # Should read valid entries, skip corrupt one
        entries = journal.read_all()
        assert len(entries) == 2
