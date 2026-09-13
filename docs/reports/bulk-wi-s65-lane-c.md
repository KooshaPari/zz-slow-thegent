### [WL-8790]

**Title:** Preserve workflow checkpointing by separating checkpoint token parse and checkpoint persistence
**Source:** [thegent/src/thegent/workflow/checkpoint_persist.py:523]
**Acceptance checklist:**

- [ ] Separate checkpoint token parse failures from persistence failures.
- [ ] Preserve checkpoint persistence with token parse fallback.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Improves reliability for workflow recovery across token format changes.

### [WL-8791]

**Title:** Preserve session cache by separating cache policy parse and cache eviction
**Source:** [thegent/src/thegent/session/cache_policy.py:358]
**Acceptance checklist:**

- [ ] Separate cache policy parse failures from eviction logic failures.
- [ ] Preserve eviction behavior with default cache policy.
- [ ] Add tests for parse and eviction branches.
      **Notes:** Keeps session memory in control under cache policy drift.

### [WL-8792]

**Title:** Preserve API key validation by separating key format parse and key validation execution
**Source:** [thegent/src/thegent/auth/key_validator.py:501]
**Acceptance checklist:**

- [ ] Separate API key format parse failures from validation execution.
- [ ] Preserve validation defaults with format fallback.
- [ ] Add tests for parse and validation branches.
      **Notes:** Prevents key validation outages during format migration.

### [WL-8793]

**Title:** Preserve queue metrics collector by separating metrics selector parse and collector scheduling
**Source:** [thegent/src/thegent/queue/collector.py:333]
**Acceptance checklist:**

- [ ] Separate metrics selector parse failures from collector scheduling failures.
- [ ] Preserve collector scheduling with selector fallback.
- [ ] Add tests for selector and scheduling branches.
      **Notes:** Maintains monitoring continuity under selector schema changes.

### [WL-8794]

**Title:** Preserve artifact versioning by separating version parse and version apply
**Source:** [thegent/src/thegent/artifacts/version_manager.py:589]
**Acceptance checklist:**

- [ ] Separate artifact version parse failures from version apply failures.
- [ ] Preserve version apply with default version fallback.
- [ ] Add tests for parse and apply branches.
      **Notes:** Prevents versioning regressions from one malformed version string.

### [WL-8795]

**Title:** Preserve command queue balancing by separating balance policy parse and balance execution
**Source:** [thegent/src/thegent/commands/queue_balance.py:523]
**Acceptance checklist:**

- [ ] Separate queue balance policy parse failures from execution failures.
- [ ] Preserve balance execution with default policy.
- [ ] Add tests for parse and execution branches.
      **Notes:** Improves queue fairness during balance policy updates.

### [WL-8796]

**Title:** Preserve integration request routing by separating request parse and route dispatch
**Source:** [thegent/src/thegent/integrations/request_router.py:378]
**Acceptance checklist:**

- [ ] Separate integration request parse failures from route dispatch failures.
- [ ] Preserve route dispatch with parse fallback.
- [ ] Add tests for parse and dispatch branches.
      **Notes:** Keeps integrations running during request schema transitions.

### [WL-8797]

**Title:** Preserve artifact cleanup scheduling by separating cleanup criteria parse and schedule execution
**Source:** [thegent/src/thegent/artifacts/cleanup_scheduler.py:501]
**Acceptance checklist:**

- [ ] Separate cleanup criteria parse failures from schedule execution failures.
- [ ] Preserve cleanup execution with criteria fallback.
- [ ] Add tests for criteria parse and schedule execution branches.
      **Notes:** Prevents cleanup backlog from malformed criteria payloads.

### [WL-8798]

**Title:** Preserve session restart by separating restart config parse and restart orchestration
**Source:** [thegent/src/thegent/session/restart.py:423]
**Acceptance checklist:**

- [ ] Separate restart config parse failures from orchestration failures.
- [ ] Preserve restart orchestration with default restart config.
- [ ] Add tests for config parse and orchestration branches.
      **Notes:** Improves restart determinism across environment variations.

### [WL-8799]

**Title:** Preserve workflow reporting by separating reporting query parse and report generation
**Source:** [thegent/src/thegent/workflow/reporter.py:589]
**Acceptance checklist:**

- [ ] Separate workflow reporting query parse failures from report generation failures.
- [ ] Preserve report generation with query fallback.
- [ ] Add tests for parse and generation branches.
      **Notes:** Keeps reporting reliable with mixed query formats.
