### [WL-6470] Harden config settings projection for selective key export

**Source Path+Line:** [thegent/src/thegent/config_provider.py:28]
**Acceptance Checklist:**

- [ ] Ensure `_settings_to_dict` returns only requested keys without leaking unset fields.
- [ ] Add focused tests for empty key lists, unknown keys, and stable key ordering.
- [ ] Preserve current provider contract for callers using full-settings mode.
      **Notes:** Implementation should stay local to config shaping logic and avoid side effects in provider resolution.

### [WL-6471] Stabilize shared server session bootstrap response contract

**Source Path+Line:** [thegent/src/thegent/shared_server_integration.py:21]
**Acceptance Checklist:**

- [ ] Normalize bootstrap return payload keys for success, partial-failure, and no-op paths.
- [ ] Add tests that pin language filtering and project-root override behavior.
- [ ] Keep cleanup and info APIs backward compatible with existing session flows.
      **Notes:** Focus on deterministic startup metadata so downstream orchestration can branch safely.

### [WL-6472] Add deterministic dequeue/backpressure behavior in task queue core

**Source Path+Line:** [thegent/src/thegent/task_queue/queue.py:10]
**Acceptance Checklist:**

- [ ] Define and enforce queue ordering semantics under concurrent enqueue/dequeue operations.
- [ ] Add timeout and max-depth coverage to prevent silent starvation.
- [ ] Document failure behavior when consumers request from an empty queue.
      **Notes:** Keep changes scoped to queue internals and test synchronization boundaries explicitly.

### [WL-6473] Tighten watcher spec event filtering at handler boundary

**Source Path+Line:** [thegent/src/thegent/native/watcher_daemon.py:152]
**Acceptance Checklist:**

- [ ] Ensure `_SpecHandler` ignores noisy filesystem events not matching active watch specs.
- [ ] Add tests for include/exclude glob collisions and duplicate event coalescing.
- [ ] Verify no regression in daemon callback delivery ordering.
      **Notes:** Prioritize low-noise event streams to reduce downstream churn in watcher consumers.

### [WL-6474] Improve cache tier fallback guarantees for multi-level cache reads

**Source Path+Line:** [thegent/src/thegent/cache/multi_level.py:39]
**Acceptance Checklist:**

- [ ] Enforce clear read-through order across memory, disk, and upstream tiers.
- [ ] Add tests for stale-entry invalidation and partial-tier outages.
- [ ] Keep cache hit/miss metrics accurate after fallback paths execute.
      **Notes:** This item should strengthen resilience without changing the external cache API.

### [WL-6475] Formalize promotion scoring thresholds in model promoter workflow

**Source Path+Line:** [thegent/src/thegent/learning/promotion.py:10]
**Acceptance Checklist:**

- [ ] Centralize threshold constants and remove implicit magic numbers in promotion decisions.
- [ ] Add tests covering edge-threshold ties and insufficient-signal rejection.
- [ ] Preserve existing promotion output schema used by callers.
      **Notes:** Keep behavior auditable so governance tooling can explain promotion outcomes.

### [WL-6476] Validate infra provisioner resource spec before execution fan-out

**Source Path+Line:** [thegent/src/thegent/infra/provisioner.py:25]
**Acceptance Checklist:**

- [ ] Add preflight validation for malformed `ResourceSpec` entries before provisioning begins.
- [ ] Surface actionable error messages that identify failing resource identifiers.
- [ ] Add regression tests for mixed valid/invalid batch requests.
      **Notes:** Emphasis is fail-fast validation to reduce partial provisioning side effects.

### [WL-6477] Enforce keepalive lifecycle invariants in terminal keepalive manager

**Source Path+Line:** [thegent/src/thegent/infra/terminal_keepalive.py:244]
**Acceptance Checklist:**

- [ ] Guard start/stop transitions to prevent duplicate worker threads.
- [ ] Add tests for repeated start-stop cycles and max-failure shutdown behavior.
- [ ] Confirm tmux/stdin transport fallback path remains intact.
      **Notes:** Keep lifecycle control deterministic because session stability depends on it.

### [WL-6478] Strengthen quality control plane gate exit codes and diagnostics

**Source Path+Line:** [thegent/scripts/validate_quality_control_plane.py:35]
**Acceptance Checklist:**

- [ ] Differentiate contract-missing, parse-failure, and threshold-breach exit codes.
- [ ] Emit concise diagnostics that pinpoint the failing contract section.
- [ ] Add CLI tests that assert stable stderr wording for CI parsing.
      **Notes:** Intended for CI reliability; avoid broad refactors outside gate evaluation logic.

### [WL-6479] Expand SARIF emission fidelity for generated-python antipattern scan

**Source Path+Line:** [thegent/scripts/check_generated_python_antipatterns.py:123]
**Acceptance Checklist:**

- [ ] Ensure SARIF output includes stable rule IDs, locations, and severity mapping.
- [ ] Add tests for empty findings, single finding, and multi-file finding aggregation.
- [ ] Preserve plain-text output path for local developer workflows.
      **Notes:** Keep SARIF schema-compliant so results ingest cleanly in code scanning platforms.
