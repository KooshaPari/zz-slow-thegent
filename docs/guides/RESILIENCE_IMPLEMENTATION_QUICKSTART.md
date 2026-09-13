# Resilience Patterns: Quick-Start Implementation Guide

**Document Version**: 1.0
**Date**: 2026-02-19
**Category**: Implementation Guide
**Audience**: Backend engineers, DevOps, systems architects

---

## Quick Navigation

- **[5-Minute Setup](#5-minute-setup)** — Get basic resilience working
- **[Copy-Paste Code](#copy-paste-code)** — Ready-to-use implementations
- **[Common Scenarios](#common-scenarios)** — Solutions to real problems
- **[Troubleshooting](#troubleshooting)** — Debug resilience issues
- **[Deployment Checklist](#deployment-checklist)** — Pre-production verification

---

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
pip install tenacity pybreaker httpx asyncio pydantic
```

### Step 2: Create Base Resilience Client

**File**: `src/resilience/http_client.py`

```python
import httpx
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from pybreaker import CircuitBreaker


class ResilientHTTPClient:
    """HTTP client with retry, circuit breaker, timeout."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
        self.breaker = CircuitBreaker(
            fail_max=5,
            timeout_seconds=60,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (
                httpx.NetworkError,
                httpx.TimeoutException,
            )
        ),
    )
    async def get(self, url: str) -> dict:
        """GET request with retry and circuit breaker."""

        async def _request():
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()

        return await self.breaker.call(_request)

    async def close(self):
        await self.client.aclose()


# Usage
client = ResilientHTTPClient()
try:
    data = await client.get("https://api.example.com/data")
    print(f"✓ Success: {data}")
except Exception as e:
    print(f"✗ Failed: {e}")
```

### Step 3: Create Health Check Endpoint

**File**: `src/health.py`

```python
from fastapi import FastAPI, Response
from enum import Enum
import time

app = FastAPI()


class HealthStatus(Enum):
    HEALTHY = 200
    UNHEALTHY = 503


startup_time = time.time()


@app.get("/health/live")
async def health_live(response: Response):
    """Liveness: Is service running?"""
    response.status_code = HealthStatus.HEALTHY.value
    return {
        "status": "alive",
        "uptime_sec": time.time() - startup_time,
    }


@app.get("/health/ready")
async def health_ready(response: Response):
    """Readiness: Is service ready to serve?"""
    try:
        # Check dependencies
        await check_database()
        await check_cache()

        response.status_code = HealthStatus.HEALTHY.value
        return {"status": "ready"}
    except Exception as e:
        response.status_code = HealthStatus.UNHEALTHY.value
        return {"status": "not_ready", "reason": str(e)}


async def check_database():
    """Verify database connectivity."""
    # Your DB ping logic
    pass


async def check_cache():
    """Verify cache connectivity."""
    # Your cache ping logic
    pass
```

### Step 4: Configure Docker Health Check

**File**: `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/

# Health check
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=5s \
    --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
```

**That's it!** You now have:
- ✅ Retry with exponential backoff
- ✅ Circuit breaker protection
- ✅ Health checks
- ✅ Docker automatic restart

---

## Copy-Paste Code

### Pattern 1: Retry with Fallback

```python
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def call_external_api():
    return await httpx.get("https://api.example.com/data")


# With fallback
async def call_with_fallback():
    try:
        return await call_external_api()
    except Exception:
        return {"cached": True, "data": []}  # Fallback value
```

### Pattern 2: Circuit Breaker

```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(
    fail_max=5,  # Open after 5 failures
    timeout_seconds=60,  # Wait 60s before retrying
)


async def call_protected_service():
    try:
        return await breaker.call(some_async_function)
    except CircuitBreaker.CircuitBreakerListenerException:
        logger.error("Circuit breaker OPEN")
        return None
```

### Pattern 3: Concurrent with Semaphore

```python
import asyncio


async def run_with_concurrency(tasks, max_concurrent=10):
    """Run tasks with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_task(task):
        async with semaphore:
            return await task()

    return await asyncio.gather(*[bounded_task(t) for t in tasks])


# Usage
tasks = [fetch_user(i) for i in range(100)]
results = await run_with_concurrency(tasks, max_concurrent=10)
```

### Pattern 4: Timeout with Default

```python
import asyncio


async def call_with_timeout(coro, timeout_sec=5, default=None):
    """Call with timeout; return default on timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_sec)
    except asyncio.TimeoutError:
        logger.warning(f"Timeout after {timeout_sec}s")
        return default


# Usage
result = await call_with_timeout(
    fetch_recommendations(),
    timeout_sec=5,
    default=[],  # Return empty list on timeout
)
```

### Pattern 5: Bulkhead (Thread Pool Isolation)

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor


class Bulkhead:
    def __init__(self, max_workers=10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def call_cpu_bound(self, func, *args):
        """Run CPU-bound function in separate pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)


# Usage
bulkhead = Bulkhead(max_workers=4)
result = await bulkhead.call_cpu_bound(expensive_cpu_function)
```

### Pattern 6: Graceful Shutdown

```python
import asyncio
import signal


class Service:
    def __init__(self):
        self.running = True
        self.tasks = []

    async def start(self):
        """Start service with graceful shutdown."""
        # Register signal handlers
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, self.stop)
        loop.add_signal_handler(signal.SIGINT, self.stop)

        # Run until stopped
        while self.running:
            await asyncio.sleep(1)

    def stop(self):
        """Graceful shutdown."""
        print("Stopping...")
        self.running = False

    async def run_task_with_cleanup(self, coro):
        """Run task; ensure cleanup on shutdown."""
        task = asyncio.create_task(coro)
        self.tasks.append(task)

        try:
            return await task
        finally:
            self.tasks.remove(task)
```

---

## Common Scenarios

### Scenario 1: External API Integration

**Problem**: External API is flaky; occasional timeouts and errors.

**Solution**:
```python
class ExternalAPIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10)
        self.breaker = CircuitBreaker(fail_max=5, timeout_seconds=60)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (
                httpx.TimeoutException,
                httpx.NetworkError,
            )
        ),
    )
    async def get_user(self, user_id: str) -> dict:
        async def _fetch():
            resp = await self.client.get(f"/users/{user_id}")
            resp.raise_for_status()
            return resp.json()

        return await self.breaker.call(_fetch)

    async def get_user_cached(self, user_id: str, cache):
        """With cache fallback."""
        try:
            return await self.get_user(user_id)
        except Exception:
            # Try cache
            cached = await cache.get(f"user:{user_id}")
            if cached:
                return cached
            raise
