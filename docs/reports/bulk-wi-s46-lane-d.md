### [WL-7850]

**Title:** Make conflict queue writes crash-safe with file+directory fsync before atomic replace
**Source:** [thegent/src/thegent/sync/queue.py:71]
**Acceptance checklist:**

- [ ] Update `ConflictQueueStore._write` to flush+fsync the temp file before `replace()` and fsync the parent directory after replace where supported.
- [ ] Preserve the existing JSON payload schema (`version`, `conflicts`) and deterministic key ordering.
- [ ] Add tests for successful write, simulated mid-write interruption, and preservation of last valid queue content on write failure.
      **Notes:** Current temp-file replace flow reduces corruption risk but does not guarantee durability across sudden host crashes.

### [WL-7851]

**Title:** Eliminate check/consume race in multi-key limiter by adding ordered lock acquisition for atomic allow-all
**Source:** [thegent/src/thegent/routing/rate_limiter.py:143]
**Acceptance checklist:**

- [ ] Refactor `MultiKeyRateLimiter.allow_all` to lock all involved keys in a deterministic order and perform check+consume in one critical section.
- [ ] Keep response shape unchanged while ensuring no partial consumption is possible under concurrency.
- [ ] Add concurrency tests proving all-or-nothing behavior with overlapping key sets and racing threads.
      **Notes:** The current two-phase approach can still race between `check()` and `allow()` calls under contention.

### [WL-7852]

**Title:** Add stale in-flight task requeue policy with lease timeout in Maildir queue
**Source:** [thegent/src/thegent/mesh/task_queue.py:180]
**Acceptance checklist:**

- [ ] Introduce lease metadata for `cur/` tasks and a sweep path that returns expired tasks to `new/` for retry.
- [ ] Ensure requeued tasks increment attempt metadata and retain original task ID for traceability.
- [ ] Add tests for normal ack flow, expired lease recovery, and non-expired in-flight task preservation.
      **Notes:** Tasks can remain stranded in `cur/` after worker failure without bounded automatic recovery.

### [WL-7853]

**Title:** Replace silent layout restore failure with typed validation errors in pane manager
**Source:** [thegent/src/thegent/ui/compositor/pane_manager.py:181]
**Acceptance checklist:**

- [ ] Add explicit schema validation for `layout_data` (required keys, node shape, direction enum) before deserialization.
- [ ] Replace broad `except Exception` return-false behavior with typed exceptions that include failing node context.
- [ ] Add tests for valid layout restore, malformed node payload, and invalid direction value.
      **Notes:** Current restore path can hide corruption details and makes UI recovery/debugging harder.

### [WL-7854]

**Title:** Surface seed JSONL parse failures as structured diagnostics instead of warning-and-skip behavior
**Source:** [thegent/src/thegent/memory/seed_storage.py:61]
**Acceptance checklist:**

- [ ] Return/raise structured parse diagnostics with line number and error class when `load_seeds` encounters invalid JSON or missing fields.
- [ ] Preserve successful seed loading behavior for valid lines and blank-line skipping.
- [ ] Add tests for fully valid files, single malformed line, and mixed valid/invalid line handling.
      **Notes:** Silent skipping can hide seed store corruption and lead to incorrect downstream analytics.

### [WL-7855]

**Title:** Enforce explicit compression contract for zstd trace files instead of implicit gzip fallback
**Source:** [thegent/src/thegent/trace/schema.py:160]
**Acceptance checklist:**

- [ ] Replace `compression="zstd"` gzip fallback behavior with explicit zstd support or a clear `NotImplementedError` at initialization.
- [ ] Keep gzip and uncompressed read/write behavior unchanged.
- [ ] Add tests for gzip roundtrip, uncompressed roundtrip, and deterministic zstd-mode failure semantics when unsupported.
      **Notes:** Current zstd setting silently writing gzip can produce misleading artifacts and decode mismatches.

### [WL-7856]

**Title:** Add stale-sample eviction and minimum-sample guardrails to EWMA latency ranking
**Source:** [thegent/src/thegent/routing/latency_tracker.py:116]
**Acceptance checklist:**

- [ ] Introduce configurable staleness TTL and exclude/penalize stale provider-model records during `rank_by_latency`.
- [ ] Add minimum-sample handling so single outlier samples cannot dominate fast-path routing decisions.
- [ ] Add tests for fresh sample ranking, stale record decay, and cold-start providers with insufficient sample counts.
      **Notes:** Ranking currently treats old and sparse samples as equally trustworthy, which can degrade route quality.

### [WL-7857]

**Title:** Harden frontmatter boundary parsing to avoid false delimiter matches in rules sync
**Source:** [thegent/src/thegent/core/rules_sync.py:69]
**Acceptance checklist:**

- [ ] Update `_parse_frontmatter` to detect only line-anchored opening/closing `---` markers and reject malformed multi-block headers.
- [ ] Preserve current metadata parsing behavior for valid rule files.
- [ ] Add tests for valid frontmatter, body text containing `---`, and unclosed or duplicate frontmatter blocks.
      **Notes:** Current delimiter search can mis-parse files when body content includes delimiter-like text.

### [WL-7858]

**Title:** Require native JSONL runtime explicitly in public parser APIs and remove silent Python fallback
**Source:** [thegent/src/thegent/native/jsonl_parser.py:168]
**Acceptance checklist:**

- [ ] Update `JsonlParser.stream/count/filter/sample` to fail with explicit native-runtime errors when native binary/module is unavailable.
- [ ] Keep `_py_*` helpers scoped to tests/internal compatibility paths only, not default production execution.
- [ ] Add tests for native-available success and native-missing explicit failure messages across all public APIs.
      **Notes:** Automatic fallback obscures performance and behavior drift between environments.

### [WL-7859]

**Title:** Add append integrity checks and idempotency key guard for sync decision journal entries
**Source:** [thegent/src/thegent/sync/journal.py:65]
**Acceptance checklist:**

- [ ] Add optional idempotency key support that rejects duplicate append attempts for the same decision in a cycle.
- [ ] Validate required entry fields and enforce non-empty `entry_id/cycle_id/wl_id/decision` before write.
- [ ] Add tests for normal append/read, duplicate-idempotency rejection, and invalid-entry validation failures.
      **Notes:** Journal append currently accepts all entries, increasing risk of accidental duplicate or malformed replay data.
