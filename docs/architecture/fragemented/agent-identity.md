# Agent Identity and Discovery System

**Status**: Design v1.0
**Date**: 2026-02-19
**Scope**: Agent identification, registry management, and service discovery across 5-20 agents in multiple projects

---

## Overview

The Agent Identity and Discovery system provides:

- **Unique global identifiers** for all agents across all projects
- **Persistent identity** that survives agent restarts and project migrations
- **Scalable service discovery** supporting 5-20 agents with <100ms lookup latency
- **Fallback mechanisms** for offline/degraded scenarios
- **Decentralized architecture** (no single point of failure)

---

## Agent ID Format & Semantics

### Canonical Format

```
{project}:{uuid}:L{tier}:{role-slug}
```

**Components**:

| Component   | Type   | Length     | Format                           | Example                                |
| ----------- | ------ | ---------- | -------------------------------- | -------------------------------------- |
| `project`   | String | 3-16 chars | lowercase, alphanumeric, dashes  | `kush`, `atoms`, `my-project`          |
| `uuid`      | String | 36 chars   | UUID v4 (canonical RFC4122)      | `8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a` |
| `L{tier}`   | Enum   | 2 chars    | `L1`, `L2`, or `L3`              | `L1`                                   |
| `role-slug` | String | 3-32 chars | lowercase, alphanumeric, hyphens | `claude-code`, `runner-1`, `cursor-01` |

### Examples

```
kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code
  ├─ Project: kush
  ├─ UUID: 8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a
  ├─ Tier: L1 (top-level agent)
  └─ Role: claude-code (Claude Code editor)

atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude
  └─ Top-level Claude agent in atoms project

kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1
  └─ L2 sub-agent named "runner-1" in kush project

atoms:3d4e5f6a-7b8c-9d0e-1f2a-3b4c-5d6e:L3:cursor-01
  └─ L3 simulated agent (Cursor window) in atoms project
```

### Uniqueness Constraints

| Level       | Constraint                                        | Implication                                          |
| ----------- | ------------------------------------------------- | ---------------------------------------------------- |
| Global      | `{project}:{uuid}` is globally unique             | Only one agent with given UUID in given project      |
| Per-Project | Multiple agents can have same `role-slug`         | `runner-1`, `runner-2`, `runner-3` in same project   |
| Per-Agent   | UUID is immutable                                 | Identifies same agent across all projects it touches |
| Per-Tier    | Within project, can have multiple L1/L2/L3 agents | Multiple L2s in same project, each with unique UUID  |

### Special Cases

**L1 Agent Identity Schemes:**

- Claude Code: `{project}:L1:claude-code` (may have single UUID per project)
- Claude (CLI): `{project}:L1:claude` (may share UUID across projects if CLI-global)
- Cursor: `{project}:L1:cursor` (one Cursor window per project)

**L3 Agent Naming:**

- Cursor windows: `{project}:L3:cursor-01`, `cursor-02`, etc. (numbered)
- CLI agents: `{project}:L3:cli-agent-01` (numbered)
- External tools: `{project}:L3:tool-{tool_name}` (tool-specific)

---

## Agent UUID Generation & Persistence

### UUID Generation (At Agent Startup)

```python
# Pseudocode for agent startup
def initialize_agent_identity(project: str, role: str, tier: str):
    config_path = f"~/.claude/civilization/{project}/{role}.agent-id"

    if config_path.exists():
        uuid = read_file(config_path).strip()  # Reuse existing UUID
    else:
        uuid = generate_uuid_v4()  # Generate new
        write_file(config_path, uuid)
        chmod(config_path, 0o600)  # Readable only by agent

    agent_id = f"{project}:{uuid}:L{tier}:{role}"
    return agent_id
```

**Persistence Locations**:

```
~/.claude/civilization/
├── kush/
│   ├── claude-code.agent-id  (contains: 8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a)
│   ├── runner-1.agent-id
│   ├── runner-2.agent-id
│   └── researcher-1.agent-id
├── atoms/
│   ├── claude.agent-id
│   └── cursor-01.agent-id
└── thegent/
    ├── claude-code.agent-id
    └── reviewer-1.agent-id
```

**Guarantees**:

