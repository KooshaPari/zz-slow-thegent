<DONE>
# Library Replacement Audit — Deep & Wide

> **Purpose**: Comprehensive audit of custom implementations that could be replaced with libraries or library + thin wrapper. Extends [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./LIBRARY_FIRST_AUDIT_AND_PLAN.md). **Includes proposed new libraries**, **replacements of existing libs**, and **polish / intuitiveness / robustness / extensibility / enhancements**.
> **Status**: Deep Audit Complete (Extended) | **Date**: 2026-02-16 | **Updated**: 2026-02-17
> **P3 Polish**: Summary table, cross-links, next actions added
> **Note**: This document has been consolidated into [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) - see consolidated version for implementation plan
> **Related**:

- [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) - Consolidated migration plan (recommended)
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream

---

## Document Summary

| Aspect                   | Details                                                                          |
| ------------------------ | -------------------------------------------------------------------------------- |
| **Document Type**        | Deep file-level audit                                                            |
| **Lines**                | ~825 lines                                                                       |
| **Sections**             | 47 sections covering all library replacement opportunities                       |
| **Status**               | Audit complete, consolidated into LIBRARY_REPLACEMENT_CONSOLIDATED.md            |
| **Key Findings**         | 47 replacement opportunities across HTTP, retry, caching, XML, monitoring, etc.  |
| **Consolidated Version** | See [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) |
| **BACKLOG Items**        | 9 items extracted (see consolidated doc)                                         |

---

## Next Actions (WORK_STREAM IDs)

**Note**: All BACKLOG items are tracked in [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md). See that document for:

- 9 BACKLOG items (P1: HTTP/Retry/File Watching, P2: Caching/Circuit Breaker/YAML, P3: Logging/JSON)
- Migration phases and implementation details
- Performance targets and risk mitigation

**See Also**: [WORK_STREAM.md](../reference/WORK_STREAM.md) for full backlog

---

## 1. Executive Summary

### Replacements (custom / stdlib → library)

| Category                | Files | Custom Pattern                    | Library Recommendation   | Priority |
| ----------------------- | ----- | --------------------------------- | ------------------------ | -------- |
| **HTTP**                | 7+    | urllib.request                    | httpx                    | P1       |
| **Retry**               | 4     | Manual loops                      | tenacity                 | P1       |
| **File watching**       | 1     | os.walk + mtime polling           | watchdog                 | P1       |
| **ANSI stripping**      | 5     | Duplicated `re.sub(r"\x1b\[...")` | rich.strip_control_codes | P2       |
| **Caching**             | 5+    | Custom TTL, file cache            | cachetools, diskcache    | P2       |
| **XML parsing**         | 2     | Custom regex + state machine      | defusedxml, lxml         | P2       |
| **Resource monitoring** | 1     | Custom FD/mem/load via subprocess | psutil                   | P2       |
| **Circuit breaker**     | 1     | Custom ToolCircuitBreaker         | pybreaker                | P2       |
| **Process discovery**   | 1     | ps, /proc parsing                 | psutil                   | P2       |
| **Debounce**            | 1     | threading.Timer + manual          | custom minimal           | P3       |
| **Stream parsing**      | 2     | Custom JSONL + regex              | ijson, json-stream       | P3       |
| **Hashing**             | 15+   | hashlib (OK)                      | Keep; unify md5→sha256   | P3       |
| **Logging**             | 60+   | stdlib logging                    | structlog                | P3       |

### Proposed new libraries (greenfield / enhancement)

| Category             | Files | Current                                                    | Proposed Library                               | Priority |
| -------------------- | ----- | ---------------------------------------------------------- | ---------------------------------------------- | -------- |
| **Config/env**       | 15+   | os.environ.get scattered                                   | pydantic-settings (already used) — consolidate | P2       |
| **Slugify**          | 1     | Custom `_slugify` regex                                    | python-slugify                                 | P3       |
| **Format parsing**   | 6+    | regex for CLI output                                       | parse (format strings)                         | P3       |
| **ID generation**    | 10+   | `uuid.uuid4().hex[:8]`                                     | shortuuid or nanoid                            | P3       |
| **Date/time**        | 20+   | datetime + time.perf_counter                               | pendulum (optional)                            | P3       |
| **Subprocess**       | 20+   | subprocess.run/Popen                                       | plumbum (optional) for shell-like              | P3       |
| **JSONL**            | 2     | Manual json.dumps per line                                 | jsonlines                                      | P3       |
| **YAML round-trip**  | 5+    | PyYAML                                                     | ruamel.yaml (preserve comments)                | P3       |
| **Rate limiting**    | 3     | Custom throttle logic                                      | limits or ratelimit                            | P3       |
| **Testing**          | 50+   | pytest, unittest.mock                                      | hypothesis, pytest-mock                        | P3       |
| **Data structures**  | many  | itertools, manual                                          | more-itertools, boltons                        | P3       |
| **Shell safety**     | 0     | No shlex.quote                                             | shlex.quote for user input                     | P2       |
| **CWD cache**        | 1     | Custom \_CWD_CACHE dict + TTL                              | cachetools.TTLCache                            | P2       |
| **Queue storage**    | 4     | PromptQueue, DeferralQueue, EscalationQueue — manual JSONL | jsonlines                                      | P2       |
| **Version parsing**  | 5+    | Manual version/schema_version strings                      | packaging.Version                              | P3       |
| **Exclude patterns** | 2     | Hardcoded exclude_dirs set                                 | pathspec (.gitignore-style)                    | P3       |
| **Platform dirs**    | 3+    | ~/.cache, ~/.factory, Path expand                          | platformdirs                                   | P3       |
| **Human-readable**   | 0     | —                                                          | humanize (bytes, durations)                    | P3       |

### Replacements of existing libraries (lib → better lib)

| Current Library | Files | Replacement | Rationale                                                       | Priority |
| --------------- | ----- | ----------- | --------------------------------------------------------------- | -------- |
| **PyYAML**      | 15+   | ruamel.yaml | Preserves comments, key order; round-trip safe for config edits | P2       |
| **stdlib json** | 50+   | orjson      | 5–50× faster; native datetime; drop-in for loads/dumps          | P3       |
| **argparse**    | 4     | typer       | Unify with main CLI; better help, validation                    | P3       |
| **tomlkit**     | 1     | —           | Add to pyproject deps (mcp_manage uses it; may be transitive)   | P2       |

