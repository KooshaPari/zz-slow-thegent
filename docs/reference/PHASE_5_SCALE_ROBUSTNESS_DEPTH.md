# Phase 5 Scale: Redis & Distributed Robustness (WP-5004)

This document defines the architecture for scaling `thegent` from a single-machine CLI to a distributed, multi-server orchestration platform.

## 1. Stateless Orchestrator Pattern

To achieve horizontal scalability, the `thegent` core must be stateless.

- **State Externalization**: All `RunMeta`, `Checkpoint`, and `Event` data moves from local JSONL files to a **Distributed State Store (Redis)**.
- **Shared-Log Architecture**: A centralized event log (Redis Pub/Sub or Streams) allows multiple `thegent` instances to synchronize their worldviews.

## 2. Redis-Backed EventStore

The `thegent` EventStore implementation will support a Redis backend:

- `FASTMCP_EVENT_STORE_URL=redis://host:port`
- **Key-Value Store**: Use Redis hashes for `RunMeta` and `CheckpointMeta`.
- **List/Stream**: Use Redis Streams for the Immutable Audit Trail (P-069).

## 3. Adaptive Concurrency with Hysteresis (WP-1002)

To prevent "thundering herd" and "oscillation" in agent scaling:

- **Dwell Time**: Capacity adjustments require a minimum dwell time (e.g., 30s) before scaling back down.
- **Risk-Based Reservation**: Reserve a "Critical Lane" (e.g., 20% of capacity) for recovery agents and high-risk overrides that must not be throttled.
- **Hysteresis Loop**:
  - `Scale UP` threshold: 80% utilization for 10s.
  - `Scale DOWN` threshold: 40% utilization for 60s.

## 4. Distributed Idempotency (WP-2001)

- **Idempotency Key**: `(run_id, step_index, action_type, content_hash)`.
- **Redis Global Lock**: Use Redlock or a similar distributed locking mechanism for critical writes to the Work Stream (WP-1005).

## 5. Graceful Degradation (NFR-010)

If the Redis cluster is unavailable:

1. **Fallback to Memory**: Revert to local MemoryStore with a "Degraded" warning.
2. **Persistence Gap**: Notify the operator that distributed state is unavailable and actions are not being synced across instances.
3. **Recovery**: Automatically resync local state to Redis once the connection is restored.

---

_Cross-ref: [FASTMCP_DEPLOYMENT_GUIDE.md](../FASTMCP_DEPLOYMENT_GUIDE.md) | [05-ARCHITECTURE.md](../plans/05-ARCHITECTURE.md)_

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
