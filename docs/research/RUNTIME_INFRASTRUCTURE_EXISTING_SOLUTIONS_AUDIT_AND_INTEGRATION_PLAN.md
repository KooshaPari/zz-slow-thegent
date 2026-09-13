<DONE>
# Runtime Infrastructure: Existing Solutions Audit & Integration Plan

**Date:** 2026-02-17
**Status:** Research & Integration Planning
**Purpose:** Audit existing solutions, identify integration opportunities, and plan adoption of proven libraries

**Last Updated:** 2026-02-17
**Related:** [RUNTIME_INFRASTRUCTURE_RESOURCE_LEAKS_AUDIT_AND_PLAN.md](RUNTIME_INFRASTRUCTURE_RESOURCE_LEAKS_AUDIT_AND_PLAN.md)

---

## Executive Summary

This document audits existing Python libraries and tools for runtime resource management, process lifecycle, and leak detection. It identifies:

1. **Direct Solutions** - Libraries that solve our exact problems
2. **Indirect Support** - Tools that complement our work
3. **Integration Opportunities** - How to adopt existing solutions instead of custom code
4. **Gaps** - Areas where custom implementation is still needed

**Key Finding:** Several mature libraries exist that can replace or enhance our custom implementations, particularly for process monitoring (`psutil`), async subprocess management (`trio`), and leak detection (`psleak`). Additionally, Python's standard library (`tracemalloc`, `resource`) and CPython's test infrastructure provide proven patterns for resource management and leak detection.

**Research Methodology:** This audit combines:

- Web research via DuckDuckGo searches
- Analysis of CPython standard library implementations (`subprocess`, `multiprocessing`, `concurrent.futures`)
- Review of CPython test suite patterns (`test.support.os_helper`, `test.libregrtest.refleak`)
- Evaluation of mature third-party libraries
- Cross-platform compatibility analysis

---

## 1. Existing Solutions Audit

### 1.1 Process & System Monitoring

#### psutil (⭐ 11k stars, actively maintained)

**What it does:**

- Cross-platform process and system monitoring
- Process management (create, terminate, wait)
- Resource monitoring (CPU, memory, disk, network)
- File descriptor tracking
- Process tree navigation

**Key Features:**

```python
import psutil

# Process management
proc = psutil.Process(pid)
proc.terminate()
proc.wait()

# Resource monitoring
proc.memory_info()  # RSS, VMS
proc.num_fds()  # File descriptor count
proc.open_files()  # List open files
proc.connections()  # Network connections

# System-wide
psutil.virtual_memory()
psutil.cpu_percent()
psutil.disk_usage("/")
```

**Integration Opportunities:**

- ✅ **Replace custom resource monitoring** - Use `psutil` instead of custom `resource_monitor.py`
- ✅ **Enhance process registry** - Use `psutil.Process` for better process introspection
- ✅ **File descriptor tracking** - Use `proc.num_fds()` and `proc.open_files()` for leak detection
- ✅ **Process tree management** - Use `proc.children(recursive=True)` for cleanup

**Current Usage:** Not used in codebase (should be added)

**Recommendation:** **HIGH PRIORITY** - Adopt `psutil` for all resource monitoring and process introspection.

---

#### psleak (⭐ 9 stars, experimental)

**What it does:**

- Memory leak detection framework
- Resource leak detection (FDs, handles, threads)
- Test framework for leak detection
- Heap introspection

**Key Features:**

```python
from psleak import MemoryLeakTestCase


class TestLeaks(MemoryLeakTestCase):
    def test_fun(self):
        self.execute(some_function)  # Detects leaks automatically
```

**Integration Opportunities:**

- ✅ **Add leak detection tests** - Use `psleak` for automated leak detection in test suite
- ✅ **Memory leak detection** - Use heap introspection APIs
- ✅ **FD leak detection** - Use built-in FD tracking

**Current Usage:** Not used

**Recommendation:** **MEDIUM PRIORITY** - Add `psleak` to test suite for continuous leak detection.

---

#### fdleaky (⭐ 0 stars, specialized tool)

**What it does:**

- File descriptor leak detection utility
- Monitors file and socket operations
- Reports resources that remain open longer than expected
- Provides stack traces for leak sources
- Interactive debugging (press 'p' to print stack traces)

**Key Features:**

```python
# Run with fdleaky monitoring
python -m fdleaky your_module

# Or as a package
python -m fdleaky your_script.py

# With uvicorn
poetry run python -m fdleaky uvicorn my_app:app
```

**How it works:**

- Patches built-in file and socket operations
- Tracks all open file descriptors
- Monitors for resources that remain open too long (default 180 seconds)
- Provides stack traces to help identify the source of leaks

**Integration Opportunities:**

- ✅ **Development-time leak detection** - Use `fdleaky` during development to catch FD leaks early
- ✅ **Interactive debugging** - Press 'p' in terminal to print stack traces for open FDs
- ✅ **Long-running application monitoring** - Monitor applications for FD leaks over time
- ⚠️ **Runtime overhead** - Patching adds overhead, use for debugging not production

**Current Usage:** Not used

**Recommendation:** **MEDIUM PRIORITY** - Use `fdleaky` for development-time leak detection, complementing `psleak` in tests.

**Comparison with psleak:**

- `fdleaky`: Runtime monitoring, interactive debugging, focuses on FDs
- `psleak`: Test framework, automated detection, covers memory + FDs + threads

---

#### Python Standard Library: `tracemalloc` (Python 3.4+)

**What it does:**

- Built-in memory allocation tracing
- Tracks where memory blocks were allocated
- Computes differences between snapshots to detect leaks
- Provides statistics per filename and line number
- Zero external dependencies

**Key Features:**

```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Take snapshots
snapshot1 = tracemalloc.take_snapshot()
# ... run code ...
snapshot2 = tracemalloc.take_snapshot()

# Compare to find leaks
top_stats = snapshot2.compare_to(snapshot1, "lineno")
for stat in top_stats[:10]:
    print(stat)

# Get current memory usage
current, peak = tracemalloc.get_traced_memory()
```

**Integration Opportunities:**

- ✅ **Memory leak detection** - Use `tracemalloc` for memory leak detection in tests
- ✅ **Memory profiling** - Profile memory usage during development
- ✅ **Zero dependencies** - Built into Python, no external library needed
- ✅ **Test fixture pattern** - Use pytest fixtures with `tracemalloc` (see CPython patterns)

**Current Usage:** Not used

**Recommendation:** **HIGH PRIORITY** - Use `tracemalloc` for memory leak detection in tests, complementing `psleak`.

**CPython Test Pattern:**

```python
# From CPython test suite (pythonspeed.com article)
import tracemalloc
import gc
import pytest


@pytest.fixture(autouse=True)
def check_for_memory_leaks():
    if os.getenv("CHECK_LEAKS") == "1":
        tracemalloc.start()
        gc.collect()
        current_mem_usage = tracemalloc.get_traced_memory()[0]

        try:
            yield
        finally:
            gc.collect()
            final_mem_usage = tracemalloc.get_traced_memory()[0]
            assert final_mem_usage - current_mem_usage < 10_000, "memory was leaked"
            tracemalloc.stop()
```

---

#### memray (⭐ 14.8k stars, Bloomberg)

**What it does:**

- Memory profiler for Python
- Traces every function call (not sampling)
- Handles native C/C++ calls
- Generates flame graphs and reports
- Works with threads and native threads

**Key Features:**

```python
import memray

# Programmatic tracking
with memray.Tracker("output_file.bin"):
    # Your code here
    pass

# CLI usage
memray run my_script.py
memray flamegraph output.bin
```

**Integration Opportunities:**

- ⚠️ **Memory profiling** - Use for deep memory profiling during development
- ⚠️ **Production profiling** - Can profile in production (Linux/macOS only)
- ⚠️ **Native code tracking** - Tracks C extensions (numpy, pandas)
- ❌ **Not for leak detection** - Focused on profiling, not automated leak detection

**Current Usage:** Not used

**Recommendation:** **LOW PRIORITY** - Use for deep memory profiling if needed, but `tracemalloc` + `psleak` are better for leak detection.

---

#### Fil Profiler (⭐ 894 stars, pythonspeed.com)

**What it does:**

- Memory profiler designed for data processing
- Native support for Jupyter
- Finds peak memory usage and allocation sources
- Cross-platform (Linux, macOS)

**Key Features:**

```python
# Automatic profiling
filprofile run my_script.py

# Jupyter integration
%load_ext filprofiler
```

**Integration Opportunities:**

- ⚠️ **Data processing profiling** - If we do heavy data processing
- ⚠️ **Jupyter support** - If we use Jupyter notebooks
- ❌ **Not for leak detection** - Focused on profiling, not automated detection

