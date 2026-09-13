### [WL-8470]

**Title:** Preserve CLI history output by separating history fetch and response redaction
**Source:** [thegent/src/thegent/cli/history.py:378]
**Acceptance checklist:**

- [ ] Separate history fetch failures from response redaction failures.
- [ ] Preserve command history output with safe redaction fallback.
- [ ] Add tests for fetch and redaction branches.
      **Notes:** Keeps command history functional while safeguarding output formatting.

### [WL-8471]

**Title:** Preserve integration callbacks by separating callback parse and callback dispatch
**Source:** [thegent/src/thegent/integrations/callback.py:432]
**Acceptance checklist:**

- [ ] Separate callback payload parsing from callback dispatch.
- [ ] Preserve retry behavior when dispatch path is temporarily unavailable.
- [ ] Add tests for parse and dispatch branches.
      **Notes:** Improves webhook resilience with malformed payloads.

### [WL-8472]

**Title:** Preserve policy diff generation by separating source load and rule comparison
**Source:** [thegent/src/thegent/policies/diff.py:501]
**Acceptance checklist:**

- [ ] Separate source load failures from rule comparison failures.
- [ ] Preserve last-known diff output when source load is partial.
- [ ] Add tests for source and comparison failures.
      **Notes:** Helps audit workflows continue under stale policy sources.

### [WL-8473]

**Title:** Preserve health alerting by separating threshold config and notifier execution
**Source:** [thegent/src/thegent/health/alerts.py:336]
**Acceptance checklist:**

- [ ] Separate threshold config parse failures from notifier execution failures.
- [ ] Preserve alerting with fallback thresholds.
- [ ] Add tests for config and notifier branches.
      **Notes:** Keeps operators informed during notifier instability.

### [WL-8474]

**Title:** Preserve sync conflict handling by separating conflict detect and conflict resolve
**Source:** [thegent/src/thegent/sync/conflict.py:589]
**Acceptance checklist:**

- [ ] Distinguish conflict detection failures from conflict resolution failures.
- [ ] Preserve detected-conflict records on resolve errors.
- [ ] Add tests for detection and resolution branch failures.
      **Notes:** Prevents silent conflict loss under partial failures.

### [WL-8475]

**Title:** Preserve command queue health by separating queue metadata and processing counters
**Source:** [thegent/src/thegent/queue/health.py:413]
**Acceptance checklist:**

- [ ] Separate queue metadata read failures from processing counter updates.
- [ ] Preserve counter accuracy under metadata fallback.
- [ ] Add tests for metadata and counter branch failures.
      **Notes:** Keeps health metrics actionable during partial queue metadata corruption.

### [WL-8476]

**Title:** Preserve artifact cache by separating lookup key normalization and cache miss handling
**Source:** [thegent/src/thegent/artifacts/cache.py:355]
**Acceptance checklist:**

- [ ] Separate lookup key normalization failures from cache miss handling failures.
- [ ] Preserve cache fallback flow when normalization fails.
- [ ] Add tests for normalization and miss handling branches.
      **Notes:** Avoids cache thrash when keys are partially malformed.

### [WL-8477]

**Title:** Preserve CLI command docs by separating parser metadata loading and render assembly
**Source:** [thegent/src/thegent/cli/docs.py:294]
**Acceptance checklist:**

- [ ] Separate parser metadata load failures from command doc render assembly.
- [ ] Preserve command documentation using template fallback.
- [ ] Add tests for metadata and render failures.
      **Notes:** Supports help text reliability across parser metadata drift.

### [WL-8478]

**Title:** Preserve session export by separating data extraction and export formatter
**Source:** [thegent/src/thegent/session/exporter.py:427]
**Acceptance checklist:**

- [ ] Separate session data extraction failures from formatter failures.
- [ ] Preserve export output with degraded formatter behavior.
- [ ] Add tests for extraction and formatter branches.
      **Notes:** Keeps session portability during formatter upgrades.

### [WL-8479]

**Title:** Preserve sync scheduling by separating dependency graph build and worker reservation
**Source:** [thegent/src/thegent/sync/scheduler.py:462]
**Acceptance checklist:**

- [ ] Separate dependency graph build errors from worker reservation errors.
- [ ] Preserve scheduling fallback on reservation failures.
- [ ] Add tests for graph build and reservation branch behavior.
      **Notes:** Prevents scheduling dead zones under transient graph changes.
