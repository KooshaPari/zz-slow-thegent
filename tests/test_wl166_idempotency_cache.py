"""Tests for WL-166: Idempotency Index Cache.

@pytest.mark.requirement("WL-166")
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import orjson as json
import pytest

from thegent.integrations.idempotency_cache import IdempotencyCache, IdempotencyRecord

# ---------------------------------------------------------------------------
# Test: IdempotencyRecord
# ---------------------------------------------------------------------------


class TestIdempotencyRecord:
    """Test IdempotencyRecord dataclass."""

    @pytest.mark.requirement("WL-166")
    def test_create_record(self) -> None:
        """Test creating an IdempotencyRecord."""
        record = IdempotencyRecord(
            operation_id="op-001",
            wl_id="WL-160",
            connector="github",
            timestamp="2026-02-22T10:00:00+00:00",
            content_hash="abc123",
        )
        assert record.operation_id == "op-001"
        assert record.wl_id == "WL-160"
        assert record.connector == "github"

    @pytest.mark.requirement("WL-166")
    def test_record_to_dict(self) -> None:
        """Test serializing a record to dict."""
        record = IdempotencyRecord(
            operation_id="op-002",
            wl_id="WL-161",
            connector="linear",
            timestamp="2026-02-22T10:00:00+00:00",
            content_hash="xyz789",
        )
        d = record.to_dict()
        assert d["operation_id"] == "op-002"
        assert d["wl_id"] == "WL-161"
        assert d["connector"] == "linear"

    @pytest.mark.requirement("WL-166")
    def test_record_from_dict(self) -> None:
        """Test deserializing a record from dict."""
        d = {
            "operation_id": "op-003",
            "wl_id": "WL-162",
            "connector": "workstream",
            "timestamp": "2026-02-22T10:00:00+00:00",
            "content_hash": "def456",
        }
        record = IdempotencyRecord.from_dict(d)
        assert record.operation_id == "op-003"
        assert record.wl_id == "WL-162"
        assert record.connector == "workstream"


# ---------------------------------------------------------------------------
# Test: IdempotencyCache
# ---------------------------------------------------------------------------


class TestIdempotencyCacheBasic:
    """Test basic cache operations."""

    @pytest.mark.requirement("WL-166")
    def test_check_nonexistent_operation(self, tmp_path: Path) -> None:
        """Test checking for an operation that doesn't exist."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")
        assert not cache.check("op-001")

    @pytest.mark.requirement("WL-166")
    def test_record_and_check(self, tmp_path: Path) -> None:
        """Test recording and checking an operation."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")

        cache.record(
            operation_id="op-001",
            wl_id="WL-160",
            connector="github",
            content_hash="hash123",
        )

        assert cache.check("op-001")

    @pytest.mark.requirement("WL-166")
    def test_record_multiple_operations(self, tmp_path: Path) -> None:
        """Test recording multiple operations."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")

        for i in range(5):
            cache.record(
                operation_id=f"op-{i:03d}",
                wl_id="WL-160",
                connector="github",
                content_hash=f"hash{i}",
            )

        for i in range(5):
            assert cache.check(f"op-{i:03d}")

    @pytest.mark.requirement("WL-166")
    def test_check_content_index(self, tmp_path: Path) -> None:
        """Equivalent connector+wl+hash content should be indexed."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")
        cache.record(
            operation_id="op-idx-001",
            wl_id="WL-166",
            connector="github",
            content_hash="abc123",
        )

        assert cache.check_content("github", "WL-166", "abc123")
        assert not cache.check_content("github", "WL-166", "different")

    @pytest.mark.requirement("WL-166")
    def test_invalidate_operation(self, tmp_path: Path) -> None:
        """Test removing an operation from the cache."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")

        cache.record(
            operation_id="op-001",
            wl_id="WL-160",
            connector="github",
            content_hash="hash123",
        )
        assert cache.check("op-001")

        cache.invalidate("op-001")
        assert not cache.check("op-001")

    @pytest.mark.requirement("WL-166")
    def test_invalidate_nonexistent_operation(self, tmp_path: Path) -> None:
        """Test invalidating an operation that doesn't exist (no-op)."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")
        # Should not raise
        cache.invalidate("op-nonexistent")

    @pytest.mark.requirement("WL-166")
    def test_clear_older_than_datetime(self, tmp_path: Path) -> None:
        """Test clearing records older than a given datetime."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")

        now = datetime.now(UTC)
        old_time = (now - timedelta(days=2)).isoformat()
        recent_time = now.isoformat()

        # Manually inject old and recent records
        cache._records["op-old"] = IdempotencyRecord(
            operation_id="op-old",
            wl_id="WL-160",
            connector="github",
            timestamp=old_time,
            content_hash="hash-old",
        )
        cache._records["op-recent"] = IdempotencyRecord(
            operation_id="op-recent",
            wl_id="WL-160",
            connector="github",
            timestamp=recent_time,
            content_hash="hash-recent",
        )

        cutoff = now - timedelta(days=1)
        removed = cache.clear_older_than(cutoff)

        assert removed == 1
        assert not cache.check("op-old")
        assert cache.check("op-recent")

    @pytest.mark.requirement("WL-166")
    def test_clear_older_than_string(self, tmp_path: Path) -> None:
        """Test clearing records using an ISO 8601 string cutoff."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")

        old_time = (datetime.now(UTC) - timedelta(days=2)).isoformat()
        recent_time = datetime.now(UTC).isoformat()

        cache._records["op-old"] = IdempotencyRecord(
            operation_id="op-old",
            wl_id="WL-160",
            connector="github",
            timestamp=old_time,
            content_hash="hash-old",
        )
        cache._records["op-recent"] = IdempotencyRecord(
            operation_id="op-recent",
            wl_id="WL-160",
            connector="github",
            timestamp=recent_time,
            content_hash="hash-recent",
        )

        cutoff_str = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        removed = cache.clear_older_than(cutoff_str)

        assert removed == 1
        assert not cache.check("op-old")
        assert cache.check("op-recent")


# ---------------------------------------------------------------------------
# Test: Persistence
# ---------------------------------------------------------------------------


class TestIdempotencyCachePersistence:
    """Test persistence of cache across instances."""

    @pytest.mark.requirement("WL-166")
    def test_cache_persists_to_file(self, tmp_path: Path) -> None:
        """Test that cache is written to the JSON file."""
        cache_path = tmp_path / "cache.json"
        cache = IdempotencyCache(cache_path=cache_path)

        cache.record(
            operation_id="op-001",
            wl_id="WL-160",
            connector="github",
            content_hash="hash123",
        )

        assert cache_path.exists()
        data = json.loads(cache_path.read_text())
        assert len(data["records"]) == 1
        assert data["records"][0]["operation_id"] == "op-001"

    @pytest.mark.requirement("WL-166")
    def test_cache_loads_from_existing_file(self, tmp_path: Path) -> None:
        """Test that cache loads existing records from file."""
        cache_path = tmp_path / "cache.json"

        # Create a cache and add records
        cache1 = IdempotencyCache(cache_path=cache_path)
        cache1.record(
            operation_id="op-001",
            wl_id="WL-160",
            connector="github",
            content_hash="hash123",
        )

        # Create a new cache instance
        cache2 = IdempotencyCache(cache_path=cache_path)
        assert cache2.check("op-001")

    @pytest.mark.requirement("WL-166")
    def test_cache_creates_parent_directory(self, tmp_path: Path) -> None:
        """Test that cache creates parent directory if it doesn't exist."""
        cache_path = tmp_path / "subdir" / "another" / "cache.json"
        cache = IdempotencyCache(cache_path=cache_path)

        cache.record(
            operation_id="op-001",
            wl_id="WL-160",
            connector="github",
            content_hash="hash123",
        )

        assert cache_path.exists()
        assert cache_path.parent.exists()

    @pytest.mark.requirement("WL-166")
    def test_cache_handles_missing_file_gracefully(self, tmp_path: Path) -> None:
        """Test that cache gracefully handles a missing file on load."""
        cache_path = tmp_path / "nonexistent.json"
        # Should not raise
        cache = IdempotencyCache(cache_path=cache_path)
        assert len(cache.get_all_records()) == 0


# ---------------------------------------------------------------------------
# Test: Inspection
# ---------------------------------------------------------------------------


class TestIdempotencyCacheInspection:
    """Test cache inspection methods."""

    @pytest.mark.requirement("WL-166")
    def test_get_all_records(self, tmp_path: Path) -> None:
        """Test retrieving all records from the cache."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")

        cache.record("op-001", "WL-160", "github", "hash1")
        cache.record("op-002", "WL-161", "linear", "hash2")
        cache.record("op-003", "WL-162", "workstream", "hash3")

        records = cache.get_all_records()
        assert len(records) == 3
        assert records[0].operation_id in {"op-001", "op-002", "op-003"}

    @pytest.mark.requirement("WL-166")
    def test_replay_mutation_id_record_is_stable(self, tmp_path: Path) -> None:
        """Re-recording same mutation_id should overwrite, not duplicate."""
        cache = IdempotencyCache(cache_path=tmp_path / "cache.json")
        cache.record("mutation-id-1", "WL-231", "github", "hash-a")
        cache.record("mutation-id-1", "WL-231", "github", "hash-b")
        records = cache.get_all_records()
        assert len(records) == 1
        assert records[0].operation_id == "mutation-id-1"
        assert records[0].content_hash == "hash-b"
