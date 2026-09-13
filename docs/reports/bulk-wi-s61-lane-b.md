### [WL-8580]

**Title:** Preserve config migration by separating migration manifest parse and migration state writes
**Source:** [thegent/src/thegent/config/migration_engine.py:331]
**Acceptance checklist:**

- [ ] Separate migration manifest parse failures from migration state write failures.
- [ ] Preserve migration progress with state-write fallback.
- [ ] Add tests for manifest and state-write branches.
      **Notes:** Prevents migration deadlock when manifest schema drifts.

### [WL-8581]

**Title:** Preserve queue drain health by separating backlog stats compute and health signal generation
**Source:** [thegent/src/thegent/queue/drain_health.py:589]
**Acceptance checklist:**

- [ ] Separate backlog stats computation failures from health signal generation.
- [ ] Preserve health signaling with statistic fallback.
- [ ] Add tests for compute and signal branches.
      **Notes:** Improves operational visibility during backpressure spikes.

### [WL-8582]

**Title:** Preserve API connector sync by separating connector capabilities parse and connector registration
**Source:** [thegent/src/thegent/connectors/sync.py:477]
**Acceptance checklist:**

- [ ] Separate connector capabilities parsing failures from connector registration failures.
- [ ] Preserve connector registration defaults when capabilities parsing fails.
- [ ] Add tests for parse and registration branches.
      **Notes:** Keeps connectors discoverable despite partial capability metadata.

### [WL-8583]

**Title:** Preserve artifact export by separating export descriptor parse and export transport
**Source:** [thegent/src/thegent/artifacts/exporter.py:498]
**Acceptance checklist:**

- [ ] Separate export descriptor parsing failures from transport send failures.
- [ ] Preserve export transport with descriptor fallback.
- [ ] Add tests for descriptor parse and transport branches.
      **Notes:** Supports exports when one descriptor definition is partially invalid.

### [WL-8584]

**Title:** Preserve session telemetry by separating session event parse and telemetry batching
**Source:** [thegent/src/thegent/session/telemetry.py:333]
**Acceptance checklist:**

- [ ] Separate session event parse failures from telemetry batching failures.
- [ ] Preserve batching with parse fallback.
- [ ] Add tests for event parse and batching paths.
      **Notes:** Improves telemetry stability in high-volume sessions.

### [WL-8585]

**Title:** Preserve routing cache invalidation by separating policy token parse and route cache invalidation
**Source:** [thegent/src/thegent/routing/cache.py:512]
**Acceptance checklist:**

- [ ] Separate routing policy token parse failures from cache invalidation failures.
- [ ] Preserve cache invalidation fallback for parse failures.
- [ ] Add tests for token parse and invalidation branches.
      **Notes:** Prevents unnecessary routing misses during token format drift.

### [WL-8586]

**Title:** Preserve prompt execution by separating prompt body parse and execution context binding
**Source:** [thegent/src/thegent/prompt/executor.py:357]
**Acceptance checklist:**

- [ ] Separate prompt body parse failures from execution context binding failures.
- [ ] Preserve execution context when parse fails.
- [ ] Add tests for parse and context binding branches.
      **Notes:** Keeps prompt execution continuity under malformed inputs.

### [WL-8587]

**Title:** Preserve API retry logs by separating retry event parse and log persistence
**Source:** [thegent/src/thegent/api/retry_logger.py:451]
**Acceptance checklist:**

- [ ] Separate retry event parse failures from log persistence failures.
- [ ] Preserve retry event logs with fallback persistence mode.
- [ ] Add tests for parse and persistence branch failures.
      **Notes:** Improves failure forensics when retry events are malformed.

### [WL-8588]

**Title:** Preserve task dependency planning by separating dependency parse and scheduling algorithm
**Source:** [thegent/src/thegent/planning/dependencies.py:389]
**Acceptance checklist:**

- [ ] Separate dependency parse failures from scheduling algorithm failures.
- [ ] Preserve scheduling algorithm fallback behavior.
- [ ] Add tests for parse and scheduling branches.
      **Notes:** Reduces unnecessary task drops from malformed dependency data.

### [WL-8589]

**Title:** Preserve artifact pruning by separating prune list parse and prune execution
**Source:** [thegent/src/thegent/artifacts/prune.py:523]
**Acceptance checklist:**

- [ ] Separate prune list parse failures from prune execution failures.
- [ ] Preserve execution with conservative prune defaults.
- [ ] Add tests for list parse and execution branches.
      **Notes:** Prevents over-pruning when prune input is partially malformed.