- Same agent always gets same UUID across restarts
- Agent UUID is immutable (persisted in `~/.claude/civilization/`)
- If agent file deleted, new UUID generated (treated as new agent)

---

## Global Registry Schema

### Primary Registry: `~/.claude/civilization/registry.json`

**Location**: Shared home directory (`~/.claude/civilization/`)

**Format**: JSON (human-readable, git-friendly)

**Schema**:

```json
{
  "version": "1.0",
  "metadata": {
    "last_updated": "2026-02-19T14:37:42Z",
    "civilization_id": "global-001",
    "registry_type": "authoritative"
  },
  "agents": [
    {
      "id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
      "project": "kush",
      "uuid": "8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a",
      "tier": "L1",
      "role": "claude-code",
      "status": "active",
      "created_at": "2026-02-10T08:00:00Z",
      "last_heartbeat": "2026-02-19T14:37:38Z",
      "heartbeat_interval_seconds": 10,
      "parent_id": null,
      "capabilities": [
        "read_files",
        "write_files",
        "run_bash",
        "delegate_to_l2",
        "researcher",
        "planner",
        "implementer"
      ],
      "endpoints": {
        "mcp": "127.0.0.1:3847",
        "mcp_scheme": "stdio",
        "http": "http://127.0.0.1:8317",
        "git_home": "/Users/kooshapari/temp-PRODVERCEL/485/kush"
      },
      "resource_quota": {
        "cpu_percent": 40,
        "memory_mb": 8192,
        "network_bps": 10000000,
        "max_concurrent_l2": 5
      },
      "current_state": {
        "status": "working",
        "tasks_claimed": 3,
        "l2_active": 2,
        "cpu_usage_percent": 25,
        "memory_usage_mb": 1500,
        "timestamp": "2026-02-19T14:37:38Z"
      }
    },
    {
      "id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
      "project": "kush",
      "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "tier": "L2",
      "role": "runner-1",
      "status": "active",
      "created_at": "2026-02-19T10:15:00Z",
      "last_heartbeat": "2026-02-19T14:37:40Z",
      "heartbeat_interval_seconds": 30,
      "parent_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
      "capabilities": [
        "read_files",
        "write_files",
        "run_tests",
        "delegate_to_l3"
      ],
      "endpoints": {
        "mcp": "127.0.0.1:3847",
        "message_queue": "/Users/kooshapari/.claude/civilization/queues/kush:runner-1.mq"
      },
      "resource_quota": {
        "cpu_percent": 15,
        "memory_mb": 3072,
        "max_concurrent_tasks": 2
      },
      "current_state": {
        "status": "working",
        "tasks_active": 1,
        "cpu_usage_percent": 10,
        "memory_usage_mb": 450,
        "timestamp": "2026-02-19T14:37:40Z"
      }
    },
    {
      "id": "atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude",
      "project": "atoms",
      "uuid": "7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f",
      "tier": "L1",
      "role": "claude",
      "status": "active",
      "created_at": "2026-02-15T12:30:00Z",
      "last_heartbeat": "2026-02-19T14:37:35Z",
      "heartbeat_interval_seconds": 15,
      "parent_id": null,
      "capabilities": ["read_files", "delegate_to_l2", "researcher"],
      "endpoints": {
        "mcp": "127.0.0.1:3848"
      },
      "resource_quota": {
        "cpu_percent": 35,
        "memory_mb": 6144
      },
      "current_state": {
        "status": "idle",
        "cpu_usage_percent": 5,
        "memory_usage_mb": 300,
        "timestamp": "2026-02-19T14:37:35Z"
      }
    },
    {
      "id": "atoms:3d4e5f6a-7b8c-9d0e-1f2a-3b4c-5d6e:L3:cursor-01",
      "project": "atoms",
      "uuid": "3d4e5f6a-7b8c-9d0e-1f2a-3b4c-5d6e",
      "tier": "L3",
      "role": "cursor-01",
      "status": "active",
      "created_at": "2026-02-19T08:00:00Z",
      "last_heartbeat": "2026-02-19T14:37:32Z",
      "heartbeat_interval_seconds": 60,
      "parent_id": "atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude",
      "capabilities": ["read_files", "write_files", "run_bash"],
      "endpoints": {
        "mcp": "127.0.0.1:3849"
      },
      "current_state": {
        "status": "idle",
        "cpu_usage_percent": 0,
        "memory_usage_mb": 50,
        "timestamp": "2026-02-19T14:37:32Z"
      }
    }
  ],
  "projects": [
    {
      "name": "kush",
      "created_at": "2026-02-10T08:00:00Z",
      "git_home": "/Users/kooshapari/temp-PRODVERCEL/485/kush",
      "agents": [
        "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
        "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
        "kush:f9e8d7c6-b5a4-3c2b-1a09-8f7e6d5c4b3a:L2:researcher-1"
      ],
      "resource_quota": {
        "cpu_percent": 40,
        "memory_mb": 8192
      },
      "current_usage": {
        "cpu_percent": 28,
        "memory_mb": 2300,
        "timestamp": "2026-02-19T14:37:38Z"
      }
    },
    {
      "name": "atoms",
      "created_at": "2026-02-15T12:30:00Z",
      "git_home": "/Users/kooshapari/atoms",
      "agents": [
        "atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude",
        "atoms:3d4e5f6a-7b8c-9d0e-1f2a-3b4c-5d6e:L3:cursor-01"
      ],
      "resource_quota": {
        "cpu_percent": 35,
        "memory_mb": 6144
      },
      "current_usage": {
        "cpu_percent": 15,
        "memory_mb": 1800,
        "timestamp": "2026-02-19T14:37:35Z"
      }
    }
  ]
}
```

