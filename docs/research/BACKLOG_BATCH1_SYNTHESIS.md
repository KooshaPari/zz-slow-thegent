<DONE>
# Backlog Research Synthesis: 3-Month Deep Dive (Batch 1)
**Date:** 2026-02-19
**Scope:** Initial ~50 links from the 1,888 unique link backlog (3-month Safari history).

---

## 1. Tooling & Infrastructure: User / Agent / Project Levels

### **A. User Level (Persistence & Interface)**

- **Memory Persistence (The SQL Shift)**:
  - **Gibson / Memori**: A significant movement toward using **relational SQL (Postgres)** instead of Vector DBs for "Hard Preferences" and entities. SQL provides deterministic recall for facts like "User prefers pnpm" which are often lost in "noisy" vector retrieval.
  - **Persistent Sessions**: Re-emphasizing the need for stateful inference wrappers to handle long-running background tasks (e.g., `calljmp`).
- **macOS 26 Alert**: macOS 26 foregrounds background Node.js processes into the Dock. This affects local developers running many MCP servers, causing significant Dock clutter.

### **B. Agent Level (Orchestration & Tools)**

- **Communication Protocols**:
  - **LatentMAS**: Agents collaborate via hidden vector representations instead of text, saving 90% of token costs and reducing information loss.
  - **Agience & Distributed MAS**: Frameworks for agents to discover each other and communicate over a network (distributed intelligent agents).
- **Tool Integration**:
  - **mcp-use**: A Python-native client that reduces MCP integration to **6 lines of code**.
  - **CDP MCP (Chrome DevTools)**: A "learned" automation pattern where an AI identifies a DOM path once, and then executes via CDP directly, bypassing expensive LLM vision/scraping calls.
- **Reasoning Patterns**: **Aster Agents** advocates for non-deterministic reasoning agents that decide _how_ to collaborate, rather than being restricted to fixed DAGs or prompt chains.

### **C. Project Level (Methodology & Guardrails)**

- **Runtime Guardrails**:
  - **Zsh Hooks**: Implementing `.zshrc.local` triggers that override common commands (like `npx`) to prevent agents from bypassing project-specific build systems.
  - **PM2 for Backend Observability**: Running microservices in PM2 so agents can autonomously access logs (`pm2 logs`) and handle crashes.
- **Strategic Scaffolding**:
  - **Spec-Driven Development (Spec-Kit)**: Forcing agents to reference PRDs and ADRs before every edit to prevent "context drift."
  - **PRD -> Bolt -> Cursor Pipeline**: A high-speed MVP methodology identified as the current "gold standard" for starting new projects.

---

## 2. Strategic "Contrarian" Patterns

### A. The Return to SQL (Structured Memory)

A significant thread argues that **Vector DBs are "noisy"** and **Graphs are "complex to scale."** The "Gibson" project advocates for using **PostgreSQL/SQL** to store explicit user preferences, rules, and entities, using standard joins/indexes for deterministic retrieval.

### B. "Learned" Browser Automation

Instead of constant LLM-driven scraping, the **CDP MCP** approach uses the LLM to _teach_ a script the DOM path once. Subsequent runs use Chrome DevTools Protocol directly, cutting costs by 99% and increasing reliability against UI changes.

### C. Latent Space Collaboration (LatentMAS)

Research into bypassing text entirely for multi-agent workflows. By passing "internal thoughts" (KV Caches/Hidden States) between models, agents can share "telepathic" context with zero information loss and minimal token cost.

---

## 3. Ecosystem Intelligence & Warnings

- **macOS 26 Conflict**: MCP developers should beware of macOS 26's new behavior of foregrounding background Node.js processes into the Dock, which creates UI clutter during local development.
- **The "Failure" Rate**: AI projects often fail (66%+) when trying to replace deterministic logic with non-deterministic LLMs. Success lies in "agentic pipelines" where AI handles reasoning and standard software handles execution.

---

## 4. Priority Queue: Backlog Integration

1.  **[Tooling] mcp-use Integration**: Evaluate `mcp-use` for simplifying `thegent`'s internal MCP client logic.
2.  **[Architecture] Gibson-style SQL Memory**: Implement a structured SQL table for "Hard Preferences" (e.g., "Always use pnpm," "Never use emojis") to supplement the vector memory.
3.  **[Automation] CDP-based Workflows**: Port the `chrome-devtools-mcp` concept for the "Reddit Content Fetcher" to make it more robust.
4.  **[Framework] Atomic Agents Review**: Deep dive into the "Atomic" philosophy for `thegent`'s skill development.

---

## 5. Metadata

- **Links Extracted**: 1,888
- **Batch 1 Progress**: 40/150 analyzed.
- **Backlog Source**: `Safari History (3 Months)`
