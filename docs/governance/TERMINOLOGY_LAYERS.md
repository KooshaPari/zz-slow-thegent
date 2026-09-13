# Terminology: Layer Vocabulary

**Purpose:** Establish consistent vocabulary for ease of communication across thegent, harnesses, and LLM infrastructure.

**Reference:** CLAUDE.md § Terminology (Layer Vocabulary)

---

## Core Terms

### Harness

The **agent layer**. Executes agent logic, tools, and workflows. May or may not come with a CLI, API, or other interface.

**Examples:**

- Codex CLI
- Claude Code CLI
- Claude Agent SDK
- Factory Droid
- Cursor (agent mode)

### LLM

The **model** (as known). The underlying language model invoked for completions.

**Examples:** GPT-5, Claude, Gemini, GLM-5, etc.

### Presentation Layer

The **UI layer** of a harness. How the user interacts with the agent.

**Examples:** Terminal UI, IDE panel, web UI, chat interface.

### Various Layers

Layers **between and around** the harness, LLM, and presentation. Include routing, proxy, auth, orchestration.

**Examples:**

- CLIProxyAPIPlus (proxy, auth, routing)
- LiteLLM Router (routing, fallback)
- thegent (orchestration, delegation)

---

## Layer Diagram (Conceptual)

```
┌─────────────────────────────────────────────────────────┐
│  Presentation layer  (UI: terminal, IDE, web)           │
├─────────────────────────────────────────────────────────┤
│  Harness  (agent layer: Codex CLI, Claude Code, Droid)  │
├─────────────────────────────────────────────────────────┤
│  Various layers  (routing, proxy, auth, orchestration)   │
├─────────────────────────────────────────────────────────┤
│  LLM  (model: GPT-5, Claude, Gemini, etc.)              │
└─────────────────────────────────────────────────────────┘
```

---

## Usage

- Use **harness** when referring to the agent execution layer (Codex, Claude Code, Droid, Cursor).
- Use **LLM** when referring to the model.
- Use **presentation layer** when referring to UI/UX of a harness.
- Use **various layers** when referring to routing, proxy, auth, orchestration between harness and LLM.
