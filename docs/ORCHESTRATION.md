# Thegent Orchestration Optimization Program (v1.0)

This document summarizes the unified orchestration architecture implemented for `thegent`.

## Core Features

### 1. Unified Execution Lifecycle (Phase 1)

- **Run IDs & Correlation**: Every action is tracked with a unique `run_id` and optional `correlation_id`.
- **Run Registry**: A persistent JSONL store of all execution metadata, including start/end events, durations, and exit codes.
- **Telemetry Contracts**: Standardized fields for agent, model, lane, and confidence.

### 2. Dependency-aware DAG Orchestration (Phase 1 & 2)

- **Routing Engine**: Executes tasks in parallel based on their dependencies.
- **Quorum & Arbitration**: Supports multi-agent consensus for critical tasks.
- **Confidence-aware Routing**: Automatically escalates low-confidence tasks to 2-agent quorum.
- **Evidence Capture**: Every completed task links to its execution record (session ID).

### 3. Resilience & Self-healing (Phase 2 & 5)

- **Adaptive Retries**: Exponential backoff for transient failures (e.g., rate limits).
- **Circuit Breakers**: Prevents cascading failures by isolating unstable agents or models.
- **Checkpoint/Rollback**: Immutable point-in-time snapshots of DAG state.
- **Auto-Reconciliation**: Automatically recovers from crashes by syncing DAG state with live OS processes on restart.

### 4. Governance & Security (Phase 3)

- **Policy Engine**: Enforces rules based on environment (e.g., trust score gates in production).
- **Signed Artifacts**: Cryptographic signatures ensure the integrity of the run registry.
- **Immutable Audit Trail**: Verifiable history of all orchestration actions.
- **Governance Overrides**: Authorized bypass for critical recovery with mandatory rationale.

### 5. Operator Cockpit & UX (Phase 4)

- **Cockpit Summary**: High-level overview of session health and resource states.
- **Decision Replay**: Detailed rationales stored for every execution failure.
- **One-click Fallbacks**: Simplified recovery through automated agent swapping.
- **Feedback Loops**: Operator-driven confidence calibration.

## CLI Command Reference

| Command                    | Description                             |
| -------------------------- | --------------------------------------- |
| `thegent cockpit`          | High-level orchestration health summary |
| `thegent history list`     | View recent execution runs              |
| `thegent history verify`   | Audit registry integrity                |
| `thegent dag run`          | Execute DAG with auto-reconciliation    |
| `thegent dag sync --watch` | Health-monitoring loop for active tasks |
| `thegent dag checkpoint`   | Create state snapshot                   |
| `thegent benchmark`        | Latency and success rate metrics        |
| `thegent archive`          | Cleanup old session data                |

## Status: v1.0 Ready

The orchestration program is fully integrated, hardened, and ready for production use.

---

## See also

- [WORK_STREAM.md](reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](plans/00-MASTER-INDEX.md) — plan index
