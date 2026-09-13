<DONE>
# Cross-Platform Desktop Automation: Integration Guide

**Purpose:** Comprehensive guide for integrating desktop automation with existing thegent systems (distributed coordination, observability, state persistence, testing).

**Date:** 2026-02-16
**Status:** Research & Integration Guide
**Related:** CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md

---

## Table of Contents

1. [Distributed Coordination Integration](#1-distributed-coordination-integration)
2. [Observability Integration](#2-observability-integration)
3. [State Persistence Integration](#3-state-persistence-integration)
4. [Testing Strategy Integration](#4-testing-strategy-integration)
5. [Error Handling Integration](#5-error-handling-integration)
6. [Cost & Rate Limiting Integration](#6-cost--rate-limiting-integration)
7. [Security Integration](#7-security-integration)
8. [Performance Integration](#8-performance-integration)
9. [Troubleshooting Guide](#9-troubleshooting-guide)
10. [Migration Path](#10-migration-path)

---

## 1. Distributed Coordination Integration

### 1.1 EditLeaseManager Integration

**Purpose:** Use existing `EditLeaseManager` for file-level coordination during desktop automation.

**Integration Pattern:**

```python
from thegent.orchestration.leasing import get_lease_manager, EditLeaseManager


class DesktopAutomationCoordinator:
    """Coordinate desktop automation with edit leases."""

    def __init__(self, state_dir: Path):
        self.lease_manager = get_lease_manager(state_dir)
        self.automation_locks: dict[str, EditLease] = {}

    def acquire_automation_lock(self, scope: AutomationScope, agent_id: str, duration: float = 300.0) -> bool:
        """Acquire automation lock using edit lease pattern."""
        # Convert automation scope to lease path
        lease_path = self._scope_to_lease_path(scope)

        # Acquire lease
        acquired = self.lease_manager.acquire(path=lease_path, agent_id=agent_id, duration=duration, force=False)

        if acquired:
            self.automation_locks[lease_path] = EditLease(
                path=lease_path, agent_id=agent_id, expires_at=time.time() + duration
            )

        return acquired

    def release_automation_lock(self, scope: AutomationScope, agent_id: str):
        """Release automation lock."""
        lease_path = self._scope_to_lease_path(scope)
        self.lease_manager.release(lease_path, agent_id)
        self.automation_locks.pop(lease_path, None)

    def _scope_to_lease_path(self, scope: AutomationScope) -> str:
        """Convert automation scope to lease path."""
        # Format: "automation:{app_name}:{window_title}:{region}"
        return f"automation:{scope.app_name}:{scope.window_title}:{scope.region}"
```

**Benefits:**

- Reuses existing coordination infrastructure
- Zero-latency in-memory coordination (MTSP-14)
- Automatic expiration prevents deadlocks
- File-based persistence for recovery

### 1.2 Redis-Based Distributed Coordination

**Purpose:** Extend to Redis for multi-machine coordination.

**Integration Pattern:**

```python
import redis
from redis.lock import Lock


class DistributedAutomationCoordinator:
    """Distributed coordination via Redis."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.lock_timeout = 300  # 5 minutes

    def acquire_distributed_lock(self, scope: AutomationScope, agent_id: str, ttl: int = 300) -> Lock | None:
        """Acquire distributed lock via Redis."""
        lock_key = f"automation:lock:{scope.app_name}:{scope.window_title}"

        lock = Lock(redis=self.redis, name=lock_key, timeout=ttl, sleep=0.1, blocking_timeout=5.0)

        if lock.acquire(blocking=False):
            # Store lock metadata
            self.redis.setex(
                f"{lock_key}:meta",
                ttl,
                json.dumps({"agent_id": agent_id, "acquired_at": time.time(), "scope": scope.to_dict()}),
            )
            return lock

        return None

    def release_distributed_lock(self, lock: Lock):
        """Release distributed lock."""
        lock.release()
```

**Redis Patterns:**

- **Pub/Sub:** Real-time event notifications (`thegent:automation:{scope}:events`)
- **Streams:** Persistent automation event log
- **Redlock:** Distributed mutual exclusion for critical operations

### 1.3 Swarm Consensus Integration

**Purpose:** Use `SwarmConsensus` for multi-agent automation decisions.

**Integration Pattern:**

```python
from thegent.orchestration.swarm_consensus import SwarmConsensus, SwarmVote


class ConsensusBasedAutomation:
    """Consensus-based automation coordination."""

    def __init__(self, task_id: str):
        self.consensus = SwarmConsensus(task_id, threshold=0.67)

    def vote_on_automation(self, agent_id: str, action: AutomationAction, signature: str):
        """Agent votes on automation action."""
        vote = {"action": action.to_dict(), "approve": True, "confidence": 0.85}
        self.consensus.record_vote(agent_id, vote, signature)

    def evaluate_consensus(self, total_agents: int) -> tuple[bool, AutomationAction | None]:
        """Evaluate if consensus reached."""
        reached, result = self.consensus.evaluate_consensus(total_agents)
        if reached and result:
            # Parse result back to AutomationAction
            action = AutomationAction.from_dict(result["action"])
            return True, action
        return False, None
```

**Use Cases:**

- Multi-agent approval for sensitive actions (screenshot, clipboard)
- Conflict resolution when agents disagree
- High-confidence automation decisions

---

## 2. Observability Integration

### 2.1 OpenTelemetry Integration

**Purpose:** Integrate desktop automation with existing OTel instrumentation.

**Integration Pattern:**

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("thegent.desktop_automation")


class ObservableDesktopAutomationProvider(DesktopAutomationProvider):
    """Desktop automation provider with OTel instrumentation."""

    def click(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click with OTel tracing."""
        with tracer.start_as_current_span("desktop_automation.click") as span:
            # Set span attributes
            span.set_attribute("automation.action", "click")
            span.set_attribute("automation.platform", platform.system().lower())
            span.set_attribute("automation.selector", element.selector)
            span.set_attribute("automation.element_name", element.name)
            span.set_attribute("automation.element_role", element.role)

            # Record start time
            start_time = time.time()

            try:
                # Execute automation
                result = self._provider.click(element, timeout_ms)
                duration_ms = (time.time() - start_time) * 1000

                # Set result attributes
                span.set_attribute("automation.success", result.success)
                span.set_attribute("automation.duration_ms", duration_ms)

                if result.success:
                    span.set_status(Status(StatusCode.OK))
                else:
                    span.set_status(Status(StatusCode.ERROR, result.error))
                    span.set_attribute("automation.error", result.error)

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("automation.error", str(e))
                span.set_attribute("automation.duration_ms", duration_ms)
                raise
```

**OTel Semantic Conventions:**

```python
# Map to OTel GenAI conventions
span.set_attribute("gen_ai.system", "desktop_automation")
span.set_attribute("gen_ai.request.model", "macos_applescript")  # or "windows_uia", "linux_atspi"
span.set_attribute("gen_ai.usage.total_tokens", 0)  # N/A for automation
span.set_attribute("gen_ai.usage.cost", automation_cost_usd)
span.set_attribute("thegent.lane", "standard")
span.set_attribute("thegent.agent_id", agent_id)
```

### 2.2 Metrics Integration

**Purpose:** Expose desktop automation metrics via Prometheus.

**Integration Pattern:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
automation_actions_total = Counter(
    "desktop_automation_actions_total", "Total automation actions", ["action_type", "platform", "success"]
)

automation_latency_seconds = Histogram(
    "desktop_automation_latency_seconds",
    "Automation action latency",
    ["action_type", "platform"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
)

automation_active_locks = Gauge("desktop_automation_active_locks", "Active automation locks", ["platform"])


class MetricsDesktopAutomationProvider(DesktopAutomationProvider):
    """Provider with Prometheus metrics."""

    def click(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click with metrics."""
        platform_name = platform.system().lower()
        start_time = time.time()

        try:
            result = self._provider.click(element, timeout_ms)
            duration = time.time() - start_time

            # Record metrics
            automation_actions_total.labels(
                action_type="click", platform=platform_name, success=str(result.success)
            ).inc()

            automation_latency_seconds.labels(action_type="click", platform=platform_name).observe(duration)

            return result

        except Exception as e:
            duration = time.time() - start_time
            automation_actions_total.labels(action_type="click", platform=platform_name, success="false").inc()
            automation_latency_seconds.labels(action_type="click", platform=platform_name).observe(duration)
            raise
```

### 2.3 Run Registry Integration

**Purpose:** Log automation events to `run_registry.jsonl`.

**Integration Pattern:**

```python
from thegent.execution import RunRegistry


class RegistryDesktopAutomationProvider(DesktopAutomationProvider):
    """Provider with run registry logging."""

    def __init__(self, run_registry: RunRegistry):
        self.run_registry = run_registry

    def click(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click with registry logging."""
        start_time = time.time()
        result = self._provider.click(element, timeout_ms)
        duration_ms = (time.time() - start_time) * 1000

        # Log to registry
        self.run_registry.register_automation_event(
            run_id=self.run_id,
            event="automation_action",
            action_type="click",
            element=element.to_dict(),
            result=result.to_dict(),
            duration_ms=duration_ms,
            platform=platform.system(),
            cost_usd=self._estimate_cost("click", duration_ms),
        )

        return result
```

**Registry Event Format:**

```json
{
  "event": "automation_action",
  "run_id": "run_abc123",
  "timestamp": "2026-02-16T12:00:00Z",
  "action_type": "click",
  "element": {
    "selector": "button[name='Save']",
    "name": "Save",
    "role": "button"
  },
  "result": {
    "success": true,
    "duration_ms": 95.2
  },
  "platform": "Darwin",
  "cost_usd": 0.0001,
  "trace_id": "abc123...",
  "span_id": "def456..."
}
```

---

## 3. State Persistence Integration

### 3.1 Checkpoint Integration

**Purpose:** Integrate automation state with `CheckpointRegistry`.

**Integration Pattern:**

```python
from thegent.execution import CheckpointRegistry


class CheckpointableAutomationWorkflow:
    """Automation workflow with checkpoint support."""

    def __init__(self, checkpoint_registry: CheckpointRegistry):
        self.checkpoint_registry = checkpoint_registry
        self.current_step = 0
        self.workflow_state: dict = {}

    def execute_step(self, step: AutomationStep) -> AutomationResult:
        """Execute step with checkpointing."""
        # Execute automation step
        result = step.execute()

        # Update workflow state
        self.workflow_state[f"step_{self.current_step}"] = {
            "step": step.to_dict(),
            "result": result.to_dict(),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.current_step += 1

        # Create checkpoint after each step
        checkpoint = self.checkpoint_registry.create_checkpoint(
            reason=f"Automation step {self.current_step} completed",
            dag_content=json.dumps(self.workflow_state),
            owner=self.agent_id,
        )

        return result

    def resume_from_checkpoint(self, checkpoint_id: str):
        """Resume workflow from checkpoint."""
        checkpoint = self.checkpoint_registry.get_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        # Restore workflow state
        self.workflow_state = json.loads(checkpoint["dag_content"])
        self.current_step = len(self.workflow_state)

        # Resume execution
        return self._resume_execution()
```

### 3.2 Continuity Packet Integration

**Purpose:** Use continuity packets for automation handoff.

**Integration Pattern:**

```python
@dataclass
class AutomationContinuityPacket:
    """Continuity packet for automation handoff."""

    continuity_packet_id: str
    run_id: str
    created_at_utc: str
    phase: str
    progress: float
    summary: str
    next_action: str
    automation_state: dict
    unresolved_risks: list[str]
    owner: str
    handoff_to: str | None = None


class ContinuityAutomationWorkflow:
    """Automation workflow with continuity packets."""

    def create_continuity_packet(self, run_id: str, handoff_to: str | None = None) -> AutomationContinuityPacket:
        """Create continuity packet for handoff."""
        packet = AutomationContinuityPacket(
            continuity_packet_id=f"cp_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            created_at_utc=datetime.now(UTC).isoformat(),
            phase=self.current_phase,
            progress=self.current_progress,
            summary=self._generate_summary(),
            next_action=self._get_next_action(),
            automation_state=self.workflow_state,
            unresolved_risks=self._identify_risks(),
            owner=self.current_owner,
            handoff_to=handoff_to,
        )

        # Store continuity packet
        self._store_continuity_packet(packet)

        return packet

    def resume_from_continuity_packet(self, packet_id: str):
        """Resume from continuity packet."""
        packet = self._load_continuity_packet(packet_id)

        # Restore state
        self.workflow_state = packet.automation_state
        self.current_phase = packet.phase
        self.current_progress = packet.progress
        self.current_owner = packet.handoff_to or packet.owner

        # Resume execution
        return self._resume_execution()
```

---

## 4. Testing Strategy Integration

### 4.1 Unit Testing Integration

**Purpose:** Use existing test infrastructure for automation tests.

**Integration Pattern:**

```python
import pytest
from unittest.mock import Mock, patch
from thegent.infra.desktop_automation.base import DesktopAutomationProvider
from thegent.infra.desktop_automation.macos import macOSAutomationProvider


@pytest.fixture
def mock_automation_provider():
    """Mock automation provider for unit tests."""
    provider = Mock(spec=DesktopAutomationProvider)
    provider.click.return_value = AutomationResult(success=True)
    provider.type_text.return_value = AutomationResult(success=True)
    provider.find_element.return_value = UIElement(
        selector="button[name='Save']",
        name="Save",
        role="button",
        bounds={"x": 100, "y": 200, "width": 80, "height": 30},
    )
    return provider


@pytest.mark.unit
def test_click_success(mock_automation_provider):
    """Test successful click."""
    element = mock_automation_provider.find_element("button[name='Save']")
    result = mock_automation_provider.click(element)

    assert result.success
    mock_automation_provider.click.assert_called_once_with(element)


@pytest.mark.unit
def test_element_not_found(mock_automation_provider):
    """Test element not found."""
    mock_automation_provider.find_element.return_value = None

    element = mock_automation_provider.find_element("nonexistent")
    assert element is None
```

### 4.2 Integration Testing Integration

**Purpose:** Use existing integration test patterns.

**Integration Pattern:**

```python
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific integration test")
@pytest.mark.requires_permissions
def test_macos_automation_integration():
    """Integration test for macOS automation."""
    provider = macOSAutomationProvider()

    # Open TextEdit
    subprocess.run(["open", "-a", "TextEdit"])
    time.sleep(2)

    # Find "New Document" button
    element = provider.find_element("New Document")
    assert element is not None

    # Click it
    result = provider.click(element)
    assert result.success

    # Cleanup
    subprocess.run(["pkill", "TextEdit"])
```

### 4.3 Chaos Testing Integration

**Purpose:** Use existing chaos testing patterns.

**Integration Pattern:**

```python
@pytest.mark.chaos
def test_automation_timeout_chaos(mock_automation_provider):
    """Chaos test: automation timeout."""
    # Mock timeout
    mock_automation_provider.click.side_effect = TimeoutError("Automation timeout")

    element = UIElement(selector="button", name="Test", role="button", bounds={})

    with pytest.raises(TimeoutError):
        mock_automation_provider.click(element, timeout_ms=1000)


@pytest.mark.chaos
def test_permission_denied_chaos():
    """Chaos test: permission denied."""
    provider = macOSAutomationProvider()

    # Mock permission check failure
    with patch.object(provider, "_check_permissions", return_value=False):
        element = UIElement(selector="button", name="Test", role="button", bounds={})
        result = provider.click(element)

        assert not result.success
        assert "permission" in result.error.lower()
```

### 4.4 Property-Based Testing Integration

**Purpose:** Use Hypothesis for property-based testing.

**Integration Pattern:**

```python
from hypothesis import given, strategies as st


@given(selector=st.text(min_size=1, max_size=100), timeout=st.floats(min_value=0.1, max_value=10.0))
def test_find_element_properties(selector: str, timeout: float):
    """Property-based test for element finding."""
    provider = get_provider()
    result = provider.find_element(selector, timeout_ms=timeout * 1000)

    # Properties:
    # - Result is either None or valid UIElement
    # - If result is not None, element.selector matches
    # - Timeout is respected
    assert result is None or isinstance(result, UIElement)
    if result:
        assert result.selector == selector or selector in result.name
```

---

## 5. Error Handling Integration

### 5.1 Resilience Integration

**Purpose:** Use existing retry/fallback patterns.

**Integration Pattern:**

```python
from thegent.agents.resilience import classify_failure, is_retryable, FailureKind, retry_with_backoff


class ResilientDesktopAutomationProvider(DesktopAutomationProvider):
    """Provider with retry/fallback integration."""

    @retry_with_backoff(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def click_with_retry(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click with automatic retry."""
        result = self.click(element, timeout_ms)

        if not result.success:
            # Classify failure
            failure_kind = classify_failure(result.error)

            if is_retryable(failure_kind):
                raise RetryableError(result.error)
            else:
                raise NonRetryableError(result.error)

        return result
```

### 5.2 Circuit Breaker Integration

**Purpose:** Use existing circuit breaker patterns.

**Integration Pattern:**

```python
from thegent.agents.resilience import ToolCircuitBreaker


class CircuitBreakerAutomationProvider(DesktopAutomationProvider):
    """Provider with circuit breaker."""

    def __init__(self):
        self.circuit_breaker = ToolCircuitBreaker(name="desktop_automation", threshold=5, window_s=300)

    def click(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click with circuit breaker."""
        if self.circuit_breaker.is_open():
            return AutomationResult(success=False, error="Circuit breaker is open")

        try:
            result = self._provider.click(element, timeout_ms)

            if result.success:
                self.circuit_breaker.record_success()
            else:
                self.circuit_breaker.record_failure()

            return result

        except Exception as e:
            self.circuit_breaker.record_failure()
            raise
```

---

## 6. Cost & Rate Limiting Integration

### 6.1 Cost Tracking Integration

**Purpose:** Integrate with existing cost tracking.

**Integration Pattern:**

```python
from thegent.governance.cost import CostAggregator, CostEstimator


class CostAwareAutomationProvider(DesktopAutomationProvider):
    """Provider with cost tracking."""

    def __init__(self, cost_aggregator: CostAggregator):
        self.cost_aggregator = cost_aggregator
        self.cost_estimator = CostEstimator()

    def click(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click with cost tracking."""
        start_time = time.time()
        result = self._provider.click(element, timeout_ms)
        duration_ms = (time.time() - start_time) * 1000

        # Estimate cost
        cost = self.cost_estimator.estimate_automation(
            action_type="click", duration_ms=duration_ms, success=result.success
        )

        # Track cost
        self.cost_aggregator.track_automation_cost(
            action_type="click", cost_usd=cost, duration_ms=duration_ms, success=result.success
        )

        return result
```

### 6.2 Rate Limiting Integration

**Purpose:** Integrate with existing rate limiting.

**Integration Pattern:**

```python
from thegent.agents.resilience import TokenBucket, get_token_bucket


class RateLimitedAutomationProvider(DesktopAutomationProvider):
    """Provider with rate limiting."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.token_bucket = TokenBucket(
            capacity=100,  # 100 actions per minute
            refill_per_sec=100.0 / 60.0,
            provider=f"automation_{agent_id}",
        )

    def click(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click with rate limiting."""
        # Acquire token
        if not self.token_bucket.acquire():
            return AutomationResult(success=False, error="Rate limit exceeded")

        # Execute automation
        return self._provider.click(element, timeout_ms)
```

---

## 7. Security Integration

### 7.1 Policy Engine Integration

**Purpose:** Integrate with existing policy engine.

**Integration Pattern:**

```python
from thegent.execution import PolicyEngine


class PolicyEnforcedAutomationProvider(DesktopAutomationProvider):
    """Provider with policy enforcement."""

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine

    def click(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click with policy check."""
        # Create run metadata
        run_meta = RunMeta(
            mode="desktop_automation",
            automation_action=AutomationAction(type="click", selector=element.selector),
            agent_id=self.agent_id,
        )

        # Check policy
        decision, reason = self.policy_engine.evaluate(run_meta)

        if decision == "deny":
            return AutomationResult(success=False, error=f"Policy denied: {reason}")

        # Execute automation
        return self._provider.click(element, timeout_ms)
```

---

## 8. Performance Integration

### 8.1 Concurrency Controller Integration

**Purpose:** Integrate with existing concurrency control.

**Integration Pattern:**

```python
from thegent.execution import ConcurrencyController


class ConcurrencyControlledAutomationProvider(DesktopAutomationProvider):
    """Provider with concurrency control."""

    def __init__(self, concurrency_controller: ConcurrencyController):
        self.concurrency_controller = concurrency_controller

    def execute_batch(self, actions: list[AutomationAction]) -> list[AutomationResult]:
        """Execute batch with concurrency control."""
        results = []

        for action in actions:
            # Acquire concurrency slot
            if not self.concurrency_controller.acquire(lane="standard", owner=self.agent_id):
                results.append(AutomationResult(success=False, error="Concurrency limit exceeded"))
                continue

            try:
                # Execute action
                result = self._execute_action(action)
                results.append(result)
            finally:
                # Release slot (if needed)
                pass  # ConcurrencyController manages slots automatically

        return results
```

---

## 9. Troubleshooting Guide

### 9.1 Common Issues

**Issue: Permission Denied**

- **Symptoms:** Automation fails with permission error
- **Diagnosis:** Check accessibility permissions
- **Solution:** Grant permissions via System Preferences (macOS) or Group Policy (Windows)

**Issue: Element Not Found**

- **Symptoms:** `find_element` returns None
- **Diagnosis:** Check selector, wait for element to load
- **Solution:** Use cached elements, add wait logic, try alternate selectors

**Issue: Rate Limit Exceeded**

- **Symptoms:** Automation fails with rate limit error
- **Diagnosis:** Check token bucket capacity
- **Solution:** Increase rate limit, reduce automation frequency

**Issue: Cost Budget Exceeded**

- **Symptoms:** Automation blocked due to budget
- **Diagnosis:** Check automation budget utilization
- **Solution:** Increase budget, optimize automation actions

### 9.2 Debugging Tools

**OTel Trace Viewer:**

- View automation traces in Jaeger/Tempo
- Filter by `automation.action`, `automation.platform`
- Analyze latency distributions

**Prometheus Metrics:**

- Query `desktop_automation_actions_total`
- Query `desktop_automation_latency_seconds`
- Set up Grafana dashboards

**Run Registry:**

- Query `run_registry.jsonl` for automation events
- Filter by `event=automation_action`
- Analyze success rates, error patterns

---

## 10. Migration Path

### 10.1 Phase 1: Basic Integration (Week 1-2)

- [ ] Integrate with EditLeaseManager
- [ ] Add OTel instrumentation
- [ ] Add Prometheus metrics
- [ ] Log to run registry

### 10.2 Phase 2: Advanced Integration (Week 3-4)

- [ ] Integrate with CheckpointRegistry
- [ ] Add continuity packet support
- [ ] Integrate with PolicyEngine
- [ ] Add cost tracking

### 10.3 Phase 3: Distributed Integration (Week 5-6)

- [ ] Add Redis-based coordination
- [ ] Integrate with SwarmConsensus
- [ ] Add distributed locking
- [ ] Add event-driven coordination

### 10.4 Phase 4: Testing Integration (Week 7-8)

- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add chaos tests
- [ ] Add property-based tests

---

**Status:** Integration guide complete. Ready for implementation.

---

## 11. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Worker Droid

### Changes Made

1. **Added Section 9:** Troubleshooting Guide
   - Common issues (Permission Denied, Element Not Found, Rate Limit Exceeded, Cost Budget Exceeded)
   - Diagnosis steps for each issue
   - Solutions and fixes
   - Debugging tools (OTel Trace Viewer, Prometheus Metrics, Run Registry)

2. **Added Section 10:** Migration Path
   - Phase 1: Basic Integration (EditLeaseManager, OTel, Prometheus, run registry)
   - Phase 2: Advanced Integration (CheckpointRegistry, continuity packets, PolicyEngine, cost tracking)
   - Phase 3: Distributed Integration (Redis coordination, SwarmConsensus, distributed locking, event-driven)
   - Phase 4: Testing Integration (unit tests, integration tests, chaos tests, property-based tests)

3. **Enhanced Section 2:** Observability Integration
   - OpenTelemetry instrumentation examples
   - OTel semantic conventions for automation
   - Prometheus metrics integration
   - Run registry event format

4. **Enhanced Section 3:** State Persistence Integration
   - Checkpoint integration for workflow recovery
   - Continuity packet implementation for handoff

5. **Enhanced Section 5:** Error Handling Integration
   - Resilience integration (retry/fallback)
   - Circuit breaker integration with ToolCircuitBreaker

6. **Enhanced Section 6:** Cost & Rate Limiting Integration
   - Cost tracking integration with CostAggregator
   - Rate limiting with TokenBucket

### Practical Examples Added

| Example                     | File                             | Purpose                                  |
| --------------------------- | -------------------------------- | ---------------------------------------- |
| OTel Tracing                | `otel_integration.py`            | Instrument automation with OpenTelemetry |
| Prometheus Metrics          | `metrics_integration.py`         | Expose automation metrics                |
| Run Registry Logging        | `registry_integration.py`        | Log automation events                    |
| Checkpoint Integration      | `checkpoint_integration.py`      | Workflow recovery with checkpoints       |
| Continuity Packet           | `continuity_integration.py`      | Agent handoff with continuity            |
| Resilience Integration      | `resilience_integration.py`      | Retry/fallback patterns                  |
| Circuit Breaker Integration | `circuit_breaker_integration.py` | Failure protection                       |
| Cost Tracking               | `cost_integration.py`            | Automation cost attribution              |
| Rate Limiting               | `rate_limit_integration.py`      | Token bucket rate limiting               |
| Policy Engine Integration   | `policy_integration.py`          | Policy enforcement                       |

### Cross-References Added

- Internal: `src/thegent/orchestration/leasing.py`, `src/thegent/execution.py:ConcurrencyController`
- External: OpenTelemetry Documentation, Prometheus Documentation

### Verification Checklist

- [x] Code examples are syntactically correct Python
- [x] All integration patterns follow existing conventions
- [x] Cross-references point to existing code
- [x] Migration path is actionable with clear phases

---

## See Also

- [CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md](./CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md) - Consolidated cross-platform guide
- [CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md](./CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md) - Main research document
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [research-cross-platform-desktop](../reference/WORK_STREAM.md#research-cross-platform-desktop) - Desktop automation BACKLOG item
