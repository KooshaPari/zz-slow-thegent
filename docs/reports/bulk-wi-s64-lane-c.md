### [WL-8740]

**Title:** Preserve queue backoff by separating backoff parse and backoff scheduling
**Source:** [thegent/src/thegent/queue/backoff_controller.py:412]
**Acceptance checklist:**

- [ ] Separate backoff config parse failures from backoff scheduling failures.
- [ ] Preserve scheduling with default backoff behavior.
- [ ] Add tests for config and scheduling branches.
      **Notes:** Improves queue throughput under intermittent backoff misconfigurations.

### [WL-8741]

**Title:** Preserve artifact cleanup by separating cleanup policy parse and artifact deletion
**Source:** [thegent/src/thegent/artifacts/cleanup_policy.py:331]
**Acceptance checklist:**

- [ ] Separate cleanup policy parse failures from artifact deletion failures.
- [ ] Preserve deletion safety with fallback policy.
- [ ] Add tests for parse and deletion branch failures.
      **Notes:** Avoids accidental deletions during policy parse regressions.

### [WL-8742]

**Title:** Preserve sync replay by separating replay checkpoint parse and replay worker dispatch
**Source:** [thegent/src/thegent/sync/replay_worker.py:478]
**Acceptance checklist:**

- [ ] Separate replay checkpoint parse failures from worker dispatch failures.
- [ ] Preserve worker dispatch with checkpoint fallback.
- [ ] Add tests for checkpoint parse and dispatch branches.
      **Notes:** Improves sync recovery when checkpoint format drifts.

### [WL-8743]

**Title:** Preserve policy audit trail by separating policy event parse and audit emission
**Source:** [thegent/src/thegent/policies/audit_trail.py:589]
**Acceptance checklist:**

- [ ] Separate policy event parse failures from audit emission failures.
- [ ] Preserve emission with raw event fallback.
- [ ] Add tests for parse and emission branch handling.
      **Notes:** Maintains policy auditing under event format churn.

### [WL-8744]

**Title:** Preserve command queue diagnostics by separating diagnostic parse and diagnostic sink
**Source:** [thegent/src/thegent/commands/queue_diagnostics.py:357]
**Acceptance checklist:**

- [ ] Separate diagnostic parse failures from diagnostic sink failures.
- [ ] Preserve diagnostics with sink fallback behavior.
- [ ] Add tests for parse and sink branches.
      **Notes:** Keeps queue diagnostics available under parser instability.

### [WL-8745]

**Title:** Preserve artifact retrieval by separating retrieval manifest parse and retrieval execution
**Source:** [thegent/src/thegent/artifacts/retrieval_worker.py:512]
**Acceptance checklist:**

- [ ] Separate retrieval manifest parse failures from retrieval execution failures.
- [ ] Preserve retrieval execution with manifest fallback.
- [ ] Add tests for manifest parse and execution branches.
      **Notes:** Improves retrieval behavior in mixed-manifest environments.

### [WL-8746]

**Title:** Preserve API token lifecycle by separating token metadata parse and token rotation
**Source:** [thegent/src/thegent/auth/token_lifecycle.py:333]
**Acceptance checklist:**

- [ ] Separate token metadata parse failures from token rotation failures.
- [ ] Preserve rotation behavior on metadata parse fallback.
- [ ] Add tests for metadata parse and rotation failures.
      **Notes:** Helps prevent token service stalls in evolving metadata formats.

### [WL-8747]

**Title:** Preserve alerting routes by separating alert route parse and alert dispatch
**Source:** [thegent/src/thegent/alerts/router.py:589]
**Acceptance checklist:**

- [ ] Separate alert route parse failures from alert dispatch failures.
- [ ] Preserve dispatch with fallback routes.
- [ ] Add tests for route parse and dispatch branches.
      **Notes:** Keeps critical alerts operational during route definition churn.

### [WL-8748]

**Title:** Preserve workflow status by separating status payload parse and status persistence
**Source:** [thegent/src/thegent/workflow/status_persistence.py:441]
**Acceptance checklist:**

- [ ] Separate workflow status parse failures from persistence failures.
- [ ] Preserve status updates with persistence fallback.
- [ ] Add tests for status parse and persistence branches.
      **Notes:** Maintains status continuity during payload format changes.

### [WL-8749]

**Title:** Preserve integration health by separating health rule parse and rule execution
**Source:** [thegent/src/thegent/integrations/health_rules.py:523]
**Acceptance checklist:**

- [ ] Separate integration health rule parse failures from rule execution failures.
- [ ] Preserve health checks with execution fallback rules.
- [ ] Add tests for parse and execution branches.
      **Notes:** Improves integration reliability under health rule drift.
