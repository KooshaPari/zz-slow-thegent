<DONE>
# Runtime Infrastructure Solutions: Executive Summary

**Date:** 2026-02-17
**Status:** Research Complete - Ready for Implementation
**Purpose:** Quick reference for existing solutions audit and integration recommendations

---

## Key Findings

### ✅ High-Value Integrations (Immediate)

1. **`psutil` (⭐ 11k stars)** - **CRITICAL**
   - **Purpose:** Process & system monitoring, resource tracking
   - **Impact:** Replace custom resource monitoring, enhance process introspection
   - **Action:** Add to dependencies, refactor `resource_monitor.py`
   - **Priority:** **HIGH** - Do immediately

2. **`psleak` (⭐ 9 stars, experimental)** - **IMPORTANT**
   - **Purpose:** Automated leak detection framework
   - **Impact:** Continuous leak detection in tests
   - **Action:** Add to test dependencies, create leak detection tests
   - **Priority:** **MEDIUM** - Do next week

### ⚠️ Already Available (No Action Needed)

- **`watchdog`** - Already in dependencies ✅
  - File system monitoring (if needed)

### ❌ Not Needed (Low Priority)

- **`trio`** - Async library (we're synchronous)
- **`pexpect`** - Interactive subprocess control (not needed)
- **`sh`** - Pythonic subprocess (Unix-only, doesn't solve our problems)
- **`watchman`** - Enterprise file watching (overkill)
- **`aiofiles`** - Async file I/O (not needed)

---

## Integration Roadmap

### Phase 1: Immediate (This Week)

**Add `psutil` for Resource Monitoring**

```bash
# Add to pyproject.toml
dependencies = [
    # ... existing ...
    "psutil>=5.9.0",
]
```

**Refactor `resource_monitor.py`:**
- Replace custom `resource` module usage with `psutil`
- Use `psutil.Process` for process introspection
- Use `proc.num_fds()` and `proc.open_files()` for FD tracking

**Enhance `process_registry.py`:**
- Add `psutil.Process` integration to `ProcessHandle`
- Add `cleanup_process_tree()` using `psutil.wait_procs()`
- Add resource usage tracking per process

**Expected Benefits:**
- ✅ Better cross-platform support
- ✅ Reduced custom code (~200 lines)
- ✅ Better process introspection
- ✅ More accurate resource monitoring

---

### Phase 2: Testing (Next Week)

**Add `psleak` for Leak Detection**

```bash
# Add to pyproject.toml test dependencies
[project.optional-dependencies]
test = [
    # ... existing ...
    "psleak>=0.1.0",
]
```

**Create Leak Detection Tests:**
- Test `SubprocessManager` for leaks
- Test file operations for FD leaks
- Test process registry for process leaks

**Add to CI/CD:**
- Run leak detection in CI pipeline
- Set up alerts for detected leaks

**Expected Benefits:**
- ✅ Automated leak detection
- ✅ Continuous testing
- ✅ Early leak detection

---

## What We Keep (Custom Implementation)

### ✅ Process Registry (`process_registry.py`)
**Why:** No library provides global process registry with automatic cleanup
**Status:** Keep and enhance with `psutil`

### ✅ Subprocess Manager (`subprocess_manager.py`)
**Why:** No library provides resource-aware wrapper with limits
**Status:** Keep and enhance with `psutil`

### ✅ Resource Limits (`resource_limits.py`)
**Why:** Application-specific policy, not generic library concern
**Status:** Keep as-is

---

## What We Replace (Use Libraries)

### ❌ Custom Resource Monitoring → `psutil`
**Current:** Custom `resource_monitor.py` using `resource` module
**Better:** Use `psutil` for all resource monitoring
**Impact:** ~200 lines of code removed, better cross-platform support

### ❌ Manual Leak Detection → `psleak`
**Current:** Manual leak detection in tests
**Better:** Use `psleak` framework for automated detection
**Impact:** Better test coverage, continuous leak detection

---

## Quick Start Implementation

### Step 1: Add Dependencies

```bash
# Add psutil
uv add psutil

# Add psleak to test dependencies
uv add --dev psleak
```

### Step 2: Refactor Resource Monitor

```python
# src/thegent/infra/resource_monitor.py
import psutil
import time
from dataclasses import dataclass


@dataclass
class ResourceStats:
    fd_count: int
    fd_limit: int
    fd_usage_percent: float
    process_count: int
    memory_mb: float
    cpu_percent: float
    timestamp: float


class ResourceMonitor:
    def get_stats(self) -> ResourceStats:
        process = psutil.Process()

        # Use psutil for FD tracking
        try:
            fd_count = process.num_fds() if hasattr(process, "num_fds") else 0
            fd_count += len(process.open_files()) + len(process.connections())
        except (psutil.AccessDenied, AttributeError):
            fd_count = 0

        # Use psutil for memory
        memory_mb = process.memory_info().rss / 1024 / 1024

        # Use psutil for CPU
        cpu_percent = process.cpu_percent(interval=0.1)

        # ... rest of implementation
```

### Step 3: Enhance Process Registry

```python
# src/thegent/infra/process_registry.py (additions)
import psutil


class ProcessHandle:
    def get_psutil_process(self) -> Optional[psutil.Process]:
        try:
            return psutil.Process(self.pid)
        except psutil.NoSuchProcess:
            return None


class ProcessRegistry:
    def cleanup_process_tree(self, pid: int, timeout: float = 10.0) -> int:
        """Clean up process and all children using psutil."""
        try:
            proc = psutil.Process(pid)
            children = proc.children(recursive=True)

            # Use psutil.wait_procs for efficient cleanup
            gone, alive = psutil.wait_procs(children, timeout=timeout)

            # Kill remaining
            for child in alive:
                child.kill()

            # Terminate parent
            proc.terminate()
            proc.wait(timeout=timeout)

            return len(gone) + len(alive) + 1
        except psutil.NoSuchProcess:
            return 0
```

### Step 4: Add Leak Detection Tests

```python
# tests/test_resource_leaks.py
from psleak import MemoryLeakTestCase, Checkers
from thegent.infra.subprocess_manager import get_subprocess_manager


class TestSubprocessLeaks(MemoryLeakTestCase):
    def test_subprocess_manager_no_leak(self):
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
```

---

## Success Metrics

### Immediate (Week 1)
- ✅ `psutil` integrated and working
- ✅ Resource monitoring using `psutil`
- ✅ Process registry enhanced with `psutil`
- ✅ ~200 lines of custom code removed

### Testing (Week 2)
- ✅ `psleak` integrated and working
- ✅ Leak detection tests passing
- ✅ CI/CD running leak detection
- ✅ Zero leaks detected

---

## References

- **Full Audit:** [RUNTIME_INFRASTRUCTURE_EXISTING_SOLUTIONS_AUDIT_AND_INTEGRATION_PLAN.md](RUNTIME_INFRASTRUCTURE_EXISTING_SOLUTIONS_AUDIT_AND_INTEGRATION_PLAN.md)
- **Original Plan:** [RUNTIME_INFRASTRUCTURE_RESOURCE_LEAKS_AUDIT_AND_PLAN.md](RUNTIME_INFRASTRUCTURE_RESOURCE_LEAKS_AUDIT_AND_PLAN.md)

---

## Decision Matrix

| Library | Purpose | Priority | Action | Impact |
|---------|---------|----------|--------|--------|
| `psutil` | Resource monitoring | HIGH | Add & integrate | Replace custom code, better monitoring |
| `psleak` | Leak detection | MEDIUM | Add to tests | Automated leak detection |
| `watchdog` | File watching | LOW | Already have | No action needed |
| `trio` | Async I/O | LOW | Skip | Not needed (synchronous) |
| `pexpect` | Interactive subprocess | LOW | Skip | Not needed |
| `sh` | Pythonic subprocess | LOW | Skip | Unix-only, doesn't solve problems |

---

**Next Steps:** See [RUNTIME_INFRASTRUCTURE_EXISTING_SOLUTIONS_AUDIT_AND_INTEGRATION_PLAN.md](RUNTIME_INFRASTRUCTURE_EXISTING_SOLUTIONS_AUDIT_AND_INTEGRATION_PLAN.md) for detailed implementation plan.
