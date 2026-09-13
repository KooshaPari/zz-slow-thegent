# Multi-Tenant Agent Civilization Controller - Implementation Plan

**Status**: Implementation Roadmap v1.0
**Date**: 2026-02-19
**Timeline**: 6 weeks (phased deployment)
**Team**: 1-2 agents, 10-20 min per phase

---

## Executive Summary

This document outlines a phased approach to building the multi-tenant agent civilization framework, starting from zero and scaling incrementally to 5-20 agents across multiple projects.

**Key Philosophy**: Ship early, iterate fast, add features only when needed.

---

## Phase 1: Foundation (Week 1-2)

**Goal**: Single-project multi-agent coordination works.
**Scope**: Agents in same project can coordinate tasks.
**Agents**: 2-3 per project, 1 project (kush).

### Phase 1 Tasks

#### 1.1: Agent Identity Infrastructure (Day 1)

**Deliverable**: Agents have globally unique IDs.

```python
# Code: ~/.claude/civilization/agent_registry.py


class AgentIdentity:
    """Generate and persist agent identity."""

    def __init__(self, project: str, role: str, tier: str):
        self.project = project
        self.role = role
        self.tier = tier
        self.config_path = Path.home() / ".claude" / "civilization" / project / f"{role}.agent-id"

    def get_or_create_uuid(self) -> str:
        """Get existing UUID or create new one."""
        if self.config_path.exists():
            return self.config_path.read_text().strip()
        else:
            uuid = str(uuid4())
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(uuid)
            self.config_path.chmod(0o600)
            return uuid

    @property
    def agent_id(self) -> str:
        """Return canonical agent ID."""
        uuid = self.get_or_create_uuid()
        return f"{self.project}:{uuid}:L{self.tier}:{self.role}"
```

**Testing**:

```python
# test_agent_identity.py


def test_agent_id_format():
    identity = AgentIdentity("kush", "runner-1", "2")
    agent_id = identity.agent_id
    assert agent_id.startswith("kush:")
    assert "L2" in agent_id
    assert "runner-1" in agent_id


def test_agent_id_persistence():
    identity1 = AgentIdentity("kush", "runner-1", "2")
    uuid1 = identity1.get_or_create_uuid()

    identity2 = AgentIdentity("kush", "runner-1", "2")
    uuid2 = identity2.get_or_create_uuid()

    assert uuid1 == uuid2  # Same UUID on second call
```

**Effort**: 2 tool calls (code + test)

#### 1.2: File-Based Registry (Day 2-3)

**Deliverable**: Registry file exists, agents can register/lookup.

```python
# Code: ~/.claude/civilization/registry.py


class FileBasedRegistry:
    """File-based agent registry with git persistence."""

    def __init__(self, registry_path: str = None):
        self.registry_path = registry_path or str(Path.home() / ".claude" / "civilization" / "registry.json")
        self.cache = {}
        self.cache_ttl_seconds = 10

    def register_agent(self, agent_entry: dict) -> bool:
        """Register or update agent in registry."""
        registry = self._read_registry()
        agent_id = agent_entry["id"]

        # Find and update or append
        found = False
        for i, agent in enumerate(registry["agents"]):
            if agent["id"] == agent_id:
                registry["agents"][i] = agent_entry
                found = True
                break

        if not found:
            registry["agents"].append(agent_entry)

        self._write_registry(registry)
        self._git_commit(f"Register agent: {agent_id}")
        return True

    def lookup_agent(self, agent_id: str) -> dict:
        """Look up agent by ID."""
        registry = self._read_registry()
        for agent in registry["agents"]:
            if agent["id"] == agent_id:
                return agent
        raise AgentNotFound(agent_id)

    def list_agents(self, project: str = None, tier: str = None) -> list:
        """List agents matching criteria."""
        registry = self._read_registry()
        results = []
        for agent in registry["agents"]:
            if project and agent["project"] != project:
                continue
            if tier and agent["tier"] != tier:
                continue
            results.append(agent)
        return results

    def _read_registry(self) -> dict:
        """Read registry from disk."""
        if not Path(self.registry_path).exists():
            return self._create_empty_registry()
        with open(self.registry_path, "r") as f:
            return json.load(f)

    def _write_registry(self, registry: dict):
        """Write registry to disk."""
        Path(self.registry_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(registry, f, indent=2)

    def _create_empty_registry(self) -> dict:
        """Create empty registry structure."""
        return {
            "version": "1.0",
            "metadata": {"last_updated": now().isoformat(), "civilization_id": "global-001"},
            "agents": [],
            "projects": [],
        }

    def _git_commit(self, message: str):
        """Commit registry changes to git."""
        registry_dir = Path(self.registry_path).parent
        subprocess.run(["git", "add", self.registry_path], cwd=registry_dir)
        subprocess.run(["git", "commit", "-m", message], cwd=registry_dir)
```

