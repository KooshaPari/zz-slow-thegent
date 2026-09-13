### [WL-8780]

**Title:** Preserve sync queue fairness by separating fairness rule parse and fairness enforcement
**Source:** [thegent/src/thegent/sync/fairness.py:333]
**Acceptance checklist:**

- [ ] Separate fairness rule parse failures from fairness enforcement failures.
- [ ] Preserve enforcement with default fairness rules.
- [ ] Add tests for fairness parse and enforcement branches.
      **Notes:** Keeps fairness guarantees stable under rule format drift.

### [WL-8781]

**Title:** Preserve artifact export by separating export manifest parse and export execution
**Source:** [thegent/src/thegent/artifacts/export_dispatch.py:523]
**Acceptance checklist:**

- [ ] Separate export manifest parse failures from execution failures.
- [ ] Preserve execution with manifest fallback.
- [ ] Add tests for parse and execution branches.
      **Notes:** Prevents export pipeline stalls from malformed manifests.

### [WL-8782]

**Title:** Preserve CLI history parse by separating history file parse and history render
**Source:** [thegent/src/thegent/cli/history_render.py:589]
**Acceptance checklist:**

- [ ] Separate history file parse failures from history render failures.
- [ ] Preserve render fallback on parse failures.
- [ ] Add tests for parse and render branch failures.
      **Notes:** Keeps command history readable under history format changes.

### [WL-8783]

**Title:** Preserve policy cache by separating cache descriptor parse and cache update
**Source:** [thegent/src/thegent/policies/cache_manager.py:501]
**Acceptance checklist:**

- [ ] Separate policy cache descriptor parse failures from cache update failures.
- [ ] Preserve cache updates with descriptor fallback.
- [ ] Add tests for descriptor parse and cache update branches.
      **Notes:** Improves policy access under descriptor schema variation.

### [WL-8784]

**Title:** Preserve queue task handoff by separating task handoff parse and handoff routing
**Source:** [thegent/src/thegent/queue/task_handoff.py:412]
**Acceptance checklist:**

- [ ] Separate task handoff parse failures from routing failures.
- [ ] Preserve handoff routing with parse fallback.
- [ ] Add tests for parse and routing branch failures.
      **Notes:** Improves queue throughput under handoff payload inconsistencies.

### [WL-8785]

**Title:** Preserve authentication middleware by separating middleware config parse and middleware registration
**Source:** [thegent/src/thegent/auth/middleware.py:333]
**Acceptance checklist:**

- [ ] Separate middleware config parse failures from registration failures.
- [ ] Preserve middleware registration with fallback config.
- [ ] Add tests for config and registration branches.
      **Notes:** Stabilizes auth pipeline under middleware config drift.

### [WL-8786]

**Title:** Preserve artifact scanning by separating scan request parse and scan worker dispatch
**Source:** [thegent/src/thegent/artifacts/scanner.py:589]
**Acceptance checklist:**

- [ ] Separate scan request parse failures from worker dispatch failures.
- [ ] Preserve scan dispatch with request fallback.
- [ ] Add tests for request parse and dispatch branches.
      **Notes:** Improves scan completion under request format variation.

### [WL-8787]

**Title:** Preserve command diagnostics by separating diagnostic rule parse and diagnostic publish
**Source:** [thegent/src/thegent/commands/diagnostic_publish.py:477]
**Acceptance checklist:**

- [ ] Separate diagnostic rule parse failures from publish failures.
- [ ] Preserve diagnostic publish with rule fallback.
- [ ] Add tests for diagnostic parse and publish branches.
      **Notes:** Keeps diagnostic output useful under diagnostics schema changes.

### [WL-8788]

**Title:** Preserve sync lock state by separating lock state parse and lock state persistence
**Source:** [thegent/src/thegent/sync/lock_state.py:501]
**Acceptance checklist:**

- [ ] Separate sync lock state parse failures from persistence failures.
- [ ] Preserve lock behavior with state parse fallback.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Prevents lock contention spikes during state format issues.

### [WL-8789]

**Title:** Preserve alert dispatch by separating alert event parse and alert handler routing
**Source:** [thegent/src/thegent/alerts/handler_router.py:358]
**Acceptance checklist:**

- [ ] Separate alert event parse failures from handler routing failures.
- [ ] Preserve alert routing via fallback handlers.
- [ ] Add tests for parse and routing branches.
      **Notes:** Improves alert delivery under alert payload variation.
