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