### Registry Operations

#### Register Agent (On Startup)

```python
def register_agent(agent_id: str, metadata: dict) -> bool:
    """
    Register or update agent in global registry.
    Called at agent startup.
    """
    registry = read_registry()

    # Check if agent already exists
    existing = find_agent_in_registry(agent_id, registry)
    if existing:
        # Update heartbeat, status
        existing["last_heartbeat"] = now()
        existing["current_state"] = metadata["current_state"]
    else:
        # Add new agent
        registry["agents"].append({"id": agent_id, **metadata, "created_at": now(), "last_heartbeat": now()})

    write_registry(registry)
    git_commit(f"Register agent: {agent_id}")
    return True
```

#### Update Agent Status (Periodic Heartbeat)

```python
def heartbeat(agent_id: str, current_state: dict) -> bool:
    """
    Update agent heartbeat and current state.
    Called every 10-60 seconds (depends on tier).
    """
    registry = read_registry()
    agent = find_agent_in_registry(agent_id, registry)

    if not agent:
        raise AgentNotFound(agent_id)

    agent["last_heartbeat"] = now()
    agent["current_state"] = current_state

    write_registry(registry)
    # Batch commits: push every 30s or every 10 heartbeats
    if should_push_registry():
        git_push()
    return True
```

#### Lookup Agent

```python
def lookup_agent(agent_id: str) -> dict:
    """
    Look up agent in registry.
    Prefer local cache, fall back to git, then fallback to gossip.
    """
    # Try cache (in-memory, TTL=10s)
    if agent_id in LOCAL_CACHE and not LOCAL_CACHE[agent_id].expired():
        return LOCAL_CACHE[agent_id]

    # Try file (fast, immediate)
    registry = read_registry()
    agent = find_agent_in_registry(agent_id, registry)
    if agent:
        LOCAL_CACHE[agent_id] = CachedAgent(agent, ttl=10s)
        return agent

    # Try git pull (slower, ~1s)
    git_pull()
    registry = read_registry()
    agent = find_agent_in_registry(agent_id, registry)
    if agent:
        LOCAL_CACHE[agent_id] = CachedAgent(agent, ttl=10s)
        return agent

    # Try peer gossip (if git pull failed)
    return query_peer_gossip(agent_id, timeout=2s)
```

---

## Service Discovery Mechanisms

### Option 1: File-Based Registry (Primary)

**Strengths**:

- Simple (no separate service)
- Git-native (commits are audit trail)
- Works offline
- Compatible with existing projects

**Weaknesses**:

- ~1s lookup latency (need git pull)
- Eventual consistency (~10s propagation)
- Scaling concerns beyond 100 agents

**Implementation**:

```python
class FileBasedRegistry:
    def __init__(self, registry_path: str):
        self.registry_path = registry_path
        self.local_cache = {}
        self.cache_ttl = 10  # seconds

    def lookup(self, agent_id: str) -> AgentEntry:
        # Try cache first
        if agent_id in self.local_cache:
            cached = self.local_cache[agent_id]
            if not cached.expired():
                return cached.data

        # Try file
        registry = self._read_registry()
        for agent in registry["agents"]:
            if agent["id"] == agent_id:
                self.local_cache[agent_id] = CacheEntry(agent, ttl=self.cache_ttl)
                return agent

        # Try git pull
        subprocess.run(["git", "pull"], cwd=os.path.dirname(self.registry_path))
        registry = self._read_registry()
        for agent in registry["agents"]:
            if agent["id"] == agent_id:
                self.local_cache[agent_id] = CacheEntry(agent, ttl=self.cache_ttl)
                return agent

        raise AgentNotFound(agent_id)

    def _read_registry(self) -> dict:
        with open(self.registry_path, "r") as f:
            return json.load(f)
```

**Lookup Diagram**:

```
lookup(agent_id)
  ├─ Cache hit? → return (10ms)
  ├─ File hit? → cache + return (50ms)
  └─ File miss → git pull → retry (1000ms)
```

### Option 2: MCP Service Registry (Real-Time Alternative)

**Strengths**:

- <50ms lookup latency (local MCP call)
- Real-time updates (push-based)
- Scalable to 1000+ agents
- Strong consistency

**Weaknesses**:

- Requires MCP server (extra process)
- Single point of failure (can add replicas)
- Offline not supported (unless local cache)

**Implementation**:

```python
class MCPServiceRegistry:
    def __init__(self, mcp_endpoint: str):
        self.mcp_client = fastmcp.client.connect(mcp_endpoint)
        self.local_cache = {}

    async def lookup(self, agent_id: str) -> AgentEntry:
        # Try cache
        if agent_id in self.local_cache:
            cached = self.local_cache[agent_id]
            if not cached.expired():
                return cached.data

        # Query MCP service
        result = await self.mcp_client.call_tool(
            'registry_lookup',
            {'agent_id': agent_id}
        )

        if result.success:
            agent = result.data
            self.local_cache[agent_id] = CacheEntry(agent, ttl=5s)
            return agent
        else:
            raise AgentNotFound(agent_id)
```

**MCP Tool Schema**:

```python
@mcp.tool()
async def registry_lookup(agent_id: str) -> dict:
    """
    Look up agent in global registry.
    Returns full agent entry or AgentNotFound.
    """
    return get_registry_db().lookup(agent_id)


@mcp.tool()
async def registry_list_agents(
    project: str = None, tier: str = None, capability: str = None, status: str = "active"
) -> list:
    """
    List agents matching filters.
    """
    return get_registry_db().filter({"project": project, "tier": tier, "capability": capability, "status": status})
```

### Option 3: Gossip Protocol (Peer Discovery)

**Strengths**:

- Fully decentralized (no central registry needed)
- Resilient (survives network partitions)
- P2P discovery (agents find each other directly)
- Works offline

**Weaknesses**:

- 1-5s propagation (probabilistic)
- Eventual consistency (temporary inconsistency)
- Higher bandwidth (periodic gossip)

**Implementation**:

```python
class GossipRegistry:
    def __init__(self, agent_id: str, heartbeat_interval: int = 30):
        self.agent_id = agent_id
        self.heartbeat_interval = heartbeat_interval
        self.known_agents = {}  # agent_id → AgentEntry
        self.peers = set()  # known peer agent IDs

    def gossip(self):
        """
        Periodic gossip: send heartbeat to random peers.
        Called every heartbeat_interval seconds.
        """
        # Send heartbeat to N random peers
        for peer_id in random.sample(self.peers, min(3, len(self.peers))):
            peer_entry = self.known_agents[peer_id]
            self._send_heartbeat_to(peer_entry)

    def _send_heartbeat_to(self, peer_entry: AgentEntry):
        """Send heartbeat to peer agent."""
        message = {
            "type": "heartbeat",
            "agent_id": self.agent_id,
            "agents": list(self.known_agents.values()),  # Piggybacking
            "timestamp": now(),
        }
        self._send_message(peer_entry, message)

    def on_heartbeat_received(self, message: dict):
        """
        Handle incoming heartbeat from peer.
        Merge view of agents from peer.
        """
        for agent_entry in message["agents"]:
            self._merge_agent_entry(agent_entry)

        # Add peer to known peers
        self.peers.add(message["agent_id"])

    def lookup(self, agent_id: str) -> AgentEntry:
        """Look up agent locally (gossip result)."""
        if agent_id not in self.known_agents:
            # Trigger gossip query (async)
            self._query_peers_for(agent_id)
            raise AgentNotFound(agent_id)  # Temporary

        return self.known_agents[agent_id]
```