**Keep as-is**: typer, rich, pydantic, httpx, tenacity, litellm, fastmcp, starlette, uvicorn, opentelemetry — no better replacement warranted.

### Scope (wider / deeper)

| Area             | File count | Notes                                                                            |
| ---------------- | ---------- | -------------------------------------------------------------------------------- |
| JSON (stdlib)    | 50+        | execution (55), mcp_server (68), cli (95), mcp_manage (14), mcp_tools_modes (39) |
| YAML (PyYAML)    | 15+        | cliproxy_manager, cli, constitution, teammates, scripts, templates               |
| Subprocess       | 20+        | cliproxy_manager (11), mcp_manage (17), scrapers (4), discovery (4), shadow (5)  |
| Logging          | 70+        | Every module                                                                     |
| Path/Pathlib     | 200+       | Widespread pathlib usage; keep                                                   |
| CSV              | 10+        | cli (csv.writer), tests; stdlib fine                                             |
| Platform checks  | 15+        | mcp_manage, cliproxy_manager; stdlib platform fine                               |
| Queue/JSONL      | 4          | PromptQueue, DeferralQueue, EscalationQueue, human_requests                      |
| Custom TTL cache | 2          | \_CWD_CACHE (cli_impl), tools/cache                                              |
| File I/O (open)  | 60+        | Widespread; stdlib fine                                                          |

### Polish, Intuitiveness, Robustness, Extensibility & Enhancements

| Dimension         | Current                                            | Proposed Libraries / Patterns                                                    | Priority |
| ----------------- | -------------------------------------------------- | -------------------------------------------------------------------------------- | -------- |
| **Polish**        | Rich tables; some bare `print`                     | rich.Progress, rich.Spinner, rich.Live for long ops                              | P2       |
| **Intuitiveness** | typer; manual validation messages                  | typer callbacks, shell completion (--install-completion), rich.prompt            | P2       |
| **Robustness**    | try/except; tenacity; manual validation            | exceptiongroup, pydantic ValidationError handling, retry decorators              | P2       |
| **Extensibility** | Custom SitbackPluginRegistry; file-based discovery | pluggy or importlib.metadata entry_points                                        | P3       |
| **Enhancements**  | —                                                  | typer-rich (richer typer help), questionary (interactive prompts), textual (TUI) | P3       |

**Design principles** (for all changes):

- **Polish**: Reduce cognitive load; consistent progress feedback; clear status.
- **Intuitiveness**: Self-documenting CLI; helpful errors; discoverable features.
- **Robustness**: Fail gracefully; retry where appropriate; validate early.
- **Extensibility**: Plugin hooks; entry_points; avoid hardcoding.
- **Enhancements**: Add value without breaking existing flows.

---

## 2. HTTP — urllib.request (P1)

**Anti-pattern**: Project standard is httpx. urllib is low-level, sync-only, no connection pooling.

**Files using urllib.request**:

- `models/scrapers.py` — proxy model discovery (3 calls)
- `agents/cliproxy_manager.py` — health check, model fetch (3 calls)
- `agents/cursor_api_runner.py` — health check (1 call)
- `execution.py` — policy check URL (1 call)
- `mcp_manage.py` — config fetch (2 calls)
- `clode_main.py` — health URL check (1 call)
- `routing/alerting.py` — webhook POST (1 call)

**Recommendation**: Replace all with `httpx.get()` / `httpx.post()`. httpx is already in deps. Thin wrapper for timeout/retry if needed.

**Effort**: 2–3 hrs. Search-replace pattern; add httpx client where connection reuse matters.

---

## 3. Retry (P1)

**Already covered** in TENACITY_RETRY_AUDIT_PLAN. Remaining custom loops:

- `cli_impl.py` — EAGAIN retry, DAG retry backoff
- `loop_controller.py` — `while attempt <= budget.max_retries` + sleep
- `state_machine.py` — uses tenacity ✓

**Recommendation**: Migrate all to tenacity. See TENACITY_RETRY_AUDIT_PLAN.

---

## 4. File Watching (P1)

**File**: `governance/triggers.py` — WatchdogTrigger

**Current**: `os.walk` every 2s, mtime comparison, exclude_dirs filter.

**Recommendation**: `watchdog.Observer` + `FileSystemEventHandler`. Debounce via `watchdog`'s event coalescing or thin wrapper.

**Library**: `watchdog`

---

## 5. ANSI Stripping (P2)

**Duplicated in 5+ files**:

- `agents/codex_proxy.py`
- `agents/direct_agents.py`
- `agents/droid.py`
- `agents/cursor_api_runner.py`
- `parser.py`

**Pattern**: `re.sub(r"\x1b\[[0-9;]*m", "", text)` — strips basic ANSI CSI sequences only.

**Libraries**:

- `ansi2text` (PyPI) — strips ANSI to plain text
- `strip-ansi` (npm, but Python equivalents exist)
- `rich` — has `strip_control_codes()` — **rich is already in deps**

**Recommendation**: Use `rich.console.strip_control_codes(text)` or extract to `thegent.utils.strip_ansi(text)` and call from all agents. Rich is already a dep.

**Effort**: 1 hr. Single helper + replace 5 call sites.

---

## 6. Caching (P2)

**Files**:

- `tools/cache.py` — ResourceCache (ETag + TTL file-based)
- `models/speed_values.py` — `_CACHE` tuple (timestamp, data)
- `models/quality_values.py` — same pattern
- `models/catalog.py` — `_ROUTE_RESOLVE_CACHE`, `_STATIC_CATALOG`
- `models/scrapers.py` — `_load_cached`, `_save_cache` (JSON file + mtime)

**Recommendation**:

- In-memory TTL: `cachetools.TTLCache`
- File-based: `diskcache.Cache` or `cachetools` + disk backend
- Scrapers: Replace `_load_cached`/`_save_cache` with diskcache

**Libraries**: `cachetools`, `diskcache`

---

## 7. XML Parsing & Repair (P2)

**Files**:

- `contracts/parser.py` — `IncrementalXMLParser`, `StreamingXMLParser` — regex-based `<TAG>value</TAG>` extraction
- `tools/xml_repair.py` — `SloppyXMLRepair` — regex repair for unclosed/naked tags

**Current**: Custom regex; no full XML parser. Handles simple agent output only.

**Libraries**:

- **Parsing**: `defusedxml` (secure), `xml.etree.ElementTree` (stdlib) — for full XML; current use case is intentionally permissive
- **Repair**: No standard lib for "repair malformed XML from LLM". Options: `lxml` with `recover=True`, or keep custom for domain-specific repair

**Recommendation**:

- For parsing: If we need stricter validation, use `defusedxml`. Current regex extractor is domain-specific (agent outputs); keep or wrap in a small module.
- For repair: Evaluate `lxml.etree.fromstring(text, parser=etree.XMLParser(recover=True))` — may be overkill. Document as "intentionally custom for LLM output repair."

**Priority**: P2 — low; current impl is small and domain-specific.

---

## 8. Resource Monitoring (P2)

**File**: `orchestration/load_based_limits.py`

**Current**:

- `_get_fd_usage()` — `/proc/self/fd` or `lsof -p PID`
- `_get_memory_mb()` — `resource.getrusage`, `/proc/meminfo`, or `vm_stat`
- `_get_load_avg()` — `os.getloadavg()`

**Library**: `psutil` — cross-platform, handles FD count, memory, load, CPU.

**Recommendation**: Replace with `psutil.Process().num_fds()` (Linux), `psutil.virtual_memory()`, `psutil.getloadavg()`. Thin wrapper for `ResourceSnapshot`.

**Library**: `psutil`

---

## 9. Circuit Breaker (P2)

**File**: `agents/resilience.py` — `ToolCircuitBreaker`

**Current**: Manual list of failure timestamps, prune by window, threshold check.

**Library**: `pybreaker` — state machine (closed → open → half-open), configurable.

**Recommendation**: Use `pybreaker.CircuitBreaker` or wrap tenacity with fail-fast when circuit open.

---

## 10. Process Discovery (P2)

**File**: `discovery.py`

**Current**: `subprocess.run(["ps", ...])`, `/proc` parsing, `lsof` for FD.

**Library**: `psutil` — `psutil.Process().cmdline()`, `psutil.process_iter()`, parent/child tree.

**Recommendation**: Use `psutil` for process tree and command-line extraction. Reduces platform-specific branches.

---

## 11. Debounce (P3)

**File**: `governance/triggers.py` — WatchdogTrigger

**Current**: `threading.Timer` for debounce; cancel/reschedule on new events.

**Libraries**: No standard debounce lib. `more-itertools` has no debounce. Custom is ~20 LOC.

**Recommendation**: Keep custom or use a tiny `debounce` helper. Low priority.

---

## 12. Stream / JSONL Parsing (P3)

**Files**:

- `output_parser.py` — JSONL line-by-line, regex for noise stripping
- `parser.py` — CLI output regex (RESUME_RE, TOKEN_USAGE_RE, MCP_ERROR_RE)

**Libraries**:

- **Streaming JSON**: `ijson`, `json-stream` — for large JSON streams
- **JSONL**: stdlib `json.loads` per line is fine
- **CLI parsing**: Domain-specific; regex is appropriate. Could use `parse` (PyPI) for format strings if patterns grow.

**Recommendation**: Keep for now. output_parser is domain-specific (agent stream formats). If we add large JSON streaming, consider ijson.

---

## 13. Hashing (P3)

**Current**: `hashlib.sha256`, `hashlib.md5` (cache.py ETag) throughout.

**Recommendation**:

