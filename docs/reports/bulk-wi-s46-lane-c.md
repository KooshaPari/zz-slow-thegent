### [WL-7840]

**Title:** Add deterministic profile merge precedence for layered clode profile sources
**Source:** [thegent/src/thegent/clode_profiles.py:112]
**Acceptance checklist:**

- [ ] Define and enforce a single precedence order for base, workspace, and session profile layers.
- [ ] Preserve current resolved profile output when only one profile source is present.
- [ ] Add tests for single-source load, multi-layer override, and equal-priority conflict handling.
      **Notes:** Line 112 is in profile merge flow where inconsistent precedence can produce non-reproducible runtime settings.

### [WL-7841]

**Title:** Normalize tool invocation envelope fields before dispatch routing
**Source:** [thegent/src/thegent/tool_router.py:87]
**Acceptance checklist:**

- [ ] Add envelope normalization for required dispatch fields before routing decisions execute.
- [ ] Preserve successful dispatch behavior for already-normalized tool requests.
- [ ] Add tests for normalized input, missing required fields, and malformed envelope values.
      **Notes:** Line 87 sits in routing entry where request normalization should happen once before fanout.

### [WL-7842]

**Title:** Enforce monotonic session event sequence numbers during append operations
**Source:** [thegent/src/thegent/session/event_log.py:143]
**Acceptance checklist:**

- [ ] Reject append attempts when the incoming sequence number is not strictly greater than the latest persisted value.
- [ ] Preserve append behavior for correctly ordered event sequences.
- [ ] Add tests for ordered appends, duplicate sequence rejection, and out-of-order append rejection.
      **Notes:** Line 143 is in append path where sequence validation prevents replay ambiguity.

### [WL-7843]

**Title:** Add explicit fallback reason codes for native terminal capture degradation
**Source:** [thegent/src/thegent/tools/terminal_capture.py:196]
**Acceptance checklist:**

- [ ] Emit structured fallback reason codes when native capture cannot be used and a secondary path is selected.
- [ ] Preserve current successful capture behavior when native capture remains available.
- [ ] Add tests for native-success, capability-missing fallback, and runtime-error fallback paths.
      **Notes:** Line 196 is in backend selection where fallback attribution is needed for field diagnostics.

### [WL-7844]

**Title:** Guard workspace claim writes with atomic temp-file swap semantics
**Source:** [thegent/src/thegent/commands/workstream.py:219]
**Acceptance checklist:**

- [ ] Write claim updates through a temp file and atomic rename to prevent partial-file corruption.
- [ ] Preserve existing claim file format and ordering for successful writes.
- [ ] Add tests for normal write, interrupted write simulation, and concurrent writer contention.
      **Notes:** Line 219 is in claim persistence path where non-atomic writes can leave malformed ownership state.

### [WL-7845]

**Title:** Add stale-worker quarantine state before supervisor restart loops
**Source:** [thegent/src/thegent/workers/supervisor.py:233]
**Acceptance checklist:**

- [ ] Introduce a quarantine state for repeatedly failing workers prior to automatic restart attempts.
- [ ] Preserve existing restart behavior for transient single-failure workers.
- [ ] Add tests for transient failure recovery, repeated failure quarantine, and manual quarantine clear.
      **Notes:** Line 233 is in restart decision flow where endless loops should become explicit quarantine outcomes.

### [WL-7846]

**Title:** Validate cache metadata timestamp bounds before index hydration
**Source:** [thegent/src/thegent/cache/index.py:258]
**Acceptance checklist:**

- [ ] Reject cache metadata with impossible or out-of-bounds timestamps during hydration.
- [ ] Preserve hydration behavior for metadata entries with valid timestamp bounds.
- [ ] Add tests for valid metadata, future timestamp rejection, and negative timestamp rejection.
      **Notes:** Line 258 is in metadata hydration where invalid time values can poison cache validity checks.

### [WL-7847]

**Title:** Add explicit retry jitter cap and deterministic seed option for network retries
**Source:** [thegent/src/thegent/net/retry.py:171]
**Acceptance checklist:**

- [ ] Apply a configurable upper bound to jitter values used in retry backoff calculations.
- [ ] Preserve current retry timing distribution when jitter cap is not explicitly overridden.
- [ ] Add tests for capped jitter behavior, uncapped default behavior, and deterministic seeded jitter mode.
      **Notes:** Line 171 is in backoff computation where uncontrolled jitter can inflate tail latency.

### [WL-7848]

**Title:** Enforce protocol state terminality in A2A router post-completion handling
**Source:** [thegent/src/thegent/protocols/a2a.py:211]
**Acceptance checklist:**

- [ ] Reject non-terminal follow-up messages after a conversation reaches terminal protocol state.
- [ ] Preserve valid handling for messages that occur before terminal transition.
- [ ] Add tests for valid pre-terminal flow, post-terminal rejection, and duplicate terminal message idempotency.
      **Notes:** Line 211 is in message handling where terminal-state enforcement protects protocol consistency.

### [WL-7849]

**Title:** Add health-check evaluation latency budget with per-check overrun reporting
**Source:** [thegent/src/thegent/monitoring/health_check.py:64]
**Acceptance checklist:**

- [ ] Add per-check latency budgets and mark checks as overrun when execution exceeds budget.
- [ ] Preserve current pass/fail semantics for checks that complete within budget.
- [ ] Add tests for in-budget checks, over-budget checks, and mixed-budget evaluation cycles.
      **Notes:** Line 64 is in check evaluation where runtime overruns currently lack explicit surfaced signals.
