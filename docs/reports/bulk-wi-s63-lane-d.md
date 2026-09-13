### [WL-8700]

**Title:** Preserve auth token exchange by separating token request parse and exchange transport
**Source:** [thegent/src/thegent/auth/token_exchange.py:441]
**Acceptance checklist:**

- [ ] Separate token request parse failures from exchange transport failures.
- [ ] Preserve exchange fallback on transport issues.
- [ ] Add tests for parse and exchange branch failures.
      **Notes:** Keeps auth exchange stable with transient transport issues.

### [WL-8701]

**Title:** Preserve sync recovery by separating recovery marker parse and recovery action
**Source:** [thegent/src/thegent/sync/recovery.py:512]
**Acceptance checklist:**

- [ ] Separate recovery marker parse failures from recovery action failures.
- [ ] Preserve recovery action with marker fallback.
- [ ] Add tests for marker and action branches.
      **Notes:** Improves recovery in mixed marker/version environments.

### [WL-8702]

**Title:** Preserve command telemetry by separating command meta parse and telemetry flush
**Source:** [thegent/src/thegent/commands/telemetry.py:333]
**Acceptance checklist:**

- [ ] Separate command metadata parse failures from telemetry flush failures.
- [ ] Preserve command telemetry flush with metadata fallback.
- [ ] Add tests for metadata and flush branches.
      **Notes:** Helps command teams maintain visibility during parser regressions.

### [WL-8703]

**Title:** Preserve artifact search by separating search query parse and result ranking
**Source:** [thegent/src/thegent/artifacts/search_query.py:589]
**Acceptance checklist:**

- [ ] Separate search query parse failures from result ranking failures.
- [ ] Preserve baseline ranking on query parse failures.
- [ ] Add tests for query parse and ranking branches.
      **Notes:** Maintains search usability when query grammar changes.

### [WL-8704]

**Title:** Preserve queue dispatch by separating dispatch policy parse and dispatch execution
**Source:** [thegent/src/thegent/queue/dispatch.py:378]
**Acceptance checklist:**

- [ ] Separate dispatch policy parse failures from execution failures.
- [ ] Preserve dispatch with fallback policies.
- [ ] Add tests for parse and execution branches.
      **Notes:** Reduces queue jitter under policy rollouts.

### [WL-8705]

**Title:** Preserve session audit trail by separating audit item parse and audit sink routing
**Source:** [thegent/src/thegent/session/audit_sink.py:501]
**Acceptance checklist:**

- [ ] Separate audit item parse failures from audit sink routing failures.
- [ ] Preserve audit routing with parse fallback.
- [ ] Add tests for parse and sink routing branches.
      **Notes:** Improves audit reliability under schema drift.

### [WL-8706]

**Title:** Preserve integration event batching by separating event parse and batch scheduling
**Source:** [thegent/src/thegent/integrations/event_batcher.py:412]
**Acceptance checklist:**

- [ ] Separate integration event parse failures from batch scheduling failures.
- [ ] Preserve scheduling with minimal parse fallback.
- [ ] Add tests for parse and scheduling branches.
      **Notes:** Maintains integration throughput during event shape changes.

### [WL-8707]

**Title:** Preserve workflow DAG validation by separating DAG parse and DAG execution checks
**Source:** [thegent/src/thegent/workflow/dag_validator.py:531]
**Acceptance checklist:**

- [ ] Separate DAG parse failures from execution check failures.
- [ ] Preserve execution checks with fallback DAG structure.
- [ ] Add tests for parse and execution-check branches.
      **Notes:** Prevents DAG failures from cascading into pipeline stalling.

### [WL-8708]

**Title:** Preserve config fallback by separating fallback profile parse and fallback profile apply
**Source:** [thegent/src/thegent/config/fallback_profile.py:333]
**Acceptance checklist:**

- [ ] Separate fallback profile parse failures from apply failures.
- [ ] Preserve apply path with default fallback profile.
- [ ] Add tests for parse and apply branches.
      **Notes:** Improves resilience during profile format transitions.

### [WL-8709]

**Title:** Preserve artifact archival by separating archive policy parse and archive executor
**Source:** [thegent/src/thegent/artifacts/archive_executor.py:477]
**Acceptance checklist:**

- [ ] Separate archive policy parse failures from archive executor failures.
- [ ] Preserve archive execution with default policy fallback.
- [ ] Add tests for parse and executor branches.
      **Notes:** Prevents archive pipeline regressions from one policy parse issue.
