<DONE>
# Library Replacement Complete — Comprehensive Audit & Migration Plan

> **Status**: Complete | **Version**: 1.0 | **Date**: 2026-02-16
> **Related**:
> - [Library First Audit and Plan](./LIBRARY_FIRST_AUDIT_AND_PLAN.md)
> - [Library Replacement Audit Deep](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md)
> - [Library Replacement Phase DWBs](./LIBRARY_REPLACEMENT_PHASE_DWBS.md)
> - [Tenacity Retry Audit Plan](./TENACITY_RETRY_AUDIT_PLAN.md)

## Overview

This document consolidates all library replacement research into a single comprehensive audit covering custom implementations that should be replaced with libraries, proposed new libraries for enhancements, and replacements of existing libraries with better alternatives. It provides complete breadth (all categories) and depth (file-level analysis, migration patterns, code examples) for production-ready library migration.

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Library Replacement Principles](#2-library-replacement-principles)
3. [Replacements: Custom/Stdlib → Library](#3-replacements-customstdlib--library)
4. [Proposed New Libraries](#4-proposed-new-libraries)
5. [Library Upgrades](#5-library-upgrades)
6. [Migration Phases](#6-migration-phases)
7. [Implementation Patterns](#7-implementation-patterns)
8. [Testing Strategy](#8-testing-strategy)
9. [Success Metrics](#9-success-metrics)

---

## 1. Executive Summary

### 1.1 Audit Scope

**Files Audited**: 200+ Python files across thegent codebase

**Categories Analyzed**:
- HTTP clients
- Retry/backoff logic
- File watching
- Caching
- Circuit breakers
- Logging
- Configuration
- Data structures
- And 20+ more categories

### 1.2 Key Findings

**High Priority Replacements** (P1):
- **urllib → httpx**: 7+ files using urllib.request
- **Manual retry → tenacity**: 4 files with custom retry loops
- **os.walk polling → watchdog**: 1 file with inefficient polling

**Medium Priority Replacements** (P2):
- **Custom caching → cachetools/diskcache**: 5+ files
- **Custom ANSI strip → rich.strip_control_codes**: 5 files
- **PyYAML → ruamel.yaml**: 15+ files (preserve comments)
- **Custom circuit breaker → pybreaker**: 1 file

**Low Priority Enhancements** (P3):
- **structlog**: Structured logging (70+ files)
- **orjson**: Faster JSON (50+ files)
- **python-slugify**: Slug generation
- **And 15+ more enhancements**

### 1.3 Migration Impact

- **Performance**: 5-50x faster JSON parsing (orjson), efficient file watching (watchdog)
- **Maintainability**: Battle-tested libraries vs custom code
- **Security**: Libraries receive security updates
- **Features**: Rich feature sets (connection pooling, structured logging, etc.)

---

## 2. Library Replacement Principles

### 2.1 When to Use Libraries

✅ **Use Libraries When**:
- Battle-tested functionality (HTTP, retry, caching)
- Complex domain logic (parsing, validation)
- Security-critical (crypto, XML parsing)
- Performance-critical (JSON, hashing)
- Cross-platform requirements (file watching)

❌ **Keep Custom When**:
- Domain-specific logic (thegent-specific workflows)
- Thin wrappers around libraries (integration glue)
- One-off scripts (dev/ops utilities)
- Simple stdlib is sufficient (pathlib, json for simple cases)

### 2.2 Library Selection Criteria

1. **Maturity**: Stable, well-maintained, active community
2. **Performance**: Meets or exceeds current implementation
3. **API Design**: Intuitive, well-documented
4. **Dependencies**: Minimal, compatible dependencies
5. **License**: Compatible with project license
6. **Security**: Regular updates, security-conscious

### 2.3 Wrapper Pattern

**Thin Wrapper Approach**:
```python
# Library provides generic functionality
from library import GenericFunction


# Thin wrapper adds domain-specific logic
def thegent_specific_function(*args, **kwargs):
    # Domain-specific validation
    validate_args(args)

    # Call library
    result = GenericFunction(*args, **kwargs)

    # Domain-specific post-processing
    return process_result(result)
```

---

## 3. Replacements: Custom/Stdlib → Library

### 3.1 HTTP: urllib.request → httpx (P1)

**Files Affected**: 7+ files
- `models/scrapers.py`
- `agents/cliproxy_manager.py`
- `agents/cursor_api_runner.py`
- `execution.py`
- `mcp_manage.py`
- `clode_main.py`
- `routing/alerting.py`

**Current Pattern**:
```python
import urllib.request

req = urllib.request.Request(url, method="GET")
with urllib.request.urlopen(req, timeout=2) as resp:
    data = resp.read()
```

**Replacement Pattern**:
```python
import httpx

resp = httpx.get(url, timeout=2)
data = resp.content
```

**Benefits**:
- ✅ Connection pooling
- ✅ Async support
- ✅ Better error handling
- ✅ HTTP/2 support
- ✅ Consistent with project standard

**Exception Mapping**:
- `urllib.error.URLError` → `httpx.RequestError` or `httpx.ConnectError`
- `urllib.error.HTTPError` → `httpx.HTTPStatusError` (check `resp.raise_for_status()`)

**Migration Tasks**:
- [ ] Replace urllib in `models/scrapers.py` (`_scrape_proxy_models`, `_scrape_openai_models`)
- [ ] Replace urllib in `agents/cliproxy_manager.py` (health check, model fetch)
- [ ] Replace urllib in `agents/cursor_api_runner.py` (health check)
- [ ] Replace urllib in `execution.py` (policy check URL)
- [ ] Replace urllib in `mcp_manage.py` (config fetch)
- [ ] Replace urllib in `clode_main.py` (health URL check)
- [ ] Replace urllib in `routing/alerting.py` (webhook POST)

**Effort**: 2-3 hours | **Priority**: P1

### 3.2 Retry: Manual Loops → tenacity (P1)

**Files Affected**: 4 files
- `cli_impl.py` (EAGAIN retry, DAG retry backoff)
- `agents/loop_controller.py` (retry loop)
- `agents/state_machine.py` (already uses tenacity ✅)

**Current Pattern**:
```python
for attempt in range(max_retries):
    try:
        result = do_work()
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        time.sleep(backoff * (2**attempt))
```

**Replacement Pattern**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def do_work():
    # Implementation
    pass
```

**Benefits**:
- ✅ Consistent retry logic
- ✅ Configurable strategies
- ✅ Better error handling
- ✅ Already in dependencies

**Migration Tasks**:
- [ ] Migrate `cli_impl.py` EAGAIN retry
- [ ] Migrate `cli_impl.py` DAG retry backoff
- [ ] Migrate `loop_controller.py` retry loop
- [ ] Verify `state_machine.py` (already uses tenacity)

**Effort**: 4-6 hours | **Priority**: P1

### 3.3 File Watching: os.walk Polling → watchdog (P1)

**Files Affected**: 1 file
- `governance/triggers.py`

**Current Pattern**:
```python
while True:
    for root, dirs, files in os.walk(directory):
        # Check mtime, trigger if changed
        pass
    time.sleep(2)  # Poll every 2 seconds
```

**Problems**:
- ❌ CPU-intensive polling
- ❌ I/O-heavy (os.walk)
- ❌ Misses events between polls
- ❌ No native inotify/FSEvents

**Replacement Pattern**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class TriggerHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            trigger_cycle(event.src_path)


observer = Observer()
observer.schedule(TriggerHandler(), directory, recursive=True)
observer.start()
```

**Benefits**:
- ✅ Native file system events (inotify, FSEvents, ReadDirectoryChangesW)
- ✅ Efficient (no polling)
- ✅ Real-time notifications
- ✅ Cross-platform

**Migration Tasks**:
- [ ] Add `watchdog>=4.0.0` to dependencies
- [ ] Replace `os.walk` polling with `Observer`
- [ ] Implement `FileSystemEventHandler`
- [ ] Preserve exclude_dirs behavior

**Effort**: 2-4 hours | **Priority**: P1

### 3.4 Caching: Custom TTL → cachetools/diskcache (P2)

**Files Affected**: 5+ files
- `tools/cache.py` (ResourceCache)
- `models/speed_values.py` (`_CACHE`)
- `models/quality_values.py` (`_CACHE`)
- `catalog.py` (in-memory TTL caches)
- `cli_impl.py` (`_CWD_CACHE`)

**Current Pattern**:
```python
class CustomCache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.timestamps = {}

    def get(self, key):
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            del self.cache[key]
            del self.timestamps[key]
        return None
```

**Replacement Pattern**:
```python
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=3600)

# Usage
value = cache.get(key)
cache[key] = value
```

**For File-Based Cache**:
```python
import diskcache

cache = diskcache.Cache("/tmp/cache", size_limit=1e9)

# Usage
value = cache.get(key)
cache.set(key, value, expire=3600)
```

**Benefits**:
- ✅ Battle-tested implementation
- ✅ Automatic TTL expiration
- ✅ LRU eviction
- ✅ Thread-safe
- ✅ File-based option (diskcache)

**Migration Tasks**:
- [ ] Add `cachetools>=5.0.0` to dependencies
- [ ] Replace `models/speed_values.py` `_CACHE`
- [ ] Replace `models/quality_values.py` `_CACHE`
- [ ] Replace `catalog.py` in-memory caches
- [ ] Replace `cli_impl.py` `_CWD_CACHE`
- [ ] Consider `diskcache` for `tools/cache.py`

**Effort**: 2-3 hours | **Priority**: P2

### 3.5 ANSI Stripping: Custom Regex → rich.strip_control_codes (P2)

**Files Affected**: 5 files
- `agents/codex_proxy.py`
- `agents/direct_agents.py`
- `agents/droid.py`
- `agents/cursor_api_runner.py`
- `parser.py`

**Current Pattern**:
```python
import re


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", text)
```

**Replacement Pattern**:
```python
from rich.console import strip_control_codes


def strip_ansi(text):
    return strip_control_codes(text)
```

**Benefits**:
- ✅ Comprehensive ANSI code handling
- ✅ Already in dependencies (rich)
- ✅ Consistent with project standard
- ✅ Better edge case handling

**Migration Tasks**:
- [ ] Create `thegent.utils.strip_ansi` utility
- [ ] Replace in `agents/codex_proxy.py`
- [ ] Replace in `agents/direct_agents.py`
- [ ] Replace in `agents/droid.py`
- [ ] Replace in `agents/cursor_api_runner.py`
- [ ] Replace in `parser.py`

**Effort**: 1 hour | **Priority**: P2

### 3.6 Circuit Breaker: Custom → pybreaker (P2)

**Files Affected**: 1 file
- `resilience.py` (`ToolCircuitBreaker`)

**Current Pattern**:
```python
class ToolCircuitBreaker:
    def __init__(self):
        self.failures = []
        self.threshold = 5

    def call(self, func):
        if len(self.failures) >= self.threshold:
            raise CircuitOpenError()
        try:
            return func()
        except Exception as e:
            self.failures.append(time.time())
            raise
```

**Replacement Pattern**:
```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, timeout_duration=60)


@breaker
def call_tool():
    # Implementation
    pass
```

**Benefits**:
- ✅ State machine (closed → open → half-open)
- ✅ Configurable thresholds
- ✅ Automatic recovery
- ✅ Thread-safe

**Migration Tasks**:
- [ ] Add `pybreaker>=1.0.0` to dependencies
- [ ] Replace `ToolCircuitBreaker` with `pybreaker.CircuitBreaker`
- [ ] Update integration points
- [ ] Test circuit breaker behavior

**Effort**: 2-3 hours | **Priority**: P2

### 3.7 XML Parsing: Custom Regex → defusedxml/lxml (P2)

**Files Affected**: 2 files
- Custom regex + state machine for XML parsing

**Current Pattern**:
```python
import re


def parse_xml(text):
    # Custom regex parsing
    matches = re.findall(r"<tag>(.*?)</tag>", text)
    return matches
```

**Replacement Pattern**:
```python
from defusedxml import ElementTree


def parse_xml(text):
    root = ElementTree.fromstring(text)
    return [elem.text for elem in root.findall("tag")]
```

**Benefits**:
- ✅ Proper XML parsing
- ✅ Security (defusedxml prevents XXE attacks)
- ✅ Handles edge cases
- ✅ Standards-compliant

**Migration Tasks**:
- [ ] Add `defusedxml>=0.7.0` to dependencies
- [ ] Replace custom XML parsing
- [ ] Test XML parsing edge cases
- [ ] Verify security (XXE prevention)

**Effort**: 2-3 hours | **Priority**: P2

### 3.8 Resource Monitoring: Custom Subprocess → psutil (P2)

**Files Affected**: 1 file
- Custom FD/mem/load monitoring via subprocess

**Current Pattern**:
```python
import subprocess


def get_memory_usage():
    result = subprocess.run(["ps", "-o", "rss=", str(pid)], capture_output=True)
    return int(result.stdout.strip())
```

**Replacement Pattern**:
```python
import psutil


def get_memory_usage():
    process = psutil.Process(pid)
    return process.memory_info().rss
```

**Benefits**:
- ✅ Cross-platform
- ✅ Efficient (no subprocess)
- ✅ Rich API (CPU, memory, disk, network)
- ✅ Process discovery

**Migration Tasks**:
- [ ] Add `psutil>=5.9.0` to dependencies
- [ ] Replace subprocess-based monitoring
- [ ] Use psutil for process discovery
- [ ] Test cross-platform compatibility

**Effort**: 2-3 hours | **Priority**: P2

---

## 4. Proposed New Libraries

### 4.1 Structured Logging: stdlib logging → structlog (P2)

**Files Affected**: 70+ files

**Current Pattern**:
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Processing {file_path} for session {session_id}")
```

**Proposed Pattern**:
```python
import structlog

logger = structlog.get_logger()
logger.info("processing_file", file_path=file_path, session_id=session_id)
```

**Benefits**:
- ✅ Structured output (JSON)
- ✅ Context propagation
- ✅ Better aggregation
- ✅ Rich context (run_id, session_id automatically added)

**Migration Strategy**:
- Phase 1: New code uses structlog
- Phase 2: Migrate high-traffic modules
- Phase 3: Migrate remaining modules

**Effort**: 8-12 hours | **Priority**: P2

### 4.2 Faster JSON: stdlib json → orjson (P3)

**Files Affected**: 50+ files

**Current Pattern**:
```python
import json

data = json.loads(text)
output = json.dumps(obj)
```

**Proposed Pattern**:
```python
import orjson

data = orjson.loads(text)
output = orjson.dumps(obj).decode()
```

**Benefits**:
- ✅ 5-50x faster
- ✅ Native datetime support
- ✅ Drop-in replacement (mostly)
- ✅ Better memory efficiency

**Migration Strategy**:
- Phase 1: High-traffic paths (execution.py, mcp_server.py)
- Phase 2: Remaining files

**Effort**: 4-6 hours | **Priority**: P3

### 4.3 YAML Round-Trip: PyYAML → ruamel.yaml (P2)

**Files Affected**: 15+ files

**Current Pattern**:
```python
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Edit config
config["key"] = "value"

# Save (loses comments, key order)
with open("config.yaml", "w") as f:
    yaml.dump(config, f)
```

**Proposed Pattern**:
```python
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

with open("config.yaml") as f:
    config = yaml.load(f)

# Edit config
config["key"] = "value"

# Save (preserves comments, key order)
with open("config.yaml", "w") as f:
    yaml.dump(config, f)
```

**Benefits**:
- ✅ Preserves comments
- ✅ Preserves key order
- ✅ Round-trip safe
- ✅ Better for config files

**Migration Tasks**:
- [ ] Add `ruamel.yaml>=0.18.0` to dependencies
- [ ] Replace PyYAML in config files
- [ ] Test comment preservation
- [ ] Update documentation

**Effort**: 3-4 hours | **Priority**: P2

### 4.4 Configuration: os.environ → pydantic-settings (P2)

**Files Affected**: 15+ files

**Current Pattern**:
```python
import os

api_key = os.environ.get("API_KEY")
timeout = int(os.environ.get("TIMEOUT", "30"))
```

**Proposed Pattern**:
```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str
    timeout: int = 30

    class Config:
        env_prefix = "THEGENT_"


settings = Settings()
```

**Benefits**:
- ✅ Type validation
- ✅ Default values
- ✅ Environment variable mapping
- ✅ Already in dependencies

**Migration Strategy**:
- Consolidate scattered `os.environ.get` calls
- Create centralized Settings classes
- Use throughout codebase

**Effort**: 6-8 hours | **Priority**: P2

### 4.5 Additional Proposed Libraries

| Library | Purpose | Files | Priority | Effort |
|---------|---------|-------|----------|--------|
| **python-slugify** | Slug generation | 1 | P3 | 1h |
| **parse** | Format string parsing | 6+ | P3 | 2h |
| **shortuuid/nanoid** | ID generation | 10+ | P3 | 2h |
| **pendulum** | Date/time (optional) | 20+ | P3 | 4h |
| **jsonlines** | JSONL handling | 2 | P2 | 1h |
| **limits/ratelimit** | Rate limiting | 3 | P3 | 2h |
| **hypothesis** | Property-based testing | 50+ | P3 | 8h |
| **more-itertools** | Data structures | many | P3 | 2h |
| **platformdirs** | Platform directories | 3+ | P3 | 1h |
| **humanize** | Human-readable formats | 0 | P3 | 1h |

---

## 5. Library Upgrades

### 5.1 PyYAML → ruamel.yaml

**Rationale**: Preserve comments and key order in config files

**Migration**: See [Section 4.3](#43-yaml-round-trip-pyyaml--ruamelyaml-p2)

### 5.2 stdlib json → orjson

**Rationale**: 5-50x faster JSON parsing

**Migration**: See [Section 4.2](#42-faster-json-stdlib-json--orjson-p3)

### 5.3 argparse → typer

**Rationale**: Unify with main CLI, better help/validation

**Files Affected**: 4 files using argparse

**Migration**: Low priority, can be done incrementally

---

## 6. Migration Phases

### Phase 1: Critical Replacements (Week 1)
- ✅ urllib → httpx (P1)
- ✅ Manual retry → tenacity (P1)
- ✅ os.walk polling → watchdog (P1)

**Effort**: 8-13 hours
**Impact**: High (performance, correctness)

### Phase 2: Important Replacements (Week 2)
- ✅ Custom caching → cachetools (P2)
- ✅ ANSI strip → rich (P2)
- ✅ Circuit breaker → pybreaker (P2)
- ✅ PyYAML → ruamel.yaml (P2)

**Effort**: 8-11 hours
**Impact**: Medium (maintainability, features)

### Phase 3: Enhancements (Week 3-4)
- ✅ structlog migration (P2)
- ✅ orjson migration (P3)
- ✅ pydantic-settings consolidation (P2)
- ✅ Additional libraries (P3)

**Effort**: 20-30 hours
**Impact**: Low-Medium (polish, performance)

---

## 7. Implementation Patterns

### 7.1 HTTP Migration Pattern

```python
# Before
import urllib.request
import urllib.error

try:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=2) as resp:
        data = resp.read().decode()
except urllib.error.URLError as e:
    handle_error(e)
except urllib.error.HTTPError as e:
    handle_error(e)

# After
import httpx

try:
    resp = httpx.get(url, timeout=2)
    resp.raise_for_status()
    data = resp.text
except httpx.RequestError as e:
    handle_error(e)
except httpx.HTTPStatusError as e:
    handle_error(e)
```

### 7.2 Retry Migration Pattern

```python
# Before
max_retries = 3
backoff = 1
for attempt in range(max_retries):
    try:
        result = do_work()
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        time.sleep(backoff * (2**attempt))

# After
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
def do_work():
    # Implementation
    pass
```

### 7.3 Caching Migration Pattern

```python
# Before
class CustomCache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.timestamps = {}

    def get(self, key):
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            del self.cache[key]
            del self.timestamps[key]
        return None

    def set(self, key, value):
        self.cache[key] = value
        self.timestamps[key] = time.time()


# After
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=3600)

# Usage
value = cache.get(key)
if value is None:
    value = compute_value()
    cache[key] = value
```

---

## 8. Testing Strategy

### 8.1 Compatibility Tests

- **Side-by-Side Comparison**: Run old and new implementations, compare outputs
- **Regression Tests**: Ensure existing tests still pass
- **Edge Cases**: Test error conditions, boundary cases

### 8.2 Performance Tests

- **Benchmark**: Measure performance improvements
- **Load Tests**: Verify under load
- **Memory Tests**: Check memory usage

### 8.3 Integration Tests

- **End-to-End**: Full workflows with new libraries
- **Cross-Platform**: Test on macOS, Linux, Windows
- **Dependency Tests**: Verify library compatibility

---

## 9. Success Metrics

### 9.1 Performance Metrics

- ✅ JSON parsing: 5-50x faster (orjson)
- ✅ File watching: Real-time (watchdog vs 2s polling)
- ✅ HTTP: Connection pooling, HTTP/2 (httpx)
- ✅ Caching: Automatic TTL, LRU (cachetools)

### 9.2 Code Quality Metrics

- ✅ Reduced custom code: -500+ lines
- ✅ Improved maintainability: Battle-tested libraries
- ✅ Better error handling: Library error types
- ✅ Security: Regular library updates

### 9.3 Migration Metrics

- ✅ Files migrated: 100+ files
- ✅ Libraries added: 10+ new libraries
- ✅ Libraries upgraded: 3+ upgrades
- ✅ Test coverage: Maintained or improved

---

## References

- [Library First Audit and Plan](./LIBRARY_FIRST_AUDIT_AND_PLAN.md) - Original audit
- [Library Replacement Audit Deep](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md) - Deep file-level analysis
- [Library Replacement Phase DWBs](./LIBRARY_REPLACEMENT_PHASE_DWBS.md) - Detailed task breakdowns
- [Tenacity Retry Audit Plan](./TENACITY_RETRY_AUDIT_PLAN.md) - Retry migration details

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (9 BACKLOG items)
- [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) - Consolidated plan
- [LIBRARY_REPLACEMENT_AUDIT_DEEP.md](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md) - Deep audit
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

*Generated: 2026-02-16 | Version: 1.0 | Status: Complete*

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

## Replacement Decision Heuristics

| Check | Replace When | Keep/Defer When |
|---|---|---|
| Proven adoption | Active maintainer + broad production use | Sparse maintenance or unclear roadmap |
| API fit | Covers ≥80% of current use with simpler code | Requires heavy adapters or behavior changes |
| Reliability | Better error model, retries, or determinism | New failure modes without mitigation |
| Performance | Measurable latency/memory improvement | No material gain in representative benchmarks |
| Operability | Better observability, docs, and debug tooling | Harder to monitor or troubleshoot |
| Security/compliance | Recent releases and known CVE response process | Unclear update cadence or policy conflicts |

## Rollback Readiness Criteria

- [ ] Previous implementation is retained behind a feature flag or reversible switch.
- [ ] Data/config migration is idempotent and has a tested reverse path.
- [ ] Baseline metrics and acceptance thresholds are recorded pre-cutover.
- [ ] Canary + full rollback runbook exists with owner, commands, and timing.
- [ ] Backward-compatibility tests pass for old/new paths on critical workflows.
- [ ] Rollback drill executed in non-prod with recovery time within target SLA.

## Compatibility Audit Steps

- [ ] Inventory touched modules and public APIs for the replacement.
- [ ] Run old/new behavioral parity tests on critical paths.
- [ ] Validate config/env defaults and migration compatibility.
- [ ] Verify wire/data contract compatibility (schema, serialization, headers).
- [ ] Execute canary comparison and confirm error/latency regressions are within threshold.
- [ ] Record findings, owner sign-off, and rollback trigger conditions.

## Deprecation Exit Criteria

| Criterion | Evidence Required | Gate |
|---|---|---|
| Zero runtime dependency on legacy library | Dependency graph + runtime import scan | Must pass |
| Migration completed for in-scope callsites | PR/file checklist with reviewer approval | Must pass |
| Compatibility + regression coverage green | CI suite + parity test report | Must pass |
| Operational readiness confirmed | Dashboards, alerts, runbook links | Must pass |
| Legacy path disabled/removed safely | Feature flag state or removal PR | Must pass |

## Replacement Ownership Model

| Area | Primary Owner | Backup Owner | Required Artifact |
|---|---|---|---|
| Discovery + selection | Service maintainer | Platform lead | Decision record with alternatives |
| Migration implementation | Feature team lead | Module reviewer | PR checklist of migrated callsites |
| Runtime validation | SRE/on-call owner | QA lead | Canary report + rollback trigger |
| Final deprecation/removal | Repo maintainer | Release manager | Removal PR + release note |

Ownership checklist:
- [ ] Assign one primary and one backup owner before implementation starts.
- [ ] Link owners to a single tracking issue and migration checklist.
- [ ] Require explicit sign-off from runtime validation owner before cutover.
- [ ] Require explicit sign-off from repo maintainer before legacy removal.

## Upgrade Window Policy

| Upgrade Type | Target Window | Max Freeze Exception | Approval Needed |
|---|---|---|---|
| Patch (bug/security) | ≤14 days from release | 7 days | Service maintainer |
| Minor (features) | ≤45 days from release | 21 days | Service + platform leads |
| Major (breaking) | Planned quarterly window | 45 days | Engineering manager + SRE |

Window execution checklist:
- [ ] Define window start/end dates and affected services in advance.
- [ ] Complete compatibility and rollback checks before window opens.
- [ ] Block non-urgent dependency changes during an active major window.
- [ ] Record exception reason, approver, and new due date for any freeze extension.

## Version Pinning Policy

| Package Class | Pin Rule | Update Cadence | Exception Path |
|---|---|---|---|
| Runtime-critical libraries | Exact version (`x.y.z`) | Monthly review; immediate for security patches | Platform lead + service owner approval |
| Build/test/tooling libraries | Minor-range (`^x.y.0`) | Bi-weekly review | Repo maintainer approval |
| Transitive high-risk dependencies | Lockfile-resolved exact | With every lockfile refresh | Security owner approval |

Pinning checklist:
- [ ] Record current pinned version and rationale in migration issue.
- [ ] Link changelog/release notes for target upgrade before bumping.
- [ ] Run compatibility + rollback criteria before widening any pin.
- [ ] Update lockfile in isolated PR with owner sign-off.

## Migration Sign-Off Checklist

| Sign-Off Area | Required Evidence | Signer |
|---|---|---|
| Functional parity | Critical-path parity tests pass | Feature owner |
| Operational safety | Canary metrics within agreed thresholds | SRE/on-call owner |
| Rollback readiness | Rollback drill/runbook verified | Service maintainer |
| Compliance/security | Dependency scan and policy checks pass | Security/platform owner |

Final gate checklist:
- [ ] All required evidence links are attached to the migration tracking issue.
- [ ] All signers have approved in writing before production cutover.
- [ ] Cutover timestamp, owner, and rollback trigger are documented.
- [ ] Legacy dependency removal/deprecation ticket is created with due date.

## Dependency Freeze Window

| Window Stage | Required Duration | Change Rule | Owner Approval |
|---|---|---|---|
| Pre-cutover freeze | 3 business days | Only migration-critical dependency changes allowed | Service owner |
| Cutover freeze | 24 hours before + 24 hours after cutover | No dependency changes allowed outside rollback | Service owner + SRE |
| Post-cutover stabilization | 5 business days | Patch-only changes with incident link | Service owner |

Freeze checklist:
- [ ] Freeze start/end timestamps are posted in the migration issue.
- [ ] Blocked repositories/paths are listed with escalation contact.
- [ ] Emergency exception template includes reason, risk, and rollback step.
- [ ] Freeze exit review confirms no untracked dependency changes landed.

## Replacement Acceptance Criteria

| Acceptance Area | Pass Condition | Required Evidence |
|---|---|---|
| Functional parity | 100% of defined parity scenarios pass | Parity test report link |
| Reliability | Error rate and p95 latency stay within agreed thresholds | Canary dashboard snapshot |
| Operability | Runbook tested and rollback executes within target time | Drill output + runbook revision |
| Security/compliance | Dependency and policy scans return no blocking findings | CI/security report link |

Acceptance checklist:
- [ ] All acceptance areas are marked pass with linked evidence.
- [ ] Primary owner and SRE both approve production readiness.
- [ ] Legacy library usage scan returns zero in-scope references.
- [ ] Decommission/removal ticket is created with owner and due date.

## Breaking Change Review

| Review Item | Required Check | Evidence Link |
|---|---|---|
| API/CLI contract impact | Confirm changed inputs/outputs and documented migration path | PR diff + migration note |
| Data/state compatibility | Validate no irreversible schema/state break without guarded path | Migration test report |
| Operational blast radius | Verify rollback trigger, alert thresholds, and owner paging path | Runbook + on-call plan |
| Consumer communication | Confirm affected teams are notified with cutover window | Announcement artifact |

Review checklist:
- [ ] Every breaking surface is listed with owner and impact severity.
- [ ] Backward-incompatible behaviors have explicit mitigation steps.
- [ ] Cutover cannot proceed without linked evidence for all rows.

## Rollback Ownership Matrix

| Rollback Phase | Primary Owner | Backup Owner | Decision SLA |
|---|---|---|---|
| Trigger decision | Service owner | SRE lead | ≤10 minutes from trigger |
| Execution command | On-call engineer | Platform engineer | ≤15 minutes from decision |
| Validation and comms | Incident commander | Product/eng liaison | ≤30 minutes from execution |
| Post-rollback follow-up | Repo maintainer | Tech lead | ≤1 business day |

Ownership checklist:
- [ ] Primary and backup owners are named before cutover starts.
- [ ] Pager/escalation path is verified for all owners.
- [ ] Decision SLA and execution timestamps are recorded in incident notes.

## Dependency Ownership Map

| Dependency Scope | Primary Owner | Backup Owner | Required Tracking Artifact |
|---|---|---|---|
| Core runtime dependency | Service maintainer | Platform maintainer | Linked migration issue with due date |
| Shared internal wrapper/library | Platform team lead | Repo maintainer | Owner map entry in docs + PR reference |
| Test/build-only dependency | Module maintainer | CI/tooling owner | Changelog link + validation checklist |
| Transitive high-risk dependency | Security owner | Service maintainer | Risk note + remediation timeline |

Ownership mapping checklist:
- [ ] Each in-scope dependency has exactly one primary and one backup owner.
- [ ] Every owner row links to a single issue/PR tracking artifact.
- [ ] Owners confirm SLA for upgrade, incident response, and deprecation sign-off.

## Change Freeze Exceptions

| Exception Type | Allowed When | Required Approver | Required Evidence |
|---|---|---|---|
| Security patch | Critical vulnerability with active or high-likelihood exploit | Security owner + service owner | CVE/advisory link + rollback plan |
| Production incident mitigation | Dependency change required to restore service | Incident commander + SRE owner | Incident ID + blast-radius note |
| Compliance/legal mandate | Regulatory obligation with fixed deadline | Engineering manager + compliance owner | Policy reference + due date |

Exception checklist:
- [ ] Exception request states scope, risk, and exact expiration date.
- [ ] Approval is recorded in writing before merge/cutover.
- [ ] Post-exception review logs outcome and follow-up owner.

## Dependency Risk Scoring

| Risk Factor | Score (0-3) | Quick Rule |
|---|---:|---|
| Runtime criticality | 0-3 | 3 if startup/request path breaks without it |
| Exploitability/security exposure | 0-3 | 3 if known vuln with public exploit path |
| Upgrade complexity | 0-3 | 3 if API/behavior changes need code migration |
| Observability/rollback confidence | 0-3 | 3 if weak telemetry or unproven rollback |

Scoring checklist:
- [ ] Assign a score per factor and compute total (0-12).
- [ ] Classify total: Low (0-3), Medium (4-7), High (8-12).
- [ ] Require security + SRE sign-off for all High-risk replacements.
- [ ] Link scorecard artifact in the migration tracking issue.

## Replacement Freeze Checklist

| Freeze Gate | Verification | Owner |
|---|---|---|
| Scope lock | In-scope dependency list is finalized and version-pinned | Service owner |
| Change controls | Branch protection + required reviewers are enabled | Repo maintainer |
| Exception path | Emergency exception template and approvers are documented | SRE lead |
| Exit criteria | Freeze end requires parity, reliability, and rollback evidence | Service owner + SRE |

Execution checklist:
- [ ] Announce freeze window and impacted repos/channels.
- [ ] Confirm no non-exception dependency PRs remain open.
- [ ] Record all approved exceptions with expiry and rollback notes.
- [ ] Run freeze-exit audit and attach evidence before reopening changes.

## Upgrade Blast Radius Map

| Impact Surface | Failure Mode | Detection Signal | Owner | Containment Step |
|---|---|---|---|---|
| Runtime startup path | Service fails to boot after replacement | Startup health check / crash loop alert | Service owner | Revert dependency bump and redeploy last known-good build |
| Request/response contract | Consumer-facing API behavior drift | Contract tests + 4xx/5xx anomaly alerts | API owner | Roll back release and restore prior schema/serializer behavior |
| Job/worker execution | Background jobs stall or retry-loop | Queue lag + dead-letter growth alerts | Worker owner | Disable new worker release and replay from stable version |
| CI/build pipeline | Build/test tooling fails on new version | Required CI gates + failure trend spike | Build owner | Pin previous tool version and rerun full validation |
| Observability/telemetry | Logging/metrics/traces degrade or vanish | Missing signal SLO breach | SRE owner | Restore prior instrumentation package/config |

Blast-radius checklist:
- [ ] Enumerate all affected services, jobs, and shared libraries.
- [ ] Link one primary detector and one fallback detector per surface.
- [ ] Assign one accountable owner per surface before merge.
- [ ] Pre-approve rollback command/runbook for every High-risk surface.

## Verification Signoff Matrix

| Verification Gate | Required Signoff | Minimum Evidence | Status |
|---|---|---|---|
| Functional parity | Service owner | Passing regression/contract test report | ☐ Pending / ☐ Approved |
| Reliability guardrails | SRE owner | Error budget + latency/capacity check snapshot | ☐ Pending / ☐ Approved |
| Security posture | Security owner | Vulnerability scan + advisory review artifact | ☐ Pending / ☐ Approved |
| Rollback readiness | Incident commander | Successful rollback drill or dry-run record | ☐ Pending / ☐ Approved |
| Consumer readiness | Product/API owner | Communication artifact + migration notes | ☐ Pending / ☐ Approved |

Signoff checklist:
- [ ] No gate is marked Approved without linked evidence.
- [ ] Any Pending gate blocks production cutover.
- [ ] Approval timestamps and approver identities are recorded.
- [ ] Final cutover note links to this completed matrix.
