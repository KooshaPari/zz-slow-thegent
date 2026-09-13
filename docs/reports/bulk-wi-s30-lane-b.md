### [WL-7030]

**Title:** Expose watcher SHM bootstrap failures with typed fallback diagnostics
**Source:** [thegent/src/thegent/native/watcher_daemon.py:100]
**Acceptance checklist:**

- [ ] Replace broad SHM bootstrap exception handling with typed import/config/initialization failure categories.
- [ ] Preserve non-fatal fallback-to-`None` behavior while surfacing deterministic degraded-state diagnostics.
- [ ] Add tests for successful SHM bootstrap, missing dependency import, and invalid SHM path initialization.
      **Notes:** Catch-all failure handling during breaker bootstrap hides whether watcher health telemetry is disabled by config, dependency, or runtime issues.

### [WL-7031]

**Title:** Classify watch callback execution failures before breaker escalation
**Source:** [thegent/src/thegent/native/watcher_daemon.py:207]
**Acceptance checklist:**

- [ ] Replace callback catch-all handling with typed runtime failure classification and bounded diagnostic payloads.
- [ ] Preserve callback isolation and continued watcher processing after per-event failures.
- [ ] Add tests for successful callback execution, expected callback errors, and unexpected callback exceptions.
      **Notes:** Broad callback exception handling currently compresses all callback fault modes into one opaque error path.

### [WL-7032]

**Title:** Preserve breaker-recording failure causes during callback error handling
**Source:** [thegent/src/thegent/native/watcher_daemon.py:217]
**Acceptance checklist:**

- [ ] Replace generic breaker-recording exception handling with explicit transport/state failure categories.
- [ ] Keep watcher callback error flow non-fatal while recording bounded breaker-write failure metadata.
- [ ] Add tests for successful breaker writes, unavailable breaker backend, and runtime write failures.
      **Notes:** Silent-style breaker fallback diagnostics can mask observability loss when callback failures stop incrementing circuit signals.

### [WL-7033]

**Title:** Separate observer start failure classes in watcher daemon lifecycle
**Source:** [thegent/src/thegent/native/watcher_daemon.py:289]
**Acceptance checklist:**

- [ ] Replace broad observer start exception handling with typed startup failure classification.
- [ ] Preserve existing raise behavior while attaching actionable startup diagnostics.
- [ ] Add tests for successful start, filesystem permission failures, and observer backend initialization failures.
      **Notes:** Generic startup exceptions obscure why watcher startup failed and slow operational triage.

### [WL-7034]

**Title:** Distinguish observer stop failures from join-time shutdown errors
**Source:** [thegent/src/thegent/native/watcher_daemon.py:312]
**Acceptance checklist:**

- [ ] Replace broad shutdown exception handling with explicit stop-versus-join failure diagnostics.
- [ ] Preserve idempotent shutdown semantics and cleanup thread signaling.
- [ ] Add tests for clean shutdown, observer stop failure, and join timeout/error paths.
      **Notes:** Collapsing shutdown failure modes into generic warnings makes daemon lifecycle regressions harder to diagnose.

### [WL-7035]

**Title:** Classify native SHM initialization failures in circuit breaker bootstrap
**Source:** [thegent/src/thegent/native/state_shm.py:212]
**Acceptance checklist:**

- [ ] Replace catch-all native SHM init handling with typed path, permission, and extension-call error branches.
- [ ] Preserve fallback store behavior while emitting deterministic failure metadata for native initialization loss.
- [ ] Add tests for native init success, invalid SHM path, and extension constructor failure.
      **Notes:** Broad fallback handling hides the root cause of native circuit-breaker disablement.

### [WL-7036]

**Title:** Preserve native record-failure transport errors before fallback write
**Source:** [thegent/src/thegent/native/state_shm.py:237]
**Acceptance checklist:**

- [ ] Replace generic native `record_failure` exception handling with explicit failure-category diagnostics.
- [ ] Preserve fallback write semantics when native writes fail.
- [ ] Add tests for native write success, native write exception fallback, and repeated fallback behavior under persistent native errors.
      **Notes:** One-size-fits-all warnings for native write failures limit reliability debugging for SHM-backed breaker state.

### [WL-7037]

**Title:** Surface malformed queue-entry parse drops with bounded skip accounting
**Source:** [thegent/src/thegent/queue/storage.py:29]
**Acceptance checklist:**

- [ ] Replace silent JSON parse suppression in queue file reads with bounded malformed-line accounting.
- [ ] Preserve tolerant queue ingestion behavior for valid lines.
- [ ] Add tests for fully valid queue files, mixed valid/invalid lines, and completely malformed files.
      **Notes:** Silent malformed-line drops can make queue depth and ordering appear healthy when records are being discarded.

### [WL-7038]

**Title:** Differentiate lease timestamp decode failures from truly expired claims
**Source:** [thegent/src/thegent/queue/storage.py:85]
**Acceptance checklist:**

- [ ] Replace blanket lease-parse exception suppression with typed timestamp-format diagnostics.
- [ ] Preserve existing include-expired filtering behavior for well-formed lease timestamps.
- [ ] Add tests for valid lease timestamps, malformed lease values, and missing lease fields.
      **Notes:** Current exception suppression conflates bad lease metadata with normal queue-filtering behavior.

### [WL-7039]

**Title:** Expose lockfile JSON decode failures during queue read under lock
**Source:** [thegent/src/thegent/queue/locking.py:54]
**Acceptance checklist:**

- [ ] Replace silent locked-read JSON parse suppression with bounded malformed-entry diagnostics.
- [ ] Preserve lock-holding read continuity for valid entries.
- [ ] Add tests for valid locked reads, mixed malformed rows, and corrupted lockfile content.
      **Notes:** Suppressing parse failures while holding the lock can hide queue data corruption and complicate recovery.
