### [WL-7810]

**Title:** Add startup timing breakdown to CLI diagnostics for slow-boot triage
**Source:** [thegent/src/thegent/cli/bootstrap.py:88]
**Acceptance checklist:**

- [ ] Emit a compact timing breakdown for key startup phases when diagnostics mode is enabled.
- [ ] Preserve default quiet startup output when diagnostics mode is disabled.
- [ ] Add tests for diagnostics-enabled timing output, disabled mode silence, and deterministic key ordering.
      **Notes:** Startup slowdowns are difficult to localize because current logs do not split initialization cost by phase.

### [WL-7811]

**Title:** Make config file parse errors show line and column with offending token preview
**Source:** [thegent/src/thegent/config/loader.py:134]
**Acceptance checklist:**

- [ ] Include line, column, and a short offending token preview in config parse failures.
- [ ] Preserve current failure exit semantics for invalid config files.
- [ ] Add tests for malformed YAML, malformed JSON, and successful load behavior.
      **Notes:** Current parse errors are technically correct but too opaque for fast local fixes.

### [WL-7812]

**Title:** Prevent duplicate Ctrl-C handling from emitting repeated shutdown banners
**Source:** [thegent/src/thegent/runtime/shutdown.py:59]
**Acceptance checklist:**

- [ ] Ensure shutdown banner emission is idempotent across repeated interrupt signals.
- [ ] Preserve graceful cleanup execution for the first interrupt.
- [ ] Add tests for single interrupt, rapid repeated interrupts, and post-shutdown no-op handling.
      **Notes:** Multiple interrupt events can spam terminal output and obscure real shutdown errors.

### [WL-7813]

**Title:** Add explicit cache metadata version mismatch message before cache rebuild
**Source:** [thegent/src/thegent/cache/index.py:173]
**Acceptance checklist:**

- [ ] Detect metadata version mismatches and emit a clear message naming expected and actual versions.
- [ ] Preserve automatic cache rebuild behavior after mismatch detection.
- [ ] Add tests for matching versions, mismatched versions, and missing metadata file handling.
      **Notes:** Silent cache invalidation behavior can feel like random slowness without clear user feedback.

### [WL-7814]

**Title:** Stabilize command suggestion ranking by preferring exact prefix matches first
**Source:** [thegent/src/thegent/cli/suggest.py:102]
**Acceptance checklist:**

- [ ] Rank exact prefix matches ahead of fuzzy-only candidates in command suggestions.
- [ ] Preserve existing fuzzy suggestion fallback when no prefix match exists.
- [ ] Add tests for exact-prefix priority, fuzzy fallback, and tie-breaking determinism.
      **Notes:** Suggestion ordering currently varies in ways that slow down repeated shell usage.

### [WL-7815]

**Title:** Improve worker crash reporting with last-heartbeat age and task label
**Source:** [thegent/src/thegent/workers/supervisor.py:147]
**Acceptance checklist:**

- [ ] Include worker task label and last-heartbeat age in crash diagnostics.
- [ ] Preserve existing non-zero exit and crash propagation behavior.
- [ ] Add tests for healthy worker, abrupt worker crash, and stale-heartbeat crash contexts.
      **Notes:** Crash logs currently omit the operational context needed for quick root-cause triage.

### [WL-7816]

**Title:** Avoid noisy no-op writes by skipping state file flush when content hash is unchanged
**Source:** [thegent/src/thegent/state/store.py:91]
**Acceptance checklist:**

- [ ] Skip disk writes when serialized state content hash matches the most recent persisted value.
- [ ] Preserve immediate persistence when state content changes.
- [ ] Add tests for unchanged state skip, changed state write, and process restart hash initialization.
      **Notes:** Frequent identical writes add unnecessary filesystem churn during local iteration.

### [WL-7817]

**Title:** Add retry budget exhaustion summary with attempt count and cumulative wait
**Source:** [thegent/src/thegent/net/retry.py:118]
**Acceptance checklist:**

- [ ] Emit final retry exhaustion summary including total attempts and cumulative backoff duration.
- [ ] Preserve per-attempt logging behavior in debug mode.
- [ ] Add tests for immediate success, eventual success, and exhausted retries.
      **Notes:** Final retry failures currently lack aggregate context needed to judge network stability.

### [WL-7818]

**Title:** Harden path normalization by rejecting control characters in workspace-relative inputs
**Source:** [thegent/src/thegent/fs/paths.py:67]
**Acceptance checklist:**

- [ ] Reject workspace-relative path inputs containing control characters before normalization.
- [ ] Preserve valid path normalization behavior for ordinary ASCII paths.
- [ ] Add tests for control-character rejection, valid normalization, and traversal rejection parity.
      **Notes:** Hidden control characters can create confusing file resolution behavior and hard-to-debug errors.

### [WL-7819]

**Title:** Improve test-run UX by printing concise failure recap after parallel suite completion
**Source:** [thegent/src/thegent/test/runner.py:201]
**Acceptance checklist:**

- [ ] Print a short grouped failure recap after parallel test execution completes.
- [ ] Preserve full detailed failure output and existing exit codes.
- [ ] Add tests for all-pass runs, mixed pass/fail runs, and recap ordering determinism.
      **Notes:** In long parallel runs, actionable failures are buried in interleaved output and are easy to miss.
