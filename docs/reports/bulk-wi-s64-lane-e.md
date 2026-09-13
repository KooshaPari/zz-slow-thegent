### [WL-8760]

**Title:** Preserve artifact metadata by separating metadata parser and metadata store updates
**Source:** [thegent/src/thegent/artifacts/metadata_store.py:501]
**Acceptance checklist:**

- [ ] Separate metadata parser failures from metadata store update failures.
- [ ] Preserve metadata writes with parser fallback.
- [ ] Add tests for parser and store update branches.
      **Notes:** Helps artifact operations continue under metadata schema drift.

### [WL-8761]

**Title:** Preserve workflow queue by separating workflow parse and workflow queue write
**Source:** [thegent/src/thegent/workflow/queue_writer.py:377]
**Acceptance checklist:**

- [ ] Separate workflow parse failures from queue write failures.
- [ ] Preserve queue writes using parse fallback.
- [ ] Add tests for parse and queue write branches.
      **Notes:** Improves workflow throughput on parse regression cases.

### [WL-8762]

**Title:** Preserve session profile application by separating profile parse and profile apply
**Source:** [thegent/src/thegent/session/profile_apply.py:589]
**Acceptance checklist:**

- [ ] Separate session profile parse failures from profile apply failures.
- [ ] Preserve apply flow with default session profile.
- [ ] Add tests for parse and apply branches.
      **Notes:** Helps maintain session behavior across profile format changes.

### [WL-8763]

**Title:** Preserve event sink health by separating sink config parse and sink health checks
**Source:** [thegent/src/thegent/events/sink_health.py:412]
**Acceptance checklist:**

- [ ] Separate sink configuration parse failures from sink health checks.
- [ ] Preserve sink health checks with fallback configs.
- [ ] Add tests for config parse and health check branches.
      **Notes:** Improves proactive fault detection under sink config drift.

### [WL-8764]

**Title:** Preserve CLI startup by separating startup argument parse and startup hook registration
**Source:** [thegent/src/thegent/cli/startup_hooks.py:523]
**Acceptance checklist:**

- [ ] Separate startup argument parse failures from startup hook registration failures.
- [ ] Preserve hook registration fallback during argument parse issues.
- [ ] Add tests for parse and hook registration branches.
      **Notes:** Increases CLI startup reliability in nonstandard invocations.

### [WL-8765]

**Title:** Preserve queue persistence by separating state serialize and state persist
**Source:** [thegent/src/thegent/queue/state_persist.py:333]
**Acceptance checklist:**

- [ ] Separate queue state serialize failures from persistence failures.
- [ ] Preserve queue state operations with in-memory fallback.
- [ ] Add tests for serialize and persist branches.
      **Notes:** Prevents queue outages during serialization format mismatches.

### [WL-8766]

**Title:** Preserve sync diff application by separating diff parse and diff apply
**Source:** [thegent/src/thegent/sync/diff_apply.py:501]
**Acceptance checklist:**

- [ ] Separate sync diff parse failures from apply failures.
- [ ] Preserve diff apply with fallback parse logic.
- [ ] Add tests for parse and apply branch behavior.
      **Notes:** Increases sync resilience when diff format is inconsistent.

### [WL-8767]

**Title:** Preserve artifact uploader diagnostics by separating diagnostic payload parse and diagnostic emit
**Source:** [thegent/src/thegent/artifacts/upload_diagnostics.py:478]
**Acceptance checklist:**

- [ ] Separate upload diagnostic payload parse failures from diagnostic emission failures.
- [ ] Preserve diagnostics with raw payload fallback.
- [ ] Add tests for payload parse and diagnostic emit branches.
      **Notes:** Improves operator troubleshooting while upload path runs.

### [WL-8768]

**Title:** Preserve policy compilation by separating policy parser and policy compiler runtime
**Source:** [thegent/src/thegent/policies/compiler.py:589]
**Acceptance checklist:**

- [ ] Separate policy parser failures from compiler runtime failures.
- [ ] Preserve runtime with safe policy parser fallback.
- [ ] Add tests for parser and compiler runtime branches.
      **Notes:** Prevents policy deployment blockers from single parser bugs.

### [WL-8769]

**Title:** Preserve task metrics by separating task metric parse and task metric publish
**Source:** [thegent/src/thegent/tasks/metric_publisher.py:378]
**Acceptance checklist:**

- [ ] Separate task metric parse failures from metric publish failures.
- [ ] Preserve publish behavior with parse fallback.
- [ ] Add tests for parse and publish branches.
      **Notes:** Keeps task telemetry useful under payload structure changes.
