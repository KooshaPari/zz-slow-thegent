# State-Aware Orchestration Design

**Status:** Design
**Date:** 2026-02-14
**Scope:** State persistence, interruption/resume, continuity packets (G-KD-03)

---

## 1. Purpose

Enable multi-step workflows with explicit state persistence, interruption/resume semantics, and continuity packets for handoff. Aligns with Zen `ctx.set_state/get_state()` patterns and Kush docs D-C.

---

## 2. Current State

| Component | Location | Purpose |
|-----------|----------|---------|
| **RunRegistry** | `execution.py` | Persists run start/finish/feedback to `run_registry.jsonl`; hash chaining for audit |
| **CheckpointRegistry** | `execution.py` | Persists DAG checkpoints (reason, dag_content, owner) to `checkpoint_registry.jsonl` |
| **session_dir** | `.thegent/sessions` | Root for run logs, registry, checkpoints |
| **dag checkpoint** | CLI | `thegent dag checkpoint`, `thegent dag rollback`, `thegent dag checkpoints` |
| **Auto-checkpoint** | CLI | On DAG status change (terminal task), creates checkpoint |

**Gap:** Run-level pause/resume, continuity packets, and explicit interruption semantics are not implemented.

---

## 3. Target Capabilities

### 3.1 State Persistence for Multi-Step

- **Run state:** Extend RunRegistry to track `running | paused | completed | failed`.
- **Checkpoint format:** Add `run_id`, `phase`, `progress`, `continuity_snapshot` to checkpoint schema.
- **Resume from checkpoint:** `thegent run --resume-from <checkpoint_id>` restores context and continues.

### 3.2 Interruption / Resume

- **Pause:** Operator or policy triggers pause; run state → `paused`; checkpoint created with continuity packet.
- **Resume:** `thegent run --resume <run_id>` or `thegent dag resume --run <run_id>` restores from last checkpoint.
- **Idempotent semantics:** Resume only from valid ready frontier (no duplicate dispatch).

### 3.3 Continuity Packets

Structured handoff format for owner transition:

```json
{
  "continuity_packet_id": "cp_abc123",
  "run_id": "run_xyz",
  "created_at_utc": "2026-02-14T12:00:00Z",
  "phase": "operator",
  "progress": 0.65,
  "summary": "Completed steps 1–3; step 4 in progress",
  "next_action": "resume_ready_frontier",
  "unresolved_risks": [],
  "owner": "alice",
  "handoff_to": "bob"
}
```

---

## 4. Phased Implementation

### Phase 1: Run State Extension (Low Effort)

- Add `run_state` to RunRegistry events: `running`, `paused`, `completed`, `failed`.
- Add `register_pause(run_id, reason, continuity_snapshot)` and `register_resume(run_id)`.
- No CLI changes yet; prepare data model.

### Phase 2: Continuity Packet Schema

- Define `ContinuityPacket` dataclass in `execution.py`.
- Store in checkpoint or new `continuity_registry.jsonl`.
- `thegent dag checkpoint` optionally emits continuity packet.

### Phase 3: Pause / Resume CLI

- `thegent run --pause` (when running) → create checkpoint + continuity packet, set run_state=paused.
- `thegent run --resume <run_id>` → load checkpoint, restore context, continue dispatch.
- MCP: `thegent_pause_run(session_id)`, `thegent_resume_run(session_id)`.

### Phase 4: MCP Context Integration

- When FastMCP supports `ctx.set_state`/`ctx.get_state`, wire run state and continuity snapshot.
- Progress+confidence snapshots in `ctx.report_progress()` payload.

---

## 5. Interface Sketch

```python
# execution.py extensions
class RunState(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


def register_pause(self, run_id: str, reason: str, continuity: dict) -> None: ...
def register_resume(self, run_id: str) -> None: ...
def get_run_state(self, run_id: str) -> RunState | None: ...
```

---

## 6. References

- Kush docs: `docs/docset/thegent-kush-docs-deep-dive-2026-02-14.md` (D-C)
- Zen: `ctx.set_state`/`ctx.get_state` for multi-phase continuity
- PRD: `docs/docset/thegent-orchestration-optimization-prd.md` (pause/resume, continuity)
- Gap analysis: G-KD-03
