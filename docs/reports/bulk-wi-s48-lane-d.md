### [WL-7950]

**Title:** Surface parse failures from task sync with file-scoped diagnostics
**Source:** [thegent/src/thegent/task/sync.py:48]
**Acceptance checklist:**

- [ ] Replace per-file `except Exception: continue` in `update_work_stream_from_tasks()` with explicit error capture that records `task_file` and exception text.
- [ ] Return an `errors` collection alongside `tasks_synced`/`backlog_rows` without aborting successful file parsing.
- [ ] Add unit tests for all-valid, mixed-validity, and all-invalid task directories verifying stable error payload structure.
      **Notes:** Current behavior silently drops invalid task files and obscures why rows are missing from BACKLOG.

### [WL-7951]

**Title:** Escape markdown-reserved characters before rendering BACKLOG rows
**Source:** [thegent/src/thegent/task/sync.py:60]
**Acceptance checklist:**

- [ ] Add a reusable sanitizer for table-cell content used by `task_id`, `title`, `source`, and `depends` when emitting backlog rows.
- [ ] Ensure newline and pipe characters are normalized so generated markdown table rows remain 5-column compliant.
- [ ] Add tests with embedded `|`, newline, and code-span text to confirm output round-trips through `parse_workstream()`.
      **Notes:** Direct interpolation can corrupt table parsing and downstream claim/complete workflows.

### [WL-7952]

**Title:** Emit structured multi-error schema validation results
**Source:** [thegent/src/thegent/task/validator.py:78]
**Acceptance checklist:**

- [ ] Replace single exception string collapsing in `TaskValidator.validate()` with extraction of all schema violations exposed by `FastJSONSchemaValidator`.
- [ ] Map violations into `ValidationError` entries with deterministic `field`, `path`, and `code` semantics.
- [ ] Add tests asserting multiple invalid fields produce complete, stably ordered error lists.
      **Notes:** One-error collapse slows remediation by forcing repeated validate/fix cycles.

### [WL-7953]

**Title:** Replace regex frontmatter parsing with delimiter-aware scanning
**Source:** [thegent/src/thegent/task/parser.py:28]
**Acceptance checklist:**

- [ ] Refactor `parse_yaml_frontmatter()` to scan line boundaries for opening/closing `---` delimiters instead of regex dotall capture.
- [ ] Reject malformed files with missing or duplicated delimiter blocks using explicit `ValueError` messages.
- [ ] Add tests covering trailing-newline variance, body-only documents, and embedded `---` lines in markdown body content.
      **Notes:** Current regex strategy is brittle for malformed inputs and can mis-split body content.

### [WL-7954]

**Title:** Remove swallowed migration extraction errors and report warnings explicitly
**Source:** [thegent/src/thegent/task/migrate.py:64]
**Acceptance checklist:**

- [ ] Replace `except Exception: pass` in WORK_STREAM detail extraction with typed handling that records warning metadata.
- [ ] Preserve successful migration output when enrichment fails, but include warning details in the returned migration result.
- [ ] Add tests for unreadable/missing/corrupt WORK_STREAM files verifying warnings are surfaced and migration continues.
      **Notes:** Silent failure hides migration defects and makes reconciliation difficult.

### [WL-7955]

**Title:** Add retry attempt budget and dead-letter path to task queue
**Source:** [thegent/src/thegent/task_queue/queue.py:32]
**Acceptance checklist:**

- [ ] Track retry attempt counts per `task_id` in `TaskQueue` and enforce a configurable maximum before rejecting requeue.
- [ ] Add a dead-letter collection for exhausted retries while preserving existing transient failure-class filtering.
- [ ] Add tests for dedupe behavior, attempt exhaustion, and retry cleanup after `complete()`.
      **Notes:** Unlimited transient retries can churn indefinitely and starve fresh queue work.

### [WL-7956]

**Title:** Fail loudly on unknown-team broadcasts in coordination protocol
**Source:** [thegent/src/thegent/team/coordination.py:63]
**Acceptance checklist:**

- [ ] Change `broadcast_message()` to raise a typed error (or return an explicit failure object) when `team_meta_path` is missing.
- [ ] Include `team_id` and `sender` in failure diagnostics to support run-time troubleshooting.
- [ ] Add tests for happy-path broadcast, unknown-team failure, and sender-exclusion behavior.
      **Notes:** Silent no-op broadcasts lose coordination signals without any observable failure path.

### [WL-7957]

**Title:** Make layout container CSS selectors deterministic across runs
**Source:** [thegent/src/thegent/ui/compositor/layout_engine.py:226]
**Acceptance checklist:**

- [ ] Replace `.layout-{id(self)}` generation with deterministic node identifiers derived from tree position or explicit node ids.
- [ ] Keep emitted direction/size CSS semantics unchanged for existing layouts.
- [ ] Add snapshot tests proving equivalent layout trees emit byte-stable CSS across repeated executions.
      **Notes:** Process-memory-derived IDs create flaky snapshots and unstable style diffs.

### [WL-7958]

**Title:** Define explicit overflow behavior for async trace queue saturation
**Source:** [thegent/src/thegent/trace/recorder.py:211]
**Acceptance checklist:**

- [ ] Add configurable overflow modes (`drop_newest`, `drop_oldest`, `error`) for `write_queue` saturation in async mode.
- [ ] Remove implicit sync-write fallback on `QueueFull` and emit structured overflow metrics/counters.
- [ ] Add async tests forcing queue pressure to verify each overflow mode and telemetry emission.
      **Notes:** Sync fallback under load can block event producers and alter latency characteristics.

### [WL-7959]

**Title:** Replace global strike-through replace with row-targeted completion mutation
**Source:** [thegent/src/thegent/commands/workstream.py:158]
**Acceptance checklist:**

- [ ] Refactor `mark_completed()` to parse BACKLOG table rows and mutate only the row whose first column matches `item_id`.
- [ ] Preserve existing file write behavior and ensure already-completed rows are handled idempotently.
- [ ] Add tests for overlapping IDs (`WL-1` vs `WL-10`) and mentions in prose that must not be altered.
      **Notes:** Global string replacement can alter unrelated rows and free-form text outside BACKLOG.