- stdlib hashlib is fine.
- Unify: Replace `hashlib.md5` in `tools/cache.py` with `sha256` for consistency (md5 is cryptographically weak; for ETag it's acceptable but sha256 is preferred).

**Effort**: 1 line change in cache.py.

---

## 14. Logging (P3)

**Current**: stdlib `logging` in 60+ files.

**Recommendation**: `structlog` for structured, JSON output. Migration is incremental.

**Library**: `structlog`

---

## 15. Threading / Subprocess Drain (P3)

**Files**: `agents/codex_proxy.py`, `agents/direct_agents.py`

**Current**: `threading.Thread(target=_drain, args=(pipe, list, callback))` for non-blocking stdout/stderr read.

**Recommendation**: stdlib threading is appropriate. For async, `asyncio.create_subprocess_exec` + streams. Keep as-is; pattern is minimal.

---

## 16. Hysteresis (P3)

**File**: `orchestration/load_based_limits.py` — `HysteresisController`

**Current**: Custom upper/lower threshold + dwell time to prevent thrashing.

**Recommendation**: Domain-specific. No standard lib. Keep custom.

---

## 17. Health Score Formula (Keep)

**File**: `governance/health_score.py`

**Current**: Weighted normalization, band thresholds. Pure domain logic.

**Recommendation**: Keep custom.

---

## 18. Config / Env Consolidation (P2 — Proposed)

**Files**: 15+ — `cliproxy_manager.py`, `cli.py`, `clode_main.py`, `dex_main.py`, `mcp_server.py`, `cli_impl.py`, `codex_proxy.py`, etc.

**Current**: Scattered `os.environ.get("THGENT_*")` bypassing `ThegentSettings`. config.py uses pydantic-settings + python-dotenv; many call sites read env directly.

**Recommendation**: Add missing vars to `ThegentSettings` (e.g. `THGENT_DEBUG`, `THGENT_OUTPUT_FORMAT`, `THGENT_SESSION_META_PATH`, `THGENT_OWNER_TAG`). Route all reads through `settings`. Reduces drift and enables validation.

**Libraries**: pydantic-settings, python-dotenv (already in deps).

---

## 19. Slugify (P3 — Proposed)

**File**: `mcp_tools_modes.py` — `_slugify(text, max_len=32)`

**Current**: `re.sub(r"[^\w\s-]", "", text.lower())` + `re.sub(r"[-\s]+", "_", ...)` — basic ASCII slug.

**Library**: `python-slugify` — Unicode-aware, configurable separators, truncation.

**Recommendation**: `from slugify import slugify`; `slugify(text, max_length=max_len, separator="_")`. Low effort.

---

## 20. Format String Parsing (P3 — Proposed)

**Files**: `discovery.py` (\_RESUME_RE), `parser.py` (RESUME_RE, TOKEN_USAGE_RE, MCP_ERROR_RE), `output_parser.py`, `governance/scanner.py`, `models/scrapers.py`, `contracts/parser.py`

**Current**: Many `re.compile(...)` for CLI output, model names, token usage. Domain-specific; regex is appropriate.

**Library**: `parse` (PyPI) — `parse.parse("--resume={resume_id}", line)` for format-string style extraction.

**Recommendation**: Consider for new patterns. Existing regex is fine; migrate only if patterns grow or become brittle.

---

## 21. ID Generation (P3 — Proposed)

**Files**: `cli.py`, `cli_impl.py`, `execution.py`, `state_machine.py`, `agileplus.py`, `agent_deployer.py`, `mcp_tools_modes.py`, `tools/human.py`, `remediation_planner.py`

**Current**: `f"run_{uuid.uuid4().hex[:8]}"`, `f"cycle_{uuid.uuid4().hex[:8]}"`, etc. — 8-char hex IDs.

**Libraries**: `shortuuid` — URL-safe short IDs; `nanoid` — compact, URL-safe.

**Recommendation**: Optional. stdlib uuid is fine. shortuuid gives shorter, URL-safe IDs if needed for URLs/APIs.

---

## 22. Date/Time (P3 — Proposed)

**Files**: `governance/ledger.py`, `orchestration/memory.py`, `cli.py`, `mcp_server.py` (time.perf_counter), many others.

**Current**: `datetime`, `time.perf_counter`, `time.sleep`, `time.monotonic`. stdlib is adequate.

**Libraries**: `pendulum`, `arrow` — timezone-aware, human parsing, intervals.

**Recommendation**: Keep stdlib. pendulum/arrow only if timezone/parsing complexity grows.

---

## 23. Subprocess (P3 — Proposed)

**Files**: 20+ — `cliproxy_manager.py` (11), `models/scrapers.py` (4), `discovery.py` (4), `mcp_manage.py` (17), `tools/terminal.py` (6), `orchestration/shadow.py` (5), etc.

**Current**: `subprocess.run`, `subprocess.Popen` with manual env, cwd, capture. No `shlex.quote` for user-provided args.

**Libraries**: `plumbum` — shell-like `local["cmd"](args)`; `sh` — simpler shell. For safety: `shlex.quote` (stdlib) for any user input in commands.

**Recommendation**: Add `shlex.quote` where user input flows into shell commands (P2). plumbum optional for complex subprocess orchestration.

---

## 24. JSONL (P3 — Proposed)

**Files**: `output_parser.py`, `tools/human.py` (human_requests.jsonl)

**Current**: Manual `json.dumps(obj) + "\n"` append; line-by-line `json.loads`.

**Library**: `jsonlines` — `jsonlines.open(path).iter()` for read; `writer.write(obj)` for append.

**Recommendation**: Low effort. Improves consistency for JSONL I/O.

---

## 25. YAML — PyYAML → ruamel.yaml (P2 — Replace existing lib)

**Files**: 15+ — `cliproxy_manager.py` (4), `cli.py` (2), `dex_main.py`, `clode_main.py`, `governance/constitution.py`, `governance/teammates.py`, `scripts/start_proxy_with_adapter.py`, `quality_runner.py`, `quality_fix_runner.py`, tests

**Current**: `yaml.safe_load`, `yaml.dump` — loses comments, key order on round-trip. Config edits (cliproxy_manager, cli) overwrite user comments.

**Library**: `ruamel.yaml` — `YAML().load()` / `YAML().dump()`; preserves comments, key order; round-trip safe.

**Recommendation**: Replace PyYAML with ruamel.yaml for all YAML I/O. Use `ruamel.yaml.YAML(typ='safe')` for load-only; `typ='rt'` for round-trip. Add `ruamel.yaml` to deps; can remove `pyyaml` if fully migrated.

**Effort**: 2–3 hrs. Create thin wrapper `thegent.utils.yaml_io` for compatibility.

---

## 26. JSON — stdlib → orjson (P3 — Replace existing lib)

**Files**: 50+ — `execution.py` (55), `mcp_server.py` (68), `cli_impl.py` (22), `cli.py` (95), `mcp_manage.py` (14), `mcp_tools_modes.py` (39), plus 40+ others.

**Current**: `json.loads`, `json.dumps`, `json.load`, `json.dump` — adequate but slow for large payloads.

**Library**: `orjson` — 5–50× faster; native datetime/UUID serialization; strict UTF-8. API: `orjson.loads(s)`, `orjson.dumps(obj)`.

**Recommendation**: Add `orjson`; use for hot paths (execution, mcp_server, routing). Create `thegent.utils.json_io` with fallback to stdlib for edge cases (orjson is strict). Keep stdlib for `default`/`object_hook` where needed.

**Effort**: 4–6 hrs. Incremental migration; start with execution.py, mcp_server.py.

---

## 27. argparse → typer (P3 — Replace existing lib)

**Files**: `governance/triggers.py`, `templates/.../quality_runner.py`, `scripts/verify-fastmcp.py` (2)

**Current**: `argparse.ArgumentParser` for standalone scripts. Main CLI uses typer.

**Recommendation**: Migrate to typer for consistency, better help, validation. Low priority — argparse is fine for one-off scripts.

**Effort**: 1–2 hrs per script.

---

## 28. tomlkit — Add to deps (P2)

**File**: `mcp_manage.py` — `import tomlkit` for Codex config.toml round-trip.

**Current**: tomlkit used but not in pyproject.toml dependencies. May be transitive (e.g. from fastmcp).

**Recommendation**: Add `tomlkit>=0.12.0` to `[project.dependencies]` for explicit dependency. Prevents breakage if transitive dep is removed.

---

## 29. Rate Limiting (P3 — Proposed)

**Files**: `mcp_server.py` (RateLimitingMiddleware from fastmcp), `execution.py`, `planning/simulation.py`, `planning/slo_regulator.py`, `agents/resilience.py`

**Current**: Custom throttle logic (hysteresis, spend thresholds). FastMCP provides RateLimitingMiddleware.

**Libraries**: `limits` — Redis/memory backend; `ratelimit` — decorator-based.

**Recommendation**: Keep custom for domain logic. limits/ratelimit if we add generic API rate limiting.

---

## 30. Testing Enhancements (P3 — Proposed)

**Files**: 50+ test files — pytest, unittest.mock, pytest-asyncio, pytest-cov, pytest-xdist.

**Current**: Solid pytest setup. Some tests use raw `unittest.mock.patch`.

**Libraries**: `hypothesis` — property-based testing; `pytest-mock` — `mocker` fixture; `pytest-benchmark` — perf tests.

**Recommendation**: Add hypothesis for fuzz-style validation of parsers/validators. pytest-mock optional (mocker cleaner than patch).

---

## 31. Data Structures (P3 — Proposed)

**Files**: Various — `itertools.chain`, manual grouping, flattening.

**Libraries**: `more-itertools` — `chunked`, `flatten`, `nth`, `unique_everseen`, etc.; `boltons` — `iterutils`, `strutils`, `cacheutils`.

**Recommendation**: Add more-itertools when patterns repeat (chunked, flatten). boltons for iterutils if needed.

---

## 32. Shell Safety (P2 — Proposed)

**Files**: Any subprocess call with user-controlled args (CLI args, agent output, config).

**Current**: No explicit `shlex.quote` usage. Commands built via list args to subprocess are generally safe; string-based `shell=True` would need quoting.

**Recommendation**: Audit subprocess calls. Use `shlex.quote(arg)` for any user input passed to shell. Prefer `subprocess.run([cmd, arg1, arg2])` over `shell=True`.

---

## 33. CWD Cache — Custom TTL dict → cachetools (P2 — Code replacement)

**File**: `cli_impl.py` — `_CWD_CACHE`, `_CWD_CACHE_TTL`, `_resolve_cwd()`

**Current**: Manual dict `{cache_key: (resolved_p, expiry, now)}` with stat-based TTL (10s). ~30 LOC.

**Recommendation**: Replace with `cachetools.TTLCache(maxsize=128, ttl=10)`. Single line; automatic eviction.

**Effort**: 0.5 hr.

---

## 34. Queue Storage — Manual JSONL → jsonlines (P2 — Code replacement)

**Files**: `queue/storage.py` (PromptQueue), `execution.py` (DeferralQueue, EscalationQueue), `tools/human.py` (human_requests.jsonl)

**Current**: All use `json.dumps(entry) + "\n"` append; line-by-line `json.loads` in loops. Duplicated pattern.

**Recommendation**: Use `jsonlines.open(path, mode="a").write(entry)` and `jsonlines.open(path).iter()`. Unify in `thegent.queue.storage`; replace 4 queue implementations.

**Effort**: 2–3 hrs.

---

## 35. Version Parsing — packaging (P3 — New lib)

**Files**: `cli_impl.py` (contract_version, schema_version), `config.py` (contract_schema_version_minimum), `mcp_server.py` (schema_version), `contracts/`

**Current**: String comparison for versions; no semver parsing.

**Library**: `packaging` — `Version("1.2.3")`, `parse_version()`, comparison operators.

**Recommendation**: Use `packaging.version.Version` for contract/schema version checks. Enables `v1 >= v2` correctly.

---

## 36. Exclude Patterns — pathspec (P3 — New lib)

**Files**: `governance/triggers.py` (exclude_dirs: .pytest_cache, .git, etc.), `install.py` (should_exclude)

**Current**: Hardcoded set of dir names. No .gitignore-style patterns.

**Library**: `pathspec` — `.gitignore`-compatible pattern matching; `PathSpec.from_lines("gitwildmatch", lines)`.

**Recommendation**: Load `.gitignore` or config exclude patterns; use pathspec for matching. Enables user-configurable excludes.

---

## 37. Platform Dirs — platformdirs (P3 — New lib)

**Files**: `config.py` (~/.cache/thegent, ~/.factory), `install.py`, various Path("~/. ...")

**Current**: Manual `Path("~/.cache/thegent").expanduser()`; platform-specific paths hardcoded.

**Library**: `platformdirs` — XDG on Linux, proper macOS/Linux/Windows dirs; `user_cache_dir("thegent")`.

**Recommendation**: Use `platformdirs.user_cache_dir("thegent")` for cache; `user_data_dir` for config. Respects XDG on Linux.

---

## 38. Human-Readable Output — humanize (P3 — New lib)

**Files**: CLI output, progress, cost displays, duration formatting.

**Current**: Manual formatting for bytes, durations, numbers (e.g. "1.2 GB", "3h 5m").

**Library**: `humanize` — `humanize.naturalsize()`, `humanize.precisedelta()`, `humanize.intcomma()`.

**Recommendation**: Use for cost/budget displays, file sizes, elapsed time. Improves UX.

---

## 39. Polish — Rich Progress & Spinners (P2 — Enhancement)

**Files**: `cli.py`, `cli_impl.py`, `mcp_server.py`, `install.py`, long-running commands

**Current**: Rich tables, console.print; some long ops (scrape, install, mcp prune) have no progress feedback.

**Recommendation**: Use `rich.progress.Progress` with `SpinnerColumn`, `TextColumn`, `BarColumn` for:

- Model scraping, catalog refresh
- Install/sync operations
- MCP prune, discovery scan
- DAG run progress

**Library**: rich (already in deps). `with Progress(...) as p: p.add_task(...)`.

**Effort**: 2–4 hrs. Wrap key long-running paths.

---

## 40. Intuitiveness — CLI UX (P2 — Enhancement)

**Files**: `main.py`, `cli.py`, typer app

**Current**: typer with good help; no shell completion by default; some validation errors are generic.

**Recommendations**:

1. **Shell completion**: Document `thegent --install-completion` (typer built-in); add to README.
2. **typer callbacks**: Use `@app.callback()` for global validation (e.g. check settings, cwd) before subcommands.
3. **Rich help**: Consider `typer-rich` for Markdown help, panels in `--help`.
4. **Interactive prompts**: For destructive ops, use `rich.prompt.Confirm` or `questionary` instead of bare `--yes`.

**Libraries**: typer-rich (optional), questionary (optional).

---

## 41. Robustness — Error Handling & Validation (P2 — Enhancement)

**Files**: 80+ with try/except; config.py, contracts/validation.py, pydantic models

**Current**: Broad `except Exception` in places; pydantic ValidationError sometimes surfaced raw; retry logic scattered.

**Recommendations**:

1. **Exception groups** (Python 3.11+): Use `except*` for concurrent failure aggregation where applicable.
2. **Structured errors**: Create `thegent.errors` module with `ThegentError`, `ValidationError`, `RetryableError`; map pydantic errors to user-friendly messages.
3. **Retry consistency**: Ensure all retry paths use tenacity; remove custom `_backoff_delay` where tenacity suffices.
4. **Validation messages**: Use pydantic `model_config = ConfigDict(...)` and custom `field_validator` messages for clearer CLI output.

**Effort**: 4–6 hrs. Incremental.

---

## 42. Extensibility — Plugin System (P3 — Enhancement)

**Files**: `sitback_plugins.py`, `governance/`, `contracts/registry.py`, `capability_registry.py`

**Current**: Custom `SitbackPluginRegistry`; file-based discovery from `~/.claude/sitback-plugins/`; manual `register_widget`, `register_startup_step`.

**Recommendations**:

1. **entry_points**: Add `[project.entry-points."thegent.plugins"]` in pyproject.toml; use `importlib.metadata.entry_points(group="thegent.plugins")` for discovery. Third-party packages can register without file drops.
2. **pluggy**: If plugin lifecycle (init, teardown, hooks) grows, consider `pluggy` for a formal hook spec.
3. **Keep file-based**: For ad-hoc/user plugins (no package install), keep `~/.claude/sitback-plugins/` as fallback.

**Libraries**: importlib.metadata (stdlib), pluggy (optional).

---

## 43. Enhancements — New Features (P3)

| Feature                   | Library                 | Purpose                                                          |
| ------------------------- | ----------------------- | ---------------------------------------------------------------- |
| **Interactive TUI**       | textual                 | Full TUI for dashboard, queue, runs (alternative to rich panels) |
| **Interactive prompts**   | questionary             | Autocomplete, multi-select, fuzzy for CLI prompts                |
| **Richer typer help**     | typer-rich              | Markdown help, panels, examples in `--help`                      |
| **Config validation**     | pydantic (already used) | Extend `validate_setup()`; add `--validate-config` command       |
| **Health check endpoint** | —                       | Already have; add `/ready`, `/live` for k8s                      |
| **Metrics export**        | prometheus-client       | Optional `/metrics` for cost, latency, queue depth               |
| **Audit log**             | structlog + JSON        | Structured audit trail for compliance                            |

---

## 44. Summary Table — File-Level (Expanded)

| File                                | Custom Implementation                   | Library                                 | Priority   |
| ----------------------------------- | --------------------------------------- | --------------------------------------- | ---------- |
| cli_impl.py                         | \_CWD_CACHE, EAGAIN retry, DAG backoff  | cachetools.TTLCache, tenacity, settings | P1, P2     |
| queue/storage.py                    | Manual JSONL (PromptQueue)              | jsonlines                               | P2         |
| execution.py                        | DeferralQueue, EscalationQueue, urllib  | jsonlines, httpx, orjson                | P1, P2, P3 |
| ------                              | ----------------------                  | ---------                               | ---------- |
| models/scrapers.py                  | urllib, custom cache                    | httpx, diskcache                        | P1, P2     |
| agents/cliproxy_manager.py          | urllib, os.environ                      | httpx, settings                         | P1, P2     |
| agents/cursor_api_runner.py         | urllib, ANSI strip                      | httpx, rich                             | P1, P2     |
| execution.py                        | urllib                                  | httpx                                   | P1         |
| mcp_manage.py                       | urllib                                  | httpx                                   | P1         |
| clode_main.py                       | urllib                                  | httpx                                   | P1         |
| routing/alerting.py                 | urllib                                  | httpx                                   | P1         |
| governance/triggers.py              | os.walk polling, debounce, exclude_dirs | watchdog, pathspec                      | P1, P3     |
| agents/loop_controller.py           | Manual retry loop                       | tenacity                                | P1         |
| agents/codex_proxy.py               | ANSI strip, os.environ                  | rich, settings                          | P2         |
| agents/direct_agents.py             | ANSI strip                              | rich                                    | P2         |
| agents/droid.py                     | ANSI strip                              | rich                                    | P2         |
| parser.py                           | ANSI strip                              | rich                                    | P2         |
| tools/cache.py                      | ETag cache, md5                         | cachetools/diskcache, sha256            | P2         |
| models/speed_values.py              | TTL cache                               | cachetools                              | P2         |
| models/quality_values.py            | TTL cache                               | cachetools                              | P2         |
| models/catalog.py                   | Route cache                             | cachetools                              | P2         |
| orchestration/load_based_limits.py  | FD/mem/load sampling                    | psutil                                  | P2         |
| agents/resilience.py                | ToolCircuitBreaker                      | pybreaker                               | P2         |
| discovery.py                        | ps, /proc                               | psutil                                  | P2         |
| contracts/parser.py                 | XML regex extractor                     | defusedxml (optional)                   | P2         |
| tools/xml_repair.py                 | XML repair                              | lxml recover (optional)                 | P2         |
| mcp_tools_modes.py                  | Custom \_slugify                        | python-slugify                          | P3         |
| tools/human.py                      | Manual JSONL append                     | jsonlines                               | P3         |
| output_parser.py                    | Manual JSONL, regex                     | jsonlines, parse (optional)             | P3         |
| cli.py                              | os.environ, uuid hex                    | settings, shortuuid (optional)          | P2, P3     |
| dex_main.py                         | os.environ                              | settings                                | P2         |
| mcp_server.py                       | os.environ                              | settings                                | P2         |
| governance/constitution.py          | PyYAML                                  | ruamel.yaml                             | P2         |
| execution.py                        | stdlib json (55 uses)                   | orjson (hot path)                       | P3         |
| mcp_server.py                       | stdlib json (68 uses)                   | orjson (hot path)                       | P3         |
| governance/triggers.py              | argparse                                | typer                                   | P3         |
| mcp_manage.py                       | tomlkit (no dep)                        | add tomlkit to deps                     | P2         |
| governance/teammates.py             | PyYAML                                  | ruamel.yaml                             | P2         |
| scripts/start_proxy_with_adapter.py | PyYAML                                  | ruamel.yaml                             | P2         |
| install.py                          | should_exclude, Path expand             | pathspec, platformdirs                  | P3         |
| config.py                           | ~/.cache, ~/.factory paths              | platformdirs                            | P3         |
| sitback_plugins.py                  | Custom plugin registry                  | entry_points, pluggy                    | P3         |
| main.py                             | typer app                               | typer callbacks, shell completion       | P2         |
| contracts/validation.py             | Validation errors                       | thegent.errors, user-friendly messages  | P2         |

---

## 45. Implementation Roadmap (Expanded)

| Phase | Task                                                                             | Effort  |
| ----- | -------------------------------------------------------------------------------- | ------- |
| 1     | Replace urllib with httpx (7 files)                                              | 2–3 hrs |
| 2     | Migrate retry loops to tenacity                                                  | 4–6 hrs |
| 3     | Replace WatchdogTrigger with watchdog                                            | 2–4 hrs |
| 4     | Consolidate ANSI strip → rich.strip_control_codes                                | 1 hr    |
| 5     | Introduce cachetools for speed/quality/catalog                                   | 2–3 hrs |
| 6     | Replace scrapers cache with diskcache                                            | 1 hr    |
| 7     | Add psutil for load_based_limits, discovery                                      | 2–3 hrs |
| 8     | Evaluate pybreaker for circuit breaker                                           | 1–2 hrs |
| 9     | Unify md5→sha256 in cache.py                                                     | 0.5 hr  |
| 10    | Consolidate os.environ → ThegentSettings                                         | 2–3 hrs |
| 11    | Audit subprocess + add shlex.quote where needed                                  | 1–2 hrs |
| 12    | Replace \_slugify with python-slugify                                            | 0.5 hr  |
| 13    | Add jsonlines for JSONL I/O                                                      | 1 hr    |
| 14    | (Optional) structlog migration                                                   | 4–8 hrs |
| 15    | (Optional) hypothesis for parser tests                                           | 2–4 hrs |
| 16    | (Optional) more-itertools for repeated patterns                                  | 1–2 hrs |
| 17    | Replace PyYAML with ruamel.yaml (15+ files)                                      | 2–3 hrs |
| 18    | Add orjson; migrate execution, mcp_server hot paths                              | 4–6 hrs |
| 19    | Add tomlkit to pyproject.toml                                                    | 0.5 hr  |
| 20    | (Optional) Migrate argparse scripts to typer                                     | 2–4 hrs |
| 21    | Replace \_CWD_CACHE with cachetools.TTLCache                                     | 0.5 hr  |
| 22    | Replace queue JSONL (PromptQueue, DeferralQueue, EscalationQueue) with jsonlines | 2–3 hrs |
| 23    | (Optional) Add packaging for version parsing                                     | 1–2 hrs |
| 24    | (Optional) Add pathspec for exclude patterns                                     | 1–2 hrs |
| 25    | (Optional) Add platformdirs for cache/config dirs                                | 1–2 hrs |
| 26    | (Optional) Add humanize for CLI output                                           | 1 hr    |
| 27    | Add rich.Progress/Spinner for long-running ops                                   | 2–4 hrs |
| 28    | Document shell completion; add typer callbacks                                   | 1–2 hrs |
| 29    | Create thegent.errors; improve ValidationError handling                          | 2–3 hrs |
| 30    | Add entry_points for plugin discovery                                            | 2–3 hrs |
| 31    | (Optional) typer-rich, questionary for CLI polish                                | 2–4 hrs |

---

## 46. Proposed New Dependencies (Summary)

| Library           | Purpose                                              | Add?              |
| ----------------- | ---------------------------------------------------- | ----------------- |
| cachetools        | TTL in-memory cache                                  | Yes               |
| diskcache         | File-based cache                                     | Yes               |
| watchdog          | File system events                                   | Yes               |
| psutil            | Process/resource monitoring                          | Yes               |
| pybreaker         | Circuit breaker                                      | Yes               |
| tomlkit           | TOML round-trip (mcp_manage)                         | Yes (add to deps) |
| ruamel.yaml       | Replace PyYAML; preserve comments                    | Yes               |
| orjson            | Fast JSON (replace stdlib in hot paths)              | Optional          |
| python-slugify    | Slug generation                                      | Optional          |
| jsonlines         | JSONL read/write                                     | Optional          |
| parse             | Format string parsing                                | Optional          |
| shortuuid         | Short URL-safe IDs                                   | Optional          |
| hypothesis        | Property-based testing                               | Dev optional      |
| more-itertools    | Iteration utilities                                  | Optional          |
| structlog         | Structured logging                                   | Optional          |
| packaging         | Version parsing (semver)                             | Optional          |
| pathspec          | .gitignore-style exclude patterns                    | Optional          |
| platformdirs      | XDG / platform cache/config dirs                     | Optional          |
| humanize          | Human-readable bytes, durations                      | Optional          |
| typer-rich        | Richer typer --help (Markdown, panels)               | Optional          |
| questionary       | Interactive CLI prompts (autocomplete, multi-select) | Optional          |
| pluggy            | Plugin hook system (extensibility)                   | Optional          |
| textual           | Full TUI (dashboard, queue)                          | Optional          |
| prometheus-client | Metrics export (/metrics)                            | Optional          |

---

## 47. Failure Modes & Error Handling

### 47.1 Failure Modes

| Failure Mode                | Impact                   | Mitigation                                                |
| --------------------------- | ------------------------ | --------------------------------------------------------- |
| **Library incompatibility** | Breaking changes         | Version pinning, compatibility testing, gradual migration |
| **Library unmaintained**    | Security vulnerabilities | Monitor maintenance status, have fallback plan            |
| **Performance regression**  | Slower than custom       | Benchmark before/after, feature flags for rollback        |
| **API differences**         | Integration issues       | Thin wrapper layer, adapter pattern, comprehensive tests  |
| **Dependency conflicts**    | Build failures           | Dependency resolution, virtual environments, lock files   |

### 47.2 Error Handling Strategy

**Migration Pattern:**

```python
# Feature flag for gradual migration
USE_NEW_LIBRARY = os.getenv("THGENT_USE_HTTPX", "0") == "1"

if USE_NEW_LIBRARY:
    try:
        import httpx

        client = httpx.Client()
    except ImportError:
        logger.warning("httpx not available, falling back to urllib")
        USE_NEW_LIBRARY = False

if not USE_NEW_LIBRARY:
    # Fallback to existing implementation
    import urllib.request
    # ... existing code
```

**Validation:**

- Pre-migration: Compatibility testing, performance benchmarking
- Post-migration: Integration tests, monitoring, rollback plan
- Performance: Monitor latency, error rates, resource usage

---

## 48. References

- [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./LIBRARY_FIRST_AUDIT_AND_PLAN.md)
- [TENACITY_RETRY_AUDIT_PLAN.md](./TENACITY_RETRY_AUDIT_PLAN.md)
- [anti-patterns.md](../guides/anti-patterns.md)
- [FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md) — shell + Py/TS/Go + BKM + lib consolidation
- PyPI: httpx, tenacity, watchdog, cachetools, diskcache, psutil, pybreaker, structlog, defusedxml, lxml, python-slugify, jsonlines, parse, shortuuid, ruamel.yaml, orjson, tomlkit, hypothesis, more-itertools, packaging, pathspec, platformdirs, humanize, typer-rich, questionary, pluggy, textual, prometheus-client

---

## 49. See Also

- [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) - **Consolidated migration plan (recommended)**
- [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./LIBRARY_FIRST_AUDIT_AND_PLAN.md) - Original audit
- [LIBRARY_REPLACEMENT_PHASE_DWBS.md](./LIBRARY_REPLACEMENT_PHASE_DWBS.md) - Phase breakdown
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (9 BACKLOG items)
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure

---

## 48. Anti-Sprawl Extension (Port & Consolidation)

**Purpose:** Avoid custom impl sprawl by checking native thegent crates, stdlib, existing deps, and libraries _before_ adding new custom code. Aligns with [FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md) §10.

### 48.1 Before Adding Custom Impl — Checklist

1. **Existing thegent native (Rust/BKM)?**
   thegent-parser, thegent-crypto, thegent-git, thegent-resources, thegent-hooks, thegent-shims, thegent-discovery, thegent-watcher, hook-dispatcher. If the capability exists there, call it (PyO3, subprocess JSON, or CLI).

2. **Python stdlib sufficient?**
   json, hashlib, subprocess, pathlib, sqlite3, graphlib, argparse, logging. Prefer stdlib over a new dependency when it’s fit for purpose.

3. **Already in pyproject.toml?**
   pydantic, httpx, tenacity, rich, typer, orjson, etc. Reuse before adding another lib.

4. **Mature library (PyPI / crates.io)?**
   See §1 (Replacements), §46 (Proposed New Dependencies). Prefer library + thin wrapper over full custom (LIBRARY_FIRST_AUDIT_AND_PLAN).

5. **Shell vs Rust?**
   If the logic lives in hooks or install shims, consider thegent-hooks or thegent-shims instead of more shell (FULL_SHELL_TO_RUST §2–§5).

6. **Document exception.**
   If custom code is still added, add a short comment: “No suitable lib/crate; see LIBRARY_FIRST_AUDIT / FULL_SHELL_TO_RUST.”

### 48.2 Consolidation Matrix (Capability → Preferred Source)

| Capability                             | Prefer                                        | Avoid                                |
| -------------------------------------- | --------------------------------------------- | ------------------------------------ |
| Retry/backoff                          | tenacity                                      | Manual for/while + sleep             |
| Cache (TTL, file)                      | cachetools, diskcache, or thegent-hooks cache | Custom dict + mtime                  |
| HTTP client                            | httpx                                         | urllib.request                       |
| Git metadata                           | thegent-git, thegent-hooks git                | subprocess.run(["git", ...])         |
| XML/JSONL parse (hot path)             | thegent-parser (BKM-02)                       | Many re.compile + hand-written loops |
| Crypto (sign/verify/hash)              | thegent-crypto (BKM-03)                       | hashlib + custom HMAC in hot path    |
| Resource sampling                      | thegent-resources (BKM-01)                    | lsof, vm_stat subprocess             |
| File watching                          | watchdog or thegent-watcher                   | os.walk polling                      |
| Circuit breaker                        | pybreaker or BKM-05 State-SHM                 | Custom failure list + timer          |
| Hook init/cache/changed-files          | thegent-hooks                                 | common.sh sourcing                   |
| PATH / tool resolution                 | thegent-tool-detect, thegent-discovery        | command -v in shell                  |
| Install shims (git, grep, find, agent) | thegent-shims (Rust)                          | Bash scripts in install.py           |
| ANSI strip                             | rich.strip_control_codes                      | re.sub(r"\x1b\[...") duplicated      |
| YAML round-trip                        | ruamel.yaml                                   | PyYAML where comments matter         |
| ID generation                          | shortuuid/nanoid or stdlib uuid               | uuid4().hex[:8] scattered            |

### 48.3 Governance

- **CLAUDE.md / CONTRIBUTING:** Add “Library-first & anti-sprawl” bullet: before new custom impl, check §48.1 and FULL_SHELL_TO_RUST §10.
- **Code review:** For new modules that implement retry, cache, HTTP, git, parse, or shell-like behavior, ask: “Is there a crate/lib listed in §48.2 or in the full port plan?”

---

## 50. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 48:** Anti-Sprawl Extension (Port & Consolidation)
   - Before adding custom impl checklist
   - Capability → Preferred Source matrix
   - Governance rules for code review

2. **Enhanced Section 45:** Expanded implementation roadmap with 31 tasks
3. **Enhanced Section 46:** Added proposed new dependencies summary table

### Cross-References Added

- FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md
- LIBRARY_REPLACEMENT_CONSOLIDATED.md
- WORK_STREAM.md

### Practical Additions

- Comprehensive library replacement checklist
- Failure modes and error handling strategies
- Anti-sprawl governance rules

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (9 BACKLOG items in consolidated doc)
- [LIBRARY_REPLACEMENT_CONSOLIDATED.md](./LIBRARY_REPLACEMENT_CONSOLIDATED.md) - Consolidated migration plan
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure
