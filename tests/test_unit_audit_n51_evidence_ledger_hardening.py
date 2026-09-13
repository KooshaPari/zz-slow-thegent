"""AUDIT-N+51: governance/evidence_ledger hardening spec (SOTA pass-33).

15 invariants FR-GOV-EL-001..015 covering EvidenceLedger init,
path-traversal guard, ledger_path derivation, _ensure_dir,
_ensure_version_marker, record, query, verify_chain, thread-safety,
and corrupt-line resilience.

@trace AUDIT-N+51  FR-GOV-EL-001..015
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Module-level import check
# ---------------------------------------------------------------------------


class TestModuleImport:
    """FR-GOV-EL-001: Module imports cleanly."""

    def test_import_evidence_ledger(self) -> None:
        from thegent.governance.evidence_ledger import EvidenceLedger

        assert EvidenceLedger is not None

    def test_import_evidence_event(self) -> None:
        from thegent.governance.evidence_ledger import EvidenceEvent

        assert EvidenceEvent is not None

    def test_import_event_type_constants(self) -> None:
        from thegent.governance.evidence_ledger import CYCLE_STARTED, TASK_COMPLETED

        assert CYCLE_STARTED == "cycle_started"
        assert TASK_COMPLETED == "task_completed"


# ---------------------------------------------------------------------------
# Trace annotation
# ---------------------------------------------------------------------------


class TestTraceAnnotation:
    """FR-GOV-EL-001: Module has @trace AUDIT-N+51 annotations."""

    def test_module_docstring_has_trace(self) -> None:
        import thegent.governance.evidence_ledger as mod

        doc = mod.__doc__ or ""
        assert "AUDIT-N+51" in doc or "@trace" in doc or "FR-GOV-EL-" in doc


# ---------------------------------------------------------------------------
# Path-traversal guards
# ---------------------------------------------------------------------------


class TestInitGuards:
    """FR-GOV-EL-001: Path-traversal guard rejects relative paths."""

    def test_rejects_relative_session_dir(self, tmp_path: Path) -> None:
        from thegent.governance.evidence_ledger import EvidenceLedger

        with pytest.raises(ValueError, match="absolute"):
            EvidenceLedger(session_dir=Path("relative/path"))

    def test_rejects_dot_relative(self, tmp_path: Path) -> None:
        from thegent.governance.evidence_ledger import EvidenceLedger

        with pytest.raises(ValueError, match="absolute"):
            EvidenceLedger(session_dir=Path("./relative"))

    def test_rejects_empty_relative(self, tmp_path: Path) -> None:
        from thegent.governance.evidence_ledger import EvidenceLedger

        with pytest.raises(ValueError, match="absolute"):
            EvidenceLedger(session_dir=Path("sessions/abc"))


class TestInitAcceptsAbsolute:
    """FR-GOV-EL-002: Path-traversal guard accepts absolute session_dir."""

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        assert ledger.session_dir == tmp_path


# ---------------------------------------------------------------------------
# ledger_path derivation
# ---------------------------------------------------------------------------


class TestLedgerPath:
    """FR-GOV-EL-003: ledger_path is derived correctly."""

    def test_ledger_path_structure(self, tmp_path: Path) -> None:
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        expected = tmp_path / "agileplus" / "evidence_ledger.jsonl"
        assert ledger.ledger_path == expected

    def test_ledger_path_is_under_session_dir(self, tmp_path: Path) -> None:
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        assert str(ledger.ledger_path).startswith(str(tmp_path))


# ---------------------------------------------------------------------------
# _ensure_dir
# ---------------------------------------------------------------------------


class TestEnsureDir:
    """FR-GOV-EL-004: _ensure_dir creates parent directories."""

    def test_creates_agileplus_subdirectory(self, tmp_path: Path) -> None:
        from thegent.governance.evidence_ledger import EvidenceLedger

        # Directory should not exist before construction
        assert not (tmp_path / "agileplus").exists()
        EvidenceLedger(session_dir=tmp_path)
        assert (tmp_path / "agileplus").is_dir()


# ---------------------------------------------------------------------------
# _ensure_version_marker
# ---------------------------------------------------------------------------


class TestVersionMarker:
    """FR-GOV-EL-005 / FR-GOV-EL-006: Version marker semantics."""

    def test_writes_schema_version_on_new_ledger(self, tmp_path: Path) -> None:
        """FR-GOV-EL-005: _ensure_version_marker writes schema version on new ledger."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        EvidenceLedger(session_dir=tmp_path)
        ledger_file = tmp_path / "agileplus" / "evidence_ledger.jsonl"
        assert ledger_file.exists()

        first_line = ledger_file.read_text().splitlines()[0]
        data = json.loads(first_line)
        assert data["event"] == "schema_version"
        assert data["version"] == 1
        assert "hash" in data

    def test_is_idempotent(self, tmp_path: Path) -> None:
        """FR-GOV-EL-006: _ensure_version_marker is idempotent."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        EvidenceLedger(session_dir=tmp_path)
        ledger_file = tmp_path / "agileplus" / "evidence_ledger.jsonl"
        line_count_after_first = len(ledger_file.read_text().splitlines())

        # Constructing a second ledger on same session_dir should NOT add another marker
        EvidenceLedger(session_dir=tmp_path)
        line_count_after_second = len(ledger_file.read_text().splitlines())
        assert line_count_after_second == line_count_after_first


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------


class TestRecord:
    """FR-GOV-EL-007 / FR-GOV-EL-008 / FR-GOV-EL-009: record() semantics."""

    def test_returns_hash_string(self, tmp_path: Path) -> None:
        """FR-GOV-EL-007: record() returns a hash string."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        h = ledger.record("scan_completed", cycle_id="c-1", payload={"file": "x.py"})
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest length

    def test_chains_prev_hash(self, tmp_path: Path) -> None:
        """FR-GOV-EL-008: record() chains prev_hash correctly."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)

        # First event: prev_hash should be the version marker hash
        h1 = ledger.record("cycle_started", cycle_id="c-1", payload={"start": True})
        # Second event: prev_hash should be h1
        h2 = ledger.record("task_completed", cycle_id="c-1", payload={"task": "t1"})

        # Read the second event's prev_hash from the file
        ledger_file = tmp_path / "agileplus" / "evidence_ledger.jsonl"
        lines = ledger_file.read_text().splitlines()
        # Line 0 = version marker, line 1 = first event, line 2 = second event
        second_event = json.loads(lines[2])
        assert second_event["prev_hash"] == h1
        assert second_event["hash"] == h2

    def test_empty_payload(self, tmp_path: Path) -> None:
        """FR-GOV-EL-009: record() handles empty payload."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        h = ledger.record("verification_completed", cycle_id="c-1")
        assert isinstance(h, str)
        assert len(h) == 64

    def test_record_with_kwargs(self, tmp_path: Path) -> None:
        """record() merges kwargs into payload when no payload dict is given."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.record("task_dispatched", cycle_id="c-1", task_id="t-42")
        events = ledger.query(cycle_id="c-1")
        assert len(events) == 1
        assert events[0].payload["task_id"] == "t-42"


# ---------------------------------------------------------------------------
# query()
# ---------------------------------------------------------------------------


class TestQuery:
    """FR-GOV-EL-010 / FR-GOV-EL-011: query() filtering."""

    def test_filters_by_cycle_id(self, tmp_path: Path) -> None:
        """FR-GOV-EL-010: query() filters by cycle_id."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.record("scan_completed", cycle_id="c-1", payload={"a": 1})
        ledger.record("scan_completed", cycle_id="c-2", payload={"b": 2})
        ledger.record("task_completed", cycle_id="c-1", payload={"c": 3})

        results = ledger.query(cycle_id="c-1")
        assert len(results) == 2
        assert all(e.cycle_id == "c-1" for e in results)

    def test_filters_by_event_type(self, tmp_path: Path) -> None:
        """FR-GOV-EL-011: query() filters by event_type."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.record("scan_completed", cycle_id="c-1", payload={"a": 1})
        ledger.record("task_completed", cycle_id="c-1", payload={"b": 2})
        ledger.record("task_completed", cycle_id="c-1", payload={"c": 3})

        results = ledger.query(event_type="scan_completed")
        assert len(results) == 1
        assert results[0].event_type == "scan_completed"

    def test_combined_filter(self, tmp_path: Path) -> None:
        """query() with both cycle_id and event_type narrows results."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.record("scan_completed", cycle_id="c-1", payload={"a": 1})
        ledger.record("task_completed", cycle_id="c-1", payload={"b": 2})
        ledger.record("scan_completed", cycle_id="c-2", payload={"c": 3})

        results = ledger.query(cycle_id="c-1", event_type="scan_completed")
        assert len(results) == 1
        assert results[0].cycle_id == "c-1"
        assert results[0].event_type == "scan_completed"

    def test_no_match_returns_empty(self, tmp_path: Path) -> None:
        """query() returns empty list when nothing matches."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.record("scan_completed", cycle_id="c-1", payload={})
        results = ledger.query(cycle_id="nonexistent")
        assert results == []


# ---------------------------------------------------------------------------
# verify_chain()
# ---------------------------------------------------------------------------


class TestVerifyChain:
    """FR-GOV-EL-012 / FR-GOV-EL-013: verify_chain() integrity."""

    def test_returns_true_for_intact_chain(self, tmp_path: Path) -> None:
        """FR-GOV-EL-012: verify_chain() returns True for intact chain."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.record("cycle_started", cycle_id="c-1", payload={})
        ledger.record("scan_completed", cycle_id="c-1", payload={})
        ledger.record("task_completed", cycle_id="c-1", payload={})

        assert ledger.verify_chain() is True

    def test_returns_false_for_corrupted_hash(self, tmp_path: Path) -> None:
        """FR-GOV-EL-013: verify_chain() returns False for corrupted ledger."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.record("cycle_started", cycle_id="c-1", payload={})
        ledger.record("task_completed", cycle_id="c-1", payload={})

        # Tamper with the hash of the second record
        ledger_file = tmp_path / "agileplus" / "evidence_ledger.jsonl"
        lines = ledger_file.read_text().splitlines()
        data = json.loads(
            lines[2]
        )  # second event line (0=marker, 1=first event, 2=second event)
        data["hash"] = "0" * 64  # corrupt hash
        lines[2] = json.dumps(data)
        ledger_file.write_text("\n".join(lines) + "\n")

        assert ledger.verify_chain() is False

    def test_returns_true_for_empty_ledger(self, tmp_path: Path) -> None:
        """verify_chain() returns True when no ledger file exists."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        # Remove the ledger file after construction
        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.ledger_path.unlink()
        assert ledger.verify_chain() is True


