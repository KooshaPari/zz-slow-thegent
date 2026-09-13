### [WL-8570]

**Title:** Preserve sync worker pool by separating worker descriptor parse and worker spawning
**Source:** [thegent/src/thegent/sync/worker_pool.py:412]
**Acceptance checklist:**

- [ ] Separate worker descriptor parse failures from worker spawn failures.
- [ ] Preserve existing worker pool during descriptor parse failures.
- [ ] Add tests for descriptor parsing and spawn paths.
      **Notes:** Improves worker availability under transient descriptor schema changes.

### [WL-8571]

**Title:** Preserve command execution audit by separating command hash and audit stream
**Source:** [thegent/src/thegent/commands/audit_logger.py:378]
**Acceptance checklist:**

- [ ] Separate command hash calculation failures from audit stream failures.
- [ ] Preserve audit stream with hash fallback data.
- [ ] Add tests for hash and stream branch failures.
      **Notes:** Keeps audits resilient when hash dependencies change.

### [WL-8572]

**Title:** Preserve artifact encryption by separating key lookup and encryption service call
**Source:** [thegent/src/thegent/security/artifact_crypto.py:531]
**Acceptance checklist:**

- [ ] Separate key lookup failures from encryption service invocation failures.
- [ ] Preserve plaintext fallback indicators when encryption service degrades.
- [ ] Add tests for key lookup and service call branches.
      **Notes:** Improves graceful degradation under key service outages.

### [WL-8573]

**Title:** Preserve health endpoint rendering by separating health dataset parse and renderer
**Source:** [thegent/src/thegent/health/renderer.py:449]
**Acceptance checklist:**

- [ ] Separate health dataset parse failures from response rendering failures.
- [ ] Preserve health endpoint output with render fallback.
- [ ] Add tests for parse and render branch handling.
      **Notes:** Maintains monitoring reliability when one layer breaks.

### [WL-8574]

**Title:** Preserve queue throttle by separating throttle policy read and throttle application
**Source:** [thegent/src/thegent/queue/throttle.py:333]
**Acceptance checklist:**

- [ ] Separate throttle policy read failures from throttle application failures.
- [ ] Preserve default throttling behavior with policy read fallback.
- [ ] Add tests for policy read and application branches.
      **Notes:** Stabilizes queue throughput under policy store issues.

### [WL-8575]

**Title:** Preserve sync checkpoints by separating checkpoint diff computation and persistence
**Source:** [thegent/src/thegent/sync/checkpoint_engine.py:601]
**Acceptance checklist:**

- [ ] Separate checkpoint diff compute failures from persistence write failures.
- [ ] Preserve checkpoint state in-memory on persistence issues.
- [ ] Add tests for diff and persistence branch failures.
      **Notes:** Improves recovery checkpoints under storage instability.

### [WL-8576]

**Title:** Preserve command completion cache by separating suggestion generation and ranking
**Source:** [thegent/src/thegent/cli/completion_suggest.py:357]
**Acceptance checklist:**

- [ ] Separate suggestion generation failures from ranking failures.
- [ ] Preserve basic ranking on generation failures.
- [ ] Add tests for generation and ranking branches.
      **Notes:** Keeps autocomplete quality from dropping to empty quickly.

### [WL-8577]

**Title:** Preserve artifact upload integrity by separating manifest validation and transfer scheduling
**Source:** [thegent/src/thegent/artifacts/upload_validator.py:412]
**Acceptance checklist:**

- [ ] Separate artifact manifest validation failures from transfer scheduling failures.
- [ ] Preserve transfer scheduling on validation fallback.
- [ ] Add tests for validation and scheduling branch handling.
      **Notes:** Reduces upload regressions from strict manifest checks.

### [WL-8578]

**Title:** Preserve shell session resume by separating session snapshot parse and session restore
**Source:** [thegent/src/thegent/shell/session_resume.py:412]
**Acceptance checklist:**

- [ ] Separate snapshot parse failures from restore execution failures.
- [ ] Preserve restore fallback when snapshots are malformed.
- [ ] Add tests for parse and restore branches.
      **Notes:** Improves operator continuity after snapshot interruptions.

### [WL-8579]

**Title:** Preserve task telemetry emission by separating telemetry extraction and delivery queue
**Source:** [thegent/src/thegent/observability/task_telemetry.py:501]
**Acceptance checklist:**

- [ ] Separate telemetry extraction failures from delivery queueing failures.
- [ ] Keep telemetry delivery queue active on extraction failures.
- [ ] Add tests for extraction and queueing branches.
      **Notes:** Maintains telemetry throughput under partial extraction issues.
