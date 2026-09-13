<DONE>
# Implementation Roadmap - LiteLLM Harness Integration

**Date**: 2026-02-18
**Status**: Planning Complete - Ready for Implementation

---

## Overview

This document provides a step-by-step implementation roadmap for integrating LiteLLM Router with Codex CLI, Claude Code, and Factory Droid harnesses, plus enhancing `plan incorporate` with task validation.

---

## Phase 1: LiteLLM Router Responses API Handler

### Goal

Enable Codex CLI to work with LiteLLM Router by creating a Responses API handler.

### Step 1.1: Create `litellm_responses_handler.py`

**File**: `src/thegent/routing/litellm_responses_handler.py` (new)

**Implementation**:

```python
"""LiteLLM Router Responses API handler for Codex CLI compatibility."""

import json
import logging
import os
from typing import Any

from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.websockets import WebSocket

from thegent.routing.litellm_router import get_litellm_router

_log = logging.getLogger(__name__)


def _responses_input_to_messages(input_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Responses API input items to Chat Completions messages."""
    messages: list[dict[str, Any]] = []
    for item in input_items:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message":
            role = item.get("role", "user")
            content = item.get("content")
            if isinstance(content, list):
                parts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        parts.append(c.get("text", ""))
                content = "\n".join(parts) if parts else ""
            elif not isinstance(content, str):
                content = str(content) if content else ""
            messages.append({"role": role, "content": content})
    return messages


def _responses_to_chat_completions(body: dict[str, Any]) -> dict[str, Any]:
    """Transform Responses API request to Chat Completions format."""
    input_items = body.get("input", [])
    if not isinstance(input_items, list):
        input_items = []
    messages = _responses_input_to_messages(input_items)
    if not messages:
        messages = [{"role": "user", "content": ""}]

    return {
        "model": body.get("model", ""),
        "messages": messages,
        "stream": body.get("stream", False),
        "temperature": body.get("temperature"),
        "max_tokens": body.get("max_output_tokens") or body.get("max_tokens"),
    }


def _chat_completions_to_responses(chunk: dict[str, Any]) -> dict[str, Any] | None:
    """Transform Chat Completions SSE chunk to Responses API format."""
    choices = chunk.get("choices", [])
    if not choices:
        return None
    delta = choices[0].get("delta", {})
    content = delta.get("content", "")
    if not content:
        return None  # Skip empty chunks

    return {
        "type": "response.output_item.added",
        "item": {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
        },
    }


async def handle_responses_request(request: Request) -> Response:
    """Handle Responses API HTTP POST request via LiteLLM Router."""
    try:
        body = await request.body()
        data = json.loads(body) if body else {}

        # Translate Responses API → Chat Completions
        chat_request = _responses_to_chat_completions(data)
        model = chat_request["model"]
        stream = chat_request.get("stream", False)

        # Get LiteLLM Router
        router = get_litellm_router()

        if stream:
            return await handle_responses_stream(request, chat_request, router)
        else:
            # Non-streaming request
            from litellm import completion

            response = completion(
                model=model,
                messages=chat_request["messages"],
                **{k: v for k, v in chat_request.items() if k not in ("model", "messages", "stream")},
            )

            # Translate response back to Responses API format
            content = response.choices[0].message.content if response.choices else ""
            responses_data = {
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "text", "text": content}],
                    }
                ]
            }

            return Response(
                content=json.dumps(responses_data),
                status_code=200,
                headers={"Content-Type": "application/json"},
            )

    except Exception as e:
        _log.error("Error handling Responses API request: %s", e, exc_info=True)
        return Response(
            content=json.dumps({"error": {"message": str(e)}}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def handle_responses_stream(request: Request, chat_request: dict[str, Any], router) -> StreamingResponse:
    """Handle Responses API streaming request via LiteLLM Router."""
    from litellm import acompletion

    async def stream():
        try:
            model = chat_request["model"]
            messages = chat_request["messages"]

            async for chunk in router.acompletion(
                model=model,
                messages=messages,
                stream=True,
                **{k: v for k, v in chat_request.items() if k not in ("model", "messages", "stream")},
            ):
                # Translate Chat Completions → Responses API
                responses_event = _chat_completions_to_responses(
                    chunk.model_dump() if hasattr(chunk, "model_dump") else chunk
                )
                if responses_event:
                    yield f"data: {json.dumps(responses_event)}\n\n"

            # Send completion event
            yield 'data: {"type": "response.completed"}\n\n'

        except Exception as e:
            _log.error("Error in Responses API stream: %s", e, exc_info=True)
            yield f'data: {{"error": {{"message": "{str(e)}"}}}}\n\n'

    return StreamingResponse(
        stream(),
        status_code=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


async def handle_responses_websocket(websocket: WebSocket) -> None:
    """Handle Responses API WebSocket request via LiteLLM Router."""
    import asyncio

    await websocket.accept()

    try:
        # Receive request
        data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)

        # Translate to Chat Completions
        chat_request = _responses_to_chat_completions(data)
        model = chat_request["model"]
        messages = chat_request["messages"]

        # Get router
        router = get_litellm_router()

        # Stream response
        async for chunk in router.acompletion(
            model=model,
            messages=messages,
            stream=True,
            **{k: v for k, v in chat_request.items() if k not in ("model", "messages", "stream")},
        ):
            responses_event = _chat_completions_to_responses(
                chunk.model_dump() if hasattr(chunk, "model_dump") else chunk
            )
            if responses_event:
                await websocket.send_json(responses_event)

        # Send completion event
        await websocket.send_json({"type": "response.completed"})

    except Exception as e:
        _log.error("Error in Responses API WebSocket: %s", e, exc_info=True)
        await websocket.send_json({"error": {"message": str(e)}})
    finally:
        await websocket.close(1000)
```

