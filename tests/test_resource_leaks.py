"""Tests for resource leaks using psleak framework, tracemalloc, and CPython patterns."""

import gc
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Skip psleak tests if not available
try:
    from psleak import Checkers, MemoryLeakTestCase
except ImportError:
    psleak_available = False
    MemoryLeakTestCase = None
    Checkers = None
else:
    psleak_available = True

from thegent.infra.process_registry import get_registry
from thegent.infra.subprocess_manager import get_subprocess_manager

# Skip psleak tests if not available
if not psleak_available:
    pytest.skip("psleak not available", allow_module_level=True)


class TestSubprocessLeaks(MemoryLeakTestCase):
    """Test for subprocess resource leaks."""

    def test_subprocess_manager_no_leak(self):
        """Test that SubprocessManager doesn't leak resources."""
        manager = get_subprocess_manager()

        def create_processes():
            for i in range(10):
                with manager.popen(["sleep", "0.1"], name=f"test-{i}"):
                    pass

        # psleak will detect if this leaks
        self.execute(
            create_processes,
            times=50,
            checkers=Checkers.only("memory", "fds"),
        )

    def test_subprocess_manager_with_output_no_leak(self):
        """Test that SubprocessManager doesn't leak when capturing output."""
        manager = get_subprocess_manager()

        def create_processes_with_output():
            for i in range(10):
                result = manager.run(
                    ["echo", f"test-{i}"],
                    name=f"test-output-{i}",
                    timeout=5.0,
                )
                assert result.returncode == 0

        self.execute(
            create_processes_with_output,
            times=30,
            checkers=Checkers.only("memory", "fds"),
        )


class TestFileDescriptorLeaks(MemoryLeakTestCase):
    """Test for file descriptor leaks."""

    def test_file_operations_no_leak(self):
        """Test that file operations don't leak FDs."""
        temp_dir = Path(tempfile.mkdtemp())

        def open_files():
            for i in range(100):
                file_path = temp_dir / f"test-{i}.txt"
                with open(file_path, "w") as f:
                    f.write("test")
                # File should be closed automatically

        try:
            self.execute(
                open_files,
                times=10,
                checkers=Checkers.only("fds"),
            )
        finally:
            # Cleanup
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_subprocess_with_file_output_no_leak(self):
        """Test that subprocess with file output doesn't leak FDs."""
        manager = get_subprocess_manager()
        temp_dir = Path(tempfile.mkdtemp())

        def create_processes_with_files():
            for i in range(50):
                file_path = temp_dir / f"output-{i}.txt"
                with open(file_path, "w") as f:
                    manager.run(
                        ["echo", f"test-{i}"],
                        name=f"test-file-{i}",
                        stdout=f,
                        timeout=5.0,
                    )

        try:
            self.execute(
                create_processes_with_files,
                times=5,
                checkers=Checkers.only("fds"),
            )
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)


class TestProcessRegistryLeaks(MemoryLeakTestCase):
    """Test for process registry leaks."""

    def test_process_registry_no_leak(self):
        """Test that ProcessRegistry doesn't leak processes."""
        registry = get_registry()

        def register_and_cleanup():
            manager = get_subprocess_manager()
            for i in range(20):
                with manager.popen(["sleep", "0.1"], name=f"registry-test-{i}"):
                    pass
            # Clean up orphaned processes
            registry.cleanup_orphaned()

        self.execute(
            register_and_cleanup,
            times=20,
            checkers=Checkers.only("memory", "fds"),
        )


class TestResourceMonitorLeaks(MemoryLeakTestCase):
    """Test for resource monitor leaks."""

    def test_resource_monitor_no_leak(self):
        """Test that ResourceMonitor doesn't leak resources."""
        from thegent.infra.resource_monitor import get_resource_monitor

        monitor = get_resource_monitor()

        def monitor_resources():
            for _ in range(100):
                stats = monitor.get_stats()
                assert stats.fd_count >= 0
                assert stats.memory_mb >= 0

        self.execute(
            monitor_resources,
            times=10,
            checkers=Checkers.only("memory", "fds"),
        )


class TestConcurrentProcessLeaks(MemoryLeakTestCase):
    """Test for concurrent process leaks."""

    def test_concurrent_processes_no_leak(self):
        """Test that concurrent processes don't leak."""
        manager = get_subprocess_manager()

        def create_concurrent_processes():
            # Create multiple processes concurrently
            processes = []
            for i in range(10):
                proc = manager.popen(["sleep", "0.2"], name=f"concurrent-{i}")
                processes.append(proc)

            # Wait for all to complete
            for proc in processes:
                with proc:
                    proc.wait()

        self.execute(
            create_concurrent_processes,
            times=10,
            checkers=Checkers.only("memory", "fds"),
        )


@pytest.mark.slow
class TestLongRunningLeaks(MemoryLeakTestCase):
    """Test for leaks in long-running operations."""

    def test_long_running_processes_no_leak(self):
        """Test that long-running processes don't leak."""
        manager = get_subprocess_manager()

        def create_long_running():
            for i in range(5):
                with manager.popen(["sleep", "1.0"], name=f"long-{i}"):
                    time.sleep(0.1)  # Let process start

        self.execute(
            create_long_running,
            times=20,
            checkers=Checkers.only("memory", "fds"),
        )


