### [WL-8280]

**Title:** Preserve borrow path with explicit handling for endpoint resolution failures
**Source:** [thegent/src/thegent/tools/borrow.py:782]
**Acceptance checklist:**

- [ ] Split endpoint resolution failures from request send failures.
- [ ] Preserve result schema for request send failures.
- [ ] Add tests for endpoint and send failure branches.
      **Notes:** Improves failure isolation in broker connectivity.

### [WL-8281]

**Title:** Preserve prompt rendering pipeline while separating cache read and render branches
**Source:** [thegent/src/thegent/prompts.py:343]
**Acceptance checklist:**

- [ ] Separate cache read exceptions from prompt render exceptions.
- [ ] Preserve render fallback when cache read fails.
- [ ] Add tests for cache read and render failures.
      **Notes:** Helps reduce user impact of cache corruption.

### [WL-8282]

**Title:** Preserve conversation export reliability while separating pack and fs sync failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:440]
**Acceptance checklist:**

- [ ] Separate archive packing failures from filesystem sync failures.
- [ ] Keep pack failures surfaced with stable return semantics.
- [ ] Add tests for pack and sync failures.
      **Notes:** Avoids masking filesystem issues behind pack errors.

### [WL-8283]

**Title:** Preserve control plane startup by separating certificate load from server bind failures
**Source:** [thegent/src/thegent/control_plane/server.py:454]
**Acceptance checklist:**

- [ ] Handle certificate loading failures separately from socket bind failures.
- [ ] Preserve existing startup behavior for bind fallback.
- [ ] Add tests for cert and bind error branches.
      **Notes:** Reduces false starts due to mixed startup errors.

### [WL-8284]

**Title:** Preserve artifact collector metrics by separating stream parse and aggregation errors
**Source:** [thegent/src/thegent/artifacts/collector.py:376]
**Acceptance checklist:**

- [ ] Distinguish stream parse issues from aggregation math issues.
- [ ] Keep collector output stable on parse problems.
- [ ] Add tests for parse and aggregation errors.
      **Notes:** Helps triage metric anomalies.

### [WL-8285]

**Title:** Preserve shell completion cache lifecycle while separating stale markers and parse errors
**Source:** [thegent/src/thegent/shell_cli.py:842]
**Acceptance checklist:**

- [ ] Separate stale cache marker handling from cache parse failures.
- [ ] Preserve completion flow with cache rebuild fallback.
- [ ] Add tests for stale markers and parse invalid data.
      **Notes:** Keeps completion responsive during cache churn.

### [WL-8286]

**Title:** Preserve settings hot reload by separating parser and merger failures
**Source:** [thegent/src/thegent/config/settings.py:472]
**Acceptance checklist:**

- [ ] Split parser exceptions from settings merge exceptions.
- [ ] Preserve existing settings baseline on merge failures.
- [ ] Add tests for parser and merge failures.
      **Notes:** Helps avoid hard crashes on partial config reloads.

### [WL-8287]

**Title:** Preserve process-compose refresh when compose parser fails
**Source:** [thegent/src/thegent/process_compose/watcher.py:301]
**Acceptance checklist:**

- [ ] Separate compose file parse errors from command scheduling errors.
- [ ] Keep refresh cadence on parse errors.
- [ ] Add tests for parser and scheduling failures.
      **Notes:** Maintains automation under config churn.

### [WL-8288]

**Title:** Preserve scheduler metrics by separating read and render failures
**Source:** [thegent/src/thegent/orchestration/scheduler.py:584]
**Acceptance checklist:**

- [ ] Split metric read exceptions from metric render exceptions.
- [ ] Preserve metrics endpoint availability despite one side failing.
- [ ] Add tests for read/render branches.
      **Notes:** Improves visibility under monitoring system issues.

### [WL-8289]

**Title:** Preserve artifact metadata handling while separating decode and persistence errors
**Source:** [thegent/src/thegent/artifacts/collector.py:409]
**Acceptance checklist:**

- [ ] Separate metadata decode failures from persistence failures.
- [ ] Keep partial metadata writes from blocking collection flow.
- [ ] Add tests for decode and persistence failure cases.
      **Notes:** Reduces cascade from partial metadata corruption.
