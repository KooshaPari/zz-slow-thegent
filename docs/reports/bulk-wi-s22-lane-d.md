### [WL-6650]

**Title:** Replace silent registry tail-hash failures with typed error handling and debug diagnostics.
**Source Path+Line:** [thegent/src/thegent/execution.py:1452]
**Acceptance Checklist:**

- [ ] Catch JSON decoding and file I/O exceptions explicitly in `_get_last_hash`.
- [ ] Emit debug-level context for malformed trailing records before falling back.
- [ ] Add unit coverage for empty, truncated, and invalid JSONL registry tails.
      **Notes:** Current broad exception suppression can hide data-quality issues in append-only run ledgers.

### [WL-6651]

**Title:** Make auto-template marker resolution report which marker triggered `ag-dd` selection.
**Source Path+Line:** [thegent/src/thegent/cli/apps/project.py:672]
**Acceptance Checklist:**

- [ ] Add optional diagnostics payload listing matched marker paths during `_resolve_migration_template`.
- [ ] Keep default CLI behavior unchanged when diagnostics mode is off.
- [ ] Add regression tests for mixed marker presence and fallback-template behavior.
      **Notes:** Operators currently cannot tell why `auto` resolved to `ag-dd` in ambiguous repositories.

### [WL-6652]

**Title:** Expand justified `noqa` parsing to support comma-separated code suppressions.
**Source Path+Line:** [thegent/src/thegent/governance/native_governance_scan.py:81]
**Acceptance Checklist:**

- [ ] Update `_SUPPRESSION_JUSTIFIED_RE` to accept `# noqa: CODE1, CODE2 -- reason` formats.
- [ ] Preserve rejection of bare `# noqa` without inline justification.
- [ ] Add fixture tests for valid multi-code, single-code, and invalid suppression comments.
      **Notes:** Current regex can misclassify legitimate multi-code suppressions as governance violations.

### [WL-6653]

**Title:** Remove silent enrichment degradation when model quality/speed lookup imports fail.
**Source Path+Line:** [thegent/src/thegent/planning/selector.py:81]
**Acceptance Checklist:**

- [ ] Replace broad exception suppression in `_calculate_score` with typed import/lookup handling.
- [ ] Emit deterministic fallback diagnostics when enrichment modules are unavailable.
- [ ] Add tests covering normal enrichment and forced import-failure paths.
      **Notes:** Silent fallback to metadata-only scoring makes selection drift difficult to diagnose.

### [WL-6654]

**Title:** Instrument native tag-extraction failures before Python parser fallback.
**Source Path+Line:** [thegent/src/thegent/contracts/parser.py:224]
**Acceptance Checklist:**

- [ ] Catch and log native parser invocation exceptions with enough context for debugging.
- [ ] Keep Python fallback behavior and return shape unchanged.
- [ ] Add tests that simulate native parser failures and assert fallback correctness.
      **Notes:** The current `except Exception: pass` path hides native-extension regressions.

### [WL-6655]

**Title:** Return structured command-failure details from zmx command runner helpers.
**Source Path+Line:** [thegent/src/thegent/session/zmx_backend.py:257]
**Acceptance Checklist:**

- [ ] Refactor `_run` to preserve return code/stderr metadata in a typed result object.
- [ ] Update call sites to consume structured failure details without changing success behavior.
- [ ] Add tests covering timeout, non-zero exit, and `OSError` branches.
      **Notes:** Boolean-only command results reduce observability for session attach/list failures.

### [WL-6656]

**Title:** Differentiate filesystem and serialization failures in markdown conversation dump writes.
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:164]
**Acceptance Checklist:**

- [ ] Split exception handling to distinguish `record.to_markdown()` failures from file write failures.
- [ ] Include the failing phase in raised `OSError` messages while preserving chaining.
- [ ] Add tests for serializer exceptions and write-permission failures.
      **Notes:** A single catch-all error path obscures root cause during dump troubleshooting.

### [WL-6657]

**Title:** Add JSON serialization diagnostics parity for conversation JSON dump writes.
**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance Checklist:**

- [ ] Handle `json.dumps` serialization errors separately from filesystem write failures.
- [ ] Emit consistent error taxonomy with the markdown dump path for operator clarity.
- [ ] Extend tests to validate error messages and exception chaining for both failure classes.
      **Notes:** JSON dump failure reporting should mirror markdown dump semantics for consistent support workflows.

### [WL-6658]

**Title:** Preserve subprocess exit metadata in helper `run_checks` failure summaries.
**Source Path+Line:** [thegent/scripts/agent_helpers.py:414]
**Acceptance Checklist:**

- [ ] Include exit code and command label in returned error payloads from `_run`.
- [ ] Truncate logged stdout/stderr safely while retaining actionable diagnostics.
- [ ] Add unit tests for command-not-found, timeout, and non-zero exit scenarios.
      **Notes:** Current summary truncation can drop the key reason a lint/test command failed.

### [WL-6659]

**Title:** Validate and report malformed coverage-report JSON instead of raising untyped exceptions.
**Source Path+Line:** [thegent/scripts/monitor_e2e_test_progress.py:25]
**Acceptance Checklist:**

- [ ] Guard `json.load` with typed decode handling and return a structured empty-report fallback.
- [ ] Print a concise warning that distinguishes missing file vs malformed JSON content.
- [ ] Add tests for missing, malformed, and valid coverage report inputs.
      **Notes:** Corrupt coverage artifacts currently bubble raw parse errors and interrupt progress reporting.
