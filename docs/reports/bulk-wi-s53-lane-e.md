### [WL-8210]

**Title:** Preserve CLI command dispatch while separating parse and runtime execution failures
**Source:** [thegent/src/thegent/shell_cli.py:682]
**Acceptance checklist:**

- [ ] Add explicit branches for parser failures vs runtime dispatch errors.
- [ ] Preserve dispatch return contracts and exit codes.
- [ ] Add tests for parse error and runtime execution error paths.
      **Notes:** Improves command pipeline observability.

### [WL-8211]

**Title:** Preserve artifact retention reporting while separating evaluation and deletion failures
**Source:** [thegent/src/thegent/artifacts/retention.py:279]
**Acceptance checklist:**

- [ ] Split retention evaluation failures from deletion routine failures.
- [ ] Keep reporting output for successful deletions unaffected.
- [ ] Add tests for evaluation exceptions and delete I/O errors.
      **Notes:** Helps maintain predictable retention behavior.

### [WL-8212]

**Title:** Preserve prompt rendering pipeline by separating context assembly failures
**Source:** [thegent/src/thegent/prompts.py:248]
**Acceptance checklist:**

- [ ] Distinguish context assembly failures from prompt format failures.
- [ ] Preserve existing rendering fallback for non-critical context assembly errors.
- [ ] Add tests for context assembly and prompt formatting failures.
      **Notes:** Helps reduce prompt generation noise in edge cases.

### [WL-8213]

**Title:** Preserve health endpoint request throttling while separating rate-limit and validation errors
**Source:** [thegent/src/thegent/health/endpoint.py:234]
**Acceptance checklist:**

- [ ] Split validation failures from backend rate-limit enforcement.
- [ ] Preserve status/headers contract for both outcomes.
- [ ] Add tests for validation failure and rate-limit responses.
      **Notes:** Clearer operational signals under load.

### [WL-8214]

**Title:** Preserve settings migration behavior while separating migration parse and patch failures
**Source:** [thegent/src/thegent/config/settings.py:312]
**Acceptance checklist:**

- [ ] Handle migration file parse errors separately from patch application failures.
- [ ] Keep migration rollback behavior stable on parse failures.
- [ ] Add tests for invalid migration files and patch conflicts.
      **Notes:** Reduces accidental configuration breakage.

### [WL-8215]

**Title:** Preserve UI panel render while separating payload schema and render engine errors
**Source:** [thegent/src/thegent/ui/compositor_manager.py:498]
**Acceptance checklist:**

- [ ] Distinguish schema validation errors from render engine runtime errors.
- [ ] Keep fallback rendering in both scenarios.
- [ ] Add tests for schema and render failures.
      **Notes:** Improves resilience during UI payload changes.

### [WL-8216]

**Title:** Preserve queue scaler behavior while separating metric fetch and decision execution
**Source:** [thegent/src/thegent/queue/scaler.py:186]
**Acceptance checklist:**

- [ ] Separate metric fetch failures from scaling decision errors.
- [ ] Preserve last-known-good scaling on metric fetch failure.
- [ ] Add tests for fetch failures and decision exceptions.
      **Notes:** Improves queue responsiveness under partial observability failures.

### [WL-8217]

**Title:** Preserve borrow retries while separating request template and request transport issues
**Source:** [thegent/src/thegent/tools/borrow.py:552]
**Acceptance checklist:**

- [ ] Split invalid request template failures from transport timeout issues.
- [ ] Preserve retry and backoff behavior on transport failures.
- [ ] Add tests for invalid templates and timeout exceptions.
      **Notes:** Prevents unnecessary retries from deterministic template errors.

### [WL-8218]

**Title:** Preserve scheduler state while separating persistence I/O from reconciliation logic
**Source:** [thegent/src/thegent/orchestration/scheduler.py:338]
**Acceptance checklist:**

- [ ] Distinguish persistence I/O failures from reconciliation algorithm errors.
- [ ] Keep reconciliation output stable on persistence failures.
- [ ] Add tests for both error paths.
      **Notes:** Improves recovery when storage is unstable.

### [WL-8219]

**Title:** Preserve artifact collector when stream processing fails versus file read failures
**Source:** [thegent/src/thegent/artifacts/collector.py:268]
**Acceptance checklist:**

- [ ] Separate stream transformation exceptions from file read failures.
- [ ] Keep collector scanning robust with partial failures.
- [ ] Add tests for stream errors and file-read errors.
      **Notes:** Prevents one bad stream from dropping entire collection.
