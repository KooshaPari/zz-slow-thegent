# Elicitation Systems & Git Strategies: Deep Research

**Date**: 2026-02-24
**Purpose**: Research MCP elicitation, Claude Code elicitation, and comprehensive git strategy comparison

---

# Part 1: Elicitation Systems Research

## 1.1 What is Elicitation?

**Elicitation** is the structured process by which an agent asks the user clarifying questions to gather requirements, resolve ambiguity, or confirm actions. It's "highly important for the agent to ask questions in a structured format."

### Why Structured Elicitation Matters

| Problem           | Unstructured           | Structured                    |
| ----------------- | ---------------------- | ----------------------------- |
| Ambiguity         | Agent guesses          | Agent asks specific options   |
| Requirements      | Free-text chaos        | Multiple-choice with context  |
| Progress blocking | Endless back-and-forth | Batch questions in one turn   |
| User fatigue      | Repetitive questions   | Smart grouping, minimal turns |

---

## 1.2 MCP Elicitation Specification

### MCP Protocol Overview

The Model Context Protocol (MCP) defines several mechanisms for agent-user interaction:

| Capability      | Description                              | Spec Reference |
| --------------- | ---------------------------------------- | -------------- |
| `elicitation`   | Request user input during tool execution | MCP 2025-03    |
| `sampling`      | Request LLM completion from client       | MCP Core       |
| `createMessage` | Create a message with user input         | MCP Sampling   |
| `roots`         | Discover workspace roots                 | MCP Roots      |
| `logging`       | Structured logging                       | MCP Logging    |

### MCP Elicitation Request Format

```json
{
  "method": "elicitation/create",
  "params": {
    "message": "I need clarification to proceed.",
    "requestedSchema": {
      "type": "object",
      "properties": {
        "framework": {
          "type": "string",
          "enum": ["react", "vue", "svelte"],
          "description": "Which framework to use?"
        },
        "typescript": {
          "type": "boolean",
          "description": "Use TypeScript?"
        }
      },
      "required": ["framework"]
    }
  }
}
```

### MCP Elicitation Response

```json
{
  "action": "accept",
  "content": {
    "framework": "react",
    "typescript": true
  }
}
```

### MCP Elicitation Actions

| Action    | Meaning                      |
| --------- | ---------------------------- |
| `accept`  | User provided values         |
| `decline` | User declined to answer      |
| `cancel`  | User cancelled the operation |

---

## 1.3 Claude Code Elicitation Feature

### Implementation Pattern

Claude Code uses the `ask_user_question` tool for structured elicitation:

```typescript
// From coder-mux toolDefinitions.ts
const AskUserQuestionQuestionSchema = z.object({
  question: z.string().min(1),
  header: z.string().min(1).max(32), // Short UI label
  options: z.array(AskUserQuestionOptionSchema).min(2).max(4),
  multiSelect: z.boolean(),
});

const AskUserQuestionToolArgsSchema = z.object({
  questions: z.array(AskUserQuestionQuestionSchema).min(1).max(4),
  answers: z.record(z.string(), z.string()).nullish(), // Prefilled answers
});
```

### Option Schema

```typescript
const AskUserQuestionOptionSchema = z.object({
  label: z.string().min(1), // Display text
  description: z.string().min(1), // Explanation of option
});
```

### Example Usage

```json
{
  "questions": [
    {
      "question": "How should I structure the authentication module?",
      "header": "Auth Structure",
      "options": [
        {
          "label": "JWT-based",
          "description": " Stateless tokens, good for APIs"
        },
        {
          "label": "Session-based",
          "description": "Server-side sessions, better security"
        },
        { "label": "OAuth2", "description": "Third-party auth providers" }
      ],
      "multiSelect": false
    },
    {
      "question": "Which features should be included in MVP?",
      "header": "MVP Scope",
      "options": [
        { "label": "Login/Logout", "description": "Basic authentication flow" },
        { "label": "Password Reset", "description": "Email-based recovery" },
        { "label": "2FA", "description": "Two-factor authentication" }
      ],
      "multiSelect": true
    }
  ]
}
```