**Current Usage:** Not used

**Recommendation:** **LOW PRIORITY** - Only if we need specialized data processing memory profiling.

---

#### memory-profiler (⭐ 4.5k stars, unmaintained)

**What it does:**

- Line-by-line memory profiling
- Time-based memory usage reports
- IPython integration
- Process memory tracking

**Key Features:**

```python
from memory_profiler import profile

@profile
def my_func():
    # Profiled function
    pass

# Or via CLI
python -m memory_profiler script.py
```

**Integration Opportunities:**

- ⚠️ **Line-by-line profiling** - If we need detailed line-level memory info
- ⚠️ **Time-based reports** - Memory usage over time
- ❌ **Unmaintained** - Author notes it's no longer actively maintained
- ❌ **Less accurate** - Uses `psutil` but less sophisticated than `memray`

**Current Usage:** Not used

**Recommendation:** **NO PRIORITY** - Unmaintained; prefer `tracemalloc` or `memray`.

---

### 1.2 Subprocess Management

#### Standard Library `subprocess` (Python 3.5+)

**What it does:**

- Process creation and management
- Stream handling (stdout, stderr, stdin)
- Timeout support
- Context manager support (`with Popen(...)`)

**Current Usage:** ✅ Used extensively throughout codebase

**Issues:**

- ❌ No automatic cleanup registry
- ❌ No resource limits enforcement
- ❌ No leak detection
- ❌ PIPE streams must be manually drained

**Recommendation:** Keep using, but wrap with our `SubprocessManager` for lifecycle management.

**CPython Best Practices (from `test_subprocess.py`):**

```python
# Always use context manager
with subprocess.Popen(...) as p:
    # Automatic cleanup
    pass

# Always close pipes explicitly
p = subprocess.Popen(..., stdout=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    # Use pipes
    pass
finally:
    p.stdout.close()
    p.stderr.close()
    p.wait()

# Use DEVNULL for unused streams
subprocess.Popen(..., stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
```

**Key Patterns from CPython:**

- ✅ Always use context manager (`with Popen(...)`)
- ✅ Explicitly close pipes before `wait()`
- ✅ Use `DEVNULL` for unused streams
- ✅ Handle `TimeoutExpired` exceptions
- ✅ Clean up `_active` list (CPython internal, but pattern applies)

---

#### multiprocessing.Pool (Python Standard Library)

**What it does:**

- Process pool management
- Automatic worker lifecycle management
- Task queue and result handling
- Worker process cleanup
- Resource tracking

**Key Features:**

```python
from multiprocessing import Pool

with Pool(processes=4) as pool:
    results = pool.map(func, iterable)
    # Automatic cleanup on exit
```

**CPython Implementation Insights:**

- Uses `_active` list to track processes
- Implements `_cleanup()` to reap zombie processes
- Uses `atexit` and signal handlers for cleanup
- Implements `maxtasksperchild` to limit worker lifetime
- Uses `util.Finalize` for automatic cleanup

**Integration Opportunities:**

- ⚠️ **Process pool pattern** - If we need process pools, use `multiprocessing.Pool`
- ✅ **Cleanup patterns** - Learn from CPython's cleanup implementation
- ✅ **Resource tracking** - See how CPython tracks active processes

**Current Usage:** Not used (we use subprocess directly)

**Recommendation:** **REFERENCE ONLY** - Study CPython's patterns, but we don't need process pools.

---

#### concurrent.futures.ProcessPoolExecutor (Python Standard Library)

**What it does:**

- Higher-level process pool interface
- Future-based API
- Automatic cleanup
- Better error handling than `multiprocessing.Pool`

**Key Features:**

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(func, arg) for arg in args]
    results = [f.result() for f in futures]
```

**CPython Implementation Insights:**

- Uses `multiprocessing` under the hood
- Implements `_ThreadWakeup` for thread communication
- Uses `weakref` for executor cleanup
- Implements `max_tasks_per_child` for worker recycling
- Handles broken process pools gracefully

**Integration Opportunities:**

- ⚠️ **Process pool pattern** - If we need process pools, use `ProcessPoolExecutor`
- ✅ **Cleanup patterns** - Learn from CPython's cleanup implementation
- ✅ **Error handling** - See how CPython handles broken pools

**Current Usage:** Not used

**Recommendation:** **REFERENCE ONLY** - Study CPython's patterns, but we don't need process pools.

---

#### trio (⭐ 7k stars, production-ready)

**What it does:**

- Modern async/await I/O library
- Structured concurrency
- Subprocess management with automatic cleanup
- Resource-aware process handling

**Key Features:**

```python
import trio


async def run_command():
    async with trio.open_process(["cmd", "args"]) as proc:
        # Automatic cleanup on exit
        stdout, stderr = await proc.communicate()
```

**Integration Opportunities:**

- ⚠️ **Async subprocess wrapper** - If we migrate to async, use `trio.open_process`
- ⚠️ **Structured concurrency** - Better process lifecycle management
- ⚠️ **Resource-aware** - Built-in resource limits
- ✅ **Process tree cleanup** - Uses `pidfd_open` on Linux for efficient waiting
- ✅ **Signal handling** - Proper SIGTERM/SIGKILL handling with timeouts

**Trio Implementation Insights:**

- Uses `pidfd_open` on Linux (kernel 5.3+) for efficient process waiting
- Falls back to `waitid` on other platforms
- Implements proper cancellation with `deliver_cancel` callback
- Uses structured concurrency (nurseries) for process lifecycle
- Handles process cleanup in `__exit__` automatically

**Key Pattern from Trio:**

```python
# Trio's process cleanup pattern
async def _posix_deliver_cancel(p: Process) -> None:
    try:
        p.terminate()
        await trio.sleep(5)
        p.kill()  # SIGKILL if SIGTERM ignored
    except OSError:
        pass
```

**Current Usage:** Not used (codebase is synchronous)

**Recommendation:** **LOW PRIORITY** - Consider for future async migration, but not immediate need. Study Trio's cleanup patterns for inspiration.

---

#### pexpect (⭐ 2.8k stars, mature)

**What it does:**

- Interactive program control
- Pseudo-terminal management
- Pattern matching on output
- Process lifecycle management

**Key Features:**

```python
import pexpect

child = pexpect.spawn("command")
child.expect("pattern")
child.sendline("input")
child.close()
```

**Integration Opportunities:**

- ⚠️ **Interactive subprocesses** - If we need interactive control
- ⚠️ **PTY management** - For terminal emulation

**Current Usage:** Not used

**Recommendation:** **LOW PRIORITY** - Only if we need interactive subprocess control.

---

#### sh (⭐ 7.2k stars, mature)

**What it does:**

- Pythonic subprocess interface
- Command execution as functions
- Automatic stream handling

**Key Features:**

```python
from sh import ls, git

# Commands as functions
ls("-l")
git("status")
```

**Integration Opportunities:**

- ⚠️ **Simplified subprocess calls** - More Pythonic interface
- ❌ **Unix-only** - Doesn't work on Windows
- ❌ **No resource management** - Still needs our wrapper

**Current Usage:** Not used

**Recommendation:** **LOW PRIORITY** - Nice-to-have, but doesn't solve our core problems.

---

### 1.3 File System Monitoring

#### watchdog (⭐ 7.2k stars, actively maintained)

**What it does:**

- File system event monitoring
- Cross-platform (Linux, macOS, Windows)
- Efficient event-driven watching
- Process management for watchers

**Key Features:**

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"File modified: {event.src_path}")


observer = Observer()
observer.schedule(Handler(), ".", recursive=True)
observer.start()
```

**Integration Opportunities:**

- ✅ **File watching** - If we need file system monitoring
- ✅ **Resource-aware** - Uses efficient OS APIs (inotify, FSEvents)
- ⚠️ **Not directly related** - Doesn't solve subprocess leaks

**Current Usage:** Not used

**Recommendation:** **LOW PRIORITY** - Only if we add file watching features.

---

#### watchman (⭐ 13.5k stars, Facebook)

**What it does:**

- High-performance file watching service
- Scalable to millions of files
- Process-based architecture
- Used by Facebook/Meta

**Integration Opportunities:**

- ⚠️ **Enterprise file watching** - Overkill for our needs
- ❌ **External service** - Requires separate daemon
- ❌ **Not directly related** - Doesn't solve our problems

**Current Usage:** Not used

**Recommendation:** **NO PRIORITY** - Overkill for our use case.

---

### 1.4 Async File I/O

#### aiofiles (⭐ 3.2k stars, actively maintained)

**What it does:**

