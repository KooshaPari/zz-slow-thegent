### [WL-7790]

**Title:** Preserve jsonl task load decode failures as structured diagnostics instead of returning empty task sets
**Source:** [thegent/src/thegent/tasking/task_file.py:44]
**Acceptance checklist:**

- [ ] Replace broad decode/load exception swallowing with explicit diagnostic metadata (path, exception type, row index).
- [ ] Keep successful JSONL task loading behavior unchanged for valid task files.
- [ ] Add tests for valid JSONL, malformed JSON rows, and unreadable file paths.
      **Notes:** Silent fallback to empty results hides task file corruption and can mislead automation into treating invalid state as no-work state.

### [WL-7791]

**Title:** Report agent registry parse failures with actionable context during startup refresh
**Source:** [thegent/src/thegent/agents/registry.py:118]
**Acceptance checklist:**

- [ ] Surface registry parse failures with file path and parse reason instead of generic falsey return values.
- [ ] Preserve existing registration behavior for valid agent manifests.
- [ ] Add tests for valid manifest loads, malformed entries, and missing registry files.
      **Notes:** Hidden registry-load failures can produce partially initialized agent pools that are difficult to debug in production.

### [WL-7792]

**Title:** Make session metadata timestamp normalization failures visible in listing output
**Source:** [thegent/src/thegent/sessions/store.py:93]
**Acceptance checklist:**

- [ ] Replace silent timestamp normalization fallback with explicit invalid-timestamp markers in session metadata.
- [ ] Preserve sorting/filter semantics for sessions with valid timestamps.
- [ ] Add tests for valid ISO timestamps, malformed timestamp strings, and timezone-offset variants.
      **Notes:** Suppressed timestamp parse errors can reorder sessions unpredictably and hide stale-state cleanup risks.

### [WL-7793]

**Title:** Expose command runner environment merge conflicts instead of silently overriding keys
**Source:** [thegent/src/thegent/runtime/command_runner.py:67]
**Acceptance checklist:**

- [ ] Detect conflicting environment keys between base env and overrides and emit structured conflict diagnostics.
- [ ] Preserve current execution flow for non-conflicting environment merges.
- [ ] Add tests for non-conflicting merges, conflicting key merges, and empty override maps.
      **Notes:** Silent key override behavior makes runtime mismatches hard to trace when command execution depends on precise env composition.

### [WL-7794]

**Title:** Emit typed workspace discovery failures when repository root resolution is ambiguous
**Source:** [thegent/src/thegent/workspace/discovery.py:52]
**Acceptance checklist:**

- [ ] Replace generic fallback root selection with typed ambiguity errors that include inspected candidates.
- [ ] Keep current root resolution behavior for single-candidate and explicit-root paths.
- [ ] Add tests for unambiguous roots, multi-candidate ambiguity, and nonexistent candidate directories.
      **Notes:** Implicitly selecting a fallback root can direct writes to the wrong repository and invalidate downstream reports.

### [WL-7795]

**Title:** Capture queue compaction rewrite failures without dropping original queue file visibility
**Source:** [thegent/src/thegent/queue/compaction.py:141]
**Acceptance checklist:**

- [ ] Preserve and report original queue-file location and rewrite failure details when compaction write fails.
- [ ] Keep successful compaction behavior unchanged for fully valid queue content.
- [ ] Add tests for successful compaction, temp-file write failure, and atomic replace failure paths.
      **Notes:** Current failure handling risks obscuring where recoverable queue data remains after interrupted compaction.

### [WL-7796]

**Title:** Record markdown report render template lookup misses with deterministic fallback metadata
**Source:** [thegent/src/thegent/reports/render.py:109]
**Acceptance checklist:**

- [ ] Emit explicit template lookup miss diagnostics with requested template key and search roots.
- [ ] Preserve render output behavior for existing templates and explicit template paths.
- [ ] Add tests for found templates, missing templates, and invalid template directory configuration.
      **Notes:** Silent template fallback can yield unexpected report layouts while masking configuration drift.

### [WL-7797]

**Title:** Surface sync manifest merge conflicts as first-class errors instead of last-write-wins behavior
**Source:** [thegent/src/thegent/sync/manifest_merge.py:76]
**Acceptance checklist:**

- [ ] Detect conflicting manifest keys during merge and return structured conflict details.
- [ ] Preserve merge behavior for non-conflicting manifests.
- [ ] Add tests for conflict-free merges, single-key conflicts, and multi-file conflict aggregation.
      **Notes:** Last-write-wins without diagnostics can silently discard intended sync directives.

### [WL-7798]

**Title:** Report profile selection fallback reasons when preferred profile resolution fails
**Source:** [thegent/src/thegent/config/profile_select.py:58]
**Acceptance checklist:**

- [ ] Expose explicit fallback reason codes when preferred profile resolution fails.
- [ ] Preserve selection behavior for valid preferred-profile inputs.
- [ ] Add tests for preferred-profile hit, missing preferred profile fallback, and invalid profile schema.
      **Notes:** Opaque fallback behavior complicates debugging when runtime behavior differs from configured profile intent.

### [WL-7799]

**Title:** Emit structured artifact copy partial-failure summaries for multi-file export operations
**Source:** [thegent/src/thegent/artifacts/export.py:132]
**Acceptance checklist:**

- [ ] Track per-file copy failures and return a partial-success summary with failed paths and error classes.
- [ ] Preserve current success behavior when all artifacts copy without errors.
- [ ] Add tests for all-success exports, mixed success/failure exports, and destination permission failures.
      **Notes:** Silent per-file copy skips can produce incomplete exports that appear successful to downstream automation.