### Claude Code Rules

1. **Max 4 questions per call** - Avoid overwhelming user
2. **Max 4 options per question** - Keep choices manageable
3. **Min 2 options per question** - Must have real choices
4. **Header max 32 chars** - Concise UI label
5. **No "Other" option** - Provided automatically by UI
6. **Unique question text** - No duplicates in same call
7. **Unique option labels** - No duplicates in same question

### Best Practices (from Gemini CLI skill-creator)

> "Avoid interrogation loops: Do not ask more than one or two clarifying questions at a time. Bias toward action: propose a concrete list of features or examples based on your initial understanding, and ask the user to refine them."

---

## 1.4 Elicitation Patterns Across Tools

| Tool            | Elicitation Method       | Max Questions | Multi-select | Special Features       |
| --------------- | ------------------------ | ------------- | ------------ | ---------------------- |
| **Claude Code** | `ask_user_question` tool | 4             | Yes          | Auto "Other" option    |
| **Gemini CLI**  | Skill-based prompts      | 2 recommended | N/A          | Propose + refine       |
| **Cline**       | Confirmation dialogs     | 1 per action  | No           | File/command approval  |
| **Cursor**      | Inline chat              | Unlimited     | No           | Contextual suggestions |
| **Aider**       | Voice/chat               | Unlimited     | No           | Architect mode         |

---

## 1.5 Proposed Helios Elicitation System

### Design Goals

1. **Structured** - JSON schema for questions
2. **Batched** - Multiple questions in one call
3. **Typed** - Support multiple input types
4. **Contextual** - Include relevant context
5. **Reversible** - User can modify answers

### Proposed Tool: `elicit`

```typescript
const ElicitQuestionSchema = z.object({
  id: z.string(), // Unique question ID
  type: z.enum([
    "single_choice", // Radio buttons
    "multi_choice", // Checkboxes
    "text", // Free text input
    "number", // Numeric input
    "file_path", // File picker
    "boolean", // Yes/No
    "range", // Slider
  ]),
  question: z.string(),
  header: z.string().max(32),
  context: z.string().optional(), // Why we're asking
  options: z
    .array(
      z.object({
        label: z.string(),
        description: z.string().optional(),
        value: z.any(), // Actual value returned
      }),
    )
    .optional(),
  default: z.any().optional(),
  validation: z
    .object({
      min: z.number().optional(),
      max: z.number().optional(),
      pattern: z.string().optional(), // Regex for text
    })
    .optional(),
  required: z.boolean().default(true),
});

const ElicitArgsSchema = z.object({
  questions: z.array(ElicitQuestionSchema).min(1).max(10),
  batch_id: z.string().optional(), // For tracking
  timeout_s: z.number().default(300), // Auto-decline after
  priority: z.enum(["low", "normal", "high", "blocking"]),
});
```

### Example Usage

```json
{
  "questions": [
    {
      "id": "auth_framework",
      "type": "single_choice",
      "question": "Which authentication framework should I use?",
      "header": "Auth Framework",
      "context": "This affects the project structure and dependencies",
      "options": [
        {
          "label": "Auth0",
          "value": "auth0",
          "description": "Managed service"
        },
        { "label": "Custom JWT", "value": "jwt", "description": "Self-hosted" },
        {
          "label": "Passport.js",
          "value": "passport",
          "description": "Node.js middleware"
        }
      ],
      "required": true
    },
    {
      "id": "include_tests",
      "type": "boolean",
      "question": "Should I include unit tests?",
      "header": "Tests",
      "default": true,
      "required": false
    },
    {
      "id": "coverage_target",
      "type": "range",
      "question": "What test coverage target?",
      "header": "Coverage",
      "context": "Only applies if tests are included",
      "validation": { "min": 50, "max": 100 },
      "default": 80,
      "required": false
    }
  ],
  "priority": "blocking",
  "timeout_s": 600
}
```

