### [WL-8750]

**Title:** Preserve session state snapshots by separating snapshot format parse and snapshot indexing
**Source:** [thegent/src/thegent/session/snapshot_index.py:531]
**Acceptance checklist:**

- [ ] Separate snapshot format parse failures from index update failures.
- [ ] Preserve snapshot indexing with fallback indexing.
- [ ] Add tests for parse and index update branches.
      **Notes:** Improves recoverability under evolving snapshot formats.

### [WL-8751]

**Title:** Preserve command error handling by separating error decode and error response construction
**Source:** [thegent/src/thegent/commands/error_handler.py:333]
**Acceptance checklist:**

- [ ] Separate command error decode failures from response construction failures.
- [ ] Preserve response construction on decode fallback.
- [ ] Add tests for decode and response branches.
      **Notes:** Keeps command debugging clear under mixed error payloads.

### [WL-8752]

**Title:** Preserve artifact lifecycle by separating lifecycle event parse and lifecycle handler dispatch
**Source:** [thegent/src/thegent/artifacts/lifecycle_handler.py:478]
**Acceptance checklist:**

- [ ] Separate lifecycle event parse failures from handler dispatch failures.
- [ ] Preserve dispatch fallback on parse failures.
- [ ] Add tests for parse and dispatch branches.
      **Notes:** Keeps lifecycle transitions stable under partial event issues.

### [WL-8753]

**Title:** Preserve sync plan reconciliation by separating plan diff parse and plan apply
**Source:** [thegent/src/thegent/sync/plan_reconcile.py:412]
**Acceptance checklist:**

- [ ] Separate sync plan diff parse failures from plan apply failures.
- [ ] Preserve apply flow with fallback plan diffs.
- [ ] Add tests for parse and apply branch failures.
      **Notes:** Helps avoid stalled sync operations when one diff format breaks.

### [WL-8754]

**Title:** Preserve metrics registry by separating registry parse and metric registration
**Source:** [thegent/src/thegent/metrics/registry.py:512]
**Acceptance checklist:**

- [ ] Separate metrics registry parse failures from metric registration failures.
- [ ] Preserve registration with fallback registry rules.
- [ ] Add tests for parse and registration branches.
      **Notes:** Supports observability under registry evolution.

### [WL-8755]

**Title:** Preserve queue drain scheduler by separating drain strategy parse and drain scheduler
**Source:** [thegent/src/thegent/queue/drain_scheduler.py:359]
**Acceptance checklist:**

- [ ] Separate drain strategy parse failures from scheduler failures.
- [ ] Preserve drain scheduling with fallback strategy.
- [ ] Add tests for strategy and scheduler branches.
      **Notes:** Improves queue stability under drain strategy config churn.

### [WL-8756]

**Title:** Preserve API response shaping by separating response schema parse and shape transform
**Source:** [thegent/src/thegent/api/response_shaper.py:523]
**Acceptance checklist:**

- [ ] Separate response schema parse failures from shape transform failures.
- [ ] Preserve API outputs with raw shape fallback.
- [ ] Add tests for schema parse and shape transform branches.
      **Notes:** Maintains API compatibility during response evolution.

### [WL-8757]

**Title:** Preserve session synchronization by separating sync descriptor parse and sync orchestration
**Source:** [thegent/src/thegent/session/sync_orchestrator.py:441]
**Acceptance checklist:**

- [ ] Separate session sync descriptor parse failures from orchestration failures.
- [ ] Preserve orchestration with descriptor fallback.
- [ ] Add tests for parse and orchestration branches.
      **Notes:** Improves session syncing during descriptor format shifts.

### [WL-8758]

**Title:** Preserve artifact validation by separating artifact type parse and type-specific validation
**Source:** [thegent/src/thegent/artifacts/type_validator.py:512]
**Acceptance checklist:**

- [ ] Separate artifact type parse failures from type-specific validation failures.
- [ ] Preserve validation using inferred defaults.
- [ ] Add tests for type parse and validation branches.
      **Notes:** Reduces false negatives when type annotations are malformed.

### [WL-8759]

**Title:** Preserve command queue retries by separating retry policy parse and retry attempt dispatch
**Source:** [thegent/src/thegent/commands/retry_queue.py:333]
**Acceptance checklist:**

- [ ] Separate retry policy parse failures from retry dispatch failures.
- [ ] Preserve retry dispatch with safe policy defaults.
- [ ] Add tests for policy and dispatch branch failures.
      **Notes:** Keeps retry workflows operational through policy churn.
