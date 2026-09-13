# Supermemory Phase 1: Detailed Work Breakdown Structure

**Status**: ACTIVE
**Timeline**: 3 days (Feb 18-20, 2026)
**Effort**: ~15-20 person-days across 3 parallel tracks
**Goal**: Authentication + Client SDK + Cache Infrastructure ready for Phase 2

---

## Executive Summary

Phase 1 establishes the **foundation** for Supermemory.ai integration across thegent:

| Package  | Lead Track   | Effort   | Deliverable                                          |
| -------- | ------------ | -------- | ---------------------------------------------------- |
| **P1.1** | Rust Client  | 4-5 days | `thegent_supermemory::Client` + auth + API modules   |
| **P1.2** | Python Cache | 3-4 days | Redis + FileCache providers with L1/L2 orchestration |
| **P1.3** | Config/CLI   | 2-3 days | `thegent login supermemory` + MCP integration + docs |

**Critical Path**: P1.1.1-3 → P1.1.4-6 → P1.2/P1.3 (can parallelize P1.2 and P1.3)

---

## P1.1: Supermemory Client (Rust) — 4-5 days

### P1.1.1: Project Scaffold & Dependencies

**Objectives**:

- Create Rust crate structure
- Add all required dependencies
- Define error handling types

**Inputs**: None
**Outputs**:

- `crates/supermemory-rs/Cargo.toml` (complete)
- `crates/supermemory-rs/src/error.rs`
- `crates/supermemory-rs/src/lib.rs` (empty, public API skeleton)

**Key Dependencies**:

```toml
[dependencies]
reqwest = { version = "0.12", features = ["json"] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
thiserror = "1.0"
log = "0.4"
uuid = { version = "1.0", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
anyhow = "1.0"
```

**Acceptance Criteria**:

- ✅ `cargo build` succeeds
- ✅ `cargo test` passes (empty test suite)
- ✅ Error types implement `std::error::Error`

**Effort**: ~1 day | **Commits**: 2-3

---

### P1.1.2: Authentication Module

**Objectives**:

- Implement API key validation
- Load credentials from environment / file
- Define auth headers and project scoping

**Inputs**: P1.1.1
**Outputs**:

- `crates/supermemory-rs/src/auth.rs`
- `crates/supermemory-rs/tests/auth_tests.rs`

**Key Types**:

```rust
pub struct ApiKey(String);
pub struct Auth { key: ApiKey, project: Option<String> }
pub struct Config { api_key: String, base_url: String, project: Option<String> }
```

**Config Sources** (in order):

1. Environment: `SM_API_KEY`, `SM_PROJECT`
2. File: `~/.sm/config` (YAML or TOML)
3. CLI argument (future)

**Acceptance Criteria**:

- ✅ API key format validation: `sm_[a-z0-9]{32,}`
- ✅ Config loads from env with fallback to file
- ✅ Auth headers correctly include `x-sm-project` if set
- ✅ Tests cover valid/invalid keys, missing credentials

**Effort**: ~1 day | **Commits**: 3-4

---

### P1.1.3: Core HTTP Client

**Objectives**:

- Implement base HTTP client with request/response handling
- Add retry logic (exponential backoff)
- Handle serialization/deserialization

**Inputs**: P1.1.1, P1.1.2
**Outputs**:

- `crates/supermemory-rs/src/client.rs`
- `crates/supermemory-rs/tests/client_tests.rs`

**Key Methods**:

```rust
pub struct SupermemoryClient { auth: Auth, http: reqwest::Client }
impl SupermemoryClient {
  pub async fn get<T>(&self, path: &str) -> Result<T>
  pub async fn post<I, O>(&self, path: &str, body: I) -> Result<O>
  pub async fn put<I, O>(&self, path: &str, body: I) -> Result<O>
  pub async fn delete(&self, path: &str) -> Result<()>
}
```

**Retry Strategy**:

- Max 3 retries with exponential backoff (100ms, 500ms, 2.5s)
- Retry on: 408, 429, 500-599
- No retry on: 4xx except above

**Acceptance Criteria**:

- ✅ Requests include auth headers
- ✅ Responses deserialize correctly (serde_json)
- ✅ Retry logic triggers on correct status codes
- ✅ Timeout: 30 seconds default
- ✅ Tests: mock HTTP responses, verify headers, test retry backoff

**Effort**: ~1 day | **Commits**: 3-4

---

### P1.1.4: Conversations API

**Objectives**:

- Implement conversation read/write operations
- Define Conversation, Message, Metadata models
- Support continuity packets

**Inputs**: P1.1.1-3
**Outputs**:

- `crates/supermemory-rs/src/api/conversations.rs`
- `crates/supermemory-rs/src/models/conversation.rs`
- `crates/supermemory-rs/tests/integration_tests.rs` (conversation section)

**Key Models**:

```rust
pub struct Conversation {
  pub id: String,
  pub title: String,
  pub messages: Vec<Message>,
  pub metadata: ConversationMetadata,
  pub created_at: DateTime<Utc>,
  pub updated_at: DateTime<Utc>,
}

pub struct Message {
  pub id: String,
  pub role: String, // "user", "assistant"
  pub content: String,
  pub created_at: DateTime<Utc>,
}

pub struct ContinuityPacket {
  pub session_id: String,
  pub context: Vec<Message>,
  pub metadata: Map<String, Value>,
}
```

**Key Methods**:

```rust
pub async fn list_conversations(&self) -> Result<Vec<Conversation>>
pub async fn get_conversation(&self, id: &str) -> Result<Conversation>
pub async fn create_conversation(&self, title: &str) -> Result<Conversation>
pub async fn add_message(&self, conv_id: &str, role: &str, content: &str) -> Result<Message>
pub async fn get_continuity_packet(&self, session_id: &str) -> Result<ContinuityPacket>
```

**Acceptance Criteria**:

- ✅ Serialization roundtrip: serde_json ↔ model
- ✅ Timestamps parse correctly
- ✅ Integration tests with mock API
- ✅ Error handling for missing conversations, invalid format

**Effort**: ~1 day | **Commits**: 3-4

---

### P1.1.5: Documents API

**Objectives**:

- Implement document archival operations
- Support MAIF artifact signatures
- Handle large document uploads

**Inputs**: P1.1.1-4
**Outputs**:

- `crates/supermemory-rs/src/api/documents.rs`
- `crates/supermemory-rs/src/models/document.rs`

**Key Models**:

```rust
pub struct Document {
  pub id: String,
  pub title: String,
  pub content: String,
  pub mime_type: String,
  pub size: u64,
  pub created_at: DateTime<Utc>,
  pub checksum: String,
}

pub struct Artifact {
  pub id: String,
  pub document_id: String,
  pub signature: String, // MAIF artifact signature
  pub content_hash: String,
}
```

**Key Methods**:

```rust
pub async fn list_documents(&self) -> Result<Vec<Document>>
pub async fn get_document(&self, id: &str) -> Result<Document>
pub async fn create_document(&self, title: &str, content: &[u8]) -> Result<Document>
pub async fn delete_document(&self, id: &str) -> Result<()>
pub async fn sign_artifact(&self, document_id: &str) -> Result<Artifact>
```

**Acceptance Criteria**:

- ✅ Upload/download roundtrip
- ✅ Checksum verification
- ✅ MAIF signature generation
- ✅ Error handling: too large, invalid mime type

**Effort**: ~1 day | **Commits**: 2-3

---

### P1.1.6: Testing & Documentation

**Objectives**:

- Comprehensive test suite
- Examples and API documentation

**Inputs**: P1.1.1-5
**Outputs**:

- `crates/supermemory-rs/tests/` (complete)
- `crates/supermemory-rs/examples/basic_usage.rs`
- `crates/supermemory-rs/README.md`
- `crates/supermemory-rs/docs/API.md`

