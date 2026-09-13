### [WL-7470]

**Title:** Narrow CLIProxy config file-open handling to explicit I/O failure classes
**Source:** [thegent/src/thegent/doctor_setup_checks.py:53]
**Acceptance checklist:**

- [ ] Replace broad config file-open error capture with explicit filesystem and permission failure handling.
- [ ] Preserve current success behavior when config content is readable YAML.
- [ ] Add tests for missing file, unreadable file permissions, and successful config load.
      **Notes:** Line 53 begins config file reading and currently funnels downstream failures through a broad catch.

### [WL-7471]

**Title:** Split CLIProxy config parse failures from generic read errors in setup checks
**Source:** [thegent/src/thegent/doctor_setup_checks.py:72]
**Acceptance checklist:**

- [ ] Replace broad config read exception handling with distinct YAML parse and transport error branches.
- [ ] Preserve existing failure status semantics for invalid config structures.
- [ ] Add tests for malformed YAML and non-dict config payload handling.
      **Notes:** Line 72 currently catches all exceptions and emits one message shape for unrelated failure types.

### [WL-7472]

**Title:** Keep MCP preflight probe diagnostics typed before auto-start fallback
**Source:** [thegent/src/thegent/doctor_setup_checks.py:115]
**Acceptance checklist:**

- [ ] Preserve typed timeout, connect, and network classifications during preflight health probing.
- [ ] Keep automatic startup behavior unchanged when preflight fails.
- [ ] Add tests covering reachable MCP, connection refusal, and timeout preflight paths.
      **Notes:** Line 115 starts the preflight health request that feeds startup decisioning.

### [WL-7473]

**Title:** Isolate MCP bootstrap import/start execution failures from readiness loop outcomes
**Source:** [thegent/src/thegent/doctor_setup_checks.py:129]
**Acceptance checklist:**

- [ ] Replace broad startup exception handling with explicit import and process-start failure categories.
- [ ] Preserve user-facing startup failure messaging contract.
- [ ] Add tests for missing startup module, unsuccessful startup return, and successful startup path.
      **Notes:** Line 129 wraps MCP startup invocation and currently collapses heterogeneous failure classes.

### [WL-7474]

**Title:** Preserve retry-loop visibility for MCP readiness polling transport failures
**Source:** [thegent/src/thegent/doctor_setup_checks.py:135]
**Acceptance checklist:**

- [ ] Keep per-reason retry counters for status-code and transport failures during readiness polling.
- [ ] Preserve timeout threshold and successful readiness exit behavior.
- [ ] Add tests for delayed readiness, persistent HTTP non-200 responses, and repeated transport faults.
      **Notes:** Line 135 begins the startup readiness loop that accumulates retry diagnostics.

### [WL-7475]

**Title:** Maintain classified MCP poll failure accounting for timeout and connect errors
**Source:** [thegent/src/thegent/doctor_setup_checks.py:146]
**Acceptance checklist:**

- [ ] Keep explicit exception classification for polling transport failures.
- [ ] Preserve retry continuation behavior after classified transient errors.
- [ ] Add tests asserting retry-failure buckets are recorded for timeout and connection faults.
      **Notes:** Line 146 is the typed polling exception branch responsible for retry-failure categorization.

### [WL-7476]

**Title:** Replace broad MCP connectivity catch with typed request-failure branches
**Source:** [thegent/src/thegent/doctor_setup_checks.py:185]
**Acceptance checklist:**

- [ ] Replace generic connectivity exception capture with typed HTTP/transport and OS failure handling.
- [ ] Preserve optional auto-start remediation when MCP is initially unreachable.
- [ ] Add tests for connection error, timeout, and successful remediation flows.
      **Notes:** Line 185 currently catches all MCP connectivity failures under one generic warning path.

### [WL-7477]

**Title:** Verify CLIProxy timeout diagnostics remain explicit in connectivity checks
**Source:** [thegent/src/thegent/doctor_setup_checks.py:211]
**Acceptance checklist:**

- [ ] Preserve explicit timeout handling branch and timeout-specific details text.
- [ ] Preserve warning status and existing operator fix hint semantics.
- [ ] Add tests for timeout-specific message formatting and status output.
      **Notes:** Line 211 is the timeout branch that should stay distinguishable from other transport failures.

### [WL-7478]

**Title:** Keep CLIProxy OS-layer transport failures separately classified from HTTP faults
**Source:** [thegent/src/thegent/doctor_setup_checks.py:227]
**Acceptance checklist:**

- [ ] Preserve dedicated OS error classification branch for CLIProxy connectivity.
- [ ] Keep HTTP/transport classification logic separate from OS error reporting.
- [ ] Add tests for simulated OS errors and validation of emitted status detail text.
      **Notes:** Line 227 handles OS-level proxy failures and should remain distinct for diagnosis.

### [WL-7479]

**Title:** Replace silent watcher SHM-breaker init fallback with observable typed diagnostics
**Source:** [thegent/src/thegent/native/watcher_daemon.py:101]
**Acceptance checklist:**

- [ ] Replace broad SHM-breaker initialization exception handling with explicit import, settings, and path-init categories.
- [ ] Preserve non-fatal watcher startup behavior when SHM breaker is unavailable.
- [ ] Add tests for successful breaker creation, dependency import failures, and invalid SHM paths.
      **Notes:** Line 100 currently catches all breaker init failures and only emits a generic debug message.
