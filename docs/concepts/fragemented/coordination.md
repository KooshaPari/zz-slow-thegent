# Cross-Project Coordination Patterns

**Status**: Design v1.0
**Date**: 2026-02-19
**Scope**: Communication protocols for L1→L2, L2↔L2, L2→L1, and civilization-wide events

---

## Overview

This document defines 5 core communication patterns that enable agents across projects to coordinate work, share resources, and handle failures gracefully.

---

## Pattern 1: Task Dispatch (L1 → L2/L3)

**Scenario**: L1 agent wants to assign work to an L2 agent.

**Characteristics**:

- Synchronous or asynchronous (sender's choice)
- Parent-child relationship (L1 supervises L2)
- Clearly defined task boundary
- Timeout & escalation path

### Synchronous Dispatch (Real-Time)

**Flow**:

```
L1 (kush:claude-code)
  ├─ Resolves L2 endpoint: kush:runner-1
  ├─ Opens MCP connection
  ├─ Sends TaskDispatchMessage
  └─ Waits for ACK (timeout: 5s)
       │
     L2 (kush:runner-1)
       ├─ Receives message
       ├─ Checks resource availability
       ├─ Sends ACK (task claimed)
       └─ Begins work
       │
     L1 (kush:claude-code)
       ├─ Receives ACK
       └─ Records: task CLAIMED by runner-1
```

**Message Schema**:

```json
{
  "message_type": "task_dispatch",
  "version": "1.0",
  "metadata": {
    "message_id": "msg-8f7e6d5c4b3a-001",
    "sender_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
    "receiver_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
    "timestamp": "2026-02-19T14:40:00Z",
    "trace_id": "trace-abc123"
  },
  "task": {
    "task_id": "research-http-library",
    "title": "Research HTTP libraries for Python",
    "description": "Compare httpx, requests, aiohttp. Recommend for project kush.",
    "scope": ["kush"],
    "deadline": "2026-02-19T16:00:00Z",
    "priority": 3,
    "estimated_effort_minutes": 30
  },
  "context": {
    "project": "kush",
    "blocking_tasks": [],
    "blocked_by_tasks": [],
    "dependencies": {
      "code_files": ["/kush/src/http_client.py"],
      "prior_research": ["docs/research/async_patterns.md"]
    }
  },
  "resource_request": {
    "cpu_percent": 20,
    "memory_mb": 512,
    "disk_mb": 100
  },
  "retry_policy": {
    "max_retries": 3,
    "backoff_strategy": "exponential",
    "backoff_base_seconds": 5
  },
  "timeout_seconds": 600
}
```

**Response (ACK)**:

```json
{
  "message_type": "task_dispatch_ack",
  "metadata": {
    "message_id": "msg-a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d-001",
    "sender_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
    "receiver_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
    "timestamp": "2026-02-19T14:40:02Z",
    "in_reply_to": "msg-8f7e6d5c4b3a-001"
  },
  "status": "CLAIMED",
  "task_id": "research-http-library",
  "start_time": "2026-02-19T14:40:02Z",
  "estimated_completion": "2026-02-19T14:55:00Z",
  "assigned_resources": {
    "cpu_percent": 20,
    "memory_mb": 512
  }
}
```

**Negative Response (Overloaded)**:

```json
{
  "message_type": "task_dispatch_nack",
  "metadata": {
    "message_id": "msg-a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d-002",
    "sender_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
    "receiver_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
    "timestamp": "2026-02-19T14:40:03Z",
    "in_reply_to": "msg-8f7e6d5c4b3a-001"
  },
  "status": "REJECTED",
  "task_id": "research-http-library",
  "reason": "AGENT_OVERLOADED",
  "details": {
    "current_load": {
      "tasks_active": 2,
      "max_concurrent": 2,
      "cpu_usage_percent": 85,
      "memory_usage_mb": 2800
    },
    "retry_after_seconds": 30,
    "suggested_agents": [
      "kush:f9e8d7c6-b5a4-3c2b-1a09-8f7e6d5c4b3a:L2:researcher-1"
    ]
  }
}
```

### Asynchronous Dispatch (Queue-Based)

**Flow**:

```
L1 (kush:claude-code)
  ├─ Writes task to WORK_STREAM.md
  ├─ Writes message to queue: ~/.claude/civilization/queues/runner-1.mq
  └─ Returns (non-blocking)
       │
     L2 (kush:runner-1)
       ├─ Polls queue every 1s
       ├─ Finds new message
       ├─ Updates WORK_STREAM.md (claims task)
       ├─ git push
       └─ Begins work
       │
     L1 (kush:claude-code)
       ├─ Periodically reads WORK_STREAM.md
       ├─ Observes: task CLAIMED by runner-1
       └─ Continues own work
```

**Message Format (Queue Entry)**:

```json
{
  "message_id": "msg-8f7e6d5c4b3a-001",
  "timestamp": "2026-02-19T14:40:00Z",
  "sender_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
  "task": {
    "task_id": "research-http-library",
    "prompt": "Research HTTP libraries..."
  }
}
```

**Queue File Location**:

```
~/.claude/civilization/queues/
├── kush:runner-1.mq          (queue for runner-1)
├── kush:researcher-1.mq
└── atoms:cursor-01.mq
```

### Comparison: Sync vs Async

| Aspect          | Synchronous                             | Asynchronous                          |
| --------------- | --------------------------------------- | ------------------------------------- |
| **Latency**     | <1s (real-time)                         | 1-5s (poll-based)                     |
| **Reliability** | High (knows immediately if failed)      | High (queue persists)                 |
| **Load**        | Can reject if overloaded (backpressure) | Can be queued (fairness)              |
| **Use Case**    | Urgent tasks, real-time response        | Bulk dispatch, low latency acceptable |
| **Fallback**    | Switch to async if sync fails           | N/A                                   |

---

## Pattern 2: Cross-Project Request (L2 ↔ L2)

**Scenario**: L2 in Project A needs work done in Project B, but doesn't want to escalate to L1.

**Characteristics**:

- Peer-to-peer (not hierarchical)
- Cross-project (different git homes)
- Negotiation-based (responder can accept/defer)
- Shared deadline

### Request-Response Flow

```
L2-A (kush:runner-1) needs research from atoms project
  ├─ Looks up available L2 researchers in atoms
  │  └─ Registry query: agents(project="atoms", tier="L2", capability="research")
  │     Result: [atoms:researcher-1 (idle)]
  │
  ├─ Sends CrossProjectRequestMessage to atoms:researcher-1
  │  ├─ Via: MCP message (primary) or message queue (fallback)
  │  └─ Content: description, deadline, incentives
  │
  └─ Waits for response (timeout: 30s)
       │
     L2-B (atoms:researcher-1)
       ├─ Receives request
       ├─ Evaluates:
       │  ├─ Capacity? (1/2 slots, yes)
       │  ├─ Specialization? (researcher, yes)
       │  ├─ Timeline? (2 hours, reasonable)
       │  └─ Cross-project credit? (yes, good)
       │
       └─ Sends response: ACCEPTED + start_time
            │
          L2-A (kush:runner-1)
            ├─ Receives: ACCEPTED
            ├─ Creates task in WORK_STREAM.md:
            │  {
            │    task_id: "atoms:research-http-async",
            │    assigned_to: "atoms:researcher-1",
            │    scope: ["kush", "atoms"],
            │    blocking: ["kush:runner-1"]
            │  }
            │
            ├─ git push (makes it official)
            ├─ Event broadcast: "cross_project_task_started"
            │  └─ All agents in both projects notified
            │
            └─ Waits for completion
                 │
               L2-B (atoms:researcher-1)
                 ├─ Works on task
                 ├─ Periodically updates WORK_STREAM.md
                 │  └─ status: IN_PROGRESS, progress_percent: 65%
                 │
                 └─ On completion:
                    ├─ Writes output to atoms project
                    ├─ Updates WORK_STREAM.md: status=COMPLETED, output_location=...
                    ├─ git push (makes output location official)
                    └─ Sends TaskCompletedMessage to kush:runner-1
                         │
                       L2-A (kush:runner-1)
                         ├─ Receives: COMPLETED + output_location
                         ├─ Reads output from atoms project (cross-project read)
                         ├─ Continues own work using borrowed results
                         ├─ Updates WORK_STREAM.md: task status=COMPLETED
                         └─ Records: cross-project credit for atoms:researcher-1
```

**Message Schema (Request)**:

```json
{
  "message_type": "cross_project_request",
  "metadata": {
    "message_id": "msg-kush-atoms-001",
    "sender_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
    "sender_project": "kush",
    "receiver_project": "atoms",
    "timestamp": "2026-02-19T14:42:00Z"
  },
  "request": {
    "request_id": "atoms:research-http-async",
    "description": "Research async HTTP libraries (httpx, aiohttp, trio-httpx). Need comparison matrix.",
    "required_capabilities": ["research"],
    "preferred_tier": "L2",
    "deadline": "2026-02-19T16:30:00Z",
    "estimated_effort_minutes": 60,
    "data_dependencies": {
      "output_format": "markdown",
      "output_location": "/atoms/docs/research/http-async-libs.md"
    }
  },
  "incentives": {
    "priority_boost": 2,
    "cross_project_credit": true,
    "resource_commitment": "kush can provide compute or storage help"
  }
}
```

**Response (Accepted)**:

```json
{
  "message_type": "cross_project_response",
  "metadata": {
    "message_id": "msg-atoms-kush-001",
    "sender_id": "atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude",
    "responder_id": "atoms:research-agent-1:L2:researcher",
    "timestamp": "2026-02-19T14:42:05Z",
    "in_reply_to": "msg-kush-atoms-001"
  },
  "status": "ACCEPTED",
  "request_id": "atoms:research-http-async",
  "responder_id": "atoms:research-agent-1:L2:researcher",
  "start_time": "2026-02-19T14:42:05Z",
  "estimated_completion": "2026-02-19T15:42:00Z",
  "commitment": {
    "will_deliver_by": "2026-02-19T15:45:00Z",
    "output_format": "markdown",
    "output_location": "/atoms/docs/research/http-async-libs.md"
  }
}
```

**Response (Deferred)**:

```json
{
  "message_type": "cross_project_response",
  "metadata": {
    "message_id": "msg-atoms-kush-002",
    "sender_id": "atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude",
    "responder_id": "atoms:research-agent-1:L2:researcher",
    "timestamp": "2026-02-19T14:42:06Z",
    "in_reply_to": "msg-kush-atoms-001"
  },
  "status": "DEFERRED",
  "request_id": "atoms:research-http-async",
  "reason": "TEMPORARILY_OVERLOADED",
  "details": {
    "current_load": {
      "tasks_active": 2,
      "tasks_queued": 3
    },
    "estimated_available_time": "2026-02-19T16:00:00Z",
    "suggested_alternatives": ["atoms:research-agent-2:L2:researcher"]
  }
}
```

---

## Pattern 3: Peer-to-Peer Negotiation (L2 ↔ L2 Same Project)

**Scenario**: Two L2 agents in same project need to coordinate access to shared resource (API key, database connection).

**Characteristics**:

- P2P (no central authority)
- Shared resource (scarce)
- Fair scheduling (queue-based)
- Timeout-based lease

### Semaphore-Based Coordination

**Flow**:

```
Runner-1 and Researcher-1 both need GitHub API
  ├─ They compete for single API key (rate-limited)
  │
  Runner-1 wants lock first
  ├─ Reads semaphore file: ~/.claude/civilization/semaphores/kush/github-api-key
  ├─ Current state: {holder: NONE, queue: []}
  ├─ Writes: {holder: runner-1, lease_until: T+60s, queue: []}
  ├─ git add + git commit
  └─ Acquires lock ✓
       │
     Researcher-1 also wants lock
       ├─ Reads semaphore file
       ├─ Current state: {holder: runner-1, lease_until: T+60s, queue: []}
       ├─ Appends self to queue: {holder: runner-1, queue: [researcher-1]}
       ├─ git add + git commit
       └─ Waits (polls queue file)
            │
          Runner-1 (using API)
            ├─ Uses GitHub API for 30s
            ├─ Decides to release early (task complete)
            ├─ Writes: {holder: NONE, queue: [researcher-1], released_at: now()}
            └─ Releases lock
                 │
               Researcher-1 (polling)
                 ├─ Detects: holder=NONE and queue=[researcher-1]
                 ├─ Acquires lock
                 ├─ Writes: {holder: researcher-1, lease_until: T+60s, queue: []}
                 └─ Now holds lock ✓
```

**Semaphore File Format**:

```json
{
  "resource_id": "github-api-key",
  "project": "kush",
  "metadata": {
    "created_at": "2026-02-19T14:00:00Z",
    "last_updated": "2026-02-19T14:43:00Z"
  },
  "current_lease": {
    "holder_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
    "acquired_at": "2026-02-19T14:42:00Z",
    "lease_until": "2026-02-19T14:43:00Z",
    "max_lease_seconds": 60
  },
  "queue": [
    {
      "requester_id": "kush:f9e8d7c6-b5a4-3c2b-1a09-8f7e6d5c4b3a:L2:researcher-1",
      "priority": 5,
      "requested_at": "2026-02-19T14:42:30Z"
    }
  ]
}
```

**Lock Acquisition Algorithm**:

```python
def acquire_semaphore(resource_id: str, agent_id: str, timeout_seconds: int = 300):
    """
    Acquire semaphore lock (lease-based).
    Returns when acquired or timeout.
    """
    semaphore_path = f"~/.claude/civilization/semaphores/{project}/{resource_id}"
    start_time = time.time()

    while True:
        # Read current state
        semaphore = read_json(semaphore_path)

        # Check if available
        if semaphore["current_lease"]["holder_id"] is None:
            # Try to acquire
            semaphore["current_lease"]["holder_id"] = agent_id
            semaphore["current_lease"]["acquired_at"] = now()
            semaphore["current_lease"]["lease_until"] = now() + 60
            write_json(semaphore_path, semaphore)
            git_push()  # Make it official
            return True  # Acquired!

        # Check if lease expired
        lease_until = datetime.fromisoformat(semaphore["current_lease"]["lease_until"])
        if lease_until < datetime.now():
            # Lease expired, forcibly acquire
            semaphore["current_lease"]["holder_id"] = agent_id
            semaphore["current_lease"]["acquired_at"] = now()
            semaphore["current_lease"]["lease_until"] = now() + 60
            write_json(semaphore_path, semaphore)
            git_push()
            return True  # Acquired after expiry

        # Add self to queue if not already there
        if agent_id not in [q["requester_id"] for q in semaphore["queue"]]:
            semaphore["queue"].append(
                {"requester_id": agent_id, "priority": calculate_priority(agent_id), "requested_at": now()}
            )
            write_json(semaphore_path, semaphore)
            git_push()

        # Check timeout
        if (time.time() - start_time) > timeout_seconds:
            raise SemaphoreAcquisitionTimeout(resource_id)

        # Wait and retry
        time.sleep(1)
```

**Release Algorithm**:

```python
def release_semaphore(resource_id: str, agent_id: str):
    """Release semaphore lock."""
    semaphore_path = f"~/.claude/civilization/semaphores/{project}/{resource_id}"
    semaphore = read_json(semaphore_path)

    # Verify this agent holds the lock
    if semaphore["current_lease"]["holder_id"] != agent_id:
        raise SemaphoreNotHeld(resource_id, agent_id)

    # Clear holder
    semaphore["current_lease"]["holder_id"] = None
    semaphore["current_lease"]["released_at"] = now()

    # Pop next from queue
    if semaphore["queue"]:
        next_requester = semaphore["queue"].pop(0)
        semaphore["next_lease"] = {"intended_holder": next_requester["requester_id"], "ready_at": now()}

    write_json(semaphore_path, semaphore)
    git_push()
```

---

## Pattern 4: Status & Escalation (L2/L3 → L1)

**Scenario**: L2 agent sends periodic status updates to L1 parent and escalates if blocked.

**Characteristics**:

- Hierarchical (parent-child)
- Periodic heartbeat (unidirectional)
- On-demand escalation (problem detected)
- Actionable alerts

### Periodic Status Update

**Flow**:

```
L2 every 5 minutes sends StatusUpdateMessage to L1
  ├─ Message contains:
  │  ├─ Current tasks (active, queued)
  │  ├─ Resource usage (CPU, memory)
  │  ├─ Completion rate (tasks/hour)
  │  └─ Alerts (none unless problem)
  │
  └─ L1 receives and logs in metrics.json
       ├─ Updates: L2 last_heartbeat, current_load
       └─ If alert present, may take action
```

**Message Schema (Status Update)**:

```json
{
  "message_type": "status_update",
  "metadata": {
    "message_id": "msg-runner-1-001",
    "sender_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
    "receiver_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
    "timestamp": "2026-02-19T14:45:00Z"
  },
  "status": "HEALTHY",
  "session_metrics": {
    "uptime_seconds": 3600,
    "tasks_completed": 12,
    "tasks_failed": 0,
    "avg_task_duration_minutes": 5.5
  },
  "current_state": {
    "tasks_active": 1,
    "tasks_queued": 2,
    "cpu_usage_percent": 25,
    "memory_usage_mb": 1200,
    "estimated_queue_drain_minutes": 10
  },
  "alerts": []
}
```

### Escalation on Blocking

**Flow**:

```
L2 is working on task-1 but blocked on atoms:task-2 (cross-project)
  ├─ T=0min: Task-1 becomes blocked, records start_time
  ├─ T=30min: Check deadline
  │  └─ deadline = T+60min
  │  └─ Remaining = 30min
  │  └─ > 30min buffer? No, escalate!
  │
  └─ Sends EscalationMessage to L1:
     {
       "escalation_level": 1,
       "reason": "BLOCKED_ON_EXTERNAL_TASK",
       "blocking_task": "atoms:task-2",
       "time_blocked_minutes": 30,
       "deadline_minutes": 30,
       "suggested_actions": [
         "check_status_atoms_task_2",
         "allocate_more_resources_atoms",
         "find_alternative_implementation"
       ]
     }
```

**Message Schema (Escalation)**:

```json
{
  "message_type": "escalation",
  "metadata": {
    "message_id": "msg-escalation-001",
    "sender_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
    "receiver_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
    "timestamp": "2026-02-19T14:45:30Z"
  },
  "escalation_level": 1,
  "task_id": "task-1",
  "reason": "BLOCKED_ON_EXTERNAL_TASK",
  "blocking_task_id": "atoms:task-2",
  "blocking_agent_id": "atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude",
  "time_blocked_minutes": 30,
  "deadline_minutes": 30,
  "blocking_task_status": "IN_PROGRESS (95% complete, expected 25 minutes)",
  "suggested_actions": [
    "check_status_atoms_task_2",
    "escalate_within_atoms_project",
    "start_parallel_alternative_approach",
    "increase_atoms_resource_quota"
  ]
}
```

---

## Pattern 5: Civilization-Wide Broadcast (Events)

**Scenario**: Critical event affects all agents (resource threshold breach, deadlock detected, cascading failure).

**Characteristics**:

- Broadcast (all agents receive)
- Event-driven (not periodic)
- Time-sensitive (immediate action needed)
- Recovery suggestions included

### Event Bus Implementation

**Primary**: Git-based event log

```
~/.claude/civilization/event_log.ndjson
```

**Example Events**:

```ndjson
{"type":"civilization.resource_threshold_breach","timestamp":"2026-02-19T14:46:00Z","resource":"cpu","threshold":90,"current":92,"affected_projects":["kush","atoms"]}
{"type":"civilization.deadlock_detected","timestamp":"2026-02-19T14:46:15Z","cycle":["kush:task-1","atoms:task-2","kush:task-3"],"recommended_resolution":"kill_kush_task_1"}
{"type":"agent.failed","timestamp":"2026-02-19T14:46:30Z","agent_id":"kush:runner-1:L2","tasks_in_progress":["task-1"],"last_heartbeat":"2026-02-19T14:45:00Z"}
{"type":"task.completed","timestamp":"2026-02-19T14:46:45Z","task_id":"atoms:research-async","agent_id":"atoms:researcher-1:L2","duration_minutes":45}
```

**Secondary**: MCP Pub-Sub (for real-time delivery)

```python
@mcp.subscription()
async def subscribe_events(topic: str = "all"):
    """
    Subscribe to civilization events.
    Topics: all, resource.*, task.*, agent.*, deadlock.*
    """
    # Returns stream of events matching topic
```

### Specific Event Schemas

**Resource Threshold Breach**:

```json
{
  "type": "civilization.resource_threshold_breach",
  "timestamp": "2026-02-19T14:46:00Z",
  "resource": "cpu",
  "threshold_percent": 90,
  "current_percent": 92,
  "civilization_metrics": {
    "cpu_percent": 92,
    "memory_percent": 78,
    "network_percent": 45
  },
  "affected_projects": ["kush", "atoms"],
  "affected_agents": [
    "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
    "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1"
  ],
  "recommended_actions": [
    "defer_non_urgent_tasks",
    "request_quota_boost_from_idle_projects",
    "increase_civilization_resource_limit"
  ],
  "ttl_seconds": 300
}
```

**Deadlock Detected**:

```json
{
  "type": "civilization.deadlock_detected",
  "timestamp": "2026-02-19T14:46:15Z",
  "cycle": [
    {
      "task_id": "kush:task-1",
      "agent_id": "kush:runner-1:L2",
      "blocked_on": "atoms:task-2"
    },
    {
      "task_id": "atoms:task-2",
      "agent_id": "atoms:researcher-1:L2",
      "blocked_on": "kush:task-3"
    },
    {
      "task_id": "kush:task-3",
      "agent_id": "kush:runner-1:L2",
      "blocked_on": "kush:task-1"
    }
  ],
  "severity": "CRITICAL",
  "recommended_resolution": {
    "action": "KILL_AND_RETRY",
    "kill_task_id": "kush:task-1",
    "retry_with_dependencies": ["atoms:task-2", "kush:task-3"]
  },
  "acknowledge_by": "2026-02-19T14:46:30Z"
}
```

**Agent Failure**:

```json
{
  "type": "agent.failed",
  "timestamp": "2026-02-19T14:46:30Z",
  "agent_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
  "reason": "HEARTBEAT_TIMEOUT",
  "last_heartbeat": "2026-02-19T14:45:00Z",
  "tasks_in_progress": [
    {
      "task_id": "task-1",
      "started_at": "2026-02-19T14:42:00Z",
      "estimated_completion": "2026-02-19T14:50:00Z"
    }
  ],
  "recovery_options": [
    {
      "option": "RETRY",
      "action": "Restart agent via ProcessCompose, resume task-1"
    },
    {
      "option": "REASSIGN",
      "action": "Assign task-1 to alternative agent"
    },
    {
      "option": "FAIL",
      "action": "Mark task-1 as FAILED, escalate to L1"
    }
  ],
  "default_action": "RETRY"
}
```

---

## Error Handling & Timeouts

### Timeout Hierarchy

| Scenario                 | Timeout           | Action                              |
| ------------------------ | ----------------- | ----------------------------------- |
| Task dispatch ACK (sync) | 5 seconds         | Retry with backoff, switch to async |
| Task execution           | 30 minutes (L2)   | Escalate, check if blocked          |
| Cross-project dependency | deadline - 30 min | Escalate, find alternative          |
| Semaphore acquisition    | 5 minutes         | Fail task, release resources        |
| Message delivery (async) | N/A (persisted)   | Retry on next poll                  |

### Retry Logic

**Exponential Backoff with Jitter**:

```python
def retry_with_backoff(
    operation, max_retries: int = 5, initial_backoff_seconds: float = 1.0, jitter_percent: float = 10
):
    """
    Retry with exponential backoff and jitter.
    """
    for attempt in range(max_retries):
        try:
            return operation()
        except TemporaryError as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff: 1s, 2s, 4s, 8s, 16s
            backoff = initial_backoff_seconds * (2**attempt)

            # Add jitter: ±10%
            jitter = backoff * random.uniform(-jitter_percent / 100, jitter_percent / 100)
            wait_time = backoff + jitter

            time.sleep(wait_time)
```

### Deadlock Detection & Prevention

**Detection Algorithm** (runs every 60s):

```python
def detect_deadlock():
    """
    Detect cycles in task dependency graph.
    """
    # Build dependency graph
    graph = {}
    for task in WORK_STREAM:
        graph[task.id] = task.blocked_on

    # Detect cycles
    cycles = find_cycles(graph)
    if cycles:
        for cycle in cycles:
            publish_event(
                {
                    "type": "civilization.deadlock_detected",
                    "cycle": cycle,
                    "recommended_resolution": compute_resolution(cycle),
                }
            )
```

**Prevention** (configured in WORK_STREAM.md):

```json
{
  "task_id": "task-1",
  "max_blocking_time_minutes": 60,
  "cycle_prevention": {
    "disable_cross_project_blocks": false,
    "max_transitive_depth": 5
  }
}
```

---

## Message Routing & Delivery

### Message Routing Decision Tree

```
message.type = ?
  ├─ task_dispatch
  │  ├─ target_tier = L1 → disallowed
  │  ├─ target_tier = L2/L3
  │  │  ├─ same_project? → use MCP (primary)
  │  │  └─ different_project? → disallowed (only cross-project_request)
  │  └─ is_synchronous?
  │     ├─ yes → MCP + wait for ACK (timeout: 5s)
  │     └─ no → queue + async poll
  │
  ├─ cross_project_request
  │  ├─ target_project ≠ sender_project? → yes, valid
  │  ├─ target_tier = L1/L2? → yes
  │  └─ use_endpoint?
  │     ├─ MCP (primary)
  │     ├─ Message queue (secondary)
  │     └─ Event bus (tertiary)
  │
  ├─ status_update / escalation
  │  ├─ target_tier = L1 (always)
  │  └─ use_endpoint?
  │     ├─ MCP (primary)
  │     ├─ Message queue (secondary)
  │     └─ Event bus (broadcast)
  │
  └─ event.* (broadcasts)
     ├─ Event log (primary, durable)
     ├─ MCP subscriptions (secondary, real-time)
     └─ Agent polling (tertiary)
```

### Endpoint Selection Algorithm

```python
async def route_message(message: Message) -> Result:
    """
    Route message to appropriate endpoint(s).
    """
    endpoints = resolve_endpoints(message.receiver_id)

    for endpoint in endpoints:
        try:
            result = await send_via_endpoint(message, endpoint)
            return result  # Success
        except (Timeout, ConnectionError) as e:
            # Try next endpoint
            continue

    raise MessageDeliveryFailed(message)
```

---

## Glossary

| Term                      | Definition                                                      |
| ------------------------- | --------------------------------------------------------------- |
| **Task Dispatch**         | L1 assigns work to L2/L3 (sync or async)                        |
| **Cross-Project Request** | L2 asks L2 in different project for help (negotiated)           |
| **Semaphore**             | Shared lock for resource access (lease-based)                   |
| **Status Update**         | Periodic heartbeat from L2/L3 to L1 (5-60s interval)            |
| **Escalation**            | L2 alerts L1 to problem (blocked, overloaded, failed)           |
| **Event Broadcast**       | Civilization-wide notification (deadlock, resource breach)      |
| **Backpressure**          | Rejecting task dispatch when overloaded                         |
| **Eventual Consistency**  | Agents converge to consistent state over time (not immediately) |
