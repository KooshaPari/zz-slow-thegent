# acp_client API Reference

> **Source**: `src/thegent/adapters/acp_client.py`

ACP (Agent Communication Protocol) HTTP client adapter.

Allows thegent to send tasks to remote ACP-compatible agents over HTTP.

Complements the stdio-based ACPClientAdapter in thegent.acp.client.

Config (all optional — can also be passed to constructor directly):
THGENT_ACP_BASE_URL - ACP server base URL (default: http://localhost:8080)
THGENT_ACP_AGENT_ID - Sender agent ID (default: "thegent")

# @trace FR-ACP-001

---

## ACPClient

HTTP client for ACP-compatible agent servers.

Sends tasks to a remote ACP server and returns structured results.
Uses httpx.AsyncClient for all I/O and tenacity with
wait_random_exponential for retry on 429/503 and transient network errors.

Example::

    client = ACPClient(base_url="http://agent.example.com:8080")
    result = await client.send_task("Summarise the latest PR diffs")
    if result.success:
        print(result.result)

### Methods

#### ACPClient.**init**

```python
__init__(self: Any, base_url: str, agent_id: str)
```

Initialise the client.

**Parameters**:

- `base_url`: ACP server base URL, e.g. `"http://localhost:8080"`.
- `agent_id`: Logical sender ID embedded in outgoing requests.

---

---

## ACPClientError

Raised when the ACP server returns a non-retryable error.

**Inherits from**: `Exception`

### Methods

#### ACPClientError.**init**

```python
__init__(self: Any, status_code: int, message: str)
```

---

---

## ACPResult

Result returned by ACPClient.send_task().

---

## ACPServerUnreachableError

Raised when the ACP server is unreachable after all retries.

**Inherits from**: `Exception`

---
