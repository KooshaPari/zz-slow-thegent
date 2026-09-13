# cross_project API Reference

> **Source**: `src/thegent/ipc/cross_project.py`

File-based IPC (inter-process communication) for cross-project agent coordination.

Uses a Maildir-style atomic write protocol so agents in different projects
can exchange messages without any network service.

Directory layout::

    ~/.thegent/ipc/
      &lt;recipient_hash&gt;/      # SHA256 of recipient address, first 16 hex chars
        tmp/                 # staging: write here first
        new/                 # ready to be read
        cur/                 # claimed (in-flight) by receiver
      broadcast/             # well-known inbox for broadcast messages
        tmp/
        new/
        cur/

Message file format (JSON, one message per file)::

    {
        "msg_id":   "&lt;uuid&gt;",
        "sender":   "&lt;project_root&gt;:&lt;agent_id&gt;",
        "recipient": "&lt;project_root&gt;:&lt;agent_id&gt;" | "*",
        "topic":    "&lt;string&gt;",
        "payload":  { ... },
        "timestamp": &lt;unix float&gt;,
        "reply_to": "&lt;msg_id&gt;" | null
    }

Atomicity guarantee: every delivery uses `os.rename` from `tmp/` to
`new/`, which is atomic on POSIX filesystems. Concurrent senders writing
to the same inbox are safe because each file name contains a UUID.

---

## CrossProjectIpc

File-based IPC client for cross-project agent communication.

Each instance is bound to a single `(project_root, agent_id)` pair and
writes/reads from `IPC_DIR` (`~/.thegent/ipc/` by default).

### Methods

#### CrossProjectIpc.**init**

```python
__init__(self: Any, agent_id: str, project_root: Path)
```

---

#### CrossProjectIpc.ack

```python
ack(self: Any, msg_id: str)
```

Acknowledge receipt of _msg_id_, removing it from the inbox.

Idempotent — safe to call more than once or on an unknown ID.

**Parameters**:

- `msg_id`: The message ID to acknowledge.

---

#### CrossProjectIpc.broadcast

```python
broadcast(self: Any, topic: str, payload: dict)
```

Broadcast a message to all listening agents.

Delivers to the well-known `broadcast` inbox so that any agent
polling that inbox receives it.

**Parameters**:

- `topic`: Message topic.
- `payload`: Arbitrary JSON-serialisable data.

**Returns**: The unique `msg_id`.

---

#### CrossProjectIpc.list_pending

```python
list_pending(self: Any)
```

Return all messages waiting in this agent's `new/` inbox.

---

#### CrossProjectIpc.receive

```python
receive(self: Any, timeout: float)
```

Claim the next message from this agent's inbox.

When _timeout_ is 0 the call is non-blocking; when _timeout_ &gt; 0 it
polls until a message arrives or the timeout elapses.

**Parameters**:

- `timeout`: Maximum seconds to wait. 0 means non-blocking.

**Returns**: The claimed :class:`IpcMessage`, or `None` if none arrived.

---

#### CrossProjectIpc.receive_broadcast

```python
receive_broadcast(self: Any, timeout: float)
```

Claim the next broadcast message.

**Parameters**:

- `timeout`: Maximum seconds to wait. 0 means non-blocking.

**Returns**: The claimed :class:`IpcMessage`, or `None`.

---

#### CrossProjectIpc.receive_topic

```python
receive_topic(self: Any, topic: str, timeout: float)
```

Claim the next message matching _topic_ from this agent's inbox.

Messages that do not match _topic_ are left untouched in the inbox.

**Parameters**:

- `topic`: The topic string to filter on.
- `timeout`: Maximum seconds to wait.

**Returns**: The first matching :class:`IpcMessage`, or `None`.

---

#### CrossProjectIpc.reply

```python
reply(self: Any, original: IpcMessage, payload: dict)
```

Send a reply to the sender of _original_.

**Parameters**:

- `original`: The message being replied to.
- `payload`: Reply payload.

**Returns**: The unique `msg_id` of the reply.

---

#### CrossProjectIpc.send

```python
send(self: Any, recipient: str, topic: str, payload: dict)
```

Send a message to _recipient_.

**Parameters**:

- `recipient`: Target address (`"&lt;project_root&gt;:&lt;agent_id&gt;"`).
- `topic`: Message topic / type string.
- `payload`: Arbitrary JSON-serialisable data.

**Returns**: The unique `msg_id` of the sent message.

---

---

## CrossProjectIpcServer

Long-running server that dispatches incoming IPC messages to handlers.

Handlers are registered per topic. An optional `default_handler` is
called for messages whose topic has no specific handler.

Example::

    server = CrossProjectIpcServer(ipc)
    server.register("ping", lambda msg: ipc.reply(msg, {"pong": True}))
    server.run(poll_interval=0.1)

### Methods

#### CrossProjectIpcServer.**init**

