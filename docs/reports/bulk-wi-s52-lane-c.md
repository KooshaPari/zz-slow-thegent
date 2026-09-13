### [WL-8140]

**Title:** Split queue claim ownership checks from stale-lock handling
**Source:** [thegent/src/thegent/queue/claim.py:332]
**Acceptance checklist:**

- [ ] Separate lock-owner mismatch branch from stale-lock expiry branch.
- [ ] Keep existing claim acquisition and release semantics.
- [ ] Add tests for ownership and staleness cases.
      **Notes:** Clarifies queue contention telemetry and avoids accidental retries.

### [WL-8141]

**Title:** Distinguish CLI profile parsing from execution dispatch failures
**Source:** [thegent/src/thegent/session/bootstrap.py:182]
**Acceptance checklist:**

- [ ] Validate profile schema before dispatching bootstrap commands.
- [ ] Keep bootstrap command behavior on invalid profile data.
- [ ] Add tests for malformed profile and execution failure paths.
      **Notes:** Helps isolate CLI config issues from runtime failures.

### [WL-8142]

**Title:** Separate artifact uploader payload validation from upload transport failures
**Source:** [thegent/src/thegent/artifacts/uploader.py:282]
**Acceptance checklist:**

- [ ] Validate payload shape before network request attempt.
- [ ] Preserve retry behavior for upload transport failures.
- [ ] Add tests for invalid payload and network timeout cases.
      **Notes:** Reduces repeated network retries due to invalid payloads.

### [WL-8143]

**Title:** Preserve workflow planner output while splitting interpolation errors from serialization
**Source:** [thegent/src/thegent/planner/task_planner.py:447]
**Acceptance checklist:**

- [ ] Split variable interpolation errors from JSON serialization errors.
- [ ] Preserve default planner output when interpolation is malformed but recoverable.
- [ ] Add tests for interpolation-only and serialization failures.
      **Notes:** Improves debuggability in templated task generation.

### [WL-8144]

**Title:** Keep history pruning behavior while separating malformed entries and file I/O failures
**Source:** [thegent/src/thegent/clipboard/history.py:182]
**Acceptance checklist:**

- [ ] Add dedicated branches for invalid timestamp entries and write failures.
- [ ] Preserve prune-by-age return contract.
- [ ] Add tests for malformed history and read-only store paths.
      **Notes:** Prevents hidden data-loss due to malformed history rows.

### [WL-8145]

**Title:** Separate dashboard command parse errors from execution exceptions
**Source:** [thegent/src/thegent/mesh/control.py:421]
**Acceptance checklist:**

- [ ] Differentiate parse errors from command-dispatch failures.
- [ ] Preserve existing command fallback behavior on invalid control commands.
- [ ] Add tests for each failure branch.
      **Notes:** More precise failures for mesh control operations.

### [WL-8146]

**Title:** Preserve execution fallback in cache rebuild while separating write errors from lock contention
**Source:** [thegent/src/thegent/cache/rebuilder.py:102]
**Acceptance checklist:**

- [ ] Split lock contention errors from file write errors.
- [ ] Keep fallback cache rebuild path for transient lock contention.
- [ ] Add tests for locked file and write-permission scenarios.
      **Notes:** Avoids masking root causes in rebuild retries.

### [WL-8147]

**Title:** Separate plugin load schema failures from plugin import failures
**Source:** [thegent/src/thegent/ui/plugin_loader.py:282]
**Acceptance checklist:**

- [ ] Validate plugin manifest schema before import.
- [ ] Keep no-plugin fallback when discovery schema is invalid.
- [ ] Add tests for invalid manifests and import exceptions.
      **Notes:** Better diagnosis for plugin startup instability.

### [WL-8148]

**Title:** Preserve health endpoint contract while splitting JSON serialization and request decode
**Source:** [thegent/src/thegent/health/endpoint.py:112]
**Acceptance checklist:**

- [ ] Separate request decode failures from response serialization failures.
- [ ] Preserve status codes used by upstream monitors.
- [ ] Add tests for both malformed request and serialization faults.
      **Notes:** Helps diagnose partial health-system degradations.

### [WL-8149]

**Title:** Preserve retention policy execution while separating dry-run validation and purge failures
**Source:** [thegent/src/thegent/artifacts/retention.py:188]
**Acceptance checklist:**

- [ ] Distinguish dry-run mode validation from actual delete/write failures.
- [ ] Preserve retention behavior and reporting output.
- [ ] Add tests for dry-run misuse and purge exception cases.
      **Notes:** Avoids misclassifying intentional dry-run errors.
