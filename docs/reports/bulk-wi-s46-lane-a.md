### [WL-7820]

**Title:** Add per-command startup timing buckets in CLI bootstrap diagnostics
**Source:** [thegent/src/thegent/cli/bootstrap.py:88]
**Acceptance checklist:**

- [ ] Emit deterministic timing buckets for init phases when diagnostics mode is enabled.
- [ ] Preserve current default startup output when diagnostics mode is disabled.
- [ ] Add tests for diagnostics-on output, diagnostics-off silence, and stable field ordering.
      **Notes:** Timing visibility at bootstrap boundaries is required to isolate slow-start regressions quickly.

### [WL-7821]

**Title:** Surface line and column context for configuration parse failures
**Source:** [thegent/src/thegent/config/loader.py:134]
**Acceptance checklist:**

- [ ] Include line, column, and short token context in parse error messages.
- [ ] Preserve existing non-zero failure semantics for malformed config files.
- [ ] Add tests for malformed YAML, malformed JSON, and successful parse behavior.
      **Notes:** Parse diagnostics should be explicit enough to fix invalid config files without additional tracing.

### [WL-7822]

**Title:** Enforce idempotent interrupt handling for runtime shutdown banners
**Source:** [thegent/src/thegent/runtime/shutdown.py:59]
**Acceptance checklist:**

- [ ] Ensure repeated interrupt signals do not emit duplicate shutdown banners.
- [ ] Preserve graceful cleanup execution on the first interrupt.
- [ ] Add tests for single interrupt, repeated interrupt burst, and post-shutdown no-op behavior.
      **Notes:** Duplicate interrupt output currently obscures actionable shutdown errors during termination.

### [WL-7823]

**Title:** Make cache version mismatch reporting explicit before rebuild
**Source:** [thegent/src/thegent/cache/index.py:173]
**Acceptance checklist:**

- [ ] Detect and report expected vs actual cache metadata version before invalidation.
- [ ] Preserve automatic rebuild flow once mismatch is detected.
- [ ] Add tests for matching versions, mismatched versions, and missing metadata files.
      **Notes:** Version drift should be visible so cache rebuilds are explainable and auditable.

### [WL-7824]

**Title:** Stabilize command suggestion rank ordering with prefix-first precedence
**Source:** [thegent/src/thegent/cli/suggest.py:102]
**Acceptance checklist:**

- [ ] Rank exact prefix matches ahead of fuzzy-only candidates.
- [ ] Preserve fuzzy fallback behavior when no prefix matches exist.
- [ ] Add tests for prefix-priority ordering, fuzzy fallback, and deterministic tie handling.
      **Notes:** Predictable suggestion ordering reduces repeated lookup friction in interactive CLI sessions.

### [WL-7825]

**Title:** Include worker crash context with task label and heartbeat age
**Source:** [thegent/src/thegent/workers/supervisor.py:147]
**Acceptance checklist:**

- [ ] Attach task label and last-heartbeat age to worker crash diagnostics.
- [ ] Preserve current crash propagation and exit behavior.
- [ ] Add tests for healthy workers, abrupt crash events, and stale-heartbeat crash paths.
      **Notes:** Crash events need richer context to shorten triage loops for unstable worker pools.

### [WL-7826]

**Title:** Skip no-op state persistence when serialized content is unchanged
**Source:** [thegent/src/thegent/state/store.py:91]
**Acceptance checklist:**

- [ ] Avoid disk writes when new serialized state hash matches the latest persisted hash.
- [ ] Preserve immediate persistence behavior when state content changes.
- [ ] Add tests for unchanged-state skip, changed-state write, and restart hash initialization.
      **Notes:** Eliminating redundant writes reduces filesystem churn without altering persistence guarantees.

### [WL-7827]

**Title:** Emit retry exhaustion summaries with attempts and total backoff
**Source:** [thegent/src/thegent/net/retry.py:118]
**Acceptance checklist:**

- [ ] Emit terminal retry summary including attempt count and cumulative wait duration.
- [ ] Preserve existing per-attempt debug logging behavior.
- [ ] Add tests for immediate success, eventual success, and exhausted retry sequences.
      **Notes:** Aggregate retry outcomes are needed to distinguish transient from persistent network failures.

### [WL-7828]

**Title:** Reject workspace-relative paths containing control characters
**Source:** [thegent/src/thegent/fs/paths.py:67]
**Acceptance checklist:**

- [ ] Reject control-character inputs before path normalization occurs.
- [ ] Preserve normal behavior for valid workspace-relative ASCII paths.
- [ ] Add tests for control-character rejection, valid normalization, and traversal rejection parity.
      **Notes:** Hidden control bytes can create ambiguous path resolution and should fail validation early.

### [WL-7829]

**Title:** Add concise post-run failure recap for parallel test execution
**Source:** [thegent/src/thegent/test/runner.py:201]
**Acceptance checklist:**

- [ ] Print a grouped failure recap after parallel test execution completes.
- [ ] Preserve full failure detail output and existing exit code behavior.
- [ ] Add tests for all-pass runs, mixed outcomes, and deterministic recap ordering.
      **Notes:** A compact recap prevents important failures from being buried in interleaved parallel logs.
