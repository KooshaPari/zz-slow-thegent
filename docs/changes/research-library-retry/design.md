# Retry Library Design Document

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Application Code (HTTP client, DB, Agent Service)              │
│  @retry(strategy="http") or @retry_async(strategy="agent")      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Retry Decorator Layer (retry.py)                               │
│  - @retry(strategy, config)                                     │
│  - @retry_async(strategy, config)                               │
│  - retry_context(strategy, config)                              │
│  - Observability hooks (before_attempt, after_attempt)          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Strategy Layer (strategies.py)                                 │
│  - HTTPStrategy (4xx/5xx/timeout detection)                    │
│  - DatabaseStrategy (connection errors, transient locks)        │
│  - AgentStrategy (temporary unavailability, rate limits)        │
│  - CustomStrategy (user-defined exception matchers)            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tenacity Layer (wrapped)                                        │
│  - tenacity.Retrying                                             │
│  - wait_random_exponential (base 2, max jitter)                │
│  - stop_after_attempt / stop_after_delay                        │
│  - Custom stop/wait strategies                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  OpenTelemetry Layer (observability.py)                         │
│  - Span events for each retry attempt                           │
│  - Metrics: retry_attempts (counter), retry_latency (histogram)│
│  - Attributes: strategy, attempt #, error type, backoff delay   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. RetryConfig (pydantic Settings)

```python
class RetryConfig(BaseSettings):
    """Configuration for retry behavior."""

    strategy: str = "default"  # "http", "db", "agent", "default"
    max_attempts: int = 5
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

    # Timeout (for stop_after_delay)
    total_timeout_seconds: float | None = None

    # Observability
    emit_metrics: bool = True
    emit_traces: bool = True

    model_config = SettingsConfigDict(env_prefix="RETRY_")
```

### 2. RetryStrategy (Enum + Matcher)

```python
class RetryStrategy(str, Enum):
    DEFAULT = "default"  # Retry on any Exception
    HTTP = "http"  # HTTP 5xx, timeouts, connection errors
    DATABASE = "database"  # DB connection errors, transient locks
    AGENT = "agent"  # Agent service unavailability
    CUSTOM = "custom"  # User-provided exception matcher


def strategy_matcher(strategy: RetryStrategy) -> Callable[[Exception], bool]:
    """Returns a predicate: Exception -> bool (retry or not)."""
```

### 3. Core Decorators

#### Sync Version
```python
@retry(strategy="http", max_attempts=3, max_delay_seconds=10)
def fetch_data(url: str) -> dict: ...
```

#### Async Version
```python
@retry_async(strategy="agent", max_attempts=5)
async def call_agent(prompt: str) -> str: ...
```

#### Context Manager
```python
with retry_context(strategy="db", max_attempts=2):
    cursor.execute(query)
    result = cursor.fetchall()
```

### 4. Pre-Built Strategies

#### HTTPStrategy
- **Retryable errors**:
  - 5xx status codes (500, 502, 503, 504)
  - Connection errors (ConnectionError, TimeoutError)
  - Partial reads (httpx.ReadError)
- **Non-retryable**: 4xx (client fault), 3xx (redirect handled by httpx)
- **Default config**: max_attempts=5, exponential_base=2, max_delay=60s

#### DatabaseStrategy
- **Retryable errors**:
  - Database connection errors (psycopg2.OperationalError, etc.)
  - Transient locks (psycopg2.extensions.TransactionRollbackError)
  - Pool exhaustion (sqlalchemy.pool.NullPool errors)
- **Non-retryable**: Integrity violations, syntax errors
- **Default config**: max_attempts=3, exponential_base=2, max_delay=30s

#### AgentStrategy
- **Retryable errors**:
  - Service unavailability (503, 500)
  - Rate limit errors (429)
  - Timeout (agent taking too long)
- **Default config**: max_attempts=7, exponential_base=2, max_delay=120s

### 5. Observability Integration

#### Span Events
Each retry attempt emits a span event:
```json
{
  "name": "retry_attempt",
  "attributes": {
    "retry.strategy": "http",
    "retry.attempt": 2,
    "retry.max_attempts": 5,
    "retry.error_type": "ConnectionError",
    "retry.next_delay_seconds": 4.2,
    "retry.total_delay_seconds": 6.0
  },
  "timestamp": "2026-02-18T10:30:45Z"
}
```

#### Metrics
```python
# Counter: number of retry attempts
retry_attempts = Counter(
    name="retry_attempts_total",
    description="Total number of retry attempts",
    attributes=["strategy", "error_type", "outcome"],  # outcome: "success" | "exhausted" | "timeout"
)

# Histogram: latency of retried operation (including backoff)
retry_latency = Histogram(
    name="retry_latency_seconds",
    description="Latency of operations with retries",
    attributes=["strategy", "outcome"],
)
```

#### Attributes (in Span)
Every span created in a retried operation includes:
- `retry.strategy`: Strategy name
- `retry.enabled`: Boolean (true if retries active)
- `retry.attempt`: Current attempt number (0-indexed)
- `retry.max_attempts`: Max attempts configured

## Exception Hierarchy

