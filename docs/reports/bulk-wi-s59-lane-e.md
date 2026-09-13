### [WL-8510]

**Title:** Preserve artifact metadata extraction by separating parser metadata and runtime context
**Source:** [thegent/src/thegent/artifacts/meta_extract.py:438]
**Acceptance checklist:**

- [ ] Separate parser metadata extraction failures from runtime context extraction.
- [ ] Preserve metadata when runtime context extraction fails.
- [ ] Add tests for parser and runtime extraction branches.
      **Notes:** Helps indexing stay useful despite parser format drift.

### [WL-8511]

**Title:** Preserve session restore by separating checkpoint load and state reconciliation
**Source:** [thegent/src/thegent/session/restore.py:602]
**Acceptance checklist:**

- [ ] Separate checkpoint load failures from state reconciliation failures.
- [ ] Preserve session state with reconciliation fallback.
- [ ] Add tests for load and reconciliation branches.
      **Notes:** Supports continuity after intermittent checkpoint write faults.

### [WL-8512]

**Title:** Preserve queue telemetry by separating poll timing and queue depth reporting
**Source:** [thegent/src/thegent/queue/telemetry.py:422]
**Acceptance checklist:**

- [ ] Separate poll timing failures from queue depth reporting failures.
- [ ] Preserve depth reporting with timed fallback.
- [ ] Add tests for timing and reporting branches.
      **Notes:** Improves operations monitoring in queue-heavy runs.

### [WL-8513]

**Title:** Preserve command dispatch by separating payload schema parsing and dispatch throttling
**Source:** [thegent/src/thegent/commands/dispatcher.py:451]
**Acceptance checklist:**

- [ ] Separate dispatch payload schema parse failures from throttling policy failures.
- [ ] Preserve dispatch path on throttle policy fallback.
- [ ] Add tests for parse and throttling branches.
      **Notes:** Prevents command bottlenecks from one schema mistake.

### [WL-8514]

**Title:** Preserve task metadata sync by separating schema sync and metadata application
**Source:** [thegent/src/thegent/tasks/metadata.py:512]
**Acceptance checklist:**

- [ ] Separate task schema sync failures from metadata application failures.
- [ ] Preserve metadata sync state with deferred application.
- [ ] Add tests for schema and application branch failures.
      **Notes:** Improves metadata coherence across sync cycles.

### [WL-8515]

**Title:** Preserve plugin config updates by separating file checksum and runtime merge
**Source:** [thegent/src/thegent/plugins/config.py:359]
**Acceptance checklist:**

- [ ] Separate plugin config checksum validation failures from runtime merge failures.
- [ ] Preserve runtime config during checksum failures.
- [ ] Add tests for checksum and merge branches.
      **Notes:** Avoids unstable plugin states from one checksum mismatch.

### [WL-8516]

**Title:** Preserve API heartbeat by separating heartbeat source and heartbeat emitter
**Source:** [thegent/src/thegent/api/heartbeat.py:498]
**Acceptance checklist:**

- [ ] Separate heartbeat source collection failures from emitter scheduling failures.
- [ ] Preserve heartbeat emission on source failures.
- [ ] Add tests for source and emitter branch failures.
      **Notes:** Keeps uptime checks meaningful despite source drift.

### [WL-8517]

**Title:** Preserve shell context by separating context source parse and context persistence
**Source:** [thegent/src/thegent/shell/context.py:333]
**Acceptance checklist:**

- [ ] Separate shell context source parsing failures from persistence failures.
- [ ] Preserve in-memory context on persistence failures.
- [ ] Add tests for context parse and persistence branches.
      **Notes:** Keeps shell interactions stable under persistence flakiness.

### [WL-8518]

**Title:** Preserve artifact integrity checks by separating checksum parse and signature validation
**Source:** [thegent/src/thegent/artifacts/integrity.py:441]
**Acceptance checklist:**

- [ ] Separate checksum parse failures from signature validation failures.
- [ ] Preserve integrity status with partial evidence.
- [ ] Add tests for checksum and signature branches.
      **Notes:** Improves trust signals under partial integrity corruption.

### [WL-8519]

**Title:** Preserve queue reconciliation by separating reconciliation plan and apply phases
**Source:** [thegent/src/thegent/queue/reconcile.py:592]
**Acceptance checklist:**

- [ ] Separate reconciliation plan failures from apply failures.
- [ ] Preserve plan state and retry behavior.
- [ ] Add tests for plan and apply branches.
      **Notes:** Helps avoid unrecoverable queue divergence after planning errors.