- Async file I/O for asyncio
- Thread pool delegation
- Context manager support

**Key Features:**

```python
import aiofiles

async with aiofiles.open("file.txt") as f:
    contents = await f.read()
```

**Integration Opportunities:**

- ⚠️ **Async file operations** - If we migrate to async
- ❌ **Not directly related** - Doesn't solve subprocess leaks

**Current Usage:** Not used

**Recommendation:** **LOW PRIORITY** - Only if we migrate to async.

---

### 1.5 Python Standard Library Patterns

#### `resource` Module (Python Standard Library, Unix-only)

**What it does:**

- System resource limit management
- Process resource usage information
- File descriptor limits (`RLIMIT_NOFILE`)
- Process count limits (`RLIMIT_NPROC`)
- Memory limits (`RLIMIT_AS`, `RLIMIT_RSS`)

**Key Features:**

```python
import resource

# Get limits
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)

# Set limits
resource.setrlimit(resource.RLIMIT_NOFILE, (4096, hard))

# Get usage
usage = resource.getrusage(resource.RUSAGE_SELF)
print(f"Memory: {usage.ru_maxrss} KB")
```

**CPython Test Patterns (`test_resource.py`):**

- Always restore original limits in `finally` blocks
- Check platform support before using limits
- Handle `ValueError` and `OSError` exceptions
- Use `RLIM_INFINITY` for unlimited resources

**Integration Opportunities:**

- ✅ **Already using** - We use `resource` in `resource_limits.py`
- ✅ **Best practices** - Follow CPython's patterns for limit management
- ✅ **Cross-platform** - Handle Windows gracefully (no `resource` module)

**Current Usage:** ✅ Used in `resource_limits.py`

**Recommendation:** **KEEP USING** - Continue using `resource` module, but enhance with `psutil` for monitoring.

---

#### `test.support.os_helper.fd_count()` (CPython Test Infrastructure)

**What it does:**

- Cross-platform file descriptor counting
- Uses `/proc/self/fd` on Linux
- Uses `/dev/fd` on macOS
- Falls back to `os.dup()` scanning on other platforms
- Handles Windows gracefully

**Key Features:**

```python
from test.support.os_helper import fd_count

# Count open file descriptors
count = fd_count()
```

**CPython Implementation:**

```python
def fd_count():
    """Count the number of open file descriptors."""
    if sys.platform.startswith(("linux", "android", "freebsd")):
        fd_path = "/proc/self/fd"
    elif support.is_apple:
        fd_path = "/dev/fd"
    else:
        fd_path = None

    if fd_path is not None:
        names = os.listdir(fd_path)
        return len(names) - 1  # Subtract listdir's own FD

    # Fallback: scan with os.dup()
    count = 0
    for fd in range(MAXFD):
        try:
            fd2 = os.dup(fd)
            os.close(fd2)
            count += 1
        except OSError:
            pass
    return count
```

**Integration Opportunities:**

- ✅ **FD counting** - Use `fd_count()` pattern for leak detection
- ✅ **Cross-platform** - Works on Linux, macOS, Windows
- ✅ **Test infrastructure** - Proven pattern from CPython test suite

**Current Usage:** Not used (we use `psutil.num_fds()`)

**Recommendation:** **REFERENCE** - Good pattern, but `psutil.num_fds()` is better (already cross-platform optimized).

---

#### `test.libregrtest.refleak` (CPython Reference Leak Detection)

**What it does:**

- Reference leak detection framework
- Memory block leak detection
- File descriptor leak detection
- Runs tests multiple times to detect leaks
- Uses `sys.gettotalrefcount()` (debug builds only)

**Key Features:**

```python
# From CPython's refleak.py
def runtest_refleak(test_name, test_func, hunt_refleak, quiet):
    """Run a test multiple times, looking for reference leaks."""
    warmups = hunt_refleak.warmups
    runs = hunt_refleak.runs

    for i in range(warmups + runs):
        support.gc_collect()
        alloc_before = sys.getallocatedblocks()
        rc_before = sys.gettotalrefcount()
        fd_before = os_helper.fd_count()

        result = test_func()

        support.gc_collect()
        alloc_after = sys.getallocatedblocks()
        rc_after = sys.gettotalrefcount()
        fd_after = os_helper.fd_count()

        # Check for leaks
        if alloc_after > alloc_before or fd_after > fd_before:
            # Leak detected
            pass
```

**Integration Opportunities:**

- ✅ **Leak detection pattern** - Use CPython's pattern for leak detection
- ✅ **Multiple runs** - Run tests multiple times to detect leaks
- ✅ **Warmup runs** - Use warmup runs to stabilize caches
- ⚠️ **Debug builds** - Requires Python debug build for `gettotalrefcount()`

**Current Usage:** Not used

**Recommendation:** **REFERENCE** - Study CPython's pattern, but use `psleak` + `tracemalloc` for easier implementation.

---

### 1.6 Best Practices from CPython Implementations

#### Subprocess Cleanup Patterns

**From `subprocess.py` (`_cleanup()` function):**

```python
# CPython's cleanup pattern
_active = []  # List of Popen instances


def _cleanup():
    """Clean up zombie processes."""
    for inst in _active[:]:
        res = inst._internal_poll(_deadstate=sys.maxsize)
        if res is not None:
            try:
                _active.remove(inst)
            except ValueError:
                pass  # Already removed
```

**Key Insights:**

- ✅ Track active processes in a global list
- ✅ Clean up on new `Popen` creation (prevents zombie accumulation)
- ✅ Use `poll()` to check if process exited
- ✅ Handle race conditions gracefully

**Our Implementation:** ✅ We use similar pattern in `ProcessRegistry`

---

#### Process Pool Cleanup Patterns

**From `multiprocessing/pool.py`:**

```python
# CPython's process pool cleanup
def _terminate_pool(cls, taskqueue, inqueue, outqueue, pool, ...):
    # 1. Notify workers to stop
    taskqueue.put(None)

    # 2. Terminate workers
    for p in pool:
        if p.exitcode is None:
            p.terminate()

    # 3. Wait for workers
    for p in pool:
        p.join()

    # 4. Close queues
    inqueue.close()
    outqueue.close()
```

**Key Insights:**

- ✅ Send sentinel to stop workers
- ✅ Terminate before joining
- ✅ Close queues after processes exit
- ✅ Handle broken processes gracefully

**Our Implementation:** ✅ We use similar pattern in `ProcessRegistry.cleanup_all()`

---

#### Concurrent Futures Cleanup Patterns

**From `concurrent/futures/process.py`:**

```python
# CPython's executor cleanup
def _join_executor_internals(self, broken=False):
    # 1. Shutdown workers
    if not broken:
        self.shutdown_workers()

    # 2. Close queues
    self.call_queue.close()
    self.call_queue.join_thread()
    self.thread_wakeup.close()

    # 3. Join processes
    for p in self.processes.values():
        if broken:
            p.terminate()
        p.join()
```

**Key Insights:**

- ✅ Close communication channels first
- ✅ Terminate broken processes
- ✅ Join all processes
- ✅ Use `join_thread()` for queue cleanup

**Our Implementation:** ✅ We use similar pattern in `ProcessRegistry`

---

## 2. Integration Plan

### 2.1 Immediate Integrations (High Priority)

#### 2.1.1 Adopt `psutil` for Resource Monitoring

**Replace:** Custom `resource_monitor.py` implementation

**Benefits:**

- ✅ Mature, well-tested library
- ✅ Cross-platform support
- ✅ Rich process introspection
- ✅ File descriptor tracking
- ✅ Memory monitoring

**Implementation:**

```python
# src/thegent/infra/resource_monitor.py
import psutil
import time
from dataclasses import dataclass
from typing import Optional


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


class ResourceMonitor:
    """Monitor system resources using psutil."""

    def get_stats(self) -> ResourceStats:
        """Get current resource statistics."""
        process = psutil.Process()

        # File descriptors (psutil handles cross-platform)
        try:
            fd_count = process.num_fds()  # psutil method
            open_files = process.open_files()
            connections = process.connections()
            fd_count = len(open_files) + len(connections)
        except (psutil.AccessDenied, AttributeError):
            fd_count = 0

        # FD limit
        try:
            import resource

            fd_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        except Exception:
            fd_limit = 1024

        # Process count
        try:
            process_count = len(psutil.pids())
        except Exception:
            process_count = 0

        # Memory (psutil provides RSS directly)
        try:
            memory_mb = process.memory_info().rss / 1024 / 1024
        except Exception:
            memory_mb = 0

        # CPU (psutil provides percentage)
        try:
            cpu_percent = process.cpu_percent(interval=0.1)
        except Exception:
            cpu_percent = 0

        return ResourceStats(
            fd_count=fd_count,
            fd_limit=fd_limit,
            fd_usage_percent=(fd_count / fd_limit * 100) if fd_limit > 0 else 0,
            process_count=process_count,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            timestamp=time.time(),
        )

    def get_process_info(self, pid: int) -> Optional[dict]:
        """Get detailed process information."""
        try:
            proc = psutil.Process(pid)
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "memory_mb": proc.memory_info().rss / 1024 / 1024,
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "num_fds": proc.num_fds() if hasattr(proc, "num_fds") else 0,
                "open_files": len(proc.open_files()),
                "connections": len(proc.connections()),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
```

