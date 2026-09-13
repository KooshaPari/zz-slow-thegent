# cliproxy_adapter API Reference

> **Source**: `src/thegent/cliproxy_adapter.py`

CLIProxy adapter: exposes /v1/responses (HTTP + WebSocket) for Codex compatibility.

cliproxyapi++ (kooshapari fork) may not implement /v1/responses. This adapter:

- Proxies all /v1/\* to the backend
- For POST /v1/responses: tries backend first; on 404, translates to /v1/chat/completions
- For WebSocket /v1/responses: bridges WS to HTTP streaming (SSE)

---

## create_adapter_app

```python
create_adapter_app(backend_url: str)
```

Create the adapter Starlette app.

---

## get_model_metadata

```python
get_model_metadata(_: Any)
```

---
