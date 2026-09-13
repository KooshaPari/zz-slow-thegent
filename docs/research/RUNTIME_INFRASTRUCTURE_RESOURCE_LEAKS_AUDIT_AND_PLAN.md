<DONE>
# Runtime Infrastructure Resource Leaks & Optimization Audit & Plan

**Date:** 2026-02-17
**Status:** Critical - Runtime issues increasing in frequency
**Issue:** Resource leaks and optimization problems causing `BlockingIOError: [Errno 35] Resource temporarily unavailable`

**Last Updated:** 2026-02-17
**Immediate Fixes Applied:** ✅ Critical file descriptor leak fixed, process registry created

---

## Immediate Fixes Applied (2026-02-17)

### ✅ Fixed Critical File Descriptor Leak

- **File:** `src/thegent/cli.py:7150`
- **Issue:** File handle opened without context manager, never closed
- **Fix:** Added `with open()` context manager and process registration
- **Impact:** Prevents file descriptor exhaustion

### ✅ Created Process Registry Infrastructure

- **File:** `src/thegent/infra/process_registry.py`
- **Purpose:** Track all subprocesses for automatic cleanup
- **Features:**
  - Automatic cleanup on exit (atexit handler)
  - Signal handlers for graceful shutdown
  - Process tracking and statistics
  - Orphaned process cleanup

### ✅ Created Subprocess Manager

- **File:** `src/thegent/infra/subprocess_manager.py`
- **Purpose:** Resource-aware subprocess management
- **Features:**
  - Context manager for automatic cleanup
  - Resource limits (max concurrent processes)
  - Automatic stream draining
  - Timeout handling

### ✅ Updated Critical Code Paths

- **File:** `src/thegent/agents/cliproxy_manager.py`
- **Changes:** All `subprocess.Popen` calls now register processes
- **Impact:** Proxy processes tracked and cleaned up on exit

---

## Executive Summary

Runtime infrastructure is experiencing increasing resource leaks and optimization issues, manifesting as:

- `BlockingIOError: [Errno 35] Resource temporarily unavailable` (file descriptor exhaustion)
- Process leaks (zombie processes)
- Subprocess handles not properly cleaned up
- File handles opened without context managers
- No process registry or lifecycle management
- Missing resource limits and monitoring

**Impact:** System becomes unusable after extended operation, requiring restarts.

---

## 1. Critical Resource Leaks Identified

### 1.1 File Descriptor Leaks

**CRITICAL:** File opened without context manager in `cli.py:7150`

```python
# ❌ LEAK: File handle never closed
subprocess.Popen(["fd", ".", "-H", "--full-path"], stdout=open(index_file, "w"))
```

**Fix:**

```python
# ✅ CORRECT: Use context manager
with open(index_file, "w") as f:
    proc = subprocess.Popen(["fd", ".", "-H", "--full-path"], stdout=f)
    # Track proc for cleanup
```

**Other Potential FD Leaks:**

- `subprocess.Popen` with `PIPE` that aren't drained/closed
- File opens without `with` statements (though grep shows most use context managers)
- Network connections (httpx) that aren't properly closed

### 1.2 Subprocess Process Leaks

**Issue:** `subprocess.Popen` instances created but not tracked or cleaned up.

**Locations:**

- `cliproxy_manager.py:404, 423, 523` - Proxy processes
- `direct_agents.py:404` - Agent execution processes
- `cli_impl.py:105` - Various CLI processes
- `main.py:1941` - Watcher processes
- `cli.py:7150` - Indexing processes

**Problem Pattern:**

```python
# ❌ LEAK: Process not tracked, no cleanup
proc = subprocess.Popen([...], stdout=subprocess.DEVNULL, ...)
# Process continues running, no cleanup on exit
```

**Impact:**

- Zombie processes accumulate
- File descriptors held by processes
- Ports held by dead processes
- System resource exhaustion

### 1.3 Subprocess Output Stream Leaks

**Issue:** `subprocess.Popen` with `stdout=PIPE` or `stderr=PIPE` that aren't drained.

**Location:** `direct_agents.py:404-443`

