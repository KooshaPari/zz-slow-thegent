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
