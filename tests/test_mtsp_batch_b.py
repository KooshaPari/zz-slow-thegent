"""Tests for Batch B MTSP infrastructure."""

import asyncio
import os
import tempfile
import threading
import time
from pathlib import Path

import pytest

from thegent.agents.in_process_runner import InProcessAgentRunner
from thegent.orchestration.worker_pool import TaskRequest, TaskWorkerPool
from thegent.testing.port_lease import PortLeaseManager


@pytest.mark.asyncio
async def test_mtsp_02_in_process_runner_cwd_isolation():
    """Test MTSP-02: In-Process Agent Runner cwd isolation."""
    # This test verifies that InProcessAgentRunner correctly handles cwd isolation
    # using the global lock.

    class MockRunner:
        def __init__(self):
            self.cwds = []

        def run(self, prompt, cd, **kwargs):
            # Simulate some work that depends on cwd
            time.sleep(0.1)
            self.cwds.append(os.getcwd())
            return {"stdout": f"Running in {os.getcwd()}", "stderr": "", "exit_code": 0}

    base_runner = MockRunner()
    runner = InProcessAgentRunner("mock", base_runner=base_runner)

    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        tmp1_path = Path(tmp1).resolve()
        tmp2_path = Path(tmp2).resolve()

        # Run two "tasks" in parallel threads
        def task1():
            runner.run("task1", cd=tmp1_path)

        def task2():
            runner.run("task2", cd=tmp2_path)

        t1 = threading.Thread(target=task1)
        t2 = threading.Thread(target=task2)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Verify that both tasks saw their respective cwds
        assert any(str(tmp1_path) in cwd for cwd in base_runner.cwds)
        assert any(str(tmp2_path) in cwd for cwd in base_runner.cwds)


@pytest.mark.asyncio
async def test_mtsp_16_port_lease_manager():
    """Test MTSP-16: Port Lease Manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lease_dir = Path(tmpdir)
        manager = PortLeaseManager(lease_dir=lease_dir, port_range=(9100, 9105))

        # Lease a port
        port1 = manager.lease_port()
        assert 9100 <= port1 <= 9105
        assert (lease_dir / f"{port1}.lock").exists()

        # Lease another port
        port2 = manager.lease_port()
        assert 9100 <= port2 <= 9105
        assert port1 != port2
        assert (lease_dir / f"{port2}.lock").exists()

        # Release ports
        manager.release_port(port1)
        assert not (lease_dir / f"{port1}.lock").exists()

        manager.release_port(port2)
        assert not (lease_dir / f"{port2}.lock").exists()


@pytest.mark.asyncio
async def test_mtsp_03_task_worker_pool():
    """Test MTSP-03: Task Worker Pool."""
    with tempfile.TemporaryDirectory() as tmpdir:
        queue_dir = Path(tmpdir)
        pool = TaskWorkerPool(max_workers=2, queue_dir=queue_dir)

        # Start pool in background task
        pool_task = asyncio.create_task(pool.start())

        try:
            # Submit a simple task
            task = TaskRequest(command=["echo", "hello mtsp"])
            pool.submit_task(task)

            # Wait for result
            result = pool.get_result(task.id, timeout=10)
            assert result is not None
            assert "hello mtsp" in result.stdout
            assert result.exit_code == 0
        finally:
            pool.stop()
            await pool_task
