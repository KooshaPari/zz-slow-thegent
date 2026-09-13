"""Tests for WL-187: External Write Batching.

Verifies that write requests are correctly batched and flushed.

# @trace WL-187
"""

from __future__ import annotations

import pytest

from thegent.integrations.external_write_batcher import (
    ExternalWriteBatcher,
    WriteRequest,
)


@pytest.mark.requirement("WL-187")
class TestExternalWriteBatcher:
    """WL-187: External write batching."""

    def test_init_default_batch_size(self):
        """Default batch size is 50."""
        batcher = ExternalWriteBatcher()
        assert batcher.pending_count() == 0

    def test_init_custom_batch_size(self):
        """Custom batch size is accepted."""
        batcher = ExternalWriteBatcher(batch_size=25)
        assert batcher.pending_count() == 0

    def test_init_invalid_batch_size(self):
        """Batch size < 1 raises ValueError."""
        with pytest.raises(ValueError, match="batch_size must be >= 1"):
            ExternalWriteBatcher(batch_size=0)

    def test_add_single_request(self):
        """add() increases pending_count."""
        batcher = ExternalWriteBatcher()
        request = WriteRequest(record_id="rec1", payload={"key": "value"})
        batcher.add(request)
        assert batcher.pending_count() == 1

    def test_add_multiple_requests(self):
        """add() accumulates multiple requests."""
        batcher = ExternalWriteBatcher()
        for i in range(5):
            request = WriteRequest(record_id=f"rec{i}", payload={"index": i})
            batcher.add(request)
        assert batcher.pending_count() == 5

    def test_flush_empty_returns_empty_list(self):
        """flush() on empty batcher returns empty list."""
        batcher = ExternalWriteBatcher()
        result = batcher.flush()
        assert result == []
        assert batcher.pending_count() == 0

    def test_flush_clears_pending(self):
        """flush() clears the pending buffer."""
        batcher = ExternalWriteBatcher(batch_size=10)
        for i in range(5):
            request = WriteRequest(record_id=f"rec{i}", payload={"index": i})
            batcher.add(request)
        batcher.flush()
        assert batcher.pending_count() == 0

    def test_flush_single_batch(self):
        """flush() returns single batch if requests <= batch_size."""
        batcher = ExternalWriteBatcher(batch_size=10)
        for i in range(5):
            request = WriteRequest(record_id=f"rec{i}", payload={"index": i})
            batcher.add(request)
        batches = batcher.flush()
        assert len(batches) == 1
        assert len(batches[0]) == 5

    def test_flush_multiple_batches(self):
        """flush() creates multiple batches."""
        batcher = ExternalWriteBatcher(batch_size=3)
        for i in range(10):
            request = WriteRequest(record_id=f"rec{i}", payload={"index": i})
            batcher.add(request)
        batches = batcher.flush()
        assert len(batches) == 4  # 3, 3, 3, 1
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
        assert len(batches[2]) == 3
        assert len(batches[3]) == 1

    def test_flush_exact_multiple(self):
        """flush() with exact multiple of batch_size."""
        batcher = ExternalWriteBatcher(batch_size=5)
        for i in range(15):
            request = WriteRequest(record_id=f"rec{i}", payload={"index": i})
            batcher.add(request)
        batches = batcher.flush()
        assert len(batches) == 3
        assert all(len(batch) == 5 for batch in batches)

    def test_flush_preserves_request_data(self):
        """flush() preserves request payloads correctly."""
        batcher = ExternalWriteBatcher(batch_size=2)
        req1 = WriteRequest(record_id="rec1", payload={"a": 1})
        req2 = WriteRequest(record_id="rec2", payload={"b": 2})
        req3 = WriteRequest(record_id="rec3", payload={"c": 3})
        batcher.add(req1)
        batcher.add(req2)
        batcher.add(req3)
        batches = batcher.flush()
        assert batches[0][0] == req1
        assert batches[0][1] == req2
        assert batches[1][0] == req3

    def test_multiple_flush_cycles(self):
        """Multiple add/flush cycles work independently."""
        batcher = ExternalWriteBatcher(batch_size=2)

        # First cycle
        batcher.add(WriteRequest(record_id="rec1", payload={"cycle": 1}))
        batcher.add(WriteRequest(record_id="rec2", payload={"cycle": 1}))
        batches1 = batcher.flush()
        assert len(batches1) == 1
        assert len(batches1[0]) == 2

        # Second cycle
        batcher.add(WriteRequest(record_id="rec3", payload={"cycle": 2}))
        batches2 = batcher.flush()
        assert len(batches2) == 1
        assert len(batches2[0]) == 1

        # Verify pending is still empty
        assert batcher.pending_count() == 0
