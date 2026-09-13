### [WL-7450]

**Title:** Bound watcher SHM bootstrap failures with typed setup diagnostics
**Source:** [thegent/src/thegent/native/watcher_daemon.py:100]
**Acceptance checklist:**

- [ ] Replace broad watcher SHM bootstrap exception handling with explicit import, path-create, and interface-init failure branches.
- [ ] Preserve current `None` return contract when SHM support is unavailable.
- [ ] Add tests for successful SHM bootstrap, missing native module, and SHM interface initialization failure.
      **Notes:** Line 100 currently collapses all SHM bootstrap faults into one debug message.

### [WL-7451]

**Title:** Preserve watcher callback failure taxonomy before breaker recording attempts
**Source:** [thegent/src/thegent/native/watcher_daemon.py:207]
**Acceptance checklist:**

- [ ] Replace broad callback wrapper handling with explicit callback-runtime and callback-contract failure categories.
- [ ] Preserve current non-crashing callback dispatch behavior.
- [ ] Add tests for successful callback execution, callback exception reporting, and continued event dispatch after failures.
      **Notes:** The catch-all at line 207 masks callback failure classes that should remain distinguishable in diagnostics.

### [WL-7452]

**Title:** Separate breaker record-failure write faults from callback error reporting in watcher dispatch
**Source:** [thegent/src/thegent/native/watcher_daemon.py:217]
**Acceptance checklist:**

- [ ] Replace broad breaker write exception handling with explicit SHM write, state-transition, and transport failure branches.
- [ ] Preserve current best-effort breaker update semantics after callback failures.
- [ ] Add tests for successful breaker writes, SHM write failure, and fallback logging behavior.
      **Notes:** Line 217 currently swallows all breaker write faults into one debug path.

### [WL-7453]

**Title:** Classify watcher observer startup failures into actionable initialization stages
**Source:** [thegent/src/thegent/native/watcher_daemon.py:289]
**Acceptance checklist:**

- [ ] Replace broad observer startup exception handling with explicit observer-start, cleanup-thread, and state-transition failure categories.
- [ ] Preserve current failure propagation semantics when startup cannot complete.
- [ ] Add tests for successful startup, observer start failure, and cleanup thread initialization failure.
      **Notes:** The catch-all at line 289 conflates distinct startup-stage failures in watcher lifecycle management.

### [WL-7454]

**Title:** Preserve watcher shutdown stop-stage fault context without obscuring stop progression
**Source:** [thegent/src/thegent/native/watcher_daemon.py:312]
**Acceptance checklist:**

- [ ] Replace broad observer stop exception handling with explicit stop-signal and observer-state failure branches.
- [ ] Preserve current shutdown continuation behavior after stop errors.
- [ ] Add tests for normal shutdown, observer stop exception, and post-stop state consistency.
      **Notes:** Line 312 currently emits a generic warning that loses stop-stage root-cause detail.

### [WL-7455]

**Title:** Bound native SHM interface initialization failures in breaker store setup
**Source:** [thegent/src/thegent/native/state_shm.py:212]
**Acceptance checklist:**

- [ ] Replace broad native SHM initialization exception handling with explicit directory-create, interface-bind, and permission failure branches.
- [ ] Preserve fallback store activation when native SHM setup fails.
- [ ] Add tests for successful native init, parent directory creation failure, and interface constructor errors.
      **Notes:** The broad handler at line 212 hides which SHM setup stage failed before fallback activation.

### [WL-7456]

**Title:** Distinguish native breaker write failures from fallback handoff paths in record_failure
**Source:** [thegent/src/thegent/native/state_shm.py:237]
**Acceptance checklist:**

- [ ] Replace broad native `record_failure` exception handling with explicit argument-shape, IPC-write, and runtime failure categories.
- [ ] Preserve fallback write behavior when native writes fail.
- [ ] Add tests for successful native writes, native write failure, and fallback path invocation.
      **Notes:** Line 237 currently merges all native write errors into one warning before fallback.

### [WL-7457]

**Title:** Narrow config file read failures in setup checks to parse and IO-specific diagnostics
**Source:** [thegent/src/thegent/doctor_setup_checks.py:72]
**Acceptance checklist:**

- [ ] Replace broad CLIProxy config read exception handling with explicit file IO, YAML decode, and schema-shape failure categories.
- [ ] Preserve current fail status semantics for invalid or unreadable config.
- [ ] Add tests for valid config load, malformed YAML, and permission-denied reads.
      **Notes:** The catch-all at line 72 makes it harder to separate parse regressions from filesystem failures.

### [WL-7458]

**Title:** Preserve MCP bootstrap failure attribution when automatic startup fails
**Source:** [thegent/src/thegent/doctor_setup_checks.py:157]
**Acceptance checklist:**

- [ ] Replace broad MCP auto-start exception handling with explicit import, invocation, and polling-stage failure branches.
- [ ] Preserve current boolean return contract for startup success and failure.
- [ ] Add tests for successful startup, `mcp_up` invocation failure, and retry-loop exception paths.
      **Notes:** Line 157 currently collapses MCP bootstrap failures into one generic startup error.

### [WL-7459]

**Title:** Differentiate summary run timestamp parse faults from unrelated run-shape errors
**Source:** [thegent/src/thegent/summary.py:318]
**Acceptance checklist:**

- [ ] Replace broad run-filter parse exception handling with explicit timestamp parse and missing-field failure categories.
- [ ] Preserve continuation behavior across valid runs when one run record is malformed.
- [ ] Add tests for valid run filtering, malformed timestamps, and missing `started_at_utc` field handling.
      **Notes:** The suppression at line 318 can silently hide malformed run records during period summaries.
