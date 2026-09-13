### [WL-7190]

**Title:** Preserve transition-state read failures instead of silently returning no prior environment
**Source:** [thegent/src/thegent/execution.py:2102]
**Acceptance checklist:**

- [ ] Replace blanket transition-state exception fallback with typed file-read and JSON-parse handling.
- [ ] Preserve `None` behavior only when no prior state file exists.
- [ ] Add tests for valid state, missing state, and malformed transition payloads.
      **Notes:** Silent state-read suppression can hide trust-boundary regressions.

### [WL-7191]

**Title:** Classify MAIF artifact generation failure modes before falling back to in-process artifact construction
**Source:** [thegent/src/thegent/execution.py:2177]
**Acceptance checklist:**

- [ ] Replace broad artifact-generation exception handling with explicit transport, serialization, and binary-exec branches.
- [ ] Preserve deterministic fallback artifact behavior when external generation is unavailable.
- [ ] Add tests for successful MAIF generation, binary failure, and invalid payload serialization.
      **Notes:** Untyped fallback paths reduce operator visibility into artifact integrity failures.

### [WL-7192]

**Title:** Surface per-line registry parse failures with bounded diagnostics during integrity verification
**Source:** [thegent/src/thegent/execution.py:2267]
**Acceptance checklist:**

- [ ] Refactor registry read loop to distinguish decode errors from schema-shape failures.
- [ ] Preserve continued validation for remaining lines after recoverable parse failures.
- [ ] Add tests for valid chains, mixed malformed lines, and sustained decode failures.
      **Notes:** Generic decode fallback obscures where audit integrity degraded.

### [WL-7193]

**Title:** Preserve escalation-queue row parsing failures instead of skipping malformed pending records silently
**Source:** [thegent/src/thegent/execution.py:2460]
**Acceptance checklist:**

- [ ] Replace blanket pending-item parse suppression with bounded malformed-row diagnostics.
- [ ] Keep filtering semantics for valid pending and past-SLA rows.
- [ ] Add tests for valid queues, malformed entries, and mixed pending/resolved rows.
      **Notes:** Silent row drops can underreport blocked items that require operator action.

### [WL-7194]

**Title:** Differentiate escalation-resolution parse failures from intentional pass-through of untouched rows
**Source:** [thegent/src/thegent/execution.py:2482]
**Acceptance checklist:**

- [ ] Classify row parse failures during resolution and annotate unresolved malformed entries.
- [ ] Preserve current behavior for non-target rows and successfully resolved pending entries.
- [ ] Add tests for resolvable rows, malformed lines, and mixed-format queue files.
      **Notes:** Unclassified parse fallback can leave unresolved escalations without actionable context.

### [WL-7195]

**Title:** Avoid silent preflight MCP health-probe suppression before auto-start flow
**Source:** [thegent/src/thegent/doctor_setup_checks.py:106]
**Acceptance checklist:**

- [ ] Replace preflight catch-all suppression with typed connection and timeout handling.
- [ ] Preserve auto-start behavior when MCP is legitimately not running.
- [ ] Add tests for healthy preflight responses, connection refusal, and timeout cases.
      **Notes:** Hidden preflight failures make startup diagnosis slower and less reliable.

### [WL-7196]

**Title:** Record retry-loop probe failures while waiting for MCP startup readiness
**Source:** [thegent/src/thegent/doctor_setup_checks.py:122]
**Acceptance checklist:**

- [ ] Add bounded diagnostics for repeated retry-loop probe exceptions without log spam.
- [ ] Preserve retry cadence and overall startup timeout behavior.
- [ ] Add tests for transient recovery and persistent startup failure scenarios.
      **Notes:** Silent retry failures hide whether readiness checks are progressing.

### [WL-7197]

**Title:** Differentiate CLIProxy connectivity failure classes instead of collapsing to a generic not-running warning
**Source:** [thegent/src/thegent/doctor_setup_checks.py:181]
**Acceptance checklist:**

- [ ] Replace broad CLIProxy exception suppression with typed transport and timeout branches.
- [ ] Preserve warn-level guidance for intentionally offline proxy workflows.
- [ ] Add tests for reachable proxy, connection refusal, and timeout probes.
      **Notes:** Generic warnings can mask distinct connectivity failure causes.

### [WL-7198]

**Title:** Prevent destructive lockfile removal on unclassified shared MCP lockfile read failures
**Source:** [thegent/src/thegent/shared_mcp_manager.py:64]
**Acceptance checklist:**

- [ ] Replace broad lockfile-read exception handling with explicit JSON parse and IO error branches.
- [ ] Preserve stale-lock cleanup only when stale state is positively confirmed.
- [ ] Add tests for valid lockfiles, malformed lockfiles, and transient read failures.
      **Notes:** Blind lockfile deletion can disrupt healthy shared MCP sessions.

### [WL-7199]

**Title:** Preserve process-discovery failure context when inferring process-compose PID
**Source:** [thegent/src/thegent/shared_mcp_manager.py:94]
**Acceptance checklist:**

- [ ] Replace PID-discovery catch-all handling with typed subprocess and parse-failure branches.
- [ ] Preserve startup fallback behavior when PID discovery is unavailable.
- [ ] Add tests for successful PID discovery, empty `pgrep` output, and subprocess failures.
      **Notes:** Silent PID probe failures reduce ownership visibility during MCP incidents.