```python
# ⚠️ RISK: PIPE streams must be drained or closed
proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,  # Must be drained!
    stderr=subprocess.PIPE,  # Must be drained!
    ...
)
# If process writes to stdout/stderr and we don't read, buffer fills
# Process blocks, FD held
```

**Current Code:** Uses threads to drain, but if threads fail or timeout, streams aren't closed.

### 1.4 Network Connection Leaks

**Issue:** httpx clients may not be properly closed in error cases.

**Locations:**

- `cliproxy_manager.py:361, 605` - Uses context managers ✅
- `cliproxy_adapter.py:130, 214, 368` - Uses async context managers ✅
- But error paths may not close properly

### 1.5 Process Registry Missing

**Issue:** No global registry of started processes for cleanup.

**Impact:**

- Can't enumerate all processes to clean up
- No atexit handler to clean up on exit
- Processes survive parent termination

---

## 2. Resource Exhaustion Patterns

### 2.1 File Descriptor Exhaustion

**Symptom:** `BlockingIOError: [Errno 35] Resource temporarily unavailable`

**Causes:**

1. File handles opened without closing
2. Subprocess PIPE streams not drained/closed
3. Network connections not closed
4. Process handles accumulating

**Detection:**

```bash
# Check current FD usage
lsof -p $(pgrep -f thegent) | wc -l

# Check FD limits
ulimit -n

# Monitor FD usage over time
watch -n 1 'lsof -p $(pgrep -f thegent) | wc -l'
```

### 2.2 Process Accumulation

**Symptom:** Many zombie processes, ports held by dead processes

**Causes:**

1. Processes started but not waited on
2. Processes killed but not reaped
3. Orphaned processes from crashes

**Detection:**

```bash
# Find zombie processes
ps aux | grep ' Z '

# Find processes holding ports
lsof -i :8317 -i :3847

# Count thegent processes
ps aux | grep thegent | wc -l
```

### 2.3 Memory Leaks

**Potential Issues:**

- Large data structures not released
- Circular references preventing GC
- Caches growing unbounded

---

## 3. Root Cause Analysis

### 3.1 Missing Resource Management Infrastructure

**Problems:**

1. **No Process Registry** - Can't track all started processes
2. **No Resource Limits** - No limits on concurrent subprocesses
3. **No Cleanup Handlers** - No atexit/signal handlers for cleanup
4. **No Monitoring** - No metrics on resource usage
5. **No Context Managers** - Many resources not using context managers

### 3.2 Inconsistent Cleanup Patterns

**Problems:**

1. Some code uses context managers, some doesn't
2. Error paths don't always clean up
3. Timeout paths may not clean up properly
4. No standardized cleanup pattern

### 3.3 Missing Error Recovery

**Problems:**

1. No retry with backoff for resource exhaustion
2. No automatic cleanup on errors
3. No resource pool management

---

## 4. Comprehensive Solution Plan

### 4.1 Process Registry & Lifecycle Management

**Create:** `src/thegent/infra/process_registry.py`