```python
class RetryException(Exception):
    """Base exception for retry-specific errors."""

    pass


class RetryExhausted(RetryException):
    """Raised when max attempts reached."""

    last_exception: Exception
    attempts: int


class RetryTimeout(RetryException):
    """Raised when total_timeout_seconds exceeded."""

    last_exception: Exception
    elapsed_seconds: float
```

## Configuration

### Environment Variables (pydantic SettingsConfigDict)
```bash
RETRY_STRATEGY=http
RETRY_MAX_ATTEMPTS=5
RETRY_MAX_DELAY_SECONDS=60.0
RETRY_EXPONENTIAL_BASE=2.0
RETRY_JITTER=true
RETRY_EMIT_METRICS=true
RETRY_EMIT_TRACES=true
```

### Programmatic (Override in Code)
```python
retry_config = RetryConfig(
    strategy="agent",
    max_attempts=10,
    max_delay_seconds=120.0,
)

@retry(config=retry_config)
def call_agent(...):
    ...
```

## Integration Points

### With Agent Services
```python
# In agent runner
@retry_async(strategy="agent")
async def run_agent(agent_id: str, prompt: str) -> str:
    return await http_client.post(f"{AGENT_URL}/run", json={"prompt": prompt})
```

### With HTTP Client (httpx)
```python
# Wrap httpx.AsyncClient
class RetryableAsyncClient(httpx.AsyncClient):
    @retry_async(strategy="http")
    async def request(self, *args, **kwargs):
        return await super().request(*args, **kwargs)
```

### With Database (SQLAlchemy)
```python
# Wrap connection/transaction
@retry(strategy="database")
def execute_query(query):
    with engine.connect() as conn:
        return conn.execute(query)
```

## Error Handling & Backoff

### Backoff Strategy
- **Function**: `wait_random_exponential(multiplier=1, max=60)`
- **Formula**: `min(2^attempt + random(0, 1), 60)`
- **Example**:
  - Attempt 1: ~1s + jitter
  - Attempt 2: ~2s + jitter
  - Attempt 3: ~4s + jitter
  - Attempt 4: ~8s + jitter
  - Attempt 5: ~16s + jitter (capped at 60s)

### Stop Conditions
1. **Max Attempts**: Stop after N attempts (default 5)
2. **Total Timeout**: Stop if total_timeout_seconds exceeded
3. **Success**: Stop on first successful attempt

### Logging & Observability
- **Before attempt**: Log "Attempting [operation], attempt N/M"
- **After attempt (success)**: Log "Success after N attempts, total latency X.Xs"
- **After attempt (retry)**: Log "Retrying after error [type], waiting Ns before attempt N"
- **After attempt (exhausted)**: Log "Max attempts exhausted, last error: [...]"

## Test Strategy

### Unit Tests
- **Config validation**: Invalid retry configs raise errors
- **Strategy matching**: Each strategy correctly identifies retryable exceptions
- **Backoff calculation**: Exponential backoff is correct (no jitter variation)
- **Decorator behavior**: Retries work for sync/async/context manager
- **Observability**: Span events emitted, metrics recorded

### Integration Tests
- **HTTP strategy**: Mock HTTP service, test 5xx retry
- **Database strategy**: Mock DB, test connection error retry
- **Agent strategy**: Mock agent service, test timeout retry
- **End-to-end**: Full retry cycle (attempt 1 fails, attempt 2 succeeds)
- **Exhaustion**: Verify RetryExhausted raised after max attempts

### Performance Tests
- **Nominal path** (no retry): <1ms overhead
- **Backoff calculation**: <100us per attempt
- **Span events**: <10ms total for 5 retries

## Implementation Order

1. **Phase 1**: Core retry library (RetryConfig, decorators, tenacity wrapper)
2. **Phase 2**: Strategies (HTTP, Database, Agent pre-built strategies)
3. **Phase 3**: Observability (OpenTelemetry instrumentation, span events, metrics)
4. **Phase 4**: Tests (unit, integration, performance)
5. **Phase 5**: Documentation (guide, examples, migration paths)
6. **Phase 6**: Integration (3+ services migrated)

---

## Comparison with Alternatives

### Option 1: Custom Retry Loop (Manual)
- **Pros**: No dependency, complete control
- **Cons**: Code duplication, no observability, maintainability burden
- **Verdict**: ❌ Rejected (CLAUDE.md: "No manual retry loops")

### Option 2: Existing pybreaker (Circuit Breaker)
- **Pros**: Prevents cascading failures
- **Cons**: Different concern; doesn't handle backoff/retry logic
- **Verdict**: ✅ Complementary (pybreaker for circuit breaking, tenacity for retry)

### Option 3: tenacity (Chosen)
- **Pros**: Battle-tested, well-documented, extensible, already a dependency
- **Cons**: Requires thin wrapper for project conventions
- **Verdict**: ✅ Chosen (standard practice across industry)

### Option 4: asyncio.retry / Stamina
- **Pros**: Alternative libraries with similar features
- **Cons**: Less mature than tenacity, not in current dependencies
- **Verdict**: ❌ Rejected (prefer existing dependency)

---

## Open Questions

1. **Should we integrate with circuit breaker (pybreaker)?** Scope for Phase 2?
2. **Should we auto-retry on all HTTPExceptions or be explicit per error?** Current design: explicit
3. **Should rate-limit errors (429) always retry with exponential backoff, or use Retry-After header?** Design decision: Use Retry-After if present, else exponential
