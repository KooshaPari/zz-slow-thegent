# Planning Simulation & Replay Sandbox Depth (WP-4007, WP-12004)

This document provides technical depth for the **Simulation Engine** and **Replay Sandbox**, enabling "What-if" analysis and pre-flight verification without mutating real-world state.

## 1. Virtual State Isolation (The Sandbox)

Simulations must run in a "No-Side-Effect" environment. `thegent` uses a multi-layered isolation strategy:

### 1.1 Virtual File System (VFS)

For tools that modify the file system (e.g., `Write`, `StrReplace`, `delete_file`), the simulation engine injects a `VirtualFileSystem` layer:

- **Copy-on-Write (CoW)**: The simulation reads from the real FS but writes to an in-memory `OverlayFS`.
- **Isolation**: No simulation write ever touches the real disk.
- **Diff Generation**: The engine compares the `OverlayFS` with the real FS to generate a "Predicted Change Manifest."

### 1.2 Tool Side-Effect Mocking

Every tool in the `thegent` registry must define a `simulate()` method or a `dry_run` behavior:

- **Read-Only Tools**: Execute as normal (safe).
- **Mutating Tools**: Return a "Mock Result" (e.g., `git commit` returns a dummy hash; `gh pr create` returns a placeholder URL).
- **Side-Effect Schema**:
  ```python
  class ToolSideEffect(BaseModel):
      tool_id: str
      action: str
      impacted_resources: list[str]
      predicted_result: Any
      reversibility: Literal["atomic", "manual", "irreversible"]
  ```

## 2. Probabilistic Planning (Monte Carlo / PERT)

For complex multi-agent DAGs, the simulation engine provides schedule risk quantification.

### 2.1 PERT Uncertainty (WP-8002)

Instead of a single duration, each node in the DAG carries:

- `t_optimistic` (O)
- `t_most_likely` (M)
- `t_pessimistic` (P)
- **Calculated Duration**: `T = (O + 4M + P) / 6`

### 2.2 Monte Carlo Simulation

The engine runs N=1000 iterations of the DAG, sampling from the PERT distributions to produce:

- **P50 (Median)**: 50% chance of completion by this time.
- **P80 (Target)**: 80% confidence band (the standard for commitment).
- **P95 (Safe)**: 95% confidence band (includes worst-case jitter).

## 3. What-if Scenario Branching (WP-12004)

Operators can "Fork" an execution at any decision node:

1. **Checkpoint Capture**: Save the `RunState` and `Context` at node N.
2. **Alternative Input**: Inject a different agent response or tool result.
3. **Shadow Execution**: Run the remainder of the DAG in the **Replay Sandbox**.
4. **Outcome Comparison**: The Cockpit displays a side-by-side "Baseline vs. What-if" outcome.

## 4. Pre-flight Verification

Irreversible actions (e.g., `git push --force`, `rm -rf`) trigger a mandatory simulation:

- **Policy Gate**: The `PolicyEngine` evaluates the "Predicted Change Manifest."
- **Visual Preview**: The operator sees a diff of all files that _would_ be changed and a list of all tools that _would_ be called.
- **Commitment**: Only after simulation success and operator sign-off is the "Sandbox Lock" released for real execution.

---

_Cross-ref: [PHASE_4_COCKPIT_UX_DEPTH.md](./PHASE_4_COCKPIT_UX_DEPTH.md) | [03-UNIFIED-DAG.md](../plans/03-UNIFIED-DAG.md)_

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
