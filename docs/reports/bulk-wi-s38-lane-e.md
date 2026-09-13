### [WL-7460]

**Title:** Enforce concrete sync component implementations for the orchestrator `sync` contract
**Source:** [thegent/src/thegent/sync/orchestrator.py:52]
**Acceptance checklist:**

- [ ] Enforce runtime registration validation so components missing a concrete `sync` implementation are rejected early.
- [ ] Preserve current async execution behavior for valid components.
- [ ] Add tests that verify abstract-only components fail registration while concrete components execute successfully.
      **Notes:** Line 52 is an abstract `sync` contract that currently uses `pass`.

### [WL-7461]

**Title:** Enforce concrete update behavior for sync components instead of accepting abstract-only stubs
**Source:** [thegent/src/thegent/sync/orchestrator.py:56]
**Acceptance checklist:**

- [ ] Require a concrete `update` implementation for all registered sync components.
- [ ] Preserve backward compatibility for components that intentionally delegate `update` to `sync`.
- [ ] Add tests covering missing `update` implementations and successful delegated update flows.
      **Notes:** Line 56 is an abstract `update` contract that currently uses `pass`.

### [WL-7462]

**Title:** Add explicit metadata validation for audit type `name` to prevent invalid plugin registration
**Source:** [thegent/src/thegent/sync/audit_framework.py:84]
**Acceptance checklist:**

- [ ] Validate that each audit type exposes a non-empty and unique `name` value at registration time.
- [ ] Preserve existing audit execution behavior for valid built-in audit types.
- [ ] Add tests for missing/empty names and duplicate name collisions.
      **Notes:** Line 84 is the abstract `name` property placeholder implemented as `pass`.

### [WL-7463]

**Title:** Validate audit type `description` contract for complete audit catalog surfacing
**Source:** [thegent/src/thegent/sync/audit_framework.py:89]
**Acceptance checklist:**

- [ ] Enforce non-empty `description` values for audit types during framework initialization.
- [ ] Preserve current output format for existing audit summaries.
- [ ] Add tests for missing description text and valid descriptions.
      **Notes:** Line 89 is the abstract `description` property placeholder implemented as `pass`.

### [WL-7464]

**Title:** Add deterministic failure handling for audit type `run` implementations in the framework lifecycle
**Source:** [thegent/src/thegent/sync/audit_framework.py:93]
**Acceptance checklist:**

- [ ] Add explicit guardrails so invalid `run` implementations are reported as typed framework errors.
- [ ] Preserve successful execution paths for properly implemented audit types.
- [ ] Add tests for successful audit execution and invalid run-method implementations.
      **Notes:** Line 93 is the abstract async `run` contract with `pass` placeholder behavior.

### [WL-7465]

**Title:** Replace placeholder update success path with executable component and dependency update workflow
**Source:** [thegent/src/thegent/commands/sync.py:569]
**Acceptance checklist:**

- [ ] Implement real update execution with concrete update actions and outcome reporting.
- [ ] Preserve existing dry-run semantics and messaging.
- [ ] Add tests for update success, no-op updates, and surfaced update failures.
      **Notes:** Line 569 documents the current `update` path as a placeholder success response.

### [WL-7466]

**Title:** Implement remote-backed sync push transport instead of stub-only file reporting
**Source:** [thegent/src/thegent/commands/sync.py:662]
**Acceptance checklist:**

- [ ] Implement authenticated push transport to configured sync targets.
- [ ] Preserve existing file discovery and target resolution behavior.
- [ ] Add tests for successful push, missing target configuration, and partial push failures.
      **Notes:** Line 662 returns a stub message and does not perform remote push operations.

### [WL-7467]

**Title:** Implement sync pull state ingestion pipeline with validation and apply steps
**Source:** [thegent/src/thegent/commands/sync.py:700]
**Acceptance checklist:**

- [ ] Implement remote pull transport and structured payload validation.
- [ ] Apply pulled state via explicit local update operations with conflict handling.
- [ ] Add tests for successful pull, unreachable source, and invalid payload handling.
      **Notes:** Line 700 returns a stub response with no remote backend integration.

### [WL-7468]

**Title:** Implement non-stub reset operations with audited local state rollback
**Source:** [thegent/src/thegent/commands/sync.py:741]
**Acceptance checklist:**

- [ ] Execute concrete reset operations for supported local sync artifacts.
- [ ] Preserve safe defaults with explicit confirmation/audit output for destructive paths.
- [ ] Add tests for successful reset, no-op reset, and reset failure recovery.
      **Notes:** Line 741 reports a stub reset summary without applying any reset changes.

### [WL-7469]

**Title:** Replace stubbed board sync executor with provider-specific GitHub and Linear synchronization
**Source:** [thegent/src/thegent/commands/sync.py:1007]
**Acceptance checklist:**

- [ ] Implement provider-specific board sync adapters for GitHub Projects and Linear.
- [ ] Preserve current work-stream parsing and dry-run reporting behavior.
- [ ] Add tests for successful sync, provider auth/config failures, and per-item update failures.
      **Notes:** Line 1007 returns a stubbed board sync result (`"stub": True`).