```python
"""Process registry for tracking and cleaning up subprocesses."""

import atexit
import logging
import signal
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from thegent.thg_platform import Platform, detect_platform


@dataclass
class ProcessHandle:
    """Handle for a tracked subprocess."""

    pid: int
    proc: subprocess.Popen
    name: str
    started_at: float = field(default_factory=time.time)
    cleanup_on_exit: bool = True
    timeout: Optional[float] = None

    def is_alive(self) -> bool:
        """Check if process is still running."""
        return self.proc.poll() is None

    def terminate(self, timeout: float = 5.0) -> bool:
        """Terminate process gracefully."""
        if not self.is_alive():
            return True

        try:
            self.proc.terminate()
            self.proc.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            self.proc.kill()
            try:
                self.proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                return False
            return True
        except Exception as e:
            logging.warning(f"Error terminating process {self.pid}: {e}")
            return False


class ProcessRegistry:
    """Registry for tracking subprocesses with automatic cleanup."""

    def __init__(self):
        self._processes: dict[int, ProcessHandle] = {}
        self._lock = threading.Lock()
        self._cleanup_registered = False
        self._register_cleanup()

    def _register_cleanup(self):
        """Register cleanup handlers."""
        if self._cleanup_registered:
            return

        # Register atexit handler
        atexit.register(self.cleanup_all)

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self._cleanup_registered = True

    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        logging.info(f"Received signal {signum}, cleaning up processes...")
        self.cleanup_all()
        raise SystemExit(1)

    def register(
        self,
        proc: subprocess.Popen,
        name: str,
        cleanup_on_exit: bool = True,
        timeout: Optional[float] = None,
    ) -> ProcessHandle:
        """Register a process for tracking."""
        if proc.poll() is not None:
            # Process already finished
            return ProcessHandle(
                pid=proc.pid,
                proc=proc,
                name=name,
                cleanup_on_exit=False,
            )

        handle = ProcessHandle(
            pid=proc.pid,
            proc=proc,
            name=name,
            cleanup_on_exit=cleanup_on_exit,
            timeout=timeout,
        )

        with self._lock:
            self._processes[proc.pid] = handle

        logging.debug(f"Registered process {proc.pid} ({name})")
        return handle

    def unregister(self, pid: int) -> Optional[ProcessHandle]:
        """Unregister a process."""
        with self._lock:
            return self._processes.pop(pid, None)

    def get(self, pid: int) -> Optional[ProcessHandle]:
        """Get process handle by PID."""
        with self._lock:
            return self._processes.get(pid)

    def list_alive(self) -> list[ProcessHandle]:
        """List all alive processes."""
        with self._lock:
            return [h for h in self._processes.values() if h.is_alive()]

    def cleanup_all(self, timeout: float = 10.0) -> int:
        """Clean up all registered processes."""
        with self._lock:
            processes = list(self._processes.values())

        cleaned = 0
        for handle in processes:
            if handle.cleanup_on_exit and handle.is_alive():
                if handle.terminate(timeout=timeout):
                    cleaned += 1
                    self.unregister(handle.pid)

        logging.info(f"Cleaned up {cleaned} processes")
        return cleaned

    def cleanup_orphaned(self) -> int:
        """Clean up processes that have died but weren't unregistered."""
        with self._lock:
            processes = list(self._processes.values())

        cleaned = 0
        for handle in processes:
            if not handle.is_alive():
                self.unregister(handle.pid)
                cleaned += 1

        return cleaned

    def get_stats(self) -> dict:
        """Get registry statistics."""
        with self._lock:
            processes = list(self._processes.values())

        alive = [h for h in processes if h.is_alive()]
        return {
            "total": len(processes),
            "alive": len(alive),
            "dead": len(processes) - len(alive),
            "processes": [
                {
                    "pid": h.pid,
                    "name": h.name,
                    "alive": h.is_alive(),
                    "uptime": time.time() - h.started_at,
                }
                for h in processes
            ],
        }


# Global registry instance
_registry: Optional[ProcessRegistry] = None


def get_registry() -> ProcessRegistry:
    """Get global process registry."""
    global _registry
    if _registry is None:
        _registry = ProcessRegistry()
    return _registry
```

### 4.2 Resource-Aware Subprocess Wrapper

**Create:** `src/thegent/infra/subprocess_manager.py`

