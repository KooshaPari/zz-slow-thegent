### [WL-6990]

**Title:** Classify alias discovery fallbacks instead of swallowing unexpected lookup errors
**Source:** [thegent/src/thegent/execution.py:167]
**Acceptance checklist:**

- [ ] Replace broad fallback handling with typed branches for missing alias data and runtime failures.
- [ ] Preserve current user-facing behavior for expected no-alias cases.
- [ ] Add tests for successful lookup, missing alias, and unexpected resolver failure.
      **Notes:** Unclassified fallbacks can hide regressions in command discovery paths.

### [WL-6991]

**Title:** Surface message-loading failures as degraded state rather than silent empty results
**Source:** [thegent/src/thegent/execution.py:448]
**Acceptance checklist:**

- [ ] Replace catch-all empty-result fallback with structured IO and parse error handling.
- [ ] Keep valid empty-message semantics for legitimately empty stores.
- [ ] Add tests for normal loads, missing files, and malformed payloads.
      **Notes:** Returning empties for all failures obscures data-plane reliability.

### [WL-6992]

**Title:** Preserve per-run metadata parse errors during history hydration
**Source:** [thegent/src/thegent/execution.py:875]
**Acceptance checklist:**

- [ ] Replace blanket metadata parse suppression with bounded diagnostics.
- [ ] Continue hydrating valid records when individual rows are malformed.
- [ ] Add tests for mixed valid and invalid metadata entries.
      **Notes:** Silent per-row drops can misrepresent run-history completeness.

### [WL-6993]

**Title:** Differentiate event replay decode failures from legitimate no-event timelines
**Source:** [thegent/src/thegent/execution.py:938]
**Acceptance checklist:**

- [ ] Refactor replay loading to classify decode/shape failures separately from empty timelines.
- [ ] Preserve replay behavior for valid histories and true empty states.
- [ ] Add tests for valid event streams, malformed lines, and absent timelines.
      **Notes:** Conflating failure and empty history weakens incident reconstruction.

### [WL-6994]

**Title:** Add typed handling for command dispatch setup failures before execution start
**Source:** [thegent/src/thegent/execution.py:1076]
**Acceptance checklist:**

- [ ] Replace broad setup exception swallowing with explicit validation and dispatch-error branches.
- [ ] Keep current launch flow for successful setup paths.
- [ ] Add tests for valid setup, missing prerequisites, and dispatcher initialization errors.
      **Notes:** Silent setup failures cause launches to fail without actionable signals.

### [WL-6995]

**Title:** Preserve state-transition failure context during run lifecycle updates
**Source:** [thegent/src/thegent/execution.py:1262]
**Acceptance checklist:**

- [ ] Replace catch-all transition fallback with explicit state-validation and persistence error handling.
- [ ] Ensure successful transitions remain unchanged.
- [ ] Add tests for valid transitions, invalid state payloads, and storage write failures.
      **Notes:** Hidden transition errors can leave run state stale while reporting success.

### [WL-6996]

**Title:** Distinguish registry read failures from true missing-entry lookups
**Source:** [thegent/src/thegent/execution.py:1386]
**Acceptance checklist:**

- [ ] Replace blanket lookup failure fallback with typed file-read and decode branches.
- [ ] Preserve not-found behavior only when entries are genuinely absent.
- [ ] Add tests for present entries, absent entries, and unreadable registry files.
      **Notes:** Treating all failures as missing entries masks storage integrity issues.

### [WL-6997]

**Title:** Prevent untyped scan-loop exceptions from suppressing follow-up run reconciliation
**Source:** [thegent/src/thegent/execution.py:1398]
**Acceptance checklist:**

- [ ] Replace broad scan-loop exception suppression with classified recoverable/fatal paths.
- [ ] Continue reconciliation for unaffected items after recoverable failures.
- [ ] Add tests for partial-scan failures and complete successful reconciliation.
      **Notes:** Suppressed loop errors can leave stale run metadata in downstream views.

### [WL-6998]

**Title:** Record parser failures in status aggregation instead of collapsing to generic defaults
**Source:** [thegent/src/thegent/execution.py:1461]
**Acceptance checklist:**

- [ ] Refactor aggregation error handling to separate parse, shape, and transport failures.
- [ ] Preserve existing aggregate output for valid inputs.
- [ ] Add tests for valid aggregates, malformed records, and mixed-quality inputs.
      **Notes:** Generic defaults make status quality issues hard to diagnose.

### [WL-6999]

**Title:** Preserve pending-message poll failure classes instead of returning silent empties
**Source:** [thegent/src/thegent/execution.py:1806]
**Acceptance checklist:**

- [ ] Replace broad exception-to-empty fallback with explicit degraded-result signaling.
- [ ] Emit bounded diagnostics for metadata lookup and registry parsing failures.
- [ ] Add tests for successful polling, missing metadata, and malformed registry lines.
      **Notes:** Silent empty responses can hide message-delivery control-flow regressions.
