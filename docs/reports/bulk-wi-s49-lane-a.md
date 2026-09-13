### [WL-7970]

**Title:** Add explicit command origin tags to session start audit events
**Source:** [thegent/src/thegent/cli/session.py:118]
**Acceptance checklist:**

- [ ] Include a deterministic command-origin tag on each session start audit event.
- [ ] Preserve existing session start success and failure exit semantics.
- [ ] Add tests for interactive start, scripted start, and missing-origin fallback behavior.
      **Notes:** Origin tags are required to separate manual and automated session start traffic in diagnostics.

### [WL-7971]

**Title:** Enforce stable ordering for environment variable overlay resolution
**Source:** [thegent/src/thegent/config/env_overlay.py:73]
**Acceptance checklist:**

- [ ] Resolve overlay sources in a fixed documented order across repeated executions.
- [ ] Preserve current key precedence when conflicts occur between overlays.
- [ ] Add tests for deterministic ordering, conflict precedence, and empty-overlay no-op behavior.
      **Notes:** Stable overlay ordering prevents configuration drift between equivalent runs.

### [WL-7972]

**Title:** Emit queue wait duration in worker dispatch timeout warnings
**Source:** [thegent/src/thegent/workers/dispatch.py:149]
**Acceptance checklist:**

- [ ] Include queue wait duration milliseconds in timeout warning payloads.
- [ ] Preserve existing timeout thresholds and task handoff logic.
- [ ] Add tests for under-threshold silence, threshold breach warning content, and repeated timeout warnings.
      **Notes:** Wait-duration context is needed to distinguish transient spikes from sustained saturation.

### [WL-7973]

**Title:** Reject invalid profile aliases before runtime profile activation
**Source:** [thegent/src/thegent/runtime/profile.py:61]
**Acceptance checklist:**

- [ ] Validate profile alias format before activation and return actionable errors for invalid aliases.
- [ ] Preserve successful activation behavior for valid aliases.
- [ ] Add tests for valid alias activation, invalid alias rejection, and unknown-alias handling.
      **Notes:** Early alias validation avoids ambiguous runtime failures during profile selection.

### [WL-7974]

**Title:** Add expected-versus-observed schema version details to cache restore failures
**Source:** [thegent/src/thegent/cache/restore.py:132]
**Acceptance checklist:**

- [ ] Report expected and observed schema version values when cache restore rejects metadata.
- [ ] Preserve automatic cache rebuild behavior after version mismatch detection.
- [ ] Add tests for matching schema restore, mismatched schema rebuild, and missing schema metadata cases.
      **Notes:** Version mismatch detail is required for auditable cache invalidation decisions.

### [WL-7975]

**Title:** Fail registry initialization on duplicate command short names
**Source:** [thegent/src/thegent/commands/registry.py:94]
**Acceptance checklist:**

- [ ] Detect duplicate short names and abort registry initialization with conflict details.
- [ ] Preserve normal registry initialization when short names are unique.
- [ ] Add tests for duplicate rejection, unique registration success, and short-name lookup integrity.
      **Notes:** Duplicate short names must hard-fail to prevent ambiguous command routing.

### [WL-7976]

**Title:** Include monotonic elapsed time fields in network retry attempt logs
**Source:** [thegent/src/thegent/net/retry_loop.py:107]
**Acceptance checklist:**

- [ ] Attach monotonic elapsed time milliseconds to every retry attempt log record.
- [ ] Preserve current retry schedule, jitter behavior, and maximum attempt limits.
- [ ] Add tests for elapsed-field presence, retry interval integrity, and exhausted retry logging.
      **Notes:** Monotonic elapsed timing enables reliable latency regression detection independent of wall clock.

### [WL-7977]

**Title:** Block workspace write operations that resolve outside configured roots
**Source:** [thegent/src/thegent/fs/write_guard.py:58]
**Acceptance checklist:**

- [ ] Reject writes resolving outside configured workspace roots with explicit path diagnostics.
- [ ] Preserve successful writes for normalized in-scope paths.
- [ ] Add tests for outside-root rejection, inside-root success, and traversal normalization edge cases.
      **Notes:** Write boundary enforcement is required to prevent accidental cross-workspace file mutation.

### [WL-7978]

**Title:** Emit grouped summary counts for skipped checks in validation runs
**Source:** [thegent/src/thegent/validation/reporting.py:176]
**Acceptance checklist:**

- [ ] Print a grouped skipped-check summary with per-reason counts at run completion.
- [ ] Preserve existing per-check skip details and current validation exit behavior.
- [ ] Add tests for no-skips output, single-reason grouping, and deterministic multi-reason ordering.
      **Notes:** Grouped skip counts improve triage without removing line-level validation evidence.

### [WL-7979]

**Title:** Add checksum diff details to artifact verification mismatch errors
**Source:** [thegent/src/thegent/artifacts/integrity.py:121]
**Acceptance checklist:**

- [ ] Include expected and observed checksum values in verification mismatch errors.
- [ ] Preserve successful verification flow for matching checksums.
- [ ] Add tests for checksum match success, mismatch detail emission, and missing-checksum handling.
      **Notes:** Mismatch details are needed to diagnose artifact integrity failures quickly.
