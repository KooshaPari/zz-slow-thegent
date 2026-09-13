### [WL-7500]

**Title:** Replace `SyncCommand` push subcommand stub contract with implemented behavior documentation
**Source:** [thegent/src/thegent/commands/sync.py:134]
**Acceptance checklist:**

- [ ] Update sync command contract/docs so `push` no longer advertises itself as stub-only behavior.
- [ ] Ensure implementation and help text describe actual transfer semantics and failure modes.
- [ ] Add tests asserting command help and runtime behavior remain aligned.
      **Notes:** Line 134 still labels `push` as "stubbed for now," which can drift from implemented behavior.

### [WL-7501]

**Title:** Remove stale stub language from `SyncCommand` pull subcommand definition
**Source:** [thegent/src/thegent/commands/sync.py:135]
**Acceptance checklist:**

- [ ] Replace pull subcommand documentation that claims stub-only behavior.
- [ ] Define expected backend integration contract for remote pull in command docs.
- [ ] Add tests validating pull command help text matches actual operational status.
      **Notes:** Line 135 marks `pull` as stubbed in the subcommand doc block.

### [WL-7502]

**Title:** Eliminate stub-only reset contract from sync subcommand surface
**Source:** [thegent/src/thegent/commands/sync.py:136]
**Acceptance checklist:**

- [ ] Update reset subcommand contract to reflect real destructive/non-destructive behavior.
- [ ] Document precise reset scope and rollback expectations for affected files.
- [ ] Add tests confirming command output and docs agree on reset behavior.
      **Notes:** Line 136 still describes `reset` as stubbed-for-now behavior.

### [WL-7503]

**Title:** Implement non-stub remote pull backend path in `SyncCommand.pull`
**Source:** [thegent/src/thegent/commands/sync.py:756]
**Acceptance checklist:**

- [ ] Replace the `[stub] Would pull state` success path with real remote retrieval and apply logic.
- [ ] Return per-file pull outcomes and backend error metadata in `OperationResult.details`.
- [ ] Add tests for successful pull, unreachable backend, and partial apply failures.
      **Notes:** Line 756 returns a stub message and does not execute an actual remote pull.

### [WL-7504]

**Title:** Implement real reset mutations instead of stub response in `SyncCommand.reset`
**Source:** [thegent/src/thegent/commands/sync.py:797]
**Acceptance checklist:**

- [ ] Replace stub-only summary messaging with concrete reset operations against local state.
- [ ] Track and report exact mutated files and rollback-safe metadata.
- [ ] Add tests for no-op reset, populated reset, and failure handling during destructive steps.
      **Notes:** Line 797 emits a stub message and explicitly avoids making destructive changes.

### [WL-7505]

**Title:** Complete PERT forward pass critical-path and float computation
**Source:** [thegent/src/thegent/planning/simulation.py:38]
**Acceptance checklist:**

- [ ] Implement dependency-aware forward/backward pass to compute critical path and total float.
- [ ] Validate expected duration and variance aggregation at plan level.
- [ ] Add tests covering branching graphs, parallel paths, and invalid predecessor references.
      **Notes:** Line 38 labels `pert_forward_pass` as a D1 stub and currently sets `critical_path=False` for all tasks.

### [WL-7506]

**Title:** Implement resource contention simulation for D2 planning overlays
**Source:** [thegent/src/thegent/planning/simulation.py:148]
**Acceptance checklist:**

- [ ] Replace empty-list return with overlap/window analysis for resource demand vs capacity.
- [ ] Emit deterministic contention records with affected tasks and contention ratios.
- [ ] Add tests for no-contention, single-resource saturation, and multi-resource contention cases.
      **Notes:** Line 148 marks D2 contention logic as stub and currently returns no findings.

### [WL-7507]

**Title:** Upgrade continuity risk scoring from D3 stub heuristic to calibrated model
**Source:** [thegent/src/thegent/planning/simulation.py:224]
**Acceptance checklist:**

- [ ] Implement calibrated continuity-risk scoring with explicit factor weighting and thresholds.
- [ ] Separate task-local risk accumulation from global risk totals to avoid cross-task bleed-through.
- [ ] Add tests for stale snapshots, owner-coverage gaps, and mixed-risk portfolios.
      **Notes:** Line 224 documents continuity scoring as a D3 stub with simplified heuristic behavior.

### [WL-7508]

**Title:** Implement persistent model tier mutation in `ModelPromoter._update_model_tier`
**Source:** [thegent/src/thegent/learning/promotion.py:24]
**Acceptance checklist:**

- [ ] Replace no-op `pass` with model catalog lookup and tier persistence logic.
- [ ] Record promotion audit metadata (old tier, new tier, trigger metrics, timestamp).
- [ ] Add tests for successful promotion, unknown model IDs, and idempotent re-promotions.
      **Notes:** Line 24 is a no-op `pass`, so promotion decisions are logged but not persisted.

### [WL-7509]

**Title:** Implement durable `PLAN_STATUS.md` writeback in plan system sync path
**Source:** [thegent/src/thegent/integration/plan_system.py:232]
**Acceptance checklist:**

- [ ] Replace placeholder comment path with a real file rewrite preserving existing PLAN_STATUS formatting.
- [ ] Ensure dependency/blocking updates round-trip without dropping unrelated sections.
- [ ] Add tests for save/load idempotency and concurrent update safety.
      **Notes:** Line 232 states full file rewrite is deferred, leaving `_save_plan_status` in-memory only.