**Testing**:

```python
def test_register_agent():
    registry = FileBasedRegistry()
    agent_entry = {"id": "kush:...:L1:claude-code", "project": "kush", "tier": "L1", "status": "active"}
    assert registry.register_agent(agent_entry)
    assert registry.lookup_agent(agent_entry["id"]) == agent_entry


def test_list_agents_by_project():
    registry = FileBasedRegistry()
    # Register 2 agents in kush, 1 in atoms
    # Query: list_agents(project='kush') → 2 results
```

**Effort**: 3 tool calls (core registry, CRUD operations, tests)

#### 1.3: Unified Work Stream (Day 3-4)

**Deliverable**: Global WORK_STREAM.md with task state machine.

```markdown
# Unified Work Stream

| Task ID | Description      | Status    | Assigned To | Blocked By | Scope |
| ------- | ---------------- | --------- | ----------- | ---------- | ----- |
| task-1  | research-http    | PENDING   | -           | -          | kush  |
| task-2  | implement-client | PENDING   | -           | task-1     | kush  |
| task-3  | test-suite       | COMPLETED | runner-1    | -          | kush  |
```

**Implementation**:

```python
# Code: ~/.claude/civilization/work_stream.py


class UnifiedWorkStream:
    """Manage global work stream with git persistence."""

    def __init__(self, work_stream_path: str = None):
        self.work_stream_path = work_stream_path or str(Path.home() / ".claude" / "civilization" / "WORK_STREAM.md")

    def add_task(self, task: dict) -> bool:
        """Add task to work stream."""
        tasks = self._read_tasks()
        task.setdefault("status", "PENDING")
        task.setdefault("assigned_to", None)
        task.setdefault("blocked_by", [])
        tasks.append(task)
        self._write_tasks(tasks)
        self._git_commit(f"Add task: {task['task_id']}")
        return True

    def claim_task(self, task_id: str, agent_id: str) -> bool:
        """Claim task for agent."""
        tasks = self._read_tasks()
        for task in tasks:
            if task["task_id"] == task_id:
                if task["status"] != "PENDING":
                    raise TaskAlreadyClaimed(task_id)
                task["status"] = "CLAIMED"
                task["assigned_to"] = agent_id
                self._write_tasks(tasks)
                self._git_commit(f"Claim task {task_id}: {agent_id}")
                return True
        raise TaskNotFound(task_id)

    def complete_task(self, task_id: str, output_location: str = None) -> bool:
        """Mark task as completed."""
        tasks = self._read_tasks()
        for task in tasks:
            if task["task_id"] == task_id:
                task["status"] = "COMPLETED"
                task["completed_at"] = now().isoformat()
                if output_location:
                    task["output_location"] = output_location
                self._write_tasks(tasks)
                self._git_commit(f"Complete task {task_id}")
                # Broadcast unblock event
                self._publish_event({"type": "task.completed", "task_id": task_id})
                return True
        raise TaskNotFound(task_id)

    def _read_tasks(self) -> list:
        """Read work stream from markdown."""
        # Simple markdown table parser
        if not Path(self.work_stream_path).exists():
            return []
        # TODO: Implement markdown table parsing
        pass

    def _write_tasks(self, tasks: list):
        """Write work stream to markdown."""
        # TODO: Implement markdown table generation
        pass

    def _git_commit(self, message: str):
        """Commit changes to git."""
        pass
```

**Effort**: 3 tool calls (core, markdown parsing, tests)

#### 1.4: Heartbeat Mechanism (Day 5)

**Deliverable**: Agents send periodic heartbeats.

```python
# Code: ~/.claude/civilization/heartbeat.py


class HeartbeatManager:
    """Manage agent heartbeats."""

    def __init__(self, agent_id: str, interval_seconds: int = 30):
        self.agent_id = agent_id
        self.interval_seconds = interval_seconds
        self.last_heartbeat = None
        self.registry = FileBasedRegistry()

    async def start_heartbeat_loop(self):
        """Send heartbeats periodically."""
        while True:
            self._send_heartbeat()
            await asyncio.sleep(self.interval_seconds)

    def _send_heartbeat(self):
        """Send single heartbeat."""
        agent_entry = self._get_current_state()
        self.registry.register_agent(agent_entry)
        self.last_heartbeat = now()
        logger.debug(f"Heartbeat sent: {self.agent_id}")

    def _get_current_state(self) -> dict:
        """Get agent's current state."""
        return {
            "id": self.agent_id,
            "last_heartbeat": now().isoformat(),
            "current_state": {
                "status": "active",
                "tasks_active": self._count_active_tasks(),
                "cpu_usage_percent": self._get_cpu_usage(),
                "memory_usage_mb": self._get_memory_usage(),
            },
        }
```

**Testing**:

```python
@pytest.mark.asyncio
async def test_heartbeat_loop():
    hb = HeartbeatManager("kush:...:L2:runner-1", interval_seconds=1)
    task = asyncio.create_task(hb.start_heartbeat_loop())

    await asyncio.sleep(2.5)  # Wait for 2+ heartbeats
    task.cancel()

    assert hb.last_heartbeat is not None
    assert (now() - hb.last_heartbeat).total_seconds() < 2
```

**Effort**: 2 tool calls (implementation, tests)

#### 1.5: Stale Agent Detection (Day 5)

**Deliverable**: Mark agents as stale if no heartbeat.

```python
def detect_stale_agents():
    """Mark agents as stale if heartbeat missed."""
    registry = FileBasedRegistry()
    all_agents = registry.list_agents()

    for agent in all_agents:
        last_hb = datetime.fromisoformat(agent["last_heartbeat"])
        heartbeat_interval = agent.get("heartbeat_interval_seconds", 30)
        grace_period = heartbeat_interval * 3

        if (now() - last_hb).total_seconds() > grace_period:
            agent["status"] = "stale"
            registry.register_agent(agent)
            logger.warning(f"Agent marked stale: {agent['id']}")
```

**Effort**: 1 tool call

### Phase 1 Deliverables

- [ ] Agent IDs: globally unique, immutable
- [ ] Registry: file-based, git-persisted
- [ ] Work stream: markdown format, claim/complete operations
- [ ] Heartbeats: agents ping every 30s, update registry
- [ ] Stale detection: agents marked inactive after 3 missed heartbeats

**Phase 1 Effort**: ~10-15 tool calls total

---

## Phase 2: Single-Project Multi-Agent (Week 2-3)

**Goal**: L1 can dispatch tasks to L2s in same project.
**Scope**: Task dispatch (sync + async), task execution, load monitoring.
**Agents**: 3 L2s per project, 1 project (kush).

### Phase 2 Tasks

#### 2.1: Task Dispatch (Sync Path) (Days 1-2)