```

### Scenario 2: Database Connection Management

**Problem**: Too many concurrent DB connections cause pool exhaustion.

**Solution**:
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://...",
    pool_size=20,  # Max idle connections
    max_overflow=10,  # Max overflow connections
    pool_timeout=30,  # Wait 30s for connection
    pool_recycle=3600,  # Recycle connections every hour
)


async def get_user_with_timeout(user_id: int):
    """Query with timeout."""
    try:
        async with engine.connect() as conn:
            # Execute with explicit timeout
            result = await asyncio.wait_for(
                conn.execute(select(User).where(User.id == user_id)),
                timeout=5,
            )
            return result.first()
    except asyncio.TimeoutError:
        logger.warning(f"DB query timeout for user {user_id}")
        return None
```

### Scenario 3: Background Task Queue

**Problem**: Long-running tasks fail silently; need automatic retry and monitoring.

**Solution**:
```python
from celery import Celery
from tenacity import retry, stop_after_attempt, wait_exponential

app = Celery("tasks")


@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def process_batch(self, batch_id: str):
    """Process batch with automatic retry."""
    try:
        # Process logic
        result = do_processing(batch_id)
        return {"status": "success", "result": result}
    except Exception as exc:
        logger.error(f"Processing failed: {exc}")
        # Automatic retry with exponential backoff
        raise self.retry(exc=exc)
```

### Scenario 4: Load Shedding Under High Load