```python
"""Resource-aware subprocess management with automatic cleanup."""

import contextlib
import logging
import subprocess
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Optional

from thegent.infra.process_registry import ProcessHandle, get_registry


class SubprocessManager:
    """Manager for subprocess lifecycle with resource tracking."""

    MAX_CONCURRENT_PROCESSES = 50
    MAX_PROCESS_UPTIME = 3600  # 1 hour

    def __init__(self):
        self.registry = get_registry()
        self._active_count = 0
        self._lock = threading.Lock()

    @contextlib.contextmanager
    def popen(
        self,
        args: list[str],
        name: str,
        **kwargs,
    ) -> Iterator[subprocess.Popen]:
        """Context manager for subprocess.Popen with automatic cleanup."""
        # Check resource limits
        with self._lock:
            if self._active_count >= self.MAX_CONCURRENT_PROCESSES:
                raise RuntimeError(f"Maximum concurrent processes ({self.MAX_CONCURRENT_PROCESSES}) exceeded")
            self._active_count += 1

        proc: Optional[subprocess.Popen] = None
        handle: Optional[ProcessHandle] = None

        try:
            # Ensure stdout/stderr are handled
            if "stdout" not in kwargs:
                kwargs["stdout"] = subprocess.PIPE
            if "stderr" not in kwargs:
                kwargs["stderr"] = subprocess.PIPE

            proc = subprocess.Popen(args, **kwargs)
            handle = self.registry.register(
                proc=proc,
                name=name,
                cleanup_on_exit=True,
            )

            yield proc

        finally:
            with self._lock:
                self._active_count -= 1

            # Cleanup
            if proc is not None:
                # Drain stdout/stderr to prevent blocking
                if proc.stdout:
                    try:
                        proc.stdout.close()
                    except Exception:
                        pass
                if proc.stderr:
                    try:
                        proc.stderr.close()
                    except Exception:
                        pass

                # Wait for process or terminate
                if proc.poll() is None:
                    try:
                        proc.wait(timeout=5.0)
                    except subprocess.TimeoutExpired:
                        proc.terminate()
                        try:
                            proc.wait(timeout=2.0)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.wait()

            if handle:
                self.registry.unregister(handle.pid)

    def run(
        self,
        args: list[str],
        name: str,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        """Run subprocess with resource tracking."""
        with self.popen(args, name, **kwargs) as proc:
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=proc.returncode,
                    stdout=stdout,
                    stderr=stderr,
                )
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                raise subprocess.TimeoutExpired(
                    cmd=args,
                    timeout=timeout,
                    output=stdout,
                    stderr=stderr,
                )


# Global manager instance
_manager: Optional[SubprocessManager] = None


def get_subprocess_manager() -> SubprocessManager:
    """Get global subprocess manager."""
    global _manager
    if _manager is None:
        _manager = SubprocessManager()
    return _manager
```

### 4.3 File Descriptor Monitoring

**Create:** `src/thegent/infra/resource_monitor.py`

```python
"""Resource monitoring and leak detection."""

import logging
import os
import resource
import threading
import time
from dataclasses import dataclass
from typing import Optional

import psutil


@dataclass
class ResourceStats:
    """Resource usage statistics."""

    fd_count: int
    fd_limit: int
    fd_usage_percent: float
    process_count: int
    memory_mb: float
    cpu_percent: float
    timestamp: float

    def is_critical(self) -> bool:
        """Check if resource usage is critical."""
        return (
            self.fd_usage_percent > 80.0 or self.process_count > 100 or self.memory_mb > 2048  # 2GB
        )


class ResourceMonitor:
    """Monitor system resources and detect leaks."""

    def __init__(self, check_interval: float = 60.0):
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stats_history: list[ResourceStats] = []
        self._max_history = 100

    def start(self):
        """Start monitoring thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)

    def _monitor_loop(self):
        """Monitoring loop."""
        while self._running:
            try:
                stats = self.get_stats()
                self._stats_history.append(stats)
                if len(self._stats_history) > self._max_history:
                    self._stats_history.pop(0)

                if stats.is_critical():
                    logging.warning(
                        f"Critical resource usage detected: "
                        f"FDs: {stats.fd_count}/{stats.fd_limit} ({stats.fd_usage_percent:.1f}%), "
                        f"Processes: {stats.process_count}, "
                        f"Memory: {stats.memory_mb:.1f}MB"
                    )

            except Exception as e:
                logging.error(f"Error in resource monitor: {e}")

            time.sleep(self.check_interval)

    def get_stats(self) -> ResourceStats:
        """Get current resource statistics."""
        process = psutil.Process()

        # File descriptors
        try:
            fd_count = len(process.open_files()) + len(process.connections())
        except (psutil.AccessDenied, AttributeError):
            fd_count = 0

        try:
            fd_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        except Exception:
            fd_limit = 1024

        fd_usage_percent = (fd_count / fd_limit * 100) if fd_limit > 0 else 0

        # Process count
        try:
            process_count = len(psutil.pids())
        except Exception:
            process_count = 0

        # Memory
        try:
            memory_mb = process.memory_info().rss / 1024 / 1024
        except Exception:
            memory_mb = 0

        # CPU
        try:
            cpu_percent = process.cpu_percent(interval=0.1)
        except Exception:
            cpu_percent = 0

        return ResourceStats(
            fd_count=fd_count,
            fd_limit=fd_limit,
            fd_usage_percent=fd_usage_percent,
            process_count=process_count,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            timestamp=time.time(),
        )

    def get_history(self) -> list[ResourceStats]:
        """Get resource usage history."""
        return self._stats_history.copy()

    def detect_leak(self) -> Optional[str]:
        """Detect potential resource leaks from history."""
        if len(self._stats_history) < 10:
            return None

        recent = self._stats_history[-10:]

        # Check for increasing FD count
        fd_trend = [s.fd_count for s in recent]
        if all(fd_trend[i] < fd_trend[i + 1] for i in range(len(fd_trend) - 1)):
            return "File descriptor leak detected (increasing trend)"

        # Check for increasing process count
        proc_trend = [s.process_count for s in recent]
        if all(proc_trend[i] < proc_trend[i + 1] for i in range(len(proc_trend) - 1)):
            return "Process leak detected (increasing trend)"

        # Check for increasing memory
        mem_trend = [s.memory_mb for s in recent]
        if all(mem_trend[i] < mem_trend[i + 1] for i in range(len(mem_trend) - 1)):
            return "Memory leak detected (increasing trend)"

        return None


# Global monitor instance
_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """Get global resource monitor."""
    global _monitor
    if _monitor is None:
        _monitor = ResourceMonitor()
    return _monitor
```

