### [WL-8440]

**Title:** Preserve dataset validation by separating schema validation and constraint checks
**Source:** [thegent/src/thegent/datasets/validator.py:401]
**Acceptance checklist:**

- [ ] Separate schema validation failures from constraint validation failures.
- [ ] Preserve best-effort ingestion for constraint recoverable cases.
- [ ] Add tests for schema and constraint branches.
      **Notes:** Improves dataset reliability when schema checks are strict.

### [WL-8441]

**Title:** Preserve API contract checks by separating OpenAPI load and client-side validation
**Source:** [thegent/src/thegent/api/contract_checker.py:356]
**Acceptance checklist:**

- [ ] Separate contract spec load failures from runtime validation failures.
- [ ] Keep runtime checks running with cached specs on load failures.
- [ ] Add tests for spec load and runtime validation branches.
      **Notes:** Avoids contract check outages during spec sync latency.

### [WL-8442]

**Title:** Preserve queue worker startup by separating environment detection and worker bootstrap
**Source:** [thegent/src/thegent/queue/worker.py:512]
**Acceptance checklist:**

- [ ] Separate runtime env detection failures from worker bootstrap failures.
- [ ] Keep worker bootstrap resilient with defaults when env detection fails.
- [ ] Add tests for environment and bootstrap branches.
      **Notes:** Improves startup behavior in mixed environments.

### [WL-8443]

**Title:** Preserve command line output by separating pretty printer and pager selection
**Source:** [thegent/src/thegent/cli/output.py:422]
**Acceptance checklist:**

- [ ] Split printer output failures from pager selection failures.
- [ ] Preserve command output on pager fallback.
- [ ] Add tests for printer and pager error cases.
      **Notes:** Prevents output blackouts under pager configuration drift.

### [WL-8444]

**Title:** Preserve API retry telemetry by separating retry metrics parsing and export
**Source:** [thegent/src/thegent/retry/telemetry.py:273]
**Acceptance checklist:**

- [ ] Separate metrics parse failures from export upload failures.
- [ ] Preserve retry metadata even if export path fails.
- [ ] Add tests for parse and export branches.
      **Notes:** Helps correlate retries when export channels degrade.

### [WL-8445]

**Title:** Preserve plugin CLI registration by separating manifest parse and command binding
**Source:** [thegent/src/thegent/ui/cli_plugin.py:333]
**Acceptance checklist:**

- [ ] Separate manifest parse failures from command binding failures.
- [ ] Keep existing command bindings available when bind phase fails.
- [ ] Add tests for manifest and binding branches.
      **Notes:** Maintains plugin usability with partial registration issues.

### [WL-8446]

**Title:** Preserve websocket reconnect logic by separating backoff calc and reconnect attempt
**Source:** [thegent/src/thegent/clients/ws_reconnect.py:391]
**Acceptance checklist:**

- [ ] Separate backoff calculation failures from reconnect attempt failures.
- [ ] Preserve stable reconnect schedule on calc errors.
- [ ] Add tests for backoff and reconnect branches.
      **Notes:** Avoids reconnection storms during timing calculation regressions.

### [WL-8447]

**Title:** Preserve task planner by separating dependency extraction and schedule synthesis
**Source:** [thegent/src/thegent/planning/task_planner.py:447]
**Acceptance checklist:**

- [ ] Separate dependency extraction failures from schedule synthesis failures.
- [ ] Keep schedule synthesis robust with partial dependency info.
- [ ] Add tests for extraction and schedule synthesis paths.
      **Notes:** Keeps planning continuity under partial task graph degradation.

### [WL-8448]

**Title:** Preserve artifact signing by separating key lookup and signing service call
**Source:** [thegent/src/thegent/security/signer.py:468]
**Acceptance checklist:**

- [ ] Split signing key lookup failures from signing service request failures.
- [ ] Keep unsigned fallback artifact path available with explicit warning.
- [ ] Add tests for lookup and signing service failures.
      **Notes:** Improves reliability when signing dependencies are unstable.

### [WL-8449]

**Title:** Preserve event replay ordering by separating cursor reconciliation and event application
**Source:** [thegent/src/thegent/events/replay_order.py:523]
**Acceptance checklist:**

- [ ] Separate cursor reconciliation failures from event apply failures.
- [ ] Preserve replay ordering state on apply failures.
- [ ] Add tests for cursor versus apply branch handling.
      **Notes:** Helps maintain sequence integrity during replay failures.
