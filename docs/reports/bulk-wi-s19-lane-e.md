### [WL-6510] Implement real MCP tool execution in gateway execute path

**Source Path+Line:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance Checklist:**

- [ ] Replace placeholder execution with concrete MCP invocation and typed result mapping.
- [ ] Preserve unknown-server and timeout error paths with deterministic error payloads.
- [ ] Add focused tests covering success, server missing, and execution failure branches.
      **Notes:** Current path documents itself as a stub and should become the production execution entrypoint.

### [WL-6511] Wire native diff statistics instead of zeroed fallback output

**Source Path+Line:** [thegent/src/thegent/native/git_native.py:56]
**Acceptance Checklist:**

- [ ] Implement `diff_stat` through `thegent_git` bindings (or explicit subprocess fallback inside the native layer contract).
- [ ] Remove unconditional warning + zero values when repository has actual changes.
- [ ] Add unit tests validating changed-file, insertion, and deletion counts on a temp repo.
      **Notes:** The current TODO returns all zeros, which masks real repository churn in downstream callers.

### [WL-6512] Implement GitHub Project item upsert during sync flow

**Source Path+Line:** [thegent/src/thegent/integrations/gh_project_sync.py:202]
**Acceptance Checklist:**

- [ ] Replace mock return with concrete create/update calls for project items.
- [ ] Populate created/updated/error counters from real operation results.
- [ ] Add integration-style tests with mocked GH CLI responses for create and update paths.
      **Notes:** This path currently performs discovery but never mutates project state.

### [WL-6513] Implement CSV-to-project import through GitHub API workflow

**Source Path+Line:** [thegent/src/thegent/integrations/gh_project_sync.py:359]
**Acceptance Checklist:**

- [ ] Parse CSV rows into validated item payloads before API submission.
- [ ] Execute import calls and return real imported/error totals.
- [ ] Add tests for malformed rows, partial failures, and successful bulk import.
      **Notes:** Current behavior is a hardcoded zero import response.

### [WL-6514] Complete PERT forward pass critical-path computation

**Source Path+Line:** [thegent/src/thegent/planning/simulation.py:38]
**Acceptance Checklist:**

- [ ] Compute earliest/latest timings and critical-path flags across dependency-aware graph traversal.
- [ ] Derive p50/p90 confidence values from task variance instead of default placeholders.
- [ ] Add deterministic tests for branching DAGs and zero-float critical tasks.
      **Notes:** The function is marked as a D1 stub and needs full schedule analysis semantics.

### [WL-6515] Implement resource contention simulation output generation

**Source Path+Line:** [thegent/src/thegent/planning/simulation.py:148]
**Acceptance Checklist:**

- [ ] Detect overlapping windows by shared resource constraints.
- [ ] Emit structured contention records with severity and candidate mitigation data.
- [ ] Add tests demonstrating at least one contention and one non-contention scenario.
      **Notes:** The current implementation returns an empty list regardless of inputs.

### [WL-6516] Implement continuity risk scoring model with actionable recommendations

**Source Path+Line:** [thegent/src/thegent/planning/simulation.py:224]
**Acceptance Checklist:**

- [ ] Compute risk score from open tasks, blocked count, ownership gaps, and interruption context.
- [ ] Produce non-empty factors/recommendations for high-risk states.
- [ ] Add tests for low-risk baseline and elevated-risk handoff conditions.
      **Notes:** Docstring marks this as D3 stub; score generation should align with workflow handoff policy.

### [WL-6517] Replace hardcoded execution quality metrics with computed telemetry

**Source Path+Line:** [thegent/src/thegent/execution.py:1047]
**Acceptance Checklist:**

- [ ] Source routing/accuracy/freshness/interruption/cost metrics from actual run telemetry.
- [ ] Keep metric schema stable while removing placeholder literals.
- [ ] Add tests that validate metric values change with fixture telemetry inputs.
      **Notes:** Placeholder constants currently make dashboard values static and non-diagnostic.

### [WL-6518] Implement unified config conflict detection and merge strategy

**Source Path+Line:** [thegent/src/thegent/integration/unified_config.py:162]
**Acceptance Checklist:**

- [ ] Detect divergences across configuration sources and classify conflict types.
- [ ] Apply deterministic merge strategy and write back resolved config where required.
- [ ] Add tests for no-conflict, simple override, and irreconcilable conflict cases.
      **Notes:** Inline comments outline intended behavior but current code remains placeholder-only.

### [WL-6519] Replace harness status placeholder with concrete capability probe

**Source Path+Line:** [thegent/src/thegent/sitback_plugins.py:136]
**Acceptance Checklist:**

- [ ] Return structured harness health with explicit unavailable/error states.
- [ ] Separate import/runtime failures from "not configured" outcomes.
- [ ] Add tests for harness-present and harness-absent environments.
      **Notes:** This function is explicitly named placeholder and should become the stable status provider.
