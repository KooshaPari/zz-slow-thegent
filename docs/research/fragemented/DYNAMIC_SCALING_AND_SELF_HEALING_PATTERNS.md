<DONE>
# Dynamic Scaling and Self-Healing Patterns: Comprehensive Reference

**Document Version**: 1.0
**Date**: 2026-02-19
**Category**: Research, Architecture, Resilience
**Status**: Complete Reference

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Core Patterns Overview](#core-patterns-overview)
3. [Dynamic Scaling Patterns](#dynamic-scaling-patterns)
4. [Self-Healing Techniques](#self-healing-techniques)
5. [Tools & Frameworks](#tools--frameworks)
6. [Implementation Guide for Agent Swarms](#implementation-guide-for-agent-swarms)
7. [Recovery Patterns](#recovery-patterns)
8. [Code Examples](#code-examples)
9. [Configuration & Deployment](#configuration--deployment)
10. [Monitoring & Observability](#monitoring--observability)
11. [Anti-Patterns & Pitfalls](#anti-patterns--pitfalls)
12. [Decision Matrix](#decision-matrix)

---

## Executive Summary

Modern distributed systems require **resilience by design**. This document synthesizes best practices for:

- **Dynamic Scaling**: Adapting concurrency, load, and resource allocation in real-time
- **Self-Healing**: Automatic recovery without external intervention
- **Graceful Degradation**: Reducing scope rather than failing catastrophically
- **Agent Swarms**: Coordination of multiple autonomous agents with health management

### Key Principle

> **Fail gracefully, recover automatically, scale adaptively — never silently degrade.**

---

## Core Patterns Overview

### Pattern Families

| Pattern | Purpose | Key Mechanism | When to Use |
|---------|---------|---------------|-----------|
| **Circuit Breaker** | Pause before failing | Tracks failures; opens/closes state | External service calls, APIs |
| **Bulkhead** | Isolate failures | Separate thread pools/resources | CPU-bound, I/O-bound isolation |
| **Throttling** | Control load | Queue, rate limit, reject | Prevent overload, backpressure |
| **Exponential Backoff** | Reduce retries | Increasing wait between attempts | Transient failures |
| **Adaptive Concurrency** | Scale with success | Adjust parallel workers | Dynamic workload handling |
| **Health Checks** | Monitor state | Periodic heartbeat | Detect failures early |
| **Auto-Restart** | Resume operation | Restart on failure | Process crashes, hangs |
| **Graceful Degradation** | Reduce, not kill | Drop low-priority work | Resource exhaustion |
| **Resource Pooling** | Prevent starvation | Reuse connections, threads | Database, HTTP connections |
| **Load Shedding** | Reject work | Drop excess load | Overload protection |

---

## Dynamic Scaling Patterns

### 1. Circuit Breaker Pattern

**Concept**: Monitor failures; automatically open circuit when threshold exceeded; half-open for recovery.

**State Machine**:
```
        CLOSED (healthy)
           ↓ (failure threshold exceeded)
        OPEN (failing fast)
           ↓ (timeout elapsed)
      HALF_OPEN (test recovery)
           ↓ (success)
        CLOSED
           ↓ (failure)
        OPEN
```

**Key Parameters**:
- `failure_threshold`: Number of failures before opening (e.g., 5)
- `timeout_seconds`: Time in OPEN state before trying HALF_OPEN (e.g., 60s)
- `success_threshold`: Number of successes in HALF_OPEN before closing (e.g., 3)
- `window_size`: Sliding window for tracking failures (e.g., 10 calls)

**When to Use**:
- External API calls (network might recover)
- Database connections (pool might exhaust)
- Microservice calls (downstream service might restart)
- Any "call-wait-fail" scenario

**Benefits**:
- Prevents cascading failures
- Reduces load on failing service
- Fast-fail behavior (no hanging requests)

**Drawback**:
- Requests fail immediately in OPEN state (expected behavior)

---

### 2. Bulkhead Pattern

**Concept**: Partition resources (threads, connections) to isolate failures.

**Types**:

#### Thread Pool Bulkhead
```
Main Thread Pool → [Task 1, Task 2, Task 3]
CPU-Bound Pool → [CPU Task 1, CPU Task 2]
I/O-Bound Pool → [API Call 1, API Call 2]
```

One pool exhaustion doesn't block others.

#### Connection Pool Bulkhead
```
Main DB Pool (20 connections) → General queries
Analytics Pool (5 connections) → Reporting queries
Batch Pool (10 connections) → Bulk operations
```

#### Semaphore Bulkhead
```
Limit concurrent calls to resource:
max_concurrent = 10
current_running = 7
available = 3
```

**When to Use**:
- Mixed CPU-bound and I/O-bound workloads
- Multiple service dependencies
- Protecting critical paths from resource exhaustion

**Configuration**:
- **CPU-bound**: Set pool size = CPU cores (e.g., 8)
- **I/O-bound**: Set pool size = CPU cores × 2-4 (e.g., 32)
- **Mixed**: Use separate bulkheads for each type

---

### 3. Throttling & Backpressure

**Concept**: Control inflow rate to prevent overload.

**Strategies**:

#### Rate Limiting (Token Bucket)
```
Tokens per second: 100
Bucket capacity: 1000

Request arrives → Check tokens
  ✓ Tokens available → Deduct & process
  ✗ No tokens → Queue or reject
  ✓ Tokens refill each second
```

#### Queuing with Backpressure
```
Load → Queue (max=1000) → Worker Pool (size=50)

Queue full? → Backpressure signal
Caller → Slow down, retry, or fail gracefully
```

#### Adaptive Throttling
```
Success rate > 95%? → Increase rate (ramp up)
Success rate < 80%? → Decrease rate (ramp down)
```

**When to Use**:
- API rate limits (external services)
- Database connection pooling
- Message queue systems
- Preventing thundering herd

---

### 4. Exponential Backoff with Jitter

**Concept**: Increase wait time between retries; add randomness to prevent thundering herd.

**Formula**:
```
wait_time = min(max_wait, base_wait × (2 ^ attempt) + random_jitter)

Example (base=1s, max=60s):
Attempt 1: 1s + 0-500ms  = 1.0-1.5s
Attempt 2: 2s + 0-500ms  = 2.0-2.5s
Attempt 3: 4s + 0-500ms  = 4.0-4.5s
Attempt 4: 8s + 0-500ms  = 8.0-8.5s
Attempt 5: 16s + 0-500ms = 16.0-16.5s
Attempt 6: 32s + 0-500ms = 32.0-32.5s
Attempt 7: 60s (capped)
```

**Why Jitter**:
- Prevents coordinated retries from multiple clients
- Spreads load naturally over time
- Reduces "thundering herd" effect

**Configuration**:
- `base_wait`: Starting wait (1-2s for network; 100ms for local)
- `max_wait`: Maximum wait (30-60s typical)
- `jitter_factor`: Randomness (0.0-1.0, typically 0.1-0.5)
- `max_retries`: Total attempts (3-5 typical)

---

### 5. Adaptive Concurrency Control

**Concept**: Adjust parallelism based on success rate (Little's Law).

**Formula**:
```
optimal_concurrency = throughput × latency

Dynamic adjustment:
  if (success_rate > 95%) → concurrency += 1
  if (success_rate < 80%) → concurrency -= 1
  if (p95_latency > SLO) → concurrency -= 1
```

**Example**:
```
Initial concurrency: 10
Success rate: 98% → Increase to 11
Latency spike detected → Decrease to 9
Success rate recovers → Increase to 10
```

**When to Use**:
- Load varies dramatically
- Latency SLOs matter
- System can handle variable load
- Not fixed-scale workloads

**Benefits**:
- Automatically finds optimal concurrency
- Adapts to resource changes
- Better utilization without overload

---

## Self-Healing Techniques

### 1. Health Checks (Heartbeat Monitoring)

**Concept**: Periodic verification that system is operational.

**Types**:

#### Liveness Probe
```
Question: "Is the service running?"
Answer: "Yes" (process exists, can respond)
Action: Restart if "No" for N consecutive checks
Frequency: Every 10-30 seconds
Timeout: 5 seconds
```

#### Readiness Probe
```
Question: "Is the service ready to serve requests?"
Answer: "Yes" (all dependencies available, warmed up)
Action: Remove from load balancer if "No"
Frequency: Every 5-10 seconds
Timeout: 3 seconds
```

#### Startup Probe
```
Question: "Is the service still starting up?"
Answer: "Yes" (waiting for dependencies)
Action: Give grace period; don't restart yet
Duration: Until first "No" answer
Frequency: Every 1 second
```

**Implementation**:
```python
# Simple HTTP health check
GET /health/live → 200 OK if running
GET /health/ready → 200 OK if ready
GET /health/startup → 200 OK if fully started

# Health response:
{
  "status": "healthy",
  "uptime": 3600,
  "checks": {
    "db": "ok",
    "cache": "ok",
    "queue": "ok"
  }
}
```

**Configuration**:
- Liveness: 10s interval, 3 failures to restart
- Readiness: 5s interval, 2 failures to remove
- Startup: 1s interval, 30s max startup time

---

### 2. Automatic Restart Policies

**Concept**: Automatically restart failed processes with backoff.

**Policy Types**:

#### Immediate Restart
```
Process exits → Restart immediately

Use when:
- Crashes are rare
- Fast restart is safe
- No state loss on restart
```

#### Exponential Backoff Restart
```
Attempt 1: Restart now
Attempt 2: Wait 2s, restart
Attempt 3: Wait 4s, restart
Attempt 4: Wait 8s, restart
Attempt 5: Wait 16s, restart
Attempt 6+: Wait 30s (cap), restart

Use when:
- Failure might be temporary
- Each restart has cost
- Want to give system time to recover
```

#### Circuit Breaker Restart
```
If restart_count > 5 in 10 minutes:
  → OPEN: Don't restart (alert human)
  → Wait 30 minutes
  → HALF_OPEN: Try one restart
  → If success: CLOSED (reset counter)
  → If failure: OPEN again

Use when:
- Restart won't help (permanent failure)
- Need human intervention
- Restart has high cost
```

**Configuration**:
```yaml
restart_policy:
  strategy: "exponential_backoff"
  initial_backoff_ms: 2000
  max_backoff_ms: 30000
  backoff_multiplier: 2.0
  max_retries: 10
  circuit_breaker:
    failure_threshold: 5
    timeout_seconds: 600  # 10 minutes
```

---

### 3. Graceful Degradation

**Concept**: Reduce functionality rather than crash.

**Strategies**:

#### Feature Degradation
```
Database unavailable?
  ✓ Cache hits: Serve from cache
  ✓ Cache miss: Serve default value or simplified response
  ✓ Queue writes: Buffer locally, retry later
  ✗ Don't crash
```

#### Load Shedding
```
Queue > 95% capacity?
  1. Drop lowest-priority work
  2. Reject new requests with 503 (Temporarily Unavailable)
  3. Continue processing high-priority work
  4. Wait for queue to drain
```

#### Timeout with Fallback
```
Call external service:
  timeout: 5s
  on_timeout: Return cached result or default
  don't_wait: Keep retrying in background
```

#### Cascading Degradation
```
Level 1: Full service
Level 2: Reduce query complexity (no joins)
Level 3: Serve read-only (no writes)
Level 4: Serve from cache only
Level 5: Return error page or SLA-based response
```

**When to Use**:
- Dependencies fail (database, external API)
- Resource exhaustion (memory, CPU)
- Traffic spikes
- Coordinated attacks (rate limit)

---

### 4. Resource Pooling

**Concept**: Reuse expensive resources to prevent starvation.

**Types**:

#### Database Connection Pool
```
Pool size: 20 connections
Idle timeout: 5 minutes

Request → Acquire connection (or wait)
         → Execute query
         → Release connection (back to pool)

Benefits:
- Avoid creating new connection per request
- Reuse TCP connection
- Prevent "connection pool exhaustion"
```

#### HTTP Connection Pool
```
Pool size: 100 sockets per host
Timeout: 60 seconds

Benefits:
- HTTP Keep-Alive (persistent connections)
- Avoid TCP handshake per request
- Better throughput
```

#### Thread Pool
```
Fixed pool: 50 threads
Queue capacity: 1000 tasks

Benefits:
- Avoid creating new thread per task
- Prevent unlimited thread creation
- Bounded resource usage
```

#### Object Pool (Cache)
```
Pool: [Object1, Object2, ..., ObjectN]
Reuse after use
Benefits:
- Avoid GC pressure
- Fast allocation
- Predictable memory usage
```

**Configuration**:
- **Connection pools**: Size = (core_count × 2) to (core_count × 4)
- **Thread pools**: Size = core_count (CPU) or core_count × 2-4 (I/O)
- **Idle timeout**: 5-30 minutes
- **Max wait**: 5-30 seconds

---

### 5. Load Shedding

**Concept**: Strategically drop work to maintain SLO.

**Strategies**:

#### Priority-Based Shedding
```
Level 0: Critical (user requests)
Level 1: Important (batch jobs)
Level 2: Nice-to-have (analytics)
Level 3: Background (cleanup)

When overloaded → Drop from Level 3 first
                 → Then Level 2
                 → Never drop Level 0
```

#### Queue-Depth Based
```
Queue size policy:
  < 50%: Accept all
  50-75%: Warn (increase capacity if possible)
  75-95%: Reject non-critical
  > 95%: Reject all but critical

This prevents queue from growing unbounded
```

#### Timeout-Based
```
Task deadline: 10 seconds
Processing time: 8 seconds

Deadline vs. remaining time?
  ✓ Deadline - processing_time > latency → Accept
  ✗ Deadline - processing_time < latency → Reject (will timeout)
```

**Response to Shed Request**:
```
HTTP 503 Service Unavailable
Retry-After: 60

Or:

HTTP 429 Too Many Requests
Retry-After: 60
```

---

## Tools & Frameworks

### Python Ecosystem

#### Tenacity (Retry with Backoff)

**Installation**: `pip install tenacity`

**Features**:
- Exponential backoff with jitter
- Multiple stop conditions (max retries, timeout)
- Retry on specific exceptions
- Pre/post retry hooks
- Async support

**Example**:
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
def call_external_api():
    return requests.get("https://api.example.com/data")
```

#### PyBreaker (Circuit Breaker)

**Installation**: `pip install pybreaker`

**Features**:
- State management (CLOSED, OPEN, HALF_OPEN)
- Configurable thresholds
- Listeners for state changes
- Async support

**Example**:
```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(
    fail_max=5,
    timeout_seconds=60,
    listeners=[on_open, on_close],
)


def call_api():
    try:
        return breaker.call(requests.get, "https://api.example.com")
    except CircuitBreaker.CircuitBreakerListenerException:
        return None  # Fallback
```

#### Resilience4py (Comprehensive Resilience)

**Installation**: `pip install resilience4py`

**Features**:
- Circuit breaker, bulkhead, retry, timeout
- Chainable decorators
- Metrics and monitoring
- Async support

**Example**:
```python
from resilience4py import CircuitBreaker, Bulkhead, Retry


@CircuitBreaker(max_failures=5, timeout=60)
@Bulkhead(max_concurrent_calls=10)
@Retry(max_attempts=3, wait=1000)
async def call_external_service():
    return await httpx.get("https://api.example.com")
```

#### APScheduler (Scheduled Tasks)

**Installation**: `pip install apscheduler`

**Features**:
- Scheduled task execution
- Multiple schedulers (cron, interval, date)
- Job persistence
- Async support

**Example**:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler()


@scheduler.scheduled_job(IntervalTrigger(seconds=10))
def health_check():
    # Runs every 10 seconds
    check_system_health()


scheduler.start()
```

#### Pydantic + Validation (Configuration)

**Installation**: `pip install pydantic`

**Features**:
- Type-safe configuration
- Validation on load
- Environment variable support

**Example**:
```python
from pydantic import BaseModel, Field


class ResilienceConfig(BaseModel):
    circuit_breaker_threshold: int = Field(default=5, ge=1, le=100)
    timeout_seconds: float = Field(default=30, gt=0, le=300)
    retry_max_attempts: int = Field(default=3, ge=1, le=10)
    bulkhead_max_concurrent: int = Field(default=50, ge=1, le=1000)


config = ResilienceConfig()
```

### Process Management

#### Systemd (Linux Native)

**Service Configuration**:
```ini
[Unit]
Description=My Agent Service
After=network.target

[Service]
Type=simple
User=agent
ExecStart=/usr/bin/python /app/agent.py
Restart=on-failure
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
```

**Auto-restart policy**:
- `Restart=on-failure` — Restart if exit code != 0
- `RestartSec=10` — Wait 10s between restarts
- `StartLimitBurst=5` — Max 5 restarts in interval
- `StartLimitInterval=300` — Within 5 minutes

#### Supervisor (Python Process Manager)

**Installation**: `pip install supervisor`

**Configuration**:
```ini
[program:agent]
command=/usr/bin/python /app/agent.py
autorestart=true
startsecs=10
stopwaitsecs=10
redirect_stderr=true
stdout_logfile=/var/log/agent.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
```

**Features**:
- Python-native process management
- Automatic restart
- Log rotation
- Group management

#### Tmux (Session Recovery)

**Session Management**:
```bash
# Create session
tmux new-session -d -s agent-1

# Send command
tmux send-keys -t agent-1 "python agent.py" Enter

# Attach for monitoring
tmux attach-session -t agent-1

# List sessions
tmux list-sessions
```

**Recovery**:
```bash
# Session survives terminal disconnect
# Reconnect later:
tmux attach-session -t agent-1
```

### Container Orchestration

#### Docker Health Checks

**Dockerfile**:
```dockerfile
FROM python:3.12

COPY agent.py /app/agent.py

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/health_check.py

CMD ["python", "/app/agent.py"]
```

**Health Check Script**:
```python
#!/usr/bin/env python
import requests
import sys

try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        sys.exit(0)  # Healthy
except:
    pass

sys.exit(1)  # Unhealthy
```

**Docker Compose**:
```yaml
services:
  agent:
    build: .
    healthcheck:
      test: ["CMD", "python", "/app/health_check.py"]
      interval: 30s
      timeout: 10s
      start_period: 5s
      retries: 3
    restart_policy:
      condition: on-failure
      delay: 5s
      max_attempts: 5
      window: 300s
```

#### Kubernetes Probes

**Liveness Probe** (is it alive?):
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

**Readiness Probe** (is it ready?):
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

**Startup Probe** (is it still starting?):
```yaml
startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 1
  timeoutSeconds: 5
  failureThreshold: 30
```

---

## Implementation Guide for Agent Swarms

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ Agent Swarm Coordinator                                 │
│ ┌──────────────────────────────────────────────────┐   │
│ │ • Health Monitor (heartbeat every 5-10s)         │   │
│ │ • Adaptive Concurrency Controller                 │   │
│ │ • Load Balancer                                   │   │
│ │ • Circuit Breaker (per agent type)                │   │
│ └──────────────────────────────────────────────────┘   │
│                                                         │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│ │  Agent 1     │  │  Agent 2     │  │  Agent 3     │  │
│ │ (CPU-bound)  │  │  (I/O-bound) │  │  (Hybrid)    │  │
│ │ PID: 12345   │  │ PID: 12346   │  │ PID: 12347   │  │
│ │ Status: OK   │  │ Status: OK   │  │ Status: SLOW │  │
│ └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    [Health OK]          [Health OK]          [Slow, retry]
```

### 1. Agent Health Heartbeat

**Concept**: Periodic health check (5-10 seconds).

**Implementation**:
```python
import time
import asyncio
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    HEALTHY = "healthy"
    SLOW = "slow"
    UNHEALTHY = "unhealthy"
    CRASHED = "crashed"


@dataclass
class AgentHealth:
    agent_id: str
    status: HealthStatus
    last_heartbeat: float
    response_time_ms: float
    error_count: int


async def health_check_agent(agent_id: str, timeout: float = 5.0) -> AgentHealth:
    """Check if agent is responsive."""
    start = time.time()
    try:
        # Send heartbeat signal
        response = await agent_heartbeat(agent_id, timeout=timeout)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        # Classify health
        if elapsed > 1000:  # > 1s is slow
            status = HealthStatus.SLOW
        elif response.get("error"):
            status = HealthStatus.UNHEALTHY
        else:
            status = HealthStatus.HEALTHY

        return AgentHealth(
            agent_id=agent_id,
            status=status,
            last_heartbeat=time.time(),
            response_time_ms=elapsed,
            error_count=response.get("error_count", 0),
        )

    except asyncio.TimeoutError:
        return AgentHealth(
            agent_id=agent_id,
            status=HealthStatus.UNHEALTHY,
            last_heartbeat=time.time(),
            response_time_ms=timeout * 1000,
            error_count=999,
        )
    except Exception:
        return AgentHealth(
            agent_id=agent_id,
            status=HealthStatus.CRASHED,
            last_heartbeat=time.time(),
            response_time_ms=0,
            error_count=999,
        )


async def monitor_agent_health(agent_ids: list[str], interval_sec: int = 10):
    """Continuously monitor agent health."""
    while True:
        health_checks = []
        for agent_id in agent_ids:
            health = await health_check_agent(agent_id)
            health_checks.append(health)

            # Take action based on health
            if health.status == HealthStatus.CRASHED:
                await restart_agent(agent_id)
            elif health.status == HealthStatus.UNHEALTHY:
                await pause_agent(agent_id)
                # Retry after grace period
                await asyncio.sleep(30)
                await resume_agent(agent_id)
            elif health.status == HealthStatus.SLOW:
                await reduce_agent_workload(agent_id)

        # Log health summary
        log_health_summary(health_checks)
        await asyncio.sleep(interval_sec)
```

### 2. Automatic Pause Instead of Kill

**Concept**: Pause agent (preserve state) instead of killing (lose state).

**Implementation**:
```python
import signal
from enum import Enum
from dataclasses import dataclass


class AgentState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    DRAINING = "draining"  # Finishing current task
    RESTARTING = "restarting"


@dataclass
class Agent:
    pid: int
    state: AgentState
    current_task: str = None
    checkpoint: dict = None


async def pause_agent(agent: Agent, graceful: bool = True):
    """Pause agent gracefully."""
    if agent.state == AgentState.RUNNING:
        agent.state = AgentState.DRAINING  # Let it finish current task

        # Wait up to 60s for task to complete
        for _ in range(60):
            if agent.current_task is None:
                break
            await asyncio.sleep(1)

        # Send SIGSTOP (pause without killing)
        os.kill(agent.pid, signal.SIGSTOP)
        agent.state = AgentState.PAUSED
        print(f"Agent {agent.pid} paused (state preserved)")


async def resume_agent(agent: Agent):
    """Resume paused agent."""
    if agent.state == AgentState.PAUSED:
        # Send SIGCONT (resume)
        os.kill(agent.pid, signal.SIGCONT)
        agent.state = AgentState.RUNNING
        print(f"Agent {agent.pid} resumed")


async def restart_agent_with_backoff(agent: Agent, max_retries: int = 5):
    """Restart with exponential backoff."""
    for attempt in range(1, max_retries + 1):
        wait_time = min(30, 2 ** (attempt - 1))  # 1s, 2s, 4s, 8s, 16s, cap 30s

        print(f"Restarting agent {agent.pid} (attempt {attempt}/{max_retries})")
        agent.state = AgentState.RESTARTING

        # Kill old process
        try:
            os.kill(agent.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # Already dead

        # Wait
        await asyncio.sleep(wait_time)

        # Start new process
        try:
            new_pid = await start_agent_process(agent.pid)
            agent.pid = new_pid
            agent.state = AgentState.RUNNING
            print(f"Agent {agent.pid} restarted successfully")
            return
        except Exception as e:
            print(f"Restart failed: {e}")
            if attempt == max_retries:
                print(f"Max retries ({max_retries}) exceeded. Giving up.")
                agent.state = AgentState.CRASHED
                break
```

### 3. Resource Monitoring

**Concept**: Monitor CPU, memory, disk; take action if exceeded.

**Implementation**:
```python
import psutil
from dataclasses import dataclass


@dataclass
class ResourceThresholds:
    cpu_percent_max: float = 80.0
    memory_percent_max: float = 85.0
    memory_gb_max: float = 8.0


async def monitor_agent_resources(
    agent_pid: int,
    thresholds: ResourceThresholds,
):
    """Monitor agent resource usage."""
    try:
        process = psutil.Process(agent_pid)

        # Get resource usage
        cpu_percent = process.cpu_percent(interval=1)
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        memory_gb = memory_info.rss / (1024**3)

        # Check thresholds
        if cpu_percent > thresholds.cpu_percent_max:
            print(f"High CPU: {cpu_percent}%")
            await reduce_agent_workload(agent_pid)

        if memory_gb > thresholds.memory_gb_max:
            print(f"High memory: {memory_gb:.2f} GB")
            # Pause and let garbage collection work
            os.kill(agent_pid, signal.SIGSTOP)
            await asyncio.sleep(10)
            os.kill(agent_pid, signal.SIGCONT)

        if memory_percent > thresholds.memory_percent_max:
            print(f"High memory %: {memory_percent}%")
            # Clear caches, reduce buffers
            await cleanup_agent_memory(agent_pid)

    except psutil.NoSuchProcess:
        print(f"Agent {agent_pid} not found")
```

### 4. Queue Management (Backpressure)

**Concept**: Don't accept new work if overloaded.

**Implementation**:
```python
from collections import deque
from dataclasses import dataclass


@dataclass
class QueueMetrics:
    size: int
    capacity: int
    load_percent: float


class BackpressureQueue:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queue = deque(maxlen=max_size)
        self.metrics = QueueMetrics(0, max_size, 0.0)

    async def enqueue(self, task, priority: int = 1) -> bool:
        """
        Try to enqueue task. Return False if queue full.

        Priority levels:
        0 = CRITICAL (always accept)
        1 = HIGH (accept if < 90%)
        2 = NORMAL (accept if < 75%)
        3 = LOW (accept if < 50%)
        """
        self.metrics.size = len(self.queue)
        self.metrics.load_percent = (self.metrics.size / self.max_size) * 100

        # Check priority-based acceptance
        if priority == 0:  # CRITICAL
            can_accept = self.metrics.size < self.max_size
        elif priority == 1:  # HIGH
            can_accept = self.metrics.load_percent < 90
        elif priority == 2:  # NORMAL
            can_accept = self.metrics.load_percent < 75
        else:  # LOW
            can_accept = self.metrics.load_percent < 50

        if can_accept:
            self.queue.append((priority, task))
            return True
        else:
            # Backpressure: reject with 503
            print(f"Backpressure: Queue {self.metrics.load_percent:.1f}% full")
            return False

    async def dequeue(self):
        """Dequeue highest-priority task."""
        if not self.queue:
            return None

        # Sort by priority (lower = higher priority)
        tasks = sorted(self.queue, key=lambda x: x[0])
        if tasks:
            priority, task = tasks[0]
            self.queue.remove((priority, task))
            return task
        return None
```

### 5. Graceful Drain Pattern

**Concept**: Stop accepting new work; finish current tasks.

**Implementation**:
```python
class AgentSwarm:
    def __init__(self, num_agents: int = 10):
        self.agents = [Agent(i) for i in range(num_agents)]
        self.draining = False
        self.queue = BackpressureQueue()

    async def graceful_drain(self, timeout: float = 300):
        """
        Stop accepting new work.
        Finish current tasks.
        Restart after drain.
        """
        print("Initiating graceful drain...")
        self.draining = True

        # Step 1: Stop accepting new work
        print("Step 1: Stopped accepting new work")

        # Step 2: Wait for agents to finish current tasks
        start = time.time()
        while time.time() - start < timeout:
            active_tasks = sum(1 for agent in self.agents if agent.current_task is not None)
            if active_tasks == 0:
                print("Step 2: All agents finished their tasks")
                break

            print(f"Waiting... {active_tasks} tasks still running")
            await asyncio.sleep(5)

        # Step 3: Process remaining queued items
        while not self.queue.queue.empty() and time.time() - start < timeout:
            task = await self.queue.dequeue()
            if task:
                print(f"Processing queued task: {task}")
                # Process task

        # Step 4: Resume accepting work
        self.draining = False
        print("Graceful drain complete. Ready for new work.")
```

---

## Recovery Patterns

### 1. Circuit Breaker State Machine

**Full State Flow**:

```python
from enum import Enum
from typing import Callable, Any
import time


class CircuitBreakerState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: float = 60,
        success_threshold: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_open_time = None

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection."""

        # CLOSED: Normal operation
        if self.state == CircuitBreakerState.CLOSED:
            try:
                result = await func(*args, **kwargs)
                self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    self.last_open_time = time.time()
                    print(f"{self.name}: Circuit OPEN (failure_count={self.failure_count})")

                raise

        # OPEN: Failing fast
        elif self.state == CircuitBreakerState.OPEN:
            # Check if timeout elapsed
            if time.time() - self.last_open_time > self.timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                print(f"{self.name}: Circuit HALF_OPEN (testing recovery)")
            else:
                # Still in timeout, fail immediately
                raise Exception(f"{self.name}: Circuit breaker is OPEN")

        # HALF_OPEN: Testing recovery
        if self.state == CircuitBreakerState.HALF_OPEN:
            try:
                result = await func(*args, **kwargs)
                self.success_count += 1

                if self.success_count >= self.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    print(f"{self.name}: Circuit CLOSED (recovered)")

                return result
            except Exception as e:
                self.state = CircuitBreakerState.OPEN
                self.last_open_time = time.time()
                self.failure_count = 0
                self.success_count = 0
                print(f"{self.name}: Circuit OPEN (recovery failed)")
                raise
```

### 2. Bulkhead Isolation

**Full Implementation**:

```python
import asyncio
from typing import Callable, Any


class Bulkhead:
    """Isolate resources to prevent cascading failures."""

    def __init__(self, name: str, max_concurrent: int = 50):
        self.name = name
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_count = 0
        self.max_concurrent = max_concurrent
        self.rejected_count = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with bulkhead protection."""
        try:
            # Try to acquire permit (non-blocking)
            acquired = self.semaphore._value > 0
            if not acquired and self.active_count >= self.max_concurrent:
                self.rejected_count += 1
                raise Exception(f"{self.name}: Bulkhead exhausted ({self.active_count}/{self.max_concurrent})")

            # Acquire permit (might wait)
            async with self.semaphore:
                self.active_count += 1
                try:
                    return await func(*args, **kwargs)
                finally:
                    self.active_count -= 1
        except asyncio.QueueFull:
            self.rejected_count += 1
            raise


class MultiResourceBulkhead:
    """Multiple bulkheads for different resource types."""

    def __init__(self):
        self.bulkheads = {
            "cpu_bound": Bulkhead("cpu_bound", max_concurrent=8),
            "io_bound": Bulkhead("io_bound", max_concurrent=50),
            "database": Bulkhead("database", max_concurrent=20),
        }

    async def call_cpu_bound(self, func, *args, **kwargs):
        return await self.bulkheads["cpu_bound"].call(func, *args, **kwargs)

    async def call_io_bound(self, func, *args, **kwargs):
        return await self.bulkheads["io_bound"].call(func, *args, **kwargs)

    async def call_database(self, func, *args, **kwargs):
        return await self.bulkheads["database"].call(func, *args, **kwargs)

    def get_stats(self):
        return {
            name: {
                "active": bh.active_count,
                "max": bh.max_concurrent,
                "rejected": bh.rejected_count,
                "utilization": bh.active_count / bh.max_concurrent,
            }
            for name, bh in self.bulkheads.items()
        }
```

### 3. Timeout with Fallback

**Implementation**:

```python
import asyncio
from functools import wraps


async def with_timeout_and_fallback(
    func,
    timeout_sec: float,
    fallback_func=None,
    fallback_value=None,
):
    """
    Call function with timeout.
    On timeout: use fallback function or return fallback value.
    """
    try:
        return await asyncio.wait_for(func(), timeout=timeout_sec)
    except asyncio.TimeoutError:
        if fallback_func:
            return await fallback_func()
        elif fallback_value is not None:
            return fallback_value
        else:
            raise


# Decorator version
def timeout_with_fallback(timeout_sec: float, fallback_value=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_sec)
            except asyncio.TimeoutError:
                if fallback_value is not None:
                    return fallback_value
                raise

        return wrapper

    return decorator


# Usage
@timeout_with_fallback(timeout_sec=5, fallback_value=[])
async def fetch_user_recommendations():
    return await external_ai_service.get_recommendations()
```

### 4. Checkpoint & Resume

**Implementation**:

```python
import json
import os
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class TaskCheckpoint:
    task_id: str
    agent_id: str
    progress: float  # 0.0-1.0
    state: dict[str, Any]
    timestamp: float
    error: str = None


class CheckpointManager:
    def __init__(self, checkpoint_dir: str = "/tmp/checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)

    def save_checkpoint(self, checkpoint: TaskCheckpoint):
        """Save task progress."""
        filename = f"{self.checkpoint_dir}/{checkpoint.task_id}.json"
        with open(filename, "w") as f:
            json.dump(asdict(checkpoint), f)
        print(f"Checkpoint saved: {filename}")

    def load_checkpoint(self, task_id: str) -> TaskCheckpoint:
        """Load task progress."""
        filename = f"{self.checkpoint_dir}/{task_id}.json"
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                return TaskCheckpoint(**data)
        except FileNotFoundError:
            return None

    def clear_checkpoint(self, task_id: str):
        """Clear after successful completion."""
        filename = f"{self.checkpoint_dir}/{task_id}.json"
        if os.path.exists(filename):
            os.remove(filename)


class ResumableTask:
    """Task that can be paused and resumed."""

    async def run_with_checkpoint(self, task_id: str, steps: list[str]):
        """Run task, saving checkpoint after each step."""
        checkpoint_mgr = CheckpointManager()
        checkpoint = checkpoint_mgr.load_checkpoint(task_id)

        # Determine starting point
        start_idx = 0
        if checkpoint:
            print(f"Resuming task {task_id} at {checkpoint.progress * 100:.1f}%")
            start_idx = checkpoint.state.get("last_step_idx", 0)

        # Execute steps
        for idx, step in enumerate(steps[start_idx:], start=start_idx):
            try:
                await self.execute_step(step)
                progress = (idx + 1) / len(steps)

                # Save checkpoint
                checkpoint = TaskCheckpoint(
                    task_id=task_id,
                    agent_id="unknown",
                    progress=progress,
                    state={"last_step_idx": idx},
                    timestamp=time.time(),
                )
                checkpoint_mgr.save_checkpoint(checkpoint)

            except Exception as e:
                # Save error state
                checkpoint = TaskCheckpoint(
                    task_id=task_id,
                    agent_id="unknown",
                    progress=(idx / len(steps)),
                    state={"last_step_idx": idx},
                    timestamp=time.time(),
                    error=str(e),
                )
                checkpoint_mgr.save_checkpoint(checkpoint)
                raise

        # Clean up after success
        checkpoint_mgr.clear_checkpoint(task_id)
```

---

## Code Examples

### Complete Resilient HTTP Client

```python
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from pybreaker import CircuitBreaker


class ResilientHTTPClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
        self.breaker = CircuitBreaker(
            fail_max=5,
            timeout_seconds=60,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get(self, url: str, **kwargs) -> dict:
        """GET with retry and circuit breaker."""

        async def _make_request():
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()
            return response.json()

        return await self.breaker.call(_make_request)

    async def close(self):
        await self.client.aclose()


# Usage
client = ResilientHTTPClient()
try:
    data = await client.get("https://api.example.com/data")
    print(f"Success: {data}")
except Exception as e:
    print(f"Failed after retries: {e}")
```

### Adaptive Concurrency Controller

```python
import asyncio
import time
from dataclasses import dataclass


@dataclass
class ConcurrencyStats:
    current: int
    success_count: int
    failure_count: int
    success_rate: float


class AdaptiveConcurrency:
    def __init__(self, initial: int = 10, min_conc: int = 1, max_conc: int = 100):
        self.current = initial
        self.min_conc = min_conc
        self.max_conc = max_conc
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.time()

    async def adjust(self):
        """Adjust concurrency based on success rate."""
        if time.time() - self.last_adjustment < 10:  # Adjust every 10s
            return

        total = self.success_count + self.failure_count
        if total == 0:
            return

        success_rate = self.success_count / total

        if success_rate > 0.95 and self.current < self.max_conc:
            self.current = min(self.current + 1, self.max_conc)
            print(f"↑ Increased concurrency to {self.current} (success rate: {success_rate:.1%})")
        elif success_rate < 0.80 and self.current > self.min_conc:
            self.current = max(self.current - 1, self.min_conc)
            print(f"↓ Decreased concurrency to {self.current} (success rate: {success_rate:.1%})")

        # Reset counters
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.time()

    async def execute(self, tasks: list[callable]) -> list:
        """Execute tasks with adaptive concurrency."""
        semaphore = asyncio.Semaphore(self.current)

        async def bounded_task(task):
            async with semaphore:
                try:
                    result = await task()
                    self.success_count += 1
                    return result
                except Exception as e:
                    self.failure_count += 1
                    raise

        return await asyncio.gather(*[bounded_task(t) for t in tasks], return_exceptions=True)

    def get_stats(self) -> ConcurrencyStats:
        total = self.success_count + self.failure_count
        success_rate = (self.success_count / total) if total > 0 else 0
        return ConcurrencyStats(
            current=self.current,
            success_count=self.success_count,
            failure_count=self.failure_count,
            success_rate=success_rate,
        )
```

---

## Configuration & Deployment

### Environment Variables

```bash
# Resilience thresholds
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT_SEC=60
CIRCUIT_BREAKER_SUCCESS_THRESHOLD=3

# Retry settings
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_WAIT_SEC=2
RETRY_MAX_WAIT_SEC=60
RETRY_JITTER_FACTOR=0.1

# Bulkhead settings
BULKHEAD_CPU_BOUND=8
BULKHEAD_IO_BOUND=50
BULKHEAD_DATABASE=20

# Health checks
HEALTH_CHECK_INTERVAL_SEC=10
HEALTH_CHECK_TIMEOUT_SEC=5
HEALTH_CHECK_FAILURE_THRESHOLD=3

# Adaptive concurrency
ADAPTIVE_CONCURRENCY_INITIAL=10
ADAPTIVE_CONCURRENCY_MIN=1
ADAPTIVE_CONCURRENCY_MAX=100
ADAPTIVE_CONCURRENCY_SUCCESS_THRESHOLD=0.95
ADAPTIVE_CONCURRENCY_FAILURE_THRESHOLD=0.80
```

### Pydantic Configuration

```python
from pydantic_settings import BaseSettings


class ResilienceSettings(BaseSettings):
    # Circuit breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_sec: float = 60
    circuit_breaker_success_threshold: int = 3

    # Retry
    retry_max_attempts: int = 3
    retry_base_wait_sec: float = 2
    retry_max_wait_sec: float = 60
    retry_jitter_factor: float = 0.1

    # Bulkhead
    bulkhead_cpu_bound: int = 8
    bulkhead_io_bound: int = 50
    bulkhead_database: int = 20

    # Health checks
    health_check_interval_sec: int = 10
    health_check_timeout_sec: float = 5
    health_check_failure_threshold: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True
```

### Docker Compose Example

```yaml
version: "3.9"

services:
  agent-1:
    build:
      context: .
      dockerfile: Dockerfile.agent
    environment:
      AGENT_ID: agent-1
      CIRCUIT_BREAKER_FAILURE_THRESHOLD: 5
      HEALTH_CHECK_INTERVAL_SEC: 10
    ports:
      - "8001:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 5s
    restart: on-failure:5
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  agent-2:
    build:
      context: .
      dockerfile: Dockerfile.agent
    environment:
      AGENT_ID: agent-2
      CIRCUIT_BREAKER_FAILURE_THRESHOLD: 5
      HEALTH_CHECK_INTERVAL_SEC: 10
    ports:
      - "8002:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 5s
    restart: on-failure:5
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  coordinator:
    build:
      context: .
      dockerfile: Dockerfile.coordinator
    depends_on:
      - agent-1
      - agent-2
    environment:
      AGENT_HEALTH_CHECK_INTERVAL_SEC: 10
      ADAPTIVE_CONCURRENCY_INITIAL: 10
    ports:
      - "8000:8000"
    restart: on-failure:5
```

---

## Monitoring & Observability

### Metrics to Track

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResilienceMetrics:
    # Circuit breaker
    cb_state: str  # "CLOSED", "OPEN", "HALF_OPEN"
    cb_failures: int
    cb_state_changes: int

    # Retry
    retry_total_attempts: int
    retry_successes: int
    retry_failures: int

    # Bulkhead
    bh_active_count: int
    bh_max_concurrent: int
    bh_rejected_count: int
    bh_utilization: float

    # Health
    health_checks_passed: int
    health_checks_failed: int
    uptime_sec: float

    # Timestamp
    timestamp: datetime


class MetricsCollector:
    def __init__(self):
        self.metrics = []

    def collect(self, metrics: ResilienceMetrics):
        """Record metrics."""
        self.metrics.append(metrics)

    def get_recent(self, last_n: int = 100) -> list[ResilienceMetrics]:
        """Get last N measurements."""
        return self.metrics[-last_n:]

    def export_prometheus(self) -> str:
        """Export as Prometheus metrics."""
        latest = self.metrics[-1] if self.metrics else None
        if not latest:
            return ""

        lines = [
            f"# HELP resilience_cb_failures Circuit breaker failures",
            f"# TYPE resilience_cb_failures counter",
            f"resilience_cb_failures {latest.cb_failures}",
            f"# HELP resilience_bulkhead_utilization Bulkhead utilization",
            f"# TYPE resilience_bulkhead_utilization gauge",
            f"resilience_bulkhead_utilization {latest.bh_utilization}",
            f"# HELP resilience_health_check_passed Health checks passed",
            f"# TYPE resilience_health_check_passed counter",
            f"resilience_health_check_passed {latest.health_checks_passed}",
        ]
        return "\n".join(lines)
```

### Structured Logging

```python
import json
import logging
from dataclasses import asdict


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "circuit_breaker"):
            log_data["circuit_breaker"] = record.circuit_breaker
        if hasattr(record, "bulkhead"):
            log_data["bulkhead"] = record.bulkhead

        return json.dumps(log_data)


# Setup
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Usage
logger.info(
    "Circuit breaker state changed",
    extra={
        "circuit_breaker": {
            "name": "api_service",
            "state": "OPEN",
            "failures": 5,
        }
    },
)
```

---

## Anti-Patterns & Pitfalls

### ❌ Anti-Pattern 1: Silent Failures

**Bad**:
```python
def call_api():
    try:
        return requests.get(url)
    except:
        return None  # Silent failure!
```

**Good**:
```python
def call_api():
    try:
        return requests.get(url)
    except requests.RequestException as e:
        logger.warning(f"API call failed: {e}", extra={"url": url})
        raise  # Propagate; let caller decide
```

**Why**: Silent failures hide bugs. Explicit is better than implicit.

### ❌ Anti-Pattern 2: Infinite Retries

**Bad**:
```python
@retry(
    stop=never,  # Retries forever!
)
def call_api():
    return requests.get(url)
```

**Good**:
```python
@retry(
    stop=stop_after_attempt(3),
)
def call_api():
    return requests.get(url)
```

**Why**: Infinite retries consume resources and can cascade.

### ❌ Anti-Pattern 3: Retrying Non-Idempotent Operations

**Bad**:
```python
@retry()
async def transfer_money(account_a, account_b, amount):
    # If this is retried, money might transfer twice!
    account_a.balance -= amount
    account_b.balance += amount
    db.commit()
```

**Good**:
```python
@retry(
    retry=retry_if_exception_type(NetworkError),
)
async def transfer_money_idempotent(transaction_id, account_a, account_b, amount):
    # Check if already processed
    if db.get_transaction(transaction_id):
        return  # Already done

    account_a.balance -= amount
    account_b.balance += amount
    db.save_transaction(transaction_id)
    db.commit()
```

**Why**: Retrying non-idempotent operations causes data corruption.

### ❌ Anti-Pattern 4: Not Monitoring Circuit Breaker State

**Bad**:
```python
breaker = CircuitBreaker()
# Never check if breaker is OPEN
# Silent failures when breaker is OPEN
```

**Good**:
```python
breaker = CircuitBreaker()
try:
    await breaker.call(func)
except CircuitBreaker.CircuitBreakerOpenException:
    logger.error("Circuit breaker is OPEN; service unavailable")
    # Send 503, alert team
```

**Why**: You need to know when your safety valve is triggered.

### ❌ Anti-Pattern 5: Fixed Concurrency in Variable Load

**Bad**:
```python
semaphore = asyncio.Semaphore(50)  # Fixed
# If load doubles, still 50; overloaded
# If load halves, still 50; wasted resources
```

**Good**:
```python
adaptive = AdaptiveConcurrency(initial=10)
# Automatically adjusts based on success rate
# Scales up with load, scales down with congestion
```

**Why**: Fixed concurrency doesn't adapt to reality.

### ❌ Anti-Pattern 6: Killing Instead of Pausing

**Bad**:
```python
os.kill(agent_pid, signal.SIGKILL)  # Immediate death
# State lost, in-progress work abandoned
```

**Good**:
```python
await pause_agent(agent_pid)  # SIGSTOP (pause)
# State preserved, can resume
# Or graceful_drain to finish work first
```

**Why**: Killing loses state and work; pausing preserves both.

---

## Decision Matrix

### When to Use Each Pattern

| Scenario | Pattern | Reason |
|----------|---------|--------|
| External API might fail temporarily | Circuit Breaker + Retry | Prevent cascading; let transient failures pass |
| CPU vs I/O mixed workload | Bulkhead | Isolate; prevent CPU starvation of I/O |
| Preventing thundering herd | Exponential Backoff + Jitter | Spread retries over time |
| System overloaded | Load Shedding + Backpressure | Reject gracefully; protect core |
| Service unresponsive | Health Check + Auto-Restart | Detect early; recover automatically |
| High variance load | Adaptive Concurrency | Scale to actual demand |
| Need to preserve work | Checkpoint + Resume | Survive crashes; continue work |
| Must finish current work | Graceful Drain | Safety before restart |
| Preventing starvation | Resource Pooling | Reuse; prevent exhaustion |
| Resource limits exceeded | Bulkhead + Timeout | Isolate; fail fast |

---

## Conclusion

**Key Takeaways**:

1. **Circuit Breaker** prevents cascading failures by failing fast when dependencies fail.
2. **Bulkhead** isolates failures so one problem doesn't break everything.
3. **Throttling & Backpressure** prevent overload and graceful degradation.
4. **Exponential Backoff** reduces thundering herd and lets systems recover.
5. **Adaptive Concurrency** automatically finds optimal parallelism.
6. **Health Checks** detect failures early before they cascade.
7. **Auto-Restart** recovers from transient failures without human intervention.
8. **Graceful Degradation** reduces scope rather than crashing.
9. **Resource Pooling** prevents starvation and exhaustion.
10. **Load Shedding** maintains SLO under overload.

**Apply these patterns systematically** to build resilient, self-healing distributed systems.

---

## References & Further Reading

### Tools
- **Tenacity**: https://tenacity.readthedocs.io/
- **PyBreaker**: https://github.com/danielfm/pybreaker
- **Resilience4py**: https://github.com/davisb10/resilience4py
- **Systemd**: https://systemd.io/
- **Supervisor**: http://supervisord.org/
- **APScheduler**: https://apscheduler.readthedocs.io/

### Papers & Articles
- "Release It! Design and Deploy Production-Ready Software" by Michael Nygard (Circuit Breaker pattern origin)
- "The Tail at Scale" (Google, 2013) - Adaptive strategies
- "Google SRE Book" - Resilience and operational excellence

### Standards
- Kubernetes Probes: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- Prometheus Metrics: https://prometheus.io/docs/instrumenting/exposition_formats/

---

**Document Version**: 1.0
**Last Updated**: 2026-02-19
**Status**: Complete Reference for Implementation
