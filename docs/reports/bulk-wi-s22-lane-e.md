### [WL-6660]

**Title:** Surface native parser failures in `_strip_think_blocks` instead of silently falling back
**Source:** [thegent/src/thegent/output_parser.py:277]
**Acceptance checklist:**

- [ ] Capture parser exception metadata (exception type + message) in debug logs when native strip fails.
- [ ] Keep regex fallback behavior but expose a counter/flag so operators can detect repeated native-path failures.
- [ ] Add tests that simulate native parser exceptions and assert both fallback output correctness and diagnostics emission.
      **Notes:**
- The current `except Exception: pass` hides parser regressions and makes fallback usage invisible.

### [WL-6661]

**Title:** Implement structured forwarding for non-heartbeat worker output in `_forward_logs`
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:142]
**Acceptance checklist:**

- [ ] Route non-heartbeat stdout lines into runtime-scoped logs/telemetry instead of dropping them.
- [ ] Parse and persist stderr payloads with runtime identity and timestamp context.
- [ ] Add async tests proving heartbeat updates still work while regular logs and errors are retained.
      **Notes:**
- Both non-heartbeat stdout and collected stderr are currently discarded via `pass` branches.

### [WL-6662]

**Title:** Report tmux pane probe failures in `send_keepalive_enter` with actionable diagnostics
**Source:** [thegent/src/thegent/infra/terminal_keepalive.py:217]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression around `tmux display-message` with targeted exception handling.
- [ ] Emit debug diagnostics that distinguish timeout, missing tmux binary, and command failure return codes.
- [ ] Add tests for probe failure paths to verify keepalive returns remain safe while reasons are observable.
      **Notes:**
- Silent probe failures currently collapse multiple root causes into a generic keepalive miss.

### [WL-6663]

**Title:** Remove broad exception swallow in `_get_configured_providers_from_cliproxy`
**Source:** [thegent/src/thegent/doctor.py:530]
**Acceptance checklist:**

- [ ] Narrow exception handling to expected config parsing/runtime errors and preserve traceback context in diagnostics.
- [ ] Return partial provider discoveries with explicit warning metadata instead of silently returning incomplete sets.
- [ ] Add unit tests for malformed config, missing files, and provider credential edge cases.
      **Notes:**
- The current blanket `except` can hide provider-detection failures and under-report configured integrations.

### [WL-6664]

**Title:** Preserve deadline monitor unregister failures with structured warning paths
**Source:** [thegent/src/thegent/execution.py:448]
**Acceptance checklist:**

- [ ] Replace silent `except` around `get_deadline_monitor().unregister(...)` with warning-level diagnostics.
- [ ] Include `owner`/`run_id` context in emitted diagnostics to support cleanup investigations.
- [ ] Add tests covering missing monitor module and unregister runtime failures without breaking run teardown.
      **Notes:**
- Swallowing unregister exceptions can leave hidden deadline artifacts and make resource accounting drift hard to debug.

### [WL-6665]

**Title:** Harden stale lockfile cleanup path in `ensure_shared_mcp_server`
**Source:** [thegent/src/thegent/shared_mcp_manager.py:64]
**Acceptance checklist:**

- [ ] Guard lockfile parse/unlink flows with explicit file-not-found and JSON corruption handling.
- [ ] Avoid unconditional `lockfile.unlink()` on generic exceptions; gate deletes behind validated stale-state checks.
- [ ] Add tests for corrupted lockfiles, concurrent deletion races, and permission-denied cleanup behavior.
      **Notes:**
- Generic exception cleanup currently risks masking root causes and may delete lockfiles without provenance checks.

### [WL-6666]

**Title:** Surface prompt queue sync ingestion failures instead of returning zero silently
**Source:** [thegent/src/thegent/planning/workstream_db.py:451]
**Acceptance checklist:**

- [ ] Replace `except Exception: return 0` with structured error reporting that includes queue path and failure phase.
- [ ] Preserve successfully upserted counts while reporting partial-sync failures to callers.
- [ ] Add tests for import failures, malformed queue records, and mixed-success ingestion runs.
      **Notes:**
- Returning `0` on any exception conflates “empty queue” with “sync failed,” obscuring backlog visibility.

### [WL-6667]

**Title:** Differentiate worktree listing failures from valid empty state in `list_worktrees`
**Source:** [thegent/src/thegent/infra/worktree.py:79]
**Acceptance checklist:**

- [ ] Return structured result metadata (success/error) so callers can distinguish command failure from zero worktrees.
- [ ] Capture stderr/exit code from `git worktree list --porcelain` when parsing or invocation fails.
- [ ] Add tests for git-not-found, nonzero exit, and malformed porcelain output handling.
      **Notes:**
- The current `return []` on exceptions hides operational failures as if no worktrees exist.

### [WL-6668]

**Title:** Replace silent JSON decode fallback in `transform_openrouter_models`
**Source:** [thegent/src/thegent/cliproxy_models_transform.py:131]
**Acceptance checklist:**

- [ ] Emit parse/type failure diagnostics with bounded payload context before returning failure.
- [ ] Return a typed error object (or Result variant) so callers can respond explicitly to transform failures.
- [ ] Add tests for malformed JSON, schema drift, and mixed valid/invalid model entries.
      **Notes:**
- The current `except (json.JSONDecodeError, TypeError): pass` suppresses why transform output becomes `None`.

### [WL-6669]

**Title:** Add resilient context-history failure reporting in `_record_context_history`
**Source:** [thegent/src/thegent/infra/fast_subprocess.py:45]
**Acceptance checklist:**

- [ ] Keep non-blocking semantics but log structured history-write failures with command/task identifiers.
- [ ] Track dropped history-write counts for observability without impacting subprocess execution paths.
- [ ] Add tests confirming command execution succeeds while history failures are externally visible.
      **Notes:**
- Silent suppression prevents operators from detecting persistent history-capture degradation.
