# ShareCLI Boundary Contracts

## Status

Draft - pre-code contract specification for the `thegent` -> `sharecli`
boundary cleanup.

## Purpose

This document defines the contracts that must exist before moving execution
substrate code from `thegent` into canonical `sharecli`. It prevents broad
module movement from turning into implicit API design.

## Boundary Rule

`sharecli` owns process orchestration, command execution substrate, queueing,
merge/worktree mechanics, and process/resource telemetry. `thegent` owns
governance, agent orchestration, policy, MCP/tool registry, memory, and
human/agent workflow decisions.

`thegent-sharecli` is source evidence only. New implementation work goes to
`sharecli`.

## Contract Surfaces

| Contract          | Producer                                   | Consumer                                          | Current evidence                                                        | Target owner |
| ----------------- | ------------------------------------------ | ------------------------------------------------- | ----------------------------------------------------------------------- | ------------ |
| Process lifecycle | `sharecli`                                 | `thegent` high-level CLI / governance adapters    | `sharecli/src/runtime.rs`, `sharecli/src/commands/mod.rs`               | `sharecli`   |
| Harness health    | `sharecli`                                 | `thegent.mesh` status and governance checks       | `sharecli/src/monitoring.rs`, `thegent` mesh observability              | `sharecli`   |
| Queue             | `sharecli`                                 | `thegent.mesh.MeshManager`, CLI task commands     | `src/thegent/mesh/task_queue.py`                                        | `sharecli`   |
| Merge             | `sharecli`                                 | git/worktree execution and governance evidence    | `src/thegent/mesh/smart_merge.py`, `merge.py`                           | `sharecli`   |
| Worktree          | `sharecli`                                 | parallel agent work allocation                    | `src/thegent/mesh/git_parallelism.py`, `src/thegent_gitops/`            | `sharecli`   |
| Execution safety  | `sharecli` emits; `thegent` decides policy | policy gates, sandbox tier checks, audit evidence | `src/thegent/mesh/sandbox.py`, `resources.py`, `crates/harness-native/` | split        |

## Process Lifecycle Contract

Minimum operations:

| Operation                            | Required behavior                                                                    |
| ------------------------------------ | ------------------------------------------------------------------------------------ |
| `list(filter)`                       | Return managed process records filtered by project, harness, pid, or all.            |
| `start(project, harness, cwd, args)` | Start a process in a known project context and return pid plus metadata.             |
| `stop(selector, mode)`               | Stop only selected managed processes; never kill unrelated agent/terminal processes. |
| `status(verbose)`                    | Return process counts, memory, pool status, and degraded conditions.                 |
| `prune(idle_threshold, dry_run)`     | Report or stop idle managed processes according to policy input.                     |

Minimum record fields:

| Field                        | Meaning                             |
| ---------------------------- | ----------------------------------- |
| `pid`                        | OS process id.                      |
| `name`                       | Process executable or display name. |
| `project`                    | Registered project name, if known.  |
| `harness`                    | Harness/runtime kind, if known.     |
| `cmd`                        | Command vector for diagnostics.     |
| `memory_mb`                  | Current memory estimate.            |
| `started_at` or `start_time` | Process start timestamp.            |
| `status`                     | running, idle, stopped, or error.   |

Acceptance gates:

- `sharecli` tests prove lifecycle commands do not target unmanaged processes.
- `thegent` adapters can call lifecycle operations without importing
  `sharecli` internals.
- Stop/prune behavior is policy-gated by `thegent` before any destructive
  operation.

## Harness Health Contract

Minimum operations:

| Operation            | Required behavior                                             |
| -------------------- | ------------------------------------------------------------- |
| `health()`           | Report sharecli runtime availability and degraded reasons.    |
| `pool_status()`      | Report shared runtime pool totals and idle counts.            |
| `queue_depth()`      | Report per-queue new/cur/stale counts once queue moves.       |
| `resource_summary()` | Report total memory, high-water warnings, and process counts. |

Minimum record fields:

| Field               | Meaning                                         |
| ------------------- | ----------------------------------------------- |
| `healthy`           | Boolean health state.                           |
| `version`           | sharecli version.                               |
| `runtime_available` | Whether process runtime can spawn/list/stop.    |
| `degraded_reasons`  | Stable strings suitable for governance reports. |
| `last_check`        | Last health check timestamp.                    |