**Test Coverage**:

- Auth: 12 tests (valid key, invalid key, env loading, file loading)
- Client: 8 tests (serialization, retry, timeouts, error handling)
- Conversations: 10 tests (CRUD, messages, continuity packets)
- Documents: 8 tests (CRUD, checksums, signatures)
- **Total**: 40+ tests, target >85% coverage

**Examples**:

```rust
// examples/basic_usage.rs
#[tokio::main]
async fn main() {
  let client = SupermemoryClient::from_env()?;
  let convs = client.list_conversations().await?;
  for conv in convs {
    println!("{}: {}", conv.id, conv.title);
  }
}
```

**Documentation**:

- README.md: overview, setup, example
- API.md: all public types + methods with doc comments
- TROUBLESHOOTING.md: common errors, solutions

**Acceptance Criteria**:

- ✅ All tests pass: `cargo test`
- ✅ Coverage >85% (use `tarpaulin`)
- ✅ Docs build: `cargo doc --open`
- ✅ Example runs: `cargo run --example basic_usage`

**Effort**: ~1 day | **Commits**: 3-4

---

## P1.2: L1/L2 Cache Infrastructure (Python) — 3-4 days

### P1.2.1: Cache Interface (Abstract Base Class)

**Objectives**:

- Define cache provider contract
- Support TTL, eviction, persistence
- Enable provider switching (Redis ↔ FileCache)

**Inputs**: None
**Outputs**:

- `src/thegent/memory/cache_provider.py`
- `src/thegent/memory/models/cache_item.py`
- `src/thegent/memory/tests/test_cache_provider.py`

**Key Types**:

```python
class CacheProvider(ABC):
  async def get(self, key: str) -> Optional[Any]
  async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None
  async def delete(self, key: str) -> None
  async def exists(self, key: str) -> bool
  async def flush(self) -> None
  async def evict_expired(self) -> int  # returns # evicted

@dataclass
class CacheItem:
  key: str
  value: Any
  created_at: datetime
  expires_at: Optional[datetime]
  hits: int = 0
```

**Acceptance Criteria**:

- ✅ All methods are abstract (ABC enforcement)
- ✅ TTL semantics: expiry timestamps, auto-eviction
- ✅ Type hints complete
- ✅ 100% docstring coverage

**Effort**: ~0.5 days | **Commits**: 2

---

### P1.2.2: Redis Provider

**Objectives**:

- Redis-backed cache implementation
- Connection pooling, cluster support
- Health checks and graceful degradation

**Inputs**: P1.2.1
**Outputs**:

- `src/thegent/memory/redis_provider.py`
- `src/thegent/memory/tests/test_redis_provider.py`

**Key Implementation**:

```python
class RedisProvider(CacheProvider):
    def __init__(self, url: str = "redis://localhost:6379", pool_size: int = 10):
        self.pool = redis.ConnectionPool(url)
        self.client = redis.Redis(connection_pool=self.pool)

    async def get(self, key: str) -> Optional[Any]:
        value = await self.client.get(key)
        if value:
            await self.client.incr(f"{key}:hits")
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        await self.client.set(key, json.dumps(value), ex=ttl)

    async def health_check(self) -> bool:
        try:
            await self.client.ping()
            return True
        except Exception:
            return False
```

**Acceptance Criteria**:

- ✅ Connects to Redis (local or remote)
- ✅ TTL maps to Redis `EX` parameter
- ✅ Health check succeeds if Redis is up
- ✅ Connection pooling reduces latency
- ✅ Tests use Redis testcontainer or mock

**Effort**: ~1 day | **Commits**: 3-4

---

### P1.2.3: FileCache Provider

**Objectives**:

- Local file-based cache fallback
- JSONL for fast append + indexing for random access
- Rotation and cleanup

**Inputs**: P1.2.1
**Outputs**:

- `src/thegent/memory/file_cache_provider.py`
- `src/thegent/memory/tests/test_file_cache_provider.py`

