"""Tests for per-owner usage tracking in ConcurrencyController.

@trace FR-ORC-001 (swarm-usage-tracking)
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from thegent.execution import ConcurrencyController
from thegent.orchestration.resource.load_based_limits import (
    OwnerStats,
    UsageTracker,
    get_usage_tracker,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# OwnerStats unit tests
# ---------------------------------------------------------------------------


class TestOwnerStats:
    """Tests for the OwnerStats dataclass."""

    def test_defaults(self) -> None:  # @trace FR-ORC-001
        stats = OwnerStats(owner="alice")
        assert stats.owner == "alice"
        assert stats.active_count == 0
        assert stats.total_runs == 0
        assert stats.total_elapsed_ms == 0.0

    def test_avg_elapsed_ms_zero_runs(self) -> None:  # @trace FR-ORC-001
        stats = OwnerStats(owner="bob")
        assert stats.avg_elapsed_ms == 0.0

    def test_avg_elapsed_ms_with_runs(self) -> None:  # @trace FR-ORC-001
        stats = OwnerStats(owner="carol", total_runs=4, total_elapsed_ms=200.0)
        assert stats.avg_elapsed_ms == pytest.approx(50.0)

    def test_to_dict_keys(self) -> None:  # @trace FR-ORC-001
        stats = OwnerStats(owner="dave", active_count=2, total_runs=5, total_elapsed_ms=500.0)
        d = stats.to_dict()
        assert d["owner"] == "dave"
        assert d["active_count"] == 2
        assert d["total_runs"] == 5
        assert d["total_elapsed_ms"] == pytest.approx(500.0)
        assert d["avg_elapsed_ms"] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# UsageTracker unit tests
# ---------------------------------------------------------------------------


@pytest.fixture
def tracker() -> UsageTracker:
    """Fresh UsageTracker instance per test (isolated from the singleton)."""
    return UsageTracker()


class TestUsageTrackerRecordStart:
    """Tests for UsageTracker.record_start."""

    def test_increments_active_count(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("agent-a", "run-1")
        assert tracker.get_stats("agent-a").active_count == 1

    def test_multiple_starts_same_owner(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("agent-a", "run-1")
        tracker.record_start("agent-a", "run-2")
        assert tracker.get_stats("agent-a").active_count == 2

    def test_does_not_affect_total_runs(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("agent-a", "run-1")
        assert tracker.get_stats("agent-a").total_runs == 0

    def test_isolates_owners(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("owner-x", "run-1")
        tracker.record_start("owner-y", "run-2")
        assert tracker.get_stats("owner-x").active_count == 1
        assert tracker.get_stats("owner-y").active_count == 1


class TestUsageTrackerRecordEnd:
    """Tests for UsageTracker.record_end."""

    def test_decrements_active_count(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("agent-a", "run-1")
        tracker.record_end("agent-a", "run-1", 100.0)
        assert tracker.get_stats("agent-a").active_count == 0

    def test_clamps_active_count_at_zero(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        # record_end without a prior record_start must not go negative.
        tracker.record_end("agent-a", "run-1", 100.0)
        assert tracker.get_stats("agent-a").active_count == 0

    def test_increments_total_runs(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("agent-a", "run-1")
        tracker.record_end("agent-a", "run-1", 100.0)
        assert tracker.get_stats("agent-a").total_runs == 1

    def test_accumulates_elapsed_ms(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("agent-a", "run-1")
        tracker.record_end("agent-a", "run-1", 150.0)
        tracker.record_start("agent-a", "run-2")
        tracker.record_end("agent-a", "run-2", 250.0)
        stats = tracker.get_stats("agent-a")
        assert stats.total_runs == 2
        assert stats.total_elapsed_ms == pytest.approx(400.0)
        assert stats.avg_elapsed_ms == pytest.approx(200.0)

    def test_partial_decrement(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("agent-a", "run-1")
        tracker.record_start("agent-a", "run-2")
        tracker.record_end("agent-a", "run-1", 50.0)
        assert tracker.get_stats("agent-a").active_count == 1


class TestUsageTrackerGetStats:
    """Tests for UsageTracker.get_stats."""

    def test_unknown_owner_returns_zero_stats(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        stats = tracker.get_stats("nobody")
        assert stats.owner == "nobody"
        assert stats.active_count == 0
        assert stats.total_runs == 0

    def test_returns_snapshot_not_reference(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("agent-a", "run-1")
        snap1 = tracker.get_stats("agent-a")
        tracker.record_start("agent-a", "run-2")
        # snap1 must remain at active_count=1
        assert snap1.active_count == 1


class TestUsageTrackerGetAllStats:
    """Tests for UsageTracker.get_all_stats."""

    def test_empty_when_no_records(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        assert tracker.get_all_stats() == {}

    def test_returns_all_owners(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("owner-a", "run-1")
        tracker.record_start("owner-b", "run-2")
        all_stats = tracker.get_all_stats()
        assert "owner-a" in all_stats
        assert "owner-b" in all_stats

    def test_returns_snapshots(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("owner-a", "run-1")
        snap = tracker.get_all_stats()["owner-a"]
        tracker.record_start("owner-a", "run-2")
        assert snap.active_count == 1


class TestUsageTrackerReset:
    """Tests for UsageTracker.reset."""

    def test_reset_specific_owner(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("owner-a", "run-1")
        tracker.record_start("owner-b", "run-2")
        tracker.reset("owner-a")
        assert "owner-a" not in tracker.get_all_stats()
        assert "owner-b" in tracker.get_all_stats()

    def test_reset_all(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.record_start("owner-a", "run-1")
        tracker.record_start("owner-b", "run-2")
        tracker.reset()
        assert tracker.get_all_stats() == {}

    def test_reset_unknown_owner_is_safe(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        tracker.reset("nobody")  # Must not raise


class TestUsageTrackerThreadSafety:
    """Concurrent stress tests to verify threading.Lock correctness."""

    def test_concurrent_starts_and_ends(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        n_threads = 20
        runs_per_thread = 50
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for i in range(runs_per_thread):
                    run_id = f"run-{threading.current_thread().name}-{i}"
                    tracker.record_start("shared-owner", run_id)
                    tracker.record_end("shared-owner", run_id, float(i))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        stats = tracker.get_stats("shared-owner")
        assert stats.active_count == 0
        assert stats.total_runs == n_threads * runs_per_thread

    def test_concurrent_different_owners(self, tracker: UsageTracker) -> None:  # @trace FR-ORC-001
        n_owners = 10
        errors: list[Exception] = []

        def worker(owner_id: int) -> None:
            try:
                owner = f"owner-{owner_id}"
                for i in range(5):
                    tracker.record_start(owner, f"run-{i}")
                    tracker.record_end(owner, f"run-{i}", 10.0)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_owners)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        all_stats = tracker.get_all_stats()
        assert len(all_stats) == n_owners
        for stats in all_stats.values():
            assert stats.total_runs == 5
            assert stats.active_count == 0


# ---------------------------------------------------------------------------
# Module-level singleton test
# ---------------------------------------------------------------------------


class TestGetUsageTrackerSingleton:
    """get_usage_tracker() must return the same instance every time."""

    def test_singleton_identity(self) -> None:  # @trace FR-ORC-001
        t1 = get_usage_tracker()
        t2 = get_usage_tracker()
        assert t1 is t2


# ---------------------------------------------------------------------------
# ConcurrencyController integration tests
# ---------------------------------------------------------------------------


@pytest.fixture
def cc(tmp_path: Path) -> ConcurrencyController:
    """ConcurrencyController with an isolated UsageTracker."""
    ctrl = ConcurrencyController(
        session_dir=tmp_path,
        max_concurrency=5,
        use_load_based=False,
    )
    # Inject an isolated tracker so this test does not affect the singleton.
    ctrl._usage_tracker = UsageTracker()
    return ctrl


def _patch_sessions(running: int):
    """Return a context manager that mocks ps_impl to report *running* running sessions."""
    fake_sessions = [{"status": "running"}] * running
    return patch("thegent.cli.commands.impl.ps_impl", return_value=fake_sessions)


class TestConcurrencyControllerUsageIntegration:
    """Integration tests: ConcurrencyController calls UsageTracker correctly."""

    def test_acquire_calls_record_start_when_admitted(self, cc: ConcurrencyController) -> None:  # @trace FR-ORC-001
        with _patch_sessions(0):
            admitted = cc.acquire(owner="agent-x", run_id="run-001")
        assert admitted is True
        assert cc._usage_tracker.get_stats("agent-x").active_count == 1

    def test_acquire_does_not_call_record_start_when_blocked(
        self, cc: ConcurrencyController
    ) -> None:  # @trace FR-ORC-001
        # Fill all 5 slots so the next acquire is blocked.
        with _patch_sessions(5):
            admitted = cc.acquire(owner="agent-y", run_id="run-002")
        assert admitted is False
        assert cc._usage_tracker.get_stats("agent-y").active_count == 0

    def test_release_calls_record_end(self, cc: ConcurrencyController) -> None:  # @trace FR-ORC-001
        with _patch_sessions(0):
            cc.acquire(owner="agent-z", run_id="run-003")
        cc.release(owner="agent-z", run_id="run-003", elapsed_ms=250.0)
        stats = cc._usage_tracker.get_stats("agent-z")
        assert stats.active_count == 0
        assert stats.total_runs == 1
        assert stats.total_elapsed_ms == pytest.approx(250.0)

    def test_get_usage_stats_returns_serializable_dict(self, cc: ConcurrencyController) -> None:  # @trace FR-ORC-001
        with _patch_sessions(0):
            cc.acquire(owner="agent-w", run_id="run-004")
        cc.release(owner="agent-w", run_id="run-004", elapsed_ms=100.0)
        result = cc.get_usage_stats()
        assert "agent-w" in result
        assert result["agent-w"]["total_runs"] == 1
        assert result["agent-w"]["avg_elapsed_ms"] == pytest.approx(100.0)

    def test_get_usage_stats_empty_when_no_activity(self, cc: ConcurrencyController) -> None:  # @trace FR-ORC-001
        result = cc.get_usage_stats()
        assert result == {}

    def test_multiple_owners_tracked_independently(self, cc: ConcurrencyController) -> None:  # @trace FR-ORC-001
        with _patch_sessions(0):
            cc.acquire(owner="owner-1", run_id="r1")
        with _patch_sessions(1):
            cc.acquire(owner="owner-2", run_id="r2")

        cc.release(owner="owner-1", run_id="r1", elapsed_ms=50.0)
        cc.release(owner="owner-2", run_id="r2", elapsed_ms=75.0)

        stats = cc.get_usage_stats()
        assert stats["owner-1"]["total_elapsed_ms"] == pytest.approx(50.0)
        assert stats["owner-2"]["total_elapsed_ms"] == pytest.approx(75.0)