**Deliverable**: L1 can dispatch task to L2 synchronously.

```python
# Code: ~/.claude/civilization/task_dispatch.py


class SyncTaskDispatcher:
    """Dispatch tasks synchronously (L1 → L2)."""

    def __init__(self):
        self.registry = FileBasedRegistry()

    async def dispatch_task(
        self, task_id: str, prompt: str, agent_id: str, timeout_seconds: float = 30.0
    ) -> DispatchResult:
        """Dispatch task to agent, wait for ACK."""
        agent = self.registry.lookup_agent(agent_id)
        mcp_endpoint = agent["endpoints"]["mcp"]

        # Connect to agent's MCP endpoint
        async with connect_mcp(mcp_endpoint, timeout=timeout_seconds) as client:
            # Send task dispatch message
            result = await client.call_tool(
                "task_dispatch", {"task_id": task_id, "prompt": prompt, "timeout_seconds": 600}
            )

            if result.success:
                return DispatchResult(task_id=task_id, status="CLAIMED", agent_id=agent_id)
            else:
                raise DispatchFailed(result.error)
```

**MCP Tool** (exposed by L2 agents):

```python
@mcp.tool()
async def task_dispatch(task_id: str, prompt: str, timeout_seconds: int):
    """
    Accept task dispatch from L1.
    Returns success or rejection.
    """
    # Check capacity
    if agent.current_load >= agent.max_concurrent_tasks:
        return {"success": False, "error": "OVERLOADED"}

    # Reserve resources
    agent.claim_task(task_id)

    # Begin work asynchronously
    asyncio.create_task(agent.execute_task(task_id, prompt))

    return {"success": True, "status": "CLAIMED"}
```

**Effort**: 2-3 tool calls

#### 2.2: Task Dispatch (Async Path) (Day 2)

**Deliverable**: L1 can queue task for L2.

```python
class AsyncTaskDispatcher:
    """Dispatch tasks asynchronously via message queue."""

    def dispatch_task_async(self, task_id: str, prompt: str, agent_id: str):
        """Queue task for agent."""
        queue_path = self._get_queue_path(agent_id)
        queue_entry = {"task_id": task_id, "prompt": prompt, "queued_at": now().isoformat()}
        self._append_to_queue(queue_path, queue_entry)
```

**Effort**: 1-2 tool calls

#### 2.3: L2 Task Executor (Days 3-4)

**Deliverable**: L2 executes task, updates work stream.

```python
class L2TaskExecutor:
    """Execute assigned tasks."""

    async def execute_task(self, task_id: str, prompt: str):
        """Execute task to completion."""
        work_stream = UnifiedWorkStream()

        try:
            # Claim task
            work_stream.claim_task(task_id, self.agent_id)

            # Run task (call LLM or external service)
            output = await self._run_task_prompt(prompt)

            # Store output
            output_path = self._store_output(task_id, output)

            # Mark complete
            work_stream.complete_task(task_id, output_location=output_path)

            logger.info(f"Task {task_id} completed: {output_path}")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            work_stream.fail_task(task_id, error=str(e))
```

**Effort**: 2-3 tool calls

#### 2.4: Load Monitoring & Admission Control (Days 4-5)

**Deliverable**: Agents reject tasks if overloaded.

```python
class ResourceManager:
    """Monitor resources, admit/reject tasks."""

    def can_allocate_task(self, task: dict, agent_id: str) -> tuple[bool, str]:
        """Check if agent can accept task."""
        agent = self.registry.lookup_agent(agent_id)

        # Check 1: Concurrent task limit
        if agent["current_state"]["tasks_active"] >= agent["resource_quota"]["max_concurrent_tasks"]:
            return False, "Agent already at max concurrent tasks"

        # Check 2: CPU headroom
        cpu_available = 100 - agent["current_state"]["cpu_usage_percent"]
        if cpu_available < task["resource_request"]["cpu_percent"]:
            return False, "Insufficient CPU headroom"

        return True, "OK"
```