### 4.4 Fix Critical Leaks

**Priority 1: Fix file descriptor leak in `cli.py:7150`**

```python
# Before (LEAK):
subprocess.Popen(["fd", ".", "-H", "--full-path"], stdout=open(index_file, "w"))

# After (FIXED):
from thegent.infra.subprocess_manager import get_subprocess_manager

manager = get_subprocess_manager()
with open(index_file, "w") as f:
    manager.run(
        ["fd", ".", "-H", "--full-path"],
        name="file-index",
        stdout=f,
        timeout=30.0,
    )
```

**Priority 2: Fix subprocess cleanup in `cliproxy_manager.py`**

```python
# Before:
proc = subprocess.Popen([...], stdout=subprocess.DEVNULL, ...)
# No cleanup, process leaks

# After:
from thegent.infra.subprocess_manager import get_subprocess_manager

manager = get_subprocess_manager()
with manager.popen([...], name="cliproxy") as proc:
    # Process automatically cleaned up on exit
    ...
```

**Priority 3: Fix PIPE draining in `direct_agents.py`**

```python
# Before:
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# Threads drain, but if they fail, streams leak

# After:
from thegent.infra.subprocess_manager import get_subprocess_manager

manager = get_subprocess_manager()
with manager.popen(cmd, name="agent-run") as proc:
    # Streams automatically drained and closed
    ...
```

### 4.5 Add Resource Limits

**Create:** `src/thegent/infra/resource_limits.py`

