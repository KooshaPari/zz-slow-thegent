# fast_websocket API Reference

> **Source**: `src/thegent/infra/fast_websocket.py`

Fast WebSocket client with optimized backends.

This module provides optimized WebSocket client support:

- websockets library (modern, fast, async-first)
- websocket-client fallback (legacy support)
- Unified API for both sync and async operations

Performance improvements:

- websockets: Modern, faster, better async support
- Better resource management
- Automatic backend selection

---

## FastWebSocket

High-performance WebSocket client with automatic backend selection.

### Methods

#### FastWebSocket.**init**

```python
__init__(self: Any, url: str)
```

Initialize WebSocket client.

**Parameters**:

- `url`: WebSocket URL (ws:// or wss://)
- `**kwargs`: Additional connection options

---

#### FastWebSocket.close_sync

```python
close_sync(self: Any)
```

Close connection synchronously.

---

#### FastWebSocket.connect_sync

```python
connect_sync(self: Any)
```

Connect synchronously using websocket-client.

Performance: - websocket-client: Legacy, sync-only - Fallback for compatibility

---

#### FastWebSocket.recv_sync

```python
recv_sync(self: Any)
```

Receive data synchronously.

---

#### FastWebSocket.send_sync

```python
send_sync(self: Any, data: Any)
```

Send data synchronously.

---

---

## close_sync

```python
close_sync(self: Any)
```

Close connection synchronously.

---

## connect_sync

```python
connect_sync(self: Any)
```

Connect synchronously using websocket-client.

Performance: - websocket-client: Legacy, sync-only - Fallback for compatibility

---

## recv_sync

```python
recv_sync(self: Any)
```

Receive data synchronously.

---

## send_sync

```python
send_sync(self: Any, data: Any)
```

Send data synchronously.

---

## websocket_connect_sync

```python
websocket_connect_sync(url: str)
```

Create and connect WebSocket synchronously.

---
