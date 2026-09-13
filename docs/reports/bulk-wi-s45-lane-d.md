### [WL-7800]

**Title:** Add per-component timeout budgets and cancellation propagation in sync orchestrator runs
**Source:** [thegent/src/thegent/sync/orchestrator.py:152]
**Acceptance checklist:**

- [ ] Add a per-component timeout map to orchestrator execution and enforce it during each component `sync()` call.
- [ ] Ensure timeout-triggered cancellation does not abort unrelated components and is reflected in `SyncResult` status metadata.
- [ ] Add tests for all-success, single-component timeout, and mixed success/timeout execution paths.
      **Notes:** Current sync execution can hang on one slow component and delay the full cycle without actionable timeout attribution.

### [WL-7801]

**Title:** Persist structured routing failure reason codes in route executor audit output
**Source:** [thegent/src/thegent/routing/route_executor.py:128]
**Acceptance checklist:**

- [ ] Extend routing audit records with normalized `failure_code` and `failure_stage` fields for no-route and execution-error outcomes.
- [ ] Keep existing audit schema keys intact while appending the new diagnostics fields.
- [ ] Add tests that validate audit serialization for success, provider rejection, and downstream execution failure.
      **Notes:** Routing incidents currently require log scraping because audit entries lack stable reason codes.

### [WL-7802]

**Title:** Make workstream claim operations atomic with optimistic version checks
**Source:** [thegent/src/thegent/commands/workstream.py:106]
**Acceptance checklist:**

- [ ] Add version-token or checksum verification before rewriting the CLAIMED table so concurrent claimers cannot overwrite each other.
- [ ] Return a deterministic conflict error when the file changed between read and write.
- [ ] Add tests for single claimer success, concurrent claim conflict, and retry-after-refresh success.
      **Notes:** Non-atomic claim rewrites risk lost ownership updates in parallel lane execution.

### [WL-7803]

**Title:** Add redaction pass for environment secrets before conversation dump persistence
**Source:** [thegent/src/thegent/session/conversation_dumper.py:85]
**Acceptance checklist:**

- [ ] Implement a configurable redaction pass that masks common secret patterns before records are written.
- [ ] Preserve record shape and turn ordering while redacting only sensitive values.
- [ ] Add tests covering API key pattern masking, benign text passthrough, and deterministic redaction output.
      **Notes:** Session dumps may capture sensitive tokens from tool output unless masked pre-write.

### [WL-7804]

**Title:** Expose recorder flush latency histograms and queue-drain status in trace stats
**Source:** [thegent/src/thegent/trace/recorder.py:99]
**Acceptance checklist:**

- [ ] Add flush latency and queue-drain metrics to recorder stats output with stable field names.
- [ ] Track and report pending item count at flush start/end for backlog diagnostics.
- [ ] Add tests validating stats fields on idle flush, heavy flush, and flush-after-backpressure cases.
      **Notes:** Current recorder telemetry is insufficient to diagnose intermittent trace lag spikes.

### [WL-7805]

**Title:** Enforce bounded worker task retries with explicit terminal error classification
**Source:** [thegent/src/thegent/core/worker_pool.py:226]
**Acceptance checklist:**

- [ ] Introduce max retry attempts per task with configurable backoff in `PersistentWorkerPool` dispatch.
- [ ] Classify terminal outcomes as retryable vs non-retryable and include classification in `AgentResult`.
- [ ] Add tests for immediate success, retry-then-success, and retry-exhausted failure behavior.
      **Notes:** Unbounded or opaque retry behavior can hide persistent task failures and waste compute.

### [WL-7806]

**Title:** Add source provenance tags for terminal capture fallback path selection
**Source:** [thegent/src/thegent/tools/terminal_capture.py:111]
**Acceptance checklist:**

- [ ] Include a required provenance field in capture responses indicating `tmux`, `zmx`, `proc`, or `termitty` path.
- [ ] Ensure provenance is set consistently for success and partial-capture outcomes.
- [ ] Add tests for each capture backend path and an unavailable-backend failure case.
      **Notes:** Debugging missing terminal output is difficult without a clear record of which capture path was used.

### [WL-7807]

**Title:** Add stale-check detection and age thresholds in health checker evaluations
**Source:** [thegent/src/thegent/monitoring/health_check.py:9]
**Acceptance checklist:**

- [ ] Add per-check freshness thresholds and flag checks as stale when latest sample exceeds threshold.
- [ ] Include stale age and threshold values in health payloads for operator triage.
- [ ] Add tests for fresh, stale, and missing-sample scenarios.
      **Notes:** A pass/fail-only checker can report healthy status from outdated measurements.

### [WL-7808]

**Title:** Validate A2A message role transitions and reject illegal state progressions
**Source:** [thegent/src/thegent/protocols/a2a.py:130]
**Acceptance checklist:**

- [ ] Define allowed role/state transitions in router message handling and reject invalid transitions with explicit errors.
- [ ] Preserve current schema validation behavior while adding transition-level validation.
- [ ] Add tests for valid progression, invalid role jump, and duplicate terminal-state messages.
      **Notes:** Schema-valid messages can still violate protocol flow and create inconsistent multi-agent state.

### [WL-7809]

**Title:** Record prune candidate decision traces for PPID and command-line classification
**Source:** [thegent/src/thegent/prune_utils.py:79]
**Acceptance checklist:**

- [ ] Emit structured decision traces that show which PPID/command predicates marked a process as orphaned.
- [ ] Add a dry-run diagnostics payload listing kept vs pruned candidates with reason codes.
- [ ] Add tests for true orphan, protected process exclusion, and ambiguous parent-chain cases.
      **Notes:** Prune actions are currently hard to audit when investigating accidental or missed cleanups.