**Action Items:**

- [ ] Add `psutil` to `pyproject.toml` dependencies
- [ ] Refactor `resource_monitor.py` to use `psutil`
- [ ] Update `ProcessRegistry` to use `psutil.Process` for introspection
- [ ] Add `psutil`-based process tree cleanup

---

#### 2.1.2 Enhance Process Registry with `psutil`

**Enhance:** Existing `process_registry.py`

**Benefits:**

- ✅ Better process introspection
- ✅ Process tree navigation
- ✅ Cross-platform process management
- ✅ Resource usage per process

**Implementation:**

```python
# src/thegent/infra/process_registry.py (additions)

import psutil
from thegent.infra.process_registry import ProcessHandle, ProcessRegistry


class ProcessHandle:
    """Enhanced with psutil integration."""

    def get_psutil_process(self) -> Optional[psutil.Process]:
        """Get psutil Process object for introspection."""
        try:
            return psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            return None

    def get_resource_usage(self) -> Optional[dict]:
        """Get resource usage using psutil."""
        proc = self.get_psutil_process()
        if not proc:
            return None

        try:
            return {
                "memory_mb": proc.memory_info().rss / 1024 / 1024,
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "num_fds": proc.num_fds() if hasattr(proc, "num_fds") else 0,
                "num_threads": proc.num_threads(),
                "open_files": len(proc.open_files()),
                "connections": len(proc.connections()),
            }
        except (psutil.AccessDenied, AttributeError):
            return None


class ProcessRegistry:
    """Enhanced with psutil integration."""

    def cleanup_process_tree(self, pid: int, timeout: float = 10.0) -> int:
        """Clean up process and all children using psutil."""
        try:
            proc = psutil.Process(pid)
            children = proc.children(recursive=True)

            cleaned = 0
            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                    cleaned += 1
                except psutil.NoSuchProcess:
                    pass

            # Wait for children
            gone, alive = psutil.wait_procs(children, timeout=timeout)

            # Kill any remaining
            for child in alive:
                try:
                    child.kill()
                    cleaned += 1
                except psutil.NoSuchProcess:
                    pass

            # Terminate parent
            try:
                proc.terminate()
                proc.wait(timeout=timeout)
                cleaned += 1
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    proc.kill()
                    proc.wait(timeout=2.0)
                except psutil.NoSuchProcess:
                    pass

            return cleaned
        except psutil.NoSuchProcess:
            return 0
```

**Action Items:**

- [ ] Add `psutil` integration to `ProcessHandle`
- [ ] Add `cleanup_process_tree` method using `psutil`
- [ ] Update cleanup logic to use process trees
- [ ] Add resource usage tracking per process

---

### 2.2 Testing Integrations (Medium Priority)

#### 2.2.1 Add `psleak` for Automated Leak Detection

**Add:** Leak detection tests using `psleak`

**Benefits:**

- ✅ Automated leak detection
- ✅ Memory leak detection
- ✅ FD leak detection
- ✅ Thread leak detection
- ✅ Continuous testing

**Implementation:**

```python
# tests/test_resource_leaks.py

import pytest
from psleak import MemoryLeakTestCase, Checkers
from thegent.infra.subprocess_manager import get_subprocess_manager


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


class TestFileDescriptorLeaks(MemoryLeakTestCase):
    """Test for file descriptor leaks."""

    def test_file_operations_no_leak(self):
        """Test that file operations don't leak FDs."""

        def open_files():
            for i in range(100):
                with open(f"/tmp/test-{i}.txt", "w") as f:
                    f.write("test")

        self.execute(
            open_files,
            times=10,
            checkers=Checkers.only("fds"),
        )
```

**Action Items:**

- [ ] Add `psleak` to test dependencies
- [ ] Create leak detection test suite
- [ ] Add to CI/CD pipeline
- [ ] Set up automated leak detection

---

#### 2.2.2 Add `tracemalloc` for Memory Leak Detection

**Add:** Memory leak detection using Python's built-in `tracemalloc`

**Benefits:**

- ✅ Zero dependencies (built into Python)
- ✅ Detailed allocation tracking
- ✅ Snapshot comparison for leak detection
- ✅ Proven pattern from CPython test suite

**Implementation (CPython Pattern):**

```python
# tests/conftest.py

import os
import gc
import tracemalloc
import pytest

if os.getenv("CHECK_LEAKS") == "1":

    @pytest.fixture(autouse=True)
    def check_for_memory_leaks():
        """Check for memory leaks using tracemalloc."""
        tracemalloc.start()
        gc.collect()
        current_mem_usage = tracemalloc.get_traced_memory()[0]

        try:
            yield
        finally:
            gc.collect()
            final_mem_usage = tracemalloc.get_traced_memory()[0]
            # Fail if more than 10KB leaked
            assert final_mem_usage - current_mem_usage < 10_000, (
                f"memory was leaked: {final_mem_usage - current_mem_usage} bytes"
            )
            tracemalloc.stop()
```

**Advanced Usage (Snapshot Comparison):**

```python
# tests/test_memory_leaks.py

import tracemalloc
import pytest


class TestMemoryLeaks:
    """Test for memory leaks using tracemalloc snapshots."""

    def test_function_no_memory_leak(self):
        """Test that a function doesn't leak memory."""
        tracemalloc.start()

        # Take initial snapshot
        snapshot1 = tracemalloc.take_snapshot()

        # Run function multiple times
        for _ in range(100):
            my_function()

        # Take final snapshot
        snapshot2 = tracemalloc.take_snapshot()

        # Compare snapshots
        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        # Check for significant leaks (>1MB)
        total_leaked = sum(stat.size_diff for stat in top_stats)
        assert total_leaked < 1_000_000, f"Memory leak detected: {total_leaked} bytes"

        tracemalloc.stop()
```

**Action Items:**

- [ ] Add `tracemalloc`-based leak detection fixtures
- [ ] Create memory leak test suite
- [ ] Add snapshot comparison tests
- [ ] Integrate with pytest

---

#### 2.2.3 Add `fdleaky` for Development-Time FD Leak Detection

**Add:** File descriptor leak detection during development

**Benefits:**

- ✅ Interactive debugging (press 'p' for stack traces)
- ✅ Real-time FD monitoring
- ✅ Stack trace for leak sources
- ✅ Long-running application monitoring

**Usage:**

```bash
# Run application with fdleaky
python -m fdleaky thegent serve

# Or with uvicorn
python -m fdleaky uvicorn app:app
```

**Integration:**

- Add to development workflow
- Use for debugging FD leaks
- Complement `psleak` tests with runtime monitoring

**Action Items:**

- [ ] Add `fdleaky` to dev dependencies
- [ ] Document usage in development guide
- [ ] Add to development workflow

---

#### 2.2.4 Implement CPython-Style Leak Detection Pattern

**Add:** Reference leak detection pattern from CPython

**Benefits:**

- ✅ Proven pattern from CPython test suite
- ✅ Detects reference leaks, memory leaks, FD leaks
- ✅ Multiple runs with warmup
- ✅ Comprehensive leak detection

**Implementation:**

```python
# tests/test_refleak.py

import gc
import os
import sys
from test.support import os_helper


def runtest_refleak(test_func, warmups=3, runs=5):
    """Run a test multiple times, looking for resource leaks."""
    # Warmup runs
    for _ in range(warmups):
        test_func()
        gc.collect()

    # Measurement runs
    alloc_deltas = []
    fd_deltas = []

    for _ in range(runs):
        gc.collect()
        alloc_before = sys.getallocatedblocks()
        fd_before = os_helper.fd_count()

        test_func()

        gc.collect()
        alloc_after = sys.getallocatedblocks()
        fd_after = os_helper.fd_count()

        alloc_deltas.append(alloc_after - alloc_before)
        fd_deltas.append(fd_after - fd_before)

    # Check for leaks (all deltas should be <= 0)
    assert all(d <= 0 for d in alloc_deltas), f"Memory leak: {alloc_deltas}"
    assert all(d <= 0 for d in fd_deltas), f"FD leak: {fd_deltas}"
```

