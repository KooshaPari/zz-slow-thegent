# Civilization-Scale Performance & Resource Orchestration

**Status**: Design v1.0
**Date**: 2026-02-19
**Scope**: Global resource management for 5-20 agents across multiple projects

---

## Overview

The civilization must manage finite compute resources (CPU, memory, network) fairly across 5-20 agents in multiple projects. This document describes:

- **Global resource model** (how much compute available?)
- **Per-project quotas** (how to divide among projects?)
- **Load balancing** (which agent should get this task?)
- **Backpressure** (when to reject tasks?)
- **Resource negotiation** (can Project A borrow from Project B?)

---

## Global Resource Model

### Resource Types

| Resource    | Unit            | Typical Limit     | Notes                                |
| ----------- | --------------- | ----------------- | ------------------------------------ |
| CPU         | percent (0-100) | 80-100%           | Share 1 CPU core across civilization |
| Memory      | MB/GB           | 8-16 GB total     | Per-agent quotas sum to total        |
| Network     | Mbps            | 10-100 Mbps       | Per-project bandwidth limits         |
| Disk I/O    | MB/s            | Unlimited (local) | Not constrained in this design       |
| Concurrency | tasks           | 5-20 parallel     | Max L2 agents × max tasks per L2     |

### Resource State

**Location**: `~/.claude/civilization/resource_state.json` (updated every 10s)

```json
{
  "timestamp": "2026-02-19T14:47:00Z",
  "civilization_id": "global-001",
  "total_resources": {
    "cpu_percent": 100,
    "memory_mb": 16384,
    "network_mbps": 100
  },
  "current_usage": {
    "cpu_percent": 45,
    "memory_mb": 6500,
    "network_mbps": 15
  },
  "available_resources": {
    "cpu_percent": 55,
    "memory_mb": 9884,
    "network_mbps": 85
  },
  "headroom": {
    "cpu_percent": 55,
    "memory_mb": 9884,
    "network_mbps": 85,
    "safety_margin_percent": 20
  },
  "projects": [
    {
      "name": "kush",
      "quota": {
        "cpu_percent": 40,
        "memory_mb": 8192,
        "network_mbps": 40
      },
      "usage": {
        "cpu_percent": 28,
        "memory_mb": 2300,
        "network_mbps": 10
      },
      "available": {
        "cpu_percent": 12,
        "memory_mb": 5892,
        "network_mbps": 30
      }
    },
    {
      "name": "atoms",
      "quota": {
        "cpu_percent": 35,
        "memory_mb": 6144,
        "network_mbps": 35
      },
      "usage": {
        "cpu_percent": 15,
        "memory_mb": 1800,
        "network_mbps": 5
      },
      "available": {
        "cpu_percent": 20,
        "memory_mb": 4344,
        "network_mbps": 30
      }
    },
    {
      "name": "thegent",
      "quota": {
        "cpu_percent": 25,
        "memory_mb": 2048,
        "network_mbps": 25
      },
      "usage": {
        "cpu_percent": 2,
        "memory_mb": 400,
        "network_mbps": 0
      },
      "available": {
        "cpu_percent": 23,
        "memory_mb": 1648,
        "network_mbps": 25
      }
    }
  ]
}
```

---

## Per-Project Quota Allocation

### Quota Setting Strategy

**Goal**: Fair distribution while respecting project importance/activity.

**Factors**:

- Civilization total resources (fixed)
- Number of projects (variable, 2-10)
- Project activity level (L1 agents per project)
- Historical usage patterns
- Project priority/SLA

### Quota Allocation Algorithm

**Option 1: Equal Share (Simplest)**

```
quota_per_project = total_resources / num_projects

Example (3 projects, 100 CPU):
  kush: 33%
  atoms: 33%
  thegent: 33%
```

**Pros**: Simple, fair
**Cons**: Doesn't account for activity, one idle project wastes quota

