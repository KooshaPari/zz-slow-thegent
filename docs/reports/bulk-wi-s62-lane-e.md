### [WL-8660]

**Title:** Preserve command runtime by separating command parse and runtime dispatch
**Source:** [thegent/src/thegent/commands/runner.py:378]
**Acceptance checklist:**

- [ ] Separate command parse failures from runtime dispatch failures.
- [ ] Preserve dispatch fallback on parse failures.
- [ ] Add tests for parse and dispatch branches.
      **Notes:** Improves command execution reliability under mixed command inputs.

### [WL-8661]

**Title:** Preserve integration sync by separating sync event parse and integration writeback
**Source:** [thegent/src/thegent/integrations/sync_engine.py:441]
**Acceptance checklist:**

- [ ] Separate sync event parse failures from integration writeback failures.
- [ ] Preserve sync state with writeback retries.
- [ ] Add tests for parse and writeback branches.
      **Notes:** Helps integration sync survive bad event payloads.

### [WL-8662]

**Title:** Preserve policy evaluator by separating policy parse and context binding
**Source:** [thegent/src/thegent/policies/evaluator_core.py:412]
**Acceptance checklist:**

- [ ] Separate policy parse failures from context binding failures.
- [ ] Preserve context binding with degraded policy parse fallback.
- [ ] Add tests for parse and context binding branches.
      **Notes:** Keeps policy evaluation active with partial parse failures.

### [WL-8663]

**Title:** Preserve artifact uploader by separating upload metadata parse and upload scheduler
**Source:** [thegent/src/thegent/artifacts/upload_scheduler.py:531]
**Acceptance checklist:**

- [ ] Separate upload metadata parse failures from upload scheduler failures.
- [ ] Preserve scheduler behavior with metadata fallback.
- [ ] Add tests for metadata parse and scheduler branches.
      **Notes:** Reduces upload backlog due to metadata payload regressions.

### [WL-8664]

**Title:** Preserve queue drain diagnostics by separating metric extraction and diagnostic emission
**Source:** [thegent/src/thegent/queue/diagnostic_publisher.py:333]
**Acceptance checklist:**

- [ ] Separate queue metric extraction failures from diagnostic emission failures.
- [ ] Preserve diagnostics with extraction fallback.
- [ ] Add tests for extraction and emission branch failures.
      **Notes:** Keeps operational visibility under partial queue metric anomalies.

### [WL-8665]

**Title:** Preserve sync retry by separating retry policy parse and retry executor binding
**Source:** [thegent/src/thegent/sync/retry_executor.py:589]
**Acceptance checklist:**

- [ ] Separate retry policy parse failures from retry executor binding failures.
- [ ] Preserve default binding on policy parse errors.
- [ ] Add tests for parse and binding branches.
      **Notes:** Improves sync robustness during policy rollouts.

### [WL-8666]

**Title:** Preserve task queue integrity by separating queue snapshot parse and snapshot persistence
**Source:** [thegent/src/thegent/queue/snapshot_writer.py:477]
**Acceptance checklist:**

- [ ] Separate queue snapshot parse failures from snapshot persistence failures.
- [ ] Preserve queue snapshots in-memory on persistence failure.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Improves resilience for recovery workflows.

### [WL-8667]

**Title:** Preserve CLI context sync by separating context source resolve and context application
**Source:** [thegent/src/thegent/cli/context_sync.py:401]
**Acceptance checklist:**

- [ ] Separate CLI context source resolve failures from context application failures.
- [ ] Preserve context application when resolution is partial.
- [ ] Add tests for resolve and apply branches.
      **Notes:** Keeps CLI behavior stable under source metadata inconsistencies.

### [WL-8668]

**Title:** Preserve artifact cleanup scheduling by separating cleanup selection and cleanup enqueue
**Source:** [thegent/src/thegent/artifacts/cleanup_scheduler.py:498]
**Acceptance checklist:**

- [ ] Separate cleanup selection failures from cleanup enqueue failures.
- [ ] Preserve enqueue behavior with selection fallback.
- [ ] Add tests for selection and enqueue branches.
      **Notes:** Prevents cleanup pipeline stalls under dynamic criteria changes.

### [WL-8669]

**Title:** Preserve authentication state by separating auth token parse and auth state persistence
**Source:** [thegent/src/thegent/auth/state_store.py:531]
**Acceptance checklist:**

- [ ] Separate auth token parse failures from auth state persistence failures.
- [ ] Preserve in-memory auth state with parse fallback.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Improves auth continuity during token format or storage faults.
