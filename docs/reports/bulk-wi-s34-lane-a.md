### [WL-7220]

**Title:** Classify CLIProxy config read failures by parse versus file I/O conditions
**Source:** [thegent/src/thegent/doctor_setup_checks.py:60]
**Acceptance checklist:**

- [ ] Replace broad config-read exception handling with explicit YAML-parse and filesystem error branches.
- [ ] Preserve existing fail status semantics when config content is invalid or unreadable.
- [ ] Add tests for valid config load, malformed YAML, and permission-denied config paths.
      **Notes:** Line 60 currently funnels all config read failures into one generic message, reducing setup triage precision.

### [WL-7221]

**Title:** Distinguish MCP health-probe transport errors from startup orchestration failures
**Source:** [thegent/src/thegent/doctor_setup_checks.py:106]
**Acceptance checklist:**

- [ ] Replace broad MCP health probe suppression with typed connection and timeout failure categories.
- [ ] Preserve current auto-start behavior when MCP is initially unreachable.
- [ ] Add tests for reachable MCP, connection refusal, and probe timeout paths.
      **Notes:** Line 106 currently swallows initial probe failure classes, obscuring whether failures are transient or configuration-driven.

### [WL-7222]

**Title:** Preserve MCP startup polling failure taxonomy during readiness loop retries
**Source:** [thegent/src/thegent/doctor_setup_checks.py:122]
**Acceptance checklist:**

- [ ] Replace broad polling-loop exception handling with explicit connect-timeout and request-failure branches.
- [ ] Preserve retry loop timing and successful readiness detection semantics.
- [ ] Add tests for successful delayed startup, repeated timeout retries, and non-timeout polling failures.
      **Notes:** Line 122 currently collapses polling-time faults into silent retries without cause classification.

### [WL-7223]

**Title:** Separate MCP bootstrap import errors from runtime startup execution failures
**Source:** [thegent/src/thegent/doctor_setup_checks.py:128]
**Acceptance checklist:**

- [ ] Replace broad startup exception handling with explicit import and startup invocation failure branches.
- [ ] Preserve current user-visible failure messaging contract for unsuccessful MCP auto-start.
- [ ] Add tests for missing startup module import, startup return failure, and successful bootstrap flows.
      **Notes:** Line 128 currently combines distinct bootstrap failure classes into a single message shape.

### [WL-7224]

**Title:** Differentiate connectivity check request faults from auto-start remediation outcomes
**Source:** [thegent/src/thegent/doctor_setup_checks.py:156]
**Acceptance checklist:**

- [ ] Replace broad MCP connectivity exception handling with typed request failure categories.
- [ ] Preserve fallback to `ensure_mcp_running` when auto-start is enabled.
- [ ] Add tests for unreachable MCP with successful remediation and unreachable MCP with failed remediation.
      **Notes:** Line 156 currently maps all connectivity exceptions to one warning pathway before optional remediation.

### [WL-7225]

**Title:** Classify CLIProxy connectivity failures without masking timeout versus refusal states
**Source:** [thegent/src/thegent/doctor_setup_checks.py:181]
**Acceptance checklist:**

- [ ] Replace broad CLIProxy connectivity exception handling with explicit timeout and connection-refused branches.
- [ ] Preserve current warning-level contract when CLIProxy is unavailable.
- [ ] Add tests for successful reachability, request timeout, and refused connection scenarios.
      **Notes:** Line 181 currently collapses distinct transport failures into a single “not running” status message.

### [WL-7226]

**Title:** Preserve watcher SHM breaker initialization diagnostics for import and config paths
**Source:** [thegent/src/thegent/native/watcher_daemon.py:100]
**Acceptance checklist:**

- [ ] Replace broad SHM breaker initialization exception handling with explicit import, settings, and init failure classes.
- [ ] Preserve non-fatal watcher startup behavior when SHM breaker is unavailable.
- [ ] Add tests for successful SHM breaker creation, missing dependency imports, and invalid SHM path configuration.
      **Notes:** Line 100 currently routes all breaker initialization issues through one debug message, limiting observability.

### [WL-7227]

**Title:** Differentiate watcher callback execution faults from event dispatch pipeline behavior
**Source:** [thegent/src/thegent/native/watcher_daemon.py:207]
**Acceptance checklist:**

- [ ] Replace broad callback exception handling with bounded classification of user-callback runtime error types.
- [ ] Preserve continued event processing for subsequent file-system events after callback failures.
- [ ] Add tests for successful callbacks, callback runtime exceptions, and post-failure continued dispatch.
      **Notes:** Line 207 currently logs callback failures generically, making recurring callback fault patterns harder to diagnose.

### [WL-7228]

**Title:** Classify watcher breaker record-failure write faults separately from callback failures
**Source:** [thegent/src/thegent/native/watcher_daemon.py:217]
**Acceptance checklist:**

- [ ] Replace broad breaker write exception handling with explicit transport and state-write failure categories.
- [ ] Preserve callback-error logging semantics when breaker recording is unavailable.
- [ ] Add tests for successful breaker record writes, record-time exceptions, and breaker-unavailable mode.
      **Notes:** Line 217 currently merges breaker telemetry write faults into one debug branch with limited failure context.

### [WL-7229]

**Title:** Remove silent configured-provider extraction fallback in provider discovery initialization
**Source:** [thegent/src/thegent/doctor.py:530]
**Acceptance checklist:**

- [ ] Replace silent broad exception suppression during configured-provider extraction with explicit parse and lookup failure handling.
- [ ] Preserve successful provider set construction when cliproxy config data is valid.
- [ ] Add tests for valid provider extraction, malformed config content, and missing-provider key paths.
      **Notes:** Line 530 currently suppresses all configured-provider extraction failures and can underreport provider availability.