**Option 2: Usage-Based (Adaptive)**

```
historical_usage_per_project = average_last_7_days_usage
quota_per_project = (historical_usage / sum(historical_usage)) * total_resources

Example:
  kush: used 40% avg → quota 40%
  atoms: used 35% avg → quota 35%
  thegent: used 25% avg → quota 25%
```

**Pros**: Aligns quota with actual usage
**Cons**: Unused capacity if project slows down, takes time to converge

**Option 3: Priority-Based (Flexible)**

```
priority_per_project = {kush: 1.0 (high), atoms: 0.8 (medium), thegent: 0.6 (low)}
quota_per_project = (priority / sum(priorities)) * total_resources

Example:
  kush: priority 1.0 → quota 40%
  atoms: priority 0.8 → quota 32%
  thegent: priority 0.6 → quota 24%
  (1.0 + 0.8 + 0.6 = 2.4, each gets (priority/2.4)*100%)
```

**Pros**: Explicit control, reflects business priority
**Cons**: Requires manual tuning, rigid

### Recommended Approach: Hybrid (Options 2 + 3)

**Strategy**:

1. Start with equal share (safe baseline)
2. Monitor historical usage for 7 days
3. Shift to usage-based allocation (adapts automatically)
4. Apply priority multiplier if explicit priority set (e.g., production > staging)

```python
def allocate_quota(
    projects: list[str],
    total_resources: dict,
    historical_usage: dict[str, dict] = None,
    priorities: dict[str, float] = None,
) -> dict[str, dict]:
    """
    Allocate civilization resources to projects.
    """
    n_projects = len(projects)

    # Start with equal share
    equal_quota = {res: total / n_projects for res, total in total_resources.items()}

    # If we have historical usage, weight by it
    if historical_usage and len(historical_usage) == n_projects:
        total_usage = sum(historical_usage[p]["cpu"] for p in projects)
        if total_usage > 0:
            # Allocate based on historical usage
            return {
                project: {
                    "cpu_percent": (historical_usage[project]["cpu"] / total_usage) * 100,
                    "memory_mb": (
                        historical_usage[project]["memory"] / sum(u["memory"] for u in historical_usage.values())
                    )
                    * total_resources["memory_mb"],
                    "network_mbps": (
                        historical_usage[project]["network"] / sum(u["network"] for u in historical_usage.values())
                    )
                    * total_resources["network_mbps"],
                }
                for project in projects
            }

    # If we have priorities, adjust allocation
    if priorities:
        priority_sum = sum(priorities.values())
        return {
            project: {
                "cpu_percent": (priorities.get(project, 1.0) / priority_sum) * 100,
                "memory_mb": (priorities.get(project, 1.0) / priority_sum) * total_resources["memory_mb"],
                "network_mbps": (priorities.get(project, 1.0) / priority_sum) * total_resources["network_mbps"],
            }
            for project in projects
        }

    # Fallback: equal share
    return {project: equal_quota for project in projects}
```

---

## Load Balancing Strategies

### Strategy 1: Locality First (Recommended)

**Goal**: Prefer same-project agents (lower latency, no cross-project coordination).

```python
def select_agent_locality_first(task_id: str, required_capability: str, source_project: str) -> AgentEntry:
    """
    Select agent for task, preferring same project.
    """
    # Try same project first (low latency)
    candidates_same_project = registry.query(
        project=source_project, capability=required_capability, status="active", availability="idle_or_available"
    )

    if candidates_same_project:
        # Sort by load (least loaded first)
        sorted_candidates = sorted(candidates_same_project, key=lambda a: a["current_state"]["tasks_active"])
        return sorted_candidates[0]

    # Try other projects (higher latency, cross-project)
    candidates_other_projects = registry.query(
        capability=required_capability, status="active", availability="idle_or_available"
    )

    if candidates_other_projects:
        sorted_candidates = sorted(
            candidates_other_projects,
            key=lambda a: (
                a["project"] != source_project,  # Prefer same project
                a["current_state"]["tasks_active"],  # Then least loaded
            ),
        )
        return sorted_candidates[0]

    raise NoAvailableAgents(required_capability)
```

**Advantages**:

- Minimizes cross-project overhead (no network crossing)
- Agents stay focused on their project
- Easier to reason about (work stays local)

**Disadvantages**:

- May not use idle capacity in other projects
- Blocks task if no capacity in source project

### Strategy 2: Load Balancing (Fair Distribution)

**Goal**: Balance load evenly across all agents, regardless of project.

```python
def select_agent_load_balanced(task_id: str, required_capability: str) -> AgentEntry:
    """
    Select least-loaded agent globally.
    """
    candidates = registry.query(capability=required_capability, status="active", availability="idle_or_available")

    if not candidates:
        raise NoAvailableAgents(required_capability)

    # Sort by load (least loaded first)
    sorted_candidates = sorted(
        candidates,
        key=lambda a: (
            a["current_state"]["cpu_usage_percent"],
            a["current_state"]["memory_usage_mb"],
            a["current_state"]["tasks_active"],
        ),
    )

    return sorted_candidates[0]
```

**Advantages**:

- Maximizes utilization (no idle agents)
- Fair distribution of work
- Better for cross-project optimization

**Disadvantages**:

- Higher latency (cross-project communication)
- More complex coordination
- May create cascading failures

### Strategy 3: Hybrid (Recommended for Production)

**Goal**: Prefer locality, but spill over to other projects if overloaded.

```python
def select_agent_hybrid(
    task_id: str, required_capability: str, source_project: str, locality_threshold_percent: float = 80.0
) -> AgentEntry:
    """
    Prefer same-project agents unless overloaded.
    """
    # Check if same-project agents are overloaded
    same_project_usage = get_project_usage(source_project, "cpu_percent")

    # If same-project usage < threshold, use locality-first
    if same_project_usage < locality_threshold_percent:
        try:
            return select_agent_locality_first(task_id, required_capability, source_project)
        except NoAvailableAgents:
            pass  # Fall through to load-balanced

    # If same-project overloaded (>80%), use load-balanced
    return select_agent_load_balanced(task_id, required_capability)
```

**Parameters**:

- `locality_threshold_percent`: When to abandon locality preference (default: 80%)
- `capability`: Required agent capability
- `task_priority`: Higher priority tasks can use cross-project resources

---

## Backpressure Mechanisms

### Admission Control (Accept/Reject Decision)

**When to reject a task:**

```python
def can_allocate_task(task: Task, agent: AgentEntry) -> tuple[bool, str]:
    """
    Check if agent has capacity for task.
    Returns (can_allocate, reason).
    """
    project = agent["project"]
    resource_state = read_resource_state()

    # Check 1: Agent overloaded?
    if agent["current_state"]["tasks_active"] >= agent["resource_quota"]["max_concurrent_tasks"]:
        return False, f"Agent already running {agent['current_state']['tasks_active']} tasks"

    # Check 2: Project quota available?
    project_available = resource_state["projects"][project]["available"]
    required = task["resource_request"]

    if project_available["cpu_percent"] < required["cpu_percent"]:
        return False, f"Project {project} insufficient CPU: {project_available['cpu_percent']}% needed"

    if project_available["memory_mb"] < required["memory_mb"]:
        return False, f"Project {project} insufficient memory: {project_available['memory_mb']}MB needed"

    # Check 3: Civilization quota available?
    civilization_available = resource_state["available_resources"]
    if civilization_available["cpu_percent"] < required["cpu_percent"]:
        return False, f"Civilization insufficient CPU: {civilization_available['cpu_percent']}% needed"

    # All checks passed
    return True, "OK"
```

### Queueing Strategy

**If task rejected:**

