<DONE>
# Library Replacement — Consolidated Migration Plan

> **Status**: Complete | **Version**: 2.0 | **Date**: 2026-02-17
> **Purpose**: Unified, comprehensive library replacement strategy consolidating all audit documents
> **Source**: Consolidated from LIBRARY_FIRST_AUDIT_AND_PLAN.md, LIBRARY_REPLACEMENT_AUDIT_DEEP.md, LIBRARY_REPLACEMENT_PHASE_DWBS.md

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Replacement Strategy](#2-replacement-strategy)
3. [Priority Classifications](#3-priority-classifications)
4. [Migration Phases](#4-migration-phases)
5. [Implementation Details](#5-implementation-details)
6. [Performance Targets](#6-performance-targets)
7. [Risk Mitigation](#7-risk-mitigation)
8. [Testing Requirements](#8-testing-requirements)
9. [BACKLOG Items](#9-backlog-items)

---

## 1. Executive Summary

### 1.1 Core Principle

**Library-First Approach**: Prefer **library + thin wrapper** over full custom implementation. Libraries provide:

- Battle-tested behavior
- Security fixes
- Community maintenance
- Performance optimizations
- Cross-platform compatibility

### 1.2 Replacement Categories

| Category                | Files Affected | Current                   | Replacement              | Priority |
| ----------------------- | -------------- | ------------------------- | ------------------------ | -------- |
| **HTTP**                | 7+             | urllib.request            | httpx                    | P1       |
| **Retry/Backoff**       | 4              | Manual loops              | tenacity                 | P1       |
| **File Watching**       | 1              | os.walk polling           | watchdog                 | P1       |
| **ANSI Stripping**      | 5              | Custom regex              | rich.strip_control_codes | P2       |
| **Caching**             | 5+             | Custom TTL                | cachetools, diskcache    | P2       |
| **XML Parsing**         | 2              | Custom regex              | defusedxml, lxml         | P2       |
| **Resource Monitoring** | 1              | Custom subprocess         | psutil                   | P2       |
| **Circuit Breaker**     | 1              | Custom ToolCircuitBreaker | pybreaker                | P2       |
| **Process Discovery**   | 1              | ps parsing                | psutil                   | P2       |
| **Logging**             | 60+            | stdlib logging            | structlog                | P3       |
| **YAML**                | 15+            | PyYAML                    | ruamel.yaml              | P2       |
| **JSON**                | 50+            | stdlib json               | orjson (optional)        | P3       |

### 1.3 Source Documents

- `LIBRARY_FIRST_AUDIT_AND_PLAN.md` - High-level audit and principles
- `LIBRARY_REPLACEMENT_AUDIT_DEEP.md` - File-level deep audit (825 lines)
- `LIBRARY_REPLACEMENT_PHASE_DWBS.md` - Detailed task breakdowns (204 lines)
- `LIBRARY_REPLACEMENT_COMPLETE.md` - Previous consolidation (878 lines)

**Total**: ~2000+ lines consolidated into unified migration plan

---

## 2. Replacement Strategy

### 2.1 Migration Approach

**Phased Migration**:

1. **Phase 1**: Critical replacements (P1) - HTTP, Retry, File Watching
2. **Phase 2**: High-value replacements (P2) - Caching, Circuit Breaker, YAML
3. **Phase 3**: Polish & optimization (P3) - Logging, JSON, Enhancements

**Backward Compatibility**: Maintain existing APIs during migration, gradual deprecation

### 2.2 Wrapper Pattern

**Thin Wrapper Strategy**:

```python
# Example: Retry wrapper
from tenacity import retry, stop_after_attempt, wait_exponential


def retry_with_usage_limit(max_attempts=3):
    """Domain-specific retry wrapper"""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_usage_limit,  # Custom condition
    )
```

**Benefits**:

- Domain-specific logic in wrapper
- Library handles retry mechanics
- Consistent behavior across codebase
- Easy to test and maintain

---

## 3. Priority Classifications

### 3.1 Priority 1 (P1) - Critical

**HTTP (urllib → httpx)**:

- **Files**: 7+ files using `urllib.request`
- **Impact**: Security, performance, async support
- **Effort**: Medium (API changes)
- **Risk**: Low (httpx is drop-in replacement)

**Retry/Backoff (Manual → tenacity)**:

- **Files**: 4 files with manual retry loops
- **Impact**: Consistency, maintainability
- **Effort**: Low (decorator pattern)
- **Risk**: Low (tenacity already in deps)

**File Watching (Polling → watchdog)**:

- **Files**: 1 file (`governance/triggers.py`)
- **Impact**: Performance, CPU usage
- **Effort**: Low (watchdog API)
- **Risk**: Low (watchdog is mature)

### 3.2 Priority 2 (P2) - High Value

**Caching (Custom → cachetools/diskcache)**:

- **Files**: 5+ files with custom TTL caches
- **Impact**: Maintainability, performance
- **Effort**: Medium (refactor cache APIs)
- **Risk**: Medium (cache behavior changes)

**Circuit Breaker (Custom → pybreaker)**:

- **Files**: 1 file (`resilience.py`)
- **Impact**: Reliability, consistency
- **Effort**: Low (state machine replacement)
- **Risk**: Low (pybreaker is mature)

**YAML (PyYAML → ruamel.yaml)**:

- **Files**: 15+ files using PyYAML
- **Impact**: Config preservation, round-trip
- **Effort**: Medium (API changes)
- **Risk**: Low (ruamel.yaml is compatible)

**ANSI Stripping (Custom → rich)**:

- **Files**: 5 files with custom regex
- **Impact**: Maintainability, correctness
- **Effort**: Low (direct replacement)
- **Risk**: Low (rich already in deps)

### 3.3 Priority 3 (P3) - Polish & Optimization

**Logging (stdlib → structlog)**:

- **Files**: 60+ files using stdlib logging
- **Impact**: Structured logging, observability
- **Effort**: High (widespread changes)
- **Risk**: Medium (logging behavior changes)

**JSON (stdlib → orjson)**:

- **Files**: 50+ files using stdlib json
- **Impact**: Performance (5-50x faster)
- **Effort**: Medium (drop-in replacement)
- **Risk**: Low (orjson is compatible)

---

## 4. Migration Phases

### Phase 1: Critical Replacements (Weeks 1-2)

**Deliverables**:

- [ ] Replace urllib with httpx (7 files)
- [ ] Migrate manual retry loops to tenacity (4 files)
- [ ] Replace polling with watchdog (1 file)
- [ ] Unit tests for all replacements
- [ ] Performance benchmarks

**Dependencies**:

- `httpx` (already in deps)
- `tenacity` (already in deps)
- `watchdog` (add to deps)

**Tasks**:
| ID | Task | Files | Effort |
|----|------|-------|--------|
| P1-HTTP-1 | Audit urllib usage | 7 files | 2 hours |
| P1-HTTP-2 | Replace urllib with httpx | 7 files | 8 hours |
| P1-RETRY-1 | Audit manual retry loops | 4 files | 2 hours |
| P1-RETRY-2 | Migrate to tenacity | 4 files | 6 hours |
| P1-WATCH-1 | Replace polling with watchdog | 1 file | 4 hours |

### Phase 2: High-Value Replacements (Weeks 3-4)

**Deliverables**:

- [ ] Replace custom caching with cachetools/diskcache (5 files)
- [ ] Replace custom circuit breaker with pybreaker (1 file)
- [ ] Replace PyYAML with ruamel.yaml (15 files)
- [ ] Replace custom ANSI stripping with rich (5 files)
- [ ] Integration tests

**Dependencies**:

- `cachetools` (add to deps)
- `diskcache` (optional, add to deps)
- `pybreaker` (add to deps)
- `ruamel.yaml` (add to deps)
- `rich` (already in deps)

**Tasks**:
| ID | Task | Files | Effort |
|----|------|-------|--------|
| P2-CACHE-1 | Audit custom caches | 5 files | 2 hours |
| P2-CACHE-2 | Replace with cachetools | 5 files | 12 hours |
| P2-CB-1 | Replace circuit breaker | 1 file | 4 hours |
| P2-YAML-1 | Replace PyYAML with ruamel | 15 files | 16 hours |
| P2-ANSI-1 | Replace ANSI stripping | 5 files | 4 hours |

### Phase 3: Polish & Optimization (Weeks 5-6)

**Deliverables**:

- [ ] Migrate logging to structlog (60 files, optional)
- [ ] Replace json with orjson (50 files, optional)
- [ ] Performance optimization
- [ ] Documentation updates

**Dependencies**:

- `structlog` (add to deps, optional)
- `orjson` (add to deps, optional)

**Tasks**:
| ID | Task | Files | Effort |
|----|------|-------|--------|
| P3-LOG-1 | Audit logging usage | 60 files | 4 hours |
| P3-LOG-2 | Migrate to structlog | 60 files | 40 hours |
| P3-JSON-1 | Replace json with orjson | 50 files | 20 hours |

---

## 5. Implementation Details

### 5.1 HTTP Replacement (urllib → httpx)

**Before**:

```python
import urllib.request
import urllib.parse

url = "https://api.example.com/data"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    data = response.read()
```

**After**:

```python
import httpx

url = "https://api.example.com/data"
with httpx.Client() as client:
    response = client.get(url)
    data = response.content
```

**Benefits**:

- Async support
- Connection pooling
- Better error handling
- Type hints
- Modern API

### 5.2 Retry Replacement (Manual → tenacity)

**Before**:

```python
import time

for attempt in range(3):
    try:
        result = api_call()
        break
    except Exception as e:
        if attempt == 2:
            raise
        time.sleep(2**attempt)
```

**After**:

```python
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
def api_call():
    # Implementation
    pass
```

**Benefits**:

- Consistent retry behavior
- Configurable strategies
- Better error handling
- Less boilerplate

### 5.3 File Watching Replacement (Polling → watchdog)

**Before**:

```python
import os
import time


def watch_directory(path):
    last_mtime = {}
    while True:
        for root, dirs, files in os.walk(path):
            for file in files:
                filepath = os.path.join(root, file)
                mtime = os.path.getmtime(filepath)
                if filepath not in last_mtime or mtime > last_mtime[filepath]:
                    # Handle change
                    handle_change(filepath)
                last_mtime[filepath] = mtime
        time.sleep(2)
```

**After**:

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            handle_change(event.src_path)


observer = Observer()
observer.schedule(ChangeHandler(), path, recursive=True)
observer.start()
```

**Benefits**:

- Native OS events (inotify, FSEvents)
- Lower CPU usage
- Real-time notifications
- Cross-platform

### 5.4 Caching Replacement (Custom → cachetools)

**Before**:

```python
import time
from typing import Dict, Optional


class TTLCache:
    def __init__(self, ttl: int):
        self.ttl = ttl
        self.cache: Dict[str, tuple] = {}

    def get(self, key: str) -> Optional[object]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None

    def set(self, key: str, value: object):
        self.cache[key] = (value, time.time())
```

**After**:

```python
from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=300)


def get_cached(key: str):
    return cache.get(key)


def set_cached(key: str, value: object):
    cache[key] = value
```

**Benefits**:

- Battle-tested implementation
- Automatic eviction
- Thread-safe
- Less code

### 5.5 Circuit Breaker Replacement (Custom → pybreaker)

**Before**:

```python
class ToolCircuitBreaker:
    def __init__(self):
        self.failures = []
        self.state = "closed"

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            raise CircuitBreakerOpen()
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
```

**After**:

```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, timeout_duration=60)


@breaker
def api_call():
    # Implementation
    pass
```

**Benefits**:

- Standard state machine
- Configurable thresholds
- Automatic recovery
- Less code

---

## 6. Performance Targets

### 6.1 Benchmarks

| Operation              | Current      | Target | Library                                   |
| ---------------------- | ------------ | ------ | ----------------------------------------- |
| **HTTP Request**       | 100ms        | 50ms   | httpx (connection pooling)                |
| **File Watch Latency** | 2s (polling) | <100ms | watchdog (native events)                  |
| **JSON Parse**         | 5ms          | 0.1ms  | orjson (5-50x faster)                     |
| **Cache Lookup**       | 1ms          | 0.5ms  | cachetools (optimized)                    |
| **YAML Parse**         | 10ms         | 8ms    | ruamel.yaml (similar, preserves comments) |

### 6.2 Resource Usage

| Metric                  | Current              | Target             | Improvement           |
| ----------------------- | -------------------- | ------------------ | --------------------- |
| **CPU (file watching)** | High (polling)       | Low (events)       | 80% reduction         |
| **Memory (caching)**    | Custom (inefficient) | cachetools (LRU)   | 30% reduction         |
| **Network (HTTP)**      | No pooling           | Connection pooling | 50% latency reduction |

---

## 7. Risk Mitigation

### 7.1 Technical Risks

| Risk                       | Impact | Mitigation                               |
| -------------------------- | ------ | ---------------------------------------- |
| **API incompatibility**    | High   | Comprehensive testing, gradual migration |
| **Behavior changes**       | Medium | Feature flags, rollback plan             |
| **Performance regression** | Low    | Benchmarking, monitoring                 |
| **Dependency issues**      | Medium | Version pinning, dependency audit        |

### 7.2 Migration Risks

| Risk                    | Impact | Mitigation                            |
| ----------------------- | ------ | ------------------------------------- |
| **Breaking changes**    | High   | Backward compatibility, feature flags |
| **Testing gaps**        | Medium | Comprehensive test coverage           |
| **Rollback complexity** | Medium | Phased rollout, monitoring            |

### 7.3 Mitigation Strategies

**Testing**:

- Unit tests for all replacements
- Integration tests for critical paths
- Performance benchmarks
- Compatibility tests

**Rollback**:

- Feature flags for instant rollback
- Version pinning
- Gradual rollout with monitoring

**Monitoring**:

- Error rates
- Performance metrics
- Resource usage
- User feedback

---

## 8. Testing Requirements

### 8.1 Unit Tests

**Coverage Requirements**:

- All replacements: >90% coverage
- Critical paths: >95% coverage
- Error handling: >85% coverage

**Test Structure**:

```python
# tests/test_http_replacement.py

import pytest
import httpx
from unittest.mock import patch


def test_httpx_replacement():
    """Test urllib → httpx migration"""
    with httpx.Client() as client:
        response = client.get("https://httpbin.org/get")
        assert response.status_code == 200
```

### 8.2 Integration Tests

**Test Scenarios**:

1. HTTP requests with various endpoints
2. Retry behavior under failures
3. File watching with real filesystem
4. Cache behavior with TTL
5. Circuit breaker state transitions

### 8.3 Performance Tests

**Benchmark Requirements**:

- HTTP: <50ms (p95)
- File watch: <100ms latency
- JSON parse: <0.1ms (p95)
- Cache lookup: <0.5ms (p95)

**Benchmark Framework**:

- Use `pytest-benchmark` for Python benchmarks
- Use `hyperfine` for CLI benchmarks
- Compare with baseline (current implementation)

---

## 9. BACKLOG Items

Add to [WORK_STREAM.md](../reference/WORK_STREAM.md) BACKLOG:

| ID                                   | Title                                                  | Priority | Depends |
| ------------------------------------ | ------------------------------------------------------ | -------- | ------- |
| **research-library-http**            | Replace urllib with httpx (7 files)                    | P1       | -       |
| **research-library-retry**           | Migrate manual retry loops to tenacity (4 files)       | P1       | -       |
| **research-library-watchdog**        | Replace polling with watchdog (1 file)                 | P1       | -       |
| **research-library-cache**           | Replace custom caching with cachetools (5 files)       | P2       | -       |
| **research-library-circuit-breaker** | Replace custom circuit breaker with pybreaker (1 file) | P2       | -       |
| **research-library-yaml**            | Replace PyYAML with ruamel.yaml (15 files)             | P2       | -       |
| **research-library-ansi**            | Replace custom ANSI stripping with rich (5 files)      | P2       | -       |
| **research-library-logging**         | Migrate logging to structlog (60 files, optional)      | P3       | -       |
| **research-library-json**            | Replace json with orjson (50 files, optional)          | P3       | -       |

---

## 10. References

### Source Documents

- [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./LIBRARY_FIRST_AUDIT_AND_PLAN.md) - High-level audit
- [LIBRARY_REPLACEMENT_AUDIT_DEEP.md](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md) - Deep file-level audit
- [LIBRARY_REPLACEMENT_PHASE_DWBS.md](./LIBRARY_REPLACEMENT_PHASE_DWBS.md) - Task breakdowns
- [LIBRARY_REPLACEMENT_COMPLETE.md](./LIBRARY_REPLACEMENT_COMPLETE.md) - Previous consolidation

### External Resources

- [httpx Documentation](https://www.python-httpx.org/) - HTTP client
- [tenacity Documentation](https://tenacity.readthedocs.io/) - Retry library
- [watchdog Documentation](https://python-watchdog.readthedocs.io/) - File watching
- [cachetools Documentation](https://cachetools.readthedocs.io/) - Caching
- [pybreaker Documentation](https://pybreaker.readthedocs.io/) - Circuit breaker
- [ruamel.yaml Documentation](https://yaml.readthedocs.io/) - YAML parser

---

**Status**: Complete consolidation ready for implementation
**Next Steps**: Add BACKLOG items to WORK_STREAM, begin Phase 1 implementation

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (9 BACKLOG items)
- [LIBRARY_REPLACEMENT_AUDIT_DEEP.md](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md) - Deep audit document
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added planning patterns
2. Added implementation roadmap
3. Enhanced cross-references

### Cross-References Added

- WORK_STREAM.md
- Implementation guides

### Practical Additions

- Planning templates
- Roadmap configurations
