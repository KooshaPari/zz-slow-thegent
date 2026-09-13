# Merged Fragmented Markdown

## Source: docs/api

## Source: cli-reference.md

# CRUN CLI Command Reference

**Complete guide to CRUN command-line interface commands and options (current behavior)**

## Table of Contents

1. [Global Options](#global-options)
2. [AI Plan Commands](#ai-plan-commands)
3. [Plan Commands](#plan-commands)
4. [Monitoring Commands](#monitoring-commands)
5. [UI Commands](#ui-commands)
6. [Examples](#examples)
7. [Error Messages & Solutions](#error-messages--solutions)

---

## Global Options

Global options work with any CRUN command:

```bash
crun [OPTIONS] COMMAND [ARGS]
```

| Option           | Description               | Example               |
| ---------------- | ------------------------- | --------------------- |
| `--help`         | Show help message         | `crun --help`         |
| `-v, --version`  | Show CRUN version         | `crun --version`      |
| `--list-clients` | List available UI clients | `crun --list-clients` |

---

## AI Plan Commands

AI planning commands are in the `ai-plan` namespace.

> Legacy docs may still show `crun plan generate-massive`. The current command path is `crun ai-plan generate-massive`.

### `crun ai-plan generate-massive`

Generate a large, detailed project plan using AI.

**Usage:**

```bash
crun ai-plan generate-massive [OPTIONS] DESCRIPTION_FILE
```

**Arguments:**

- `DESCRIPTION_FILE` - Path to PRD/description file (text or JSON)

**Options:**

| Flag                         | Default                     | Description                   |
| ---------------------------- | --------------------------- | ----------------------------- |
| `-o, --output`               | `massive-plan.json`         | Output path for generated WBS |
| `--max-depth`                | `4`                         | Maximum WBS hierarchy depth   |
| `--model`                    | `anthropic/claude-sonnet-4` | Primary model for generation  |
| `--fast-model`               | `anthropic/claude-haiku-4`  | Fast model for simpler tasks  |
| `--streaming/--no-streaming` | `--streaming`               | Enable streaming progress     |
| `--api-key`                  | from `OPENROUTER_API_KEY`   | API key override              |

**Examples:**

```bash
# Basic
crun ai-plan generate-massive project_spec.txt -o my_plan.json

# Custom depth and model
crun ai-plan generate-massive project_spec.txt --max-depth 5 --model anthropic/claude-opus-4 -o big_plan.json

# Use stdin
echo "Build a task management app" | crun ai-plan generate-massive - -o plan.json
```

### `crun ai-plan visualize`

**Usage:**

```bash
crun ai-plan visualize [OPTIONS] PLAN_FILE
```

**Arguments:**

- `PLAN_FILE` - Path to WBS plan file (JSON)

**Options:**

| Flag                                           | Default                | Description                           |
| ---------------------------------------------- | ---------------------- | ------------------------------------- |
| `-f, --format`                                 | `gantt`                | `gantt`, `dag`, `timeline`, `mermaid` |
| `-o, --output`                                 | auto                   | Output path                           |
| `--highlight-critical/--no-highlight-critical` | `--highlight-critical` | Highlight critical path               |

**Example:**

```bash
crun ai-plan visualize my_plan.json --format dag --output dag.png
```

### `crun ai-plan edit`

**Usage:**

```bash
crun ai-plan edit [OPTIONS] PLAN_FILE
```

**Options:**

| Flag             | Description                                                   |
| ---------------- | ------------------------------------------------------------- |
| `-t, --task`     | (required) Task ID to edit                                    |
| `--set-status`   | Set status (`pending`, `in_progress`, `completed`, `blocked`) |
| `--set-assignee` | Set assignee                                                  |
| `--set-priority` | Set priority                                                  |
| `--add-tag`      | Add a tag                                                     |
| `--remove-tag`   | Remove a tag                                                  |

### `crun ai-plan monitor`

**Usage:**

```bash
crun ai-plan monitor [OPTIONS] PLAN_FILE
```

**Options:**

| Flag                  | Default         | Description                                      |
| --------------------- | --------------- | ------------------------------------------------ |
| `-f, --follow`        | `False`         | Stream execution updates                         |
| `-w, --workers`       | `10`            | Maximum workers                                  |
| `-p, --priority`      | `critical_path` | `critical_path`, `slack`, `complexity`, `hybrid` |
| `--dry-run/--execute` | `--dry-run`     | Simulate or execute                              |

---

## Plan Commands

`crun plan` covers planning setup, validation, analysis, and task management commands (non-AI generation commands).

### Representative commands

- `crun plan init`
- `crun plan new`
- `crun plan show`
- `crun plan estimate`
- `crun plan cp`
- `crun plan risk`
- `crun plan sync`
- `crun plan watch`
- `crun plan install-hooks`
- `crun plan uninstall-hooks`
- `crun plan export-tasks`
- `crun plan run-tasks`
- `crun plan template list`
- `crun plan template show`
- `crun plan validate`
- `crun plan migrate`

Use `crun plan --help` to view the full command list available in your installed build.

---

## Monitoring Commands

Monitoring is under `crun monitor` for static quality/test monitoring.
Some builds may also expose adapter-based dashboards under `crun monitoring` (project/agent/quality/all).

### `crun monitor start`

Start static monitoring and optional lint/test fixing over a workspace.

Options:

- `--workspace, -w`: Workspace directory (default `.`)
- `--languages, -l`: Comma-separated languages to scan (default `python,typescript`)
- `--lint` (default true): Enable lint fixing
- `--tests` (default true): Enable test fixing
- `--workers, -j`: Max worker count (default `4`)

Example:

```bash
crun monitor start --workspace . --languages python,typescript
```

### `crun monitor list-models`

List models available to the monitor runner.

```bash
crun monitor list-models
```

### Legacy `crun monitoring` alias (when available)

If your installed build includes the optional adapter package, these legacy subcommands may appear:

`crun monitoring project | agent | quality | all`

---

## UI Commands

### `crun gui`

Launch the graphical user interface.

### `crun tui`

Launch the terminal user interface.

---

## Examples

### AI plan flow

```bash
cat > my_project.txt << 'EOF'
Build a REST API with:
- Authentication
- PostgreSQL
- Redis
- Docker containerization
EOF

crun ai-plan generate-massive my_project.txt -o api_plan.json
crun ai-plan visualize api_plan.json --format dag -o dag.png
crun ai-plan monitor api_plan.json --workers 8
```

### Planning setup flow

```bash
crun plan init
crun plan sync
crun plan show
```

### Monitoring flow

```bash
crun monitor start --workspace .
```

---

## Error Messages & Solutions

### Error: `Command not found: crun`

**Cause:** CRUN is not installed in the active environment.

**Solution:**

```bash
source venv/bin/activate
pip install -e ".[all]"
```

### Error: `Error: API key required`

**Cause:** OpenRouter API key missing.

**Solution:**

```bash
export OPENROUTER_API_KEY=or-your-key
```

### Error: `No such option: --use-tot`

**Cause:** `--use-tot` and `--use-adapt` were removed from `ai-plan`.

**Solution:** Use `--max-depth` and model selection (`--model`, `--fast-model`) instead.

### Error: `Usage: crun quality`

**Cause:** `crun quality` is not a top-level command.

**Solution:**

```bash
crun monitor start --workspace . --languages python,typescript --lint --tests
```

---

## Environment Variables for CLI

```bash
export CRUN_DEFAULT_MODEL=anthropic/claude-sonnet-4
export CRUN_DEBUG=true
export CRUN_LOG_LEVEL=DEBUG
export OPENROUTER_API_KEY=or-your-key
```

## Command Chaining

```bash
crun ai-plan generate-massive spec.txt -o plan.json && \
crun ai-plan visualize plan.json --format dag && \
crun ai-plan monitor plan.json --dry-run
```

**Version:** CRUN 3.0.0 | Last Updated: 2026-02-22

---

## Source: mcp-protocol.md

# MCP Protocol Guide

## Overview

Model Context Protocol (MCP) is a standardized protocol for AI agents to discover and execute tools. This guide covers how atoms-mcp-prod implements MCP and how to use it with Claude and other AI agents.

## Architecture

### 5 Consolidated Agent-Optimized Tools

Instead of creating a tool for every operation, atoms-mcp uses 5 consolidated tools that handle multiple operations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FastMCP Server (v2.13.1)                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 5 Consolidated Agent-Optimized Tools                                  │  │
│  │ ├─ workspace_operation (set/get/list/create/update/delete)           │  │
│  │ ├─ entity_operation (CRUD on documents, requirements, tasks)         │  │
│  │ ├─ relationship_operation (create/query/delete relationships)        │  │
│  │ ├─ workflow_execute (multi-step transaction workflows)               │  │
│  │ └─ data_query (FTS, semantic, hybrid, aggregation)                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                               │
│  ┌───────────────────────────▼───────────────────────────────────────────┐  │
│  │ Services Layer                                                        │  │
│  │ ├─ Unified Search (FTS + Vector/Semantic hybrid)                     │  │
│  │ ├─ Embedding Factory (Vertex AI + caching)                           │  │
│  │ ├─ Relationship Engine (graph operations)                            │  │
│  │ ├─ Compliance Engine (audit logging)                                 │  │
│  │ └─ Event Publisher (real-time updates)                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Supabase         Upstash Redis    Google Vertex
   (Database)       (Cache)          (Embeddings)
```

## 5 MCP Tools Exposed

### 1. workspace_operation

Manage user's **active context** (organization, project, document):

```python
async def workspace_operation(
    operation: str,        # "set_active", "get_active", "list", "create", "update", "delete"
    workspace_id: Optional[str],
    name: Optional[str],
    description: Optional[str],
    metadata: Optional[dict]
) -> dict
```

**Operations:**

- `set_context()` - Set active workspace entity
- `get_context()` - Get current context
- `list_workspaces()` - List available workspaces
- `create_workspace()` - Create new workspace

**Benefit:** Agents don't need to repeat project_id in every request; context persists across multi-turn conversations.

### 2. entity_operation

CRUD operations on documents, requirements, tasks, and custom entity types:

```python
async def entity_operation(
    operation: str,        # "create", "read", "update", "delete", "list", "search"
    entity_type: str,      # "document", "requirement", "task", custom types
    entity_id: Optional[str],
    properties: Optional[dict],
    filters: Optional[dict],
    limit: Optional[int],
    offset: Optional[int]
) -> dict
```

**Supported Entity Types:**

- Documents
- Requirements
- Projects
- Tasks
- Organizations
- Users

**Operation Types:**
| Operation | Purpose |
|-----------|---------|
| `create` | Create new entity |
| `read` | Retrieve entity by ID |
| `update` | Modify entity properties |
| `delete` | Remove entity (soft/hard) |
| `list` | List entities with filters |
| `search` | Text search on entities |
| `archive` | Mark as inactive |
| `restore` | Reactivate archived entity |
| `history` | View version history |

### 3. relationship_operation

Manage entity relationships and graph operations:

```python
async def relationship_operation(
    operation: str,        # "create", "query", "delete"
    entity_id: str,
    target_id: str,
    relationship_type: str,  # "member", "contains", "references", custom
    properties: Optional[dict]
) -> dict
```

**Relationship Types:**

- `member` - Entity membership
- `contains` - Containment relationship
- `references` - Reference relationship
- `traces_to` - Requirement traceability
- Custom types as defined by workspace

### 4. workflow_execute

Execute multi-step transaction workflows:

```python
async def workflow_execute(
    workflow_id: str,
    steps: list,           # Ordered list of operations
    input_data: dict,
    transaction: bool = True
) -> dict
```

**Benefits:**

- Atomic operations (all or nothing)
- Ordered execution
- Built-in error recovery

### 5. data_query

Unified search with full-text, semantic, and aggregation support:

```python
async def data_query(
    query_type: str,       # "fts", "semantic", "hybrid", "aggregation"
    q: str,                # Query string
    filters: Optional[dict],
    limit: Optional[int],
    offset: Optional[int],
    sort_by: Optional[str]
) -> dict
```

**Query Types:**
| Type | Description |
|------|-------------|
| **Search** | Full-text and keyword search |
| **Semantic (RAG)** | AI-powered similarity search using Vertex AI embeddings |
| **Aggregate** | Statistical analysis (count, sum, avg) |
| **Analyze** | Deep insights (requirement coverage, complexity) |
| **Relationship** | Entity graph navigation |

**Search Modes:**

- `semantic` - Vector similarity only (slow, accurate)
- `keyword` - BM25 text search (fast, exact)
- `hybrid` - Combined semantic + keyword (balanced)
- `auto` - Intelligently chooses based on query

## Response Format

All tools return standardized JSON:

```json
{
  "success": true,
  "data": {...},
  "error": null,
  "metadata": {
    "timestamp": "2024-11-25T...",
    "execution_time_ms": 123,
    "workspace_id": "...",
    "user_id": "..."
  }
}
```

## Authentication

| Method             | Description                                            |
| ------------------ | ------------------------------------------------------ |
| **OAuth 2.0 PKCE** | Recommended for Claude Desktop - browser-based flow    |
| **Bearer Tokens**  | For service-to-service - JWT in `auth_token` parameter |
| **Session Tokens** | Created during OAuth flow, cached in-memory            |

**RLS Integration:** Server extracts user_id from JWT, sets Supabase context, queries automatically filtered.

## Connecting Claude Desktop

Add to Claude's configuration file:

```json
{
  "mcpServers": {
    "atoms": {
      "command": "python",
      "args": ["cli.py", "run"],
      "env": {
        "SUPABASE_URL": "https://...",
        "SUPABASE_KEY": "..."
      }
    }
  }
}
```

## Typical Workflows

**Workflow 1: Create a Project with Documents**

```
1. workspace_operation (set_context) → Set active workspace/project
2. entity_operation (create) → Create project entity
3. entity_operation (create) → Create documents within project
4. relationship_operation (link) → Link documents to project
5. data_query (search) → Verify created structure
```

**Workflow 2: Search and Analyze Requirements**

```
1. workspace_operation (get_context) → Get current workspace context
2. data_query (rag_search) → Semantic search for requirements
3. data_query (analyze) → Analyze requirement coverage
4. relationship_operation (list) → Find related entities
5. workflow_execute → Execute impact analysis workflow
```

---

**Content merged from:** technical-documentation-mcp.md

---

## Source: rest-api.md

# REST API Reference

## Overview

This documentation covers the REST API endpoints exposed by atomsAgent (FastAPI backend). For client-side integration examples, see the frontend documentation.

**Base URL:** `http://localhost:8000` (development) or your deployed instance

## API Specification

### OpenAI-Compatible Endpoints (v1 API)

These endpoints follow the OpenAI API specification for drop-in replacement compatibility.

```
POST /v1/chat/completions     # Chat completion (streaming & non-streaming)
GET  /v1/models               # List available models
POST /v1/embeddings           # Generate embeddings
POST /v1/ocr                  # Document OCR via Vertex Vision
```

### MCP Management Endpoints

```
POST   /atoms/mcp/register    # Register MCP server
GET    /atoms/mcp/servers     # List registered servers
DELETE /atoms/mcp/servers/{id}# Unregister server
POST   /atoms/mcp/tools       # Discover tools
POST   /atoms/mcp/test        # Test connection
```

### Agent Management Endpoints

```
POST   /atoms/agents          # Create agent
GET    /atoms/agents/{id}     # Get agent
PUT    /atoms/agents/{id}     # Update agent
DELETE /atoms/agents/{id}     # Delete agent
```

### Chat & Conversation Endpoints

```
POST /atoms/conversations                    # Create conversation
GET  /atoms/conversations/{id}               # Get conversation
POST /atoms/conversations/{id}/messages      # Add message
GET  /atoms/messages                         # List messages
```

### Platform Admin Endpoints

```
POST /atoms/platform/prompts        # Create system prompt
GET  /atoms/platform/prompts/{id}   # Get prompt
PUT  /atoms/platform/prompts/{id}   # Update prompt
GET  /atoms/platform/system-prompts # List prompts
```

### Global Endpoints

```
GET /health   # Health check
GET /ready    # Readiness check
GET /metrics  # Prometheus metrics
```

## Request/Response Formats

### Chat Completions Request

**POST /v1/chat/completions**

```json
{
  "model": "claude-4.5-sonnet",
  "messages": [{ "role": "user", "content": "Hello!" }],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1024,
  "system_prompt": "Optional override",
  "metadata": {
    "session_id": "session-123",
    "organization_id": "org-uuid",
    "user_id": "user-uuid",
    "workflow": "customer_support",
    "variables": { "customer_name": "John" },
    "allowed_tools": ["calculator", "web_search"],
    "mcp_servers": {}
  }
}
```

### Chat Completions Response (Non-Streaming)

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "claude-4.5-sonnet",
  "choices": [
    {
      "index": 0,
      "message": { "role": "assistant", "content": "Hello! How can I help?" },
      "finish_reason": "stop"
    }
  ],
  "usage": { "prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15 }
}
```

### Streaming Response (SSE)

Server-Sent Events format:

```
data: {"choices":[{"delta":{"content":"Hello"}}]}
data: {"choices":[{"delta":{"content":" world"}}]}
data: [DONE]
```

### Error Response

```json
{
  "detail": "Error message",
  "status": 400
}
```

## Authentication

| Method    | Header                          | Description                            |
| --------- | ------------------------------- | -------------------------------------- |
| JWT Token | `Authorization: Bearer <token>` | WorkOS JWT with user_id, org_id claims |
| API Key   | `X-API-Key: <key>`              | Static API key for service-to-service  |

**JWT Claims Expected:**

- `user_id` - User identifier
- `org_id` - Organization identifier (multi-tenant)
- `permissions` - Permission array (cached for 5 minutes for performance)

## Available AI Models

**Google Vertex AI:**
| Model | Use Case |
|-------|----------|
| Claude 4.5 Sonnet | Recommended for quality & tool-use |
| Claude 4.5 Haiku | Recommended for speed/cost |
| Claude 3.7 Sonnet | Legacy support |
| Claude 3.7 Haiku | Legacy support |
| Gemini 2.5 Pro | Advanced reasoning |
| Gemini 2.5 Flash | Fast, multimodal |

**Fallback API:**

- Anthropic Claude API: https://api.anthropic.com/v1/messages

## 4-Level Prompt Orchestration

The system composes system prompts from 4 hierarchical levels:

| Level            | Source          | Purpose                         |
| ---------------- | --------------- | ------------------------------- |
| **Platform**     | Config file     | Default prompt for all users    |
| **Organization** | Database table  | Custom prompts per organization |
| **User**         | Database table  | User-specific customizations    |
| **Workflow**     | Config/Database | Workflow-specific context       |

**Composition Logic:** Platform + Organization + User + Workflow = Final System Prompt

**Variable Templating:** Prompts can include `{{customer_name}}`, `{{context}}` which are rendered via Jinja2 before sending to Claude.

## MCP Server Integration

**Registration Workflow:**

1. Register via CLI: `atoms-agent mcp create --org <uuid> --name "My Tool" --url https://mcp.example.com`
2. Store in Database with auth config (bearer token, OAuth, API key)
3. User enables specific servers from marketplace
4. System composes enabled servers into single MCP interface for Claude

**Server Scopes:** Platform (all users), Organization, User, Project

---

**Content merged from:** technical-documentation-backend.md

---

Copied count: 3
