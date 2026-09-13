### [WL-8040]

**Title:** Separate thegent startup config errors by source and remediation path
**Source:** [thegent/src/thegent/config_defaults.py:78]
**Acceptance checklist:**

- [ ] Split startup bootstrap failures into missing-file, parse, and schema-merge branches in config loading.
- [ ] Preserve existing precedence and fallback behavior for optional config inputs while surfacing explicit remediation for hard failures.
- [ ] Add regression tests for missing config, malformed values, and successful default merge paths.
      **Notes:** Clear fault separation shortens configuration triage and avoids ambiguous startup states.

### [WL-8041]

**Title:** Partition shell CLI argument parsing failures from execution-time validation
**Source:** [thegent/src/thegent/main.py:90]
**Acceptance checklist:**

- [ ] Split CLI parse failures from post-parse runtime validation and return distinct diagnostic envelopes.
- [ ] Keep current successful command startup semantics for valid argument combinations and env defaults.
- [ ] Add tests that assert parse-only failures, validation-only failures, and successful startup behavior.
      **Notes:** Deterministic failure classes help distinguish user typos from policy constraints.

### [WL-8042]

**Title:** Disambiguate doctor check failures by check category and execution mode
**Source:** [thegent/src/thegent/doctor.py:145]
**Acceptance checklist:**

- [ ] Split doctor checks into availability, contract, and runtime checks with separate failure reporting.
- [ ] Preserve existing aggregated summary output while adding category-level status metadata.
- [ ] Add tests for each check category plus mixed-failure and all-green doctor runs.
      **Notes:** Category-level visibility prevents false urgency from non-blocking checks.

### [WL-8043]

**Title:** Split workstream sync argument parsing from persistence mutation errors
**Source:** [thegent/src/thegent/commands/sync.py:520]
**Acceptance checklist:**

- [ ] Separate CLI sync command argument validation from file mutation and writeback error handling.
- [ ] Preserve current rollback semantics for partially written workstream files.
- [ ] Add tests for invalid arguments, write failures, and idempotent successful sync execution.
      **Notes:** Explicit fault buckets make sync operations safer under partial infrastructure failures.

### [WL-8044]

**Title:** Distinguish task frontmatter syntax from payload semantic violations in parsing
**Source:** [thegent/src/thegent/task/parser.py:112]
**Acceptance checklist:**

- [ ] Emit separate parser errors for malformed frontmatter and semantic schema mismatches.
- [ ] Preserve successful parsing behavior for valid tasks and existing metadata normalization.
- [ ] Add tests for malformed YAML delimiters, invalid fields, and valid task bodies.
      **Notes:** Clear separation reduces duplicate parse-fix loops.

### [WL-8045]

**Title:** Split task validation into structural and semantic rule paths
**Source:** [thegent/src/thegent/task/validator.py:170]
**Acceptance checklist:**

- [ ] Separate required-field checks from semantic cross-field rules and constraint-specific diagnostics.
- [ ] Preserve valid-task throughput and existing task-level validation output format for accepted tasks.
- [ ] Add tests for missing-required fields, cross-field violations, and clean validation sets.
      **Notes:** Structured failures make schema repair easier under large task imports.

### [WL-8046]

**Title:** Separate sync engine planning from execution for clearer state transitions
**Source:** [thegent/src/thegent/sync/engine.py:18]
**Acceptance checklist:**

- [ ] Split plan construction failures from execution failures with explicit transition states.
- [ ] Preserve current sync outcomes and keep successful dry-run paths behavior unchanged.
- [ ] Add tests for plan-only failures, execution faults, and full successful engine runs.
      **Notes:** Distinguishing planning and execution failures makes sync recovery deterministic.

### [WL-8047]

**Title:** Isolate routing fallback decisions from capability checks
**Source:** [thegent/src/thegent/routing/auto_router.py:132]
**Acceptance checklist:**

- [ ] Separate capability detection failures from fallback selection and retry policy failures in routing logic.
- [ ] Preserve existing successful route selection ordering and deterministic provider hints.
- [ ] Add tests for capability-gaps, fallback transitions, and stable successful auto-routing.
      **Notes:** Routing resilience depends on being explicit about why each fallback branch was chosen.

### [WL-8048]

**Title:** Disentangle project registry load errors from namespace merge conflicts
**Source:** [thegent/src/thegent/registry/project_registry.py:256]
**Acceptance checklist:**

- [ ] Split registry load exceptions into transport/load and namespace-merge conflict branches.
- [ ] Preserve successful namespace overlays and existing default registry fallback behavior.
- [ ] Add tests for missing registries, merge conflicts, and stable namespace merges.
      **Notes:** Clean conflict partitioning prevents partial registry corruption.

### [WL-8049]

**Title:** Separate alert rendering failures from alert state hydration errors
**Source:** [thegent/src/thegent/ux/alerts.py:33]
**Acceptance checklist:**

- [ ] Split alert fetch/hydrate failures from render-time failures and return structured error envelopes.
- [ ] Preserve successful alert display behavior for valid hydrated payloads.
- [ ] Add tests for fetch failures, render failures, and fully healthy alert pipelines.
      **Notes:** Isolated alert failure paths help unblock diagnostics without breaking UI state.
