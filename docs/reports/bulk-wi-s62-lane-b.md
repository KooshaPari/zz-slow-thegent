### [WL-8630]

**Title:** Preserve event stream integrity by separating stream parse and stream state advance
**Source:** [thegent/src/thegent/events/stream.py:447]
**Acceptance checklist:**

- [ ] Separate event stream parse failures from stream state advancement.
- [ ] Preserve state advancement behavior with parse fallback.
- [ ] Add tests for parse and state-advance branches.
      **Notes:** Improves stream stability under malformed event payloads.

### [WL-8631]

**Title:** Preserve sync conflict diagnostics by separating conflict reason parse and conflict report emission
**Source:** [thegent/src/thegent/sync/conflict_report.py:512]
**Acceptance checklist:**

- [ ] Separate conflict reason parse failures from conflict report emission.
- [ ] Preserve conflict reporting with reason fallback.
- [ ] Add tests for parse and emission branch errors.
      **Notes:** Helps operators triage conflicts when one reason format degrades.

### [WL-8632]

**Title:** Preserve queue worker health by separating worker heartbeat parse and health status write
**Source:** [thegent/src/thegent/queue/worker_health.py:333]
**Acceptance checklist:**

- [ ] Separate worker heartbeat parse failures from health write failures.
- [ ] Preserve worker status with heartbeat fallback.
- [ ] Add tests for heartbeat parse and status write branches.
      **Notes:** Improves long-running worker reliability under heartbeat noise.

### [WL-8633]

**Title:** Preserve API request retries by separating retry policy decode and retry executor
**Source:** [thegent/src/thegent/http/retry_policy.py:531]
**Acceptance checklist:**

- [ ] Separate retry policy decode failures from retry executor failures.
- [ ] Preserve executor fallback when policy decode is invalid.
- [ ] Add tests for decode and executor branches.
      **Notes:** Prevents broad request stalls due to one policy decode bug.

### [WL-8634]

**Title:** Preserve config template rendering by separating variable rendering and output assembly
**Source:** [thegent/src/thegent/config/templates.py:501]
**Acceptance checklist:**

- [ ] Separate template variable rendering failures from output assembly failures.
- [ ] Preserve rendered output with assembly fallback.
- [ ] Add tests for rendering and assembly branch failures.
      **Notes:** Keeps config generation resilient under template syntax drift.

### [WL-8635]

**Title:** Preserve artifact retention by separating retention rule parse and retention executor
**Source:** [thegent/src/thegent/artifacts/retention_runner.py:412]
**Acceptance checklist:**

- [ ] Separate retention rule parse failures from retention executor failures.
- [ ] Preserve retention execution with rule fallback.
- [ ] Add tests for parse and executor branches.
      **Notes:** Helps prevent retention misbehavior under malformed retention configs.

### [WL-8636]

**Title:** Preserve sync connector provisioning by separating connector metadata parse and connector bootstrap
**Source:** [thegent/src/thegent/integrations/connector_bootstrap.py:398]
**Acceptance checklist:**

- [ ] Separate connector metadata parse failures from connector bootstrap failures.
- [ ] Preserve bootstrap behavior with metadata fallback.
- [ ] Add tests for metadata parse and bootstrap branches.
      **Notes:** Supports stable onboarding despite connector spec drift.

### [WL-8637]

**Title:** Preserve task orchestration by separating dependency parse and orchestrator assignment
**Source:** [thegent/src/thegent/tasks/orchestrator.py:489]
**Acceptance checklist:**

- [ ] Separate dependency parse failures from orchestrator assignment failures.
- [ ] Preserve assignment fallback for invalid dependency graphs.
- [ ] Add tests for parse and assignment branches.
      **Notes:** Keeps tasks scheduled in partial parse-failure scenarios.

### [WL-8638]

**Title:** Preserve shell profile resolution by separating profile source parse and profile resolution cache
**Source:** [thegent/src/thegent/shell/profile_resolver.py:523]
**Acceptance checklist:**

- [ ] Separate shell profile source parse failures from profile resolution cache failures.
- [ ] Preserve cache fallback for profile resolution.
- [ ] Add tests for parse and cache resolution branches.
      **Notes:** Reduces startup issues from profile format mismatches.

### [WL-8639]

**Title:** Preserve webhook payload replay by separating payload schema parse and replay scheduler
**Source:** [thegent/src/thegent/webhooks/replay.py:412]
**Acceptance checklist:**

- [ ] Separate webhook payload schema failures from replay scheduler failures.
- [ ] Preserve replay scheduling with schema fallback payload.
- [ ] Add tests for schema and scheduler branches.
      **Notes:** Helps webhook operators recover from bad historical payloads.
