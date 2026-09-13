"""WP-2005: Poison pill detection tests.

Verifies PoisonPillDetector raises PoisonPillError for:
- Single chunk > 100 KB
- Same chunk repeated > 5 times in 10s
- tool_use count > 200

# @trace WL-039 WP-2005
"""

from __future__ import annotations

import pytest

from thegent.governance.poison_pill import (
    CHUNK_SIZE_LIMIT_BYTES,
    REPEAT_COUNT_LIMIT,
    TOOL_USE_LIMIT,
    PoisonPillDetector,
    PoisonPillError,
)

# ---------------------------------------------------------------------------
# Chunk overflow tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestChunkOverflow:
    """Chunks exceeding 100 KB must raise PoisonPillError immediately."""

    def test_chunk_exactly_at_limit_ok(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        # Exactly at limit is fine
        chunk = "x" * CHUNK_SIZE_LIMIT_BYTES
        detector.scan_chunk(chunk)  # must not raise

    def test_chunk_one_byte_over_limit_raises(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        chunk = "x" * (CHUNK_SIZE_LIMIT_BYTES + 1)
        with pytest.raises(PoisonPillError) as exc_info:
            detector.scan_chunk(chunk)
        assert exc_info.value.kind == "chunk_overflow"

    def test_chunk_10x_limit_raises(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        chunk = "a" * (CHUNK_SIZE_LIMIT_BYTES * 10)
        with pytest.raises(PoisonPillError, match="chunk_overflow"):
            detector.scan_chunk(chunk)

    def test_chunk_overflow_emits_governance_event(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        chunk = "z" * (CHUNK_SIZE_LIMIT_BYTES + 1000)
        with pytest.raises(PoisonPillError):
            detector.scan_chunk(chunk)
        events = detector.governance_log
        assert len(events) == 1
        assert events[0]["event"] == "poison_pill_detected"
        assert events[0]["kind"] == "chunk_overflow"

    def test_multiple_small_unique_chunks_do_not_raise(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        for i in range(50):
            detector.scan_chunk(f"hello world {i}")  # unique content, should not raise

    def test_empty_chunk_ok(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        detector.scan_chunk("")  # empty chunk is fine


# ---------------------------------------------------------------------------
# Repeat chunk tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRepeatChunk:
    """The same chunk repeated >= REPEAT_COUNT_LIMIT times in 10s triggers poison pill."""

    def test_repeat_below_limit_ok(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        for _ in range(REPEAT_COUNT_LIMIT - 1):
            detector.scan_chunk("looping output")  # must not raise

    def test_repeat_at_limit_raises(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        for _ in range(REPEAT_COUNT_LIMIT):
            detector.scan_chunk("loop")
        # The REPEAT_COUNT_LIMIT-th scan records, next one triggers
        with pytest.raises(PoisonPillError) as exc_info:
            detector.scan_chunk("loop")
        assert exc_info.value.kind == "repeat_chunk"

    def test_repeat_emits_governance_event(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        for _ in range(REPEAT_COUNT_LIMIT):
            detector.scan_chunk("repeated")
        with pytest.raises(PoisonPillError):
            detector.scan_chunk("repeated")
        events = detector.governance_log
        assert any(e["kind"] == "repeat_chunk" for e in events)

    def test_different_chunks_do_not_trigger_repeat(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        for i in range(20):
            detector.scan_chunk(f"chunk-{i}")  # all unique, must not raise


# ---------------------------------------------------------------------------
# Tool use overflow tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestToolUseOverflow:
    """Tool use count exceeding TOOL_USE_LIMIT must raise PoisonPillError."""

    def test_tool_use_at_limit_ok(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        for _ in range(TOOL_USE_LIMIT):
            detector.record_tool_use()  # exactly at limit is fine

    def test_tool_use_one_over_raises(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        for _ in range(TOOL_USE_LIMIT):
            detector.record_tool_use()
        with pytest.raises(PoisonPillError) as exc_info:
            detector.record_tool_use()
        assert exc_info.value.kind == "tool_use_overflow"

    def test_tool_use_overflow_emits_governance_event(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        for _ in range(TOOL_USE_LIMIT):
            detector.record_tool_use()
        with pytest.raises(PoisonPillError):
            detector.record_tool_use()
        events = detector.governance_log
        assert any(e["kind"] == "tool_use_overflow" for e in events)

    def test_tool_use_counter_increments(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        for i in range(10):
            detector.record_tool_use()
            assert detector.tool_use_count == i + 1


# ---------------------------------------------------------------------------
# Governance log consistency
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGovernanceLog:
    """Governance log captures all emitted events."""

    def test_no_events_on_clean_run(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        detector.scan_chunk("normal output")
        assert detector.governance_log == []

    def test_governance_log_is_copy(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        chunk = "x" * (CHUNK_SIZE_LIMIT_BYTES + 1)
        with pytest.raises(PoisonPillError):
            detector.scan_chunk(chunk)
        log1 = detector.governance_log
        log2 = detector.governance_log
        assert log1 == log2
        assert log1 is not log2  # must be a copy

    def test_governance_event_has_required_fields(self) -> None:
        # @trace WL-039 WP-2005
        detector = PoisonPillDetector()
        chunk = "x" * (CHUNK_SIZE_LIMIT_BYTES + 100)
        with pytest.raises(PoisonPillError):
            detector.scan_chunk(chunk)
        event = detector.governance_log[0]
        required_fields = {"event", "kind", "detail", "tool_use_count", "timestamp"}
        assert required_fields.issubset(set(event.keys()))
