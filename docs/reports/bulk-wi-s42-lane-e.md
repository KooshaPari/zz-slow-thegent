### [WL-7660]

**Title:** Preserve transcript indexing reliability by classifying export metadata write failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:342]
**Acceptance checklist:**

- [ ] Replace broad exception handling around transcript indexing writes with typed filesystem and serialization branches.
- [ ] Preserve current export success behavior while emitting actionable diagnostics when index persistence fails.
- [ ] Add tests for readonly destination paths, invalid metadata payloads, and successful index writes.
      **Notes:** Current broad catch behavior at line 342 reduces debuggability when transcript export appears to succeed but metadata is incomplete.

### [WL-7661]

**Title:** Improve CLI resilience by separating command-runner setup failures from execution failures
**Source:** [thegent/src/thegent/shell_cli.py:342]
**Acceptance checklist:**

- [ ] Split catch-all shell CLI error handling into setup, spawn, and runtime failure classes.
- [ ] Preserve existing return contract for successful command runs.
- [ ] Add tests for invalid executable path, subprocess launch error, and non-zero exit propagation.
      **Notes:** A single broad exception path at line 341 blurs where shell command failures originate.

### [WL-7662]

**Title:** Standardize top-level shell CLI error surfacing for better operator troubleshooting
**Source:** [thegent/src/thegent/shell_cli.py:389]
**Acceptance checklist:**

- [ ] Replace generic exception wrapping with typed terminal/reporting errors that preserve stderr context.
- [ ] Keep user-facing messaging concise while retaining machine-readable error details.
- [ ] Add tests covering malformed input args, downstream runtime faults, and happy-path output.
      **Notes:** Line 388 currently collapses distinct failure modes into a generic handler, reducing devx for CLI debugging.

### [WL-7663]

**Title:** Reduce watcher daemon false-healthy states by reporting startup exception categories
**Source:** [thegent/src/thegent/native/watcher_daemon.py:100]
**Acceptance checklist:**

- [ ] Introduce typed startup error categories for socket setup, file watch init, and bootstrap config issues.
- [ ] Preserve daemon lifecycle behavior for healthy starts.
- [ ] Add tests for invalid watch root, missing permissions, and clean startup.
      **Notes:** Catch-all startup handling at line 100 can leave operators without clear remediation steps.

### [WL-7664]

**Title:** Make watcher event-loop recovery deterministic instead of silently masking handler faults
**Source:** [thegent/src/thegent/native/watcher_daemon.py:207]
**Acceptance checklist:**

- [ ] Replace broad per-event exception suppression with bounded retry plus structured warning output.
- [ ] Preserve continuous processing for unrelated events after one handler failure.
- [ ] Add tests for malformed events, transient handler exceptions, and normal event throughput.
      **Notes:** Broad catching at line 207 weakens reliability by hiding recurring event processing defects.

### [WL-7665]

**Title:** Surface nested watcher callback errors with contextual metadata for faster triage
**Source:** [thegent/src/thegent/native/watcher_daemon.py:217]
**Acceptance checklist:**

- [ ] Emit callback function name, event type, and path context when inner callback handling fails.
- [ ] Preserve non-crashing callback fanout behavior.
- [ ] Add tests for one failing callback among multiple subscribers and full-success fanout.
      **Notes:** The inner exception branch at line 217 currently suppresses high-signal callback diagnostics.

### [WL-7666]

**Title:** Improve SHM breaker reliability by exposing native write-path degradation events
**Source:** [thegent/src/thegent/native/state_shm.py:237]
**Acceptance checklist:**

- [ ] Classify native `record_failure` exceptions and emit one-shot degradation markers when fallback mode activates.
- [ ] Preserve functional fallback behavior to avoid hard outages when native SHM faults.
- [ ] Add tests for simulated native bridge exceptions and fallback consistency.
      **Notes:** Line 237 currently warns generically, making it hard to distinguish transient errors from sustained degradation.

### [WL-7667]

**Title:** Add explicit partial-health semantics when SHM health reads fail and fallback returns default
**Source:** [thegent/src/thegent/native/state_shm.py:298]
**Acceptance checklist:**

- [ ] Return structured read status (`ok`/`degraded`) alongside health value when native reads error.
- [ ] Preserve compatibility for callers that only consume numeric health.
- [ ] Add tests for native read exceptions, fallback reads, and successful native path.
      **Notes:** Returning only `0.0` on errors at line 298 can hide instrumentation failures as legitimate health drops.

### [WL-7668]

**Title:** Improve adapter normalization devx with typed diagnostics before fallback extraction
**Source:** [thegent/src/thegent/contracts/adapters.py:234]
**Acceptance checklist:**

- [ ] Replace broad adapter failure catch with typed normalization error categories and provider context.
- [ ] Preserve existing `allow_fallback` semantics for compatibility.
- [ ] Add tests for adapter schema mismatch, adapter runtime exception, and successful fallback extraction.
      **Notes:** Generic exception handling at line 233 makes provider-specific adapter regressions harder to debug.

### [WL-7669]

**Title:** Make project discovery cache failures observable without breaking scan workflows
**Source:** [thegent/src/thegent/discovery/projects.py:107]
**Acceptance checklist:**

- [ ] Replace silent suppression in discovery cache writes with low-noise warnings containing operation and path context.
- [ ] Preserve best-effort discovery behavior so scans complete when cache persistence fails.
- [ ] Add tests for sqlite write conflicts, file permission errors, and normal cache updates.
      **Notes:** `contextlib.suppress(Exception)` at line 107 currently hides cache reliability defects that impact repeated scan performance.
