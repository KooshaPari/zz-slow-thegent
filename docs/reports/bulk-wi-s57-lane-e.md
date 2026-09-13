### [WL-8410]

**Title:** Preserve deployment config by separating template render and config merge
**Source:** [thegent/src/thegent/deploy/config.py:451]
**Acceptance checklist:**

- [ ] Separate deployment template render failures from config merge failures.
- [ ] Preserve baseline merge when rendering fails.
- [ ] Add tests for template render and merge branches.
      **Notes:** Helps deployments proceed when UI templates are mismatched.

### [WL-8411]

**Title:** Preserve artifact retention policy by separating policy load and action execution
**Source:** [thegent/src/thegent/artifacts/retention_policy.py:377]
**Acceptance checklist:**

- [ ] Separate retention policy load failures from policy action execution failures.
- [ ] Preserve retention defaults when loading fails.
- [ ] Add tests for load and execution branches.
      **Notes:** Prevents retention drift during transient policy source issues.

### [WL-8412]

**Title:** Preserve metrics stream by separating point parsing and output scheduling
**Source:** [thegent/src/thegent/metrics/streamer.py:602]
**Acceptance checklist:**

- [ ] Separate metrics point parsing failures from output scheduling failures.
- [ ] Keep metrics stream alive with parse fallback.
- [ ] Add tests for parse and scheduling branches.
      **Notes:** Improves observability under malformed point payloads.

### [WL-8413]

**Title:** Preserve alert routing by separating rule evaluation and notifier dispatch
**Source:** [thegent/src/thegent/alerts/routing.py:489]
**Acceptance checklist:**

- [ ] Separate alert rule evaluation failures from notifier dispatch failures.
- [ ] Preserve notifier fallback path when rules are temporarily invalid.
- [ ] Add tests for rule and dispatch branches.
      **Notes:** Keeps critical alerts functional during rule rollout.

### [WL-8414]

**Title:** Preserve task queue fairness by separating priority queue reorder and fairness counters
**Source:** [thegent/src/thegent/queue/fairness.py:512]
**Acceptance checklist:**

- [ ] Separate priority reorder failures from fairness counter update failures.
- [ ] Keep fairness counters monotonic on reorder branch failures.
- [ ] Add tests for reorder and counter branch behavior.
      **Notes:** Helps maintain fairness properties with noisy counters.

### [WL-8415]

**Title:** Preserve artifact upload by separating preflight validation and multipart upload
**Source:** [thegent/src/thegent/artifacts/multipart.py:438]
**Acceptance checklist:**

- [ ] Separate preflight validation failures from multipart session creation.
- [ ] Preserve single-part fallback on multipart-specific failures.
- [ ] Add tests for preflight and multipart branches.
      **Notes:** Improves upload success in constrained network segments.

### [WL-8416]

**Title:** Preserve command completion by separating completion source resolution and response render
**Source:** [thegent/src/thegent/shell_cli/completion.py:519]
**Acceptance checklist:**

- [ ] Separate completion source resolution failures from response render failures.
- [ ] Preserve baseline completion list for render problems.
- [ ] Add tests for source and render error branches.
      **Notes:** Keeps shell UX stable for autocomplete users.

### [WL-8417]

**Title:** Preserve runtime diagnostics by separating profiler sample decode and report emission
**Source:** [thegent/src/thegent/diagnostics/profiler.py:365]
**Acceptance checklist:**

- [ ] Separate profiler sample decoding failures from report emission failures.
- [ ] Keep diagnostics available with raw sample outputs.
- [ ] Add tests for decode and report branches.
      **Notes:** Helps debugging when profiler payload formats change.

### [WL-8418]

**Title:** Preserve endpoint allowlist by separating wildcard parse and enforcement update
**Source:** [thegent/src/thegent/security/allowlist.py:392]
**Acceptance checklist:**

- [ ] Separate wildcard parse failures from allowlist enforcement update failures.
- [ ] Preserve current allowlist behavior on wildcard branch errors.
- [ ] Add tests for parse and enforcement branches.
      **Notes:** Prevents accidental exposure during allowlist refactors.

### [WL-8419]

**Title:** Preserve session command history by separating command tokenization and persistence commit
**Source:** [thegent/src/thegent/session/history_store.py:512]
**Acceptance checklist:**

- [ ] Separate command tokenization failures from persistence commit failures.
- [ ] Preserve command history retrieval with tokenization fallback.
- [ ] Add tests for tokenization and persistence failures.
      **Notes:** Keeps operators productive despite parsing drift.
