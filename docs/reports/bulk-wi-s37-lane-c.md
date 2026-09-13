### [WL-7390]

**Title:** Replace abstract evaluator `NotImplementedError` surface with protocol-backed evaluation contract checks
**Source:** [thegent/src/thegent/evals/integration.py:57]
**Acceptance checklist:**

- [ ] Introduce a typed evaluator protocol or abstract contract validation that is enforced at evaluator registration time.
- [ ] Preserve explicit failure behavior for evaluators that do not implement required scoring semantics.
- [ ] Add tests for valid evaluator implementations and invalid subclasses missing `evaluate` behavior.
      **Notes:** Line 57 currently raises `NotImplementedError` directly in the base evaluator path.

### [WL-7391]

**Title:** Classify WORK_STREAM enrichment read failures in task migration instead of silently skipping context
**Source:** [thegent/src/thegent/task/migrate.py:65]
**Acceptance checklist:**

- [ ] Replace blanket exception suppression around WORK_STREAM parsing with typed file-read and decode handling.
- [ ] Preserve task migration output shape when enrichment data is unavailable.
- [ ] Add tests for successful enrichment, missing file, and malformed WORK_STREAM payloads.
      **Notes:** Line 65 currently swallows all enrichment read failures with `pass`.

### [WL-7392]

**Title:** Differentiate JSON sniffing parse failures from true legacy-format detection in task parser
**Source:** [thegent/src/thegent/task/parser.py:68]
**Acceptance checklist:**

- [ ] Replace broad JSON detection exception suppression with explicit decode-error handling and diagnostics.
- [ ] Preserve format auto-detection precedence for YAML frontmatter and legacy task forms.
- [ ] Add tests for valid JSON, malformed JSON, and mixed-format edge cases.
      **Notes:** Line 68 currently suppresses all JSON parse failures during format detection.

### [WL-7393]

**Title:** Implement real update execution in sync manager instead of placeholder success responses
**Source:** [thegent/src/thegent/commands/sync.py:569]
**Acceptance checklist:**

- [ ] Replace placeholder update success path with concrete dependency/component update actions.
- [ ] Preserve dry-run behavior with accurate no-change reporting.
- [ ] Add tests for successful update, no-op update, and update failure propagation.
      **Notes:** Line 569 documents the current update path as placeholder-only behavior.

### [WL-7394]

**Title:** Replace stubbed sync push message with backend-backed remote publish workflow
**Source:** [thegent/src/thegent/commands/sync.py:662]
**Acceptance checklist:**

- [ ] Implement remote push transport with deterministic per-file success/failure reporting.
- [ ] Preserve current target resolution rules from CLI arg and settings fallback.
- [ ] Add tests for successful push, unreachable target, and partial transfer failures.
      **Notes:** Line 662 returns a `[stub]` push message instead of executing remote sync.

### [WL-7395]

**Title:** Replace stubbed sync pull path with remote state fetch and local apply pipeline
**Source:** [thegent/src/thegent/commands/sync.py:700]
**Acceptance checklist:**

- [ ] Implement pull transport to fetch canonical remote state artifacts.
- [ ] Apply pulled state through validated local write/update operations with explicit conflict handling.
- [ ] Add tests for successful pull, missing remote state, and invalid remote payloads.
      **Notes:** Line 700 currently returns a `[stub]` pull response with no backend integration.

### [WL-7396]

**Title:** Implement concrete sync reset operations instead of non-destructive stub-only reporting
**Source:** [thegent/src/thegent/commands/sync.py:741]
**Acceptance checklist:**

- [ ] Replace reset stub response with explicit local-state reset actions scoped to documented targets.
- [ ] Preserve auditability by returning deterministic file-level reset changes.
- [ ] Add tests for successful reset execution, empty-reset scenarios, and recoverable reset failures.
      **Notes:** Line 741 currently reports what would reset without performing reset operations.

### [WL-7397]

**Title:** Implement provider-specific board sync executor rather than stubbed mirrored-item returns
**Source:** [thegent/src/thegent/commands/sync.py:1007]
**Acceptance checklist:**

- [ ] Replace stub board sync return payload with real GitHub/Linear sync operations.
- [ ] Preserve source-specific mapping rules from WORK_STREAM item status to board item state.
- [ ] Add tests for successful board sync, auth failures, and per-item sync errors.
      **Notes:** Line 1007 marks board sync output as stubbed and always successful.

### [WL-7398]

**Title:** Persist model tier mutations in promoter workflow instead of no-op tier updates
**Source:** [thegent/src/thegent/learning/promotion.py:24]
**Acceptance checklist:**

- [ ] Implement `_update_model_tier` to persist catalog tier changes for promoted models.
- [ ] Validate model existence and accepted tier values before committing updates.
- [ ] Add tests for successful promotion persistence, unknown model IDs, and invalid tier transitions.
      **Notes:** Line 24 is an unimplemented `pass` in the tier update function.

### [WL-7399]

**Title:** Implement conflict-aware config synchronization engine for unified config manager
**Source:** [thegent/src/thegent/integration/unified_config.py:162]
**Acceptance checklist:**

- [ ] Implement conflict detection across config sources using deterministic precedence rules.
- [ ] Apply a merge strategy that preserves source-of-truth provenance per updated key.
- [ ] Add tests for conflict-free sync, merge conflicts, and idempotent repeated sync runs.
      **Notes:** Line 162 is a placeholder and does not perform any synchronization logic.
