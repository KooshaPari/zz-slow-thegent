### [WL-7320]

**Title:** Classify shell launch preflight failures without collapsing runtime setup diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:262]
**Acceptance checklist:**

- [ ] Replace broad shell preflight exception handling with explicit config-read and invocation failure branches.
- [ ] Preserve current command exit semantics when shell preflight cannot complete.
- [ ] Add tests for successful preflight, malformed preflight input, and runtime launch exceptions.
      **Notes:** Line 262 currently funnels heterogeneous shell preflight failures into a single generic error pathway.

### [WL-7321]

**Title:** Distinguish command execution wrapper faults from top-level shell orchestration failures
**Source:** [thegent/src/thegent/shell_cli.py:341]
**Acceptance checklist:**

- [ ] Replace broad top-level shell command exception handling with typed subprocess and state-transition failure branches.
- [ ] Preserve current stderr reporting contract for command execution failures.
- [ ] Add tests for successful command execution, subprocess failure propagation, and orchestration exceptions.
      **Notes:** Line 341 currently collapses execution wrapper errors and orchestration defects into one catch-all handler.

### [WL-7322]

**Title:** Preserve shell session teardown diagnostics instead of masking cleanup-stage exception classes
**Source:** [thegent/src/thegent/shell_cli.py:388]
**Acceptance checklist:**

- [ ] Replace broad teardown exception handling with explicit transport-close and resource-release failure branches.
- [ ] Preserve session cleanup attempt semantics even when partial teardown steps fail.
- [ ] Add tests for clean teardown, partially failed cleanup, and repeated teardown invocation behavior.
      **Notes:** Line 388 currently suppresses teardown failure granularity, reducing post-run incident attribution.

### [WL-7323]

**Title:** Surface conversation dump serialization failures with bounded error classification
**Source:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance checklist:**

- [ ] Replace broad serialization exception handling with explicit JSON encoding and payload-shape failure branches.
- [ ] Preserve successful write behavior for valid conversation payloads.
- [ ] Add tests for valid serialization, non-serializable payload segments, and mixed record batches.
      **Notes:** Line 163 currently handles all dump serialization faults uniformly, obscuring malformed payload root causes.

### [WL-7324]

**Title:** Differentiate conversation artifact write I/O faults from logical dump state errors
**Source:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance checklist:**

- [ ] Replace broad artifact write exception handling with explicit filesystem permission and path-state failure branches.
- [ ] Preserve existing artifact naming and output location contract on successful writes.
- [ ] Add tests for successful writes, permission-denied paths, and invalid output directory states.
      **Notes:** Line 215 currently merges write-time I/O faults and state errors into one recovery path.

### [WL-7325]

**Title:** Preserve conversation export finalization diagnostics for batched dump completion failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:342]
**Acceptance checklist:**

- [ ] Replace broad finalization exception handling with typed summary-build and flush failure categories.
- [ ] Preserve successful batch completion semantics when all records finalize cleanly.
- [ ] Add tests for normal finalization, partial finalization failure, and repeated finalization attempts.
      **Notes:** Line 342 currently suppresses completion-stage error taxonomy, making export reliability regressions harder to trace.

### [WL-7326]

**Title:** Classify watcher event-loop runtime failures separately from transient callback errors
**Source:** [thegent/src/thegent/native/watcher_daemon.py:289]
**Acceptance checklist:**

- [ ] Replace broad watcher loop exception handling with explicit observer-runtime and queue-processing failure branches.
- [ ] Preserve loop continuity guarantees for recoverable per-event anomalies.
- [ ] Add tests for stable event-loop execution, runtime loop exceptions, and recovery after transient errors.
      **Notes:** Line 289 currently groups distinct event-loop failure modes into one generic branch.

### [WL-7327]

**Title:** Preserve watcher restart diagnostics by separating initialization versus restart-cycle faults
**Source:** [thegent/src/thegent/native/watcher_daemon.py:312]
**Acceptance checklist:**

- [ ] Replace broad restart-cycle exception handling with explicit watcher-init and restart-trigger failure categories.
- [ ] Preserve current retry cadence when restart is still viable.
- [ ] Add tests for successful restart, initialization failure, and exhausted retry behavior.
      **Notes:** Line 312 currently masks whether failures originate at restart trigger time or reinitialization time.

### [WL-7328]

**Title:** Differentiate watcher shutdown path failures from active-loop interruption conditions
**Source:** [thegent/src/thegent/native/watcher_daemon.py:321]
**Acceptance checklist:**

- [ ] Replace broad shutdown exception handling with explicit stop-signal and observer-close failure branches.
- [ ] Preserve non-blocking shutdown semantics during interruption handling.
- [ ] Add tests for clean shutdown, interrupted shutdown, and shutdown with observer-close exceptions.
      **Notes:** Line 321 currently collapses interruption and shutdown faults, reducing lifecycle observability.

### [WL-7329]

**Title:** Surface watcher backend handoff failures before fallback dispatch decisions are made
**Source:** [thegent/src/thegent/native/watcher_daemon.py:386]
**Acceptance checklist:**

- [ ] Replace broad backend handoff exception handling with explicit adapter-resolution and dispatch invocation failure branches.
- [ ] Preserve successful backend dispatch behavior for supported event payloads.
- [ ] Add tests for successful handoff, unresolved adapter scenarios, and dispatch-time exceptions.
      **Notes:** Line 386 currently obscures backend handoff fault classes behind a single generic error path.