Acceptance gates:

- `thegent mesh status` can present sharecli health through an adapter.
- The health contract has a degraded state, not only pass/fail.
- Status collection never requires process termination.

## Queue Contract

Minimum operations:

| Operation                    | Required behavior                                                   |
| ---------------------------- | ------------------------------------------------------------------- |
| `enqueue(payload, priority)` | Atomically add a task and return an id.                             |
| `claim(owner)`               | Atomically move one ready task to in-flight ownership.              |
| `ack(task_id)`               | Idempotently mark in-flight task complete.                          |
| `requeue(task_id, reason)`   | Return in-flight task to ready queue with updated attempt metadata. |
| `list(state)`                | List ready, in-flight, stale, or all tasks.                         |
| `stale(now, threshold)`      | Identify in-flight tasks older than threshold.                      |

Minimum envelope fields:

| Field        | Meaning                                                               |
| ------------ | --------------------------------------------------------------------- |
| `id`         | Stable task id.                                                       |
| `payload`    | JSON-serializable task payload.                                       |
| `priority`   | Lower number is higher priority unless superseded by a future policy. |
| `created_at` | Creation timestamp.                                                   |
| `attempts`   | Claim/retry count.                                                    |
| `owner`      | Current owner, if claimed.                                            |
| `claimed_at` | Claim timestamp, if claimed.                                          |

Acceptance gates:

- Existing `tests/mesh/test_task_queue.py` behavior is ported or preserved by
  adapter tests.
- Atomic delivery and claim semantics remain crash-recoverable.
- thegent no longer imports queue implementation after compatibility sunset.

## Merge Contract

Minimum operations:

| Operation                                 | Required behavior                                        |
| ----------------------------------------- | -------------------------------------------------------- |
| `configure(repo, mode)`                   | Configure merge driver or report unsupported state.      |
| `merge(base, ours, theirs, output, path)` | Run structural merge with deterministic fallback policy. |
| `detect_conflicts(repo)`                  | Return unresolved conflict paths and metadata.           |
| `record_result(result)`                   | Emit evidence for governance and audit surfaces.         |

Minimum result fields:

| Field                   | Meaning                                               |
| ----------------------- | ----------------------------------------------------- |
| `success`               | True when no unresolved conflicts remain.             |
| `conflicts`             | Conflict path list.                                   |
| `output`                | Tool stdout/stderr summary.                           |
| `tool`                  | mergiraf, git-merge-file, or other configured driver. |
| `used_structural_merge` | Whether an AST-aware merge tool handled the merge.    |

Acceptance gates:

- Existing `tests/mesh/test_smart_merge.py` and `tests/mesh/test_merge.py`
  behavior is preserved.
- Fallback policy is explicit and test-covered; no silent degradation.
- thegent consumes merge evidence through adapter records.

## Worktree Contract

Minimum operations:

| Operation                       | Required behavior                                             |
| ------------------------------- | ------------------------------------------------------------- |
| `allocate(repo, owner, branch)` | Create or reserve a worktree for an owner.                    |
| `release(worktree_id, outcome)` | Release, clean, or quarantine a worktree.                     |
| `status(worktree_id)`           | Report branch, path, dirty state, and owner.                  |
| `queue_conflict(record)`        | Persist conflict records for later human or agent resolution. |
| `list(repo, state)`             | List active, idle, dirty, and quarantined worktrees.          |

Minimum record fields:

| Field    | Meaning                                     |
| -------- | ------------------------------------------- |
| `id`     | Worktree allocation id.                     |
| `repo`   | Repository path or registered project id.   |
| `path`   | Worktree path.                              |
| `branch` | Branch/ref checked out.                     |
| `owner`  | Agent or process owner.                     |
| `state`  | active, idle, dirty, released, quarantined. |

Acceptance gates:

- Existing `tests/mesh/test_git_parallelism.py`, `tests/unit/test_git_parallelism.py`,
  and `tests/mesh/test_worktree.py` behaviors are preserved or mapped.
- Conflict queue records are durable and inspectable.
- thegent governance can deny allocation before sharecli mutates git state.

## Execution Safety Contract

Minimum operations:

| Operation                                 | Required behavior                                                                  |
| ----------------------------------------- | ---------------------------------------------------------------------------------- |
| `evaluate_request(command, cwd, context)` | Produce sandbox/resource requirements for a command request.                       |
| `execute(request)`                        | Execute within the selected policy envelope, after thegent approval when required. |
| `emit_audit(record)`                      | Emit structured execution evidence.                                                |
| `purify(context)`                         | Clean task-local temporary state without touching active agents or terminals.      |

Minimum record fields:

| Field          | Meaning                                           |
| -------------- | ------------------------------------------------- |
| `command`      | Command vector or logical operation.              |
| `cwd`          | Working directory.                                |
| `sandbox_tier` | Selected sandbox/resource tier.                   |
| `limits`       | CPU, memory, process, and time limits.            |
| `policy_ref`   | thegent policy decision id or evidence reference. |
| `exit_status`  | Execution result after completion.                |

Acceptance gates:

- sharecli never independently decides governance approval.
- thegent never shells directly into substrate mechanics when a sharecli
  contract exists.
- Purification is non-destructive and excludes active agent/terminal processes.

## Compatibility and Sunset Rules

| Compatibility name      | Decision                                                           |
| ----------------------- | ------------------------------------------------------------------ |
| `thegent-sharecli`      | No new implementation. Use as concept archive only.                |
| `heliosShield`          | Keep as temporary compatibility wording until adapter names exist. |
| `thegent.mesh.*`        | Keep temporary import shims only after implementation moves.       |
| `thegent_gitops.*`      | Move or shim behind sharecli worktree contract.                    |
| `crates/harness-native` | Move or mirror into sharecli native runtime ownership.             |

## Owner-Side Test Mapping

| Contract           | Current thegent tests to preserve                                                                                                       | Owner-side tests to add in sharecli                                                             |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Process lifecycle  | `tests/mesh/test_process_detection.py`, `tests/mesh/test_observability.py`                                                              | Managed-process list/start/stop/status/prune tests that prove unmanaged processes are excluded. |
| Harness health     | `tests/mesh/test_observability.py`, mesh status command tests                                                                           | `health`, `pool_status`, and degraded-state tests over `SharedRuntime` and monitoring reports.  |
| Queue              | `tests/mesh/test_task_queue.py`, queue paths in `tests/mesh/test_process_detection.py`                                                  | Atomic enqueue/claim/ack/requeue/stale tests under the sharecli-owned queue module.             |
| Merge              | `tests/mesh/test_smart_merge.py`, `tests/mesh/test_merge.py`                                                                            | Structural merge, conflict detection, evidence-record, and explicit fallback-policy tests.      |
| Worktree           | `tests/mesh/test_git_parallelism.py`, `tests/unit/test_git_parallelism.py`, `tests/mesh/test_worktree.py`, `tests/mesh/test_git.py`     | Worktree allocate/release/status/conflict-queue tests plus gitops compatibility tests.          |
| Execution safety   | `tests/mesh/test_sandboxing.py`, `tests/mesh/test_resources.py`, `tests/mesh/test_injection.py`                                         | Sandbox/resource envelope, audit-record, purification, and no-agent-termination tests.          |
| Governance adapter | `tests/unit/governance/test_heliosShield_bridge.py`, `tests/test_integration_teammates_heliosShield.py`, `tests/test_unit_teammates.py` | No sharecli governance tests; sharecli emits records, thegent decides approval.                 |

Sunset can start only when:

1. Contract tests exist on both producer and consumer sides.
2. `thegent` imports adapters rather than implementation modules.
3. `sharecli` has an owner-side boundary document or migration plan.
4. CI or task quality has the staged boundary drift check described in
   `docs/specs/contracts/sharecli-boundary-drift-check.md`.

## Verification Matrix

| Requirement                                 | Evidence to add before code movement                                                                                                     |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| thegent consumes sharecli process lifecycle | Adapter tests for status/start/stop/prune dry-run.                                                                                       |
| Queue semantics preserved                   | Ported queue tests plus thegent shim tests.                                                                                              |
| Merge semantics preserved                   | Ported smart merge tests plus evidence adapter tests.                                                                                    |
| Worktree semantics preserved                | Ported worktree/git-parallelism tests plus conflict queue tests.                                                                         |
| Execution safety split respected            | Boundary drift reporter/test rejecting new direct execution-substrate imports in thegent governance/CLI after each lane's adapter lands. |
| Compatibility sunset is trackable           | Dedicated checklist in the audit and sharecli-side boundary doc.                                                                         |