**Implementation Strategy**:

- **Storage**: `~/.thegent/cache/` directory
- **Format**: JSONL (one cache item per line) + index file
- **Index**: `{key}:{offset}:{length}` for O(1) lookups
- **Rotation**: When size >100MB, compress and archive

**Key Methods**:

```python
class FileCacheProvider(CacheProvider):
    def __init__(self, cache_dir: str = "~/.thegent/cache"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_file = self.cache_dir / "cache.jsonl"
        self.index_file = self.cache_dir / "cache.index"

    async def get(self, key: str) -> Optional[Any]:
        # Read index, seek to offset, deserialize
        offset = self._read_index(key)
        if not offset:
            return None
        return self._read_at_offset(offset)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        # Append to JSONL, update index
        offset = self._append_to_cache(key, value, ttl)
        self._update_index(key, offset)

    async def evict_expired(self) -> int:
        # Scan JSONL, remove expired items, rewrite
        return self._rewrite_cache()
```

**Acceptance Criteria**:

- ✅ Stores and retrieves items correctly
- ✅ Index allows O(1) random access
- ✅ TTL: items with `expires_at` in past are ignored
- ✅ Rotation: archive at 100MB, compress previous
- ✅ Tests: CRUD, expiry, rotation, concurrent access

**Effort**: ~1 day | **Commits**: 3-4

---

### P1.2.4: Context Manager (L1/L2 Orchestration)

**Objectives**:

- Coordinate L1 (in-memory), L2 (Redis/FileCache), L3 (Supermemory) fallback
- Continuity packet creation
- Cache coherence

**Inputs**: P1.2.1-3
**Outputs**:

- `src/thegent/memory/context_manager.py`
- `src/thegent/memory/tests/test_context_manager.py`

**Key Implementation**:

```python
class ContextManager:
    def __init__(self, l1_provider: CacheProvider, l2_provider: CacheProvider):
        self.l1 = l1_provider  # In-memory or fast local
        self.l2 = l2_provider  # Redis or FileCache fallback

    async def get(self, key: str, tier: Tier = Tier.L2) -> Optional[Any]:
        # Try L1 first
        value = await self.l1.get(key)
        if value:
            return value

        # Try L2
        if tier >= Tier.L2:
            value = await self.l2.get(key)
            if value:
                await self.l1.set(key, value)  # Promote to L1
                return value

        # Tier.L3 would call Supermemory (future)
        return None

    async def set(self, key: str, value: Any, tier: Tier = Tier.L2) -> None:
        await self.l1.set(key, value)
        if tier >= Tier.L2:
            await self.l2.set(key, value)

    async def create_continuity_packet(self, session_id: str) -> ContinuityPacket:
        # Collect context from L1+L2, create packet
        context = await self.l1.get(f"session:{session_id}:context") or []
        return ContinuityPacket(session_id=session_id, context=context)
```

**Enums**:

```python
class Tier(Enum):
    L1 = 1  # In-memory
    L2 = 2  # Cache (Redis/File)
    L3 = 3  # Supermemory (future)
```

**Acceptance Criteria**:

- ✅ L1 promotion: L2 hit populates L1
- ✅ Coherence: `set` updates both L1 and L2
- ✅ Continuity packet includes session context
- ✅ Fallback: if L2 down, still serve L1

**Effort**: ~0.5 days | **Commits**: 2

---

### P1.2.5: Testing & Benchmarks

**Objectives**:

- Comprehensive test suite for all providers
- Performance benchmarks (throughput, latency, memory)
- Failure scenarios (Redis down, disk full, etc.)

**Inputs**: P1.2.1-4
**Outputs**:

- `src/thegent/memory/tests/test_*.py` (complete)
- `src/thegent/memory/benchmarks/cache_benchmarks.py`
- `src/thegent/memory/benchmarks/results.md`

