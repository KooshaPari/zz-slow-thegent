### [WL-7090]

**Title:** Preserve environment-state read failures instead of silently treating state as absent
**Source:** [thegent/src/thegent/execution.py:2102]
**Acceptance checklist:**

- [ ] Replace catch-all state-read fallback with typed file-read and JSON-parse error handling.
- [ ] Preserve `None` semantics only when transition state is genuinely missing.
- [ ] Add tests for valid state, missing state file, and malformed state payloads.
      **Notes:** Silent state-read suppression can hide trust-boundary tracking regressions.

### [WL-7091]

**Title:** Distinguish MAIF artifact generation transport errors from model-construction fallback paths
**Source:** [thegent/src/thegent/execution.py:2177]
**Acceptance checklist:**

- [ ] Replace broad artifact-generation exception handling with classified binary, IO, and serialization failure branches.
- [ ] Preserve deterministic fallback artifact construction when external generation is unavailable.
- [ ] Add tests for successful generation, binary invocation failure, and invalid payload serialization.
      **Notes:** Unclassified fallback behavior obscures why MAIF generation degraded.

### [WL-7092]

**Title:** Surface audit-registry line decode failures with bounded corruption diagnostics
**Source:** [thegent/src/thegent/execution.py:2267]
**Acceptance checklist:**

- [ ] Refactor per-line audit parsing to classify JSON decode and schema-shape failures.
- [ ] Preserve continued validation for remaining records after recoverable line failures.
- [ ] Add tests for fully valid chains, mixed malformed lines, and sustained decode errors.
      **Notes:** Generic decode messages reduce precision when reconstructing integrity failures.

### [WL-7093]

**Title:** Preserve escalation-queue row parsing failures instead of skipping malformed pending records silently
**Source:** [thegent/src/thegent/execution.py:2460]
**Acceptance checklist:**

- [ ] Replace blanket pending-item parse suppression with bounded malformed-row diagnostics.
- [ ] Keep filtering semantics for valid pending and past-SLA rows.
- [ ] Add tests for valid queues, malformed entries, and mixed pending/resolved rows.
      **Notes:** Silent row drops can underreport blocked items that require operator action.

### [WL-7094]

**Title:** Differentiate escalation-resolution parse failures from intentional pass-through of untouched rows
**Source:** [thegent/src/thegent/execution.py:2482]
**Acceptance checklist:**

- [ ] Classify row parse failures during resolution and annotate unresolved malformed entries.
- [ ] Preserve current behavior for non-target rows and successfully resolved pending entries.
- [ ] Add tests for resolvable rows, malformed lines, and mixed-format queue files.
      **Notes:** Unclassified parse fallback can leave unresolved escalations without actionable context.

### [WL-7095]

**Title:** Report preflight MCP health probe failures before auto-start fallback attempts
**Source:** [thegent/src/thegent/doctor_setup_checks.py:106]
**Acceptance checklist:**

- [ ] Replace silent preflight exception suppression with typed connectivity diagnostics.
- [ ] Preserve automatic startup behavior when MCP is not yet running.
- [ ] Add tests for healthy MCP responses, timeout failures, and connection refusals.
      **Notes:** Hidden preflight failures make startup triage slower and less reliable.

### [WL-7096]

**Title:** Record retry-loop probe failure classes while waiting for MCP startup readiness
**Source:** [thegent/src/thegent/doctor_setup_checks.py:122]
**Acceptance checklist:**

- [ ] Add bounded diagnostics for retry-loop connection and timeout failures without log spam.
- [ ] Preserve retry cadence and startup timeout thresholds.
- [ ] Add tests for transient recoveries and persistent startup failures.
      **Notes:** Silent retries hide whether readiness checks are progressing or repeatedly failing.

### [WL-7097]

**Title:** Surface CLIProxy reachability check failures in connectivity diagnostics
**Source:** [thegent/src/thegent/doctor_setup_checks.py:181]
**Acceptance checklist:**

- [ ] Replace catch-all CLIProxy probe suppression with typed transport and timeout branches.
- [ ] Preserve warn-level user guidance when proxy is intentionally offline.
- [ ] Add tests for reachable proxy, refused connections, and timed-out probes.
      **Notes:** Generic proxy-down warnings can mask distinct connectivity failure modes.

### [WL-7098]

**Title:** Avoid destructive lockfile deletion on unclassified shared-MCP lockfile read errors
**Source:** [thegent/src/thegent/shared_mcp_manager.py:64]
**Acceptance checklist:**

- [ ] Replace broad lockfile-read exception handling with explicit JSON parse and IO error paths.
- [ ] Preserve stale-lock cleanup only when stale state is positively confirmed.
- [ ] Add tests for valid stale lockfiles, malformed lockfiles, and transient read failures.
      **Notes:** Blind lockfile removal can disrupt healthy shared MCP sessions.

### [WL-7099]

**Title:** Preserve process-discovery failures when inferring process-compose PID for shared MCP startup
**Source:** [thegent/src/thegent/shared_mcp_manager.py:94]
**Acceptance checklist:**

- [ ] Replace broad PID-discovery exception suppression with typed subprocess and parse failure handling.
- [ ] Preserve fallback behavior that still allows startup to complete without discovered PID.
- [ ] Add tests for successful PID discovery, empty `pgrep` output, and subprocess execution errors.
      **Notes:** Silent PID-probe failures weaken operator visibility into shared MCP ownership.
