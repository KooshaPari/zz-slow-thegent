# headless_manager API Reference

> **Source**: `src/thegent/lsp/headless_manager.py`

Headless LSP Server Manager - Full-featured LSP infrastructure.

---

## HeadlessLSPManager

Manages multiple LSP servers in headless mode.

### Methods

#### HeadlessLSPManager.**init**

```python
__init__(self: Any, cache_dir: Any)
```

---

#### HeadlessLSPManager.ensure_server

```python
ensure_server(self: Any, language: str, auto_install: Any)
```

Ensure LSP server is running for language, auto-installing if needed.

**Parameters**:

- `language`: Language name
- `auto_install`: Auto-install LSP server if missing (None = use config default)

**Returns**: HeadlessLSPServer instance or None

---

#### HeadlessLSPManager.list_servers

```python
list_servers(self: Any)
```

List all running servers.

---

#### HeadlessLSPManager.stop_all

```python
stop_all(self: Any)
```

Stop all LSP servers.

---

#### HeadlessLSPManager.stop_server

```python
stop_server(self: Any, language: str)
```

Stop LSP server for language.

---

---

## HeadlessLSPServer

Manages a single LSP server process.

### Methods

#### HeadlessLSPServer.**init**

```python
__init__(self: Any, language: str, config: dict[(str, Any)])
```

---

#### HeadlessLSPServer.is_running

```python
is_running(self: Any)
```

Check if server is running.

---

#### HeadlessLSPServer.start

```python
start(self: Any)
```

Start LSP server process.

---

#### HeadlessLSPServer.stop

```python
stop(self: Any)
```

Stop LSP server process.

---

---

## ensure_server

```python
ensure_server(self: Any, language: str, auto_install: Any)
```

Ensure LSP server is running for language, auto-installing if needed.

**Parameters**:

- `language`: Language name
- `auto_install`: Auto-install LSP server if missing (None = use config default)

**Returns**: HeadlessLSPServer instance or None

---

## is_running

```python
is_running(self: Any)
```

Check if server is running.

---

## list_servers

```python
list_servers(self: Any)
```

List all running servers.

---

## start

```python
start(self: Any)
```

Start LSP server process.

---

## stop

```python
stop(self: Any)
```

Stop LSP server process.

---

## stop_all

```python
stop_all(self: Any)
```

Stop all LSP servers.

---

## stop_server

```python
stop_server(self: Any, language: str)
```

Stop LSP server for language.

---