# ---------------------------------------------------------------------------
# Thread-safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """FR-GOV-EL-014: Thread-safety: concurrent record() calls don't crash."""

    def test_concurrent_records(self, tmp_path: Path) -> None:
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        errors: list[BaseException] = []

        def worker(idx: int) -> None:
            try:
                ledger.record(
                    "task_completed",
                    cycle_id=f"c-{idx % 3}",
                    payload={"worker": idx},
                )
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent records raised: {errors}"
        # All 20 events should be recorded (plus the version marker)
        events = ledger.query()
        assert len(events) == 20

    def test_lock_exists(self, tmp_path: Path) -> None:
        """Verify the RLock is present on the instance."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        assert hasattr(ledger, "_lock")
        assert isinstance(ledger._lock, type(threading.RLock()))


# ---------------------------------------------------------------------------
# Corrupt JSONL line resilience
# ---------------------------------------------------------------------------


class TestCorruptLineResilience:
    """FR-GOV-EL-015: Corrupt JSONL line is skipped gracefully."""

    def test_corrupt_line_skipped_in_get_last_hash(self, tmp_path: Path) -> None:
        """_get_last_hash() skips corrupt lines and returns last valid hash."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        h1 = ledger.record("cycle_started", cycle_id="c-1", payload={})

        # Append a corrupt line followed by a valid line
        ledger_file = tmp_path / "agileplus" / "evidence_ledger.jsonl"
        corrupt_line = "NOT-VALID-JSON {{{"
        valid_event = {
            "event_type": "task_completed",
            "cycle_id": "c-1",
            "payload": {"task": "t2"},
            "prev_hash": h1,
            "hash": "a" * 64,
        }
        with ledger_file.open("a", encoding="utf-8") as f:
            f.write(corrupt_line + "\n")
            f.write(json.dumps(valid_event) + "\n")

        # _get_last_hash should skip the corrupt line and find the last valid one
        last_hash = ledger._get_last_hash()
        assert last_hash == "a" * 64

    def test_corrupt_line_skipped_in_query(self, tmp_path: Path) -> None:
        """query() skips corrupt lines and returns valid events."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.record("cycle_started", cycle_id="c-1", payload={})

        # Inject a corrupt line
        ledger_file = tmp_path / "agileplus" / "evidence_ledger.jsonl"
        with ledger_file.open("a", encoding="utf-8") as f:
            f.write("{broken json\n")

        # query should not crash
        results = ledger.query(cycle_id="c-1")
        assert len(results) == 1

    def test_corrupt_line_skipped_in_verify_chain(self, tmp_path: Path) -> None:
        """verify_chain() skips corrupt lines gracefully."""
        from thegent.governance.evidence_ledger import EvidenceLedger

        ledger = EvidenceLedger(session_dir=tmp_path)
        ledger.record("cycle_started", cycle_id="c-1", payload={})

        # Inject a corrupt line between records
        ledger_file = tmp_path / "agileplus" / "evidence_ledger.jsonl"
        with ledger_file.open("a", encoding="utf-8") as f:
            f.write("TRASH LINE\n")

        # verify_chain should not raise, just skip the corrupt line
        # Since the chain is still valid for non-corrupt records, it should be True
        # (the corrupt line is skipped, not treated as a chain break)
        assert ledger.verify_chain() is True
