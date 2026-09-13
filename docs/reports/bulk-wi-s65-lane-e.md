### [WL-8810]

**Title:** Preserve artifact retention policies by separating policy parse and retention enforcement
**Source:** [thegent/src/thegent/artifacts/retention_enforcer.py:458]
**Acceptance checklist:**

- [ ] Separate retention policy parse failures from enforcement failures.
- [ ] Preserve enforcement with fallback retention policy.
- [ ] Add tests for parse and enforcement branches.
      **Notes:** Improves retention reliability under policy schema evolution.

### [WL-8811]

**Title:** Preserve command route registration by separating route parse and route registration
**Source:** [thegent/src/thegent/commands/route_registration.py:531]
**Acceptance checklist:**

- [ ] Separate command route parse failures from route registration failures.
- [ ] Preserve route registration with fallback routes.
- [ ] Add tests for parse and registration branches.
      **Notes:** Prevents command routing regressions from one malformed route.

### [WL-8812]

**Title:** Preserve session state sync by separating state delta parse and state sync apply
**Source:** [thegent/src/thegent/session/state_sync.py:333]
**Acceptance checklist:**

- [ ] Separate session state delta parse failures from sync apply failures.
- [ ] Preserve state apply using fallback deltas.
- [ ] Add tests for parse and apply branches.
      **Notes:** Keeps state sync reliable under delta schema changes.

### [WL-8813]

**Title:** Preserve event index maintenance by separating index event parse and index maintenance scheduler
**Source:** [thegent/src/thegent/events/index_maintenance.py:589]
**Acceptance checklist:**

- [ ] Separate index event parse failures from maintenance scheduler failures.
- [ ] Preserve maintenance scheduling with parsed fallback.
- [ ] Add tests for parse and scheduler branches.
      **Notes:** Improves indexing health under event format inconsistencies.

### [WL-8814]

**Title:** Preserve sync backlog by separating backlog parse and backlog drain
**Source:** [thegent/src/thegent/sync/backlog.py:501]
**Acceptance checklist:**

- [ ] Separate sync backlog parse failures from backlog drain failures.
- [ ] Preserve backlog drain with parse fallback.
- [ ] Add tests for parse and drain branches.
      **Notes:** Keeps backlog movement stable under backlog payload drift.

### [WL-8815]

**Title:** Preserve artifact search reliability by separating query parse and result formatter
**Source:** [thegent/src/thegent/artifacts/search_formatter.py:377]
**Acceptance checklist:**

- [ ] Separate artifact search query parse failures from result formatter failures.
- [ ] Preserve results with formatter fallback.
- [ ] Add tests for query parse and formatter branches.
      **Notes:** Improves search usability during formatter/parser mismatches.

### [WL-8816]

**Title:** Preserve policy evaluation logs by separating evaluation event parse and log persistence
**Source:** [thegent/src/thegent/policies/eval_log.py:423]
**Acceptance checklist:**

- [ ] Separate policy evaluation event parse failures from log persistence failures.
- [ ] Preserve policy logs with fallback event payloads.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Maintains audit value during evaluation event evolution.

### [WL-8817]

**Title:** Preserve command pipeline by separating command metadata parse and command scheduling
**Source:** [thegent/src/thegent/commands/pipeline.py:531]
**Acceptance checklist:**

- [ ] Separate command metadata parse failures from scheduling failures.
- [ ] Preserve scheduling defaults with metadata fallback.
- [ ] Add tests for metadata parse and scheduling branches.
      **Notes:** Improves command throughput during metadata drift.

### [WL-8818]

**Title:** Preserve queue fairness metrics by separating fairness sample parse and metrics publish
**Source:** [thegent/src/thegent/queue/fairness_metrics.py:333]
**Acceptance checklist:**

- [ ] Separate fairness sample parse failures from publish failures.
- [ ] Preserve fairness metrics with fallback publish path.
- [ ] Add tests for sample parse and publish branches.
      **Notes:** Keeps fairness insights usable despite sample anomalies.

### [WL-8819]

**Title:** Preserve artifact migration status by separating migration status parse and status persist
**Source:** [thegent/src/thegent/artifacts/migration_status.py:589]
**Acceptance checklist:**

- [ ] Separate migration status parse failures from status persistence failures.
- [ ] Preserve status persistence with fallback states.
- [ ] Add tests for status parse and persistence branches.
      **Notes:** Helps operations track migrations during status payload variations.
