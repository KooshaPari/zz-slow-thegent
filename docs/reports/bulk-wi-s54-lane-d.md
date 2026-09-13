### [WL-8250]

**Title:** Preserve startup bootstrap while separating cache read failures from schema validation
**Source:** [thegent/src/thegent/session/bootstrap.py:344]
**Acceptance checklist:**

- [ ] Split bootstrap cache read failures from cache schema validation failures.
- [ ] Preserve bootstrap defaults on schema validation issues.
- [ ] Add tests for read and schema failure paths.
      **Notes:** Maintains startup stability when cache is stale.

### [WL-8251]

**Title:** Preserve artifact collector pipeline by separating stream decode and write failures
**Source:** [thegent/src/thegent/artifacts/collector.py:338]
**Acceptance checklist:**

- [ ] Separate stream decode failures from collector write failures.
- [ ] Keep collecting valid entries when one write fails.
- [ ] Add tests for decode and write exception paths.
      **Notes:** Prevents single bad stream entry from aborting the pipeline.

### [WL-8252]

**Title:** Preserve settings hot reload by separating file watch and parser failures
**Source:** [thegent/src/thegent/config/settings.py:432]
**Acceptance checklist:**

- [ ] Separate watcher event processing failures from parser failures.
- [ ] Preserve previous config on parse failures.
- [ ] Add tests for watcher and parser branches.
      **Notes:** Improves reliability when live config files are temporarily invalid.

### [WL-8253]

**Title:** Preserve queue reclaim behavior by separating stale lock detection from storage writes
**Source:** [thegent/src/thegent/queue/claim.py:411]
**Acceptance checklist:**

- [ ] Distinguish stale lock detection errors from storage write failures.
- [ ] Preserve reclaim attempt outcomes for stale locks only.
- [ ] Add tests for detection and write failures.
      **Notes:** Better queue diagnostics in multi-process conditions.

### [WL-8254]

**Title:** Preserve health endpoint fallback while separating request throttling and response composition
**Source:** [thegent/src/thegent/health/endpoint.py:312]
**Acceptance checklist:**

- [ ] Separate throttling violations from response formatter failures.
- [ ] Preserve graceful fallback when format fails.
- [ ] Add tests for throttled requests and format failures.
      **Notes:** Keeps monitoring robust under stress.

### [WL-8255]

**Title:** Preserve orchestrator command parsing while separating parse and execution exceptions
**Source:** [thegent/src/thegent/orchestration/scheduler.py:468]
**Acceptance checklist:**

- [ ] Split command parse exceptions from execution exceptions.
- [ ] Preserve command-state consistency when parse fails.
- [ ] Add tests for parse and execution paths.
      **Notes:** Makes orchestration failures actionable faster.

### [WL-8256]

**Title:** Preserve borrow retry logging while separating delay and retry dispatch failures
**Source:** [thegent/src/thegent/tools/borrow.py:708]
**Acceptance checklist:**

- [ ] Separate retry delay calculation failures from retry dispatch failures.
- [ ] Keep retry metadata output stable.
- [ ] Add tests for delay math and dispatch exceptions.
      **Notes:** Prevents retry storms from deterministic delay issues.

### [WL-8257]

**Title:** Preserve plugin loader integrity by separating plugin discovery from plugin-level validation
**Source:** [thegent/src/thegent/ui/plugin_loader.py:404]
**Acceptance checklist:**

- [ ] Distinguish discovery transport failures from plugin validation failures.
- [ ] Keep existing plugin list fallback behavior.
- [ ] Add tests for each discovery/validation branch.
      **Notes:** Helps root-cause plugin ecosystem issues.

### [WL-8258]

**Title:** Preserve agent runner behavior by separating process spawn and setup script failures
**Source:** [thegent/src/thegent/infra/agent_runner.py:350]
**Acceptance checklist:**

- [ ] Add separate branches for spawn failures and setup-script failures.
- [ ] Keep runner state cleanup consistent on both.
- [ ] Add tests for spawn and setup script branches.
      **Notes:** Improves startup diagnostics for agent workers.

### [WL-8259]

**Title:** Preserve summary rendering stability by separating section-level and full render failures
**Source:** [thegent/src/thegent/summary.py:476]
**Acceptance checklist:**

- [ ] Distinguish section render failures from full render failures.
- [ ] Preserve partial summary output when possible.
- [ ] Add tests for section and full render exception paths.
      **Notes:** Improves resilience under partial rendering regressions.
