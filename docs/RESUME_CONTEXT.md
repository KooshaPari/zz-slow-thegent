# Agent Resume Context: Ultra-Parity 2026

## Status Overview

We have completed the foundational phases (Zero-Fork, Harness, Plugin Compiler, UI Resilience, Spark Bridge, and SSH Teleportation). We have now transitioned into the **Intelligence Mesh** phase (Phase H), integrating local high-performance services and drafting agent protocols.

## Current Goal

Complete z-obj (Phase K.1), then Z-MCP bridge. ls hang fixed (see below).

## Task List

1. **Phase A**: Refactor `.zshrc` and `.zshenv` to use 100% Zsh built-ins. [COMPLETED]
2. **Phase B**: Update harness interaction for "Skip-Init" mode. [COMPLETED]
3. **Phase D**: Build the "Plugin Compiler". [COMPLETED]
4. **Phase E-G**: UI Resilience, Spark Bridge, Atuin, Teleport. [COMPLETED]
5. **Phase H**: Intelligence Mesh (MCP, NATS, Neo4j, PG.ai Specifications). [COMPLETED]
6. **Phase K.1**: z-obj structured output shim. [IN_PROGRESS] — Binary at `~/.local/bin/z-obj`; test hung (debug needed).
7. **Phase I**: Implementation of Zsh MCP Server (Z-MCP). [PENDING]
8. **Phase J**: Integration of Z-Bus (NATS) and Z-Graph (Neo4j). [PENDING]

## Local Services Identified (Up & Usable)

- **Postgres 17** (5432): Target for pgai/pgvector.
- **NATS** (4222): Target for agent coordination (Z-Bus).
- **Redis** (6379): Target for caching.
- **Neo4j** (7474): Target for graph knowledge (Z-Graph).
- **Temporal** (7233): Target for workflow orchestration.
- **Minio** (9000): Target for S3-compatible storage.
- **Loki** (3100): Target for log aggregation.

## Reference Specifications

- **Master plan**: `docs/ULTRA_PARITY_EXPANDED_PLAN.md` (expanded phases, research, DAG)
- PRD: `docs/ULTRA_PARITY_PRD.md`
- Zsh MCP Spec: `docs/ZSH_MCP_SERVER_SPEC.md`
- Neo4j Graph Spec: `docs/NEO4J_GRAPH_SPEC.md`
- NATS Event Mesh Spec: `docs/NATS_EVENT_MESH_SPEC.md`

## Implementation Strategy

- Use `zmodload zsh/parameter` in Z-MCP for zero-fork state access.
- Bridge Zsh `preexec`/`precmd` to NATS (Z-Bus) via Go shim.
- Stream agent actions to Neo4j (Z-Graph) for long-term memory.

## Fix: ls Hang (2026-02-17)

**Root cause**: (1) Harness coalesce for `ls` caused lock contention. (2) ultra-shim routed `ls` to `eza --git`, which runs git in each dir and can hang 4m+ in large repos.
**Fixes applied**:

- `rules.conf`: Changed `ls` from coalesce to passthrough.
- `~/.local/bin/ultra-shim.go`: Use plain `ls` when agent context OR when stdout is a pipe (e.g. `ls | z-obj`). Rebuilt binary.
