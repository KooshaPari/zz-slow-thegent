### [WL-8650]

**Title:** Preserve session cache by separating cache key parse and cache write scheduling
**Source:** [thegent/src/thegent/session/cache.py:442]
**Acceptance checklist:**

- [ ] Separate cache key parse failures from cache write scheduling failures.
- [ ] Preserve write scheduling with parsed-key fallback.
- [ ] Add tests for key parse and scheduling branches.
      **Notes:** Improves session responsiveness when key formats vary.

### [WL-8651]

**Title:** Preserve artifact signature verification by separating signature metadata parse and verify call
**Source:** [thegent/src/thegent/artifacts/verify.py:478]
**Acceptance checklist:**

- [ ] Separate signature metadata parse failures from verify service call failures.
- [ ] Preserve verification status with metadata fallback.
- [ ] Add tests for parse and verify branches.
      **Notes:** Maintains integrity confidence under metadata format drift.

### [WL-8652]

**Title:** Preserve config migration auditing by separating migration log parse and audit write
**Source:** [thegent/src/thegent/config/migration_audit.py:333]
**Acceptance checklist:**

- [ ] Separate migration log parse failures from audit write failures.
- [ ] Preserve migration auditing using cached audit templates.
- [ ] Add tests for parse and audit write branches.
      **Notes:** Improves audit reliability during migration schema evolution.

### [WL-8653]

**Title:** Preserve queue error handling by separating error categorization and recovery handler dispatch
**Source:** [thegent/src/thegent/queue/error_handler.py:527]
**Acceptance checklist:**

- [ ] Separate error category classification failures from recovery dispatch failures.
- [ ] Preserve queue progress with conservative recovery path.
- [ ] Add tests for classification and dispatch branches.
      **Notes:** Reduces queue downtime on transient classifier instability.

### [WL-8654]

**Title:** Preserve CLI token accounting by separating token parse and token persistence
**Source:** [thegent/src/thegent/cli/token_metrics.py:401]
**Acceptance checklist:**

- [ ] Separate token parse failures from token persistence failures.
- [ ] Preserve token accounting with parse fallback.
- [ ] Add tests for parse and persistence branch behaviors.
      **Notes:** Keeps accounting visibility when token payloads vary.

### [WL-8655]

**Title:** Preserve artifact lineage by separating lineage map parse and lineage storage update
**Source:** [thegent/src/thegent/artifacts/lineage.py:589]
**Acceptance checklist:**

- [ ] Separate lineage map parse failures from storage update failures.
- [ ] Preserve lineage links on parse fallback.
- [ ] Add tests for parse and storage branches.
      **Notes:** Improves traceability under lineage metadata drift.

### [WL-8656]

**Title:** Preserve web UI state by separating UI state parse and local cache hydrate
**Source:** [thegent/src/thegent/ui/state_loader.py:359]
**Acceptance checklist:**

- [ ] Separate UI state parse failures from cache hydration failures.
- [ ] Preserve session UI state with hydration fallback.
- [ ] Add tests for parse and cache hydrate branches.
      **Notes:** Prevents UI flicker on transient state payload issues.

### [WL-8657]

**Title:** Preserve request throttling by separating throttle config parse and throttle enforcement
**Source:** [thegent/src/thegent/http/throttle.py:471]
**Acceptance checklist:**

- [ ] Separate throttle config parse failures from throttle enforcement failures.
- [ ] Preserve baseline throttling on config failures.
- [ ] Add tests for config parse and enforcement branches.
      **Notes:** Stabilizes API behavior under config shape changes.

### [WL-8658]

**Title:** Preserve task output rendering by separating output parse and output renderer
**Source:** [thegent/src/thegent/tasks/output_renderer.py:412]
**Acceptance checklist:**

- [ ] Separate task output parse failures from output rendering failures.
- [ ] Preserve raw output render fallback.
- [ ] Add tests for parse and renderer branches.
      **Notes:** Keeps task output usable under parser or renderer regressions.

### [WL-8659]

**Title:** Preserve sync audit trail by separating audit event parse and audit event persistence
**Source:** [thegent/src/thegent/sync/audit_trail.py:523]
**Acceptance checklist:**

- [ ] Separate audit event parse failures from persistence failures.
- [ ] Preserve audit trail with raw event fallback.
- [ ] Add tests for parse and persistence branch failures.
      **Notes:** Improves traceability while avoiding audit write drops.
