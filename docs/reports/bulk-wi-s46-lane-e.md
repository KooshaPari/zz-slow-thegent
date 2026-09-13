### [WL-7860]

**Title:** Add clear dry-run summary totals to cleanup command output
**Source:** [thegent/src/thegent/cli/cleanup.py:93]
**Acceptance checklist:**

- [ ] Print a final dry-run summary with total files, total bytes, and skipped entries.
- [ ] Preserve current destructive behavior only when dry-run is explicitly disabled.
- [ ] Add tests for dry-run totals, empty-target runs, and mixed eligible/skipped artifacts.
      **Notes:** Cleanup previews currently list individual items but do not provide a quick aggregate impact view.

### [WL-7861]

**Title:** Improve env var validation errors with missing-vs-empty distinction
**Source:** [thegent/src/thegent/config/env_validation.py:71]
**Acceptance checklist:**

- [ ] Distinguish unset environment variables from variables set to empty values in validation failures.
- [ ] Preserve current startup failure behavior when required environment values are invalid.
- [ ] Add tests for missing vars, empty vars, and valid populated values.
      **Notes:** Treating missing and empty values identically slows local debugging of startup configuration issues.

### [WL-7862]

**Title:** Prevent progress bar regressions by clamping non-monotonic completion updates
**Source:** [thegent/src/thegent/ui/progress.py:128]
**Acceptance checklist:**

- [ ] Clamp completion values to avoid backward movement for a given task instance.
- [ ] Preserve final 100% completion rendering and existing status label behavior.
- [ ] Add tests for monotonic updates, out-of-order updates, and completion edge cases.
      **Notes:** Out-of-order task events can cause progress bars to jump backward and erode operator confidence.

### [WL-7863]

**Title:** Add deterministic timeout error suffix showing configured limit and elapsed time
**Source:** [thegent/src/thegent/runtime/timeouts.py:84]
**Acceptance checklist:**

- [ ] Append a stable timeout suffix that includes configured timeout and measured elapsed duration.
- [ ] Preserve timeout exception type and non-zero exit behavior.
- [ ] Add tests for timeout-triggered runs, non-timeout runs, and suffix formatting determinism.
      **Notes:** Timeout failures currently lack enough context to tell whether limits are misconfigured or execution regressed.

### [WL-7864]

**Title:** Reduce command typo friction with nearest-subcommand hint in parser failures
**Source:** [thegent/src/thegent/cli/parser.py:156]
**Acceptance checklist:**

- [ ] Show one nearest valid subcommand suggestion when parsing fails on an unknown command token.
- [ ] Preserve existing help text rendering and exit code semantics for invalid invocations.
- [ ] Add tests for single-close match, no-close-match fallback, and multi-command namespaces.
      **Notes:** Small command typos currently force full help scans instead of offering immediate corrective guidance.

### [WL-7865]

**Title:** Stabilize JSON log output by enforcing key order for top-level event fields
**Source:** [thegent/src/thegent/logging/json_sink.py:49]
**Acceptance checklist:**

- [ ] Emit top-level JSON event fields in stable key order across runs.
- [ ] Preserve log payload values and existing event schema.
- [ ] Add tests for key-order determinism, schema parity, and nested payload passthrough.
      **Notes:** Non-deterministic key ordering creates noisy diffs in local snapshots and CI log fixture checks.

### [WL-7866]

**Title:** Add file-lock contention diagnostics with holder PID and wait duration
**Source:** [thegent/src/thegent/locks/file_lock.py:117]
**Acceptance checklist:**

- [ ] Include lock-holder PID metadata and total wait time when lock acquisition times out.
- [ ] Preserve existing lock timeout behavior and failure exit semantics.
- [ ] Add tests for immediate acquisition, contention timeout, and stale lock metadata handling.
      **Notes:** Lock timeout messages are currently too sparse to identify which process is blocking progress.

### [WL-7867]

**Title:** Improve local cache prune safety with explicit protected-prefix allowlist checks
**Source:** [thegent/src/thegent/cache/prune.py:102]
**Acceptance checklist:**

- [ ] Enforce protected-prefix allowlist checks before deleting cache entries.
- [ ] Preserve successful pruning for non-protected entries and current summary reporting.
- [ ] Add tests for protected-prefix rejection, valid prune paths, and malformed entry metadata.
      **Notes:** Cache prune operations need clearer guardrails to prevent accidental removal of reserved artifacts.

### [WL-7868]

**Title:** Surface plugin load failures with plugin name and normalized import target
**Source:** [thegent/src/thegent/plugins/loader.py:139]
**Acceptance checklist:**

- [ ] Include plugin name and normalized import target in plugin load error output.
- [ ] Preserve fail-fast plugin initialization behavior on load errors.
- [ ] Add tests for successful plugin load, import failure diagnostics, and invalid plugin spec rejection.
      **Notes:** Plugin load exceptions currently provide stack traces without enough plugin identity context for fast triage.

### [WL-7869]

**Title:** Add focused post-run warning summary section to reduce scrollback hunting
**Source:** [thegent/src/thegent/reporting/run_summary.py:211]
**Acceptance checklist:**

- [ ] Print a compact warnings-only summary section at run end with stable ordering.
- [ ] Preserve full inline warning emission during execution.
- [ ] Add tests for no-warning runs, multi-warning runs, and summary ordering determinism.
      **Notes:** Actionable warnings are easy to miss in long output streams without an end-of-run recap.