```python
__init__(self: Any, ipc: CrossProjectIpc)
```

---

#### CrossProjectIpcServer.register

```python
register(self: Any, topic: str, handler: Callable[(Any, None)])
```

Register a _handler_ for messages with the given _topic_.

**Parameters**:

- `topic`: The topic string to match.
- `handler`: Callable that receives an :class:`IpcMessage`.

---

#### CrossProjectIpcServer.run

```python
run(self: Any, max_iterations: Any)
```

Start the dispatch loop.

**Parameters**:

- `max_iterations`: Stop after processing this many iterations
  (useful for testing). `None` means run forever.

---

#### CrossProjectIpcServer.set_default_handler

```python
set_default_handler(self: Any, handler: Callable[(Any, None)])
```

Set a catch-all _handler_ for unregistered topics.

---

#### CrossProjectIpcServer.stop

```python
stop(self: Any)
```

Signal the server loop to stop after the current iteration.

---

---

## IpcMessage

A single IPC message exchanged between agents.

### Methods

#### IpcMessage.from_dict

```python
from_dict(cls: Any, data: dict)
```

Construct from a plain dictionary.

---

#### IpcMessage.from_json

```python
from_json(cls: Any, text: str)
```

Deserialise from a JSON string.

---

#### IpcMessage.to_json

```python
to_json(self: Any)
```

Serialise to a JSON string.

---

---

## ack

```python
ack(self: Any, msg_id: str)
```

Acknowledge receipt of _msg_id_, removing it from the inbox.

Idempotent — safe to call more than once or on an unknown ID.

**Parameters**:

- `msg_id`: The message ID to acknowledge.

---

## broadcast

```python
broadcast(self: Any, topic: str, payload: dict)
```

Broadcast a message to all listening agents.

Delivers to the well-known `broadcast` inbox so that any agent
polling that inbox receives it.

**Parameters**:

- `topic`: Message topic.
- `payload`: Arbitrary JSON-serialisable data.

**Returns**: The unique `msg_id`.

---

## from_dict

```python
from_dict(cls: Any, data: dict)
```

Construct from a plain dictionary.

---

## from_json

```python
from_json(cls: Any, text: str)
```

Deserialise from a JSON string.

---

## list_pending

```python
list_pending(self: Any)
```

Return all messages waiting in this agent's `new/` inbox.

---

## receive

```python
receive(self: Any, timeout: float)
```

Claim the next message from this agent's inbox.

When _timeout_ is 0 the call is non-blocking; when _timeout_ &gt; 0 it
polls until a message arrives or the timeout elapses.

**Parameters**:

- `timeout`: Maximum seconds to wait. 0 means non-blocking.

**Returns**: The claimed :class:`IpcMessage`, or `None` if none arrived.

---

## receive_broadcast

```python
receive_broadcast(self: Any, timeout: float)
```

Claim the next broadcast message.

**Parameters**:

- `timeout`: Maximum seconds to wait. 0 means non-blocking.

**Returns**: The claimed :class:`IpcMessage`, or `None`.

---

## receive_topic

```python
receive_topic(self: Any, topic: str, timeout: float)
```

Claim the next message matching _topic_ from this agent's inbox.

Messages that do not match _topic_ are left untouched in the inbox.

**Parameters**:

- `topic`: The topic string to filter on.
- `timeout`: Maximum seconds to wait.

**Returns**: The first matching :class:`IpcMessage`, or `None`.

---

## register

```python
register(self: Any, topic: str, handler: Callable[(Any, None)])
```

Register a _handler_ for messages with the given _topic_.

**Parameters**:

- `topic`: The topic string to match.
- `handler`: Callable that receives an :class:`IpcMessage`.

---

## reply

```python
reply(self: Any, original: IpcMessage, payload: dict)
```

Send a reply to the sender of _original_.

**Parameters**:

- `original`: The message being replied to.
- `payload`: Reply payload.

**Returns**: The unique `msg_id` of the reply.

---

## run

```python
run(self: Any, max_iterations: Any)
```

Start the dispatch loop.

**Parameters**:

- `max_iterations`: Stop after processing this many iterations
  (useful for testing). `None` means run forever.

---

## send

```python
send(self: Any, recipient: str, topic: str, payload: dict)
```

Send a message to _recipient_.

**Parameters**:

- `recipient`: Target address (`"&lt;project_root&gt;:&lt;agent_id&gt;"`).
- `topic`: Message topic / type string.
- `payload`: Arbitrary JSON-serialisable data.

**Returns**: The unique `msg_id` of the sent message.

---

## set_default_handler

```python
set_default_handler(self: Any, handler: Callable[(Any, None)])
```

Set a catch-all _handler_ for unregistered topics.

---

## stop

```python
stop(self: Any)
```

Signal the server loop to stop after the current iteration.

---

## to_json

```python
to_json(self: Any)
```

Serialise to a JSON string.

---