**Checklist**:

- [ ] Create file
- [ ] Implement translation functions
- [ ] Implement HTTP POST handler
- [ ] Implement SSE streaming handler
- [ ] Implement WebSocket handler
- [ ] Add error handling
- [ ] Add logging

### Step 1.2: Update `cliproxy_adapter.py`

**File**: `src/thegent/cliproxy_adapter.py` (modify)

**Changes**:

1. Add import at top:

```python
import os
```

2. Modify `proxy_handler` function:

```python
async def proxy_handler(request: Request) -> Response:
    """Proxy /v1/* to backend. Transform /v1/responses to /v1/chat/completions."""
    backend = getattr(request.app.state, "backend_url", "http://127.0.0.1:8318/v1")
    path = request.url.path or "/v1/models"

    # Check if LiteLLM Router should be used
    use_litellm = os.environ.get("THGENT_USE_LITELLM_ROUTER", "0") == "1"

    if _log.isEnabledFor(logging.DEBUG) or __debug__:
        _log.debug("adapter request: %s %s (litellm=%s)", request.method, path, use_litellm)

    if not path.startswith("/v1/"):
        return Response("Not Found", status_code=404)

    # Route Responses API to LiteLLM Router if enabled
    if use_litellm and path == "/v1/responses" and request.method == "POST":
        try:
            from thegent.routing.litellm_responses_handler import handle_responses_request

            return await handle_responses_request(request)
        except Exception as e:
            _log.error("LiteLLM Router handler failed: %s", e, exc_info=True)
            # Fallback to CLIProxyAPIPlus
            pass

    backend_path = _backend_path(backend, path)
    # ... rest of existing code ...
```

3. Update `websocket_responses_handler`:

```python
async def websocket_responses_handler(websocket: Any) -> None:
    """Bridge WebSocket /v1/responses to HTTP streaming. Buffers SSE by line."""
    import asyncio

    # Check if LiteLLM Router should be used
    use_litellm = os.environ.get("THGENT_USE_LITELLM_ROUTER", "0") == "1"

    if use_litellm:
        try:
            from thegent.routing.litellm_responses_handler import handle_responses_websocket

            await handle_responses_websocket(websocket)
            return
        except Exception as e:
            _log.error("LiteLLM Router WebSocket handler failed: %s", e, exc_info=True)
            # Fallback to CLIProxyAPIPlus
            pass

    # Existing CLIProxyAPIPlus WebSocket handling...
    ...
```

**Checklist**:

- [ ] Add environment variable check
- [ ] Route `/v1/responses` to LiteLLM handler
- [ ] Update WebSocket handler
- [ ] Maintain backward compatibility
- [ ] Add error handling

### Step 1.3: Update `litellm_router.py`

**File**: `src/thegent/routing/litellm_router.py` (modify)

**Changes**:

1. Ensure router instance can be accessed:

```python
# Add global router instance (lazy initialization)
_router_instance: Router | None = None
_router_lock = threading.Lock()


def get_litellm_router_instance(policy: str | None = None) -> Router:
    """Get or create LiteLLM Router instance (singleton)."""
    global _router_instance

    with _router_lock:
        if _router_instance is None:
            _router_instance = get_litellm_router(policy)
        return _router_instance
```

2. Export function for handler:

```python
# At module level, export get_litellm_router for handler
# (get_litellm_router already exists, just ensure it's accessible)
```

**Checklist**:

- [ ] Ensure router can be accessed from handler
- [ ] Add singleton pattern if needed
- [ ] Verify model list includes Codex CLI models

### Step 1.4: Testing

**Test Cases**:

1. **HTTP POST `/v1/responses` (non-streaming)**:

```bash
curl -X POST http://localhost:8765/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-dummy" \
  -d '{
    "model": "gpt-5-mini",
    "input": [{"type": "message", "role": "user", "content": [{"type": "text", "text": "Hello"}]}],
    "stream": false
  }'
```

2. **HTTP POST `/v1/responses` (streaming)**:

```bash
curl -X POST http://localhost:8765/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-dummy" \
  -d '{
    "model": "gpt-5-mini",
    "input": [{"type": "message", "role": "user", "content": [{"type": "text", "text": "Hello"}]}],
    "stream": true
  }'
```

3. **Codex CLI**:

```bash
export OPENAI_BASE_URL=http://localhost:8765
export OPENAI_API_KEY=sk-dummy
export THGENT_USE_LITELLM_ROUTER=1
codex exec - --model gpt-5-mini <<< "Hello"
```

**Checklist**:

- [ ] Test HTTP POST non-streaming
- [ ] Test HTTP POST streaming
- [ ] Test WebSocket
- [ ] Test Codex CLI
- [ ] Test error handling
- [ ] Test model routing

---

## Phase 2: Claude Code Integration

### Goal

Route Claude Code (`clode`) through LiteLLM Router.

### Step 2.1: Update `CodexProxyRunner`

**File**: `src/thegent/agents/codex_proxy.py` (modify)

**Changes**:

1. Add `use_litellm_router` parameter to `__init__`:

```python
def __init__(
    self,
    agent_name: str,
    settings: ThegentSettings | None = None,
    model: str = "",
    use_litellm_router: bool = False,  # NEW
) -> None:
    if agent_name not in _PROXY_MODEL:
        raise ValueError(f"Unknown proxy agent: {agent_name}")
    self.agent_name = agent_name
    self._settings = settings or ThegentSettings()
    self._model = model or _PROXY_MODEL[agent_name]
    self._use_litellm_router = use_litellm_router or (os.environ.get("THGENT_USE_LITELLM_ROUTER", "0") == "1")
```

2. Add LiteLLM Router path in `run` method:

```python
def run(
    self,
    prompt: str,
    cwd: Path | None,
    mode: str,
    timeout: int,
    *,
    use_stream: bool = True,
    live_output: bool = False,
    on_stdout: Callable[[str], None] | None = None,
    on_stderr: Callable[[str], None] | None = None,
    agent_model: str | None = None,
    enable_search: bool = True,
    run_id: str | None = None,
) -> RunResult:
    model = agent_model or self._model

    # Use LiteLLM Router if enabled
    if self._use_litellm_router:
        return self._run_via_litellm_router(
            prompt, cwd, mode, timeout, model, use_stream, live_output, on_stdout, on_stderr
        )

    # Existing CLIProxyAPIPlus path...
    ...
```

3. Add `_run_via_litellm_router` method:

```python
def _run_via_litellm_router(
    self,
    prompt: str,
    cwd: Path | None,
    mode: str,
    timeout: int,
    model: str,
    use_stream: bool,
    live_output: bool,
    on_stdout: Callable[[str], None] | None,
    on_stderr: Callable[[str], None] | None,
) -> RunResult:
    """Run via LiteLLM Router directly (no Codex CLI)."""
    try:
        from thegent.routing.litellm_router import get_litellm_router
        from litellm import acompletion
        import asyncio

        router = get_litellm_router()

        messages = [{"role": "user", "content": prompt}]

        if use_stream:
            # Streaming response
            output_parts = []

            async def stream_response():
                async for chunk in router.acompletion(
                    model=model,
                    messages=messages,
                    stream=True,
                    timeout=timeout,
                ):
                    content = ""
                    if hasattr(chunk, "choices") and chunk.choices:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content"):
                            content = delta.content or ""
                    elif isinstance(chunk, dict):
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")

                    if content:
                        output_parts.append(content)
                        if live_output and on_stdout:
                            on_stdout(content)

            asyncio.run(stream_response())
            stdout = "".join(output_parts)
        else:
            # Non-streaming response
            response = asyncio.run(
                router.acompletion(
                    model=model,
                    messages=messages,
                    timeout=timeout,
                )
            )

            if hasattr(response, "choices") and response.choices:
                stdout = response.choices[0].message.content or ""
            elif isinstance(response, dict):
                stdout = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                stdout = str(response)

        return RunResult(
            exit_code=0,
            stdout=stdout,
            stderr="",
            timed_out=False,
        )

    except Exception as e:
        logger.error(f"LiteLLM Router execution failed: {e}", exc_info=True)
        return RunResult(
            exit_code=1,
            stdout="",
            stderr=f"LiteLLM Router error: {e}",
            timed_out=False,
        )
```

**Checklist**:

- [ ] Add `use_litellm_router` parameter
- [ ] Implement `_run_via_litellm_router`
- [ ] Update `run` method
- [ ] Test Claude Code integration

### Step 2.2: Update `clode_main.py`

**File**: `src/thegent/clode_main.py` (modify)

**Changes**:

1. Check for LiteLLM Router option:

```python
# In _run_model_interactive or similar function
use_litellm = os.environ.get("THGENT_USE_LITELLM_ROUTER", "0") == "1"

# When creating CodexProxyRunner
runner = CodexProxyRunner(
    agent_name="claude",
    settings=settings,
    model=model,
    use_litellm_router=use_litellm,
)
```

**Checklist**:

- [ ] Add LiteLLM Router option
- [ ] Update runner creation
- [ ] Test integration

### Step 2.3: Model Configuration

**File**: `src/thegent/routing/litellm_router.py` (modify)

**Changes**:

1. Ensure Claude Code models are in model list:

```python
# In build_litellm_model_list()
# Verify these models are included:
claude_models = [
    "claude-opus-4.6",
    "claude-sonnet-4.5",
    "claude-haiku-4.5",
    "composer-1.5",
    "composer-1.5-high",
    "composer-1.5-spark",
]
```

**Checklist**:

- [ ] Verify model list includes Claude Code models
- [ ] Configure fallback chains
- [ ] Set up cost tracking

---

## Phase 3: Factory Droid Integration

### Goal

Route Factory Droid through LiteLLM Router.

### Step 3.1: Update `DroidRunner`

**File**: `src/thegent/agents/droid.py` (modify)

**Changes**:

1. Add LiteLLM Router option:

```python
def __init__(
    self,
    droid_name: str,
    droids_dir: Path,
    droid_cmd: str = "droid",
    model: str = "custom:MiniMax-M2.5",
    use_litellm_router: bool = False,  # NEW
) -> None:
    self.droid_name = droid_name
    self.droids_dir = droids_dir.expanduser().resolve()
    self._droid_cmd = _resolve_droid_cmd(droid_cmd)
    self._model = model
    self._use_litellm_router = use_litellm_router or (os.environ.get("THGENT_USE_LITELLM_ROUTER", "0") == "1")
```

2. Update `run` method to use LiteLLM Router endpoint:

```python
def run(...) -> RunResult:
    if self._use_litellm_router:
        # Configure droid to use LiteLLM Router endpoint
        env = os.environ.copy()
        env["OPENAI_BASE_URL"] = "http://localhost:8765/v1"
        env["OPENAI_API_KEY"] = "sk-dummy"
        # Model mapping happens in LiteLLM Router config
        # Use model alias that LiteLLM Router understands
        litellm_model = self._map_droid_model_to_litellm(self._model)
        # Continue with droid exec but pointing to LiteLLM Router
        ...

    # Existing droid exec path...
    ...
```

3. Add model mapping function:

```python
def _map_droid_model_to_litellm(self, droid_model: str) -> str:
    """Map Factory Droid model names to LiteLLM model aliases."""
    mapping = {
        "Qwen3 Coder [CEREBRAS]": "qwen3-coder",
        "GLM-4.6 [Z.AI]": "glm-5",  # or "z-ai/glm-5"
        "MiniMax-M2.5": "minimax-m2.5",
        "custom:MiniMax-M2.5": "minimax-m2.5",
    }
    return mapping.get(droid_model, droid_model)
```

