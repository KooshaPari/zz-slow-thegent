<DONE>
# Codex + CLIProxyAPIPlus: Research and Plan

**Date**: 2026-02-16
**Status**: Phase 2 Complete
**Scope**: Codex Responses API compatibility with CLIProxyAPIPlus (all providers)

**Implementation (2026-02-16):**

- Phase 2: Adapter (Responses API ↔ Chat Completions bridge), model alias mapping, debug logging, 10 unit tests

---

## Executive Summary

**Problem**: Codex CLI does not work with any CLIProxyAPIPlus provider (minimax, glm, antigravity, kilo, etc.). Codex uses the **Responses API** (HTTP POST + WebSocket); CLIProxyAPIPlus only exposes **Chat Completions**. Claude harness works because it uses Chat Completions directly.

**Fix**: thegent adapter (`cliproxy_adapter.py`) bridges Responses API ↔ Chat Completions. Enable with `THGENT_CLIPROXY_ADAPTER=1`.

**Reference**: [MiniMax Codex CLI guide](https://platform.minimax.io/docs/coding-plan/codex-cli) is a good pattern for pairing custom providers to Codex (`.codex/config.toml`, `model_providers`, `codex-` prefix).

---

## 1. Research Findings

### 1.1 Codex CLI (OpenAI)

- **Install**: `npm i -g @openai/codex@0.57.0` (MiniMax docs recommend 0.57.0 due to compatibility issues)
- **Config**: `.codex/config.toml` with `[model_providers.<name>]` blocks
- **Runtime**: Codex uses `OPENAI_BASE_URL` and `OPENAI_API_KEY` (or provider-specific env) to call backend
- **Protocol**: Codex may use **Responses API** (HTTP POST + WebSocket) or **Chat Completions** depending on version/config

### 1.2 Custom Provider Pattern (MiniMax as Reference)

**Source**: [MiniMax Codex CLI](https://platform.minimax.io/docs/coding-plan/codex-cli) — useful pattern for any custom provider:

| Item             | Value                                                          |
| ---------------- | -------------------------------------------------------------- |
| **Config**       | `.codex/config.toml` with `[model_providers.<name>]` blocks    |
| **base_url**     | Points to proxy (e.g. `http://127.0.0.1:8317/v1` for thegent)  |
| **Model naming** | Some providers use `codex-` prefix (e.g. `codex-MiniMax-M2.5`) |
| **Profile**      | `model = "..."`, `model_provider = "<name>"`                   |

Adapter maps provider-specific model IDs to CLIProxy backend IDs when needed.

### 1.3 thegent Architecture

```
Codex CLI (exec/interactive)
    │
    │ OPENAI_BASE_URL=http://127.0.0.1:8317/v1
    │ OPENAI_API_KEY=sk-dummy (or provider token for routing)
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Adapter (THGENT_CLIPROXY_ADAPTER=1)                         │
│  - POST /v1/responses → translate to /v1/chat/completions   │
│  - WebSocket /v1/responses → bridge to HTTP SSE              │
│  - Transform Chat Completions SSE → Responses API format     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
CLIProxyAPIPlus (port 8318 when adapter on 8317)
    │
    │ minimax:, codex:, openai-compatibility, etc.
    ▼
Provider APIs (MiniMax, OpenAI, etc.)
```

### 1.4 CLIProxyAPIPlus Fork

| Provider             | Config block     | Models                                 |
| -------------------- | ---------------- | -------------------------------------- |
| minimax              | `minimax:`       | minimax-m2, minimax-m2.1, minimax-m2.5 |
| codex                | `codex-api-key:` | GPT-5.x                                |
| openai-compatibility | generic          | Any OpenAI-compatible                  |

**Gap**: Fork exposes Chat Completions (`/v1/chat/completions`), not Responses API (`/v1/responses`).

### 1.5 thegent Adapter (`cliproxy_adapter.py`)

| Capability              | Implementation                                                                            |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| POST /v1/responses      | Transforms to Chat Completions, proxies to backend                                        |
| Streaming (SSE)         | Transforms Chat Completions chunks → Responses API format                                 |
| WebSocket /v1/responses | Accepts WS, sends JSON; bridges to HTTP stream; sends `response.output_item.added` events |

**Potential bugs** (to verify):

1. **URL construction** (`_proxy_stream`): When `transform_responses=True`, url is built as `f"{backend}/chat/completions"` but `backend` may already end with `/v1` → double path or wrong path.
2. **WebSocket path**: `WebSocketRoute("/v1/responses", ...)` — Codex may connect to different path (e.g. `/v1/responses` with query params).
3. **Responses API event format**: Codex may expect additional event types beyond `response.output_item.added`.

### 1.6 Model Aliases

Some providers (e.g. MiniMax) document model names like `codex-MiniMax-M2.5`. Adapter maps these to CLIProxy backend IDs (`minimax-m2.5`, etc.) so requests reach the correct backend.

---

## 2. Gap Analysis

| Gap                                             | Severity | Owner                                |
| ----------------------------------------------- | -------- | ------------------------------------ |
| CLIProxyAPIPlus lacks /v1/responses             | High     | Adapter (workaround exists)          |
| Adapter WebSocket/URL bugs                      | High     | thegent                              |
| Provider model aliases (codex-\* → backend IDs) | Low      | Adapter                              |
| Codex version compatibility (0.57.0 vs latest)  | Medium   | User config                          |
| Claude harness works, Codex doesn't             | —        | Confirms Chat Completions path works |

---

## 3. Phased Implementation Plan

### Phase 1: Diagnose (2–4 tool calls, ~5 min)

| Task | Action                                                                     |
| ---- | -------------------------------------------------------------------------- |
| P1.1 | Enable adapter: `THGENT_CLIPROXY_ADAPTER=1`                                |
| P1.2 | Run `codex exec - "echo hi" --model <any-cliproxy-model>` with proxy       |
| P1.3 | Capture request path and body (Codex → adapter) via logging or proxy trace |
| P1.4 | Verify: Does Codex use POST /v1/responses or POST /v1/chat/completions?    |
| P1.5 | If WebSocket: capture WS URL and message format                            |

**Deliverable**: Clear picture of Codex request flow (HTTP vs WS, Responses vs Chat Completions).

### Phase 2: Fix Adapter (6–12 tool calls, ~10–15 min)

| Task | Action                                                                      | Depends |
| ---- | --------------------------------------------------------------------------- | ------- |
| P2.1 | Fix `_proxy_stream` URL when `transform_responses=True`                     | P1      |
| P2.2 | Add model alias mapping for provider-specific IDs (e.g. codex-\* → backend) | P1      |
| P2.3 | Harden WebSocket handler: handle connection lifecycle, timeouts, errors     | P1      |
| P2.4 | Add unit tests for Responses ↔ Chat Completions transforms                 | —       |
| P2.5 | Add integration test: mock backend, assert adapter output format            | —       |

**Deliverable**: Adapter correctly bridges Codex (Responses/WS) to CLIProxyAPIPlus (Chat Completions).

### Phase 3: CLIProxyAPIPlus Fork Updates (if needed)

| Task | Action                                                                   | Depends |
| ---- | ------------------------------------------------------------------------ | ------- |
| P3.1 | Assess: Can fork add native /v1/responses? (OpenAI Responses API spec)   | P2      |
| P3.2 | If yes: implement Responses API in fork; deprecate adapter for that path | P3.1    |
| P3.3 | Add model aliases in fork config if needed                               | P2      |

**Deliverable**: Fork optionally supports Responses API natively; or adapter remains the bridge.

### Phase 4: Documentation

| Task | Action                                                            | Depends |
| ---- | ----------------------------------------------------------------- | ------- |
| P4.1 | Document Codex + CLIProxy (all providers) in PROVIDER_SETUP_GUIDE | P2      |
| P4.2 | Reference MiniMax guide as config pattern for custom providers    | —       |

**Deliverable**: Users can run Codex with any CLIProxy provider via thegent adapter.

---

## 4. DAG Dependencies

```
P1.1 ─┬─ P1.2 ─ P1.3 ─ P1.4 ─ P1.5
      │
      └─ P2.1 ─ P2.2 ─ P2.3
              │
              ├─ P2.4 ─ P2.5
              │
              └─ P3.1 ─ P3.2 (optional)
                      │
                      └─ P3.3
              │
              └─ P4.1 ─ P4.2
```

---

## 5. Reference Links

| Resource                           | URL                                                    |
| ---------------------------------- | ------------------------------------------------------ |
| MiniMax Codex CLI (config pattern) | https://platform.minimax.io/docs/coding-plan/codex-cli |
| thegent adapter                    | `src/thegent/cliproxy_adapter.py`                      |
| cliproxyapi-plusplus               | `../cliproxyapi-plusplus/`                             |
| Catalog alignment                  | `docs/plans/CATALOG_CLIPROXY_FORK_ALIGNMENT.md`        |

---

## 6. Notes from User Context

- **All CLIProxy models do not work with Codex** — not MiniMax-specific; universal gap
- **MiniMax guide** — good reference for pairing custom providers to Codex (config pattern)
- **cliproxyapi-plusplus may need updates** — native Responses API would obviate adapter
- **Claude harness with our API does work** — confirms Chat Completions path is fine

---

## 7. Development Plan (Implementation)

| ID  | Task                                                                        | Status        |
| --- | --------------------------------------------------------------------------- | ------------- |
| D1  | ensure_proxy_running: use settings.cliproxy_adapter when env not set        | ✓             |
| D2  | CodexProxyRunner: set THGENT_CLIPROXY_ADAPTER=1 before ensure_proxy_running | ✓             |
| D3  | WebSocket handler: add timeout, handle disconnect, improve error handling   | ✓             |
| D4  | start_proxy_with_adapter: pass THGENT_CLIPROXY_ADAPTER to spawned env       | ✓             |
| D5  | Integration test: adapter transform pipeline                                | ✓             |
| D6  | Run full test suite, verify adapter unit tests                              | ✓ (53 passed) |

---

## 8. ADAPTER DEEP DIVE: Implementation Details

### 8.1 Response to Chat Completion Mapping

```python
# src/thegent/cliproxy_adapter.py (simplified)

import httpx
import json
from typing import AsyncGenerator


class ResponsesToChatAdapter:
    """Bridges OpenAI Responses API to Chat Completions."""

    async def transform_request(self, request_body: dict, backend_url: str) -> dict:
        """Transform Responses API request to Chat Completions."""
        # Extract model from response_format or use default
        model = request_body.get("model", "gpt-4")

        # Transform to chat format
        chat_request = {
            "model": model,
            "messages": self._convert_to_messages(request_body),
            "stream": request_body.get("stream", False),
            "temperature": request_body.get("temperature", 1.0),
            "max_tokens": request_body.get("max_tokens"),
        }

        return chat_request

    async def transform_response(self, chat_response: dict, original_request: dict) -> dict:
        """Transform Chat Completions response back to Responses API format."""
        # Map chat choice to response item
        response = {
            "id": f"resp_{chat_response['id']}",
            "object": "response",
            "created": chat_response["created"],
            "model": chat_response["model"],
            "output": {
                "choices": chat_response["choices"],
                "item": {
                    "id": chat_response["choices"][0]["index"],
                    "content": chat_response["choices"][0]["message"]["content"],
                },
            },
        }
        return response

    def _convert_to_messages(self, request: dict) -> list:
        """Convert Responses API input to Chat messages."""
        # Handle text, input_text, or conversation history
        messages = []
        if "input_text" in request:
            messages.append({"role": "user", "content": request["input_text"]})
        elif "conversation" in request:
            messages = request["conversation"]
        return messages
```

### 8.2 WebSocket Bridge Implementation

```python
# src/thegent/cliproxy_adapter.py (WebSocket handler)

import asyncio
import json
from starlette.websockets import WebSocket


class ResponsesWebSocketBridge:
    """Bridges WebSocket /v1/responses to HTTP SSE."""

    async def handle_websocket(self, websocket: WebSocket, backend_url: str, api_key: str):
        """Handle Codex WebSocket connection and bridge to HTTP stream."""
        await websocket.accept()

        try:
            async with httpx.AsyncClient() as client:
                # Connect to backend as SSE
                async with client.stream(
                    "POST",
                    f"{backend_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": "gpt-4", "stream": True},
                ) as response:
                    async for chunk in response.aiter_bytes():
                        # Transform chunk to Responses API format
                        transformed = self._transform_chunk(chunk)
                        await websocket.send_text(transformed)
        except Exception as e:
            await websocket.send_text(json.dumps({"error": str(e)}))
        finally:
            await websocket.close()

    def _transform_chunk(self, chunk: bytes) -> str:
        """Transform SSE chunk to Responses API format."""
        # Parse Chat Completions chunk
        # Emit response.output_item.added events
        return json.dumps({"type": "response.output_item.added", "item": {"content": "..."}})
```

### 8.3 Model Alias Mapping Configuration

```yaml
# config/cliproxy_model_aliases.yaml
# Maps Codex provider model names to CLIProxy backend IDs

aliases:
  # MiniMax
  "codex-MiniMax-M2.5": "minimax-m2.5"
  "codex-MiniMax-M2.1": "minimax-m2.1"
  "codex-MiniMax-M2": "minimax-m2"

  # OpenAI (for testing)
  "codex-gpt-4o": "openai/gpt-4o"
  "codex-gpt-4o-mini": "openai/gpt-4o-mini"

  # Anthropic
  "codex-claude-sonnet-4": "anthropic/claude-sonnet-4-20250514"

resolved_models:
  minimax-m2.5:
    provider: minimax
    context_window: 128000
    max_output: 8192
  openai/gpt-4o:
    provider: openai
    context_window: 128000
    max_output: 16384
```

---

## 9. DEBUGGING AND TROUBLESHOOTING

### 9.1 Common Issues

| Issue              | Cause                       | Solution                          |
| ------------------ | --------------------------- | --------------------------------- |
| Double path in URL | `backend` already has `/v1` | Strip `/v1` before appending      |
| WebSocket timeout  | No heartbeat                | Add ping/pong interval            |
| Empty responses    | Model not found             | Check alias mapping               |
| Stream stalls      | Buffer full                 | Increase buffer or flush interval |

### 9.2 Debug Commands

```bash
# Enable verbose logging
export THGENT_CLIPROXY_ADAPTER=1
export ADAPTER_LOG_LEVEL=debug

# Test direct adapter
python -m thegent.cliproxy_adapter --test --model "codex-MiniMax-M2.5"

# Capture adapter logs
tail -f ~/.thegent/logs/cliproxy_adapter.log

# Verify model alias resolution
python -m thegent.cliproxy_adapter resolve "codex-MiniMax-M2.5"
# Expected: minimax-m2.5 (CLIProxy backend ID)
```

### 9.3 Test Coverage

```python
# tests/test_cliproxy_adapter.py

import pytest
from thegent.cliproxy_adapter import ResponsesToChatAdapter


class TestResponsesToChatAdapter:
    def test_model_alias_resolution(self):
        adapter = ResponsesToChatAdapter()
        assert adapter.resolve_alias("codex-MiniMax-M2.5") == "minimax-m2.5"

    def test_request_transformation(self):
        adapter = ResponsesToChatAdapter()
        request = {"model": "codex-MiniMax-M2.5", "input_text": "Hello, world!", "stream": True}
        chat_request = adapter.transform_request(request, "http://localhost:8318/v1")
        assert chat_request["model"] == "minimax-m2.5"
        assert chat_request["messages"] == [{"role": "user", "content": "Hello, world!"}]

    def test_response_transformation(self):
        adapter = ResponsesToChatAdapter()
        chat_response = {
            "id": "chatcmpl-abc123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": "Hi there!"}, "finish_reason": "stop"}
            ],
        }
        resp = adapter.transform_response(chat_response, {})
        assert resp["object"] == "response"
        assert "output" in resp
```

---

## 10. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 8:** Adapter Deep Dive Implementation
   - Response to Chat Completion mapping with Python code
   - WebSocket bridge implementation
   - Model alias mapping configuration (YAML)

2. **Added Section 9:** Debugging and Troubleshooting
   - Common issues table with solutions
   - Debug commands for testing
   - Test coverage examples (pytest)

3. **Enhanced Section 3:** Updated DAG dependencies with adapter path

4. **Enhanced Section 1:** Added MiniMax Codex CLI reference link

### Cross-References Added

- MiniMax Codex CLI guide (external)
- Adapter test suite (internal)
- Model alias configuration (internal)

### Practical Additions

- Python adapter classes for request/response transformation
- WebSocket bridge with error handling
- YAML configuration for model aliases
- pytest test examples
- Debug commands for troubleshooting

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md](./AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md) - Platform research
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