**Gossip Example** (timeline):

```
T=0: Agent A boots, knows only itself
     ├─ A.known_agents = {A}
     └─ A.peers = {}

T=5s: Agent A gossips to random peers
      └─ (no peers yet, gossip fails)

T=10s: Agent A meets Agent B (via message queue)
       ├─ A adds B to peers
       ├─ A receives B's agent list (B, C, D)
       └─ A merges into known_agents

T=15s: A.known_agents = {A, B, C, D}
       └─ A can now lookup any of these

T=20s: Agent A gossips {A, B, C, D} to C
       ├─ C adds A's new agents to its view
       └─ All agents converge over time
```

### Recommended Approach: Hybrid (Options 1 + 2 + 3)

**Strategy**: File-based primary, MCP secondary, gossip tertiary

```python
class HybridRegistry:
    def __init__(self, registry_path: str, mcp_endpoint: str = None):
        self.file_registry = FileBasedRegistry(registry_path)
        self.mcp_registry = MCPServiceRegistry(mcp_endpoint) if mcp_endpoint else None
        self.gossip_registry = GossipRegistry()
        self.fallback_chain = [
            self.file_registry,  # Fast, reliable
            self.mcp_registry,  # Real-time, if available
            self.gossip_registry,  # P2P fallback
        ]

    async def lookup(self, agent_id: str) -> AgentEntry:
        """Try each registry in order until success."""
        for registry in self.fallback_chain:
            try:
                return registry.lookup(agent_id)
            except AgentNotFound:
                continue

        raise AgentNotFound(agent_id)
```

---

## DNS-Like Lookup Examples

### Example 1: Direct Agent Lookup

```
Query: resolve("kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code")
       │
       ├─ Try cache: miss
       ├─ Try file: hit
       └─ Return:
           {
             "id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
             "endpoints": {
               "mcp": "127.0.0.1:3847",
               "http": "http://127.0.0.1:8317",
               "git_home": "/Users/kooshapari/temp-PRODVERCEL/485/kush"
             }
           }
```

### Example 2: Query by Project + Capability

```
Query: resolve_any(project="kush", capability="researcher", tier="L2")
       │
       ├─ Try cache: miss
       ├─ Try MCP tool: registry_list_agents(project=kush, tier=L2, capability=researcher)
       └─ Return:
           [
             {
               "id": "kush:f9e8d7c6-b5a4-3c2b-1a09-8f7e6d5c4b3a:L2:researcher-1",
               "status": "idle",
               "endpoints": { ... }
             }
           ]
       ├─ Pick first idle agent
       └─ Return entry
```

### Example 3: Cross-Project Agent Lookup (with Fallback)

```
Query: resolve("atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude")
       │
       ├─ Try cache: miss
       ├─ Try file: miss (atoms project not yet in kush's registry)
       ├─ Try git pull: fetches latest registry (atoms agents added)
       ├─ Try file again: hit
       └─ Return: atoms L1 endpoint
```

### Example 4: Agent Discovery (Bootstrapping)

```
New agent starts in kush project.
Query: discover_agents(project="kush")
       │
       ├─ Read local registry file
       ├─ Filter: project="kush"
       └─ Return:
           [
             {
               "id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
               "status": "active",
               "endpoints": { ... }
             },
             {
               "id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
               "status": "active",
               "endpoints": { ... }
             },
             ...
           ]
       ├─ New agent connects to L1
       └─ L1 can dispatch tasks to L2s
```

---

## Address Resolution Protocol (Detailed)

### DNS-Like Resolution

