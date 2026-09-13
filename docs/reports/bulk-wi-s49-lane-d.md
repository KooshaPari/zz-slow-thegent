### [WL-8000]

**Title:** Surface per-file parse failures in task sync results with stable diagnostics
**Source:** [thegent/src/thegent/task/sync.py:48]
**Acceptance checklist:**

- [ ] Replace silent parse-loop exception swallowing in `update_work_stream_from_tasks()` with structured error capture containing `task_file`, `error_type`, and `message`.
- [ ] Preserve successful parsing for valid files in the same run and return both success metrics and collected errors.
- [ ] Add tests for all-valid, mixed-validity, and all-invalid task directories asserting deterministic error payload ordering.
      **Notes:** Missing diagnostics currently make BACKLOG drift hard to reconcile when a single malformed task file appears.

### [WL-8001]

**Title:** Escape markdown table cell content before emitting BACKLOG rows
**Source:** [thegent/src/thegent/task/sync.py:60]
**Acceptance checklist:**

- [ ] Add a shared sanitizer for BACKLOG table cells used by `task_id`, `title`, `source`, and `depends` fields.
- [ ] Normalize newline and pipe characters so generated rows always preserve the expected 5-column markdown shape.
- [ ] Add regression tests with metadata containing `|`, multiline text, and code spans to verify parse roundtrip stability.
      **Notes:** Raw interpolation can break table parsing and cascade into claim/complete command failures.

### [WL-8002]

**Title:** Return complete schema violation sets from task validation
**Source:** [thegent/src/thegent/task/validator.py:76]
**Acceptance checklist:**

- [ ] Refactor `TaskValidator.validate()` to collect all schema violations exposed by the validator instead of collapsing to one message.
- [ ] Map each violation to `ValidationError` with deterministic `field`, `path`, and `code` semantics.
- [ ] Add tests proving multi-field invalid payloads produce complete, stably ordered error lists.
      **Notes:** Single-error collapse forces repeated fix/validate cycles and slows author feedback.

### [WL-8003]

**Title:** Replace regex frontmatter extraction with delimiter-aware scanning
**Source:** [thegent/src/thegent/task/parser.py:28]
**Acceptance checklist:**

- [ ] Rework `parse_yaml_frontmatter()` to scan line boundaries for opening/closing `---` delimiters instead of relying on dotall regex capture.
- [ ] Raise explicit `ValueError` messages for missing, duplicated, or out-of-order delimiter blocks.
- [ ] Add tests for trailing-newline variance, body-only documents, and markdown bodies containing `---` text.
      **Notes:** Regex parsing is brittle on malformed files and can mis-split frontmatter and markdown body sections.

### [WL-8004]

**Title:** Expose migration enrichment warnings instead of swallowing extraction exceptions
**Source:** [thegent/src/thegent/task/migrate.py:64]
**Acceptance checklist:**

- [ ] Replace broad `except Exception: pass` during WORK_STREAM detail extraction with typed warning collection.
- [ ] Include warnings in migration result payload without aborting successful item migration.
- [ ] Add tests for missing, unreadable, and malformed WORK_STREAM sources verifying warning visibility and continued processing.
      **Notes:** Silent failure hides migration defects and makes post-migration cleanup unpredictable.

### [WL-8005]

**Title:** Add bounded retries and dead-letter routing to in-memory task queue
**Source:** [thegent/src/thegent/task_queue/queue.py:32]
**Acceptance checklist:**

- [ ] Track retry attempts per `task_id` and enforce a configurable maximum retry budget.
- [ ] Route exhausted tasks into an explicit dead-letter collection while preserving transient retry behavior for eligible failures.
- [ ] Add tests for dedupe behavior, retry exhaustion cutoff, and attempt cleanup on `complete()`.
      **Notes:** Unbounded retries can starve fresh work and keep permanently failing tasks cycling indefinitely.

### [WL-8006]

**Title:** Fail explicitly for unknown-team broadcasts in coordination flow
**Source:** [thegent/src/thegent/team/coordination.py:63]
**Acceptance checklist:**

- [ ] Update `broadcast_message()` to raise a typed error (or return an explicit failure object) when `team_meta_path` is missing.
- [ ] Include `team_id` and `sender` context in the failure payload for downstream logging and alerting.
- [ ] Add tests for successful broadcast, unknown-team failure, and sender-exclusion behavior.
      **Notes:** Silent no-op behavior drops coordination messages without any observable failure signal.

### [WL-8007]

**Title:** Make generated layout CSS selectors deterministic across runs
**Source:** [thegent/src/thegent/ui/compositor/layout_engine.py:226]
**Acceptance checklist:**

- [ ] Replace `.layout-{id(self)}` generation with deterministic node identifiers derived from tree position or explicit node IDs.
- [ ] Preserve existing layout rule semantics for direction and sizing declarations.
- [ ] Add snapshot tests asserting byte-stable CSS for equivalent layout trees across repeated executions.
      **Notes:** Process-identity-based selectors create flaky snapshots and unstable style diffs.

### [WL-8008]

**Title:** Define explicit overflow policy for async trace write queue saturation
**Source:** [thegent/src/thegent/trace/recorder.py:211]
**Acceptance checklist:**

- [ ] Add configurable overflow modes (`drop_newest`, `drop_oldest`, `error`) for async `write_queue` saturation.
- [ ] Remove implicit synchronous write fallback on `QueueFull` and emit structured overflow metrics.
- [ ] Add async tests that force queue pressure and validate behavior for each overflow mode.
      **Notes:** Sync fallback under load can block producers and distort latency-sensitive tracing paths.

### [WL-8009]

**Title:** Make queue file persistence crash-safe with full fsync sequence
**Source:** [thegent/src/thegent/sync/queue.py:71]
**Acceptance checklist:**

- [ ] Update `ConflictQueueStore._write()` to flush and fsync the temporary file before atomic replace.
- [ ] Fsync the parent directory after replace on supported platforms to harden metadata durability.
- [ ] Add tests for successful writes and simulated write interruption preserving the last valid queue file.
      **Notes:** Atomic rename without fsync can still lose recently written queue state during abrupt host crashes.
