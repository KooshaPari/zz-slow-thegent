<DONE>
# Library Replacement — Phase Design Work Breakdowns (DWBs)

> **Purpose**: Detailed task breakdown for each phase of [LIBRARY_REPLACEMENT_AUDIT_DEEP.md](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md). Use before implementation.
>
> **Status**: DWBs Complete | **Date**: 2026-02-16
> **Phases complete**: 1 (urllib→httpx), 2 (tenacity), 3 (watchdog—already done), 4 (ANSI strip), 5 (cachetools), 6 (diskcache), 7 (psutil), 8 (pybreaker), 9 (md5→sha256), 10 (os.environ→ThegentSettings), 19 (tomlkit), 21 (\_CWD_CACHE→cachetools)

---

## Phase 1: Replace urllib with httpx (7+ files)

**Effort**: 2–3 hrs | **Priority**: P1

### Tasks

| #   | Task                                          | File(s)                     | Acceptance Criteria                                                        |
| --- | --------------------------------------------- | --------------------------- | -------------------------------------------------------------------------- |
| 1.1 | Replace urllib in models/scrapers.py          | models/scrapers.py          | `_scrape_proxy_models`, `_scrape_openai_models` use httpx.get              |
| 1.2 | Replace urllib in agents/cliproxy_manager.py  | agents/cliproxy_manager.py  | Health check, model fetch use httpx.get                                    |
| 1.3 | Replace urllib in agents/cursor_api_runner.py | agents/cursor_api_runner.py | Health check uses httpx.get                                                |
| 1.4 | Replace urllib in execution.py                | execution.py                | Policy check URL uses httpx.get; map URLError/HTTPError → httpx exceptions |
| 1.5 | Replace urllib in mcp_manage.py               | mcp_manage.py               | Config fetch (2 calls) uses httpx.get                                      |
| 1.6 | Replace urllib in clode_main.py               | clode_main.py               | Health URL check uses httpx.get                                            |
| 1.7 | Replace urllib in routing/alerting.py         | routing/alerting.py         | Webhook POST uses httpx.post                                               |
| 1.8 | Replace urllib in mgmt_manage.py              | mgmt_manage.py              | If present, use httpx                                                      |

### Pattern

```python
# Before
req = urllib.request.Request(url, method="GET")
with urllib.request.urlopen(req, timeout=2) as resp:
    data = resp.read()

# After
resp = httpx.get(url, timeout=2)
data = resp.content
```

### Exception mapping

- `urllib.error.URLError` → `httpx.RequestError` or `httpx.ConnectError`
- `urllib.error.HTTPError` → `httpx.HTTPStatusError` (check `resp.raise_for_status()`)

---

## Phase 2: Migrate retry loops to tenacity

**Effort**: 4–6 hrs | **Priority**: P1

### Tasks

| #   | Task                                  | File(s)                   | Acceptance Criteria                          | Status                                                                                                                                                    |
| --- | ------------------------------------- | ------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 | Migrate cli_impl.py EAGAIN retry      | cli_impl.py               | Use tenacity.retry with retry_if_exception   | **N/A** — pattern not present; subprocess.Popen has no EAGAIN retry. Optional: add as new feature.                                                        |
| 2.2 | Migrate cli_impl.py DAG retry backoff | cli_impl.py               | Replace \_backoff_delay + loop with tenacity | **N/A** — `_backoff_delay` and DAG retry sleep not present. Audit says tenacity doesn't fit (delay before spawn, not call retry); plan was "Keep custom". |
| 2.3 | Migrate loop_controller.py retry loop | agents/loop_controller.py | Replace while attempt + sleep with tenacity  | ✓ Done — uses @with_retry                                                                                                                                 |
| 2.4 | Verify state_machine.py               | agents/state_machine.py   | Already uses tenacity ✓                      | ✓ Done — migrated to tenacity                                                                                                                             |

### Notes