**Effort**: 1-2 tool calls

### Phase 2 Deliverables

- [ ] Sync dispatch: L1 → L2 with ACK
- [ ] Async dispatch: L1 → L2 via queue
- [ ] Task execution: L2 runs task, stores output
- [ ] Load monitoring: resource usage tracking
- [ ] Admission control: reject if overloaded

**Phase 2 Effort**: ~8-12 tool calls total

---

## Phase 3: Cross-Project Coordination (Week 3-4)

**Goal**: Agents in different projects can request work from each other.
**Scope**: Cross-project requests, shared WORK_STREAM, global resource tracking.
**Agents**: 3 per project, 2 projects (kush + atoms).

### Phase 3 Tasks

#### 3.1: Global Work Stream (Days 1-2)

**Deliverable**: Single WORK_STREAM.md visible to all projects.

**Change**: Move WORK_STREAM to `~/.claude/civilization/WORK_STREAM.md`

**Effort**: 1-2 tool calls

#### 3.2: Cross-Project Requests (Days 2-3)

**Deliverable**: L2 in kush can request work from L2 in atoms.

```python
class CrossProjectRequester:
    """Request work from agents in other projects."""

    async def request_help(
        self,
        description: str,
        required_capability: str,
        target_project: str,
        deadline: datetime,
        estimated_effort_minutes: int,
    ) -> RequestApproval:
        """Request help from another project."""
        # Find agent in target_project
        candidates = self.registry.list_agents(project=target_project, capability=required_capability)

        if not candidates:
            raise NoAvailableAgents(required_capability)

        target_agent = candidates[0]  # Prefer first available

        # Send request
        request = {
            "request_id": f"{target_project}:request-{uuid4()}",
            "source_agent": self.agent_id,
            "target_agent": target_agent["id"],
            "description": description,
            "deadline": deadline.isoformat(),
            "estimated_effort_minutes": estimated_effort_minutes,
        }

        return await self._send_request(target_agent, request)
```

**Effort**: 2-3 tool calls

#### 3.3: Global Resource State (Day 4)

**Deliverable**: Track resource usage across civilization.

```python
class GlobalResourceManager:
    """Track resource state across all projects."""

    def update_resource_state(self):
        """Update global resource state file."""
        state = {
            "timestamp": now().isoformat(),
            "total_resources": {"cpu_percent": 100, "memory_mb": 16384},
            "current_usage": self._aggregate_usage(),
            "projects": [
                {
                    "name": "kush",
                    "quota": {"cpu_percent": 40, "memory_mb": 8192},
                    "usage": {"cpu_percent": 28, "memory_mb": 2300},
                },
                # ... other projects
            ],
        }
        write_json("~/.claude/civilization/resource_state.json", state)
```

**Effort**: 1-2 tool calls

#### 3.4: Event Bus (Day 5)

**Deliverable**: Global events published when tasks complete.

```python
class EventBus:
    """Publish/subscribe for civilization events."""

    def publish(self, event: dict):
        """Publish event to all agents."""
        event["timestamp"] = now().isoformat()
        # Append to event log
        with open("~/.claude/civilization/event_log.ndjson", "a") as f:
            f.write(json.dumps(event) + "\n")

    def subscribe(self, topic: str) -> AsyncIterator[dict]:
        """Subscribe to events (async generator)."""
        # Implementation: tail event log, filter by topic
        pass
```

**Effort**: 2-3 tool calls

### Phase 3 Deliverables

- [ ] Global work stream (centralized WORK_STREAM.md)
- [ ] Cross-project requests (agent-to-agent)
- [ ] Global resource state (centralized tracking)
- [ ] Event bus (pub-sub for task completion)

**Phase 3 Effort**: ~7-10 tool calls total

---

## Phase 4: Observability & Governance (Week 4-5)

