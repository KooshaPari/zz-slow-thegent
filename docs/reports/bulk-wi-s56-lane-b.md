### [WL-8330]

**Title:** Preserve event bus handling by separating deserialize and authorization failures
**Source:** [thegent/src/thegent/events/bus.py:214]
**Acceptance checklist:**

- [ ] Separate message deserialize failures from permission validation failures.
- [ ] Keep authorized events processed when malformed messages are dropped.
- [ ] Add tests for malformed payloads and auth-denied branches.
      **Notes:** Prevents one bad event format from dropping valid traffic.

### [WL-8331]

**Title:** Preserve session persistence by separating snapshot serialization and file-system write
**Source:** [thegent/src/thegent/session/snapshot.py:334]
**Acceptance checklist:**

- [ ] Separate snapshot serialization errors from filesystem write errors.
- [ ] Preserve session continuity with in-memory snapshots on FS failures.
- [ ] Add tests for both error branches.
      **Notes:** Improves recovery in ephemeral storage environments.

### [WL-8332]

**Title:** Preserve telemetry ingestion by separating metric schema and endpoint dispatch
**Source:** [thegent/src/thegent/telemetry/ingest.py:276]
**Acceptance checklist:**

- [ ] Isolate metric schema validation failures from endpoint network failures.
- [ ] Keep queueing behavior unchanged for invalid schema.
- [ ] Add tests for schema and transport branch handling.
      **Notes:** Preserves observability while containing invalid payloads.

### [WL-8333]

**Title:** Preserve auth token rotation while separating token parse and storage
**Source:** [thegent/src/thegent/auth/rotation.py:409]
**Acceptance checklist:**

- [ ] Split token decode failures from persistence failures.
- [ ] Keep rotation cycle running when storage writes fail transiently.
- [ ] Add tests for decode versus persistence conditions.
      **Notes:** Helps prevent auth outages from stale but valid tokens.

### [WL-8334]

**Title:** Preserve task scheduling by separating priority parse and queue insertion
**Source:** [thegent/src/thegent/scheduler/queue.py:461]
**Acceptance checklist:**

- [ ] Separate invalid priority parse from queue insertion failures.
- [ ] Preserve insertion defaults for parse errors.
- [ ] Add tests for invalid priority and queue-insert faults.
      **Notes:** Keeps scheduling available when one field is malformed.

### [WL-8335]

**Title:** Preserve file watcher behavior while separating path registration and event emission
**Source:** [thegent/src/thegent/watcher/paths.py:188]
**Acceptance checklist:**

- [ ] Separate path registration failures from event emission failures.
- [ ] Keep active watchers operational on emission branch errors.
- [ ] Add tests for registration and emit branches.
      **Notes:** Avoids blind spots in watcher observability.

### [WL-8336]

**Title:** Preserve plugin state reconciliation by separating diff calculation and application
**Source:** [thegent/src/thegent/ui/plugin_sync.py:311]
**Acceptance checklist:**

- [ ] Split desired-state diff generation from patch application.
- [ ] Preserve existing state while surfacing diff failures.
- [ ] Add tests for diff and patch failure modes.
      **Notes:** Reduces unintended UI drift under partial sync failure.

### [WL-8337]

**Title:** Preserve prompt compilation by separating template compile and variable resolution
**Source:** [thegent/src/thegent/prompt/engine.py:287]
**Acceptance checklist:**

- [ ] Separate compilation syntax failures from variable resolution misses.
- [ ] Keep fallback variable set when compilation fails.
- [ ] Add tests for compile and resolve branches separately.
      **Notes:** Improves prompt reliability during template evolution.

### [WL-8338]

**Title:** Preserve CLI output contract while separating formatting and compression branches
**Source:** [thegent/src/thegent/cli/output.py:356]
**Acceptance checklist:**

- [ ] Split output formatter failures from compression failures.
- [ ] Preserve output payload shape on compression errors.
- [ ] Add tests for both output pathways.
      **Notes:** Keeps CLI scripts compatible when one optimization fails.

### [WL-8339]

**Title:** Preserve artifact indexing by separating filename normalization and DB write
**Source:** [thegent/src/thegent/artifacts/index.py:244]
**Acceptance checklist:**

- [ ] Distinguish filename normalization failures from index persistence failures.
- [ ] Keep index consistency when persistence fails by deferring non-critical normalizations.
- [ ] Add tests for both branches and visibility metrics.
      **Notes:** Prevents index corruption during partial failure conditions.
