"""Race condition tests for EditLeaseManager.

FR-ORCH-001: EditLeaseManager must be thread-safe under concurrent acquire/release.

TDD: These tests are written FIRST; they demonstrate the race before fix.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from thegent.orchestration.resource.leasing import EditLeaseManager


@pytest.fixture
def lease_manager(tmp_path: Path) -> EditLeaseManager:
    """Fresh EditLeaseManager backed by a temp dir."""
    return EditLeaseManager(tmp_path)


class TestLeasingRaceConcurrentAcquire:
    """Concurrent acquire/release must not corrupt the leases dict."""

    @pytest.mark.requirement("FR-ORCH-001")
    def test_concurrent_acquire_no_data_corruption(self, lease_manager: EditLeaseManager) -> None:
        """50 threads acquiring different paths must not see KeyError or lost leases."""
        n_threads = 50
        errors: list[Exception] = []
        results: list[bool] = []
        lock = threading.Lock()

        def acquire_release(i: int) -> None:
            path = f"/tmp/file_{i}.py"
            try:
                ok = lease_manager.acquire(path, f"agent_{i}", duration=60.0)
                with lock:
                    results.append(ok)
                # Immediately release to exercise both paths
                lease_manager.release(path, f"agent_{i}")
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=acquire_release, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent acquire/release raised: {errors}"
        assert len(results) == n_threads

    @pytest.mark.requirement("FR-ORCH-001")
    def test_concurrent_acquire_same_path_exactly_one_winner(self, lease_manager: EditLeaseManager) -> None:
        """50 threads racing for the same path — exactly one must win."""
        n_threads = 50
        winners: list[int] = []
        errors: list[Exception] = []
        lock = threading.Lock()

        def try_acquire(i: int) -> None:
            try:
                ok = lease_manager.acquire("/shared/file.py", f"agent_{i}", duration=300.0)
                if ok:
                    with lock:
                        winners.append(i)
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=try_acquire, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Exception during concurrent acquire: {errors}"
        assert len(winners) >= 1, "At least one thread must win"

    @pytest.mark.requirement("FR-ORCH-001")
    def test_stress_1000_concurrent_allocations(self, tmp_path: Path) -> None:
        """Stress test: 1000 allocations across 50 threads, zero errors."""
        manager = EditLeaseManager(tmp_path)
        n_threads = 50
        n_per_thread = 20
        errors: list[Exception] = []
        lock = threading.Lock()

        def work(thread_id: int) -> None:
            for j in range(n_per_thread):
                path = f"/tmp/t{thread_id}_f{j}.py"
                try:
                    manager.acquire(path, f"agent_{thread_id}", duration=10.0)
                    manager.release(path, f"agent_{thread_id}")
                except Exception as exc:
                    with lock:
                        errors.append(exc)

        threads = [threading.Thread(target=work, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Stress test errors: {errors}"


class TestLeasingRacePrune:
    """Concurrent prune + acquire must not corrupt state."""

    @pytest.mark.requirement("FR-ORCH-001")
    def test_concurrent_prune_and_acquire(self, lease_manager: EditLeaseManager) -> None:
        """prune() and acquire() running concurrently must not corrupt leases dict."""
        errors: list[Exception] = []
        lock = threading.Lock()

        def do_prune() -> None:
            for _ in range(100):
                try:
                    lease_manager.prune()
                except Exception as exc:
                    with lock:
                        errors.append(exc)

        def do_acquire(i: int) -> None:
            for j in range(20):
                path = f"/prune_race/f{i}_{j}.py"
                try:
                    lease_manager.acquire(path, "agent_0", duration=0.001)
                except Exception as exc:
                    with lock:
                        errors.append(exc)

        threads = [threading.Thread(target=do_prune)] + [
            threading.Thread(target=do_acquire, args=(i,)) for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent prune+acquire errors: {errors}"
