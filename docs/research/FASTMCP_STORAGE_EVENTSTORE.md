<DONE>
# FastMCP Storage Backends & EventStore

**Source:** gofastmcp.com/servers/storage-backends, fastmcp/server/event_store
**Date:** 2026-02-14
**Purpose:** Extract RedisStore, DiskStore usage, EventStore(storage=), FernetEncryptionWrapper for thegent MCP server.

---

## 1. Storage Backends (py-key-value-aio)

FastMCP uses pluggable storage backends for caching and OAuth state. Default: in-memory.

### 1.1 MemoryStore (Default)

```python
from key_value.aio.stores.memory import MemoryStore

cache_store = MemoryStore()
```

- Development, single-process
- Data lost on restart
- No setup required

### 1.2 DiskStore

```python
from key_value.aio.stores.disk import DiskStore
from fastmcp.server.middleware.caching import ResponseCachingMiddleware

middleware = ResponseCachingMiddleware(cache_storage=DiskStore(directory="/var/cache/fastmcp"))
```

For OAuth:

```python
from fastmcp.server.auth.providers.github import GitHubProvider

auth = GitHubProvider(client_storage=DiskStore(directory="/var/lib/fastmcp/oauth"))
```

- Single-server production
- Data persists across restarts
- Not suitable for distributed deployments

### 1.3 RedisStore

```python
from key_value.aio.stores.redis import RedisStore
# Requires: pip install 'py-key-value-aio[redis]'

middleware = ResponseCachingMiddleware(cache_storage=RedisStore(host="redis.example.com", port=6379))

# With auth
RedisStore(host="redis.example.com", port=6379, password="your-redis-password")
```

For OAuth:

```python
auth = GitHubProvider(client_storage=RedisStore(host="redis.example.com", port=6379))
```

- Distributed production
- Multi-server deployments
- Built-in TTL support

### 1.4 FernetEncryptionWrapper (OAuth)

For production OAuth, wrap storage with encryption:

```python
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
from cryptography.fernet import Fernet

auth = GitHubProvider(
    client_storage=FernetEncryptionWrapper(
        key_value=RedisStore(host="redis.example.com", port=6379), fernet=Fernet(os.environ["STORAGE_ENCRYPTION_KEY"])
    )
)
```

- Required for production OAuth
- Without it, tokens stored in plaintext

### 1.5 PrefixCollectionsWrapper (Multi-tenant)

```python
from key_value.aio.wrappers.prefix_collections import PrefixCollectionsWrapper

base_store = RedisStore(host="redis.example.com")
namespaced_store = PrefixCollectionsWrapper(key_value=base_store, prefix="my-server")
middleware = ResponseCachingMiddleware(cache_storage=namespaced_store)
```

---

## 2. EventStore (SSE Polling)

From `fastmcp.server.event_store.EventStore`:

```python
from fastmcp.server.event_store import EventStore
from key_value.aio.stores.redis import RedisStore

# Default in-memory
event_store = EventStore()

# Redis for distributed
event_store = EventStore(storage=RedisStore(url="redis://localhost"))
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| storage | AsyncKeyValue | MemoryStore() | Backend for event storage |
| max_events_per_stream | int | 100 | Max events retained per stream |
| ttl | int | 3600 | Event TTL in seconds; None = no expiration |

### Usage with HTTP app

```python
app = mcp.http_app(
    event_store=event_store,
    retry_interval=2000,  # ms before client reconnects
    transport="streamable-http",
)
```

### ctx.close_sse_stream()

During long runs, periodically close the stream to avoid LB timeouts:

```python
if i % 30 == 0 and i > 0:
    await ctx.close_sse_stream()
```

Client reconnects with `Last-Event-ID`; EventStore resumes from last event.

---

## 3. thegent Application

| Use Case | Backend | Config |
|----------|---------|--------|
| Response cache (ps, list_agents, list_models) | DiskStore or RedisStore | `cache_storage=DiskStore(directory="/var/cache/thegent")` |
| EventStore (long thegent_run) | MemoryStore or RedisStore | `EventStore(storage=RedisStore(...))` |
| OAuth (if added) | RedisStore + FernetEncryptionWrapper | `client_storage=FernetEncryptionWrapper(...)` |
| Docket tasks (background) | `FASTMCP_DOCKET_URL=redis://...` | Task backend |

### Config Variables

| Variable | Default | Description |
|----------|---------|-------------|
| THGENT_CACHE_STORAGE | memory | `memory`, `disk:/path`, or `redis://host:port` |
| FASTMCP_DOCKET_URL | memory:// | Task backend for background tasks |

---

## EXTENSION_SUMMARY

### 4. Schema Examples

#### 4.1 Event Schema for Session State

