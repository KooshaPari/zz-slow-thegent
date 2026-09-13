# Supermemory Integration Design

**Status**: Ready for Implementation
**Date**: 2026-02-18
**Architecture**: Event-driven, layered caching with cloud fallback

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [API Contracts](#api-contracts)
5. [Failure Handling](#failure-handling)
6. [Performance Characteristics](#performance-characteristics)
7. [Testing Strategy](#testing-strategy)
8. [Deployment](#deployment)

---

## System Architecture

### Multi-Layer Memory Model

```
┌────────────────────────────────────────────────────────┐
│                   Application Layer                     │
│         (thegent Orchestration, Simulation)             │
└────────────────────┬─────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│ MemoryAPI    │          │ ArtifactAPI  │
│ (Queries)    │          │ (Storage)    │
└──────────────┘          └──────────────┘
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   LayeredCache          │
        │  (L1/L2/L3/L4)          │
        └────────────┬────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌─────────┐    ┌─────────┐    ┌──────────────────┐
│  L1: In │    │  L2: On │    │  L3/L4:          │
│  Memory │    │  Disk   │    │  Supermemory     │
│  LRU    │    │  FileDB │    │  (Knowledge+Docs)│
└─────────┘    └─────────┘    └──────────────────┘
   (16MB)        (1GB)         (Unlimited)
   <1ms         <10ms          <50-200ms
```

### Layer Responsibilities

| Layer | Purpose | Latency | Capacity | Provider |
|-------|---------|---------|----------|----------|
| **L1** | Hot cache | <1ms | 16 MB | LRU in-memory |
| **L2** | Warm cache | <10ms | 1 GB | Disk file storage |
| **L3** | Knowledge Graph | <50ms | Unlimited | Supermemory Knowledge API |
| **L4** | Immutable documents | <200ms | Unlimited | Supermemory Documents API |

---

## Component Design

### 1. SupermemoryClient (Rust)

**Location**: `thegent/crates/thegent-memory/src/client.rs`

```rust
pub struct SupermemoryClient {
    mcp_url: String,
    api_key: String,
    project_id: String,
    http_client: httpx::Client,
    retry_policy: RetryPolicy,
    circuit_breaker: CircuitBreaker,
}

impl SupermemoryClient {
    pub async fn store_knowledge(
        &self,
        entity: &str,
        relationships: Vec<Relationship>,
    ) -> Result<String>;

    pub async fn query_knowledge(
        &self,
        query: &str,
        limit: usize,
    ) -> Result<Vec<KnowledgeNode>>;

    pub async fn store_document(
        &self,
        artifact: &MAIFArtifact,
    ) -> Result<String>;

    pub async fn retrieve_document(
        &self,
        doc_id: &str,
    ) -> Result<MAIFArtifact>;
}
```

**Features**:
- Automatic retry with exponential backoff
- Circuit breaker (fail after 3 consecutive failures)
- Multi-tenant project scoping via header
- Request timeout (30s default)
- Connection pooling

### 2. MemoryManager (Python)

**Location**: `thegent/src/thegent/memory/manager.py`

```python
class MemoryManager:
    def __init__(self, config: MemoryConfig):
        self.l1_cache = LRUCache(max_size=16 * 1024 * 1024)
        self.l2_cache = FileCache(path=config.cache_dir)
        self.l3_client = SupermemoryClient(
            mcp_url=config.supermemory_url,
            project_id=config.project_id,
        )
        self.health_monitor = HealthMonitor()

    async def get_knowledge(self, query: str) -> List[KnowledgeNode]:
        """Layered read: L1 → L2 → L3"""
        # Try L1
        if key in self.l1_cache:
            return self.l1_cache[key]

        # Try L2
        if self.l2_cache.exists(key):
            data = self.l2_cache.get(key)
            self.l1_cache[key] = data
            return data

        # Try L3
        try:
            data = await self.l3_client.query_knowledge(query)
            self.l1_cache[key] = data
            self.l2_cache.set(key, data)
            return data
        except Exception as e:
            self.health_monitor.record_failure("L3_query", e)
            raise

    async def store_artifact(self, artifact: MAIFArtifact) -> str:
        """Store to L4 with L2 backup"""
        # Store in L4
        doc_id = await self.l3_client.store_document(artifact)

        # Backup to L2
        self.l2_cache.set(f"artifact:{doc_id}", artifact)

        return doc_id
```

**Features**:
- Automatic layering with fallback
- TTL-based eviction from L1
- Consistency between layers
- Failure monitoring

### 3. MAIFArtifact (Rust)

**Location**: `thegent/crates/thegent-maif/src/lib.rs`

```rust
pub struct MAIFArtifact {
    pub id: String,
    pub timestamp: u64,
    pub action_type: ActionType,
    pub agent_id: String,
    pub session_id: String,
    pub input_hash: String,
    pub output_hash: String,
    pub signature: String,
    pub previous_hash: String, // Hash chain
    pub metadata: serde_json::Value,
}

impl MAIFArtifact {
    pub fn new(
        action_type: ActionType,
        agent_id: String,
        input: &[u8],
        output: &[u8],
        previous_hash: Option<String>,
    ) -> Self;

    pub fn verify(&self, previous_hash: &str) -> bool;

    pub fn compute_hash(&self) -> String;
}
```

**Hash Chain**:
```
artifact_hash = SHA256(input_hash || output_hash || previous_hash)
signature = Sign(artifact_hash, agent_private_key)
```

**Properties**:
- Immutable once signed
- Tampering detection via hash chain
- Agent identity verification via signature
- Audit trail completeness

### 4. SimulationReplay (Python)

**Location**: `thegent/src/thegent/ux/replay.py`

```python
class SimulationReplay:
    def __init__(self, memory: MemoryManager, artifacts: MAIFStorage):
        self.memory = memory
        self.artifacts = artifacts

    async def replay_decision(
        self,
        session_id: str,
        decision_id: str,
    ) -> ReplayResult:
        """Replay decision deterministically"""
        # Retrieve context from L3
        context = await self.memory.get_knowledge(f"session:{session_id} decision:{decision_id}")

        # Retrieve artifacts from L4
        artifacts = await self.artifacts.get_artifacts(session_id)

        # Reconstruct environment
        env = self._reconstruct_environment(context, artifacts)

        # Replay
        result = await self._execute_deterministic(env, artifacts)

        return ReplayResult(
            original=artifacts[-1],
            replayed=result,
            matches=result.output_hash == artifacts[-1].output_hash,
        )
```

**Deterministic Guarantees**:
- Same random seed
- Mocked external APIs
- Isolated execution
- Time-travel debugging

---

## Data Flow

### Write Path (Store Artifact)

```
Application
    │
    ├─> Create MAIFArtifact
    │   (with hash chain)
    │
    ├─> Sign artifact
    │
    ├─> Store to L4 (Supermemory)
    │   [with retry + fallback to L2]
    │
    └─> Update L3 knowledge graph
        (session context)
```

### Read Path (Query Knowledge)

```
Application
    │
    ├─> Check L1 (in-memory)
    │   └─> Hit: return (P95: <1ms)
    │
    ├─> Check L2 (disk)
    │   └─> Hit: return + refresh L1 (P95: <10ms)
    │
    ├─> Query L3 (Supermemory)
    │   └─> Hit: return + cache to L1/L2 (P95: <50ms)
    │
    └─> Not found: return error
        [+ log to monitoring]
```

### Error Path (L3 Failure)

```
Query L3
    │
    ├─> Failure
    │   │
    │   ├─> Check circuit breaker
    │   │   ├─> Open: skip L3, return from L2
    │   │   └─> Closed: retry with backoff
    │   │
    │   ├─> Max retries reached?
    │   │   ├─> No: exponential backoff
    │   │   └─> Yes: open circuit breaker
    │   │
    │   └─> Record health metric
```

---

## API Contracts

### Memory API

```python
class IMemoryManager(Protocol):
    async def get_knowledge(
        self,
        query: str,
        limit: int = 100,
    ) -> List[KnowledgeNode]:
        """Query knowledge graph (L3 with layered fallback)"""
        ...

    async def store_knowledge(
        self,
        entity: str,
        relationships: List[Relationship],
    ) -> str:
        """Store to L3 knowledge graph"""
        ...

    async def get_artifact(self, doc_id: str) -> MAIFArtifact:
        """Retrieve artifact from L4 (with L2 fallback)"""
        ...

    async def store_artifact(
        self,
        artifact: MAIFArtifact,
    ) -> str:
        """Store to L4 documents API"""
        ...
```

### Artifact API

```python
class IMAIFStorage(Protocol):
    async def create_artifact(
        self,
        action_type: str,
        agent_id: str,
        input: bytes,
        output: bytes,
    ) -> MAIFArtifact:
        """Create and sign artifact"""
        ...

    async def verify_chain(
        self,
        artifacts: List[MAIFArtifact],
    ) -> bool:
        """Verify hash chain integrity"""
        ...

    async def store(self, artifact: MAIFArtifact) -> str:
        """Store to L4 (Supermemory Documents API)"""
        ...
```

---

## Failure Handling

### Circuit Breaker

```python
class CircuitBreaker:
    STATES = ["CLOSED", "OPEN", "HALF_OPEN"]

    def __init__(self, failure_threshold: int = 3):
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            # Check timeout (30 seconds)
            if time.time() - self.last_failure_time > 30:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpen("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise
```

### Retry Policy

```python
class RetryPolicy:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def call_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except transient_error as e:
                wait_time = 2**attempt + random.uniform(0, 1)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### Fallback Strategy

| Failure | Fallback |
|---------|----------|
| L3 query fails | Return from L2 (if available) |
| L3 store fails | Queue write to L2; retry later |
| L4 retrieve fails | Return from L2 backup |
| L4 store fails | Queue to L2; block write with timeout |

---

## Performance Characteristics

### Latency Targets

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| L1 hit | <0.1ms | <0.5ms | <1ms |
| L2 hit | <5ms | <10ms | <20ms |
| L3 query | <30ms | <50ms | <100ms |
| L3 store | <50ms | <100ms | <200ms |
| L4 store | <100ms | <200ms | <500ms |
| Artifact verify | <5ms | <10ms | <20ms |

### Throughput Targets

| Operation | Throughput | Unit |
|-----------|-----------|------|
| L1 reads | 1M | req/s |
| L1 writes | 100K | req/s |
| L3 queries | 1000 | req/s |
| L3 stores | 500 | req/s |
| L4 stores | 500 | req/s |
| Verify chain | 5000 | req/s |

### Resource Usage

| Resource | Target | Notes |
|----------|--------|-------|
| L1 memory | 16 MB | LRU cache |
| L2 disk | 1 GB | FileDB |
| Network (L3/L4) | <1 Mbps avg | Bursty during batch ops |
| CPU | <5% | Crypto ops, hashing |

---

## Testing Strategy

### Unit Tests

```python
# test_memory_manager.py
class TestMemoryManager:
    async def test_l1_hit(self):
        """L1 cache hit returns immediately"""
        ...

    async def test_l2_fallback(self):
        """L2 fallback when L1 miss"""
        ...

    async def test_l3_query(self):
        """L3 query returns knowledge nodes"""
        ...

    async def test_circuit_breaker_open(self):
        """Circuit breaker opens after threshold"""
        ...

    async def test_artifact_signature(self):
        """Artifacts signed correctly"""
        ...

    async def test_hash_chain_verify(self):
        """Hash chain verification works"""
        ...
```

**Coverage Target**: >85%

### Integration Tests

```python
# test_integration.py
class TestSupermemoryIntegration:
    async def test_end_to_end_artifact_storage(self):
        """Create, sign, store, retrieve artifact"""
        ...

    async def test_fallback_on_l3_failure(self):
        """Fallback to L2 when L3 fails"""
        ...

    async def test_deterministic_replay(self):
        """Replay decision with same output"""
        ...

    async def test_multi_tenant_isolation(self):
        """Projects isolated from each other"""
        ...
```

### Performance Tests

```python
# test_performance.py
class TestPerformance:
    async def test_l1_latency(self):
        """L1 hits under 1ms"""
        ...

    async def test_l3_throughput(self):
        """L3 queries 1000+ req/s"""
        ...

    async def test_batch_storage(self):
        """Batch artifact storage meets SLO"""
        ...
```

---

## Deployment

### Configuration

```toml
# .env.example
SM_MCP_URL="https://mcp.supermemory.ai/mcp"
SM_PROJECT_ID="my-project"
SM_API_KEY="sk-..."

# Cache settings
MEMORY_L1_SIZE_MB=16
MEMORY_L2_PATH="/var/cache/thegent"
MEMORY_L2_SIZE_MB=1024

# Retry policy
MEMORY_RETRY_MAX=3
MEMORY_RETRY_BACKOFF_BASE=2

# Circuit breaker
MEMORY_CB_THRESHOLD=3
MEMORY_CB_TIMEOUT_SEC=30
```

### Monitoring

**Key Metrics**:
- `memory_layer_hit_rate` — L1/L2/L3 hit rates
- `memory_latency_p95` — Query latency (by layer)
- `memory_circuit_breaker_state` — CB status
- `memory_artifacts_stored` — Artifact storage rate
- `memory_hash_chain_errors` — Hash chain failures

**Dashboards**:
- Memory operations overview
- Layer hit rates
- Error rates and failures
- Cost tracking (API calls to Supermemory)

### Runbooks

**Runbook: Circuit Breaker Stuck Open**
1. Check Supermemory API status
2. Manually reset circuit breaker: `thegent memory reset-cb`
3. Monitor L3 queries for recovery
4. If not recovered: open incident

**Runbook: L2 Cache Corruption**
1. Identify corrupted keys in logs
2. Remove corrupted entries: `thegent memory clean-l2`
3. Force L3 refresh: `thegent memory refresh-cache`
4. Verify artifact chain: `thegent memory verify-chain`

---

## References

- [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md](../research/SESSION_RESEARCH_FRAGMENTS_EXPANDED.md) — Research foundation
- [proposal.md](./proposal.md) — Product proposal
- [tasks.md](./tasks.md) — Implementation tasks
- [Supermemory.ai Docs](https://supermemory.ai/docs) — External API

---

**Design Review**: Pending
**Last Updated**: 2026-02-18
