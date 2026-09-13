### [WL-8320]

**Title:** Preserve config bootstrap determinism while splitting file parse and env overlay
**Source:** [thegent/src/thegent/session/bootstrap.py:401]
**Acceptance checklist:**

- [ ] Separate bootstrap file parse errors from environment overlay merge errors.
- [ ] Keep baseline defaults active when overlay loading fails.
- [ ] Add tests for malformed bootstrap files and overlay conflicts.
      **Notes:** Prevents complete startup failures due to one malformed layer.

### [WL-8321]

**Title:** Preserve queue claim semantics by splitting lock acquisition and ownership validation
**Source:** [thegent/src/thegent/queue/claim.py:523]
**Acceptance checklist:**

- [ ] Distinguish queue lock acquisition failures from ownership assertion failures.
- [ ] Preserve claim retries when ownership validation is temporary.
- [ ] Add tests for transient lock conflicts versus permanent ownership errors.
      **Notes:** Improves reliability for distributed workers.

### [WL-8322]

**Title:** Preserve plugin discovery while separating manifest parse and import path resolution
**Source:** [thegent/src/thegent/ui/plugin_loader.py:471]
**Acceptance checklist:**

- [ ] Split malformed manifest errors from import resolution failures.
- [ ] Keep successfully parsed plugins loadable despite one bad path.
- [ ] Add tests for malformed manifest and bad import branches.
      **Notes:** Avoids complete plugin UI downgrades on partial metadata issues.

### [WL-8323]

**Title:** Preserve retry schedule by separating policy parse and state persistence failures
**Source:** [thegent/src/thegent/retry/strategy.py:308]
**Acceptance checklist:**

- [ ] Isolate parsing policy text from persistence state write failures.
- [ ] Ensure retry decisions continue with in-memory state on persistence errors.
- [ ] Add tests for policy parse versus persistence branch errors.
      **Notes:** Keeps retries predictable when storage is degraded.

### [WL-8324]

**Title:** Preserve artifact cleanup while separating age calculation and deletion execution
**Source:** [thegent/src/thegent/artifacts/retention.py:420]
**Acceptance checklist:**

- [ ] Split age-based candidate calculation from deletion command execution errors.
- [ ] Preserve cleanup eligibility visibility on deletion failures.
- [ ] Add tests for candidate computation and delete-failure paths.
      **Notes:** Helps retain observability when cleanup I/O is flaky.

### [WL-8325]

**Title:** Preserve health endpoint behavior while separating schema validation and limit enforcement
**Source:** [thegent/src/thegent/health/endpoint.py:389]
**Acceptance checklist:**

- [ ] Separate invalid request schema handling from rate-limit branch behavior.
- [ ] Preserve expected status codes in both branches.
- [ ] Add tests for schema and limit failures independently.
      **Notes:** Makes monitoring behavior easier to reason about under stress.

### [WL-8326]

**Title:** Preserve mesh command ordering by separating command decoding and dispatch selection
**Source:** [thegent/src/thegent/mesh/control.py:633]
**Acceptance checklist:**

- [ ] Separate decode validation failures from dispatch selection failures.
- [ ] Keep routing fallback path active when selection is transiently unavailable.
- [ ] Add tests for malformed command and downstream failure branches.
      **Notes:** Improves control plane resilience and observability.

### [WL-8327]

**Title:** Preserve upload telemetry by separating metadata extraction and payload signing
**Source:** [thegent/src/thegent/artifacts/uploader.py:489]
**Acceptance checklist:**

- [ ] Split metadata extraction failures from signing failures.
- [ ] Preserve telemetry emission for signed payload attempts.
- [ ] Add tests for metadata and signing error paths.
      **Notes:** Avoids missing traces from one broken telemetry branch.

### [WL-8328]

**Title:** Preserve scheduler status rendering while separating template and transport failures
**Source:** [thegent/src/thegent/orchestration/scheduler.py:591]
**Acceptance checklist:**

- [ ] Separate template render errors from transport send errors.
- [ ] Keep scheduler status reporting stable for formatting failures.
- [ ] Add tests for each branch independently.
      **Notes:** Improves monitoring continuity when one output path regresses.

### [WL-8329]

**Title:** Preserve CLI autocompletion by separating grammar parse and completion cache loading
**Source:** [thegent/src/thegent/shell_cli.py:852]
**Acceptance checklist:**

- [ ] Separate completion grammar syntax parsing from cache hydration failures.
- [ ] Keep cache-backed completions available when grammar parsing is invalid.
- [ ] Add tests for grammar and cache failure branches.
      **Notes:** Reduces autocompletion outages from partial configuration issues.
