### [WL-7710]

**Title:** Make config-file parse failures actionable during startup validation
**Source:** [thegent/src/thegent/config_loader.py:91]
**Acceptance checklist:**

- [ ] Replace generic config parse exception wrapping with typed YAML/JSON decode diagnostics.
- [ ] Preserve current startup validation flow for valid configurations.
- [ ] Add tests for malformed config, unreadable config path, and successful parse behavior.
      **Notes:** Current startup parsing errors are hard to triage when multiple config inputs are present.

### [WL-7711]

**Title:** Stabilize workspace discovery by exposing ignored-root skip reasons in debug mode
**Source:** [thegent/src/thegent/discovery/workspace_scan.py:142]
**Acceptance checklist:**

- [ ] Emit concise debug-only skip reasons for ignored roots and invalid scan candidates.
- [ ] Preserve default non-verbose CLI output for normal runs.
- [ ] Add tests for ignored paths, invalid roots, and successful workspace discovery.
      **Notes:** Operators currently cannot tell whether projects were skipped intentionally or due to path normalization issues.

### [WL-7712]

**Title:** Improve retry-loop observability for flaky subprocess launches in CLI tooling
**Source:** [thegent/src/thegent/process/retry_runner.py:67]
**Acceptance checklist:**

- [ ] Add structured attempt counters and terminal failure reason reporting for launch retries.
- [ ] Preserve existing retry/backoff behavior and success return contract.
- [ ] Add tests for immediate success, eventual success after retries, and permanent launch failure.
      **Notes:** Retry behavior is present but lacks enough signal to diagnose recurring environment-specific launch flakiness.

### [WL-7713]

**Title:** Reduce session-switch confusion by validating stale symlink targets before activation
**Source:** [thegent/src/thegent/session/switch.py:118]
**Acceptance checklist:**

- [ ] Validate session symlink targets and fail with explicit remediation when targets are missing.
- [ ] Preserve successful fast-path switching for healthy sessions.
- [ ] Add tests for dangling symlink target, valid symlink target, and non-symlink session markers.
      **Notes:** Session switches can fail late when stale symlinks survive cleanup, creating ambiguous operator errors.

### [WL-7714]

**Title:** Improve template rendering devx with source-location hints for undefined variables
**Source:** [thegent/src/thegent/templates/render.py:203]
**Acceptance checklist:**

- [ ] Include template name and variable key in undefined-variable render errors.
- [ ] Preserve current rendering output for fully defined templates.
- [ ] Add tests for undefined variable failure formatting and successful render output parity.
      **Notes:** Template failures currently require manual tracing to discover which placeholder caused the render crash.

### [WL-7715]

**Title:** Harden cache TTL handling by rejecting negative durations at parse time
**Source:** [thegent/src/thegent/cache/policy.py:54]
**Acceptance checklist:**

- [ ] Add strict validation that rejects negative TTL values with clear configuration errors.
- [ ] Preserve support for existing positive TTL and zero-value semantics.
- [ ] Add tests for negative TTL rejection, zero TTL behavior, and positive TTL acceptance.
      **Notes:** Negative TTL values currently lead to non-obvious eviction behavior and inconsistent cache hit patterns.

### [WL-7716]

**Title:** Improve task-run UX by surfacing canceled-job summaries before cleanup
**Source:** [thegent/src/thegent/task/runner.py:276]
**Acceptance checklist:**

- [ ] Emit a compact canceled-job summary including task id, phase, and partial outputs preserved.
- [ ] Preserve current cleanup guarantees after cancellation.
- [ ] Add tests for user cancellation, timeout-triggered cancellation, and non-canceled execution.
      **Notes:** Cancellation paths currently clean up correctly but provide too little operator context about what completed.

### [WL-7717]

**Title:** Prevent noisy lock contention loops with bounded warning cadence in local state store
**Source:** [thegent/src/thegent/state/local_store.py:133]
**Acceptance checklist:**

- [ ] Add warning rate-limiting for repeated lock contention while retaining final failure visibility.
- [ ] Preserve existing lock acquisition timeout behavior.
- [ ] Add tests for transient contention, sustained contention, and uncontended acquisitions.
      **Notes:** High-frequency lock contention can flood logs and hide the first actionable failure signal.

### [WL-7718]

**Title:** Make environment doctor checks deterministic by normalizing PATH probe ordering
**Source:** [thegent/src/thegent/doctor/path_checks.py:88]
**Acceptance checklist:**

- [ ] Normalize PATH probe ordering to produce stable diagnostic output across shells.
- [ ] Preserve current pass/fail semantics for tool presence checks.
- [ ] Add tests for duplicate PATH segments, empty segments, and stable output ordering.
      **Notes:** Non-deterministic PATH probe output makes it harder to compare diagnostics between repeated runs.

### [WL-7719]

**Title:** Improve progress reporter reliability by guarding against negative remaining-step math
**Source:** [thegent/src/thegent/ui/progress_reporter.py:159]
**Acceptance checklist:**

- [ ] Clamp remaining-step calculations to non-negative values and log invariant violations.
- [ ] Preserve current progress event API and output schema.
- [ ] Add tests for out-of-order events, exact completion, and normal incremental progress.
      **Notes:** Rare out-of-order events can produce negative remaining-step values that confuse terminal progress output.