```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class SessionEvent:
    """Schema for session lifecycle events."""

    event_type: str  # "started", "progress", "completed", "failed"
    session_id: str
    timestamp: datetime
    agent_name: str
    data: dict
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {**asdict(self), "timestamp": self.timestamp.isoformat()}

    @classmethod
    def from_dict(cls, data: dict) -> "SessionEvent":
        return cls(
            event_type=data["event_type"],
            session_id=data["session_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            agent_name=data["agent_name"],
            data=data["data"],
            metadata=data.get("metadata"),
        )


# Event types
SESSION_STARTED = "started"
SESSION_PROGRESS = "progress"
SESSION_COMPLETED = "completed"
SESSION_FAILED = "failed"
```

**Cross-reference:** See `src/thegent/governance/evidence_ledger.py` for event sourcing patterns.

#### 4.2 Query Patterns for Event Store

```python
from typing import AsyncIterator


class EventQueryBuilder:
    """Build complex queries for EventStore."""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.filters = {}
        self.limit_count = 100
        self.order_by = "timestamp"
        self.order_dir = "asc"

    def filter_by_session(self, session_id: str) -> "EventQueryBuilder":
        self.filters["session_id"] = session_id
        return self

    def filter_by_agent(self, agent_name: str) -> "EventQueryBuilder":
        self.filters["agent_name"] = agent_name
        return self

    def filter_by_type(self, event_type: str) -> "EventQueryBuilder":
        self.filters["event_type"] = event_type
        return self

    def filter_by_timerange(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> "EventQueryBuilder":
        if start:
            self.filters["start_time"] = start
        if end:
            self.filters["end_time"] = end
        return self

    def limit(self, count: int) -> "EventQueryBuilder":
        self.limit_count = count
        return self

    async def execute(self) -> list[SessionEvent]:
        """Execute query and return events."""
        events = await self.event_store.query(**self.filters)
        # Apply ordering and limits
        events = sorted(events, key=lambda e: getattr(e, self.order_by))
        if self.order_dir == "desc":
            events = list(reversed(events))
        return events[: self.limit_count]


# Usage
events = (
    await EventQueryBuilder(event_store)
    .filter_by_agent("prod-agent")
    .filter_by_type(SESSION_COMPLETED)
    .filter_by_timerange(start=datetime.now() - timedelta(hours=1))
    .limit(50)
    .execute()
)
```

### 5. Storage Optimization Patterns

#### 5.1 TTL-Based Eviction

```python
from key_value.aio.stores.redis import RedisStore

# EventStore with aggressive TTL for cost control
event_store = EventStore(
    storage=RedisStore(url="redis://localhost"),
    max_events_per_stream=100,
    ttl=300,  # 5 minutes for ephemeral events
)

# Separate store for audit events with longer retention
audit_store = EventStore(
    storage=RedisStore(url="redis://localhost", db=1),
    max_events_per_stream=1000,
    ttl=86400,  # 24 hours for audit
)
```

**Retention Policy:**

| Event Type | TTL | Storage Backend |
|------------|-----|-----------------|
| Progress events | 5 min | Redis (db=0) |
| Session completion | 1 hour | Redis (db=0) |
| Audit logs | 24 hours | Redis (db=1) |
| Long-term analytics | 30 days | Disk/Cloud |

#### 5.2 Sharding for High Volume

```python
import hashlib


class ShardedEventStore:
    """Sharded EventStore for horizontal scaling."""

    def __init__(self, shard_count: int = 4):
        self.shard_count = shard_count
        self.stores = [EventStore(storage=RedisStore(url=f"redis://shard-{i}")) for i in range(shard_count)]

    def _get_shard(self, session_id: str) -> int:
        """Determine shard for session."""
        hash_value = hashlib.md5(session_id.encode()).hexdigest()
        return int(hash_value[:2], 16) % self.shard_count

    async def append_event(self, session_id: str, event: SessionEvent):
        shard = self._get_shard(session_id)
        await self.stores[shard].append(session_id, event)

    async def get_events(self, session_id: str) -> list[SessionEvent]:
        shard = self._get_shard(session_id)
        return await self.stores[shard].get(session_id)
```

**Cross-reference:** See `docs/guides/CROSS_PLATFORM_DEVELOPER_COOKBOOK.md` for distributed patterns.

### 6. Cross-Document References

| Reference | Purpose |
|-----------|---------|
| `FASTMCP_IMPLEMENTATION_GUIDE.md` | Storage backend configuration |
| `FASTMCP_SPEC_DEEP_DIVE.md` | EventStore specification |
| `FASTMCP_MIDDLEWARE.md` | Caching middleware patterns |
| `FASTMCP_TRANSFORMS_DEPLOYMENT.md` | HTTP deployment with EventStore |
| `src/thegent/governance/evidence_ledger.py` | Evidence ledger with event sourcing |

---

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [FASTMCP_IMPLEMENTATION_GUIDE.md](./FASTMCP_IMPLEMENTATION_GUIDE.md) - Main implementation guide
- [FASTMCP_SPEC_DEEP_DIVE.md](./FASTMCP_SPEC_DEEP_DIVE.md) - Specification deep dive
- [FASTMCP_MIDDLEWARE.md](./FASTMCP_MIDDLEWARE.md) - Middleware patterns
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

**Document Version:** 1.1
**Last Extended:** 2026-02-17
**Extension Author:** Worker Droid