**Test Matrix** (30+ tests):
| Provider | CRUD | TTL/Eviction | Concurrency | Failure |
|----------|------|--------------|------------|---------|
| FileCache | 6 | 4 | 3 | 3 |
| Redis | 6 | 4 | 3 | 3 |
| Context | 4 | 2 | 2 | 2 |

**Benchmarks** (measure for performance targets):

```python
async def bench_get_throughput(provider: CacheProvider):
  # Pre-populate 10k items
  # Measure: 1000 sequential gets/sec target
  # Acceptable: >800 ops/sec

async def bench_latency_p99(provider: CacheProvider):
  # Measure: P99 latency should be <5ms

async def bench_memory_usage(provider: CacheProvider):
  # Store 100MB, measure resident memory
  # FileCache should use <150MB
  # Redis should use <200MB (with compression)
```

**Failure Scenarios**:

- Redis unavailable: fallback to FileCache
- Disk full: graceful eviction
- Concurrent writes: no corruption
- Malformed cache items: skip, continue

**Acceptance Criteria**:

- ✅ 30+ tests, all pass
- ✅ Coverage >85%
- ✅ Throughput: >800 ops/sec (Redis), >600 ops/sec (FileCache)
- ✅ Latency: P99 <5ms
- ✅ Memory: <200MB for 100MB stored

**Effort**: ~1 day | **Commits**: 3-4

---

## P1.3: Configuration & Setup — 2-3 days

### P1.3.1: Configuration System

**Objectives**:

- YAML-based configuration for Supermemory
- Environment variable overrides
- Validation and defaults

**Inputs**: None
**Outputs**:

- `config/supermemory_config.yaml` (template)
- `src/thegent/config/supermemory.py`
- `src/thegent/config/tests/test_supermemory_config.py`

**Config Structure**:

```yaml
# config/supermemory_config.yaml
supermemory:
  base_url: https://api.supermemory.ai
  api_key_env: SM_API_KEY
  project: null # Optional project scoping
  timeout: 30
  max_retries: 3

cache:
  l1_provider: memory # or redis, file
  l2_provider: redis # or file
  redis_url: redis://localhost:6379
  file_cache_dir: ~/.thegent/cache
  max_size_mb: 500
  ttl_seconds: 3600

logging:
  level: INFO
  format: json
```

**Key Implementation**:

```python
@dataclass
class SupermemoryConfig:
    base_url: str = "https://api.supermemory.ai"
    api_key: str = ""  # Loaded from SM_API_KEY
    project: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_file(cls, path: str = "config/supermemory_config.yaml") -> "SupermemoryConfig":
        # Load YAML, override with env vars
        pass

    @classmethod
    def from_env(cls) -> "SupermemoryConfig":
        # Load from environment only
        pass

    def validate(self) -> bool:
        # Check required fields, valid URLs, API key format
        pass
```

**Acceptance Criteria**:

- ✅ Config loads from YAML + env override
- ✅ Validation: required fields, format checks
- ✅ Defaults applied for missing fields
- ✅ Tests: load file, env override, validation

**Effort**: ~0.5 days | **Commits**: 2

---

### P1.3.2: Authentication CLI (`thegent login supermemory`)

**Objectives**:

- Interactive login command
- Store credentials securely
- Support API key paste or OAuth (future)

**Inputs**: P1.3.1
**Outputs**:

- `src/thegent/cli/commands/auth.py` (updated)
- `src/thegent/cli/commands/tests/test_auth_supermemory.py`

**Implementation**:

```python
@app.command()
async def login(service: str = typer.Argument(..., help="Service to log in to")):
    if service == "supermemory":
        typer.echo("Enter your Supermemory API key (sm_...): ", nl=False)
        key = getpass.getpass("")

        # Validate key format
        if not key.startswith("sm_"):
            typer.echo("Error: Invalid API key format", err=True)
            raise typer.Exit(1)

        # Store securely in ~/.sm/config
        config_dir = Path.home() / ".sm"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config"
        config_file.write_text(f"api_key={key}\n", mode=0o600)

        typer.echo("✓ Logged in to Supermemory")
```

