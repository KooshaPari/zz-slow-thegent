### [WL-8270]

**Title:** Separate shell auto-complete parsing failures from completion execution failures
**Source:** [thegent/src/thegent/shell_cli.py:812]
**Acceptance checklist:**

- [ ] Separate parser syntax failures from completion resolver exceptions.
- [ ] Preserve completion output for execution-related failures.
- [ ] Add tests for both parsing and execution branches.
      **Notes:** Reduces ambiguity in CLI completion defects.

### [WL-8271]

**Title:** Preserve config bootstrap while separating environment load and validation failures
**Source:** [thegent/src/thegent/session/bootstrap.py:384]
**Acceptance checklist:**

- [ ] Distinguish env-file read failures from env validation failures.
- [ ] Keep defaults loaded on validation failures where appropriate.
- [ ] Add tests for missing files and invalid values.
      **Notes:** Improves startup diagnosability in partially broken environments.

### [WL-8272]

**Title:** Keep artifact retention deterministic by splitting predicate and persistence failures
**Source:** [thegent/src/thegent/artifacts/retention.py:392]
**Acceptance checklist:**

- [ ] Split evaluation predicate errors and DB persistence failures.
- [ ] Preserve retention operation for valid entries.
- [ ] Add tests for each error branch.
      **Notes:** Prevents whole-run aborts due to one failure mode.

### [WL-8273]

**Title:** Preserve queue reclaim semantics while separating duplicate claims and storage errors
**Source:** [thegent/src/thegent/queue/claim.py:451]
**Acceptance checklist:**

- [ ] Distinguish duplicate claim attempts from storage write failures.
- [ ] Preserve reclaim behavior for duplicate attempts.
- [ ] Add tests for duplicate and storage-IO failure cases.
      **Notes:** Helps operators understand contention versus infra issues.

### [WL-8274]

**Title:** Preserve health endpoint schema handling while separating parse and rate-limit branches
**Source:** [thegent/src/thegent/health/endpoint.py:352]
**Acceptance checklist:**

- [ ] Separate request schema validation from rate-limit enforcement branches.
- [ ] Preserve status code contract for both cases.
- [ ] Add tests for invalid schema and rate-limit denials.
      **Notes:** Improves reliability in active monitoring environments.

### [WL-8275]

**Title:** Preserve plugin runtime loading by separating manifest discovery and runtime import
**Source:** [thegent/src/thegent/ui/plugin_loader.py:436]
**Acceptance checklist:**

- [ ] Separate discovery list parse errors from runtime import failures.
- [ ] Maintain partial plugin loading for valid imports.
- [ ] Add tests for discovery/import branch coverage.
      **Notes:** Keeps UI functional even with malformed plugin data.

### [WL-8276]

**Title:** Preserve retry strategy calculations by separating numeric bounds and jitter generation
**Source:** [thegent/src/thegent/retry/strategy.py:272]
**Acceptance checklist:**

- [ ] Separate numeric bounds validation from jitter RNG generation failures.
- [ ] Preserve deterministic fallback on jitter failures.
- [ ] Add tests for bad bounds and jitter failures.
      **Notes:** Increases resilience in retry schedule computation.

### [WL-8277]

**Title:** Preserve artifact upload telemetry by separating metadata and transport paths
**Source:** [thegent/src/thegent/artifacts/uploader.py:442]
**Acceptance checklist:**

- [ ] Distinguish metadata extraction failures from upload transport failures.
- [ ] Preserve upload attempt outcomes on metadata branch failures.
- [ ] Add tests for each branch.
      **Notes:** Improves visibility of root-cause in uploads.

### [WL-8278]

**Title:** Preserve command routing while separating command schema validation and downstream dispatch
**Source:** [thegent/src/thegent/mesh/control.py:592]
**Acceptance checklist:**

- [ ] Split schema validation failures from downstream dispatch failures.
- [ ] Preserve routing fallback for recoverable dispatch errors.
- [ ] Add tests for malformed commands and downstream errors.
      **Notes:** Better handling under mixed control plane input quality.

### [WL-8279]

**Title:** Preserve scheduler status output while splitting formatting and transport failures
**Source:** [thegent/src/thegent/orchestration/scheduler.py:548]
**Acceptance checklist:**

- [ ] Separate status output formatting failures from transport send failures.
- [ ] Keep status polling semantics intact.
- [ ] Add tests for formatter and transport exceptions.
      **Notes:** Improves monitoring reliability when one rendering branch breaks.