```python
async def resolve(agent_id: str, timeout: float = 5.0) -> AgentEndpoint:
    """
    Resolve agent_id to usable endpoints (DNS-like resolution).
    Returns first healthy endpoint or raises AgentNotFound.
    """
    agent_entry = await registry.lookup(agent_id)

    # Try endpoints in priority order
    endpoints = [
        agent_entry["endpoints"].get("mcp"),
        agent_entry["endpoints"].get("http"),
        agent_entry["endpoints"].get("git_home"),
    ]

    for endpoint in endpoints:
        if not endpoint:
            continue

        try:
            # Dial with timeout
            result = await dial(endpoint, timeout=timeout)
            return AgentEndpoint(
                agent_id=agent_id,
                endpoint=endpoint,
                protocol=result.protocol,  # mcp, http, or file
                latency_ms=result.latency_ms,
            )
        except DialFailed:
            continue  # Try next endpoint
        except Timeout:
            # Mark endpoint as slow, continue
            continue

    # All endpoints failed
    raise AgentUnreachable(agent_id)
```

### Endpoint Fallback Chain

| Priority | Protocol         | Latency    | Use Case                             |
| -------- | ---------------- | ---------- | ------------------------------------ |
| 1        | MCP (stdio)      | <50ms      | Task dispatch, real-time             |
| 2        | HTTP             | 100-200ms  | RESTful commands, fallback           |
| 3        | Git (file-based) | 500-1000ms | Async messages, eventual consistency |

### Example: Task Dispatch with Fallback

```python
async def dispatch_task(task_id: str, agent_id: str, prompt: str):
    """
    Dispatch task to agent, trying endpoints in order.
    """
    # Resolve agent
    try:
        endpoint = await resolve(agent_id, timeout=5s)
    except AgentUnreachable:
        raise DispatchFailed(f"Agent {agent_id} unreachable")

    # Try primary endpoint (MCP)
    if endpoint.protocol == 'mcp':
        try:
            result = await send_mcp_message(endpoint.address, {
                'type': 'task_dispatch',
                'task_id': task_id,
                'prompt': prompt,
                'timeout': 600
            }, timeout=5s)
            return DispatchResult(task_id=task_id, status='DISPATCHED')
        except (Timeout, ConnectionError):
            # Fall through to HTTP
            pass

    # Try secondary endpoint (HTTP)
    if endpoint.protocol == 'http':
        try:
            result = await http_post(endpoint.address + '/task/dispatch', {
                'task_id': task_id,
                'prompt': prompt
            }, timeout=5s)
            return DispatchResult(task_id=task_id, status='DISPATCHED')
        except (Timeout, ConnectionError):
            # Fall through to git-based async
            pass

    # Try tertiary endpoint (git-based async)
    try:
        queue_path = f"~/.claude/civilization/queues/{agent_id}.mq"
        write_queue_entry(queue_path, {
            'task_id': task_id,
            'prompt': prompt,
            'timestamp': now()
        })
        git_push()
        return DispatchResult(task_id=task_id, status='QUEUED')
    except Exception as e:
        raise DispatchFailed(f"All dispatch methods failed: {e}")
```

---

## Registry Consistency & Conflict Resolution

### Update Conflict Scenario

```
Timeline:
  T1: Agent A updates registry (last_heartbeat = T1)
      ├─ git add registry.json
      └─ git commit "heartbeat"

  T1+100ms: Agent B updates registry (different heartbeat)
      ├─ git add registry.json
      └─ git commit "heartbeat"

  Result: Both commits succeed (different files/lines)
          No conflict (sequential commits)
          Final state: Agent B's heartbeat (later)
```

### Concurrent Modification (CRDT Approach)

For high-frequency updates, use CRDT (Conflict-free Replicated Data Type):

```python
class CRDTAgentEntry:
    """
    CRDT-based agent entry.
    Supports concurrent updates without conflicts.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.clock = VectorClock()  # Per-agent logical clock
        self.last_heartbeat = Last_Writer_Wins(initial=None)
        self.status = Multi_Value(initial="unknown")
        self.current_state = Map()  # CRDT map for nested updates

    def update_heartbeat(self, timestamp: float, source_agent_id: str):
        """Update heartbeat with causal ordering."""
        self.clock.increment(source_agent_id)
        self.last_heartbeat.update(timestamp, clock=self.clock, source=source_agent_id)

    def merge(self, other_entry: "CRDTAgentEntry"):
        """Merge two entries (from concurrent updates)."""
        self.clock.merge(other_entry.clock)
        self.last_heartbeat.merge(other_entry.last_heartbeat)
        self.status.merge(other_entry.status)
        self.current_state.merge(other_entry.current_state)
```