### Response Format

```json
{
  "batch_id": "batch_abc123",
  "status": "answered",
  "answers": {
    "auth_framework": "jwt",
    "include_tests": true,
    "coverage_target": 80
  },
  "user_modified": false,
  "timestamp": "2026-02-24T12:00:00Z"
}
```

---

# Part 2: Git Strategy Comparison Matrix

## 2.1 Strategy Overview

| Strategy                  | Description                               | Best For                           |
| ------------------------- | ----------------------------------------- | ---------------------------------- |
| **Lock-based**            | Exclusive file locks before edit          | Critical sections, sensitive files |
| **Optimistic**            | Edit freely, merge on commit              | Low-conflict environments          |
| **Branch-per-Agent**      | Each agent gets own branch                | Parallel development               |
| **Queue-based**           | Edits serialized through queue            | High-conflict environments         |
| **CRDT**                  | Conflict-free replicated data types       | Distributed systems                |
| **Operational Transform** | Transform operations to resolve conflicts | Real-time collaboration            |
| **Snapshot + Diff**       | Periodic snapshots, apply diffs           | Backup + restore                   |
| **Event Sourcing**        | Store events, rebuild state               | Audit trails                       |
| **N-Way Merge**           | Merge multiple branches simultaneously    | Multi-agent reconciliation         |
| **Coalescing**            | Combine similar edits automatically       | Deduplication                      |
| **Shadow Git**            | Full audit trail separate from main repo  | Granular restore                   |
| **Hybrid**                | Mix of above strategies                   | Complex requirements               |

---

## 2.2 Detailed Comparison Matrix

### Criteria Legend

| Criterion               | Weight | Description                  |
| ----------------------- | ------ | ---------------------------- |
| **Parallelism**         | HIGH   | Ability to work concurrently |
| **Conflict Rate**       | HIGH   | Frequency of merge conflicts |
| **Restore Granularity** | HIGH   | Precision of undo/restore    |
| **Disk Space**          | MEDIUM | Storage overhead             |
| **Complexity**          | MEDIUM | Implementation difficulty    |
| **Latency**             | MEDIUM | Time to complete operations  |
| **Audit Trail**         | LOW    | History visibility           |
| **Scalability**         | MEDIUM | Performance with many agents |

### Matrix (Score: 1-5, 5=Best)

| Strategy         | Parallelism | Conflict Rate | Restore Granularity | Disk Space | Complexity | Latency | Audit Trail | Scalability | **TOTAL** |
| ---------------- | ----------- | ------------- | ------------------- | ---------- | ---------- | ------- | ----------- | ----------- | --------- |
| Lock-based       | 2           | 5             | 2                   | 5          | 4          | 2       | 3           | 2           | **25**    |
| Optimistic       | 5           | 2             | 2                   | 5          | 3          | 5       | 3           | 4           | **29**    |
| Branch-per-Agent | 5           | 4             | 3                   | 3          | 3          | 4       | 5           | 3           | **30**    |
| Queue-based      | 2           | 5             | 2                   | 5          | 3          | 2       | 5           | 3           | **27**    |
| CRDT             | 5           | 5             | 3                   | 2          | 1          | 5       | 4           | 5           | **30**    |
| Op Transform     | 5           | 5             | 3                   | 3          | 1          | 5       | 4           | 4           | **30**    |
| Snapshot+Diff    | 3           | 3             | 5                   | 3          | 4          | 3       | 5           | 4           | **30**    |
| Event Sourcing   | 3           | 3             | 5                   | 2          | 2          | 3       | 5           | 5           | **28**    |
| N-Way Merge      | 4           | 3             | 3                   | 4          | 2          | 3       | 4           | 3           | **26**    |
| Coalescing       | 4           | 4             | 3                   | 4          | 3          | 4       | 4           | 4           | **30**    |
| Shadow Git       | 4           | 3             | 5                   | 3          | 3          | 4       | 5           | 4           | **31**    |
| **Hybrid**       | 5           | 4             | 5                   | 3          | 2          | 4       | 5           | 5           | **33**    |

