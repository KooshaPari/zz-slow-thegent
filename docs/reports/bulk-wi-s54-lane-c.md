### [WL-8240]

**Title:** Preserve replay flow by separating event parse and dispatch failures
**Source:** [thegent/src/thegent/execution.py:598]
**Acceptance checklist:**

- [ ] Separate replay event JSON parse failures from dispatch exceptions.
- [ ] Keep replay fallback behavior when dispatch fails.
- [ ] Add tests for parse and dispatch branch failures.
      **Notes:** Improves determinism in replay diagnostics.

### [WL-8241]

**Title:** Preserve shell history prune behavior by separating retention rule parse from file cleanup
**Source:** [thegent/src/thegent/clipboard/history.py:378]
**Acceptance checklist:**

- [ ] Separate retention rule parse failures from cleanup execution failures.
- [ ] Preserve history cleanup with valid rules on execution errors.
- [ ] Add tests for malformed rule and cleanup exception cases.
      **Notes:** Helps avoid accidental history wipeouts.

### [WL-8242]

**Title:** Preserve orchestrator status reporting by separating transport and render failures
**Source:** [thegent/src/thegent/orchestration/scheduler.py:388]
**Acceptance checklist:**

- [ ] Separate status fetch transport failures from rendering path errors.
- [ ] Keep status snapshot contract stable.
- [ ] Add tests for transport and render exceptions.
      **Notes:** Reduces monitoring blind spots under partial outages.

### [WL-8243]

**Title:** Preserve artifact retention behavior while separating predicate and deletion exceptions
**Source:** [thegent/src/thegent/artifacts/retention.py:318]
**Acceptance checklist:**

- [ ] Split predicate evaluation errors from deletion operation exceptions.
- [ ] Keep retention statistics output stable.
- [ ] Add tests for predicate and deletion failures.
      **Notes:** Better protects against partial retention failures.

### [WL-8244]

**Title:** Preserve borrow command pipeline by separating schema and call-time failures
**Source:** [thegent/src/thegent/tools/borrow.py:668]
**Acceptance checklist:**

- [ ] Split request schema validation errors from transport call failures.
- [ ] Preserve retry semantics for call-time failures.
- [ ] Add tests for schema and call branches.
      **Notes:** Prevents spurious retries from deterministic schema errors.

### [WL-8245]

**Title:** Preserve UI panel rendering by separating payload shape and rendering exceptions
**Source:** [thegent/src/thegent/ui/compositor_manager.py:532]
**Acceptance checklist:**

- [ ] Separate input payload validation from rendering engine exceptions.
- [ ] Keep fallback output generation on payload issues.
- [ ] Add tests for both branches.
      **Notes:** Improves runtime behavior during UI schema changes.

### [WL-8246]

**Title:** Preserve settings validation while separating required and optional value parsing
**Source:** [thegent/src/thegent/config/settings.py:392]
**Acceptance checklist:**

- [ ] Separate required-key parse failures from optional-key parse failures.
- [ ] Preserve default substitution for optional keys.
- [ ] Add tests for required/optional parse split behavior.
      **Notes:** Improves clarity of startup failures.

### [WL-8247]

**Title:** Preserve scheduler retry handling by separating jitter and timer exceptions
**Source:** [thegent/src/thegent/orchestration/scheduler.py:423]
**Acceptance checklist:**

- [ ] Split jitter computation failures from timer scheduling failures.
- [ ] Preserve retry scheduling contract on jitter failures.
- [ ] Add tests for jitter and timer exception paths.
      **Notes:** More robust backoff behavior under edge cases.

### [WL-8248]

**Title:** Preserve process-compose recovery by separating compose config parse and compose execution
**Source:** [thegent/src/thegent/process_compose/watcher.py:228]
**Acceptance checklist:**

- [ ] Separate config parse errors from compose runtime command failures.
- [ ] Preserve backoff/retry for runtime failures.
- [ ] Add tests for invalid config and command invocation errors.
      **Notes:** Reduces false alerts during file-editing operations.

### [WL-8249]

**Title:** Preserve summary parser by separating markdown parse and JSON serialize failures
**Source:** [thegent/src/thegent/summary.py:432]
**Acceptance checklist:**

- [ ] Distinguish markdown parse failures from JSON serialization failures.
- [ ] Keep summary generation available when one path fails.
- [ ] Add tests for malformed markdown and JSON failures.
      **Notes:** Prevents complete summary loss from one bad input format.