- **2.1, 2.2**: Not a failure. The audit described hypothetical/design patterns; the code was never implemented. N/A = nothing to migrate.
- **2.2**: TENACITY_RETRY_AUDIT_PLAN §3.4 says "Tenacity fit: No" and "Plan: Keep custom" — DAG backoff is a delay before spawn, not a function retry.

### Reference

See [TENACITY_RETRY_AUDIT_PLAN.md](./TENACITY_RETRY_AUDIT_PLAN.md).

---

## Phase 3: Replace WatchdogTrigger with watchdog

**Effort**: 2–4 hrs | **Priority**: P1

### Tasks

| #   | Task                                  | File(s)                | Acceptance Criteria                           |
| --- | ------------------------------------- | ---------------------- | --------------------------------------------- |
| 3.1 | Add watchdog to dependencies          | pyproject.toml         | `watchdog>=4.0.0`                             |
| 3.2 | Replace os.walk polling with Observer | governance/triggers.py | WatchdogTrigger uses watchdog.Observer        |
| 3.3 | Implement FileSystemEventHandler      | governance/triggers.py | Debounce via event coalescing or thin wrapper |
| 3.4 | Preserve exclude_dirs behavior        | governance/triggers.py | Filter events by path                         |

---

## Phase 4: Consolidate ANSI strip → rich.strip_control_codes

**Effort**: 1 hr | **Priority**: P2

### Tasks

| #   | Task                                   | File(s)                        | Acceptance Criteria                            |
| --- | -------------------------------------- | ------------------------------ | ---------------------------------------------- |
| 4.1 | Create thegent.utils.strip_ansi        | (new) utils.py or agents/utils | `from rich.console import strip_control_codes` |
| 4.2 | Replace in agents/codex_proxy.py       | agents/codex_proxy.py          | Use strip_control_codes                        |
| 4.3 | Replace in agents/direct_agents.py     | agents/direct_agents.py        | Use strip_control_codes                        |
| 4.4 | Replace in agents/droid.py             | agents/droid.py                | Use strip_control_codes                        |
| 4.5 | Replace in agents/cursor_api_runner.py | agents/cursor_api_runner.py    | Use strip_control_codes                        |
| 4.6 | Replace in parser.py                   | parser.py                      | Use strip_control_codes                        |

---

## Phase 5: Introduce cachetools for speed/quality/catalog

**Effort**: 2–3 hrs | **Priority**: P2

### Tasks

| #   | Task                                     | File(s)                  | Acceptance Criteria     |
| --- | ---------------------------------------- | ------------------------ | ----------------------- |
| 5.1 | Add cachetools to dependencies           | pyproject.toml           | `cachetools>=5.0.0`     |
| 5.2 | Replace models/speed_values.py \_CACHE   | models/speed_values.py   | Use cachetools.TTLCache |
| 5.3 | Replace models/quality_values.py \_CACHE | models/quality_values.py | Use cachetools.TTLCache |
| 5.4 | Replace models/catalog.py route cache    | models/catalog.py        | Use cachetools.TTLCache |

---

## Phase 6: Replace scrapers cache with diskcache

**Effort**: 1 hr | **Priority**: P2

### Tasks

| #   | Task                                           | File(s)            | Acceptance Criteria |
| --- | ---------------------------------------------- | ------------------ | ------------------- |
| 6.1 | Add diskcache to dependencies                  | pyproject.toml     | `diskcache>=5.0.0`  |
| 6.2 | Replace \_load_cached/\_save_cache in scrapers | models/scrapers.py | Use diskcache.Cache |

---

## Phase 7: Add psutil for load_based_limits, discovery

**Effort**: 2–3 hrs | **Priority**: P2

### Tasks