---

## 2.3 Strategy Deep Dive

### Lock-based

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Agent A │────▶│  Lock   │────▶│  Edit   │
└─────────┘     │ Manager │     │  File   │
                └─────────┘     └─────────┘
                     │
┌─────────┐          │ Queue
│ Agent B │──────────┘ (wait)
└─────────┘
```

**Pros**: No conflicts, simple mental model
**Cons**: Blocks parallelism, deadlocks possible

### Optimistic + N-Way Merge

```
┌─────────┐     ┌─────────┐
│ Agent A │────▶│ Branch  │
└─────────┘     │  feat/a │
                └────┬────┘
                     │
┌─────────┐     ┌────┴────┐
│ Agent B │────▶│ Branch  │──────┐
└─────────┘     │  feat/b │      │
                └─────────┘      │
                                 ▼
                          ┌──────────┐
                          │ N-Way    │
                          │ Merge    │
                          └──────────┘
```

**Pros**: Maximum parallelism, clean history
**Cons**: Merge complexity, conflict resolution overhead

### Shadow Git + Public Git

```
┌──────────────────────────────────────────────┐
│                   Shadow Git                   │
│  (Every edit, full audit, granular restore)   │
├──────────────────────────────────────────────┤
│  edit-001: +3 lines foo.py                    │
│  edit-002: -1 line bar.py                     │
│  edit-003: rename x→y                         │
│  ...                                          │
└──────────────────────┬───────────────────────┘
                       │ batch
                       ▼
┌──────────────────────────────────────────────┐
│                   Public Git                   │
│  (Logical commits, user-facing)               │
├──────────────────────────────────────────────┤
│  commit-1: "Add authentication module"        │
│  commit-2: "Fix login validation"             │
└──────────────────────────────────────────────┘
```

**Pros**: Full audit, granular restore, clean public history
**Cons**: Disk overhead, sync complexity

---

## 2.4 Recommended Hybrid Strategy

### Components

| Component               | Strategy          | Purpose                                  |
| ----------------------- | ----------------- | ---------------------------------------- |
| **Real-time edits**     | Optimistic        | Allow parallel edits                     |
| **Conflict resolution** | N-Way Merge + LLM | Auto-merge when clean, LLM for conflicts |
| **Audit trail**         | Shadow Git        | Every edit logged                        |
| **Restore**             | Snapshot + Diff   | Granular undo                            |
| **Public commits**      | Batched           | Logical units                            |

### Flow

```
Agent A edits foo.py
        │
        ▼
┌─────────────────┐
│  Optimistic     │  No lock, just edit
│  Edit Buffer    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Shadow Git     │  Log every edit
│  Journal        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Conflict Check │  Any other edits to same file?
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
   No        Yes
    │         │
    ▼         ▼
┌───────┐  ┌─────────────┐
│ Apply │  │ N-Way Merge │
│       │  │ + LLM       │
└───┬───┘  └──────┬──────┘
    │             │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ Stage for   │
    │ Commit      │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ Batch       │  At turn end or threshold
    │ Commit      │
    └─────────────┘
```

---

## 2.5 Conflict Resolution Decision Tree

```
                    ┌──────────────────┐
                    │ Conflict Detected│
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │ Same file, different hunks? │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
             Yes                            No
              │                              │
              ▼                              ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ Auto-merge      │          │ Same hunk?      │
     │ (git merge)     │          └────────┬────────┘
     └─────────────────┘                   │
                                  ┌────────┴────────┐
                                 Yes                No
                                  │                  │
                                  ▼                  ▼
                        ┌─────────────────┐  ┌─────────────────┐
                        │ LLM Merge       │  │ N-Way Merge     │
                        │ (semantic)      │  │ (git)           │
                        └────────┬────────┘  └─────────────────┘
                                 │
                        ┌────────┴────────┐
                       Success           Failed
                        │                  │
                        ▼                  ▼
                 ┌─────────────┐   ┌─────────────────┐
                 │ Apply       │   │ Flag for Agent  │
                 │ Result      │   │ (NEVER human)   │
                 └─────────────┘   └─────────────────┘
