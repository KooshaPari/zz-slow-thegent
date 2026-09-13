# Anti-Pattern Detection Guide

Hooks in `hooks/suppress-*.sh` detect and prevent common agent anti-patterns at Write/Edit time. Each hook runs during PreToolUse events.

---

## 0. Library-First (Governance)

**Principle**: Prefer **library + thin wrapper** over full custom implementation. Apply from the start of development and throughout.

**Before implementing**:
1. Search PyPI/docs for existing libraries.
2. Generic problems (retry, cache, file watch, circuit breaker): use a library.
3. If custom: document rationale in ADR.

**Project standards**: tenacity (retry), httpx (HTTP), watchdog (file watch), cachetools (cache), pybreaker (circuit breaker). See [LIBRARY_FIRST_AUDIT_AND_PLAN.md](../research/LIBRARY_FIRST_AUDIT_AND_PLAN.md).

**Proactive evolution**: Agents must not wait for the user to request governance updates. When implementing or discovering a pattern in a governed domain, check if anti-patterns.md covers it; if not, add it. See [PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md](../research/PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md).

---

## 1. Custom Retry Logic (`suppress-custom-retry.sh`)

**Pattern**: Manual retry loops (`while retry`, `for i in range(max_retries)`, `sleep` + retry).

**Why it's bad**: tenacity is already in project deps. Manual retry loops are error-prone (missing jitter, no backoff, no configurable stop conditions).

**Fix**:
```python
from tenacity import retry, stop_after_attempt, wait_random_exponential


@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(min=2, max=60))
def fetch(url: str) -> httpx.Response:
    return httpx.get(url, timeout=10)
```

**Note**: Prefer `wait_random_exponential` over `wait_exponential` — adds jitter to avoid thundering herd. See [TENACITY_RETRY_AUDIT_PLAN](../research/TENACITY_RETRY_AUDIT_PLAN.md).

**Enforcement**: Advisory (warning only).

---

## 2. V2/Duplicate Files (`suppress-v2-files.sh`)

**Pattern**: Files named `*_v2.*`, `*_new.*`, `*_old.*`, `*_backup.*`, `*_copy.*`, `*.bak`.

**Why it's bad**: Duplicates create maintenance burden and divergent implementations. The original file should be refactored instead.

**Fix**: Refactor the original file. Use git branches for experimental changes.

**Enforcement**: **BLOCKING** (prevents file creation).

---

## 3. Hardcoded Provider Strings (`suppress-hardcoded-strings.sh`)

**Pattern**: `provider = "openai"`, `model = "gpt-4"` in non-config files.

**Why it's bad**: Hardcoded providers make switching impossible without code changes. Config-driven selection enables multi-provider support.

**Fix**:
```python
from myproject.config import settings

provider = registry.get(settings.llm_provider)
```

**Enforcement**: Advisory (warning only).

---

## 4. Print Statements (`suppress-print-statements.sh`)

**Pattern**: `print()` calls in non-CLI source code (2+ occurrences).

**Why it's bad**: print() produces unstructured output that can't be filtered, aggregated, or routed. structlog provides structured, context-rich logging.

**Fix**:
```python
import structlog

logger = structlog.get_logger()
logger.info("message", key="value")
```

**Enforcement**: Advisory (warning only). CLI entry points (main.py, cli.py) are excluded.

---

## 4b. Custom Cache (`suppress-custom-cache.sh`)

**Pattern**: Manual TTL logic, custom `_CACHE` dicts with timestamp checks, file-based cache with hand-rolled invalidation.

**Why it's bad**: cachetools and diskcache provide battle-tested TTL, eviction, and persistence. Custom caches often miss edge cases (race conditions, memory growth).

**Fix**:
```python
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=60)
# or diskcache for file-based
```

**Enforcement**: Advisory (warning only).

---

## 4c. Custom File Watcher (`suppress-custom-file-watcher.sh`)

**Pattern**: `os.walk` + `stat().st_mtime` polling loop for file change detection.

**Why it's bad**: Polling is CPU/I/O heavy; misses events between polls. watchdog uses inotify/FSEvents for efficient, event-driven detection.

**Fix**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
```

**Enforcement**: Advisory (warning only).

---

## 5. God Classes (`suppress-isolated-classes.sh`)

**Pattern**: Classes with >15 methods, or 3+ Manager/Handler/Service classes in one file.

**Why it's bad**: God classes violate single responsibility. Multiple Manager-pattern classes suggest a missing generic registry.

**Fix**: Decompose into smaller classes. Use Protocol/ABC for shared interfaces. Consider a registry pattern for N similar classes.

**Enforcement**: Advisory (warning only).

---

## 6. Direct HTTP / Wrong Library (`suppress-direct-http.sh`)

**Pattern**: `import requests`, `import urllib`, or custom HTTP wrapper classes without httpx.

**Why it's bad**: httpx is the project standard (async-capable, modern API). requests is sync-only. urllib is low-level. Custom wrappers duplicate httpx functionality.

**Files to migrate**: 7 files use urllib.request — see [LIBRARY_REPLACEMENT_AUDIT_DEEP](../research/LIBRARY_REPLACEMENT_AUDIT_DEEP.md) §2.

**Fix**:
```python
import httpx

response = httpx.get(url, timeout=10)

# Async
async with httpx.AsyncClient() as client:
    response = await client.get(url, timeout=10)
