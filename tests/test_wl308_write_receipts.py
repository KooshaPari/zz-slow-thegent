"""Tests for WL-308 Remote Write Receipts.

# @trace WL-308
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import orjson as json
import pytest

from thegent.integrations.write_receipts import WriteReceipt, WriteReceiptLog


class TestWriteReceiptDataclass:
    """Tests for WriteReceipt dataclass."""

    def test_receipt_creation(self) -> None:
        """Create a WriteReceipt."""
        ts = datetime.now(UTC)
        receipt = WriteReceipt(
            wl_id="WL-001",
            connector="github",
            operation="create",
            remote_id="gh-123",
            success=True,
            timestamp=ts,
            cycle_id="cycle-1",
        )

        assert receipt.wl_id == "WL-001"
        assert receipt.connector == "github"
        assert receipt.operation == "create"
        assert receipt.remote_id == "gh-123"
        assert receipt.success is True
        assert receipt.timestamp == ts
        assert receipt.cycle_id == "cycle-1"

    def test_receipt_with_none_remote_id(self) -> None:
        """Receipt can have None remote_id for failed operations."""
        ts = datetime.now(UTC)
        receipt = WriteReceipt(
            wl_id="WL-002",
            connector="github",
            operation="update",
            remote_id=None,
            success=False,
            timestamp=ts,
            cycle_id="cycle-1",
        )

        assert receipt.remote_id is None
        assert receipt.success is False

    def test_receipt_to_dict(self) -> None:
        """to_dict converts receipt to dict with ISO timestamp."""
        ts = datetime(2026, 2, 22, 12, 0, 0, tzinfo=UTC)
        receipt = WriteReceipt(
            wl_id="WL-001",
            connector="github",
            operation="create",
            remote_id="gh-123",
            success=True,
            timestamp=ts,
            cycle_id="cycle-1",
        )

        data = receipt.to_dict()
        assert isinstance(data, dict)
        assert data["wl_id"] == "WL-001"
        assert data["connector"] == "github"
        assert data["timestamp"] == "2026-02-22T12:00:00+00:00"
        assert isinstance(data["timestamp"], str)

    @pytest.mark.requirement("WL-308")
    def test_receipt_all_fields_in_dict(self) -> None:
        """to_dict includes all receipt fields."""
        ts = datetime.now(UTC)
        receipt = WriteReceipt(
            wl_id="WL-001",
            connector="github",
            operation="create",
            remote_id="gh-123",
            success=True,
            timestamp=ts,
            cycle_id="cycle-1",
        )

        data = receipt.to_dict()
        required_keys = {"wl_id", "connector", "operation", "remote_id", "success", "timestamp", "cycle_id"}
        assert required_keys.issubset(data.keys())


class TestWriteReceiptLogInit:
    """Tests for WriteReceiptLog initialization."""

    def test_init_creates_parent_dir(self, tmp_path: Path) -> None:
        """Init creates parent directories."""
        log_path = tmp_path / "subdir" / "receipts.jsonl"
        log = WriteReceiptLog(log_path)

        assert log.log_path == log_path
        assert log.log_path.parent.exists()

    def test_init_with_string_path(self, tmp_path: Path) -> None:
        """Init accepts string path."""
        log_path = str(tmp_path / "receipts.jsonl")
        log = WriteReceiptLog(log_path)
        assert isinstance(log.log_path, Path)

    def test_init_existing_directory(self, tmp_path: Path) -> None:
        """Init with existing directory."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        assert log.log_path.parent.exists()

    @pytest.mark.requirement("WL-308")
    def test_init_log_path_set(self, tmp_path: Path) -> None:
        """Init sets log_path correctly."""
        log_path = tmp_path / "receipts.jsonl"
        log = WriteReceiptLog(log_path)
        assert log.log_path == log_path