**Goal**: Full visibility into civilization state.
**Scope**: Metrics dashboard, deadlock detection, audit logging.

### Phase 4 Tasks

#### 4.1: Metrics Dashboard (Days 1-2)

**Deliverable**: Civilization status visible at a glance.

```python
class MetricsDashboard:
    """Generate civilization metrics."""

    def compute_metrics(self) -> dict:
        """Compute civilization-wide metrics."""
        agents = self.registry.list_agents()
        work_stream = UnifiedWorkStream()

        return {
            "timestamp": now().isoformat(),
            "summary": {
                "total_agents": len(agents),
                "agents_active": len([a for a in agents if a["status"] == "active"]),
                "resource_utilization": self._compute_resource_utilization(agents),
            },
            "performance": {
                "tasks_completed_last_hour": work_stream.count_completed_last_hour(),
                "avg_task_duration": work_stream.avg_duration_minutes(),
                "queue_depth": work_stream.count_pending(),
            },
        }
```

**Effort**: 2 tool calls

#### 4.2: Deadlock Detection (Days 3-4)

**Deliverable**: Detect and alert on deadlock cycles.

```python
class DeadlockDetector:
    """Detect cyclic task dependencies."""

    def detect_deadlock(self) -> list[list]:
        """Find all cycles in task dependency graph."""
        work_stream = UnifiedWorkStream()
        tasks = work_stream.read_tasks()

        # Build dependency graph
        graph = {t["task_id"]: t.get("blocked_by", []) for t in tasks}

        # Find cycles
        cycles = find_cycles(graph)
        if cycles:
            for cycle in cycles:
                self._publish_deadlock_alert(cycle)

        return cycles
```

**Effort**: 2-3 tool calls

#### 4.3: Audit Logging (Day 5)

**Deliverable**: Log all agent actions.

```python
class AuditLogger:
    """Log all agent actions for audit trail."""

    def log(self, event: str, agent_id: str, **details):
        """Log event to audit trail."""
        entry = {"timestamp": now().isoformat(), "event": event, "agent_id": agent_id, **details}
        with open("~/.claude/civilization/audit.log", "a") as f:
            f.write(json.dumps(entry) + "\n")
```

**Effort**: 1 tool call

### Phase 4 Deliverables

- [ ] Metrics dashboard (civilization status)
- [ ] Deadlock detection (alert on cycles)
- [ ] Audit logging (event trail)

**Phase 4 Effort**: ~5-7 tool calls total

---

## Phase 5: Resilience & Optimization (Week 5-6)

**Goal**: Handle failures gracefully, optimize performance.
**Scope**: Circuit breaker, resource borrowing, load balancing.

### Phase 5 Tasks

#### 5.1: Agent Failure Recovery (Days 1-2)

**Deliverable**: Recover gracefully when agent dies.

```python
class FailureRecovery:
    """Handle agent failures."""

    def detect_agent_failure(self, agent_id: str):
        """Detect agent heartbeat timeout."""
        agent = self.registry.lookup_agent(agent_id)
        last_hb = datetime.fromisoformat(agent["last_heartbeat"])

        if (now() - last_hb).total_seconds() > 180:  # 3 minutes
            self._handle_failure(agent_id)

    def _handle_failure(self, agent_id: str):
        """Handle agent failure: reassign tasks."""
        # Find tasks assigned to dead agent
        work_stream = UnifiedWorkStream()
        tasks = work_stream.get_tasks_for_agent(agent_id)

        for task in tasks:
            if task["status"] in ["CLAIMED", "IN_PROGRESS"]:
                # Reassign to alternative agent
                new_agent = self._find_alternative_agent(task["required_capability"])
                if new_agent:
                    work_stream.reassign_task(task["task_id"], new_agent["id"])
                else:
                    work_stream.requeue_task(task["task_id"])
```

**Effort**: 2-3 tool calls

#### 5.2: Load Balancing Algorithm (Days 3-4)