```

---

# Part 3: Final Decisions

## 3.1 Shadow Git Storage Decision

**Chosen: SQLite + Journal**

| Aspect             | Decision            | Rationale                    |
| ------------------ | ------------------- | ---------------------------- |
| **Primary Store**  | SQLite              | ACID, embedded, fast queries |
| **Journal Format** | JSONL               | Append-only, streamable      |
| **Large Files**    | External (path ref) | Don't blob big files         |
| **Retention**      | Permanent           | For reconciliation           |

```sql
CREATE TABLE shadow_edits (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    thread_id TEXT,
    agent_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    file_path TEXT NOT NULL,
    edit_type TEXT NOT NULL,  -- 'create', 'modify', 'delete'
    hunk_before TEXT,         -- JSON array of lines
    hunk_after TEXT,          -- JSON array of lines
    line_start INTEGER,
    line_end INTEGER,
    metadata TEXT             -- JSON
);

CREATE INDEX idx_shadow_session ON shadow_edits(session_id);
CREATE INDEX idx_shadow_file ON shadow_edits(file_path);
CREATE INDEX idx_shadow_time ON shadow_edits(timestamp);
```

---

## 3.2 Multi-Tenant Git Strategy Decision

**Chosen: Hybrid (Optimistic + N-Way Merge + Shadow Git)**

| Scenario                        | Strategy                     |
| ------------------------------- | ---------------------------- |
| Different files                 | Optimistic (no coordination) |
| Same file, different hunks      | Auto-merge                   |
| Same hunk, no semantic conflict | N-way merge                  |
| Same hunk, semantic conflict    | LLM resolve                  |
| LLM fails                       | Flag for agent (never human) |

---

## 3.3 Local Model Threshold Decision

**Decision: Sub-2B for commit/annotation, larger for complex**

| Task                  | Model Type | Reasoning         |
| --------------------- | ---------- | ----------------- |
| Commit messages       | Sub-2B     | Simple, formulaic |
| Change classification | Sub-2B     | Few categories    |
| Session annotation    | Sub-2B     | Summary task      |
| Memory summarization  | 3-7B       | Needs coherence   |
| Search summarization  | Sub-2B     | Extraction task   |

**Break-even Analysis**:

- Sub-2B model: ~500MB RAM
- 10 concurrent = ~5GB dedicated
- Worth it if doing >50 ops/min

---

## 3.4 Elicitation System Decision

**Chosen: MCP-inspired + Claude Code patterns**

| Aspect              | Decision                                                             |
| ------------------- | -------------------------------------------------------------------- |
| **Tool name**       | `elicit`                                                             |
| **Max questions**   | 10 per batch                                                         |
| **Types supported** | single_choice, multi_choice, text, number, boolean, file_path, range |
| **Priority levels** | blocking, high, normal, low                                          |
| **Timeout**         | Configurable, default 5 min                                          |
| **Auto-escalation** | Low priority → escalate if blocking                                  |

---

## 3.5 Summary of All Decisions

| Question               | Decision                                   |
| ---------------------- | ------------------------------------------ |
| Shadow git storage     | SQLite + JSONL journal                     |
| Multi-tenant git       | Hybrid (optimistic + N-way merge + shadow) |
| Local model threshold  | Sub-2B for simple, 3-7B for complex        |
| Elicitation            | MCP-inspired `elicit` tool                 |
| Conflict resolution    | Auto → LLM → Agent flag (never human)      |
| Backup granularity     | All levels (file → hunk → edit → action)   |
| Session centralization | Required (socket attachment)               |

---

_Research Complete: 2026-02-24_
_Ready for Implementation Planning_
