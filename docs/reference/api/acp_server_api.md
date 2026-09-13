# acp_server API Reference

> **Source**: `src/thegent/adapters/acp_server.py`

ACP (Agent Communication Protocol) Server Adapter.

Wraps thegent agent capabilities as an ACP-compatible HTTP endpoint using
Starlette, consistent with the existing MCP server pattern.

ACP request format:
{"type": "task", "payload": {...}, "agent_id": "..."}

ACP response format:
{"type": "result", "result": {...}, "agent_id": "..."}

JSON-RPC methods supported (over HTTP POST /rpc and stdio): - initialize -&gt; server capabilities - agent/spawn -&gt; spawn an agent with a prompt, returns result - agent/message -&gt; send a follow-up message to an existing session - agent/stop -&gt; stop an active session - session/attach -&gt; attach to or create a named mux session - session/inspect -&gt; capture pane output from a mux session - session/send -&gt; send keystrokes to a mux session

Independently startable::

    python -m thegent.adapters.acp_server            # stdio
    python -m thegent.adapters.acp_server --http     # HTTP on port 8420

---

## ACPServerAdapter

Wraps thegent agent capabilities as an ACP-compatible endpoint.

Handles both simple task/result messages (native ACP format) and the
JSON-RPC method envelope used by the stdio transport.

ACP message flow:
Client -&gt; {"type": "task", "payload": {...}, "agent_id": "..."}
Server -&gt; {"type": "result", "result": {...}, "agent_id": "..."}

### Methods

#### ACPServerAdapter.**init**

```python
__init__(self: Any, session_endpoints: Any)
```

---

#### ACPServerAdapter.build_starlette_app

```python
build_starlette_app(self: Any)
```

Build a Starlette ASGI application exposing the ACP server over HTTP.

Endpoints:
GET /health Liveness probe.
POST /rpc JSON-RPC 2.0 endpoint.
POST /acp Native ACP message endpoint.

---

#### ACPServerAdapter.run_http

```python
run_http(self: Any, host: str, port: int)
```

Start the HTTP server (blocking).

**Parameters**:

- `host`: Bind address (default `127.0.0.1`).
- `port`: Bind port (default :data:`ACP_DEFAULT_PORT`).

---

---

## AgentSession

Represents an active ACP agent session.

### Methods

#### AgentSession.**init**

```python
__init__(self: Any, session_id: str, runner: AgentRunner, cwd: Any)
```

---

#### AgentSession.add_message

```python
add_message(self: Any, role: str, content: str)
```

Append a message to the session conversation history.

---

#### AgentSession.stop

```python
stop(self: Any)
```

Signal the session to stop.

---

---

## SessionEndpoints

Wraps session-backend calls for the session/\* ACP RPC methods.

Keeps session management logic separate from agent lifecycle logic for
testability. Callers should use :meth:`get_or_resolve_backend` rather
than constructing a backend themselves so that the backend is shared and
lazily resolved.

# @trace FR-SES-001

### Methods

#### SessionEndpoints.**init**

```python
__init__(self: Any, backend: Any)
```

Create a `SessionEndpoints` instance.

**Parameters**:

- `backend`: Optional pre-constructed backend. When _None_ the backend
  is resolved lazily on first use via
  :func:`~thegent.session.resolve_session_backend`.

---

#### SessionEndpoints.attach

```python
attach(self: Any, session_name: str)
```

Attach to _session_name_, creating it if it does not exist.

Returns a dict with `session_id` (same as _session_name_ for
backend-managed sessions) and `status` (`"attached"` or
`"created"`).

# @trace FR-SES-001

---

#### SessionEndpoints.get_or_resolve_backend

```python
get_or_resolve_backend(self: Any)
```

Return the session backend, resolving it lazily if needed.

---

#### SessionEndpoints.inspect

```python
inspect(self: Any, session_id: str, last_lines: int)
```

Capture _last_lines_ lines of output from _session_id_.

Returns a dict with `lines` (list[str]) and `backend` (str name).

# @trace FR-SES-001

---

#### SessionEndpoints.send

```python
send(self: Any, session_id: str, text: str)
```

Send _text_ (and optionally a carriage return) to _session_id_.

The send is implemented as `zmx send-keys` semantics: if _enter_ is
True, a newline character is appended. Returns `{"success": bool}`.

# @trace FR-SES-001

---

---

## add_message

```python
add_message(self: Any, role: str, content: str)
```

Append a message to the session conversation history.

---

## attach

```python
attach(self: Any, session_name: str)
```

Attach to _session_name_, creating it if it does not exist.

Returns a dict with `session_id` (same as _session_name_ for
backend-managed sessions) and `status` (`"attached"` or
`"created"`).

# @trace FR-SES-001

---

## build_starlette_app

```python
build_starlette_app(self: Any)
```

Build a Starlette ASGI application exposing the ACP server over HTTP.

Endpoints:
GET /health Liveness probe.
POST /rpc JSON-RPC 2.0 endpoint.
POST /acp Native ACP message endpoint.

---

## cli

```python
cli(http: bool, host: str, port: int, log_level: str)
```

Run ACP server in stdio mode by default, or HTTP mode with `--http`.

---

## get_or_resolve_backend

```python
get_or_resolve_backend(self: Any)
```

Return the session backend, resolving it lazily if needed.

---

## inspect

```python
inspect(self: Any, session_id: str, last_lines: int)
```

Capture _last_lines_ lines of output from _session_id_.

Returns a dict with `lines` (list[str]) and `backend` (str name).

# @trace FR-SES-001

---

## main

CLI entry point. Use `--http` flag to start HTTP server.

---

## run_http

```python
run_http(self: Any, host: str, port: int)
```

Start the HTTP server (blocking).

**Parameters**:

- `host`: Bind address (default `127.0.0.1`).
- `port`: Bind port (default :data:`ACP_DEFAULT_PORT`).

---

## send

```python
send(self: Any, session_id: str, text: str)
```

Send _text_ (and optionally a carriage return) to _session_id_.

The send is implemented as `zmx send-keys` semantics: if _enter_ is
True, a newline character is appended. Returns `{"success": bool}`.

# @trace FR-SES-001

---

## stop

```python
stop(self: Any)
```

Signal the session to stop.

---