**Deliverable**: Smart agent selection (locality + balance).

```python
class SmartLoadBalancer:
    """Select best agent for task."""

    def select_agent(self, task: dict, source_project: str) -> str:
        """Select agent (prefer locality, balance load)."""
        candidates = self.registry.list_agents(capability=task["required_capability"], status="active")

        # Separate by project
        same_project = [a for a in candidates if a["project"] == source_project]
        other_project = [a for a in candidates if a["project"] != source_project]

        # Check if same-project overloaded
        same_project_load = (
            sum(a["current_state"]["cpu_usage_percent"] for a in same_project) / len(same_project)
            if same_project
            else 100
        )

        # Use locality if not overloaded
        if same_project_load < 80 and same_project:
            # Sort by load
            same_project.sort(key=lambda a: a["current_state"]["cpu_usage_percent"])
            return same_project[0]["id"]

        # Fall back to global load balance
        all_candidates = same_project + other_project
        all_candidates.sort(key=lambda a: a["current_state"]["cpu_usage_percent"])
        return all_candidates[0]["id"]
```

**Effort**: 2 tool calls

#### 5.3: Resource Borrowing (Day 5)

**Deliverable**: Project can borrow resources from idle projects.

```python
class ResourceBorrower:
    """Manage cross-project resource borrowing."""

    async def request_borrow(
        self, borrower_project: str, resource_type: str, amount: float, duration_minutes: int
    ) -> BorrowApproval:
        """Request to borrow resources."""
        # Find idle projects
        idle_projects = self._find_idle_projects(amount=amount)

        if not idle_projects:
            raise NoIdleProjectsAvailable()

        lender_project = idle_projects[0]

        # Send borrow request to lender's L1
        approval = await self._request_approval(
            lender_project=lender_project,
            borrower_project=borrower_project,
            amount=amount,
            duration_minutes=duration_minutes,
        )

        if approval.approved:
            # Update quotas
            self._update_quota_borrow(borrower_project, lender_project, amount, duration_minutes)

        return approval
```

**Effort**: 2-3 tool calls

### Phase 5 Deliverables

- [ ] Agent failure detection & recovery
- [ ] Smart load balancing (locality + balance)
- [ ] Resource borrowing (quota negotiation)

**Phase 5 Effort**: ~6-9 tool calls total

---

## Deployment Strategy

### Prerequisites

- Git repository for `~/.claude/civilization/` (shared home)
- MCP infrastructure (existing in thegent)
- Process orchestrator (existing: process-compose or make)

### Deployment Checklist

**Per Phase**:

- [ ] Code written & tested
- [ ] Integrated into L1/L2 agents
- [ ] Tested with 2-3 agents
- [ ] Committed to git with clear commit messages
- [ ] Documentation updated
- [ ] Monitoring added (logs, metrics)

**Before Scaling**:

- [ ] All phases 1-4 complete
- [ ] > 100 tasks run successfully
- [ ] <1% task failure rate
- [ ] Deadlock detector tested with synthetic deadlocks
- [ ] Resource management tested with >90% load

### Gradual Rollout

1. **Week 1-2** (Phase 1-2): Single project (kush), 2-3 agents
2. **Week 3-4** (Phase 3-4): Two projects (kush + atoms), cross-project requests
3. **Week 5-6** (Phase 5): Full resilience, optimize performance
4. **Week 6+**: Scale to 5-20 agents across multiple projects

---

## Key Decision Points

### 1. Consistency Model

**Decision**: Eventual consistency (git-based)
**Rationale**: Decentralized, works offline, simple
**Alternative**: Strong consistency (central backend)
**Cost**: ~30-min propagation delay vs ~100ms latency

### 2. MCP vs File-Based Communication

**Decision**: Hybrid (MCP primary, file-based fallback)
**Rationale**: Real-time when available, reliable when not
**Alternative**: Pure MCP (faster)
**Cost**: More code, more edge cases to handle