```python
"""Resource limits and enforcement."""

import logging
import resource
import sys
from typing import Optional


class ResourceLimits:
    """Manage and enforce resource limits."""

    DEFAULT_FD_LIMIT = 1024
    DEFAULT_PROCESS_LIMIT = 100

    def __init__(self):
        self._original_limits = {}
        self._set_limits()

    def _set_limits(self):
        """Set resource limits."""
        try:
            # File descriptors
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            self._original_limits["nofile"] = (soft, hard)

            # Set higher limit if possible
            new_soft = min(4096, hard)
            if new_soft > soft:
                resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft, hard))
                logging.info(f"Set FD limit to {new_soft}")

            # Process count
            soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)
            self._original_limits["nproc"] = (soft, hard)

            # Set higher limit if possible
            new_soft = min(200, hard)
            if new_soft > soft:
                resource.setrlimit(resource.RLIMIT_NPROC, (new_soft, hard))
                logging.info(f"Set process limit to {new_soft}")

        except (OSError, ValueError) as e:
            logging.warning(f"Could not set resource limits: {e}")

    def get_fd_limit(self) -> int:
        """Get current FD limit."""
        try:
            return resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        except Exception:
            return self.DEFAULT_FD_LIMIT

    def get_process_limit(self) -> int:
        """Get current process limit."""
        try:
            return resource.getrlimit(resource.RLIMIT_NPROC)[0]
        except Exception:
            return self.DEFAULT_PROCESS_LIMIT

    def restore_limits(self):
        """Restore original limits."""
        for limit_name, (soft, hard) in self._original_limits.items():
            try:
                if limit_name == "nofile":
                    resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
                elif limit_name == "nproc":
                    resource.setrlimit(resource.RLIMIT_NPROC, (soft, hard))
            except Exception as e:
                logging.warning(f"Could not restore {limit_name} limit: {e}")


# Global limits instance
_limits: Optional[ResourceLimits] = None


def get_resource_limits() -> ResourceLimits:
    """Get global resource limits manager."""
    global _limits
    if _limits is None:
        _limits = ResourceLimits()
    return _limits
```

### 4.6 Add Cleanup on Startup

**Modify:** `src/thegent/main.py` or initialization code

```python
"""Add cleanup on startup."""

from thegent.infra.process_registry import get_registry
from thegent.infra.resource_monitor import get_resource_monitor


def initialize_runtime_infrastructure():
    """Initialize runtime infrastructure with cleanup."""
    # Clean up orphaned processes
    registry = get_registry()
    cleaned = registry.cleanup_orphaned()
    if cleaned > 0:
        logging.info(f"Cleaned up {cleaned} orphaned processes on startup")

    # Start resource monitoring
    monitor = get_resource_monitor()
    monitor.start()

    # Set resource limits
    from thegent.infra.resource_limits import get_resource_limits

    limits = get_resource_limits()
    logging.info(f"FD limit: {limits.get_fd_limit()}, Process limit: {limits.get_process_limit()}")
```

---

## 5. Implementation Plan

### Phase 1: Critical Fixes (Immediate)

1. **Fix file descriptor leak in `cli.py:7150`**
   - Use context manager for file handle
   - Use subprocess manager for process

2. **Add process registry**
   - Create `process_registry.py`
   - Register all `subprocess.Popen` calls
   - Add atexit cleanup

3. **Fix subprocess cleanup in `cliproxy_manager.py`**
   - Use subprocess manager context manager
   - Ensure processes are tracked and cleaned up

### Phase 2: Infrastructure (Short-term)

4. **Create subprocess manager**
   - Create `subprocess_manager.py`
   - Replace direct `subprocess.Popen` calls
   - Add resource limits

5. **Add resource monitoring**
   - Create `resource_monitor.py`
   - Monitor FD usage, process count, memory
   - Detect leaks

6. **Add resource limits**
   - Create `resource_limits.py`
   - Set appropriate limits
   - Monitor usage

### Phase 3: Comprehensive Migration (Medium-term)

7. **Migrate all subprocess calls**
   - Replace `subprocess.Popen` with manager
   - Replace `subprocess.run` with manager
   - Ensure all processes tracked

8. **Add cleanup handlers**
   - Signal handlers for cleanup
   - Atexit handlers
   - Error recovery

9. **Add monitoring and alerting**
   - Resource usage metrics
   - Leak detection alerts
   - Health checks

### Phase 4: Optimization (Long-term)

10. **Process pooling**
    - Reuse processes where possible
    - Limit concurrent processes
    - Queue management

11. **Resource pooling**
    - Connection pooling
    - File handle pooling
    - Memory management

12. **Advanced monitoring**
    - Real-time dashboards
    - Historical analysis
    - Predictive alerts

---

## 6. Testing Strategy

### 6.1 Leak Detection Tests

