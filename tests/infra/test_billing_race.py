"""Race condition tests for TeamBillingManager.

FR-ORCH-002: TeamBillingManager.record_usage must be atomic — concurrent
             writes must not corrupt or lose quota data.

TDD: These tests are written FIRST to demonstrate the race, then the fix is applied.
"""

from __future__ import annotations

import threading
from pathlib import Path

import orjson as json
import pytest

from thegent.orchestration.resource.billing import TeamBillingManager


@pytest.fixture
def billing_manager(tmp_path: Path) -> TeamBillingManager:
    """Fresh TeamBillingManager with pre-seeded quota."""
    mgr = TeamBillingManager(tmp_path)
    mgr.quotas_path.write_text(
        json.dumps(
            {
                "team1": {
                    "max_runs": 100_000,
                    "used_runs": 0,
                    "max_tokens": 1_000_000,
                    "used_tokens": 0,
                    "budget_usd": 10_000.0,
                    "used_usd": 0.0,
                }
            }
        ).decode(),
        encoding="utf-8",
    )
    return mgr


class TestBillingRaceConcurrentRecordUsage:
    """Concurrent record_usage must not corrupt or lose updates."""

    @pytest.mark.requirement("FR-ORCH-002")
    def test_concurrent_record_usage_no_lost_updates(
        self, billing_manager: TeamBillingManager
    ) -> None:
        """50 concurrent run-recording threads must result in exactly 50 used_runs."""
        n_threads = 50
        errors: list[Exception] = []
        lock = threading.Lock()
        barrier = threading.Barrier(n_threads)

        def record(_i: int) -> None:
            barrier.wait()  # All start simultaneously
            try:
                billing_manager.record_usage("team1", "run", 1.0)
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=record, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent record_usage raised: {errors}"

        data = json.loads(billing_manager.quotas_path.read_text(encoding="utf-8"))
        used = data["team1"]["used_runs"]
        assert used == n_threads, (
            f"RACE: expected {n_threads} used_runs, got {used} (lost {n_threads - used} updates)"
        )

    @pytest.mark.requirement("FR-ORCH-002")
    def test_concurrent_token_and_usd_no_lost_updates(
        self, billing_manager: TeamBillingManager
    ) -> None:
        """Concurrent token + USD updates must not corrupt each other."""
        n_threads = 30
        errors: list[Exception] = []
        lock = threading.Lock()
        barrier = threading.Barrier(n_threads * 2)

        def record_tokens(_i: int) -> None:
            barrier.wait()
            try:
                billing_manager.record_usage("team1", "tokens", 100.0)
            except Exception as exc:
                with lock:
                    errors.append(exc)

        def record_usd(_i: int) -> None:
            barrier.wait()
            try:
                billing_manager.record_usage("team1", "usd", 0.01)
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [
            threading.Thread(target=record_tokens, args=(i,)) for i in range(n_threads)
        ] + [threading.Thread(target=record_usd, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors during concurrent billing: {errors}"

        data = json.loads(billing_manager.quotas_path.read_text(encoding="utf-8"))
        expected_tokens = n_threads * 100
        expected_usd = round(n_threads * 0.01, 10)

        assert data["team1"]["used_tokens"] == expected_tokens, (
            f"Token race: expected {expected_tokens}, got {data['team1']['used_tokens']}"
        )
        assert abs(data["team1"]["used_usd"] - expected_usd) < 1e-9, (
            f"USD race: expected {expected_usd}, got {data['team1']['used_usd']}"
        )

    @pytest.mark.requirement("FR-ORCH-002")
    def test_stress_1000_concurrent_record_usage(self, tmp_path: Path) -> None:
        """Stress: 1000 concurrent record_usage calls (50 threads x 20 ops), zero errors, exact count."""
        mgr = TeamBillingManager(tmp_path)
        mgr.quotas_path.write_text(
            json.dumps(
                {
                    "stress_team": {
                        "max_runs": 1_000_000,
                        "used_runs": 0,
                        "max_tokens": 1_000_000,
                        "used_tokens": 0,
                        "budget_usd": 100_000.0,
                        "used_usd": 0.0,
                    }
                }
            ).decode(),
            encoding="utf-8",
        )

        n_threads = 50
        n_per_thread = 20
        errors: list[Exception] = []
        lock = threading.Lock()

        def work(_tid: int) -> None:
            for _ in range(n_per_thread):
                try:
                    mgr.record_usage("stress_team", "run", 1.0)
                except Exception as exc:
                    with lock:
                        errors.append(exc)

        threads = [threading.Thread(target=work, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Stress test errors: {errors}"

        data = json.loads(mgr.quotas_path.read_text(encoding="utf-8"))
        expected = n_threads * n_per_thread
        assert data["stress_team"]["used_runs"] == expected, (
            f"Stress race: expected {expected}, got {data['stress_team']['used_runs']}"
        )
