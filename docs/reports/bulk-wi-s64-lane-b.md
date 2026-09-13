### [WL-8730]

**Title:** Preserve API request assembly by separating request schema parse and request assembly
**Source:** [thegent/src/thegent/api/request_builder.py:501]
**Acceptance checklist:**

- [ ] Separate API request schema parse failures from request assembly failures.
- [ ] Preserve request assembly with permissive schema fallback.
- [ ] Add tests for schema parse and assembly branches.
      **Notes:** Improves API compatibility during schema evolution.

### [WL-8731]

**Title:** Preserve artifact retention by separating retention window parse and retention executor
**Source:** [thegent/src/thegent/artifacts/retention_window.py:411]
**Acceptance checklist:**

- [ ] Separate retention window parse failures from retention executor failures.
- [ ] Preserve retention scheduling with fallback windows.
- [ ] Add tests for parse and execution branches.
      **Notes:** Prevents retention behavior regressions from one malformed window.

### [WL-8732]

**Title:** Preserve task queue observability by separating task sample parse and sample aggregation
**Source:** [thegent/src/thegent/tasks/obsv.py:589]
**Acceptance checklist:**

- [ ] Separate task sample parse failures from sample aggregation failures.
- [ ] Preserve aggregation with raw samples when parse fails.
- [ ] Add tests for parse and aggregation branches.
      **Notes:** Maintains task observability while isolating parsing faults.

### [WL-8733]

**Title:** Preserve sync endpoint discovery by separating endpoint list parse and endpoint auth binding
**Source:** [thegent/src/thegent/sync/endpoint_discovery.py:423]
**Acceptance checklist:**

- [ ] Separate endpoint list parse failures from auth binding failures.
- [ ] Preserve auth binding using default endpoint fallbacks.
- [ ] Add tests for endpoint parse and auth binding branches.
      **Notes:** Improves connectivity under endpoint metadata drift.

### [WL-8734]

**Title:** Preserve queue replay by separating replay cursor decode and replay request dispatch
**Source:** [thegent/src/thegent/queue/replay.py:333]
**Acceptance checklist:**

- [ ] Separate replay cursor decode failures from replay request dispatch failures.
- [ ] Preserve dispatch when cursor decode fails.
- [ ] Add tests for decode and dispatch branch behavior.
      **Notes:** Helps recover replay state under partial cursor corruptions.

### [WL-8735]

**Title:** Preserve artifact sync by separating manifest extraction and sync submission
**Source:** [thegent/src/thegent/artifacts/syncer.py:501]
**Acceptance checklist:**

- [ ] Separate manifest extraction failures from sync submission failures.
- [ ] Preserve sync submission with manifest fallback.
- [ ] Add tests for extraction and sync submission branches.
      **Notes:** Reduces sync failures from malformed manifest sections.

### [WL-8736]

**Title:** Preserve command execution reporting by separating command outcome parse and reporting sink
**Source:** [thegent/src/thegent/commands/execution_report.py:523]
**Acceptance checklist:**

- [ ] Separate command outcome parse failures from reporting sink failures.
- [ ] Preserve reporting with default outcome payload.
- [ ] Add tests for parse and sink branch failures.
      **Notes:** Keeps execution transparency with consistent reporting.

### [WL-8737]

**Title:** Preserve health polling by separating poll config parse and poll executor
**Source:** [thegent/src/thegent/health/poller_core.py:477]
**Acceptance checklist:**

- [ ] Separate poll config parse failures from poll executor failures.
- [ ] Preserve executor with fallback poll config.
- [ ] Add tests for config parse and executor branches.
      **Notes:** Improves health monitoring continuity in config churn.

### [WL-8738]

**Title:** Preserve artifact access logs by separating log schema parse and log persistence
**Source:** [thegent/src/thegent/artifacts/access_log.py:333]
**Acceptance checklist:**

- [ ] Separate artifact access log schema parse failures from persistence failures.
- [ ] Preserve access logs with schema fallback.
- [ ] Add tests for schema parse and persistence branches.
      **Notes:** Helps auditability when log schemas are adjusted.

### [WL-8739]

**Title:** Preserve CLI alias resolution by separating alias parse and alias apply
**Source:** [thegent/src/thegent/cli/alias_engine.py:589]
**Acceptance checklist:**

- [ ] Separate alias parse failures from alias apply failures.
- [ ] Preserve raw command fallback when alias parse fails.
- [ ] Add tests for parse and apply branches.
      **Notes:** Keeps CLI convenience features available despite alias schema shifts.
