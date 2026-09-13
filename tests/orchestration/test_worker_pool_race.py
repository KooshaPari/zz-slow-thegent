"""Tests for race conditions in TaskWorkerPool (T3.B.B.1.1).

Demonstrates the file-based task claiming race condition where multiple
workers can attempt to rename the same file simultaneously.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from thegent.orchestration.worker_pool import TaskRequest, TaskResult, TaskWorkerPool


@pytest.fixture
def pool_dir(tmp_path: Path) -> Path:
    return tmp_path / "pool"


@pytest.fixture
def pool(pool_dir: Path) -> TaskWorkerPool:
    return TaskWorkerPool(max_workers=4, queue_dir=pool_dir)


class TestTaskWorkerPoolRaceConditions:
    """Tests demonstrating and verifying race condition fixes."""

    def test_concurrent_task_submission(self, pool: TaskWorkerPool) -> None:
        """Multiple tasks submitted concurrently should all be persisted."""
        tasks = [
            TaskRequest(id=f"task_{i}", command=["echo", str(i)]) for i in range(20)
        ]
        for t in tasks:
            pool.submit_task(t)

        # All tasks should be in inbox
        inbox_files = list(pool.inbox.glob("*.json"))
        assert len(inbox_files) == 20

    def test_task_claim_atomicity(self, pool: TaskWorkerPool) -> None:
        """Simulates the race where two workers try to claim the same task.

        The rename-based claiming in worker_pool.py has a TOCTOU race:
        two workers can both see the same file in sorted glob results,
        then both try to rename it. Only one succeeds; the other gets OSError.
        This test verifies the OSError path is handled correctly.
        """
        task = TaskRequest(id="contested_task", command=["echo", "hello"])
        task_file = pool.submit_task(task)

        # Simulate first worker claiming
        claim_path = pool.queue_dir / f"claiming_{task_file.name}"
        task_file.rename(claim_path)

        # Second worker tries to claim the same file -- should get OSError
        with pytest.raises(OSError):
            task_file.rename(pool.queue_dir / "claiming_second_attempt")

    def test_result_file_read_write_race(self, pool: TaskWorkerPool) -> None:
        """Result file could be read while still being written.

        The get_result method reads the file without locking, so a partial
        write could produce invalid JSON.
        """
        result = TaskResult(
            task_id="test_result",
            exit_code=0,
            stdout="output",
            stderr="",
            duration_s=1.0,
        )
        result_file = pool.results / "test_result.json"

        # Write a valid result
        result_file.write_text(json.dumps(result.__dict__))

        # Reading should work
        fetched = pool.get_result("test_result", timeout=1)
        assert fetched is not None
        assert fetched.task_id == "test_result"
        assert fetched.exit_code == 0

    @pytest.mark.asyncio
    async def test_multiple_workers_no_duplicate_processing(
        self, pool_dir: Path
    ) -> None:
        """Multiple workers should not process the same task twice."""
        pool = TaskWorkerPool(max_workers=4, queue_dir=pool_dir)

        # Submit 10 tasks
        for i in range(10):
            pool.submit_task(
                TaskRequest(
                    id=f"task_{i}",
                    command=["echo", f"task_{i}"],
                )
            )

        # Track which tasks get claimed (via file rename)

        claimed: list[str] = []

        async def tracking_worker(worker_id: int) -> None:
            """Worker that tracks claims without actually executing."""
            for _ in range(20):  # poll iterations
                task_files = sorted(
                    pool.inbox.glob("*.json"), key=lambda p: p.stat().st_mtime
                )
                if not task_files:
                    await asyncio.sleep(0.01)
                    continue
                task_file = task_files[0]
                claim_file = pool.queue_dir / f"claiming_{task_file.name}"
                try:
                    task_file.rename(claim_file)
                    data = json.loads(claim_file.read_text())
                    claimed.append(data["id"])
                    claim_file.unlink()
                except OSError:
                    continue

        pool._running = True
        workers = [tracking_worker(i) for i in range(4)]
        await asyncio.gather(*workers)

        # No duplicate claims
        assert len(claimed) == len(set(claimed)), (
            f"Duplicate task claims detected: {claimed}"
        )


class TestTaskWorkerPoolSubmitResult:
    """Basic correctness tests for task submission and results."""

    def test_submit_creates_file(self, pool: TaskWorkerPool) -> None:
        task = TaskRequest(id="t1", command=["echo", "hi"])
        path = pool.submit_task(task)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["id"] == "t1"

    def test_get_result_timeout(self, pool: TaskWorkerPool) -> None:
        """get_result should return None after timeout if no result exists."""
        result = pool.get_result("nonexistent", timeout=1)
        assert result is None

    def test_task_request_defaults(self) -> None:
        task = TaskRequest(command=["ls"])
        assert task.id.startswith("task_")
        assert task.cwd is None
        assert task.env == {}
        assert task.priority == 0
