### [WL-8520]

**Title:** Preserve queue worker handoff by separating readiness probe and assignment binding
**Source:** [thegent/src/thegent/queue/assignment.py:612]
**Acceptance checklist:**

- [ ] Separate readiness probe failures from assignment binding failures.
- [ ] Keep assignment fallback active when readiness probe is unstable.
- [ ] Add tests for readiness and binding branches.
      **Notes:** Improves worker startup stability under partial runtime readiness failures.

### [WL-8521]

**Title:** Preserve sync lock handling by separating lock token parse and lock renewal
**Source:** [thegent/src/thegent/sync/locks.py:412]
**Acceptance checklist:**

- [ ] Separate sync lock token parse failures from lock renewal failures.
- [ ] Preserve active work on lock renewal branch failures.
- [ ] Add tests for token parse and renewal failures.
      **Notes:** Prevents unnecessary sync stalls under token format drift.

### [WL-8522]

**Title:** Preserve artifact cleanup by separating artifact age scan and deletion scheduling
**Source:** [thegent/src/thegent/artifacts/cleanup.py:458]
**Acceptance checklist:**

- [ ] Separate age scan failures from deletion schedule failures.
- [ ] Keep cleanup schedule active with conservative age assumptions.
- [ ] Add tests for scan and schedule branch behavior.
      **Notes:** Improves cleanup safety under partial scanning failures.

### [WL-8523]

**Title:** Preserve webhook handling by separating payload decode and handler dispatch
**Source:** [thegent/src/thegent/webhooks/handler.py:334]
**Acceptance checklist:**

- [ ] Separate webhook payload decode failures from handler dispatch failures.
- [ ] Preserve dispatch fallback for decode failures.
- [ ] Add tests for decode and dispatch branches.
      **Notes:** Keeps integrations observable when payload schemas vary.

### [WL-8524]

**Title:** Preserve command execution telemetry by separating parse stage and execution trace
**Source:** [thegent/src/thegent/commands/telemetry.py:501]
**Acceptance checklist:**

- [ ] Separate command parse failures from execution trace emission failures.
- [ ] Preserve command execution when trace stage fails.
- [ ] Add tests for parse and trace emission branches.
      **Notes:** Helps diagnose execution issues without losing command-level visibility.

### [WL-8525]

**Title:** Preserve session heartbeat by separating heartbeat generator and transport send
**Source:** [thegent/src/thegent/sessions/heartbeat.py:289]
**Acceptance checklist:**

- [ ] Separate heartbeat payload generation failures from transport send failures.
- [ ] Preserve heartbeat state with send fallback.
- [ ] Add tests for generator and transport branches.
      **Notes:** Improves session stability under transport interruptions.

### [WL-8526]

**Title:** Preserve API error reporting by separating error classification and user message formatting
**Source:** [thegent/src/thegent/api/errors.py:377]
**Acceptance checklist:**

- [ ] Separate classification failures from user message formatting failures.
- [ ] Preserve safe error responses under classification branch failures.
- [ ] Add tests for classification and formatting branches.
      **Notes:** Reduces user-facing inconsistency during transient parser issues.

### [WL-8527]

**Title:** Preserve workflow queue by separating queue key expansion and dequeue selection
**Source:** [thegent/src/thegent/workflow/queue.py:451]
**Acceptance checklist:**

- [ ] Separate queue key expansion failures from dequeue selection failures.
- [ ] Preserve dequeue path for valid keys.
- [ ] Add tests for expansion and dequeue branches.
      **Notes:** Improves flow continuity when one queue key path is malformed.

### [WL-8528]

**Title:** Preserve policy enforcement by separating policy lookup and evaluator context
**Source:** [thegent/src/thegent/policies/enforce.py:512]
**Acceptance checklist:**

- [ ] Separate policy lookup failures from evaluator context failures.
- [ ] Preserve enforcement defaults when lookup is delayed.
- [ ] Add tests for lookup and evaluator branches.
      **Notes:** Helps keep guardrails active during policy data drift.

### [WL-8529]

**Title:** Preserve artifact archive by separating archive manifest and checksum persistence
**Source:** [thegent/src/thegent/artifacts/archive.py:601]
**Acceptance checklist:**

- [ ] Separate manifest generation failures from checksum persistence failures.
- [ ] Keep archive creation available with checksum fallback.
- [ ] Add tests for manifest and checksum branches.
      **Notes:** Reduces false archive corruption during checksum I/O faults.