| #   | Task                                                    | File(s)                            | Acceptance Criteria                      |
| --- | ------------------------------------------------------- | ---------------------------------- | ---------------------------------------- |
| 7.1 | Add psutil to dependencies                              | pyproject.toml                     | `psutil>=5.9.0`                          |
| 7.2 | Replace \_get_fd_usage, \_get_memory_mb, \_get_load_avg | orchestration/load_based_limits.py | Use psutil                               |
| 7.3 | Replace ps, /proc parsing in discovery                  | discovery.py                       | Use psutil.process_iter, Process.cmdline |

---

## Phase 8: Evaluate pybreaker for circuit breaker

**Effort**: 1–2 hrs | **Priority**: P2

### Tasks

| #   | Task                          | File(s)              | Acceptance Criteria                           |
| --- | ----------------------------- | -------------------- | --------------------------------------------- |
| 8.1 | Add pybreaker to dependencies | pyproject.toml       | `pybreaker>=2.0.0`                            |
| 8.2 | Replace ToolCircuitBreaker    | agents/resilience.py | Use pybreaker.CircuitBreaker or wrap tenacity |

---

## Phase 9: Unify md5→sha256 in cache.py

**Effort**: 0.5 hr | **Priority**: P3

### Tasks

| #   | Task                                    | File(s)        | Acceptance Criteria |
| --- | --------------------------------------- | -------------- | ------------------- |
| 9.1 | Replace hashlib.md5 with hashlib.sha256 | tools/cache.py | ETag uses sha256    |

---

## Phase 10: Consolidate os.environ → ThegentSettings

**Effort**: 2–3 hrs | **Priority**: P2

### Tasks

| #    | Task                                                            | File(s)                    | Acceptance Criteria                        |
| ---- | --------------------------------------------------------------- | -------------------------- | ------------------------------------------ |
| 10.1 | Add THGENT_DEBUG, THGENT_OUTPUT_FORMAT, etc. to config          | config.py                  | All THGENT\_\* env vars in ThegentSettings |
| 10.2 | Replace os.environ.get in cliproxy_manager                      | agents/cliproxy_manager.py | Use settings                               |
| 10.3 | Replace os.environ.get in cli, clode_main, dex_main, mcp_server | (multiple)                 | Use settings                               |

---

## Phase 19: Add tomlkit to pyproject.toml

**Effort**: 0.5 hr | **Priority**: P2

### Tasks

| #    | Task                                  | File(s)        | Acceptance Criteria |
| ---- | ------------------------------------- | -------------- | ------------------- |
| 19.1 | Add tomlkit to [project.dependencies] | pyproject.toml | `tomlkit>=0.12.0`   |

---

## Phase 21: Replace \_CWD_CACHE with cachetools.TTLCache

**Effort**: 0.5 hr | **Priority**: P2

### Tasks

| #    | Task                                   | File(s)     | Acceptance Criteria                    |
| ---- | -------------------------------------- | ----------- | -------------------------------------- |
| 21.1 | Replace \_CWD_CACHE dict with TTLCache | cli_impl.py | \_resolve_cwd uses cachetools.TTLCache |

---

## Execution Order (Recommended)

1. **Phase 1** (urllib→httpx) — Quick win, no new deps
2. **Phase 19** (tomlkit) — 5 min
3. **Phase 9** (md5→sha256) — 5 min
4. **Phase 4** (ANSI strip) — 1 hr
5. **Phase 21** (\_CWD_CACHE) — 30 min
6. **Phase 5, 6, 7, 8** — Add deps, replace implementations
7. **Phase 2, 3** — Larger refactors

---

## References

- [LIBRARY_REPLACEMENT_AUDIT_DEEP.md](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md)
- [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./LIBRARY_FIRST_AUDIT_AND_PLAN.md)
- [TENACITY_RETRY_AUDIT_PLAN.md](./TENACITY_RETRY_AUDIT_PLAN.md)

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

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (9 BACKLOG items)
- [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) - Consolidated plan
- [LIBRARY_REPLACEMENT_AUDIT_DEEP.md](./LIBRARY_REPLACEMENT_AUDIT_DEEP.md) - Deep audit
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