class TestErrorHandlingLeaks(MemoryLeakTestCase):
    """Test that error handling doesn't leak resources."""

    def test_error_handling_no_leak(self):
        """Test that errors don't cause resource leaks."""
        manager = get_subprocess_manager()

        def create_with_errors():
            for i in range(20):
                self._run_with_error(manager, i)

        self.execute(
            create_with_errors,
            times=10,
            checkers=Checkers.only("memory", "fds"),
        )

    def _run_with_error(self, manager, i):
        """Helper to run a command that is expected to fail."""
        try:
            # This will fail, but shouldn't leak
            manager.run(
                ["nonexistent-command-12345"],
                name=f"error-test-{i}",
                timeout=1.0,
            )
        except Exception:
            # Expected to fail
            pass


# Tracemalloc-based memory leak tests (built-in, no external dependencies)
class TestMemoryLeaksTracemalloc:
    """Test for memory leaks using tracemalloc (Python built-in)."""

    def test_subprocess_manager_no_memory_leak(self):
        """Test that SubprocessManager doesn't leak memory using tracemalloc."""
        import tracemalloc

        tracemalloc.start()

        snapshot1 = tracemalloc.take_snapshot()

        manager = get_subprocess_manager()
        for _ in range(100):
            with manager.popen(["sleep", "0.01"], name="tracemalloc-test"):
                pass

        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        # Check for significant leaks (>1MB)
        total_leaked = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        assert total_leaked < 1_000_000, f"Memory leak detected: {total_leaked} bytes"

        tracemalloc.stop()

    def test_file_operations_no_memory_leak(self):
        """Test that file operations don't leak memory using tracemalloc."""
        import tracemalloc

        tracemalloc.start()

        snapshot1 = tracemalloc.take_snapshot()

        temp_dir = Path(tempfile.mkdtemp())
        try:
            for i in range(100):
                file_path = temp_dir / f"test-{i}.txt"
                with open(file_path, "w") as f:
                    f.write("test")
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        # Check for significant leaks (>500KB)
        total_leaked = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        assert total_leaked < 500_000, f"Memory leak detected: {total_leaked} bytes"

        tracemalloc.stop()


# CPython-style reference leak detection
class TestReferenceLeaks:
    """Test for reference leaks using CPython pattern."""

    def test_subprocess_manager_no_reference_leak(self):
        """Test using CPython's refleak pattern."""
        warmups = 3
        runs = 5

        manager = get_subprocess_manager()

        def my_function():
            for i in range(10):
                with manager.popen(["sleep", "0.01"], name=f"refleak-{i}"):
                    pass

        # Warmup runs
        for _ in range(warmups):
            my_function()
            gc.collect()

        # Measurement runs
        alloc_deltas = []
        fd_deltas = []

        # Try to use fd_count from test.support if available
        try:
            from test.support import os_helper

            fd_count = os_helper.fd_count
        except ImportError:
            # Fallback: use psutil
            try:
                import psutil

                def fd_count():
                    return psutil.Process().num_fds()

            except ImportError:
                # Skip test if no way to count FDs
                pytest.skip("Cannot count file descriptors (no test.support.os_helper or psutil)")

        for _ in range(runs):
            gc.collect()
            alloc_before = sys.getallocatedblocks()
            fd_before = fd_count()

            my_function()

            gc.collect()
            alloc_after = sys.getallocatedblocks()
            fd_after = fd_count()

            alloc_deltas.append(alloc_after - alloc_before)
            fd_deltas.append(fd_after - fd_before)

        # Check for leaks (all deltas should be <= 0 or very small)
        # Allow small variations due to Python's memory management
        max_alloc_delta = max(alloc_deltas) if alloc_deltas else 0
        max_fd_delta = max(fd_deltas) if fd_deltas else 0

        # Allow up to 10 blocks and 2 FDs variation (Python's internal management)
        assert max_alloc_delta <= 10, f"Memory leak detected: {alloc_deltas}"
        assert max_fd_delta <= 2, f"FD leak detected: {fd_deltas}"


# Pytest fixture for automatic leak detection (CPython pattern)
@pytest.fixture(autouse=True)
def check_for_memory_leaks():
    """Check for memory leaks using tracemalloc (CPython pattern).

    Enabled via CHECK_LEAKS=1 environment variable.
    Uses os.environ check for minimal overhead when not needed.
    """
    if os.getenv("CHECK_LEAKS") == "1":
        import tracemalloc

        tracemalloc.start()
        gc.collect()
        current_mem_usage = tracemalloc.get_traced_memory()[0]

        try:
            yield
        finally:
            gc.collect()
            final_mem_usage = tracemalloc.get_traced_memory()[0]
            # Fail if more than 10KB leaked
            leaked = final_mem_usage - current_mem_usage
            assert leaked < 10_000, f"memory was leaked: {leaked} bytes"
    else:
        yield