**Action Items:**

- [ ] Implement CPython-style leak detection
- [ ] Add to test suite
- [ ] Use for critical resource operations

**Add:** Leak detection tests using `psleak`

**Benefits:**

- ✅ Automated leak detection
- ✅ Memory leak detection
- ✅ FD leak detection
- ✅ Thread leak detection
- ✅ Continuous testing

**Implementation:**

```python
# tests/test_resource_leaks.py

import pytest
from psleak import MemoryLeakTestCase, Checkers
from thegent.infra.subprocess_manager import get_subprocess_manager


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


class TestFileDescriptorLeaks(MemoryLeakTestCase):
    """Test for file descriptor leaks."""

    def test_file_operations_no_leak(self):
        """Test that file operations don't leak FDs."""

        def open_files():
            for i in range(100):
                with open(f"/tmp/test-{i}.txt", "w") as f:
                    f.write("test")

        self.execute(
            open_files,
            times=10,
            checkers=Checkers.only("fds"),
        )
```

**Action Items:**

- [ ] Add `psleak` to test dependencies
- [ ] Create leak detection test suite
- [ ] Add to CI/CD pipeline
- [ ] Set up automated leak detection

---

### 2.3 Future Considerations (Low Priority)

#### 2.3.1 Consider `trio` for Async Migration

**If:** We migrate to async/await

**Benefits:**

- ✅ Structured concurrency
- ✅ Better process lifecycle
- ✅ Resource-aware by design

**Action Items:**

- [ ] Evaluate async migration feasibility
- [ ] If migrating, use `trio.open_process` instead of custom wrapper

---

#### 2.3.2 Consider `watchdog` for File Watching

**If:** We add file system monitoring features

**Benefits:**

- ✅ Efficient event-driven watching
- ✅ Cross-platform support
- ✅ Mature library

**Action Items:**

- [ ] Evaluate need for file watching
- [ ] If needed, integrate `watchdog`

---

### 2.3 Standard Library Integration (High Priority)

#### 2.3.1 Use `test.support.os_helper.fd_count()` Pattern

**Enhance:** Our FD counting to use CPython's proven pattern

**Benefits:**

- ✅ Cross-platform compatibility
- ✅ Proven pattern from CPython
- ✅ Handles edge cases (Windows, macOS, Linux)

**Implementation:**

```python
# src/thegent/infra/resource_monitor.py

import sys
import os
import errno


def fd_count() -> int:
    """Count the number of open file descriptors (CPython pattern)."""
    if sys.platform.startswith(("linux", "android", "freebsd", "emscripten")):
        fd_path = "/proc/self/fd"
    elif sys.platform == "darwin":
        fd_path = "/dev/fd"
    else:
        fd_path = None

    if fd_path is not None:
        try:
            names = os.listdir(fd_path)
            # Subtract one because listdir() internally opens a file descriptor
            return len(names) - 1
        except FileNotFoundError:
            pass

    # Fallback: scan with os.dup()
    MAXFD = 256
    if hasattr(os, "sysconf"):
        try:
            MAXFD = os.sysconf("SC_OPEN_MAX")
        except OSError:
            pass

    count = 0
    for fd in range(MAXFD):
        try:
            fd2 = os.dup(fd)
            os.close(fd2)
            count += 1
        except OSError as e:
            if e.errno != errno.EBADF:
                raise
    return count
```

**Action Items:**

- [ ] Add `fd_count()` helper using CPython pattern
- [ ] Use as fallback when `psutil` unavailable
- [ ] Test cross-platform compatibility

---

#### 2.3.2 Implement CPython-Style Resource Limit Management

**Enhance:** Our `resource_limits.py` to follow CPython patterns

**Benefits:**

- ✅ Proven error handling
- ✅ Cross-platform compatibility
- ✅ Proper limit restoration

**Implementation (from CPython `test_resource.py`):**

```python
# src/thegent/infra/resource_limits.py (enhancements)

import resource
import sys
from contextlib import contextmanager


@contextmanager
def temp_rlimit(resource_type, limits):
    """Temporarily set resource limits (CPython pattern)."""
    try:
        old_limits = resource.getrlimit(resource_type)
    except (OSError, ValueError):
        # Resource not supported on this platform
        yield
        return

    try:
        resource.setrlimit(resource_type, limits)
        yield
    except (OSError, ValueError) as e:
        # Limit setting failed
        raise
    finally:
        # Always restore original limits
        try:
            resource.setrlimit(resource_type, old_limits)
        except (OSError, ValueError):
            # Restoration failed (shouldn't happen, but be safe)
            pass
```

**Action Items:**

- [ ] Add `temp_rlimit` context manager
- [ ] Use for temporary limit changes
- [ ] Ensure proper restoration

---

## 3. Gap Analysis

### 3.1 What Existing Libraries Don't Provide

#### 3.1.1 Process Registry & Lifecycle Management

**Gap:** No library provides a global process registry with automatic cleanup.

**Our Solution:** ✅ `ProcessRegistry` - Custom implementation needed

**Rationale:** This is application-specific infrastructure, not a generic library concern.

---

#### 3.1.2 Resource-Aware Subprocess Wrapper

**Gap:** No library provides resource limits and automatic cleanup for subprocesses.

**Our Solution:** ✅ `SubprocessManager` - Custom implementation needed

**Rationale:** Standard library `subprocess` is low-level; our wrapper adds application-specific lifecycle management.

---

#### 3.1.3 Application-Specific Resource Limits

**Gap:** No library enforces application-specific concurrent process limits.

**Our Solution:** ✅ `SubprocessManager.MAX_CONCURRENT_PROCESSES` - Custom implementation needed

**Rationale:** This is application policy, not a generic library concern.

---

### 3.2 What We Should Use Instead of Custom Code

#### 3.2.1 Resource Monitoring

**Current:** Custom `resource_monitor.py` using `resource` module

**Better:** Use `psutil` for all resource monitoring

**Impact:** ✅ Reduces code, improves cross-platform support, better introspection

**Replacement Strategy:**

- Keep `resource` module for limit setting (still needed)
- Use `psutil` for all monitoring and introspection
- Use `psutil.Process` for per-process resource usage

---

#### 3.2.2 Process Introspection

**Current:** Manual process management with `subprocess.Popen`

**Better:** Use `psutil.Process` for process introspection

**Impact:** ✅ Better process information, process tree navigation, resource usage per process

**Replacement Strategy:**

- Keep `subprocess.Popen` for process creation
- Use `psutil.Process` for introspection and monitoring
- Use `psutil` for process tree navigation

---

#### 3.2.3 Leak Detection

**Current:** Manual leak detection in tests

**Better:** Use `psleak` + `tracemalloc` + `fdleaky` for comprehensive leak detection

**Impact:** ✅ Automated testing, continuous leak detection, better coverage

**Multi-Tool Strategy:**

- **`psleak`**: Automated test framework for memory + FD + thread leaks
- **`tracemalloc`**: Built-in memory allocation tracking (zero dependencies)
- **`fdleaky`**: Development-time FD leak monitoring (interactive debugging)
- **CPython patterns**: Reference leak detection for comprehensive coverage

**Combined Approach:**

```python
# Comprehensive leak detection strategy

# 1. Automated tests with psleak
class TestLeaks(MemoryLeakTestCase):
    def test_no_leak(self):
        self.execute(my_function, checkers=Checkers.all())


# 2. Memory tracking with tracemalloc
@pytest.fixture(autouse=True)
def check_memory():
    tracemalloc.start()
    yield
    # Check for leaks
    tracemalloc.stop()


# 3. Development-time monitoring with fdleaky
# Run: python -m fdleaky my_script.py

# 4. CPython-style reference leak detection
# Use refleak pattern for critical operations
```

---

#### 3.2.4 File Descriptor Counting

**Current:** Using `psutil.num_fds()` (good, but can be enhanced)

**Better:** Use CPython's `fd_count()` pattern as fallback

**Impact:** ✅ More robust FD counting, works even if `psutil` unavailable

**Strategy:**

- Primary: Use `psutil.num_fds()` (fast, cross-platform)
- Fallback: Use CPython's `fd_count()` pattern (no dependencies)
- Use in tests and monitoring code

---

#### 3.2.5 Process Tree Cleanup

**Current:** Manual process tree traversal

**Better:** Use `psutil` for efficient process tree cleanup

**Impact:** ✅ More efficient cleanup, handles edge cases, cross-platform

**Strategy:**