**Acceptance Criteria**:

- ✅ `thegent login supermemory` prompts for API key
- ✅ Key stored securely in `~/.sm/config` (mode 0o600)
- ✅ Validation: format check before storing
- ✅ Logout: `thegent logout supermemory` removes credentials

**Effort**: ~0.5 days | **Commits**: 2

---

### P1.3.3: MCP Server Integration

**Objectives**:

- Register Supermemory tools with FastMCP
- Make tools available to agents
- Document tool list

**Inputs**: P1.3.1-2
**Outputs**:

- `config/mcp_servers.json` (updated)
- `src/thegent/mcp/supermemory_tools.py`
- `src/thegent/mcp/tests/test_supermemory_tools.py`

**MCP Tools** (register ~6):

```python
@mcp.tool()
async def supermemory_list_conversations(limit: int = 10) -> List[Conversation]:
    """List conversations in Supermemory"""
    client = SupermemoryClient.from_env()
    return await client.list_conversations()[:limit]


@mcp.tool()
async def supermemory_add_message(conversation_id: str, role: str, content: str) -> Message:
    """Add message to conversation"""
    client = SupermemoryClient.from_env()
    return await client.add_message(conversation_id, role, content)


# ... 4 more tools (get_conversation, create_conversation, save_document, get_continuity_packet)
```

**Config Update**:

```json
{
  "mcp_servers": [
    {
      "name": "supermemory",
      "endpoint": "stdio",
      "command": ["python", "-m", "thegent.mcp.supermemory_tools"]
    }
  ]
}
```

**Acceptance Criteria**:

- ✅ 6 tools registered and callable
- ✅ `thegent tools list` shows supermemory tools
- ✅ Tool parameters validated
- ✅ Error handling: missing auth, network errors

**Effort**: ~0.5 days | **Commits**: 2

---

### P1.3.4: Documentation

**Objectives**:

- Setup guide for users
- Configuration reference
- Troubleshooting

**Inputs**: P1.3.1-3
**Outputs**:

- `docs/guides/SUPERMEMORY_SETUP.md`
- `docs/reference/SUPERMEMORY_API_REFERENCE.md`
- `docs/guides/SUPERMEMORY_TROUBLESHOOTING.md`

**Setup Guide Sections**:

1. **Prerequisites**: API key, Python 3.10+, Redis optional
2. **Installation**: `pip install thegent`, fetch Rust client
3. **Configuration**: `thegent login supermemory`
4. **Testing**: `thegent doctor supermemory`
5. **Examples**: Store message, retrieve conversation, save document
6. **Advanced**: Custom cache provider, cluster Redis, OAuth

**Acceptance Criteria**:

- ✅ Complete end-to-end walkthrough
- ✅ All configuration options documented
- ✅ Examples runnable
- ✅ Troubleshooting covers common errors

**Effort**: ~0.5 days | **Commits**: 2

---

### P1.3.5: Health Checks & Doctor Command

**Objectives**:

- Verify Supermemory connectivity
- Diagnose auth failures, network issues
- Provide recovery procedures

**Inputs**: P1.3.1-4
**Outputs**:

- `src/thegent/cli/commands/doctor.py` (updated)
- `src/thegent/health/supermemory_health.py`

**Health Checks**:

```python
@app.command()
async def doctor():
    """Check system health"""

    checks = [
        ("Supermemory API Key", check_sm_api_key),
        ("Supermemory Connectivity", check_sm_connectivity),
        ("Redis Availability", check_redis),
        ("FileCache Writeable", check_file_cache),
        ("MCP Tools Registered", check_mcp_tools),
    ]

    for check_name, check_fn in checks:
        result = await check_fn()
        status = "✓" if result.passed else "✗"
        print(f"{status} {check_name}: {result.message}")
        if not result.passed:
            print(f"  Recovery: {result.recovery_hint}")
```

