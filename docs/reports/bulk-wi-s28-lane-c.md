### [WL-6940]

**Title:** Replace shell alias-probe catch-all suppression with typed degraded diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:177]
**Acceptance checklist:**

- [ ] Replace broad alias-probe exception swallowing with timeout and subprocess-failure classification.
- [ ] Emit non-fatal doctor diagnostics that preserve the concrete probe failure reason.
- [ ] Add tests for successful probe, timeout, and execution-failure branches.
      **Notes:** Silent probe suppression can report shell health as clean when diagnostics are unavailable.

### [WL-6941]

**Title:** Distinguish git-log command failures from legitimate empty commit windows
**Source:** [thegent/src/thegent/summary.py:61]
**Acceptance checklist:**

- [ ] Replace blanket exception-to-empty fallback with structured subprocess failure handling.
- [ ] Preserve empty-list semantics only for truly empty commit ranges.
- [ ] Add tests for non-repo paths, failing git invocations, and valid empty ranges.
      **Notes:** Conflating failures with empty history obscures summary reliability.

### [WL-6942]

**Title:** Surface malformed summary JSONL rows instead of silently dropping parse failures
**Source:** [thegent/src/thegent/summary.py:78]
**Acceptance checklist:**

- [ ] Replace parse exception swallowing with bounded malformed-row diagnostics.
- [ ] Continue ingesting valid rows while tracking skipped malformed records.
- [ ] Add tests for mixed valid and malformed `.jsonl` inputs.
      **Notes:** Hidden parse failures erode trust in generated summaries.

### [WL-6943]

**Title:** Preserve chat-log read failures as explicit degraded-state outcomes
**Source:** [thegent/src/thegent/summary.py:94]
**Acceptance checklist:**

- [ ] Replace catch-all log-read suppression with typed IO and parsing error reporting.
- [ ] Differentiate unreadable files from legitimately empty log sets.
- [ ] Add tests for readable files, missing files, and permission-denied paths.
      **Notes:** Silent read failures can make incomplete audits appear complete.

### [WL-6944]

**Title:** Capture pre-start MCP health-check failures before auto-start fallback
**Source:** [thegent/src/thegent/doctor_setup_checks.py:106]
**Acceptance checklist:**

- [ ] Replace silent preflight suppression with categorized connectivity diagnostics.
- [ ] Preserve auto-start behavior while recording why initial health checks failed.
- [ ] Add tests for healthy, timeout, and connection-refused preflight paths.
      **Notes:** Missing preflight failure context slows startup incident triage.

### [WL-6945]

**Title:** Add bounded retry-loop diagnostics for MCP startup health probes
**Source:** [thegent/src/thegent/doctor_setup_checks.py:122]
**Acceptance checklist:**

- [ ] Record failure reason classes during wait-loop retries without log spam.
- [ ] Preserve retry cadence and timeout semantics.
- [ ] Add tests for transient failures that recover and persistent failure timeouts.
      **Notes:** Silent retries hide whether startup is progressing or stalled.

### [WL-6946]

**Title:** Differentiate CLIProxy transport exceptions from non-200 service responses
**Source:** [thegent/src/thegent/doctor_setup_checks.py:181]
**Acceptance checklist:**

- [ ] Replace generic exception fallback with classified timeout/connection diagnostics.
- [ ] Preserve warn-level behavior while surfacing actionable remediation guidance.
- [ ] Add tests for transport failures and non-200 proxy responses.
      **Notes:** A single generic warning message increases proxy debugging time.

### [WL-6947]

**Title:** Avoid destructive lockfile cleanup on unclassified lockfile read failures
**Source:** [thegent/src/thegent/shared_mcp_manager.py:65]
**Acceptance checklist:**

- [ ] Replace broad exception handling with explicit JSON parse and IO error branches.
- [ ] Prevent lockfile deletion when lock state cannot be confidently classified as stale.
- [ ] Add tests for stale lock cleanup, malformed JSON, and transient read errors.
      **Notes:** Blind lockfile deletion can disrupt healthy shared MCP sessions.

### [WL-6948]

**Title:** Distinguish interface-enumeration failures from true no-interface hosts
**Source:** [thegent/src/thegent/resources/network.py:159]
**Acceptance checklist:**

- [ ] Replace generic exception fallback with machine-readable failure context.
- [ ] Preserve empty-interface output only for legitimate zero-interface scenarios.
- [ ] Add tests for psutil query exceptions and healthy enumeration.
      **Notes:** Shared empty-list output masks telemetry acquisition failures.

### [WL-6949]

**Title:** Preserve pending-message poll failure details instead of returning silent empties
**Source:** [thegent/src/thegent/execution.py:1806]
**Acceptance checklist:**

- [ ] Replace broad exception-to-empty fallback with explicit degraded-result signaling.
- [ ] Emit bounded diagnostics when metadata lookup or registry loading fails.
- [ ] Add tests for missing metadata, parser failures, and successful pending-message retrieval.
      **Notes:** Silent empty returns can hide message-delivery control-flow regressions.
