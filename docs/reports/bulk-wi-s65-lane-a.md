### [WL-8770]

**Title:** Preserve artifact sync by separating sync source parse and sync dispatch
**Source:** [thegent/src/thegent/artifacts/sync_dispatch.py:501]
**Acceptance checklist:**

- [ ] Separate sync source parse failures from dispatch failures.
- [ ] Preserve sync dispatch with fallback source.
- [ ] Add tests for source parse and dispatch branch failures.
      **Notes:** Improves sync throughput when one source format drifts.

### [WL-8771]

**Title:** Preserve command lifecycle by separating lifecycle parse and lifecycle execution
**Source:** [thegent/src/thegent/commands/lifecycle.py:331]
**Acceptance checklist:**

- [ ] Separate command lifecycle parse failures from execution failures.
- [ ] Preserve lifecycle execution with parse fallback.
- [ ] Add tests for lifecycle parse and execution branches.
      **Notes:** Prevents command lifecycle breakage from parser-only issues.

### [WL-8772]

**Title:** Preserve queue recovery by separating recovery event parse and recovery apply
**Source:** [thegent/src/thegent/queue/recovery.py:523]
**Acceptance checklist:**

- [ ] Separate recovery event parse failures from recovery apply failures.
- [ ] Preserve recovery apply with fallback events.
- [ ] Add tests for parse and apply branches.
      **Notes:** Improves queue recovery reliability under partial recover data.

### [WL-8773]

**Title:** Preserve sync endpoint auth by separating auth token parse and auth middleware binding
**Source:** [thegent/src/thegent/sync/auth_middleware.py:377]
**Acceptance checklist:**

- [ ] Separate auth token parse failures from middleware binding failures.
- [ ] Preserve middleware binding with token parse fallback.
- [ ] Add tests for token parse and binding branches.
      **Notes:** Maintains sync endpoint operation during token payload fluctuations.

### [WL-8774]

**Title:** Preserve artifact hash scheduling by separating hash policy parse and hash job scheduling
**Source:** [thegent/src/thegent/artifacts/hash_scheduler.py:531]
**Acceptance checklist:**

- [ ] Separate hash policy parse failures from hash scheduling failures.
- [ ] Preserve hash scheduling defaults under parse failures.
- [ ] Add tests for hash policy parse and scheduling branches.
      **Notes:** Improves hash job reliability under policy format changes.

### [WL-8775]

**Title:** Preserve telemetry capture by separating capture config parse and capture engine startup
**Source:** [thegent/src/thegent/telemetry/capture.py:333]
**Acceptance checklist:**

- [ ] Separate telemetry capture config parse failures from engine startup failures.
- [ ] Preserve engine startup with fallback capture config.
- [ ] Add tests for config parse and startup branches.
      **Notes:** Keeps telemetry data available during capture config churn.

### [WL-8776]

**Title:** Preserve policy result routing by separating result parse and result dispatch
**Source:** [thegent/src/thegent/policies/result_router.py:412]
**Acceptance checklist:**

- [ ] Separate policy result parse failures from result dispatch failures.
- [ ] Preserve dispatch with result fallback handling.
- [ ] Add tests for parse and dispatch branch behavior.
      **Notes:** Improves policy feedback loops across output format changes.

### [WL-8777]

**Title:** Preserve artifact upload retries by separating retry config parse and retry engine
**Source:** [thegent/src/thegent/artifacts/upload_retry.py:589]
**Acceptance checklist:**

- [ ] Separate retry configuration parse failures from retry engine failures.
- [ ] Preserve retry engine with fallback configuration.
- [ ] Add tests for parse and engine branch failures.
      **Notes:** Keeps upload retry behavior resilient under config drift.

### [WL-8778]

**Title:** Preserve command queue integrity by separating queue input parse and queue transaction commit
**Source:** [thegent/src/thegent/commands/queue_input.py:478]
**Acceptance checklist:**

- [ ] Separate command queue input parse failures from transaction commit failures.
- [ ] Preserve queue transaction state on input parse failures.
- [ ] Add tests for parse and transaction branches.
      **Notes:** Reduces queue corruption risk from malformed command inputs.

### [WL-8779]

**Title:** Preserve session event tracing by separating trace event parse and trace sink write
**Source:** [thegent/src/thegent/session/trace.py:412]
**Acceptance checklist:**

- [ ] Separate trace event parse failures from sink write failures.
- [ ] Preserve tracing with raw event fallback.
- [ ] Add tests for trace parse and sink write branches.
      **Notes:** Maintains traceability when event format varies.
