<DONE>
# thegent: Pending Plans & Roadmap (2026 Integrated)

This document outlines the pending development tasks for `thegent` framework, integrating the **AGSLAG (2025)** research swathes and **Feb 2026 Deep Research Protocol (DRP)** updates.

## Phase 1: High-Speed Foundation (Next 2 Weeks)

- [ ] **Wasm Tool Sandboxing**: Replace standard `subprocess` calls with **Extism (WebAssembly)** sandboxes for "fast-path" tools (e.g., regex, linting, parsing). Goal: <50ms tool overhead.
- [ ] **Pydantic V2 JIT Migration**: Implement JIT-compiled validation for tool schemas to support registries with 500+ tools without discovery latency.
- [ ] **Zsh "Slim-Shell" Mode**: Create a minimal Zsh environment for agents that loads in <30ms (based on Zsh-for-humans patterns).
- [ ] **Native Rust Toolchain**: Preference `fd`, `rg`, `sd`, and `ruff` for all internal framework operations.

## Phase 2: Autonomous Intelligence (Weeks 3-5)

- [ ] **Central Router Implementation**:
  - Semantic search over registered MCP servers.
  - Dynamic tool injection into agent context based on task classification.
  - Bypasses the 128-tool limit by only showing tools "relevant to the current turn."
- [ ] **AI Scratchpad & Context History**:
  - Implement a shell-integrated buffer for multi-turn command drafting.
  - Build a context-aware history search (Semantic search over past CLI tasks).
- [ ] **Hierarchical Memory (MemoryMesh v2)**:
  - **Working**: Turn-based state.
  - **Episodic**: Log of attempts/failures to prevent reasoning loops.
  - **Semantic**: Persistent Knowledge Graph stored in a local vector-graph DB (Mem0 pattern).
- [ ] **Swarm Communication Hub**: P2P and Broadcast messaging for sub-agents (e.g., `thegent research` can spawn `scout` agents that report back to a `coordinator`).

## Phase 3: SOTA Connectivity (Weeks 6-8)

- [ ] **MCP Async Streaming**: Migrate from STDIO to **Async WebSocket** transport.
- [ ] **Sampling & Notifications**: Implement standard handlers for agents to request HITL feedback (Sampling) or broadcast state changes (Notifications) across the swarm.
- [ ] **Senior Dev Indexing**: Auto-generate "Codebase Blueprints" using tree-sitter + LLM summarization.

## Research-Driven Enhancements

| Feature            | Pattern Source            | 2026 Update                 |
| :----------------- | :------------------------ | :-------------------------- |
| **Tool Discovery** | Central Router (AGSLAG)   | Semantic JIT Validation     |
| **Sandboxing**     | Containerization (Jarvis) | Wasm / Firecracker MicroVMs |
| **Memory**         | MemoryMesh (AGSLAG)       | Dynamic Pruning & Weighting |
| **Swarm**          | Agent Manager (AGSLAG)    | Async Sampling Protocol     |

---

_Status: Ready for Phase 1 Execution._
