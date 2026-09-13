### [WL-8720]

**Title:** Preserve command scheduler by separating schedule parse and task enqueueing
**Source:** [thegent/src/thegent/commands/scheduler.py:612]
**Acceptance checklist:**

- [ ] Separate schedule parse failures from task enqueueing failures.
- [ ] Preserve enqueueing with default scheduling on parse errors.
- [ ] Add tests for parse and enqueue branches.
      **Notes:** Improves command scheduling resilience under malformed schedules.

### [WL-8721]

**Title:** Preserve sync metrics by separating metric source parse and metric sink write
**Source:** [thegent/src/thegent/sync/metrics.py:522]
**Acceptance checklist:**

- [ ] Separate sync metric source parse failures from metric sink write failures.
- [ ] Preserve sink writes with source fallback behavior.
- [ ] Add tests for source parse and sink write branches.
      **Notes:** Helps monitoring remain informative under source format drift.

### [WL-8722]

**Title:** Preserve CLI plugin registration by separating plugin config parse and command hook binding
**Source:** [thegent/src/thegent/cli/plugin_config.py:401]
**Acceptance checklist:**

- [ ] Separate plugin config parse failures from command hook binding failures.
- [ ] Preserve hook bindings during config parse regressions.
- [ ] Add tests for config parse and hook binding branches.
      **Notes:** Keeps plugin capabilities discoverable during config drift.

### [WL-8723]

**Title:** Preserve artifact indexing by separating index source parse and index commit
**Source:** [thegent/src/thegent/artifacts/index_queue.py:458]
**Acceptance checklist:**

- [ ] Separate index source parse failures from commit failures.
- [ ] Preserve commit path with source fallback.
- [ ] Add tests for source and commit branch handling.
      **Notes:** Reduces index inconsistency under sporadic source payload issues.

### [WL-8724]

**Title:** Preserve authentication token refresh by separating refresh token parse and refresh call
**Source:** [thegent/src/thegent/auth/refresh.py:336]
**Acceptance checklist:**

- [ ] Separate refresh token parse failures from refresh request call failures.
- [ ] Preserve refresh attempt path with parse fallback tokens.
- [ ] Add tests for parse and refresh branch errors.
      **Notes:** Improves auth reliability under token shape changes.

### [WL-8725]

**Title:** Preserve queue diagnostics by separating metric scrape parse and diagnostics report
**Source:** [thegent/src/thegent/queue/diagnostics_report.py:512]
**Acceptance checklist:**

- [ ] Separate scrape parse failures from diagnostics report generation failures.
- [ ] Preserve report continuity with raw scrape payloads.
- [ ] Add tests for scrape and report branch failures.
      **Notes:** Keeps queue troubleshooting data available during schema churn.

### [WL-8726]

**Title:** Preserve policy enforcement by separating policy target resolution and enforcement action
**Source:** [thegent/src/thegent/policies/enforce_action.py:531]
**Acceptance checklist:**

- [ ] Separate policy target resolution failures from enforcement action failures.
- [ ] Preserve action execution with safe target fallback.
- [ ] Add tests for target and action branch behavior.
      **Notes:** Prevents enforcement stalling when one policy target is malformed.

### [WL-8727]

**Title:** Preserve sync conflict merge by separating conflict key parse and conflict merge execution
**Source:** [thegent/src/thegent/sync/conflict_merge.py:378]
**Acceptance checklist:**

- [ ] Separate conflict key parse failures from merge execution failures.
- [ ] Preserve merge attempts on key parse fallback.
- [ ] Add tests for parse and merge branch failures.
      **Notes:** Improves merge continuity during conflict metadata inconsistencies.

### [WL-8728]

**Title:** Preserve event replay by separating replay cursor parse and replay cursor store
**Source:** [thegent/src/thegent/events/replay_cursor.py:523]
**Acceptance checklist:**

- [ ] Separate replay cursor parse failures from cursor store update failures.
- [ ] Preserve replay operation with cursor fallback.
- [ ] Add tests for parse and store update branches.
      **Notes:** Improves replay behavior under cursor format changes.

### [WL-8729]

**Title:** Preserve CLI output transport by separating output formatter and transport channel
**Source:** [thegent/src/thegent/cli/output_transport.py:457]
**Acceptance checklist:**

- [ ] Separate output formatting failures from transport channel failures.
- [ ] Preserve transport fallback for non-formatter-compatible outputs.
- [ ] Add tests for formatter and transport branches.
      **Notes:** Keeps CLI output available under mixed formatter behavior.
