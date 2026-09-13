### [WL-7150]

**Title:** Preserve watcher-breaker bootstrap failures as structured capability diagnostics
**Source:** [thegent/src/thegent/native/watcher_daemon.py:101]
**Acceptance checklist:**

- [ ] Replace blanket breaker-bootstrap exception handling with typed import, settings, and path initialization branches.
- [ ] Preserve current `None` return contract when SHM is intentionally disabled or unavailable.
- [ ] Add tests for successful breaker creation, import failures, and invalid SHM path configuration.
      **Notes:** Collapsing all bootstrap failures into a debug-only message obscures why health protection is unavailable.

### [WL-7151]

**Title:** Classify native SHM initialization failures for circuit-breaker startup
**Source:** [thegent/src/thegent/native/state_shm.py:212]
**Acceptance checklist:**

- [ ] Replace broad native-init exception handling with explicit filesystem, native-binding, and permission failure categories.
- [ ] Preserve pure-Python fallback behavior after classified native initialization failures.
- [ ] Add tests for native init success, missing native extension, and backing-file creation errors.
      **Notes:** Untyped init failures make it difficult to diagnose environment versus runtime regressions.

### [WL-7152]

**Title:** Differentiate record-failure write errors from fallback-state execution in breaker updates
**Source:** [thegent/src/thegent/native/state_shm.py:237]
**Acceptance checklist:**

- [ ] Refine `record_failure` error handling to classify native write, category mapping, and transport failures.
- [ ] Preserve fallback store mutation when native writes fail.
- [ ] Add tests for native write success, native write exception, and fallback consistency.
      **Notes:** Generic fallback warnings hide whether event loss is caused by SHM I/O or invalid category mapping.

### [WL-7153]

**Title:** Preserve native circuit-state probe failure details before fallback open-state evaluation
**Source:** [thegent/src/thegent/native/state_shm.py:267]
**Acceptance checklist:**

- [ ] Replace catch-all probe handling in `is_open` with typed native call and threshold-input validation branches.
- [ ] Preserve fallback open/closed semantics when native probing fails.
- [ ] Add tests for native-open responses, native probe exceptions, and fallback threshold behavior.
      **Notes:** Silent probe degradation can mask repeated native outages during breaker decisions.

### [WL-7154]

**Title:** Surface health-score write degradation instead of debug-only suppression
**Source:** [thegent/src/thegent/native/state_shm.py:290]
**Acceptance checklist:**

- [ ] Promote native `set_health_score` failure handling to typed, bounded diagnostics.
- [ ] Preserve no-op semantics when native SHM is unavailable.
- [ ] Add tests for successful score writes, native write failure, and fallback mode behavior.
      **Notes:** Hidden health-score write failures can desynchronize observability from actual runtime health.

### [WL-7155]

**Title:** Distinguish health-score read failures from legitimate zero-health return values
**Source:** [thegent/src/thegent/native/state_shm.py:298]
**Acceptance checklist:**

- [ ] Refactor `get_health_score` error handling to separate native read faults from valid score values.
- [ ] Preserve `0.0` fallback behavior when native interface is absent.
- [ ] Add tests for successful reads, native read exceptions, and fallback default behavior.
      **Notes:** Returning `0.0` for all error modes can mimic severe health degradation and mislead operators.

### [WL-7156]

**Title:** Classify XP tracker native bootstrap failures before fallback activation
**Source:** [thegent/src/thegent/native/state_shm.py:331]
**Acceptance checklist:**

- [ ] Replace broad XpTracker init exception handling with typed path, binding, and runtime failure classes.
- [ ] Preserve pure-Python XP fallback startup when native initialization fails.
- [ ] Add tests for native XP init success, native module errors, and path-creation failures.
      **Notes:** Unclassified bootstrap failures reduce confidence in persisted XP integrity.

### [WL-7157]

**Title:** Preserve XP award native-write failure classes during fallback award execution
**Source:** [thegent/src/thegent/native/state_shm.py:345]
**Acceptance checklist:**

- [ ] Split `award` exception handling into native write, value validation, and bridge-call failure categories.
- [ ] Preserve fallback `award` behavior for recoverable native failures.
- [ ] Add tests for native award success, native exception fallback, and XP total correctness.
      **Notes:** Generic write failures can hide data-shape bugs that should be handled separately from transport errors.

### [WL-7158]

**Title:** Differentiate XP level-set native failures from fallback level mutation paths
**Source:** [thegent/src/thegent/native/state_shm.py:384]
**Acceptance checklist:**

- [ ] Replace catch-all `set_level` native error handling with typed validation and native call failure branches.
- [ ] Preserve fallback level override semantics when native updates fail.
- [ ] Add tests for native level-set success, invalid level values, and fallback level updates.
      **Notes:** Collapsing all level-set failures to debug logs obscures schema validation regressions.

### [WL-7159]

**Title:** Surface native XP state read failure categories in tracker state hydration
**Source:** [thegent/src/thegent/native/state_shm.py:391]
**Acceptance checklist:**

- [ ] Refactor `_get_native_state` exception handling to classify parse, bridge, and payload-shape failures.
- [ ] Preserve `None` contract for unrecoverable native state reads.
- [ ] Add tests for valid native state payloads, malformed payloads, and bridge-call exceptions.
      **Notes:** Undifferentiated native state-read failures make XP/state drift incidents harder to triage.