```python
"""Test for resource leaks."""

import pytest
import time
from thegent.infra.resource_monitor import get_resource_monitor
from thegent.infra.subprocess_manager import get_subprocess_manager


def test_no_fd_leak():
    """Test that file descriptors don't leak."""
    monitor = get_resource_monitor()
    initial_stats = monitor.get_stats()

    manager = get_subprocess_manager()

    # Create many processes
    for i in range(100):
        with manager.popen(["sleep", "0.1"], name=f"test-{i}"):
            pass

    # Wait for cleanup
    time.sleep(1.0)

    final_stats = monitor.get_stats()

    # FD count should not increase significantly
    assert final_stats.fd_count <= initial_stats.fd_count + 10


def test_no_process_leak():
    """Test that processes don't leak."""
    registry = get_registry()
    initial_count = len(registry.list_alive())

    manager = get_subprocess_manager()

    # Create many processes
    for i in range(50):
        with manager.popen(["sleep", "0.1"], name=f"test-{i}"):
            pass

    # Wait for cleanup
    time.sleep(1.0)

    final_count = len(registry.list_alive())

    # Process count should return to initial
    assert final_count == initial_count


def test_cleanup_on_error():
    """Test that cleanup happens on errors."""
    registry = get_registry()
    initial_count = len(registry.list_alive())

    manager = get_subprocess_manager()

    try:
        with manager.popen(["false"], name="test-error"):
            raise RuntimeError("Test error")
    except RuntimeError:
        pass

    # Wait for cleanup
    time.sleep(0.5)

    final_count = len(registry.list_alive())
    assert final_count == initial_count
```

### 6.2 Stress Tests

```python
"""Stress tests for resource exhaustion."""


def test_concurrent_process_limit():
    """Test that concurrent process limit is enforced."""
    manager = get_subprocess_manager()

    processes = []
    try:
        # Try to exceed limit
        for i in range(manager.MAX_CONCURRENT_PROCESSES + 10):
            try:
                proc = manager.popen(["sleep", "10"], name=f"stress-{i}")
                processes.append(proc)
            except RuntimeError:
                # Should raise when limit exceeded
                assert len(processes) <= manager.MAX_CONCURRENT_PROCESSES
                break
    finally:
        # Cleanup
        for proc in processes:
            try:
                proc.__exit__(None, None, None)
            except Exception:
                pass
```

### 6.3 Integration Tests

```python
"""Integration tests for runtime infrastructure."""


def test_cliproxy_lifecycle():
    """Test cliproxy process lifecycle."""
    from thegent.agents.cliproxy_manager import ensure_proxy_running

    # Start proxy
    url = ensure_proxy_running(settings)

    # Check it's tracked
    registry = get_registry()
    assert len(registry.list_alive()) > 0

    # Cleanup
    registry.cleanup_all()

    # Verify cleanup
    assert len(registry.list_alive()) == 0
```

---

## 7. Monitoring & Observability

### 7.1 Metrics to Track

1. **File Descriptors**
   - Current FD count
   - FD limit
   - FD usage percentage
   - FD leak rate

2. **Processes**
   - Current process count
   - Process limit
   - Process leak rate
   - Zombie process count

3. **Memory**
   - RSS memory usage
   - Memory leak rate
   - Peak memory usage

4. **Subprocesses**
   - Active subprocess count
   - Subprocess lifetime
   - Subprocess failure rate

### 7.2 Health Checks

```python
"""Health check for runtime infrastructure."""


def check_runtime_health() -> dict:
    """Check runtime infrastructure health."""
    monitor = get_resource_monitor()
    stats = monitor.get_stats()
    registry = get_registry()

    health = {
        "status": "healthy",
        "issues": [],
        "stats": stats.__dict__,
        "processes": registry.get_stats(),
    }

    # Check for critical issues
    if stats.is_critical():
        health["status"] = "critical"
        health["issues"].append("Resource usage critical")

    leak = monitor.detect_leak()
    if leak:
        health["status"] = "warning"
        health["issues"].append(leak)

    # Check for orphaned processes
    orphaned = registry.cleanup_orphaned()
    if orphaned > 0:
        health["issues"].append(f"{orphaned} orphaned processes cleaned up")

    return health
```

### 7.3 Logging

**Add structured logging for resource events:**

