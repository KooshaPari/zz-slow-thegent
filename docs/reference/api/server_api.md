# server API Reference

> **Source**: `src/thegent/acp/server.py`

ACP server adapter for exposing thegent agents via ACP protocol.

---

## ACPServerAdapter

Exposes thegent agents via ACP protocol (JSON-RPC over stdio).

### Methods

#### ACPServerAdapter.**init**

```python
__init__(self: Any)
```

Initialize ACP server adapter.

---

---

## AgentSession

Represents an active agent session.

### Methods

#### AgentSession.**init**

```python
__init__(self: Any, agent_id: str, runner: AgentRunner, cwd: Any)
```

Initialize agent session.

---

#### AgentSession.add_message

```python
add_message(self: Any, role: str, content: str)
```

Add a message to conversation history.

---

#### AgentSession.stop

```python
stop(self: Any)
```

Stop the session.

---

---

## add_message

```python
add_message(self: Any, role: str, content: str)
```

Add a message to conversation history.

---

## stop

```python
stop(self: Any)
```

Stop the session.

---