```python
def dispatch_task_with_queueing(task: Task, agent_id: str) -> DispatchResult:
    """
    Try to dispatch task; if rejected, queue for later.
    """
    can_allocate, reason = can_allocate_task(task, registry.lookup(agent_id))

    if can_allocate:
        return dispatch_task(task, agent_id)
    else:
        # Queue task, set retry policy
        queue_task(
            task,
            {
                "queue_reason": reason,
                "queued_at": now(),
                "retry_after_minutes": 5,  # Check again in 5 min
                "max_queue_time_minutes": 60,  # Fail if queued >1 hour
            },
        )
        return DispatchResult(task_id=task.id, status="QUEUED", message=f"Task queued: {reason}. Will retry in 5 min.")
```

### Queue Draining (When resources become available)

```python
async def drain_queued_tasks():
    """
    Periodically check if queued tasks can now run.
    Runs every 30 seconds.
    """
    queued_tasks = read_task_queue()

    for task in queued_tasks:
        # Find best agent for this task
        try:
            agent = select_agent_hybrid(task["task_id"], task["required_capability"], task["source_project"])
        except NoAvailableAgents:
            continue  # Still no capacity, stay queued

        # Check if agent has capacity now
        can_allocate, _ = can_allocate_task(task, agent)
        if can_allocate:
            # Dispatch from queue
            try:
                dispatch_task(task, agent["id"])
                remove_from_queue(task["task_id"])
            except Exception:
                continue  # Dispatch failed, stay queued
```

---

## Resource Negotiation & Borrowing

### Cross-Project Resource Borrowing

**Scenario**: Project A overloaded, Project B idle. Can A borrow from B?

```python
def request_resource_borrow(
    borrower_project: str,
    resource_type: str,  # 'cpu', 'memory'
    amount: float,
    duration_minutes: int,
    urgency: str = "normal",  # 'low', 'normal', 'high'
) -> BorrowApproval:
    """
    Request to borrow resources from idle projects.
    """
    resource_state = read_resource_state()

    # Find idle projects with excess capacity
    idle_projects = []
    for project, data in resource_state["projects"].items():
        if project == borrower_project:
            continue  # Can't borrow from self

        available = data["available"][resource_type]
        usage_percent = (data["usage"][resource_type] / data["quota"][resource_type]) * 100

        if usage_percent < 50:  # Project is idle
            idle_projects.append({"project": project, "available": available, "usage_percent": usage_percent})

    if not idle_projects:
        raise NoIdleProjectsAvailable()

    # Sort by most idle first
    idle_projects.sort(key=lambda p: p["usage_percent"])
    lender_project = idle_projects[0]["project"]

    # Request approval from lender's L1
    approval = send_borrow_request(
        lender_project=lender_project,
        borrower_project=borrower_project,
        resource_type=resource_type,
        amount=amount,
        duration_minutes=duration_minutes,
        urgency=urgency,
    )

    if approval.status == "APPROVED":
        # Update quotas temporarily
        update_quota_borrowing(
            lender_project=lender_project,
            borrower_project=borrower_project,
            resource_type=resource_type,
            amount=amount,
            borrow_until=now() + timedelta(minutes=duration_minutes),
        )

    return approval
```

**Message Schema (Borrow Request)**:

```json
{
  "message_type": "resource_borrow_request",
  "metadata": {
    "message_id": "msg-borrow-001",
    "sender_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
    "receiver_id": "thegent:...:L1:claude-code",
    "timestamp": "2026-02-19T14:48:00Z"
  },
  "borrow_request": {
    "borrower_project": "kush",
    "lender_project": "thegent",
    "resource_type": "cpu",
    "amount_percent": 10,
    "duration_minutes": 30,
    "urgency": "high",
    "justification": "Task cluster blocked on cross-project dependency"
  }
}
```

**Approval (with Terms)**:

```json
{
  "message_type": "resource_borrow_response",
  "metadata": {
    "message_id": "msg-borrow-response-001",
    "sender_id": "thegent:...:L1:claude-code",
    "receiver_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
    "timestamp": "2026-02-19T14:48:05Z",
    "in_reply_to": "msg-borrow-001"
  },
  "status": "APPROVED",
  "terms": {
    "amount_approved_percent": 10,
    "duration_minutes": 30,
    "borrow_until": "2026-02-19T15:18:00Z",
    "conditions": [
      "Reclaim resources if thegent needs them",
      "Return resources on time or default"
    ]
  }
}
```

### Quota Reclamation (Lender cancels borrow)

```python
def reclaim_borrowed_resources(lender_project: str, borrower_project: str, resource_type: str) -> bool:
    """
    Lender reclaims borrowed resources (if lender needs them).
    Gives borrower 5 minutes notice.
    """
    # Send reclamation notice to borrower
    send_message(
        receiver_id=f"{borrower_project}:...:L1",
        message={
            "type": "resource_reclamation_notice",
            "lender_project": lender_project,
            "resource_type": resource_type,
            "reclaim_at": now() + timedelta(minutes=5),
            "message": f"Need to reclaim {resource_type} back",
        },
    )

    # Borrower must return resources within 5 minutes
    # If not, hard reclaim (kill tasks to free up)
    time.sleep(300)

    # Check if resources returned
    if not resources_returned(borrower_project, lender_project, resource_type):
        # Hard reclaim: kill borrower's lowest-priority tasks
        kill_lowest_priority_tasks(borrower_project, num_tasks=3)
        log_incident(
            type="RESOURCE_RECLAMATION_FORCED", lender_project=lender_project, borrower_project=borrower_project
        )
```

---

## Performance Optimization Techniques

### Caching & Memoization

**Goal**: Avoid redundant work across projects.

**Problem**: Two projects need same research (e.g., HTTP library comparison).

**Solution**: Shared cache in `~/.claude/civilization/cache/`

```python
class SharedResultCache:
    def __init__(self):
        self.cache_dir = Path("~/.claude/civilization/cache")

    def store(self, key: str, value: dict, projects: list[str]) -> str:
        """
        Store result in cache, accessible to projects.
        """
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, "w") as f:
            json.dump(
                {
                    "key": key,
                    "value": value,
                    "created_by": "agent-id",
                    "created_at": now(),
                    "accessible_to_projects": projects,
                    "ttl_hours": 24,
                },
                f,
            )
        return str(cache_file)

    def retrieve(self, key: str, project: str) -> dict:
        """
        Retrieve cached result if available to project.
        """
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            raise CacheMiss(key)

        data = json.load(open(cache_file))
        if project not in data["accessible_to_projects"]:
            raise CacheAccessDenied(project, key)

        # Check TTL
        created_at = datetime.fromisoformat(data["created_at"])
        if (now() - created_at) > timedelta(hours=data["ttl_hours"]):
            raise CacheExpired(key)

        return data["value"]
```

**Cache Locations**:

```
~/.claude/civilization/cache/
├── research-http-libs.json       (created by atoms:researcher)
├── api-design-patterns.json
└── performance-benchmarks.json
```

**Cross-Project Cache Hit Example**:

```
Task: "research HTTP libraries"
Requested by: kush:runner-1
  ├─ Check cache: research-http-libs
  ├─ Hit! (created 2 hours ago, still fresh)
  ├─ Verify: kush in accessible_to_projects? Yes
  └─ Return: atoms:researcher's output without re-doing work
       └─ Save 30 minutes of effort!
```

### Speculative Execution

**Goal**: Start next task before current task completes (pipelining).

**Example**:

```
L2 working on Task A
  ├─ Task A estimated 10 min remaining
  ├─ Task B (dependent on A) queued, estimate 15 min
  │
  ├─ Look ahead: Task A + Task B = 25 min total
  │  └─ If resources available, start Task B early (speculative)
  │
  └─ When Task A completes:
     ├─ Task B already 5 min in
     └─ Total time: 20 min (vs 25 min if sequential)
```

