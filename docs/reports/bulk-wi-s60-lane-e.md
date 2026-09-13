### [WL-8560]

**Title:** Preserve session restore by separating checkpoint source and restore strategy
**Source:** [thegent/src/thegent/session/restore_engine.py:422]
**Acceptance checklist:**

- [ ] Separate checkpoint source selection failures from restore strategy failures.
- [ ] Preserve restore attempts with fallback source strategy.
- [ ] Add tests for source and strategy branches.
      **Notes:** Improves restoration predictability under mixed checkpoint formats.

### [WL-8561]

**Title:** Preserve command context by separating context token parse and command injection
**Source:** [thegent/src/thegent/commands/context_injector.py:331]
**Acceptance checklist:**

- [ ] Separate context token parse failures from command injection failures.
- [ ] Preserve command injection when parse fallback is used.
- [ ] Add tests for token and injection branch failures.
      **Notes:** Keeps command composition resilient under token mismatch.

### [WL-8562]

**Title:** Preserve sync metrics by separating metric series parse and metric emission
**Source:** [thegent/src/thegent/sync/metrics_sender.py:501]
**Acceptance checklist:**

- [ ] Separate metric series parse failures from metric emission failures.
- [ ] Preserve emission buffering on parse failures.
- [ ] Add tests for parse and emission branches.
      **Notes:** Helps keep sync visibility even in partial metric drift.

### [WL-8563]

**Title:** Preserve plugin health by separating plugin metadata parse and runtime probe
**Source:** [thegent/src/thegent/ui/plugin_health.py:287]
**Acceptance checklist:**

- [ ] Separate plugin metadata parse failures from runtime probe failures.
- [ ] Preserve health data with metadata fallback probes.
- [ ] Add tests for metadata and probe branch failures.
      **Notes:** Avoids false plugin health degradation.

### [WL-8564]

**Title:** Preserve route metrics by separating route match trace and metric aggregation
**Source:** [thegent/src/thegent/routing/metrics.py:444]
**Acceptance checklist:**

- [ ] Separate route match trace failures from metric aggregation failures.
- [ ] Preserve aggregation with trace fallback.
- [ ] Add tests for match trace and aggregation branches.
      **Notes:** Keeps route observability usable under tracing issues.

### [WL-8565]

**Title:** Preserve artifact ingestion by separating file ingest parse and pipeline launch
**Source:** [thegent/src/thegent/artifacts/ingest.py:468]
**Acceptance checklist:**

- [ ] Separate file ingest parse failures from pipeline launch failures.
- [ ] Preserve ingest pipeline launch on parse fallback.
- [ ] Add tests for parse and pipeline branches.
      **Notes:** Improves ingestion robustness under inconsistent input formatting.

### [WL-8566]

**Title:** Preserve CLI profile sync by separating profile list parse and profile persistence
**Source:** [thegent/src/thegent/cli/profile_sync.py:523]
**Acceptance checklist:**

- [ ] Separate profile list parse failures from profile persistence failures.
- [ ] Preserve profile sync state with list fallback.
- [ ] Add tests for list parse and persistence branches.
      **Notes:** Keeps profile sync usable under format mismatches.

### [WL-8567]

**Title:** Preserve task result handling by separating result decode and result persistence
**Source:** [thegent/src/thegent/tasks/results.py:333]
**Acceptance checklist:**

- [ ] Separate task result decode failures from result persistence failures.
- [ ] Preserve in-memory result state on persistence failures.
- [ ] Add tests for decode and persistence branches.
      **Notes:** Improves task lifecycle integrity with partial failures.

### [WL-8568]

**Title:** Preserve event replay metrics by separating replay window parse and metric emission
**Source:** [thegent/src/thegent/events/replay_metrics.py:589]
**Acceptance checklist:**

- [ ] Separate replay window parse failures from metric emission failures.
- [ ] Preserve replay metrics with fallback windows.
- [ ] Add tests for parse and emission branches.
      **Notes:** Helps maintain replay observability under window format regressions.

### [WL-8569]

**Title:** Preserve artifact indexing by separating metadata extraction and index validation
**Source:** [thegent/src/thegent/artifacts/index_validator.py:512]
**Acceptance checklist:**

- [ ] Separate metadata extraction failures from index validation failures.
- [ ] Preserve index updates with metadata fallback extraction.
- [ ] Add tests for extraction and validation branch failures.
      **Notes:** Reduces false positives during metadata extraction glitches.
