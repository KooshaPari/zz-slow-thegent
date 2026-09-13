# Contract Upgrade Playbook

**Status:** Authoritative
**Date:** 2026-02-14
**Scope:** Contract version upgrades, canary rollout, dual mode, rollback (G-RV-08)

---

## 1. Purpose

This playbook defines the operational process for upgrading contract versions (e.g., task-tool-18 → task-tool-20, csm-v1 → csm-v2). It covers dual-read/dual-write migration, canary rollout, and rollback steps.

---

## 2. Prerequisites

- **Contract registry** updated with new version and compatibility matrix (`src/thegent/contracts/registry.py`)
- **MigrationController** evaluates version status (`thegent govern migration <contract_id> <version>`)
- **Telemetry** in place for drift detection (`thegent observe drift`)
- **Fallback policy** configured per `docs/contracts/FALLBACK_POLICY.md`

---

## 3. Dual-Read / Dual-Write Migration

Use this pattern when introducing a new contract version that coexists with the old one.

### 3.1 Phases

| Phase           | Read                     | Write                 | Duration                   |
| --------------- | ------------------------ | --------------------- | -------------------------- |
| **Dual-read**   | Accept old + new formats | Emit old only         | Until adapters support new |
| **Dual-write**  | Accept old + new         | Emit both old and new | Adoption ramp              |
| **Cutover**     | Accept new only          | Emit new only         | After adoption threshold   |
| **Deprecation** | Reject old               | Emit new only         | After migration window     |

### 3.2 Implementation

1. **Register new version** in `ContractRegistry` with `compatible_with` including the old version.
2. **Add adapter** that normalizes both old and new to canonical schema.
3. **Set `migration_window_end`** on the old version (ISO date) when it will be rejected.
4. **Run `thegent govern migration <contract_id> <version>`** to verify status.

### 3.3 Example

```python
# In registry: add task-tool-20, deprecate task-tool-18 with window
ContractVersion(
    contract_id="task-tool",
    version="task-tool-20",
    description="Task-tool 20-tag XML (extended)",
    compatible_with=("task-tool-18", "csm-v1"),
)
ContractVersion(
    contract_id="task-tool",
    version="task-tool-18",
    deprecated=True,
    migration_window_end="2026-04-01",  # After this, old version rejected
)
```

---

## 4. Canary Rollout

Progressive traffic ramp for new contract versions.

### 4.1 Stages

| Stage        | Traffic %     | Observation                  | Promotion Criteria  |
| ------------ | ------------- | ---------------------------- | ------------------- |
| **Shadow**   | 0% (log only) | Compare old vs new output    | No errors in shadow |
| **Canary 1** | 1–5%          | Monitor drift, fallback rate | Drift within budget |
| **Canary 2** | 10–25%        | Same                         | No regression       |
| **Canary 3** | 50%           | Same                         | SLO met             |
| **Full**     | 100%          | Same                         | —                   |

### 4.2 Configuration

Use environment or config to control canary percentage:

- `THGENT_CONTRACT_CANARY_PERCENT` (0–100): Percentage of runs using new version.
- `THGENT_CONTRACT_CANARY_PROVIDERS`: Comma-separated providers in canary (empty = all).

### 4.3 Checks Before Promotion

1. `thegent observe drift --structural-budget 5 --semantic-budget 10` — within budget.
2. `thegent govern conformance` — all adapters pass.
3. `thegent govern migration <contract_id> <version>` — allowed, status active.

---

## 5. Rollback Steps

### 5.1 Rollback Triggers

| Trigger                        | Action                                        |
| ------------------------------ | --------------------------------------------- |
| Structural drift rate > budget | Pause canary, revert to old version           |
| Semantic drift rate > budget   | Pause canary, investigate                     |
| Fallback rate spike            | Revert, check adapter                         |
| Conformance suite failure      | Block promotion, fix adapter                  |
| Migration window expired       | Old version rejected; ensure cutover complete |

### 5.2 Rollback Procedure

1. **Stop canary:** Set `THGENT_CONTRACT_CANARY_PERCENT=0` or disable canary in config.
2. **Revert registry:** If new version was promoted, mark deprecated and extend `migration_window_end` on old version.
3. **Restart services:** Ensure all processes pick up reverted config.
4. **Verify:** `thegent govern migration <contract_id> <old_version>` shows allowed.
5. **Post-mortem:** Capture drift events, adapter logs, and root cause.

### 5.3 Emergency Rollback

If production is impacted:

1. Set `THGENT_NORMALIZATION_POLICY_ALLOW_FALLBACK=true` (if not already) to allow plain-text fallback.
2. Disable canary immediately.
3. Notify on-call; follow incident playbook.
4. After stability, perform full rollback procedure above.

---

## 6. CLI Reference

| Command                                            | Purpose                                 |
| -------------------------------------------------- | --------------------------------------- |
| `thegent govern migration <contract_id> <version>` | Evaluate migration status for a version |
| `thegent govern migration --format json`           | JSON output for automation              |
| `thegent govern contracts`                         | List all contract versions              |
| `thegent observe drift`                            | Check drift and alert budgets           |
| `thegent govern conformance`                       | Run adapter conformance suite           |

---

## 7. Checklist: New Contract Version

- [ ] Register new version in `ContractRegistry` with compatibility.
- [ ] Add or update adapter in `contracts/adapters.py`.
- [ ] Set `migration_window_end` on deprecated version.
- [ ] Run conformance: `thegent govern conformance`
- [ ] Enable shadow/canary with low percentage.
- [ ] Monitor `thegent observe drift` during ramp.
- [ ] Document rollback steps for this version.
- [ ] After cutover, remove old version from active use.

---

## 8. Related Documents

- `docs/contracts/CONTRACT_AUTHORITY.md` — Contract registry and schema
- `docs/contracts/FALLBACK_POLICY.md` — Fallback control plane
- `docs/VERIFICATION_RUNBOOK.md` — General verification checklist
