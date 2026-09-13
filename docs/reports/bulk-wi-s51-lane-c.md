### [WL-8090]

**Title:** Separate top-level CLI startup failures by argument parsing and runtime bootstrap path
**Source:** [thegent/src/thegent/main.py:84]
**Acceptance checklist:**

- [ ] Split startup argument parse failures from runtime validation failures in the main command entrypoint.
- [ ] Preserve existing successful startup and default resolution behavior for valid argument combinations.
- [ ] Add startup tests covering parse-only failures, validation-only failures, and successful launch path.
      **Notes:** This prevents CLI typo regressions from being masked by runtime bootstrap checks.

### [WL-8091]

**Title:** Split doctor command failure output by environment probe and contract check
**Source:** [thegent/src/thegent/commands/doctor.py:413]
**Acceptance checklist:**

- [ ] Split environment probe errors from contract evaluation failures in command dispatch.
- [ ] Preserve current aggregated health summary output while reporting category-level failure buckets.
- [ ] Add tests for environment-only failure, contract-only failure, and fully successful doctor runs.
      **Notes:** Clear fault taxonomy improves triage for operator-facing diagnostics.

### [WL-8092]

**Title:** Distinguish task frontmatter syntax failures from semantic schema violations
**Source:** [thegent/src/thegent/task/parser.py:112]
**Acceptance checklist:**

- [ ] Emit dedicated errors for malformed frontmatter versus schema/semantic violations.
- [ ] Preserve current successful parse and metadata normalization behavior.
- [ ] Add parser tests for syntax error, semantic rule error, and valid parsing scenarios.
      **Notes:** This reduces repeated re-submission cycles on large task imports.

### [WL-8093]

**Title:** Separate session lifecycle persistence write failures from state transition conflicts
**Source:** [thegent/src/thegent/session/manager.py:25]
**Acceptance checklist:**

- [ ] Split state-transition conflict errors from persistence I/O failures in session mutation paths.
- [ ] Preserve existing successful fork/rollback semantics and current conflict-prevention behavior.
- [ ] Add tests for conflict detection, storage-write failure, and successful transition completion.
      **Notes:** Explicit state buckets make session recovery deterministic under partial failures.

### [WL-8094]

**Title:** Partition sync command argument validation from file mutation application
**Source:** [thegent/src/thegent/commands/sync.py:520]
**Acceptance checklist:**

- [ ] Split invalid-argument validation from mutation execution failure handling.
- [ ] Preserve existing dry-run and full-sync output shape for successful operations.
- [ ] Add tests for invalid arg sets, mutation exceptions, and successful dry-run/sync paths.
      **Notes:** Helps operators see whether failures are input or persistence related.

### [WL-8095]

**Title:** Disentangle workstream parse errors from workstream persistence failures
**Source:** [thegent/src/thegent/commands/workstream.py:120]
**Acceptance checklist:**

- [ ] Separate malformed workstream read/parse failures from writeback persistence failures.
- [ ] Preserve current user-facing behavior for valid workstream command flows.
- [ ] Add regression tests for parse failure, storage write failure, and valid command execution.
      **Notes:** Clearer failure classes cut mean-time-to-recovery for workstream operations.

### [WL-8096]

**Title:** Split multi-level cache probe miss from persistence corruption handling
**Source:** [thegent/src/thegent/cache/multi_level.py:88]
**Acceptance checklist:**

- [ ] Separate cache lookup misses from deserialization/corruption and writeback failures.
- [ ] Preserve current fallback behavior for non-fatal cache misses and maintain hit/miss metrics.
- [ ] Add tests for miss, corrupt payload, writeback failure, and normal cache round-trip.
      **Notes:** Cache reliability improves when recovery paths are classified by failure class.

### [WL-8097]

**Title:** Separate memory manager load-time initialization failures from runtime seed operations
**Source:** [thegent/src/thegent/memory/manager.py:50]
**Acceptance checklist:**

- [ ] Split initialization-time memory backend setup failures from seed CRUD runtime errors.
- [ ] Preserve successful initialization defaults and normal seed lifecycle behavior for valid backends.
- [ ] Add tests for backend-init failure, seed create/update/list failures, and happy-path operations.
      **Notes:** This avoids conflating startup dependency problems with downstream memory operations.

### [WL-8098]

**Title:** Split UI launch diagnostics from underlying protocol binding negotiation
**Source:** [thegent/src/thegent/ux/launch.py:20]
**Acceptance checklist:**

- [ ] Separate launch-path display failures from protocol binding/transport initialization failures.
- [ ] Preserve current user flow for normal startup while surfacing clearer actionable logs for failures.
- [ ] Add tests for launch presentation failures, transport failures, and successful UI launch.
      **Notes:** Better partitioning improves debuggability without changing successful UX behavior.

### [WL-8099]

**Title:** Disentangle model-provider discovery errors from model registration conflicts
**Source:** [thegent/src/thegent/provider_model_manager.py:700]
**Acceptance checklist:**

- [ ] Split provider discovery exceptions from registration/override conflict failures.
- [ ] Preserve existing provider order and fallback behavior for valid registrations.
- [ ] Add tests for discovery outage, registration conflict, and clean registration success cases.
      **Notes:** Clear separation is essential for faster recovery after infra partial outages.