```python
import structlog

logger = structlog.get_logger()

# Log process creation
logger.info(
    "process_started",
    pid=proc.pid,
    name=name,
    cmd=args,
)

# Log process cleanup
logger.info(
    "process_cleaned_up",
    pid=pid,
    name=name,
    reason=reason,
)

# Log resource warnings
logger.warning(
    "resource_warning",
    fd_count=stats.fd_count,
    fd_limit=stats.fd_limit,
    fd_usage_percent=stats.fd_usage_percent,
)
```

---

## 8. Best Practices

### 8.1 Subprocess Management

**DO:**

- Use `SubprocessManager.popen()` context manager
- Always track processes in registry
- Drain stdout/stderr streams
- Set timeouts
- Handle errors gracefully

**DON'T:**

- Create `subprocess.Popen` without tracking
- Leave PIPE streams undrained
- Ignore process exit codes
- Create processes without limits

### 8.2 File Handling

**DO:**

- Use `with open()` context managers
- Close files explicitly in error cases
- Monitor file descriptor usage
- Set file descriptor limits

**DON'T:**

- Open files without context managers
- Pass file handles to subprocess without closing
- Ignore file descriptor limits

### 8.3 Resource Monitoring

**DO:**

- Monitor resource usage continuously
- Set up alerts for critical usage
- Track resource trends
- Clean up on startup

**DON'T:**

- Ignore resource warnings
- Wait until exhaustion to act
- Skip cleanup on errors

---

## 9. Migration Checklist

### Critical Fixes (Do First)

- [ ] Fix file descriptor leak in `cli.py:7150`
- [ ] Create `process_registry.py`
- [ ] Add atexit cleanup handler
- [ ] Fix subprocess cleanup in `cliproxy_manager.py`
- [ ] Fix PIPE draining in `direct_agents.py`

### Infrastructure (Do Next)

- [ ] Create `subprocess_manager.py`
- [ ] Create `resource_monitor.py`
- [ ] Create `resource_limits.py`
- [ ] Add initialization code
- [ ] Add health check command

### Migration (Do Gradually)

- [ ] Migrate `cliproxy_manager.py` subprocess calls
- [ ] Migrate `direct_agents.py` subprocess calls
- [ ] Migrate `cli_impl.py` subprocess calls
- [ ] Migrate `main.py` subprocess calls
- [ ] Migrate all other subprocess calls

### Testing (Do Continuously)

- [ ] Add leak detection tests
- [ ] Add stress tests
- [ ] Add integration tests
- [ ] Monitor in production
- [ ] Set up alerts

---

## 10. Success Criteria

### Immediate (Week 1)

- ✅ No file descriptor leaks
- ✅ All subprocess.Popen tracked
- ✅ Cleanup on exit works
- ✅ No `BlockingIOError` errors

### Short-term (Month 1)

- ✅ Resource monitoring active
- ✅ Leak detection working
- ✅ All critical subprocess calls migrated
- ✅ Resource limits enforced

### Long-term (Quarter 1)

- ✅ All subprocess calls migrated
- ✅ Comprehensive monitoring
- ✅ Automated leak detection
- ✅ Zero resource-related crashes

---

## 11. References

- Python subprocess documentation: https://docs.python.org/3/library/subprocess.html
- Resource module: https://docs.python.org/3/library/resource.html
- psutil documentation: https://psutil.readthedocs.io/
- File descriptor limits: `ulimit -n`
- Process limits: `ulimit -u`

---

## See also

- [RUNTIME_INFRASTRUCTURE_EXISTING_SOLUTIONS_AUDIT_AND_INTEGRATION_PLAN.md](RUNTIME_INFRASTRUCTURE_EXISTING_SOLUTIONS_AUDIT_AND_INTEGRATION_PLAN.md) — **Existing solutions audit and integration plan** (comprehensive review of libraries and tools)
- [PRODUCTION_PACKAGING_POLISH_OPTIMIZATION_AUDIT_AND_PLAN.md](PRODUCTION_PACKAGING_POLISH_OPTIMIZATION_AUDIT_AND_PLAN.md) — Production packaging plan
- [CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md](CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md) — Package design research