```

**Enforcement**: Advisory (warning only).

---

## Hook Integration

All hooks receive these environment variables from the dispatcher:
- `FILE_PATH` — absolute path to the file being written/edited
- `TOOL_CONTENT` — full file content (Write)
- `TOOL_NEW_STRING` — replacement text (Edit)
- `TOOL_NAME` — "Write" or "Edit"

### Blocking vs Advisory

| Hook | Behavior | Exit Code |
|------|----------|-----------|
| suppress-v2-files | **Blocking** | 2 (with JSON) |
| All others | Advisory | 0 (always) |

### Consolidated Detector

`agent-antipattern-detector.sh` combines all patterns into a single hook for performance. The individual `suppress-*.sh` hooks exist for targeted use or when only specific patterns should be checked.


---
## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index


---

## 5. Custom File Watching (`suppress-custom-file-watch.sh`)

**Pattern**: `os.walk` polling, `mtime` comparison loops for file changes.

**Why it's bad**: Polling is CPU-intensive and misses events between polls. watchdog provides native filesystem events (inotify/FSEvents).

**Fix**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            print(f"Modified: {event.src_path}")


observer = Observer()
observer.schedule(MyHandler(), path=".", recursive=True)
observer.start()
```

**Library**: `watchdog` (add to deps)

**Enforcement**: Advisory (warning only).

---

## 6. Custom Circuit Breaker (`suppress-custom-circuit-breaker.sh`)

**Pattern**: Manual failure counters, time-window pruning for circuit breaking.

**Why it's bad**: Custom implementations often miss edge cases (half-open state, concurrent access). pybreaker provides battle-tested state machine.

**Fix**:
```python
from pybreaker import CircuitBreaker, CircuitBreakerError

circuit = CircuitBreaker(fail_max=5, reset_timeout=30)


@circuit
def risky_call():
    # Your code here
    pass
```

**Library**: `pybreaker` (add to deps)

**Enforcement**: Advisory (warning only).

---

## 7. Custom TTL Cache (`suppress-custom-cache.sh`)

**Pattern**: Manual dict-based caches with `expiry` timestamps and manual cleanup.

**Why it's bad**: Error-prone (race conditions, memory leaks). cachetools provides thread-safe TTL caches with automatic eviction.

**Fix**:
```python
from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=300)  # 5 minute TTL
cache["key"] = value  # Auto-evicted after 5 minutes
```

**Library**: `cachetools` (already in deps)

**Enforcement**: Advisory (warning only).

---

## 8. Anti-Patterns Reference

| # | Anti-Pattern | Fix | Severity |
|---|--------------|-----|----------|
| 1 | Custom retry loops | tenacity | Warning |
| 2 | V2/duplicate files | Refactor original | **BLOCKING** |
| 3 | Hardcoded providers | Config-driven | Warning |
| 4 | Print statements | structlog | Warning |
| 5 | Custom file watch | watchdog | Warning |
| 6 | Custom circuit breaker | pybreaker | Warning |
| 7 | Custom TTL cache | cachetools | Warning |

---

## 9. IMPLEMENTATION: Anti-Pattern Detector

```python
#!/usr/bin/env python3
# scripts/anti_pattern_detector.py

import re
from pathlib import Path
from typing import List, Tuple

ANTI_PATTERNS = [
    ("Custom retry", r"for\s+\w+\s+in\s+range\s*\(\s*\d+\s*\).*except.*sleep", "Use tenacity"),
    ("V2 file", r"_\w*_?v2\.|\.v2\.|_new\.|\.old\.", "Refactor original"),
    ("Hardcoded provider", r'provider\s*=\s*["\']\w+["\']', "Use config"),
    ("Print statement", r"^\s*print\s*\(", "Use structlog"),
    ("os.walk polling", r"os\.walk.*mtime", "Use watchdog"),
    ("Manual cache", r"dict.*expiry|TTL.*cache", "Use cachetools"),
]


def scan_file(path: Path) -> List[Tuple[int, str, str]]:
    """Scan file for anti-patterns."""
    try:
        content = path.read_text()
    except (UnicodeDecodeError, FileNotFoundError):
        return []

    findings = []
    for pattern_id, pattern, fix in ANTI_PATTERNS:
        matches = list(re.finditer(pattern, content, re.MULTILINE))
        for match in matches:
            line_no = content[: match.start()].count("\n") + 1
            findings.append((line_no, pattern_id, fix))
    return findings


def main():
    import sys

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    if path.is_file():
        findings = scan_file(path)
        for line_no, pattern_id, fix in findings:
            print(f"⚠️  {path}:{line_no} - {pattern_id} ({fix})")
    else:
        for py_file in path.rglob("*.py"):
            findings = scan_file(py_file)
            for line_no, pattern_id, fix in findings:
                print(f"⚠️  {py_file}:{line_no} - {pattern_id} ({fix})")
```

---

## 10. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 5-7:** New anti-patterns (file watch, circuit breaker, TTL cache)
2. **Added Section 8:** Anti-patterns reference table
3. **Added Section 9:** Implementation of anti-pattern detector script

### Cross-References Added

- TENACITY_RETRY_AUDIT_PLAN.md
- LIBRARY_FIRST_AUDIT_AND_PLAN.md
- PROACTIVE_GOVERNANCE_EVOLUTION_PLAN.md

### Practical Additions

- Python anti-pattern detector script
- Library recommendations for each anti-pattern
- Severity levels (BLOCKING vs Warning)