---

## Health Checking & Stale Agent Detection

### Heartbeat Mechanism

**Heartbeat Interval** (by tier):

- L1: Every 10 seconds
- L2: Every 30 seconds
- L3: Every 60 seconds (or longer if idle)

**Stale Agent Detection**:

```python
def mark_stale_agents(registry: dict, now: float):
    """
    Mark agents as stale if heartbeat expired.
    """
    for agent in registry["agents"]:
        last_hb = datetime.fromisoformat(agent["last_heartbeat"])
        heartbeat_interval = agent.get("heartbeat_interval_seconds", 30)
        grace_period = heartbeat_interval * 3  # 3 missed heartbeats = stale

        if (now - last_hb.timestamp()) > grace_period:
            agent["status"] = "stale"
            agent["status_reason"] = f"No heartbeat for {(now - last_hb.timestamp()):.0f}s"
        elif agent["status"] == "stale":
            # Heartbeat recovered
            agent["status"] = "active"
            agent["status_reason"] = None
```

**Registry Cleanup**:

```python
def prune_stale_agents(registry: dict, max_stale_age_hours: int = 24):
    """
    Remove agents stale for >24 hours from registry.
    """
    now = time.time()
    active_agents = []
    pruned_count = 0

    for agent in registry["agents"]:
        last_hb = datetime.fromisoformat(agent["last_heartbeat"]).timestamp()
        stale_age_hours = (now - last_hb) / 3600

        if agent["status"] == "stale" and stale_age_hours > max_stale_age_hours:
            pruned_count += 1
            continue  # Skip this agent

        active_agents.append(agent)

    registry["agents"] = active_agents
    return pruned_count
```

---

## Security Considerations

### Identity Spoofing Prevention

1. **Persistent Identity**: UUID immutable, stored locally (`~/.claude/civilization/`)
2. **Registry Authentication**: Registry signed with GPG (optional, for security-sensitive projects)
3. **Endpoint Verification**: Connect to MCP endpoint, verify agent_id matches registry

```python
async def verify_agent_identity(endpoint: str, claimed_agent_id: str) -> bool:
    """
    Verify agent identity by connecting and asking agent to prove identity.
    """
    # Connect to MCP
    client = await connect_mcp(endpoint)

    # Ask agent for identity proof
    result = await client.call_tool("get_agent_identity")

    # Verify claimed_agent_id matches returned agent_id
    if result.agent_id != claimed_agent_id:
        raise IdentityMismatch(f"Expected {claimed_agent_id}, got {result.agent_id}")

    return True
```

### Registry Write Authorization

Only allow agents to update their own entry:

```python
def authorize_registry_update(updating_agent_id: str, entry_to_update: dict) -> bool:
    """
    Only allow agent to update its own entry.
    """
    # Extract project from agent_id
    updating_project = updating_agent_id.split(":")[0]
    entry_project = entry_to_update["id"].split(":")[0]

    # Only same-project agents can update (prevent cross-project tampering)
    if updating_project != entry_project:
        return False

    # Only agent itself can update its own entry
    if updating_agent_id != entry_to_update["id"]:
        return False

    return True
```

---

## Glossary

| Term            | Definition                                                         |
| --------------- | ------------------------------------------------------------------ |
| **Agent ID**    | Globally unique identifier: `{project}:{uuid}:L{tier}:{role-slug}` |
| **UUID**        | 36-character RFC4122 identifier, immutable per agent               |
| **Registry**    | Golden source of truth for agent identity, location, capabilities  |
| **Heartbeat**   | Periodic status update sent by agent (10-60s intervals)            |
| **Endpoint**    | Network address where agent can be reached (MCP, HTTP, git)        |
| **Discovery**   | Process of finding agents (registry lookup, gossip, MCP query)     |
| **CRDT**        | Conflict-free Replicated Data Type (for concurrent updates)        |
| **Stale Agent** | Agent that hasn't sent heartbeat for >3x interval                  |
