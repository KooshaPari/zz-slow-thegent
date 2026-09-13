### [WL-7430]

**Title:** Narrow conversation markdown dump error handling to explicit serialization and file-write failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance checklist:**

- [ ] Replace catch-all markdown dump exception handling with explicit `to_markdown` serialization and file-write failure branches.
- [ ] Preserve current logging detail with dump path context for each failure class.
- [ ] Add tests for successful markdown dump, serialization failure, and write-permission failure.
      **Notes:** The current broad handler conflates formatting failures with filesystem write errors.

### [WL-7431]

**Title:** Split JSON conversation dump failures into encode-time and persistence-time categories
**Source:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance checklist:**

- [ ] Replace broad JSON dump exception handling with explicit JSON encoding and write-to-disk failure branches.
- [ ] Preserve UTC timestamped filename behavior and existing success-path logging.
- [ ] Add tests for successful JSON dump, non-serializable payloads, and write I/O failures.
      **Notes:** A single exception path hides whether failure occurred before or during file persistence.

### [WL-7432]

**Title:** Isolate per-handler A2A routing failures and surface deterministic failure diagnostics
**Source:** [thegent/src/thegent/protocols/a2a.py:166]
**Acceptance checklist:**

- [ ] Replace untyped handler exception catch in router loop with explicit failure classification and structured error metadata.
- [ ] Preserve best-effort continuation so one failing handler does not block other registered handlers.
- [ ] Add tests for successful multi-handler routing and single-handler runtime failure isolation.
      **Notes:** Current blanket handling logs exceptions but does not distinguish handler contract errors from transient runtime faults.

### [WL-7433]

**Title:** Classify Nix flake inspection failures instead of collapsing checks to generic permission errors
**Source:** [thegent/src/thegent/doctor_shell_nix.py:205]
**Acceptance checklist:**

- [ ] Replace broad flake check exception handling with explicit `PermissionError` and `OSError` branches.
- [ ] Preserve non-Nix environments passing without requiring `flake.nix`.
- [ ] Add tests for existing `flake.nix`, missing `flake.nix` with Nix installed, and permission-denied reads.
      **Notes:** Generic failure messaging obscures actionable remediation for filesystem versus environment problems.

### [WL-7434]

**Title:** Remove silent `ps` shim read suppression and emit explicit environment-check failures
**Source:** [thegent/src/thegent/doctor.py:333]
**Acceptance checklist:**

- [ ] Replace silent `OSError` suppression around `~/.local/bin/ps` reads with explicit warning/failure check results.
- [ ] Preserve harmful-shim detection semantics when file reads succeed.
- [ ] Add tests for readable harmful shim, unreadable shim file, and absent shim file behavior.
      **Notes:** The current `pass` drops diagnostics when shim inspection fails, reducing observability during shell hang triage.

### [WL-7435]

**Title:** Surface shim version-probe failure causes instead of silently degrading detail output
**Source:** [thegent/src/thegent/doctor.py:393]
**Acceptance checklist:**

- [ ] Replace silent subprocess/version probe suppression with explicit typed failure reporting per shim.
- [ ] Preserve successful version enrichment when tool binaries respond correctly.
- [ ] Add tests for successful version read, command timeout, and missing binary scenarios.
      **Notes:** Hidden probe failures currently appear as generic "binary available" results, masking timeout and execution faults.

### [WL-7436]

**Title:** Replace blanket process-discovery suppression in shared MCP startup with typed PID resolution errors
**Source:** [thegent/src/thegent/shared_mcp_manager.py:136]
**Acceptance checklist:**

- [ ] Replace broad exception catch around `pgrep` parsing with explicit subprocess and parse error branches.
- [ ] Preserve lockfile creation even when PID discovery cannot resolve a process-compose PID.
- [ ] Add tests for valid PID discovery, empty `pgrep` output, and malformed PID output.
      **Notes:** Current `except Exception` fallback to `None` obscures whether discovery failed due to tooling absence or bad output.

### [WL-7437]

**Title:** Differentiate MCP startup dependency failures from runtime startup failures in shared manager
**Source:** [thegent/src/thegent/shared_mcp_manager.py:154]
**Acceptance checklist:**

- [ ] Replace broad startup exception wrapping with explicit categories for import/config, spawn, and URL-resolution failures.
- [ ] Preserve clear error propagation to callers without introducing fallback URLs in failure paths.
- [ ] Add tests for successful startup, `mcp_up()` failure, and post-start URL resolution failure.
      **Notes:** The current catch-all error message reduces precision for startup incident diagnosis.

### [WL-7438]

**Title:** Promote cliproxy cost-tracking failures from debug-only suppression to explicit telemetry outcomes
**Source:** [thegent/src/thegent/cliproxy_stream_state.py:228]
**Acceptance checklist:**

- [ ] Replace blanket cost-tracker update suppression with explicit import and runtime tracking failure classes.
- [ ] Preserve response streaming behavior when cost tracking fails.
- [ ] Add tests for successful cost tracking, missing tracker dependency, and tracker runtime exceptions.
      **Notes:** Current best-effort suppression hides budget-accounting gaps that should remain observable.

### [WL-7439]

**Title:** Eliminate silent provider-credential discovery suppression in doctor provider configuration scan
**Source:** [thegent/src/thegent/doctor.py:531]
**Acceptance checklist:**

- [ ] Replace broad exception suppression in configured-provider extraction with explicit error reporting for settings access failures.
- [ ] Preserve deterministic provider list population when credentials are present.
- [ ] Add tests for valid configured providers, missing settings object fields, and credential-read exceptions.
      **Notes:** Returning partial or empty provider sets silently can mislead downstream provider health checks.
