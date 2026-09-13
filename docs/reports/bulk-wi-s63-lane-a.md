### [WL-8670]

**Title:** Preserve audit streaming by separating event capture and audit output stream
**Source:** [thegent/src/thegent/audit/streamer.py:512]
**Acceptance checklist:**

- [ ] Separate audit event capture failures from output stream failures.
- [ ] Preserve stream continuity with capture fallback.
- [ ] Add tests for capture and stream branches.
      **Notes:** Improves audit reliability during stream sink interruptions.

### [WL-8671]

**Title:** Preserve command shortcut expansion by separating shortcut parse and expansion executor
**Source:** [thegent/src/thegent/commands/shortcuts.py:423]
**Acceptance checklist:**

- [ ] Separate shortcut parse failures from expansion executor failures.
- [ ] Preserve raw command execution when expansion fails.
- [ ] Add tests for parse and executor branches.
      **Notes:** Keeps CLI ergonomics intact during shorthand format changes.

### [WL-8672]

**Title:** Preserve workflow reconciliation by separating reconcile intent parse and reconcile action
**Source:** [thegent/src/thegent/workflow/reconcile.py:357]
**Acceptance checklist:**

- [ ] Separate reconcile intent parse failures from reconcile action failures.
- [ ] Preserve action attempts with intent fallback.
- [ ] Add tests for intent and action branches.
      **Notes:** Improves workflow consistency under intent payload regression.

### [WL-8673]

**Title:** Preserve queue latency monitoring by separating latency sample parse and monitoring emit
**Source:** [thegent/src/thegent/queue/latency.py:458]
**Acceptance checklist:**

- [ ] Separate latency sample parsing failures from monitoring emit failures.
- [ ] Preserve monitoring emission with sample fallback behavior.
- [ ] Add tests for sample parse and monitor emit branches.
      **Notes:** Maintains latency insight without complete queue monitoring outages.

### [WL-8674]

**Title:** Preserve config profile sync by separating profile descriptor parse and profile writeback
**Source:** [thegent/src/thegent/config/profile_sync.py:589]
**Acceptance checklist:**

- [ ] Separate profile descriptor parse failures from profile writeback failures.
- [ ] Preserve profile state with writeback fallback.
- [ ] Add tests for parse and writeback branches.
      **Notes:** Keeps profile synchronization usable despite partial descriptor issues.

### [WL-8675]

**Title:** Preserve API route registration by separating route manifest parse and registration application
**Source:** [thegent/src/thegent/api/route_registry.py:422]
**Acceptance checklist:**

- [ ] Separate route manifest parse failures from registration application failures.
- [ ] Preserve registrations using manifest fallback entries.
- [ ] Add tests for parse and registration branches.
      **Notes:** Prevents routing gaps when one manifest file is malformed.

### [WL-8676]

**Title:** Preserve artifact deletion safety by separating deletion criteria parse and deletion execution
**Source:** [thegent/src/thegent/artifacts/deletion.py:401]
**Acceptance checklist:**

- [ ] Separate deletion criteria parse failures from execution failures.
- [ ] Preserve execution with conservative default criteria.
- [ ] Add tests for criteria parse and execution branches.
      **Notes:** Improves safety under imperfect delete criteria.

### [WL-8677]

**Title:** Preserve command output persistence by separating output chunk parse and persistence batching
**Source:** [thegent/src/thegent/commands/output_persist.py:512]
**Acceptance checklist:**

- [ ] Separate command output chunk parse failures from persistence batching failures.
- [ ] Preserve output persistence with chunk fallback.
- [ ] Add tests for parse and batching branches.
      **Notes:** Helps avoid data loss for large command outputs.

### [WL-8678]

**Title:** Preserve session event logging by separating event parse and log record format
**Source:** [thegent/src/thegent/session/event_log.py:333]
**Acceptance checklist:**

- [ ] Separate session event parse failures from log record formatting failures.
- [ ] Preserve event logging with raw record fallback.
- [ ] Add tests for parse and format branch behavior.
      **Notes:** Improves log integrity under evolving event payloads.

### [WL-8679]

**Title:** Preserve artifact import by separating import manifest parsing and import execution planning
**Source:** [thegent/src/thegent/artifacts/import_planner.py:579]
**Acceptance checklist:**

- [ ] Separate import manifest parse failures from execution planning failures.
- [ ] Preserve import planning with manifest fallback.
- [ ] Add tests for parse and planning branch failures.
      **Notes:** Keeps imports operable in mixed manifest environments.