- Use `psutil.Process.children(recursive=True)` for tree traversal
- Use `psutil.wait_procs()` for efficient waiting
- Handle `psutil.NoSuchProcess` exceptions gracefully

---

## 4. Comprehensive Integration Examples

### 4.1 Complete Resource Monitoring with psutil

**Full Implementation:**

```python
# src/thegent/infra/resource_monitor.py (complete)

import logging
import resource
import threading
import time
from dataclasses import dataclass
from typing import Optional, List

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ResourceStats:
    """Resource usage statistics."""

    fd_count: int
    fd_limit: int
    fd_usage_percent: float
    process_count: int
    memory_mb: float
    cpu_percent: float
    num_threads: int
    open_files_count: int
    connections_count: int
    timestamp: float

    def is_critical(self) -> bool:
        """Check if resource usage is critical."""
        return (
            self.fd_usage_percent > 80.0 or self.process_count > 100 or self.memory_mb > 2048  # 2GB
        )


class ResourceMonitor:
    """Monitor system resources using psutil."""

    def __init__(self, check_interval: float = 60.0):
        """Initialize resource monitor."""
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stats_history: List[ResourceStats] = []
        self._max_history = 100

    def get_stats(self) -> ResourceStats:
        """Get current resource statistics using psutil."""
        process = psutil.Process()

        # File descriptors (psutil handles cross-platform)
        try:
            if hasattr(process, "num_fds"):
                fd_count = process.num_fds()
            else:
                # Fallback: count open files and connections
                open_files = process.open_files()
                connections = process.connections()
                fd_count = len(open_files) + len(connections)
        except (psutil.AccessDenied, AttributeError, psutil.NoSuchProcess):
            fd_count = 0

        # FD limit
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            fd_limit = soft
        except (OSError, ValueError, AttributeError):
            fd_limit = 1024

        # Process count (system-wide)
        try:
            process_count = len(psutil.pids())
        except Exception:
            process_count = 0

        # Memory (psutil provides RSS directly)
        try:
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            memory_mb = 0

        # CPU (psutil provides percentage)
        try:
            cpu_percent = process.cpu_percent(interval=0.1)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            cpu_percent = 0

        # Threads
        try:
            num_threads = process.num_threads()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            num_threads = 0

        # Open files
        try:
            open_files = process.open_files()
            open_files_count = len(open_files)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            open_files_count = 0

        # Network connections
        try:
            connections = process.connections()
            connections_count = len(connections)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            connections_count = 0

        return ResourceStats(
            fd_count=fd_count,
            fd_limit=fd_limit,
            fd_usage_percent=(fd_count / fd_limit * 100) if fd_limit > 0 else 0,
            process_count=process_count,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            num_threads=num_threads,
            open_files_count=open_files_count,
            connections_count=connections_count,
            timestamp=time.time(),
        )

    def get_process_info(self, pid: int) -> Optional[dict]:
        """Get detailed process information using psutil."""
        try:
            proc = psutil.Process(pid)
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "memory_mb": proc.memory_info().rss / 1024 / 1024,
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "num_fds": proc.num_fds() if hasattr(proc, "num_fds") else 0,
                "num_threads": proc.num_threads(),
                "open_files": len(proc.open_files()),
                "connections": len(proc.connections()),
                "create_time": proc.create_time(),
                "cmdline": proc.cmdline(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def detect_leaks(self) -> Optional[dict]:
        """Detect potential resource leaks from history."""
        if len(self._stats_history) < 10:
            return None

        recent = self._stats_history[-10:]
        oldest = recent[0]
        newest = recent[-1]

        # Check for increasing trends
        fd_trend = newest.fd_count - oldest.fd_count
        memory_trend = newest.memory_mb - oldest.memory_mb

        if fd_trend > 10 or memory_trend > 100:  # Thresholds
            return {
                "fd_leak": fd_trend > 10,
                "memory_leak": memory_trend > 100,
                "fd_delta": fd_trend,
                "memory_delta_mb": memory_trend,
            }
        return None
```

---

### 4.2 Enhanced Process Registry with psutil

**Full Implementation:**

```python
# src/thegent/infra/process_registry.py (enhancements)

import psutil
from typing import Optional, List, Dict


class ProcessHandle:
    """Enhanced with psutil integration."""

    def get_psutil_process(self) -> Optional[psutil.Process]:
        """Get psutil Process object for introspection."""
        try:
            return psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            return None

    def get_resource_usage(self) -> Optional[Dict]:
        """Get resource usage using psutil."""
        proc = self.get_psutil_process()
        if not proc:
            return None

        try:
            return {
                "memory_mb": proc.memory_info().rss / 1024 / 1024,
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "num_fds": proc.num_fds() if hasattr(proc, "num_fds") else 0,
                "num_threads": proc.num_threads(),
                "open_files": len(proc.open_files()),
                "connections": len(proc.connections()),
                "status": proc.status(),
                "create_time": proc.create_time(),
            }
        except (psutil.AccessDenied, AttributeError, psutil.NoSuchProcess):
            return None

    def get_children(self, recursive: bool = True) -> List[int]:
        """Get child process PIDs using psutil."""
        proc = self.get_psutil_process()
        if not proc:
            return []

        try:
            children = proc.children(recursive=recursive)
            return [child.pid for child in children]
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return []


class ProcessRegistry:
    """Enhanced with psutil integration."""

    def cleanup_process_tree(self, pid: int, timeout: float = 10.0) -> int:
        """Clean up process and all children using psutil (CPython pattern)."""
        try:
            proc = psutil.Process(pid)
            children = proc.children(recursive=True)

            cleaned = 0

            # Terminate children first (CPython pattern)
            for child in children:
                try:
                    child.terminate()
                    cleaned += 1
                except psutil.NoSuchProcess:
                    pass

            # Wait for children (CPython pattern)
            gone, alive = psutil.wait_procs(children, timeout=timeout)

            # Kill any remaining (CPython pattern)
            for child in alive:
                try:
                    child.kill()
                    cleaned += 1
                except psutil.NoSuchProcess:
                    pass

            # Terminate parent
            try:
                proc.terminate()
                proc.wait(timeout=timeout)
                cleaned += 1
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    proc.kill()
                    proc.wait(timeout=2.0)
                except psutil.NoSuchProcess:
                    pass

            return cleaned
        except psutil.NoSuchProcess:
            return 0

    def get_all_resource_usage(self) -> Dict[int, Dict]:
        """Get resource usage for all registered processes."""
        usage = {}
        for handle in self._processes.values():
            if handle.is_alive():
                proc_usage = handle.get_resource_usage()
                if proc_usage:
                    usage[handle.pid] = proc_usage
        return usage
```

---

### 4.3 Comprehensive Leak Detection Test Suite

**Full Implementation:**

