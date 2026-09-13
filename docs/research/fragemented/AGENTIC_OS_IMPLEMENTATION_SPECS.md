<DONE>
# Agentic OS: Implementation Specs & Reference Guide
**Date:** 2026-02-19
**Scope:** Actionable implementation patterns for high-signal tools identified in research.

---

## 1. Temporal Knowledge Graph: Graphiti MCP

- **Purpose**: Persistent, searchable memory across sessions using Neo4j.
- **Implementation**:
  - **Backend**: Neo4j Community Edition (Local).
  - **Hook**: `thegent://mcp/graphiti`
  - **Workflow**:
    1.  Agent completes a task $\rightarrow$ calls `graphiti_add_node` with task metadata.
    2.  New session starts $\rightarrow$ L1 agent calls `graphiti_query` for "Architectural Decisions" to bootstrap context.
- **Reference**: `github.com/graphiti-ai/graphiti`

---

## 2. Swarm mode: Claude-Flow / SwarmStation

- **Purpose**: Parallelize heavy tasks (e.g., refactoring 50 files) by spawning sub-agents.
- **Logic**:
  - **Dispatcher**: L1 agent analyzes total workload.
  - **Swarmer**: Spawns $N$ sub-agents via the `thegent` daemon.
  - **Collector**: L1 merges PRs/diffs from sub-agents.
- **Pattern**:
  ```bash
  # Example Swarm Command
  thegent swarm execute "refactor src/components to tailwind" --parallel 5
  ```

---

## 3. Spec-Driven Development (SDD): Spec-Kit

- **Purpose**: Enforce adherence to requirements before any code is written.
- **Mechanism**:
  - `spec-kit validate`: Compares the current PR against the `plan.md` and `PRD.md`.
  - **LSP Integration**: Real-time linting of "intent vs implementation."
- **Reference**: `github.com/spec-driven-dev/spec-kit`

---

## 4. Autonomous Visual Validation

- **Purpose**: Self-healing UI implementation.
- **Config (`.claude/settings.json`)**:
  ```json
  {
    "post_edit_hooks": [
      "playwright test --screenshot-on-failure",
      "python3 scripts/analyze_visual_delta.py"
    ]
  }
  ```
- **Logic**:
  1.  Agent edits `Button.tsx`.
  2.  Hook runs headless browser $\rightarrow$ captures snapshot.
  3.  If layout shifted $> 5\%$, failure is returned to agent.

---

## 5. Context Annotation Trinity

- **Tool 1: `repomix`**: Pack repository into a single XML for the "Project Briefing."
- **Tool 2: `code2prompt`**: Context-aware prompt generation with dependency trees.
- **Tool 3: `agents.md`**: Root-level manual for the agent to ensure "Vibe Compliance."

---

## 6. Token Economics: ccusage & Proxy

- **ccusage**: Track token savings ($100/mo flat vs $1.6k API).
- **Claude-OpenAI Wrapper**: Allows using the Claude Max plan as an OpenAI-compatible endpoint for other tools (e.g., Cursor, Aider).

---

## 7. Memory Harness: Gibson / Memori

- **Logic**: Multi-agent memory engine using SQL (PostgreSQL) for structured, deterministic long-term memory. Unlike vector DBs, it allows for relational queries ("Show me all tasks from Project X where Agent Y used library Z").
- **Reference**: `github.com/memori-ai/gibson`