class TestWriteReceiptLogAppend:
    """Tests for append method."""

    def test_append_single_receipt(self, tmp_path: Path) -> None:
        """Append a single receipt."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)
        receipt = WriteReceipt(
            wl_id="WL-001",
            connector="github",
            operation="create",
            remote_id="gh-123",
            success=True,
            timestamp=ts,
            cycle_id="cycle-1",
        )

        log.append(receipt)

        assert log.log_path.exists()

    def test_append_multiple_receipts(self, tmp_path: Path) -> None:
        """Append multiple receipts."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        for i in range(3):
            receipt = WriteReceipt(
                wl_id=f"WL-{i:03d}",
                connector="github",
                operation="create",
                remote_id=f"gh-{i}",
                success=True,
                timestamp=ts,
                cycle_id="cycle-1",
            )
            log.append(receipt)

        lines = log.log_path.read_text().strip().split("\n")
        assert len(lines) == 3

    def test_append_creates_jsonl(self, tmp_path: Path) -> None:
        """Append creates JSONL format (one JSON object per line)."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)
        receipt = WriteReceipt(
            wl_id="WL-001",
            connector="github",
            operation="create",
            remote_id="gh-123",
            success=True,
            timestamp=ts,
            cycle_id="cycle-1",
        )

        log.append(receipt)

        content = log.log_path.read_text().strip()
        data = json.loads(content)
        assert data["wl_id"] == "WL-001"

    def test_append_invalid_receipt_raises(self, tmp_path: Path) -> None:
        """Appending non-WriteReceipt raises ValueError."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        with pytest.raises(ValueError, match="WriteReceipt"):
            log.append({"not": "receipt"})

    @pytest.mark.requirement("WL-308")
    def test_append_preserves_timestamp(self, tmp_path: Path) -> None:
        """Append preserves timestamp as ISO string."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime(2026, 2, 22, 14, 30, 45, tzinfo=UTC)
        receipt = WriteReceipt(
            wl_id="WL-001",
            connector="github",
            operation="create",
            remote_id="gh-123",
            success=True,
            timestamp=ts,
            cycle_id="cycle-1",
        )

        log.append(receipt)

        content = log.log_path.read_text().strip()
        data = json.loads(content)
        assert "2026-02-22" in data["timestamp"]


class TestWriteReceiptLogReadAll:
    """Tests for read_all method."""

    def test_read_all_empty_log(self, tmp_path: Path) -> None:
        """read_all on non-existent log returns empty list."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        assert log.read_all() == []

    def test_read_all_single_receipt(self, tmp_path: Path) -> None:
        """read_all returns single receipt."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)
        receipt = WriteReceipt(
            wl_id="WL-001",
            connector="github",
            operation="create",
            remote_id="gh-123",
            success=True,
            timestamp=ts,
            cycle_id="cycle-1",
        )
        log.append(receipt)

        receipts = log.read_all()
        assert len(receipts) == 1
        assert receipts[0].wl_id == "WL-001"

    def test_read_all_multiple_receipts(self, tmp_path: Path) -> None:
        """read_all returns all receipts."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        for i in range(5):
            receipt = WriteReceipt(
                wl_id=f"WL-{i:03d}",
                connector="github",
                operation="create",
                remote_id=f"gh-{i}",
                success=True,
                timestamp=ts,
                cycle_id="cycle-1",
            )
            log.append(receipt)

        receipts = log.read_all()
        assert len(receipts) == 5
        assert all(isinstance(r, WriteReceipt) for r in receipts)

    def test_read_all_preserves_data(self, tmp_path: Path) -> None:
        """read_all preserves all receipt data."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime(2026, 2, 22, 12, 0, 0, tzinfo=UTC)
        original = WriteReceipt(
            wl_id="WL-001",
            connector="github",
            operation="update",
            remote_id="gh-456",
            success=False,
            timestamp=ts,
            cycle_id="cycle-2",
        )
        log.append(original)

        receipts = log.read_all()
        read_receipt = receipts[0]

        assert read_receipt.wl_id == "WL-001"
        assert read_receipt.connector == "github"
        assert read_receipt.operation == "update"
        assert read_receipt.remote_id == "gh-456"
        assert read_receipt.success is False
        assert read_receipt.cycle_id == "cycle-2"

    def test_read_all_malformed_log_raises(self, tmp_path: Path) -> None:
        """Malformed JSONL raises ValueError."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        log.log_path.write_text("invalid json\n")
        with pytest.raises(ValueError, match="Malformed"):
            log.read_all()

    @pytest.mark.requirement("WL-308")
    def test_read_all_returns_writereceipt_objects(self, tmp_path: Path) -> None:
        """read_all returns WriteReceipt instances."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)
        receipt = WriteReceipt(
            wl_id="WL-001",
            connector="github",
            operation="create",
            remote_id="gh-123",
            success=True,
            timestamp=ts,
            cycle_id="cycle-1",
        )
        log.append(receipt)

        receipts = log.read_all()
        assert len(receipts) == 1
        assert isinstance(receipts[0], WriteReceipt)


class TestWriteReceiptLogReadByCycle:
    """Tests for read_by_cycle method."""

    def test_read_by_cycle_single_match(self, tmp_path: Path) -> None:
        """read_by_cycle returns receipts for matching cycle."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        r1 = WriteReceipt("WL-001", "github", "create", "gh-1", True, ts, "cycle-1")
        r2 = WriteReceipt("WL-002", "github", "create", "gh-2", True, ts, "cycle-2")

        log.append(r1)
        log.append(r2)

        receipts = log.read_by_cycle("cycle-1")
        assert len(receipts) == 1
        assert receipts[0].wl_id == "WL-001"

    def test_read_by_cycle_multiple_matches(self, tmp_path: Path) -> None:
        """read_by_cycle returns all matching receipts."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        for i in range(3):
            r = WriteReceipt(f"WL-{i:03d}", "github", "create", f"gh-{i}", True, ts, "cycle-1")
            log.append(r)

        receipts = log.read_by_cycle("cycle-1")
        assert len(receipts) == 3

    def test_read_by_cycle_no_matches(self, tmp_path: Path) -> None:
        """read_by_cycle returns empty list when no matches."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        r = WriteReceipt("WL-001", "github", "create", "gh-1", True, ts, "cycle-1")
        log.append(r)

        receipts = log.read_by_cycle("cycle-2")
        assert receipts == []

    def test_read_by_cycle_empty_log(self, tmp_path: Path) -> None:
        """read_by_cycle on empty log returns empty list."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        receipts = log.read_by_cycle("cycle-1")
        assert receipts == []

    def test_read_by_cycle_empty_string_raises(self, tmp_path: Path) -> None:
        """Empty cycle_id raises ValueError."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        with pytest.raises(ValueError, match="non-empty string"):
            log.read_by_cycle("")

    def test_read_by_cycle_non_string_raises(self, tmp_path: Path) -> None:
        """Non-string cycle_id raises ValueError."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        with pytest.raises(ValueError, match="non-empty string"):
            log.read_by_cycle(123)

    @pytest.mark.requirement("WL-308")
    def test_read_by_cycle_filtering_accuracy(self, tmp_path: Path) -> None:
        """read_by_cycle accurately filters by cycle."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        for cycle in ["c1", "c2", "c3"]:
            for i in range(2):
                r = WriteReceipt(f"WL-{cycle}-{i}", "github", "create", None, True, ts, cycle)
                log.append(r)

        c2_receipts = log.read_by_cycle("c2")
        assert len(c2_receipts) == 2
        assert all(r.cycle_id == "c2" for r in c2_receipts)


