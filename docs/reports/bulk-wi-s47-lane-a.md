### [WL-7870]

**Title:** Add explicit timeout reason tags to MCP startup failure events
**Source:** [thegent/src/thegent/mcp/launcher.py:112]
**Acceptance checklist:**

- [ ] Emit structured timeout reason tags for each startup failure path.
- [ ] Preserve current non-timeout failure handling and exit semantics.
- [ ] Add tests for timeout, immediate success, and non-timeout startup failure classification.
      **Notes:** Failure tags must clearly separate startup timeout incidents from other boot errors.

### [WL-7871]

**Title:** Validate session-id format before dispatching stop requests
**Source:** [thegent/src/thegent/cli/session.py:79]
**Acceptance checklist:**

- [ ] Reject malformed session-id inputs with actionable validation errors.
- [ ] Preserve successful stop behavior for valid session-id values.
- [ ] Add tests for invalid format rejection, unknown session-id handling, and valid stop dispatch.
      **Notes:** Early session-id validation prevents noisy downstream failures in session lifecycle commands.

### [WL-7872]

**Title:** Include queue depth metrics in worker-pool saturation warnings
**Source:** [thegent/src/thegent/workers/pool.py:156]
**Acceptance checklist:**

- [ ] Attach current queue depth and configured capacity to saturation warnings.
- [ ] Preserve warning emission thresholds and existing task scheduling behavior.
- [ ] Add tests for below-threshold silence, threshold crossing warning content, and steady-state saturation logging.
      **Notes:** Saturation warnings need queue depth context to prioritize throughput tuning work.

### [WL-7873]

**Title:** Enforce deterministic ordering for merged config overlays
**Source:** [thegent/src/thegent/config/merge.py:98]
**Acceptance checklist:**

- [ ] Apply overlays in a stable documented order across repeated runs.
- [ ] Preserve override precedence semantics for conflicting keys.
- [ ] Add tests for deterministic ordering, conflict precedence, and no-op overlay merges.
      **Notes:** Stable overlay order is required for reproducible configuration behavior across environments.

### [WL-7874]

**Title:** Report active profile name in runtime preflight output
**Source:** [thegent/src/thegent/runtime/preflight.py:44]
**Acceptance checklist:**

- [ ] Print the resolved active profile name in preflight diagnostics output.
- [ ] Preserve current preflight pass/fail decisions and error propagation.
- [ ] Add tests for default profile reporting, explicit profile reporting, and preflight failure paths.
      **Notes:** Profile visibility in preflight output shortens misconfiguration triage loops.

### [WL-7875]

**Title:** Fail fast on duplicate tool aliases during command registry build
**Source:** [thegent/src/thegent/tools/registry.py:131]
**Acceptance checklist:**

- [ ] Detect duplicate aliases and stop registry build with explicit conflict details.
- [ ] Preserve successful registry construction when aliases are unique.
- [ ] Add tests for duplicate alias failure, unique alias success, and alias lookup integrity.
      **Notes:** Duplicate aliases must hard-fail to avoid ambiguous tool dispatch at runtime.

### [WL-7876]

**Title:** Add monotonic elapsed-ms fields to retry attempt logs
**Source:** [thegent/src/thegent/net/backoff.py:87]
**Acceptance checklist:**

- [ ] Include monotonic elapsed-ms values on each retry-attempt log record.
- [ ] Preserve existing retry intervals and max-attempt enforcement.
- [ ] Add tests for elapsed-ms presence, interval behavior, and retry exhaustion logging.
      **Notes:** Monotonic elapsed timing makes retry latency regressions observable without external tracing.

### [WL-7877]

**Title:** Gate unsafe workspace path writes behind explicit allowlist checks
**Source:** [thegent/src/thegent/fs/workspace_guard.py:63]
**Acceptance checklist:**

- [ ] Block writes outside allowlisted workspace roots with explicit error messages.
- [ ] Preserve allowed write behavior for in-scope normalized paths.
- [ ] Add tests for outside-root rejection, inside-root success, and normalization edge cases.
      **Notes:** Strict path-write gating is required to prevent accidental writes beyond managed workspace boundaries.

### [WL-7878]

**Title:** Emit compact summary for skipped tests with reason counts
**Source:** [thegent/src/thegent/test/reporting.py:209]
**Acceptance checklist:**

- [ ] Print a post-run skipped-test summary grouped by skip reason with counts.
- [ ] Preserve per-test skip detail output and existing final exit code behavior.
- [ ] Add tests for no-skip runs, single-reason skips, and multi-reason grouping determinism.
      **Notes:** Grouped skip summaries keep large test outputs actionable without removing detailed evidence.

### [WL-7879]

**Title:** Add checksum mismatch details to artifact integrity validation errors
**Source:** [thegent/src/thegent/artifacts/verify.py:142]
**Acceptance checklist:**

- [ ] Include expected and observed checksum values in integrity failure messages.
- [ ] Preserve successful validation flow and current artifact accept behavior.
- [ ] Add tests for checksum match success, mismatch failure details, and missing-checksum handling.
      **Notes:** Integrity errors must include checksum diffs so artifact corruption can be diagnosed quickly.