**Checklist**:

- [ ] Add `use_litellm_router` parameter
- [ ] Update `run` method
- [ ] Add model mapping
- [ ] Test Factory Droid integration

---

## Phase 4: Plan Incorporate Enhancement

### Goal

Add task validation during `plan incorporate` command.

### Step 4.1: Find `incorporate_impl`

**File**: `src/thegent/cli_impl.py` (find and modify)

**Current**: Need to locate `incorporate_impl` function

**Expected Location**: `src/thegent/cli_impl.py`

**Search**:

```bash
grep -n "def incorporate_impl" src/thegent/cli_impl.py
```

### Step 4.2: Add Validation

**Changes**:

1. Import validators:

```python
from thegent.task import validate_task_file, WorkStreamSync
from pathlib import Path
```

2. Add validation before merging:

```python
def incorporate_impl(cd: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Merge fragments from 02-UNIFIED-WBS into WORK_STREAM.md."""
    cwd = _resolve_cwd(cd)
    if cwd is None:
        cwd = Path.cwd()

    # NEW: Validate task files before incorporation
    tasks_dir = cwd / "tasks"
    if tasks_dir.exists() and tasks_dir.is_dir():
        validation_errors = []
        task_files = list(tasks_dir.glob("*.md"))

        for task_file in task_files:
            try:
                result = validate_task_file(task_file)
                if not result.valid:
                    validation_errors.append(
                        {
                            "file": str(task_file),
                            "errors": result.errors,
                        }
                    )
            except Exception as e:
                validation_errors.append(
                    {
                        "file": str(task_file),
                        "errors": [f"Validation failed: {e}"],
                    }
                )

        if validation_errors:
            return {
                "error": "Task validation failed",
                "validation_errors": validation_errors,
                "merged": 0,
            }

    # Existing incorporation logic...
    result = _existing_incorporate_logic(cwd, dry_run)

    # NEW: Auto-sync to WORK_STREAM.md after successful incorporation
    if not dry_run and result.get("merged", 0) > 0:
        try:
            work_stream_path = cwd / "docs" / "reference" / "WORK_STREAM.md"
            if work_stream_path.exists() and tasks_dir.exists():
                sync = WorkStreamSync(work_stream_path, tasks_dir)
                sync_result = sync.update_work_stream_from_tasks()
                result["synced_tasks"] = sync_result.get("tasks_synced", 0)
        except Exception as e:
            _log.warning("Failed to sync tasks to WORK_STREAM.md: %s", e)
            result["sync_warning"] = str(e)

    return result
```

**Checklist**:

- [ ] Find `incorporate_impl` function
- [ ] Add task validation
- [ ] Add auto-sync to WORK_STREAM.md
- [ ] Add error reporting
- [ ] Test with valid/invalid tasks

---

## Phase 5: Testing & Documentation

### Testing Checklist

#### Unit Tests

- [ ] Test Responses API translation functions
- [ ] Test LiteLLM Router integration
- [ ] Test error handling
- [ ] Test model routing

#### Integration Tests

- [ ] Test Codex CLI end-to-end
- [ ] Test Claude Code end-to-end
- [ ] Test Factory Droid end-to-end
- [ ] Test plan incorporate validation

#### Performance Tests

- [ ] Measure routing latency
- [ ] Test caching effectiveness
- [ ] Test load balancing

### Documentation

- [ ] Update user documentation
- [ ] Create migration guide
- [ ] Document configuration options
- [ ] Add examples

---

## Implementation Order

1. **Phase 1** (Week 1): LiteLLM Router Responses API Handler
2. **Phase 2** (Week 2): Claude Code Integration
3. **Phase 3** (Week 2): Factory Droid Integration
4. **Phase 4** (Week 2): Plan Incorporate Enhancement
5. **Phase 5** (Week 3): Testing & Documentation

---

## Success Criteria

- ✅ Codex CLI works with LiteLLM Router
- ✅ Claude Code works with LiteLLM Router
- ✅ Factory Droid works with LiteLLM Router
- ✅ Plan incorporate validates tasks
- ✅ All tests pass
- ✅ Documentation complete

---

**Status**: Ready for Implementation
**Next Step**: Begin Phase 1, Step 1.1 (Create `litellm_responses_handler.py`)
