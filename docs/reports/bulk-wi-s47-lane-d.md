### [WL-7900]

**Title:** Preserve per-file parse failures during WORK_STREAM sync instead of silently dropping tasks
**Source:** [thegent/src/thegent/task/sync.py:48]
**Acceptance checklist:**

- [ ] Update `update_work_stream_from_tasks()` to capture parse failures (file path + error) in a structured `errors` list returned to callers.
- [ ] Keep successful task parsing behavior unchanged and continue processing remaining files.
- [ ] Add tests for all-valid tasks, mixed valid/invalid tasks, and fully invalid directories to verify surfaced diagnostics.
      **Notes:** Silent `except` in the parse loop hides malformed task files and causes accidental backlog omissions.

### [WL-7901]

**Title:** Escape markdown table cell content before emitting BACKLOG rows
**Source:** [thegent/src/thegent/task/sync.py:60]
**Acceptance checklist:**

- [ ] Add a centralized sanitizer for `title`, `source`, and `depends` values that escapes pipe/newline content before table row generation.
- [ ] Preserve current row column order and default field behavior (`priority` fallback, `depends` fallback to `-`).
- [ ] Add tests for titles/sources containing `|`, newline, and backtick content to ensure table integrity.
      **Notes:** Raw interpolation can break table structure when task metadata includes markdown-reserved characters.

### [WL-7902]

**Title:** Return full schema validation error sets instead of single-message collapse
**Source:** [thegent/src/thegent/task/validator.py:76]
**Acceptance checklist:**

- [ ] Replace single `except Exception` capture with extraction of all schema violations from `FastJSONSchemaValidator` where available.
- [ ] Map each violation to `ValidationError` with stable `field`, `path`, and `code` values.
- [ ] Add tests for multi-error payloads asserting deterministic ordering and complete error coverage.
      **Notes:** Current handling reduces multiple schema violations into one message, slowing remediation.

### [WL-7903]

**Title:** Harden YAML frontmatter boundary detection to avoid regex backtracking edge cases
**Source:** [thegent/src/thegent/task/parser.py:28]
**Acceptance checklist:**

- [ ] Replace regex-only frontmatter parsing with line-anchored boundary scanning that enforces one opening and one closing delimiter.
- [ ] Preserve support for files with and without trailing newline after closing delimiter.
- [ ] Add tests for malformed delimiters, duplicate frontmatter blocks, and frontmatter-like content in markdown bodies.
      **Notes:** Greedy regex parsing can mis-handle malformed documents and produce ambiguous errors.

### [WL-7904]

**Title:** Remove silent exception swallow from WORK_STREAM detail extraction in task migration
**Source:** [thegent/src/thegent/task/migrate.py:64]
**Acceptance checklist:**

- [ ] Replace `except Exception: pass` with explicit typed error handling that logs migration diagnostics and returns warning metadata.
- [ ] Preserve migration output generation for entries that do not require WORK_STREAM enrichment.
- [ ] Add tests for readable/missing/corrupted WORK_STREAM inputs to verify fail-loud diagnostics without aborting whole migration.
      **Notes:** Suppressed extraction failures hide migration quality issues and make regressions hard to trace.

### [WL-7905]

**Title:** Add bounded retry attempt policy and dead-letter transition in in-memory task queue
**Source:** [thegent/src/thegent/task_queue/queue.py:32]
**Acceptance checklist:**

- [ ] Track retry attempts per `task_id` and reject or dead-letter tasks exceeding a configurable attempt cap.
- [ ] Keep transient-failure class filtering behavior intact for first-attempt retries.
- [ ] Add tests for retry dedupe, max-attempt cutoff, and completion cleanup of queued retries.
      **Notes:** Retry queue currently has no attempt budget, so repeatedly failing tasks can churn indefinitely.

### [WL-7906]

**Title:** Fail explicitly when broadcasting to an unknown team instead of silent return
**Source:** [thegent/src/thegent/team/coordination.py:63]
**Acceptance checklist:**

- [ ] Change `broadcast_message()` to return a typed error (or raise) when team metadata is missing.
- [ ] Include `team_id` and sender context in the error payload/log for downstream observability.
- [ ] Add tests for valid team broadcast, missing-team failure, and partial teammate list handling.
      **Notes:** Silent no-op behavior makes message-delivery failures invisible to coordinators and automation.

### [WL-7907]

**Title:** Replace process-identity CSS class generation with deterministic layout node identifiers
**Source:** [thegent/src/thegent/ui/compositor/layout_engine.py:226]
**Acceptance checklist:**

- [ ] Stop using `id(self)` in generated class names and introduce deterministic node IDs stable across runs.
- [ ] Preserve generated CSS semantics for direction, width, and height rules.
- [ ] Add tests asserting stable CSS snapshots for equivalent layout trees across repeated runs.
      **Notes:** `id(self)` makes CSS output nondeterministic and causes flaky snapshot or diff-based tests.

### [WL-7908]

**Title:** Introduce explicit trace queue overflow policy instead of synchronous write fallback
**Source:** [thegent/src/thegent/trace/recorder.py:211]
**Acceptance checklist:**

- [ ] Add configurable overflow modes (`drop_newest`, `drop_oldest`, `fail`) and remove implicit sync-write fallback on queue saturation.
- [ ] Emit structured overflow counters/metrics with session ID and dropped record counts.
- [ ] Add async tests covering each overflow mode under forced queue pressure.
      **Notes:** Falling back to synchronous writes in async mode can block producers and distort runtime behavior.

### [WL-7909]

**Title:** Replace naive backlog strike-through replacement with row-scoped table mutation
**Source:** [thegent/src/thegent/utils/workstream_ops.py:148]
**Acceptance checklist:**

- [ ] Parse BACKLOG rows into structured columns and mutate only the target `item_id` row when marking complete.
- [ ] Preserve existing behavior for appending COMPLETED rows and timestamp formatting.
- [ ] Add tests for overlapping IDs (e.g., `WL-1` vs `WL-10`), repeated IDs in prose, and idempotent completion.
      **Notes:** Global string replacement can modify unintended text and corrupt unrelated rows.