**Problem**: System overloaded; need to reject requests gracefully.

**Solution**:
```python
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

app = FastAPI()


class LoadShedder:
    def __init__(self, max_queue_size=1000):
        self.queue_size = 0
        self.max_queue_size = max_queue_size

    async def check_capacity(self):
        """Check if system can accept more work."""
        if self.queue_size >= self.max_queue_size * 0.9:
            raise OverloadError("System overloaded")

    async def increment(self):
        self.queue_size += 1

    async def decrement(self):
        self.queue_size -= 1


shedder = LoadShedder()


@app.post("/process")
async def process_request(response: Response):
    """Process request; shed load if needed."""
    await shedder.increment()
    try:
        await shedder.check_capacity()  # May raise

        # Process work
        result = await do_work()
        return result

    except OverloadError:
        response.status_code = 503
        return JSONResponse(
            {"error": "Service temporarily overloaded"},
            status_code=503,
            headers={"Retry-After": "60"},
        )
    finally:
        await shedder.decrement()
```

### Scenario 5: Health-Aware Load Balancing

**Problem**: Load balancer doesn't know agent health; sends requests to slow/unhealthy agents.

**Solution**:
```python
import httpx
import asyncio
from dataclasses import dataclass


@dataclass
class Agent:
    id: str
    url: str
    health: str = "unknown"
    response_time_ms: float = 0


class AgentPool:
    def __init__(self, agents: list[Agent]):
        self.agents = agents

    async def health_check_all(self):
        """Check health of all agents."""
        tasks = [self.check_agent(agent) for agent in self.agents]
        await asyncio.gather(*tasks)

    async def check_agent(self, agent: Agent):
        """Check single agent."""
        try:
            start = asyncio.get_event_loop().time()
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{agent.url}/health")
                elapsed = (asyncio.get_event_loop().time() - start) * 1000

                agent.health = "healthy" if resp.status_code == 200 else "unhealthy"
                agent.response_time_ms = elapsed
        except Exception:
            agent.health = "unhealthy"

    def get_best_agent(self) -> Agent:
        """Get healthiest, fastest agent."""
        healthy = [a for a in self.agents if a.health == "healthy"]
        if not healthy:
            healthy = self.agents  # Fallback to all

        return min(healthy, key=lambda a: a.response_time_ms)

    async def call_best_agent(self, endpoint: str):
        """Call endpoint on best agent."""
        await self.health_check_all()
        agent = self.get_best_agent()
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{agent.url}{endpoint}")
            return resp.json()
```

---

## Troubleshooting

### Issue 1: Circuit Breaker Always OPEN

**Symptom**: Circuit breaker transitions to OPEN but never recovers.

**Diagnosis**:
```python
# Check circuit breaker state
print(f"State: {breaker.state}")
print(f"Failure count: {breaker.fail_counter}")
print(f"Last failure: {breaker.last_failure_time}")
```

**Fix**:
```python
# Increase timeout or reset failures
breaker = CircuitBreaker(
    fail_max=5,
    timeout_seconds=120,  # Increased from 60
    fail_counter=0,  # Reset counter manually if needed
)

# Or manually reset
breaker.fail_counter = 0
```

### Issue 2: Retry Storms (Too Many Retries)

**Symptom**: Logs full of retry attempts; system hammering failing service.

**Diagnosis**:
```python
# Log retry attempts
import logging

logging.basicConfig(level=logging.DEBUG)

# Enable tenacity logging
logging.getLogger("tenacity").setLevel(logging.DEBUG)
```

**Fix**:
```python
@retry(
    stop=stop_after_attempt(2),  # Reduce from 3
    wait=wait_exponential(multiplier=2, min=5, max=60),  # Longer waits
    retry=retry_if_exception_type((NetworkError,)),  # Only specific errors
)
async def api_call():
    pass
```

### Issue 3: Connection Pool Exhaustion

**Symptom**: `sqlite3.OperationalError: database is locked` or connection pool timeout.