### 3. Resource Enforcement

**Decision**: Soft limits (warn, queue, don't kill)
**Rationale**: Fair scheduling, no task loss
**Alternative**: Hard limits (kill lowest-priority tasks)
**Cost**: May exceed resource quota temporarily

### 4. Fault Tolerance

**Decision**: Fail fast, reassign tasks
**Rationale**: Detect failures quickly, recover automatically
**Alternative**: Retry with backoff
**Cost**: May reassign tasks unnecessarily

---

## Rollback Strategy

If a phase introduces breaking changes:

1. **Rollback to Phase N-1**: Revert git commits, restart agents
2. **Preserve State**: Work stream remains in git (safe)
3. **Manual Recovery**: If agents left in bad state, manually fix WORK_STREAM.md

**Example**:

```bash
# Rollback Phase 3 (cross-project) to Phase 2 (single-project)
git checkout phase-2-stable -- ~/.claude/civilization/

# Restart agents
pkill -f "L1\|L2"
# Agents restart with Phase 2 code
```

---

## Testing Strategy

### Unit Tests (Per Phase)

Each phase includes unit tests for:

- Agent identity (format, persistence)
- Registry (CRUD operations)
- Work stream (claim, complete, fail)
- Dispatch (sync, async, failure modes)

### Integration Tests

After each phase:

- 2-3 agents execute 10+ tasks
- Tasks complete successfully
- Registry reflects final state
- Work stream updated

### Chaos Tests (Phase 5)

Before scaling:

- Kill agent mid-task (verify task reassigned)
- Network partition (verify fallback to file-based)
- Resource exhaustion (verify backpressure works)
- Deadlock cycle (verify detection + alert)

---

## Success Metrics

| Metric                     | Phase 1 | Phase 2 | Phase 3      | Phase 4   | Phase 5                |
| -------------------------- | ------- | ------- | ------------ | --------- | ---------------------- |
| **Task Success Rate**      | 95%     | 98%     | 98%          | 99%       | 99%+                   |
| **Avg Task Duration**      | <10min  | <10min  | <15min       | <15min    | <15min                 |
| **Agent Failure Recovery** | Manual  | Manual  | Automatic    | Automatic | <2min                  |
| **Deadlock Detection**     | N/A     | N/A     | Manual alert | Automatic | Automatic + resolution |
| **Resource Utilization**   | N/A     | N/A     | N/A          | 60%+      | 75%+                   |
| **Cross-Project Requests** | N/A     | N/A     | 80%+ success | 90%+      | 95%+                   |

---

## Timeline Summary

| Week | Phase          | Focus                          | Agents | Projects |
| ---- | -------------- | ------------------------------ | ------ | -------- |
| 1    | Foundation     | Identity, registry, heartbeat  | 2-3    | 1        |
| 2    | Single-Project | Task dispatch, execution       | 3 L2s  | 1        |
| 3    | Cross-Project  | Requests, global state, events | 3 L2s  | 2        |
| 4    | Observability  | Metrics, deadlock, audit       | 3 L2s  | 2        |
| 5    | Resilience     | Failure recovery, load balance | 5-10   | 3+       |
| 6    | Optimization   | Resource borrowing, caching    | 10-20  | 5-10     |

**Total Effort**: 40-60 tool calls
**Timeline**: 6 weeks (phased)
**Team**: 1-2 agents, 10-20 min per phase

---

## Open Questions for Review

1. **File-based vs Centralized**: Is eventual consistency acceptable, or do we need strong consistency?
2. **MCP Dependency**: How much can we rely on MCP being available? Is file-based fallback enough?
3. **Resource Limits**: Should we enforce hard limits (kill tasks) or soft limits (queue)?
4. **Cross-Project Visibility**: Can agents in Project A read outputs from Project B? Any security concerns?
5. **Scaling Beyond 20**: What's the breaking point? When do we need a dedicated service?
