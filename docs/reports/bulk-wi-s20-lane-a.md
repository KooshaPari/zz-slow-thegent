### [WL-6520] Tighten selective settings projection semantics for provider consumers

**Source Path+Line:** [thegent/src/thegent/config_provider.py:28]
**Acceptance Checklist:**

- [ ] Ensure `_settings_to_dict` emits only explicitly requested keys while preserving stable key ordering.
- [ ] Add tests for `None`, empty, and unknown-key inputs to lock behavior.
- [ ] Verify no regression for callers relying on full-settings snapshots.
      **Notes:** Keep implementation constrained to projection logic and avoid mutating global settings state.

### [WL-6521] Normalize shared-server initialization payload across startup paths

**Source Path+Line:** [thegent/src/thegent/shared_server_integration.py:21]
**Acceptance Checklist:**

- [ ] Standardize success and degraded-start response fields returned by `initialize_shared_servers_for_session`.
- [ ] Add tests for language filtering and custom project-root initialization.
- [ ] Preserve backward compatibility for downstream session bootstrap callers.
      **Notes:** Focus on deterministic payload shape so orchestration decisions are branch-safe.

### [WL-6522] Define deterministic dequeue behavior and empty-queue handling in task queue core

**Source Path+Line:** [thegent/src/thegent/task_queue/queue.py:10]
**Acceptance Checklist:**

- [ ] Codify FIFO guarantees under mixed enqueue/dequeue operation sequences.
- [ ] Add tests covering empty-queue reads and repeated dequeue calls after drain.
- [ ] Document queue contract for task IDs and payload integrity across operations.
      **Notes:** Keep scope local to `TaskQueue` semantics without changing external scheduler APIs.

### [WL-6523] Reduce watcher noise by enforcing spec-aware event acceptance at handler edge

**Source Path+Line:** [thegent/src/thegent/native/watcher_daemon.py:152]
**Acceptance Checklist:**

- [ ] Ensure `_SpecHandler` ignores filesystem events outside configured include/exclude patterns.
- [ ] Add tests for overlapping glob rules and duplicate event suppression.
- [ ] Confirm event delivery ordering remains stable for accepted events.
      **Notes:** Prioritize low-noise signaling to reduce unnecessary downstream processing churn.

### [WL-6524] Harden read-through fallback and stale-entry semantics in multi-level cache get path

**Source Path+Line:** [thegent/src/thegent/cache/multi_level.py:74]
**Acceptance Checklist:**

- [ ] Enforce tier traversal order and consistent return behavior in `MultiLevelCache.get`.
- [ ] Add regression tests for stale memory entries and disk-tier fallback reads.
- [ ] Validate cache hit/miss accounting remains correct after fallback execution.
      **Notes:** Strengthen resilience while preserving existing cache interface and call signatures.

### [WL-6525] Make model promotion decisions auditable with explicit threshold handling

**Source Path+Line:** [thegent/src/thegent/learning/promotion.py:16]
**Acceptance Checklist:**

- [ ] Extract promotion thresholds into named constants or configuration-backed values.
- [ ] Add edge-case tests for tie boundaries and insufficient-signal rejection.
- [ ] Ensure promotion evaluation output stays schema-compatible for existing consumers.
      **Notes:** Keep changes centered on `evaluate_promotion` decision clarity and determinism.

### [WL-6526] Add fail-fast spec validation before infrastructure provisioning attempts

**Source Path+Line:** [thegent/src/thegent/infra/provisioner.py:32]
**Acceptance Checklist:**

- [ ] Validate `ResourceSpec` inputs before side-effectful provisioning logic runs.
- [ ] Return actionable errors that identify invalid resource IDs and failing fields.
- [ ] Add tests for mixed valid/invalid batches to prevent partial silent failures.
      **Notes:** Emphasize early rejection to reduce cleanup burden from mid-flight provisioning errors.

### [WL-6527] Enforce idempotent keepalive start/stop transitions in terminal keepalive manager

**Source Path+Line:** [thegent/src/thegent/infra/terminal_keepalive.py:387]
**Acceptance Checklist:**

- [ ] Guard `start` against duplicate worker initialization when already running.
- [ ] Add lifecycle tests for repeated start/stop cycles and failure-triggered shutdown.
- [ ] Verify transport fallback behavior remains intact under restart pressure.
      **Notes:** Session reliability depends on deterministic lifecycle boundaries and thread ownership.

### [WL-6528] Strengthen rollback correctness guarantees for session turn history management

**Source Path+Line:** [thegent/src/thegent/session/manager.py:84]
**Acceptance Checklist:**

- [ ] Validate `rollback_session` behavior for boundary values and over-rollback requests.
- [ ] Add tests ensuring turn counts and persisted history remain consistent post-rollback.
- [ ] Preserve existing error taxonomy for invalid session IDs and rollback arguments.
      **Notes:** Keep rollback semantics explicit to avoid data loss during interactive recovery flows.

### [WL-6529] Improve conversation dump robustness for filesystem and serialization failure paths

**Source Path+Line:** [thegent/src/thegent/session/conversation_dumper.py:115]
**Acceptance Checklist:**

- [ ] Harden `dump_conversation` handling for directory-creation, write, and encoding failures.
- [ ] Add tests that pin filename generation and collision-handling behavior.
- [ ] Ensure dumped metadata remains complete for downstream audit tooling.
      **Notes:** Limit scope to dump path reliability without changing conversation data model contracts.
