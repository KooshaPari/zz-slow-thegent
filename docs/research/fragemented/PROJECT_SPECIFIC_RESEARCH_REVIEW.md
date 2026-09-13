<DONE>
# Project-Specific Research Review: thegent | sharecli | trace

This document filters over 5,000+ research links and 50+ AGSLAG reports to identify only those implementation patterns and findings strictly relevant to the development of **thegent**, **sharecli**, and **trace**.

---

## 1. thegent (Agent Framework & Orchestration)

**Focus**: Bypassing tool limits, swarm communication, and deep research capability.

### 🚩 Critical AGSLAG Findings

- **Central Router Pattern**: Moving from monolithic agents to a routed toolset. Essential for bypassing the 128-tool limit by semantically selecting only relevant tools for the current turn.
- **Hierarchical Memory (MemoryMesh)**: A three-tier system (Working, Episodic, Semantic) to prevent agent reasoning loops and provide long-term "codebase wisdom" via a local graph DB.
- **Autonomous Swarm Hub**: Pattern for transient "scout" agents that report findings back to a coordinator without shared-state pollution.

### ⚡ 2026 SOTA Updates (DRP)

- **Async MCP Transport**: Move to WebSocket-based streaming for tool calls to reduce latency in multi-agent handoffs.
- **Sampling Protocol**: Standardized way for `thegent` agents to request human-in-the-loop (HITL) confirmation for destructive actions.
- **Contextual Pruning**: Using LLM-based summarization to compress long search results (from DRP) before injecting them into the agent's context window.

---

## 2. sharecli (Tool Proxy & OS-Level Guardrails)

**Focus**: Deduplication, caching, and resource safety for concurrent agents.

### 🚩 Critical AGSLAG Findings

- **Containerized Sandboxing**: Blueprints for isolating every shell command in a micro-container with strict CPU/Memory limits.
- **Write Serialization**: Using FUSE overlays to ensure that if 5 agents try to edit the same file, changes are queued or branched (CoW).

### ⚡ 2026 SOTA Updates (DRP)

- **Extism (Wasm) Sandboxing**: Replacing standard subprocess calls with WebAssembly sandboxes for "fast-path" tools (linter/formatter). Latency: <50ms vs >1s for Docker.
- **Firecracker MicroVMs**: Recommended for full-shell isolation where Wasm is insufficient, providing higher security with lower overhead than standard Docker.
- **JIT Schema Validation**: Using Pydantic V2 to validate thousands of proxied tool calls per second with zero-copy overhead.

---

## 3. trace (Requirements Traceability & Observability)

**Focus**: Linking requirements to code/tests/deployment via a Knowledge Graph.

### 🚩 Critical AGSLAG Findings

- **Senior Developer Understanding**: Deep indexing using **tree-sitter** for static analysis + LLM summarization. This provides the "Nodes" for the `trace` graph (linking functions to requirements).
- **Graph-Based Impact Analysis**: Patterns for using Neo4j to predict how a requirement change ripples through the dependency graph.

### ⚡ 2026 SOTA Updates (DRP)

- **Self-Improving Memory (Mem0)**: A pattern where the traceability graph automatically "weights" connections based on how often a link is used in successful agent tasks.
- **Automated Doc-to-Code Mapping**: Using multi-modal agents to "see" UI screenshots and map them back to specific frontend components in the trace graph.

---

# UX / DX / AX Enhancements (User, Developer, Agent Experience)

These features are included based on their ability to drastically reduce friction for humans and agents interacting with the system.

## 1. UX: The "Glass-Box" Dashboard

- **Feature**: Real-time TUI/Web dashboard for swarm monitoring.
- **Source**: `mcp-dashboard-next` (AGSLAG) & `sharecli-tray`.
- **Justification**: Humans lose trust in autonomous swarms when they can't see the "thinking" process. A real-time trace of tool-calls and memory-graph updates provides essential transparency.

## 2. DX: Zsh "Instant-On" (thegent-slim)

- **Feature**: A compiled Zsh state for agent sub-shells.
- **Source**: `Zsh-for-humans` (Safari Seed).
- **Justification**: Reducing shell init from 200ms to <10ms saves minutes of cumulative wall-time in a 1,000-turn research session. It also prevents "fork-panic" by minimizing the process-tree depth.

## 3. AX: Semantic Tool Schemas (Pydantic V2)

- **Feature**: JIT-compiled validation and LLM-optimized tool descriptions.
- **Source**: 2026 DRP (Pydantic Updates).
- **Justification**: Agent Experience (AX) is primarily governed by how well an LLM understands a tool's purpose. JIT schemas ensure that even with 5,000 tools, the "Router" can serve a compressed, high-signal schema to the agent without token waste.

## 4. UX/DX: The AI Scratchpad (Inline Drafting)

- **Feature**: A transient Zsh buffer for multi-turn command drafting.
- **Source**: r/zsh (Safari Seed).
- **Justification**: Improves UX by allowing users to collaboratively "pair-code" a complex CLI command with an agent before it is executed or saved to history.

## 5. AX: Environment Purifiers (MacOps Pattern)

- **Feature**: Post-task environment "reset" (killing zombies, cleaning /tmp).
- **Source**: `MacOps` / `Rust-cleanup` (Safari Seed).
- **Justification**: Agents often fail because a previous task left a stale `.lock` file or a zombie process. Auto-purifying the workspace between tasks ensures consistent AX.

---

## Combined Roadmap Priorities (Updated)

| Priority     | Feature             | Category | Justification              |
| :----------- | :------------------ | :------- | :------------------------- |
| **Critical** | Central Tool Router | AX       | Bypass 128-tool limit      |
| **Critical** | Wasm Sandboxing     | AX/DX    | Low-latency security       |
| **High**     | Zsh Slim-Shell      | DX/AX    | <10ms startup latency      |
| **High**     | Semantic History    | DX/UX    | Search by "Task Intent"    |
| **Med**      | Glass-Box TUI       | UX       | Real-time swarm monitoring |
| **Med**      | HITL Sampling       | UX/AX    | Safe destructive actions   |
