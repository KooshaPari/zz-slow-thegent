### [WL-8260]

**Title:** Preserve queue scheduler metrics while separating ingestion and persistence failures
**Source:** [thegent/src/thegent/queue/scaler.py:262]
**Acceptance checklist:**

- [ ] Split ingestion parser failures from persistence failures.
- [ ] Keep scheduler metrics pipeline running on ingestion failures.
- [ ] Add tests for parser and persistence exceptions.
      **Notes:** Improves monitoring continuity in noisy environments.

### [WL-8261]

**Title:** Preserve conversation export behavior by separating archive generation and upload failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:401]
**Acceptance checklist:**

- [ ] Separate archive generation failures from artifact upload failures.
- [ ] Preserve local export artifacts on upload failures.
- [ ] Add tests for archive and upload failure cases.
      **Notes:** Avoids losing user exports when remote upload is unavailable.

### [WL-8262]

**Title:** Preserve retry strategy defaults by separating environment and runtime calculation failures
**Source:** [thegent/src/thegent/retry/strategy.py:232]
**Acceptance checklist:**

- [ ] Separate env parsing failures from runtime calculation failures.
- [ ] Keep default strategy on env parse problems.
- [ ] Add tests for env and calc failure scenarios.
      **Notes:** Improves reliability when runtime tuning is partially configured.

### [WL-8263]

**Title:** Preserve MCP borrow diagnostics while separating tool registration and execution failures
**Source:** [thegent/src/thegent/tools/borrow.py:744]
**Acceptance checklist:**

- [ ] Split registration failures from invocation execution failures.
- [ ] Keep borrow outcome shape stable.
- [ ] Add tests for each registration and invocation branch.
      **Notes:** Helps isolate configuration versus runtime platform issues.

### [WL-8264]

**Title:** Preserve process-compose monitor stability by separating status parse and trigger failures
**Source:** [thegent/src/thegent/process_compose/watcher.py:265]
**Acceptance checklist:**

- [ ] Distinguish process status parse failures from trigger execution failures.
- [ ] Preserve monitor polling when only one branch fails.
- [ ] Add tests for parse and trigger branches.
      **Notes:** Improves stability during compose topology changes.

### [WL-8265]

**Title:** Preserve shell history sync by separating encryption/decryption and transport failures
**Source:** [thegent/src/thegent/clipboard/history.py:418]
**Acceptance checklist:**

- [ ] Separate encryption/decryption failures from transport failures.
- [ ] Preserve sync output with transport fallback behavior.
- [ ] Add tests for crypto and transport failure branches.
      **Notes:** Useful for secure environments with mixed key states.

### [WL-8266]

**Title:** Preserve artifact retention metadata while separating serialization and retention eval failures
**Source:** [thegent/src/thegent/artifacts/retention.py:356]
**Acceptance checklist:**

- [ ] Isolate metadata serialization failures from retention evaluation failures.
- [ ] Keep retention results available on metadata failures.
- [ ] Add tests for both failure classes.
      **Notes:** Prevents unnecessary retention disruption.

### [WL-8267]

**Title:** Preserve scheduler reconciliation by separating diff computation and persistence failures
**Source:** [thegent/src/thegent/orchestration/scheduler.py:512]
**Acceptance checklist:**

- [ ] Split diff computation failures from persistence flush failures.
- [ ] Keep reconciliation decisions stable when persistence fails.
- [ ] Add tests for diff and persistence branches.
      **Notes:** Improves robustness under partial DB/storage outages.

### [WL-8268]

**Title:** Preserve CLI diagnostics while separating command cache and execution exceptions
**Source:** [thegent/src/thegent/shell_cli.py:782]
**Acceptance checklist:**

- [ ] Separate command cache miss handling from execution exceptions.
- [ ] Preserve user-facing diagnostics for execution failures.
- [ ] Add tests for cache misses and execution errors.
      **Notes:** Better observability for complex CLI flows.

### [WL-8269]

**Title:** Preserve prompt persistence while separating prompt cache write and sync failures
**Source:** [thegent/src/thegent/prompts.py:313]
**Acceptance checklist:**

- [ ] Distinguish cache write failures from sync failures.
- [ ] Preserve prompt rendering behavior when persistence fails.
- [ ] Add tests for write and sync failure paths.
      **Notes:** Keeps prompt usage stable when persistence infrastructure is flaky.