**Recovery Hints**:

- No API key: `thegent login supermemory`
- Connectivity timeout: Check firewall, VPN
- Redis unavailable: Start Redis or disable L2 cache
- FileCache disk full: Run `thegent cache evict --aggressive`

**Acceptance Criteria**:

- ✅ All 5 checks implemented
- ✅ Helpful error messages and recovery hints
- ✅ `thegent doctor` runs in <5 seconds
- ✅ Tests for success and failure cases

**Effort**: ~0.5 days | **Commits**: 2

---

## Summary by Effort & Parallelization

| Package   | Task   | Effort | Day        | Critical Path | Can Parallelize   |
| --------- | ------ | ------ | ---------- | ------------- | ----------------- |
| **P1.1**  | P1.1.1 | 1      | 1          | ✓ Lead        | —                 |
|           | P1.1.2 | 1      | 1          | ✓             | —                 |
|           | P1.1.3 | 1      | 1          | ✓             | —                 |
|           | P1.1.4 | 1      | 2          | ✓             | —                 |
|           | P1.1.5 | 1      | 2          | ✓             | —                 |
|           | P1.1.6 | 1      | 2          | —             | —                 |
| **P1.2**  | P1.2.1 | 0.5    | 1          | ✓             | ✓ Can start Day 1 |
|           | P1.2.2 | 1      | 2          | —             | ✓                 |
|           | P1.2.3 | 1      | 2          | —             | ✓                 |
|           | P1.2.4 | 0.5    | 3          | —             | —                 |
|           | P1.2.5 | 1      | 3          | —             | —                 |
| **P1.3**  | P1.3.1 | 0.5    | 2          | —             | ✓ Can start Day 1 |
|           | P1.3.2 | 0.5    | 2          | —             | ✓                 |
|           | P1.3.3 | 0.5    | 3          | —             | ✓                 |
|           | P1.3.4 | 0.5    | 3          | —             | ✓                 |
|           | P1.3.5 | 0.5    | 3          | —             | ✓                 |
| **TOTAL** | —      | **13** | **3 days** | —             | —                 |

---

## Recommended Execution Order

### Day 1 (Critical Path + Parallel Start)

- **P1.1.1-3** (Rust scaffold, auth, client) — 3 person-days
- **P1.2.1** (Cache interface) — 0.5 pd — Start in parallel
- **P1.3.1** (Configuration system) — 0.5 pd — Start in parallel

### Day 2

- **P1.1.4-6** (Conversations, Documents, tests) — 3 pd
- **P1.2.2-3** (Redis, FileCache) — 2 pd — Parallel
- **P1.3.2** (Auth CLI) — 0.5 pd — Parallel

### Day 3

- **P1.2.4-5** (Context manager, benchmarks) — 1.5 pd
- **P1.3.3-5** (MCP, docs, health) — 2 pd — Parallel
- **Integration & final testing** — 0.5 pd

---

## Success Criteria (Phase 1 Complete)

1. **All code written and tested**
   - P1.1: Rust client compiles, 40+ tests pass, docs build
   - P1.2: Python cache providers, 30+ tests pass, benchmarks show target throughput
   - P1.3: Config system works, CLI commands functional, docs complete

2. **Integration**
   - `thegent login supermemory` works end-to-end
   - MCP tools callable from agents
   - `thegent doctor supermemory` passes all checks

3. **Quality Gates**
   - All tests pass (>85% coverage)
   - Lint/type checks green
   - Security scan passes (no secrets, valid dependencies)

4. **Documentation**
   - Setup guide runnable by new users
   - API reference complete
   - Troubleshooting covers common issues

5. **Ready for Phase 2**
   - Rust client API stable (no breaking changes planned)
   - Cache infrastructure performs to SLO (<5ms P99, >800 ops/sec)
   - Foundation ready for semantic search + graph memory

---

## Next Action

Move this document to `docs/reference/` and add work items to WORK_STREAM.md.