**Diagnosis**:
```python
# Check pool status
from sqlalchemy import event
from sqlalchemy.pool import Pool


@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    print(f"Connection created. Pool size: {dbapi_conn}")


@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    print(f"Connection checked out")
```

**Fix**:
```python
# Increase pool size
engine = create_async_engine(
    "postgresql+asyncpg://...",
    pool_size=50,  # Increase
    max_overflow=20,  # Increase
)

# Or use connection pooling in application
from aiopool import AioPool

pool = AioPool(min_size=10, max_size=50)
```

### Issue 4: Timeout Too Short

**Symptom**: Tasks timing out even though they're fast; false alarms.

**Diagnosis**:
```python
# Measure actual latency
import time

start = time.time()
result = await operation()
elapsed = time.time() - start
print(f"Took {elapsed}s")
```

**Fix**:
```python
# Set timeout to P99 latency + buffer
# If P99 is 3s, set timeout to 5-6s
@timeout_with_fallback(timeout_sec=5)  # Increased from 2
async def operation():
    pass
```

---

## Deployment Checklist

### Pre-Production Verification

- [ ] **Retry Logic**
  - [ ] `max_retries` set (typically 3)
  - [ ] Exponential backoff enabled with jitter
  - [ ] Only retrying idempotent operations
  - [ ] Specific exception types (not all exceptions)

- [ ] **Circuit Breaker**
  - [ ] Failure threshold configured (e.g., 5)
  - [ ] Timeout set (e.g., 60s)
  - [ ] Success threshold for recovery (e.g., 3)
  - [ ] Monitoring/alerting on state changes

- [ ] **Timeouts**
  - [ ] HTTP timeouts set (e.g., 30s)
  - [ ] DB query timeouts set (e.g., 5s)
  - [ ] Task timeouts set appropriate to SLO

- [ ] **Health Checks**
  - [ ] Liveness endpoint responding (/health/live)
  - [ ] Readiness endpoint responding (/health/ready)
  - [ ] Docker/K8s probes configured
  - [ ] Alert on repeated failures

- [ ] **Resource Limits**
  - [ ] Connection pool size configured (20-50 typical)
  - [ ] Thread pool size appropriate (cores × 2-4)
  - [ ] Memory limits set
  - [ ] CPU limits set

- [ ] **Monitoring**
  - [ ] Metrics exposed (Prometheus/StatsD)
  - [ ] Logs structured (JSON format)
  - [ ] Alerts configured for key metrics
  - [ ] Dashboard created

- [ ] **Graceful Shutdown**
  - [ ] SIGTERM handler implemented
  - [ ] In-flight requests complete before shutdown
  - [ ] Connections closed cleanly
  - [ ] Tests verify graceful shutdown

- [ ] **Load Testing**
  - [ ] Spike test (sudden load increase)
  - [ ] Soak test (sustained load for hours)
  - [ ] Chaos test (kill random processes)
  - [ ] Results documented

---

## Configuration Template

**File**: `config/resilience.yaml`

```yaml
resilience:
  retry:
    max_attempts: 3
    base_wait_sec: 2
    max_wait_sec: 60
    jitter_factor: 0.1

  circuit_breaker:
    failure_threshold: 5
    timeout_seconds: 60
    success_threshold: 3
    enabled: true

  bulkhead:
    cpu_bound:
      max_workers: 8
    io_bound:
      max_workers: 50
    database:
      pool_size: 20
      max_overflow: 10

  timeout:
    http_request_sec: 30
    db_query_sec: 5
    task_sec: 300

  health_check:
    interval_sec: 10
    timeout_sec: 5
    failure_threshold: 3

  monitoring:
    metrics_enabled: true
    log_level: INFO
    sample_rate: 0.1
```

---

## Next Steps

1. **Copy 5-Minute Setup** to your project
2. **Test locally** with `python -m pytest`
3. **Deploy to staging** and monitor
4. **Run deployment checklist** before production
5. **Reference full guide** at `/docs/research/DYNAMIC_SCALING_AND_SELF_HEALING_PATTERNS.md`

---

**Need help?** See the full reference guide for detailed explanations and advanced patterns.
