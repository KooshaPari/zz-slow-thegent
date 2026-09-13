### [WL-8430]

**Title:** Preserve shell completion behavior by separating completion cache hydration and renderer
**Source:** [thegent/src/thegent/shell_cli/completion.py:602]
**Acceptance checklist:**

- [ ] Separate completion cache hydration failures from renderer failures.
- [ ] Preserve fallback completions when cache cannot be hydrated.
- [ ] Add tests for hydration and renderer branch failures.
      **Notes:** Keeps shell UX functional on partial completion regressions.

### [WL-8431]

**Title:** Preserve integration sync by separating connector response parsing and state reconciliation
**Source:** [thegent/src/thegent/integrations/sync_runner.py:417]
**Acceptance checklist:**

- [ ] Distinguish connector response parsing failures from reconciliation failures.
- [ ] Preserve current state when reconciliation is temporarily unavailable.
- [ ] Add tests for each branch.
      **Notes:** Prevents sync collapse under one noisy integration response.

### [WL-8432]

**Title:** Preserve artifact lookup by separating index parse and object resolution
**Source:** [thegent/src/thegent/artifacts/lookup.py:357]
**Acceptance checklist:**

- [ ] Separate index parse failures from object resolution failures.
- [ ] Keep degraded artifact resolution mode when parse fails.
- [ ] Add tests for index parse and resolution branches.
      **Notes:** Reduces lookup failures from malformed index metadata.

### [WL-8433]

**Title:** Preserve prompt template handling by separating template load and variable injection
**Source:** [thegent/src/thegent/prompt/registry.py:289]
**Acceptance checklist:**

- [ ] Distinguish template load failures from variable injection failures.
- [ ] Preserve injection defaults on template load errors.
- [ ] Add tests for both failure branches.
      **Notes:** Improves prompt reliability in multi-tenant flows.

### [WL-8434]

**Title:** Preserve runtime config reload by separating file-system watch and parser update
**Source:** [thegent/src/thegent/config/reloader.py:448]
**Acceptance checklist:**

- [ ] Separate file watch event handling from parser update logic.
- [ ] Preserve existing config on parser failures.
- [ ] Add tests for watch-events and parser-fail branches.
      **Notes:** Helps avoid config thrash during rapid file changes.

### [WL-8435]

**Title:** Preserve telemetry batching by separating sample merge and send scheduling
**Source:** [thegent/src/thegent/telemetry/batcher.py:312]
**Acceptance checklist:**

- [ ] Separate telemetry sample merge failures from send schedule failures.
- [ ] Keep sample collection active when scheduling fails.
- [ ] Add tests for merge and scheduler branch failures.
      **Notes:** Keeps telemetry quality high under intermittent transport pressure.

### [WL-8436]

**Title:** Preserve CLI diagnostics by separating diagnostic command parsing and command execution
**Source:** [thegent/src/thegent/cli/diagnostics.py:274]
**Acceptance checklist:**

- [ ] Separate diagnostics parse failures from execution failures.
- [ ] Preserve command output for non-fatal execution.
- [ ] Add tests for parser and executor branches.
      **Notes:** Prevents diagnostics failures from becoming complete blind spots.

### [WL-8437]

**Title:** Preserve policy application by separating rule filter and enforcement action
**Source:** [thegent/src/thegent/policies/enforcer.py:519]
**Acceptance checklist:**

- [ ] Separate filter expression failures from enforcement action failures.
- [ ] Maintain enforcement fallback with filtered policy subset.
- [ ] Add tests for filter and enforcement branch errors.
      **Notes:** Improves policy system stability during expression rollouts.

### [WL-8438]

**Title:** Preserve graph sync by separating node diff computation and edge commit
**Source:** [thegent/src/thegent/sync/graph_sync.py:386]
**Acceptance checklist:**

- [ ] Separate node diff failures from edge commit failures.
- [ ] Preserve node state when edge commit encounters errors.
- [ ] Add tests for diff and edge commit branches.
      **Notes:** Keeps graph data from cascading into complete sync failure.

### [WL-8439]

**Title:** Preserve session audit by separating actor attribution and event emission
**Source:** [thegent/src/thegent/audit/session.py:437]
**Acceptance checklist:**

- [ ] Separate actor attribution failures from audit emission failures.
- [ ] Preserve event emission with best-effort attribution.
- [ ] Add tests for attribution and emission errors.
      **Notes:** Helps maintain audit continuity under identity metadata drift.
