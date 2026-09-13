### [WL-8640]

**Title:** Preserve sync checkpoint replay by separating checkpoint parse and replay scheduler
**Source:** [thegent/src/thegent/sync/replay.py:358]
**Acceptance checklist:**

- [ ] Separate checkpoint parse failures from replay scheduler failures.
- [ ] Preserve scheduler operation with checkpoint fallback.
- [ ] Add tests for parse and scheduler branches.
      **Notes:** Improves recovery reliability under checkpoint format churn.

### [WL-8641]

**Title:** Preserve artifact access controls by separating ACL parse and ACL enforcement
**Source:** [thegent/src/thegent/artifacts/acl.py:522]
**Acceptance checklist:**

- [ ] Separate ACL parse failures from ACL enforcement failures.
- [ ] Preserve enforcement fallback with explicit safe defaults.
- [ ] Add tests for parse and enforcement branches.
      **Notes:** Helps prevent unauthorized access regressions or accidental lockouts.

### [WL-8642]

**Title:** Preserve telemetry sampling by separating sampler config parse and sampler runtime
**Source:** [thegent/src/thegent/telemetry/sampler.py:401]
**Acceptance checklist:**

- [ ] Separate sampler config parse failures from sampler runtime failures.
- [ ] Preserve runtime defaults under parse failures.
- [ ] Add tests for config and runtime sampler branches.
      **Notes:** Keeps telemetry load controlled during config transitions.

### [WL-8643]

**Title:** Preserve command scheduling by separating schedule expression parse and schedule execution
**Source:** [thegent/src/thegent/commands/scheduler.py:477]
**Acceptance checklist:**

- [ ] Separate schedule expression parse failures from schedule execution failures.
- [ ] Preserve execution with schedule fallback values.
- [ ] Add tests for parse and execution branch failures.
      **Notes:** Improves reliability for periodic command workflows.

### [WL-8644]

**Title:** Preserve integration health checks by separating health payload parse and health endpoint dispatch
**Source:** [thegent/src/thegent/integrations/health_check.py:333]
**Acceptance checklist:**

- [ ] Separate integration health payload parse failures from endpoint dispatch failures.
- [ ] Preserve endpoint dispatch with payload fallback.
- [ ] Add tests for parse and dispatch branches.
      **Notes:** Keeps health monitoring resilient to payload differences.

### [WL-8645]

**Title:** Preserve artifact index compaction by separating compaction planning and compaction execution
**Source:** [thegent/src/thegent/artifacts/compactor.py:589]
**Acceptance checklist:**

- [ ] Separate compaction plan failures from compaction execution failures.
- [ ] Preserve execution branch with conservative compaction plan.
- [ ] Add tests for planning and execution branches.
      **Notes:** Reduces risk of accidental data loss during compaction.

### [WL-8646]

**Title:** Preserve CLI prompt rendering by separating prompt template load and prompt render
**Source:** [thegent/src/thegent/cli/prompt_renderer.py:451]
**Acceptance checklist:**

- [ ] Separate prompt template load failures from prompt rendering failures.
- [ ] Preserve rendering fallback with embedded templates.
- [ ] Add tests for template load and render branches.
      **Notes:** Keeps CLI interaction stable under template hot reload issues.

### [WL-8647]

**Title:** Preserve sync task mapping by separating task map parse and map application
**Source:** [thegent/src/thegent/sync/task_mapper.py:422]
**Acceptance checklist:**

- [ ] Separate task map parse failures from map application failures.
- [ ] Preserve mapping with fallback task map behavior.
- [ ] Add tests for parse and application branches.
      **Notes:** Improves sync continuity when map schemas change.

### [WL-8648]

**Title:** Preserve alert dedup by separating alert fingerprint parse and dedup record write
**Source:** [thegent/src/thegent/alerts/dedup.py:512]
**Acceptance checklist:**

- [ ] Separate alert fingerprint parse failures from dedup write failures.
- [ ] Preserve dedup process with conservative hash fallback.
- [ ] Add tests for parse and write branch failures.
      **Notes:** Reduces duplicate alerts without losing alerting capabilities.

### [WL-8649]

**Title:** Preserve queue drain status by separating drain stats collect and drain status persist
**Source:** [thegent/src/thegent/queue/drain_status.py:333]
**Acceptance checklist:**

- [ ] Separate drain stats collection failures from status persistence failures.
- [ ] Preserve status persistence with in-memory fallback.
- [ ] Add tests for collection and persistence branches.
      **Notes:** Keeps operational insight during persistent storage pressure.