class TestWriteReceiptLogReadFailures:
    """Tests for read_failures method."""

    def test_read_failures_no_failures(self, tmp_path: Path) -> None:
        """read_failures returns empty list when all succeed."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        for i in range(3):
            r = WriteReceipt(f"WL-{i:03d}", "github", "create", f"gh-{i}", True, ts, "cycle-1")
            log.append(r)

        failures = log.read_failures()
        assert failures == []

    def test_read_failures_all_failures(self, tmp_path: Path) -> None:
        """read_failures returns all failed receipts."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        for i in range(3):
            r = WriteReceipt(f"WL-{i:03d}", "github", "create", None, False, ts, "cycle-1")
            log.append(r)

        failures = log.read_failures()
        assert len(failures) == 3
        assert all(not r.success for r in failures)

    def test_read_failures_mixed(self, tmp_path: Path) -> None:
        """read_failures returns only failed receipts."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        success = WriteReceipt("WL-001", "github", "create", "gh-1", True, ts, "cycle-1")
        failure = WriteReceipt("WL-002", "github", "create", None, False, ts, "cycle-1")

        log.append(success)
        log.append(failure)

        failures = log.read_failures()
        assert len(failures) == 1
        assert failures[0].wl_id == "WL-002"

    def test_read_failures_empty_log(self, tmp_path: Path) -> None:
        """read_failures on empty log returns empty list."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        failures = log.read_failures()
        assert failures == []

    @pytest.mark.requirement("WL-308")
    def test_read_failures_accurate_filter(self, tmp_path: Path) -> None:
        """read_failures accurately identifies failures."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        # Add mixed receipts
        log.append(WriteReceipt("WL-001", "github", "create", "gh-1", True, ts, "cycle-1"))
        log.append(WriteReceipt("WL-002", "linear", "update", None, False, ts, "cycle-1"))
        log.append(WriteReceipt("WL-003", "github", "delete", "gh-3", True, ts, "cycle-1"))
        log.append(WriteReceipt("WL-004", "jira", "create", None, False, ts, "cycle-1"))

        failures = log.read_failures()
        assert len(failures) == 2
        assert all(not r.success for r in failures)
        assert {r.wl_id for r in failures} == {"WL-002", "WL-004"}


class TestWriteReceiptLogIntegration:
    """Integration tests for receipt log workflow."""

    def test_full_workflow(self, tmp_path: Path) -> None:
        """Complete workflow: append, read_all, filter, read_failures."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime.now(UTC)

        # Append some receipts
        for i in range(2):
            r = WriteReceipt(f"WL-c1-{i}", "github", "create", f"gh-{i}", True, ts, "cycle-1")
            log.append(r)

        for i in range(2):
            r = WriteReceipt(f"WL-c2-{i}", "github", "create", None, False, ts, "cycle-2")
            log.append(r)

        # Read all
        all_receipts = log.read_all()
        assert len(all_receipts) == 4

        # Read by cycle
        c1_receipts = log.read_by_cycle("cycle-1")
        assert len(c1_receipts) == 2

        # Read failures
        failures = log.read_failures()
        assert len(failures) == 2
        assert all(r.cycle_id == "cycle-2" for r in failures)

    @pytest.mark.requirement("WL-308")
    def test_round_trip_consistency(self, tmp_path: Path) -> None:
        """Data survives write and read."""
        log = WriteReceiptLog(tmp_path / "receipts.jsonl")
        ts = datetime(2026, 2, 22, 15, 30, 45, tzinfo=UTC)
        original = WriteReceipt(
            wl_id="WL-123",
            connector="github",
            operation="delete",
            remote_id="gh-999",
            success=False,
            timestamp=ts,
            cycle_id="cycle-batch-1",
        )

        log.append(original)
        receipts = log.read_all()

        assert len(receipts) == 1
        read_receipt = receipts[0]
        assert read_receipt.wl_id == original.wl_id
        assert read_receipt.connector == original.connector
        assert read_receipt.operation == original.operation
        assert read_receipt.remote_id == original.remote_id
        assert read_receipt.success == original.success
        assert read_receipt.cycle_id == original.cycle_id