**Implementation**:

```python
def speculative_dispatch(current_task: Task, queue: list[Task]) -> bool:
    """
    Check if next task can start speculatively.
    """
    if not queue:
        return False

    next_task = queue[0]

    # Check dependencies
    if next_task["blocked_by"] and current_task["task_id"] in next_task["blocked_by"]:
        # Dependencies exist, can't start early
        return False

    # Check resources
    can_allocate, _ = can_allocate_task(next_task, agent)
    if not can_allocate:
        return False

    # Check if enough time to start before current ends
    time_to_start_speculation = 2  # 2 minutes to setup
    current_time_remaining = current_task["estimated_completion"] - now()
    if current_time_remaining < timedelta(minutes=time_to_start_speculation):
        return False  # Too late to speculate

    # Start Task B speculatively
    return dispatch_task(next_task, agent_id)
```

---

## Observability & Metrics

### Per-Agent Metrics

```python
class AgentMetrics:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.metrics_file = f"~/.claude/civilization/metrics/{agent_id}.json"

    def record_task_completion(self, task: Task, duration_minutes: float):
        """Record task completion metrics."""
        metrics = self.read_metrics()
        metrics["tasks_completed"] += 1
        metrics["total_duration_minutes"] += duration_minutes
        metrics["avg_duration_minutes"] = metrics["total_duration_minutes"] / metrics["tasks_completed"]
        self.write_metrics(metrics)

    def get_utilization(self) -> float:
        """Get CPU utilization for this agent."""
        # Read from agent's status
        agent_entry = registry.lookup(self.agent_id)
        return agent_entry["current_state"]["cpu_usage_percent"]

    def get_queue_depth(self) -> int:
        """Get number of pending tasks for this agent."""
        count = 0
        for task in read_work_stream():
            if task["assigned_to"] == self.agent_id and task["status"] in ["PENDING", "CLAIMED"]:
                count += 1
        return count
```

### Civilization-Wide Metrics Dashboard

**Location**: `~/.claude/civilization/metrics.json` (updated every 10s)

```json
{
  "timestamp": "2026-02-19T14:48:30Z",
  "summary": {
    "total_agents": 9,
    "agents_active": 7,
    "agents_idle": 2,
    "resource_utilization": {
      "cpu_percent": 45,
      "memory_percent": 52,
      "network_percent": 20
    }
  },
  "performance": {
    "tasks_completed_last_hour": 48,
    "tasks_failed_last_hour": 2,
    "avg_task_duration_minutes": 5.2,
    "p95_task_duration_minutes": 12.5,
    "queue_depth": 5,
    "max_wait_time_minutes": 8
  },
  "cross_project_metrics": {
    "requests_active": 1,
    "requests_completed_hour": 8,
    "avg_wait_time_minutes": 4.2,
    "success_rate_percent": 87.5
  },
  "health": {
    "deadlocks_detected": 0,
    "cascade_failures": 0,
    "resource_threshold_breaches": 1,
    "agent_failures": 0
  }
}
```

---

## Glossary

| Term               | Definition                                             |
| ------------------ | ------------------------------------------------------ |
| **Quota**          | Resource limit for a project (CPU %, memory, network)  |
| **Usage**          | Actual resource consumption by agents in project       |
| **Available**      | quota - usage = unused capacity                        |
| **Headroom**       | available - safety_margin = reclaimable                |
| **Locality**       | Preferring same-project agents (low latency)           |
| **Load Balancing** | Distributing work across agents evenly                 |
| **Backpressure**   | Rejecting tasks when overloaded                        |
| **Borrowing**      | Project A uses Project B's excess capacity temporarily |
| **Speculation**    | Starting next task before current task completes       |
| **Memoization**    | Caching results to avoid redundant work                |
