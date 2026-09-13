### [WL-8170]

**Title:** Split dashboard startup failures into config read and router init failures
**Source:** [thegent/src/thegent/mesh/cli.py:221]
**Acceptance checklist:**

- [ ] Separate manifest/config file IO failures from router initialization exceptions.
- [ ] Preserve existing fallback status for missing dashboard data.
- [ ] Add tests for unreadable config and router init failures.
      **Notes:** Improves failure attribution during dashboard boot.

### [WL-8171]

**Title:** Preserve shell command completion while splitting parser syntax from runtime errors
**Source:** [thegent/src/thegent/shell_cli.py:600]
**Acceptance checklist:**

- [ ] Isolate command parser failures from runtime execution exceptions.
- [ ] Keep completion generation behavior on parse errors.
- [ ] Add tests for parser exception and execution exception cases.
      **Notes:** Reduces user-facing completion regressions during parse edge cases.

### [WL-8172]

**Title:** Separate artifact collector read errors from artifact metadata decode
**Source:** [thegent/src/thegent/artifacts/collector.py:201]
**Acceptance checklist:**

- [ ] Handle missing artifact files independently from metadata decode failures.
- [ ] Preserve collector scan behavior for partial path failures.
- [ ] Add tests for missing files and invalid metadata formats.
      **Notes:** Prevents one bad file from aborting full collection.

### [WL-8173]

**Title:** Preserve queue claim behavior with explicit stale lock cleanup handling
**Source:** [thegent/src/thegent/queue/claim.py:371]
**Acceptance checklist:**

- [ ] Separate stale lock detection from successful lock reaping workflows.
- [ ] Preserve claim fairness guarantees and cleanup behavior.
- [ ] Add tests for stale lock and reaping operations.
      **Notes:** Improves queue health under contention.

### [WL-8174]

**Title:** Keep retry policy semantics while separating timeout and invalid strategy values
**Source:** [thegent/src/thegent/retry/strategy.py:145]
**Acceptance checklist:**

- [ ] Distinguish timeout exceedance from invalid strategy value parse failures.
- [ ] Preserve retry ceilings and defaults on policy parse faults.
- [ ] Add tests for invalid strategy specs and timeout breaches.
      **Notes:** Enhances clarity in automated retry decisioning.

### [WL-8175]

**Title:** Preserve metrics reporting while separating schema and transport failures
**Source:** [thegent/src/thegent/telemetry/metrics_sink.py:155]
**Acceptance checklist:**

- [ ] Add separate branches for payload schema validation and network send failures.
- [ ] Preserve local buffering behavior for transport outages.
- [ ] Add tests for schema violations and send exceptions.
      **Notes:** Keeps metrics telemetry reliable when one side fails.

### [WL-8176]

**Title:** Separate plugin discovery and plugin import errors in UI plugin loading
**Source:** [thegent/src/thegent/ui/plugin_loader.py:318]
**Acceptance checklist:**

- [ ] Handle discovery scan failures independently from plugin import failures.
- [ ] Keep UI startup behavior stable when plugins are partially unavailable.
- [ ] Add tests for discovery IO errors and import tracebacks.
      **Notes:** Prevents one plugin problem from breaking full UI startup.

### [WL-8177]

**Title:** Preserve bootstrap behavior while separating auth config parse and auth request failures
**Source:** [thegent/src/thegent/session/bootstrap.py:256]
**Acceptance checklist:**

- [ ] Add explicit branches for malformed auth config and request transport errors.
- [ ] Keep bootstrap success path unchanged for valid config.
- [ ] Add tests for invalid config and transport failures.
      **Notes:** Speeds auth-related troubleshooting.

### [WL-8178]

**Title:** Separate DAG cycle detection from missing-node failures
**Source:** [thegent/src/thegent/planner/dag.py:522]
**Acceptance checklist:**

- [ ] Keep cycle detection errors separate from unresolved node reference errors.
- [ ] Preserve planner fallback or error output semantics.
- [ ] Add tests for cyclic and unresolved-node inputs.
      **Notes:** Makes planner diagnostics actionable for pipeline authors.

### [WL-8179]

**Title:** Preserve artifact retention defaults while separating predicate evaluation from cleanup errors
**Source:** [thegent/src/thegent/artifacts/retention.py:240]
**Acceptance checklist:**

- [ ] Split retention predicate failures from actual cleanup I/O failures.
- [ ] Keep retention policy defaults when predicate evaluation fails.
- [ ] Add tests for invalid predicate and permission-denied cleanup.
      **Notes:** Supports safer retention actions under partial filesystem issues.
