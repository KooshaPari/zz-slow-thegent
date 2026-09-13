### [WL-8050]

**Title:** Emit explicit diagnostics and failure mode signals in WSL detection and path translation fallbacks
**Source:** [thegent/src/thegent/infra/wsl_interop.py:35]
**Acceptance checklist:**

- [ ] Distinguish non-WSL hosts from translation command failures by returning structured failure metadata from `_detect_wsl` and `_wslpath` fallback paths.
- [ ] Update `to_wsl_path` and `to_windows_path` to include the mapped method and failure reason in a structured debug payload while still returning deterministic output on hard failures.
- [ ] Add tests covering Linux non-WSL, WSL with missing `wslpath`, and malformed path conversion inputs.
      **Notes:** Current broad `except` blocks treat all errors as “not WSL,” masking actionable misconfiguration and making path issues difficult to triage.

### [WL-8051]

**Title:** Report partial file-tree size failures instead of silently ignoring inaccessible entries
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:205]
**Acceptance checklist:**

- [ ] Introduce a result object (or companion API) from directory-size traversal that captures `total_bytes` and `skip_count` with `skipped_paths`.
- [ ] Keep `get_size()` returning an integer while adding an opt-in helper that preserves existing callers and exposes partial-failure diagnostics.
- [ ] Add tests for inaccessible files, permission-denied directories, and mixed-valid traversal to verify skipped-path reporting is complete.
      **Notes:** Current implementation can undercount directory sizes without surfacing why traversal stopped or skipped entries.

### [WL-8052]

**Title:** Replace silent work-stream load failures with structured parse/load error state
**Source:** [thegent/src/thegent/integration/work_stream.py:73]
**Acceptance checklist:**

- [ ] Change `_load_work_stream` to persist a typed error object in memory when parsing fails instead of silent pass-through.
- [ ] Add a `self.load_errors` field and expose it in `get_next_item`/`claim_work_item` decisions so callers can fail fast with context.
- [ ] Add tests for unreadable WORK_STREAM, malformed table rows, and corrupted section headers.
      **Notes:** Silent exception swallowing in load paths leaves consumers unaware that backlog data is stale or missing.

### [WL-8053]

**Title:** Implement durable PLAN_STATUS.md persistence and formatting-safe rewrites
**Source:** [thegent/src/thegent/integration/plan_system.py:227]
**Acceptance checklist:**

- [ ] Replace placeholder `_save_plan_status` with deterministic file rewrite preserving markdown table headers and existing non-task sections.
- [ ] Ensure task status updates are idempotent and preserve unrelated table rows and comments.
- [ ] Add regression tests for partial statuses, non-standard column ordering, and missing PLAN_STATUS.md creation.
      **Notes:** `update_task_status()` currently updates in-memory state only, so process restarts lose work-stream progress.

### [WL-8054]

**Title:** Make file descriptor and process limit discovery return explicit failure reason envelopes
**Source:** [thegent/src/thegent/infra/resource_limits.py:50]
**Acceptance checklist:**

- [ ] Add separate `get_fd_limit_info()` and `get_process_limit_info()` APIs returning both raw limit and error cause.
- [ ] Keep existing `get_fd_limit()`/`get_process_limit()` semantics for compatibility while documenting fallback behavior.
- [ ] Add tests for unsupported platforms, permission-denied limit reads, and normal restore cycles.
      **Notes:** Limit reads currently default to constants on any exception, obscuring whether resource limits were never set or were blocked at runtime.

### [WL-8055]

**Title:** Preserve process-registry signal handling diagnostics during registration failures
**Source:** [thegent/src/thegent/infra/process_registry.py:108]
**Acceptance checklist:**

- [ ] Capture and persist signal handler registration failures in registry state instead of silent ignore.
- [ ] Ensure cleanup still registers when partial setup succeeds (atexit) and reports whether SIGTERM/SIGINT hooks are active.
- [ ] Add tests for environments where signal registration is unsupported and verify cleanup fallback remains deterministic.
      **Notes:** The current pass-through fallback hides why shutdown hooks are unavailable, making orphaned process cleanup harder to diagnose.

### [WL-8056]

**Title:** Emit actionable errors when manage-devkit config load or save fails
**Source:** [thegent/src/thegent/integration/manage_devkit.py:61]
**Acceptance checklist:**

- [ ] Replace bare `except` in `_load_manage_config` with explicit OSError/import/type error handling and structured logging payloads.
- [ ] Add validation for loaded YAML structure and fail closed when required keys are invalid.
- [ ] Add tests for missing config files, malformed YAML, and write-permission failures in `_save_manage_config`.
      **Notes:** Current bare exception handling silently drops config and registration errors, which can leave integration state effectively untraceable.

### [WL-8057]

**Title:** Return keepalive failure telemetry from terminal keepalive send attempts
**Source:** [thegent/src/thegent/infra/terminal_keepalive.py:180]
**Acceptance checklist:**

- [ ] Update `_send_keepalive_to_stdin` and `_send_keepalive_via_tmux` to return structured diagnostics for each attempt (`method`, `error`, `duration_ms`).
- [ ] Expose keepalive failure counters in `TerminalKeepalive` to support circuit-breaking after repeated misses.
- [ ] Add tests covering missing stdin, unavailable `/dev/tty`, tmux timeout, and tmux command-not-found paths.
      **Notes:** Silent fallback between methods currently masks why keepalive stops during long-running sessions.

### [WL-8058]

**Title:** Replace no-op subprocess history recording with explicit failure telemetry
**Source:** [thegent/src/thegent/infra/fast_subprocess.py:45]
**Acceptance checklist:**

- [ ] Add a lightweight in-memory failure counter and structured logger for `_record_history` exceptions.
- [ ] Ensure history recording failures never block subprocess completion but always emit event-level diagnostics and metrics.
- [ ] Add tests verifying command execution succeeds when history persistence is unavailable and failure telemetry is recorded.
      **Notes:** Current bare `pass` on history write failures loses observability for execution audit gaps.

### [WL-8059]

**Title:** Include explicit error reason in MCP service status fallback path
**Source:** [thegent/src/thegent/mcp/manage.py:308]
**Acceptance checklist:**

- [ ] Expand `service_status` to return structured status details (HTTP failure, launchctl exit, missing service path).
- [ ] Keep API compatibility while surfacing machine-readable reasons for failures and the last checked endpoint.
- [ ] Add tests for HTTP connection failure, missing binary, and launchd status mismatch behavior.
      **Notes:** Blanket `except` and generic messaging currently prevents operators from distinguishing transient unreachability from service registration failure.