```python
# tests/test_resource_leaks.py (complete)

import gc
import os
import pytest
import tracemalloc
from psleak import MemoryLeakTestCase, Checkers
from test.support import os_helper

from thegent.infra.subprocess_manager import get_subprocess_manager
from thegent.infra.process_registry import get_registry
from thegent.infra.resource_monitor import get_resource_monitor


# psleak tests
class TestSubprocessLeaks(MemoryLeakTestCase):
    """Test for subprocess resource leaks using psleak."""

    def test_subprocess_manager_no_leak(self):
        """Test that SubprocessManager doesn't leak resources."""
        manager = get_subprocess_manager()

        def create_processes():
            for i in range(10):
                with manager.popen(["sleep", "0.1"], name=f"test-{i}"):
                    pass

        self.execute(
            create_processes,
            times=50,
            checkers=Checkers.only("memory", "fds"),
        )


class TestFileDescriptorLeaks(MemoryLeakTestCase):
    """Test for file descriptor leaks using psleak."""

    def test_file_operations_no_leak(self):
        """Test that file operations don't leak FDs."""
        import tempfile

        def open_files():
            for i in range(100):
                with tempfile.NamedTemporaryFile(delete=True) as f:
                    f.write(b"test")

        self.execute(
            open_files,
            times=10,
            checkers=Checkers.only("fds"),
        )


class TestProcessRegistryLeaks(MemoryLeakTestCase):
    """Test for ProcessRegistry leaks."""

    def test_registry_cleanup_no_leak(self):
        """Test that ProcessRegistry cleanup doesn't leak."""
        registry = get_registry()

        def create_and_cleanup():
            # Create processes
            handles = []
            for i in range(10):
                proc = subprocess.Popen(["sleep", "0.1"])
                handle = registry.register(proc=proc, name=f"test-{i}")
                handles.append(handle)

            # Cleanup
            registry.cleanup_all()

        self.execute(
            create_and_cleanup,
            times=20,
            checkers=Checkers.all(),
        )


# tracemalloc tests
class TestMemoryLeaksTracemalloc:
    """Test for memory leaks using tracemalloc."""

    def test_function_no_memory_leak(self):
        """Test that a function doesn't leak memory."""
        tracemalloc.start()

        snapshot1 = tracemalloc.take_snapshot()

        # Run function multiple times
        for _ in range(100):
            my_function()

        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        # Check for significant leaks (>1MB)
        total_leaked = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        assert total_leaked < 1_000_000, f"Memory leak detected: {total_leaked} bytes"


# CPython-style reference leak detection
class TestReferenceLeaks:
    """Test for reference leaks using CPython pattern."""

    def test_cpython_style_leak_detection(self):
        """Test using CPython's refleak pattern."""
        warmups = 3
        runs = 5

        # Warmup runs
        for _ in range(warmups):
            my_function()
            gc.collect()

        # Measurement runs
        alloc_deltas = []
        fd_deltas = []

        for _ in range(runs):
            gc.collect()
            alloc_before = sys.getallocatedblocks()
            fd_before = os_helper.fd_count()

            my_function()

            gc.collect()
            alloc_after = sys.getallocatedblocks()
            fd_after = os_helper.fd_count()

            alloc_deltas.append(alloc_after - alloc_before)
            fd_deltas.append(fd_after - fd_before)

        # Check for leaks (all deltas should be <= 0)
        assert all(d <= 0 for d in alloc_deltas), f"Memory leak: {alloc_deltas}"
        assert all(d <= 0 for d in fd_deltas), f"FD leak: {fd_deltas}"


# Pytest fixture for automatic leak detection
@pytest.fixture(autouse=True)
def check_for_memory_leaks():
    """Check for memory leaks using tracemalloc (CPython pattern)."""
    if os.getenv("CHECK_LEAKS") == "1":
        tracemalloc.start()
        gc.collect()
        current_mem_usage = tracemalloc.get_traced_memory()[0]

        try:
            yield
        finally:
            gc.collect()
            final_mem_usage = tracemalloc.get_traced_memory()[0]
            # Fail if more than 10KB leaked
            assert final_mem_usage - current_mem_usage < 10_000, (
                f"memory was leaked: {final_mem_usage - current_mem_usage} bytes"
            )
            tracemalloc.stop()
```

---

## 5. Integration Roadmap

### Phase 1: Immediate (Week 1)

**Priority:** HIGH

1. **Add `psutil` dependency**
   - [ ] Add to `pyproject.toml`
   - [ ] Install and verify

2. **Refactor `resource_monitor.py`**
   - [ ] Replace custom implementation with `psutil`
   - [ ] Use `psutil.Process` for introspection
   - [ ] Use `psutil` for FD tracking

3. **Enhance `process_registry.py`**
   - [ ] Add `psutil.Process` integration
   - [ ] Add process tree cleanup using `psutil`
   - [ ] Add resource usage tracking per process

**Expected Impact:**

- ✅ Better resource monitoring
- ✅ Cross-platform improvements
- ✅ Reduced custom code

---

### Phase 2: Testing (Week 2)

**Priority:** MEDIUM

1. **Add leak detection dependencies**
   - [ ] Add `psleak` to test dependencies
   - [ ] Install and verify
   - [ ] Document `tracemalloc` usage (built-in, no install needed)

2. **Create comprehensive leak detection tests**
   - [ ] Test subprocess manager with `psleak`
   - [ ] Test file operations with `psleak`
   - [ ] Test process registry with `psleak`
   - [ ] Add `tracemalloc`-based memory leak tests
   - [ ] Add CPython-style reference leak tests
   - [ ] Add pytest fixtures for automatic leak detection

3. **Add development-time tools**
   - [ ] Add `fdleaky` to dev dependencies
   - [ ] Document usage in development guide
   - [ ] Add to development workflow

4. **Add to CI/CD**
   - [ ] Run leak detection in CI
   - [ ] Set up alerts for leaks
   - [ ] Run with `CHECK_LEAKS=1` environment variable

**Expected Impact:**

- ✅ Automated leak detection (multiple tools)
- ✅ Continuous testing
- ✅ Early leak detection
- ✅ Development-time monitoring

---

### Phase 3: Optimization (Month 1)

**Priority:** LOW

1. **Evaluate async migration**
   - [ ] Assess feasibility
   - [ ] If migrating, use `trio`

2. **Evaluate file watching**
   - [ ] Assess need
   - [ ] If needed, use `watchdog`

**Expected Impact:**

- ✅ Better architecture if async is needed
- ✅ File watching if needed

---

## 6. Dependency Management

### 6.1 New Dependencies

```toml
# pyproject.toml

[project]
dependencies = [
    # ... existing dependencies ...
    "psutil>=5.9.0",  # Process and system monitoring
]

[project.optional-dependencies]
test = [
    # ... existing test dependencies ...
    "psleak>=0.1.0",  # Leak detection framework
]

[project.optional-dependencies]
dev = [
    # ... existing dev dependencies ...
    "fdleaky>=0.0.11",  # Development-time FD leak detection
]
```

### 6.2 Dependency Justification

| Dependency | Purpose                                    | Justification                                                                      |
| ---------- | ------------------------------------------ | ---------------------------------------------------------------------------------- |
| `psutil`   | Resource monitoring, process introspection | Mature, cross-platform, well-maintained. Replaces custom resource monitoring code. |
| `psleak`   | Leak detection tests                       | Specialized framework for leak detection. Better than manual testing.              |
| `fdleaky`  | Development-time FD leak detection         | Interactive debugging tool for FD leaks. Complements `psleak` tests.               |

### 6.3 Built-in Tools (No Dependencies)

| Tool                                | Purpose                   | Usage                                                    |
| ----------------------------------- | ------------------------- | -------------------------------------------------------- |
| `tracemalloc`                       | Memory leak detection     | Built into Python 3.4+. Zero dependencies. Use in tests. |
| `resource`                          | Resource limit management | Built into Python (Unix). Already using.                 |
| `test.support.os_helper.fd_count()` | FD counting pattern       | CPython pattern. Use as fallback.                        |

---

## 7. Migration Checklist

### Immediate (Do First)

- [ ] Add `psutil` to dependencies
- [ ] Refactor `resource_monitor.py` to use `psutil`
- [ ] Enhance `process_registry.py` with `psutil` integration
- [ ] Update all resource monitoring to use `psutil`
- [ ] Test cross-platform compatibility

### Testing (Do Next)

- [ ] Add `psleak` to test dependencies
- [ ] Create leak detection test suite
- [ ] Add leak detection to CI/CD
- [ ] Set up automated leak alerts

### Future (Do Later)

- [ ] Evaluate async migration with `trio`
- [ ] Evaluate file watching with `watchdog`
- [ ] Consider other libraries as needed

---

## 8. Success Criteria

### Immediate (Week 1)

- ✅ `psutil` integrated and working
- ✅ Resource monitoring using `psutil`
- ✅ Process registry enhanced with `psutil`
- ✅ Cross-platform compatibility verified

### Testing (Week 2)

- ✅ `psleak` integrated and working
- ✅ Leak detection tests passing
- ✅ CI/CD running leak detection
- ✅ No leaks detected

### Long-term (Month 1)

- ✅ All resource monitoring using `psutil`
- ✅ Automated leak detection in place
- ✅ Reduced custom code
- ✅ Better cross-platform support

---

## 9. References

### Libraries

#### High Priority

- **psutil**: https://github.com/giampaolo/psutil — Process and system monitoring
- **psleak**: https://github.com/giampaolo/psleak — Leak detection framework
- **fdleaky**: https://github.com/tofarr/fdleaky — File descriptor leak detection

#### Standard Library

- **tracemalloc**: https://docs.python.org/3/library/tracemalloc.html — Built-in memory tracing
- **resource**: https://docs.python.org/3/library/resource.html — Resource limit management
- **subprocess**: https://docs.python.org/3/library/subprocess.html — Process management
- **multiprocessing**: https://docs.python.org/3/library/multiprocessing.html — Process pools
- **concurrent.futures**: https://docs.python.org/3/library/concurrent.futures.html — Process pool executor

#### Low Priority / Reference

- **trio**: https://github.com/python-trio/trio — Async subprocess management
- **pexpect**: https://github.com/pexpect/pexpect — Interactive subprocess control
- **sh**: https://github.com/amoffat/sh — Pythonic subprocess interface
- **watchdog**: https://github.com/gorakhargosh/watchdog — File system monitoring
- **watchman**: https://github.com/facebook/watchman — High-performance file watching
- **aiofiles**: https://github.com/Tinche/aiofiles — Async file I/O
- **memray**: https://github.com/bloomberg/memray — Memory profiler
- **Fil Profiler**: https://github.com/pythonspeed/filprofiler — Data processing profiler
- **memory-profiler**: https://github.com/pythonprofilers/memory_profiler — Line-by-line profiler (unmaintained)

### Documentation

- **psutil docs**: https://psutil.readthedocs.io/
- **trio docs**: https://trio.readthedocs.io/
- **Python subprocess**: https://docs.python.org/3/library/subprocess.html
- **Python tracemalloc**: https://docs.python.org/3/library/tracemalloc.html
- **Python resource**: https://docs.python.org/3/library/resource.html

### CPython Source Code (Reference Patterns)

- **subprocess.py**: https://github.com/python/cpython/blob/main/Lib/subprocess.py
- **multiprocessing/pool.py**: https://github.com/python/cpython/blob/main/Lib/multiprocessing/pool.py
- **concurrent/futures/process.py**: https://github.com/python/cpython/blob/main/Lib/concurrent/futures/process.py
- **test/subprocess.py**: https://github.com/python/cpython/blob/main/Lib/test/test_subprocess.py
- **test/support/os_helper.py**: https://github.com/python/cpython/blob/main/Lib/test/support/os_helper.py
- **test/libregrtest/refleak.py**: https://github.com/python/cpython/blob/main/Lib/test/libregrtest/refleak.py
- **test/resource.py**: https://github.com/python/cpython/blob/main/Lib/test/test_resource.py
- **test/tracemalloc.py**: https://github.com/python/cpython/blob/main/Lib/test/test_tracemalloc.py

### Articles & Guides

- **pythonspeed.com**: https://pythonspeed.com/articles/identifying-resource-leaks-with-pytest — Catching memory leaks with pytest
- **Stack Overflow**: https://stackoverflow.com/questions/561988/detect-file-handle-leaks-in-python — File handle leak detection discussion

---

## 10. Best Practices Summary

### 10.1 Process Management

**DO:**

- ✅ Always use context managers (`with Popen(...)`)
- ✅ Explicitly close pipes before `wait()`
- ✅ Use `DEVNULL` for unused streams
- ✅ Register processes with `ProcessRegistry`
- ✅ Use `psutil` for process introspection
- ✅ Clean up process trees recursively

**DON'T:**

- ❌ Leave `Popen` objects without cleanup
- ❌ Forget to close pipes
- ❌ Ignore `TimeoutExpired` exceptions
- ❌ Create processes without limits
- ❌ Forget to wait for processes

---

### 10.2 Resource Monitoring

**DO:**

- ✅ Use `psutil` for all resource monitoring
- ✅ Monitor FD count, memory, CPU, processes
- ✅ Track resource usage per process
- ✅ Detect leaks from history
- ✅ Use `tracemalloc` for memory tracking

**DON'T:**

- ❌ Use custom resource monitoring when `psutil` available
- ❌ Ignore resource limits
- ❌ Skip leak detection in tests
- ❌ Forget cross-platform compatibility

---

### 10.3 Leak Detection

**DO:**

- ✅ Use `psleak` for automated test leak detection
- ✅ Use `tracemalloc` for memory leak detection
- ✅ Use `fdleaky` for development-time monitoring
- ✅ Run tests multiple times to detect leaks
- ✅ Use warmup runs to stabilize caches
- ✅ Check for leaks in CI/CD

**DON'T:**

- ❌ Skip leak detection in tests
- ❌ Ignore increasing resource trends
- ❌ Forget to clean up in tests
- ❌ Skip garbage collection in leak tests

---

### 10.4 Cross-Platform Considerations

**DO:**

- ✅ Use `psutil` for cross-platform compatibility
- ✅ Handle Windows gracefully (no `resource` module)
- ✅ Use platform-specific optimizations when available
- ✅ Test on all target platforms

**DON'T:**

- ❌ Assume Unix-only APIs work everywhere
- ❌ Ignore platform differences
- ❌ Skip Windows testing
- ❌ Use platform-specific code without fallbacks

---

## 11. Integration Patterns & Anti-Patterns

### 11.1 Good Patterns

#### Pattern 1: Context Manager for Processes

```python
# GOOD: Automatic cleanup
with subprocess.Popen(...) as proc:
    # Process automatically cleaned up
    pass
```

#### Pattern 2: Registry-Based Tracking

```python
# GOOD: Centralized tracking
registry = get_registry()
with manager.popen(["cmd"], name="task") as proc:
    registry.register(proc=proc, name="task")
    # Automatic cleanup on exit
```

#### Pattern 3: Process Tree Cleanup

```python
# GOOD: Clean up entire tree
proc = psutil.Process(pid)
children = proc.children(recursive=True)
for child in children:
    child.terminate()
psutil.wait_procs(children, timeout=10)
```

#### Pattern 4: Resource Monitoring

```python
# GOOD: Use psutil for monitoring
proc = psutil.Process(pid)
memory_mb = proc.memory_info().rss / 1024 / 1024
fd_count = proc.num_fds()
```

---

### 11.2 Anti-Patterns

#### Anti-Pattern 1: Unmanaged Processes

```python
# BAD: Process not tracked or cleaned up
proc = subprocess.Popen(["cmd"])
# Process may leak if not waited for
```

#### Anti-Pattern 2: Unclosed Pipes

```python
# BAD: Pipes not closed
proc = subprocess.Popen(["cmd"], stdout=subprocess.PIPE)
proc.wait()  # Pipe still open!
```

#### Anti-Pattern 3: Manual Resource Monitoring

```python
# BAD: Custom resource monitoring
import os

fd_count = len(os.listdir("/proc/self/fd"))  # Unix-only!
```

#### Anti-Pattern 4: No Leak Detection

```python
# BAD: No leak detection in tests
def test_function():
    my_function()  # May leak, but no detection
```

---

## 12. Performance Considerations

### 12.1 psutil Performance

**Overhead:**

- `psutil.Process()`: ~0.1ms per call
- `proc.memory_info()`: ~0.5ms per call
- `proc.num_fds()`: ~1ms per call (may scan /proc)
- `proc.children()`: ~2ms per call (process tree traversal)

**Optimization:**

- Cache `psutil.Process` objects (they're lightweight)
- Batch resource queries
- Use `proc.memory_info()` sparingly (expensive)
- Use `proc.num_fds()` only when needed

---

### 12.2 Leak Detection Performance

**Overhead:**

- `psleak`: ~10-20% overhead (runs tests multiple times)
- `tracemalloc`: ~5-10% overhead (tracks all allocations)
- `fdleaky`: ~5-15% overhead (patches file operations)

**Optimization:**

- Run leak detection only in CI/CD or with `CHECK_LEAKS=1`
- Use `tracemalloc` with limited frame count (default 1)
- Use `psleak` with appropriate `times` parameter
- Disable leak detection in production

---

## 13. Security Considerations

### 13.1 Process Management Security

**Risks:**

- Process injection attacks
- Resource exhaustion attacks
- Process tree manipulation

**Mitigations:**

- ✅ Limit concurrent processes (`MAX_CONCURRENT_PROCESSES`)
- ✅ Set resource limits (`RLIMIT_NOFILE`, `RLIMIT_NPROC`)
- ✅ Monitor resource usage
- ✅ Clean up processes promptly
- ✅ Validate process inputs

---

### 13.2 Resource Monitoring Security

**Risks:**

- Information disclosure (process details)
- Resource exhaustion (monitoring overhead)

**Mitigations:**

- ✅ Handle `psutil.AccessDenied` gracefully
- ✅ Limit monitoring frequency
- ✅ Don't log sensitive process information
- ✅ Use monitoring only in development/debugging

---

## See also

- [RUNTIME_INFRASTRUCTURE_RESOURCE_LEAKS_AUDIT_AND_PLAN.md](RUNTIME_INFRASTRUCTURE_RESOURCE_LEAKS_AUDIT_AND_PLAN.md) — Original audit and plan
- [PRODUCTION_PACKAGING_POLISH_OPTIMIZATION_AUDIT_AND_PLAN.md](PRODUCTION_PACKAGING_POLISH_OPTIMIZATION_AUDIT_AND_PLAN.md) — Production packaging plan
- [RUNTIME_INFRASTRUCTURE_SOLUTIONS_SUMMARY.md](RUNTIME_INFRASTRUCTURE_SOLUTIONS_SUMMARY.md) — Executive summary
- [RUNTIME_INFRASTRUCTURE_IMPLEMENTATION_COMPLETE.md](RUNTIME_INFRASTRUCTURE_IMPLEMENTATION_COMPLETE.md) — Implementation status
