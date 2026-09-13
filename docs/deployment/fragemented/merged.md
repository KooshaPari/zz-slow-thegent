# Merged Fragmented Markdown

## Source: docs/deployment

## Source: deployment-overview.md

# CRUN Deployment Guide

**Deploy CRUN to production environments with confidence**

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Deployment Options](#deployment-options)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Local Deployment](#local-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Container Deployment (Docker)](#container-deployment-docker)
7. [Verification & Validation](#verification--validation)
8. [Rollback Procedures](#rollback-procedures)
9. [Scaling Considerations](#scaling-considerations)

---

## Deployment Overview

CRUN can be deployed in multiple ways depending on your infrastructure and use case:

| Deployment Type | Use Case                         | Complexity  | Scalability      |
| --------------- | -------------------------------- | ----------- | ---------------- |
| **Local**       | Development, testing             | Low         | Single machine   |
| **Server**      | Production on dedicated hardware | Medium      | Up to 100 agents |
| **Docker**      | Container orchestration          | High        | Multi-container  |
| **Kubernetes**  | Enterprise scale                 | High        | 1000+ agents     |
| **Cloud**       | AWS/GCP/Azure                    | Medium-High | Auto-scaling     |

---

## Deployment Options

### 1. Local Deployment

- **Best for:** Development, proof-of-concept
- **Requirements:** Single machine with Python 3.11+
- **Setup time:** 15 minutes
- **Scalability:** Limited to single machine resources

### 2. Server Deployment

- **Best for:** Production on dedicated hardware
- **Requirements:** Ubuntu/Debian server, systemd
- **Setup time:** 30 minutes
- **Scalability:** Up to 100 agents with proper resources

### 3. Docker Deployment

- **Best for:** Cloud platforms, CI/CD pipelines
- **Requirements:** Docker/Docker Compose
- **Setup time:** 20 minutes
- **Scalability:** Unlimited (horizontal scaling)

### 4. Kubernetes Deployment

- **Best for:** Enterprise, high availability
- **Requirements:** Kubernetes cluster
- **Setup time:** 1-2 hours
- **Scalability:** Unlimited (auto-scaling)

---

## Pre-Deployment Checklist

Before deploying CRUN, ensure:

- [ ] Python 3.11+ installed and tested
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -e ".[all]"`)
- [ ] `.env` file configured with production settings
- [ ] API keys configured (OpenAI, Anthropic, etc.)
- [ ] Database prepared (PostgreSQL for production)
- [ ] Redis/NATS configured (if using distributed mode)
- [ ] Sufficient disk space available (2GB minimum)
- [ ] Sufficient RAM available (8GB recommended)
- [ ] Firewall rules configured (ports: 8000, 8001, etc.)
- [ ] SSL/TLS certificates obtained (for HTTPS)
- [ ] Backup strategy defined
- [ ] Monitoring/alerting configured
- [ ] Log aggregation setup

---

## Local Deployment

### Step 1: Install CRUN

```bash
cd /path/to/crun
python3 -m venv venv
source venv/bin/activate
pip install -e ".[all]"
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

**Key settings for local deployment:**

```env
CRUN_ENVIRONMENT=development
CRUN_DEBUG=false
CRUN_LOG_LEVEL=INFO
CRUN_WORKSPACE_ROOT=/path/to/workspace
CRUN_WORKSPACE_LOG_DIR=/path/to/logs
CRUN_AGENTS_MAX_WORKERS=4
```

### Step 3: Test Installation

```bash
# Test CLI
crun --help

# Test GUI
crun gui

# Test TUI
crun tui
```

### Step 4: Create Projects

```bash
# Generate first plan
crun ai-plan generate-massive project_spec.txt -o plan.md

# Monitor execution
crun ai-plan monitor plan.md --workers 8
```

---

## Cloud Deployment

### AWS Deployment

#### Step 1: Launch EC2 Instance

```bash
# Launch Ubuntu 22.04 LTS t3.xlarge instance
# Configure security group to allow:
#   - Port 22 (SSH)
#   - Port 8000 (CRUN API)
#   - Port 8001 (WebSocket)
```

#### Step 2: SSH into Instance

```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

#### Step 3: Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip git

# Clone or upload CRUN
git clone <repository> crun
cd crun
```

#### Step 4: Setup and Deploy

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[all]"

# Configure environment
cp .env.example .env
nano .env  # Set your API keys and settings

# Start CRUN service
nohup crun gui --host 0.0.0.0 --port 8000 &
```

#### Step 5: Setup Systemd Service

Create `/etc/systemd/system/crun.service`:

```ini
[Unit]
Description=CRUN Multi-Agent Orchestration
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/crun
Environment="PATH=/home/ubuntu/crun/venv/bin"
ExecStart=/home/ubuntu/crun/venv/bin/python -m crun.cli.main gui --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable crun
sudo systemctl start crun
sudo systemctl status crun
```

### GCP Deployment

Similar steps for Google Cloud Platform:

1. Create Compute Engine VM (Ubuntu 22.04)
2. Install dependencies
3. Deploy CRUN
4. Configure Cloud Load Balancer for HA
5. Setup Cloud Logging/Monitoring

### Azure Deployment

Similar steps for Microsoft Azure:

1. Create Virtual Machine
2. Install dependencies
3. Deploy CRUN
4. Use Azure App Service or Container Instances
5. Configure Azure Monitor

---

## Container Deployment (Docker)

### Step 1: Create Dockerfile

Create `Dockerfile` in the project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app

# Install CRUN
RUN pip install --no-cache-dir -e ".[all]"

# Expose ports
EXPOSE 8000 8001

# Default command
CMD ["crun", "gui", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Create Docker Compose

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  crun:
    build: .
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - CRUN_ENVIRONMENT=production
      - CRUN_DEBUG=false
      - CRUN_DB_HOST=postgres
      - CRUN_REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/.crun/logs
      - ./cache:/app/.crun/cache
    restart: always

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=crun
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=crun
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Step 3: Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f crun

# Stop services
docker-compose down
```

### Step 4: Verify Container

```bash
# Check services running
docker-compose ps

# Access CRUN
curl http://localhost:8000/health

# View logs
docker-compose logs crun
```

---

## Verification & Validation

### Health Checks

#### 1. CLI Test

```bash
crun --version
crun --help
```

#### 2. API Test

```bash
# If running with API
curl -X GET http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "3.0.0"}
```

#### 3. Planning Test

```bash
# Generate a test plan
echo "Build a test app" | crun ai-plan generate-massive - -o test_plan.md

# Verify plan created
ls -la test_plan.md
```

#### 4. Database Test

```bash
# Test PostgreSQL connection (if configured)
psql -h localhost -U crun -d crun -c "SELECT 1;"
```

#### 5. Agent Test

```bash
# Test plan execution
crun ai-plan monitor test_plan.md --workers 1
```

### Smoke Tests

```bash
#!/bin/bash
# smoke_test.sh

echo "Testing CRUN deployment..."

# Test 1: Version
crun --version || { echo "Version check failed"; exit 1; }

# Test 2: Help
crun --help > /dev/null || { echo "Help check failed"; exit 1; }

# Test 3: Planner command group
crun ai-plan --help > /dev/null || { echo "Planner help check failed"; exit 1; }

# Test 4: Create test plan
echo "Test" | crun ai-plan generate-massive - -o test_plan.md || { echo "Plan generation failed"; exit 1; }

# Test 5: Cleanup
rm test_plan.md

echo "All smoke tests passed!"
```

Run tests:

```bash
bash smoke_test.sh
```

---

## Rollback Procedures

### Scenario 1: Rollback Docker Container

```bash
# View deployment history
docker-compose ps
docker images

# Rollback to previous image
docker-compose down
docker-compose up -d  # Uses previous image if available
```

### Scenario 2: Rollback Systemd Service

```bash
# Stop current version
sudo systemctl stop crun

# Restore from backup
cd /home/ubuntu/crun
git checkout HEAD~1  # Go to previous commit

# Restart with previous version
sudo systemctl start crun
sudo systemctl status crun
```

### Scenario 3: Database Rollback

```bash
# If using PostgreSQL, restore from backup
pg_restore -h localhost -U crun -d crun /path/to/backup.sql

# Verify restoration
psql -h localhost -U crun -d crun -c "SELECT COUNT(*) FROM plans;"
```

### Scenario 4: File-Based Rollback

```bash
# Backup before deployment
tar -czf crun_backup_$(date +%Y%m%d_%H%M%S).tar.gz /path/to/crun

# Restore from backup
tar -xzf crun_backup_20260220_100000.tar.gz -C /
```

---

## Scaling Considerations

### Horizontal Scaling (Multiple Machines)

For scaling to multiple machines:

1. **Use NATS for messaging:** Configure NATS cluster for agent coordination
2. **Use PostgreSQL:** Central database for state
3. **Use Redis:** Distributed caching
4. **Load Balancer:** Route requests across instances

**Example NATS configuration:**

```yaml
# nats.conf
cluster {
  name: "crun-cluster"
  listen: 0.0.0.0:4222
  routes: [
    "nats://nats1:6222",
    "nats://nats2:6222",
    "nats://nats3:6222"
  ]
}
```

### Vertical Scaling (Single Machine)

For scaling on a single machine:

1. **Increase resources:** RAM, CPU, disk space
2. **Adjust worker pools:** `CRUN_AGENTS_MAX_WORKERS`
3. **Database optimization:** Index frequently queried columns
4. **Cache optimization:** Redis memory allocation

**Configuration for high-load:**

```env
CRUN_AGENTS_MAX_WORKERS=100
CRUN_AGENTS_EXECUTION_TIMEOUT=600
CRUN_RESOURCES_TARGET_FD_LIMIT=65536
CRUN_PLANNING_RESOURCE_ALLOCATION_STRATEGY=aggressive
```

### Performance Tuning

```bash
# Monitor performance
watch -n 1 'ps aux | grep crun'

# Check resource usage
top -p $(pgrep -f "crun")

# Check file descriptors
lsof -p $(pgrep -f "crun") | wc -l

# Check database connections
psql -h localhost -U crun -d crun -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Troubleshooting Deployments

### Issue: Service Won't Start

```bash
# Check logs
systemctl status crun -l

# Check error
journalctl -u crun -n 50

# Verify binary exists
which crun
```

### Issue: Out of Memory

```bash
# Check memory usage
free -h

# Reduce worker count
CRUN_AGENTS_MAX_WORKERS=5

# Enable memory profiling
python -m memory_profiler crun
```

### Issue: Database Connection Failed

```bash
# Test connection
psql -h localhost -U crun -d crun

# Check credentials in .env
grep CRUN_DB .env

# Verify PostgreSQL running
systemctl status postgresql
```

---

## Monitoring in Production

### Key Metrics to Monitor

- **CPU Usage:** Should stay below 80%
- **Memory Usage:** Should not exceed 85% of available
- **Disk Space:** Maintain at least 10% free
- **Agent Count:** Track active agents
- **Task Success Rate:** Monitor for anomalies
- **API Response Time:** Should be < 1 second
- **Database Size:** Monitor growth rate

### Example Monitoring Setup

```bash
# Using Prometheus + Grafana
# 1. Install Prometheus
# 2. Configure scrape targets
# 3. Install Grafana
# 4. Create dashboards
# 5. Set up alerting
```

---

**Version:** CRUN 3.0.0 | Last Updated: 2026-02-20

---

## Source: multi-tenant-config.md

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

---

## Source: runbooks/startup.md

# CRUN Startup Runbook

**Step-by-step operational guide for starting up CRUN system**

## Table of Contents

1. [Pre-Startup Checks](#pre-startup-checks)
2. [Startup Sequence](#startup-sequence)
3. [Health Checks](#health-checks)
4. [Verification Procedures](#verification-procedures)
5. [Common Startup Issues](#common-startup-issues)
6. [Shutdown Procedure](#shutdown-procedure)

---

## Pre-Startup Checks

Perform these checks **before** attempting to start CRUN:

### 1. System Resource Check

```bash
#!/bin/bash
# Check available resources

echo "=== System Resource Check ==="

# Check available memory
FREE_MEM=$(free -m | awk '/^Mem:/ {print $7}')
echo "Free Memory: ${FREE_MEM}MB (Minimum required: 2GB/2000MB)"

if [ $FREE_MEM -lt 2000 ]; then
    echo "⚠️  WARNING: Low memory available"
fi

# Check disk space
DISK_FREE=$(df -h . | awk 'NR==2 {print $4}')
echo "Disk Space Free: $DISK_FREE (Minimum required: 2GB)"

# Check CPU count
CPU_COUNT=$(nproc)
echo "Available CPUs: $CPU_COUNT"

# Check file descriptor limit
FD_LIMIT=$(ulimit -n)
echo "File Descriptor Limit: $FD_LIMIT (Minimum: 4096, Recommended: 10240)"

if [ $FD_LIMIT -lt 4096 ]; then
    echo "⚠️  WARNING: Increase file descriptor limit"
    echo "   Run: ulimit -n 10240"
fi
```

Run the check:

```bash
bash pre_startup_check.sh
```

**Expected Output:**

```
=== System Resource Check ===
Free Memory: 8192MB (Minimum required: 2GB/2000MB)
Disk Space Free: 50G (Minimum required: 2GB)
Available CPUs: 8
File Descriptor Limit: 1024 (Minimum: 4096, Recommended: 10240)
⚠️  WARNING: Increase file descriptor limit
   Run: ulimit -n 10240
```

### 2. File Descriptor Limit Configuration

```bash
# Increase file descriptor limit
ulimit -n 10240

# Verify change
ulimit -n
# Output should be: 10240
```

### 3. Environment Variables Check

```bash
# Verify required environment variables are set
echo "Checking environment variables..."

# Check API keys are set (for AI features)
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  WARNING: No API key found"
    echo "   Set: export OPENAI_API_KEY=sk-... OR export ANTHROPIC_API_KEY=sk-ant-..."
fi

# Check CRUN_ENVIRONMENT
echo "CRUN_ENVIRONMENT: ${CRUN_ENVIRONMENT:-not set}"

# Check workspace path
echo "CRUN_WORKSPACE_ROOT: ${CRUN_WORKSPACE_ROOT:-.}"
```

### 4. Dependency Check

```bash
# Verify Python version
echo "Python version:"
python3 --version

# Verify virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  ERROR: Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    exit 1
fi

# Check CRUN is installed
if ! command -v crun &> /dev/null; then
    echo "⚠️  ERROR: CRUN not found"
    echo "   Run: pip install -e .[all]"
    exit 1
fi

echo "✓ Virtual environment: $VIRTUAL_ENV"
echo "✓ CRUN installed: $(crun --version)"
```

### 5. Database Connectivity Check

```bash
# For PostgreSQL deployments
if [ "$CRUN_DB_HOST" != "" ]; then
    echo "Checking database connectivity..."

    psql -h $CRUN_DB_HOST -U $CRUN_DB_USERNAME -d $CRUN_DB_NAME \
        -c "SELECT 1" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "✓ Database connected"
    else
        echo "⚠️  ERROR: Cannot connect to database"
        echo "   Check credentials in .env"
        exit 1
    fi
fi
```

### 6. Service Dependencies Check

```bash
# Check if Redis is running (if configured)
if [ "$REDIS_ENABLED" == "true" ]; then
    redis-cli ping > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ Redis running"
    else
        echo "⚠️  WARNING: Redis not running"
    fi
fi

# Check if NATS is running (if configured)
if [ "$NATS_ENABLED" == "true" ]; then
    nc -zv $NATS_HOST $NATS_PORT > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ NATS running"
    else
        echo "⚠️  WARNING: NATS not running"
    fi
fi
```

---

## Startup Sequence

Follow these steps **in order** to start CRUN:

### Step 1: Activate Virtual Environment

```bash
cd /path/to/crun
source venv/bin/activate

# Verify activation (prompt should show (venv))
# Expected: (venv) user@machine:crun$
```

### Step 2: Source Environment Variables

```bash
# Load .env file
source .env

# Verify key variables loaded
echo "Environment: $CRUN_ENVIRONMENT"
echo "Debug: $CRUN_DEBUG"
```

### Step 3: Start Database (if using external database)

```bash
# For PostgreSQL
sudo systemctl start postgresql

# For Redis
sudo systemctl start redis-server

# For NATS
nats-server -c nats.conf &
```

### Step 4: Create Required Directories

```bash
# Create log directory
mkdir -p .crun/logs
mkdir -p .crun/cache

# Verify permissions
chmod 755 .crun
chmod 755 .crun/logs
chmod 755 .crun/cache
```

### Step 5: Initialize Database (First Time Only)

```bash
# Create database schema
# There is no dedicated `crun init` command exposed in this branch.
# For PostgreSQL, initialize schema via your deployment tooling before first startup.
```

### Step 6: Start CRUN

Choose based on your deployment mode:

#### Option A: CLI Mode (Minimal)

```bash
# Run in foreground
crun --help

# Or run a background service
nohup crun gui &

# Or use systemd (production)
sudo systemctl start crun
```

#### Option B: GUI Mode

```bash
# Launch GUI (requires display)
crun gui --host 0.0.0.0 --port 8000
```

#### Option C: TUI Mode

```bash
# Launch Terminal UI
crun tui
```

#### Option D: Server Mode

```bash
# Start as HTTP server
python -m crun.api.server --host 0.0.0.0 --port 8000 --workers 4
```

### Step 7: Verify Service Started

```bash
# Check if CRUN process is running
ps aux | grep crun | grep -v grep

# Check port is listening (if using server mode)
netstat -tuln | grep 8000

# Or with ss (modern systems)
ss -tuln | grep 8000
```

---

## Health Checks

Perform these health checks after startup:

### 1. CLI Health Check

```bash
# Test CLI works
crun --version

# Expected output: CRUN 3.0.0
```

### 2. Service Health Check

```bash
# Check service status
sudo systemctl status crun

# Expected output:
# ● crun.service - CRUN Multi-Agent Orchestration
#    Loaded: loaded (/etc/systemd/system/crun.service; enabled; vendor preset: enabled)
#    Active: active (running) since...
```

### 3. HTTP Health Check

```bash
# If running as server
curl -s http://localhost:8000/health | jq .

# Expected output:
# {
#   "status": "healthy",
#   "version": "3.0.0",
#   "timestamp": "2026-02-20T12:00:00Z"
# }
```

### 4. Database Health Check

```bash
# Check database connection
python3 -c "
from crun.config import get_settings
settings = get_settings()
engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✓ Database connected')
"
```

### 5. Agent Pool Health Check

```bash
# Check CRUN process and logs
ps aux | grep crun | grep -v grep
tail -f .crun/logs/crun.log | sed -n '1,40p'

# There is currently no dedicated `crun status agents` command.
```

### 6. Log File Check

```bash
# Check logs for errors
tail -f .crun/logs/crun.log

# Look for ERROR or CRITICAL lines
grep -i error .crun/logs/crun.log
```

---

## Verification Procedures

### Procedure 1: Test Plan Generation

```bash
# Create a test project
cat > test_project.txt << 'EOF'
Build a simple CLI tool that:
- Reads a CSV file
- Filters rows based on column value
- Writes output to JSON
EOF

# Generate a plan
crun ai-plan generate-massive test_project.txt -o test_plan.md

# Verify plan created
if [ -f test_plan.md ]; then
    echo "✓ Plan generation working"
    wc -l test_plan.md  # Should be 1000+ lines
else
    echo "⚠️  Plan generation failed"
fi
```

### Procedure 2: Test Code Quality Analysis

```bash
# Test code quality on a sample directory
# Run monitor once over a sample directory
crun monitor start --workspace ./src --languages python,typescript --lint --tests

# Verify report created
echo "✓ Code quality command completed"
```

### Procedure 3: Test Execution

```bash
# Test plan execution
crun ai-plan monitor test_plan.md --workers 1

# Expected: Plan executes without errors
```

### Procedure 4: Test UI

```bash
# Test GUI launches (or TUI if no display)
crun gui --theme system &
sleep 5

# Check process is running
ps aux | grep crun | grep gui
```

---

## Common Startup Issues

### Issue 1: Virtual Environment Not Activated

**Symptom:**

```
bash: crun: command not found
```

**Solution:**

```bash
# Activate virtual environment
source venv/bin/activate

# Verify activation
which crun
# Should show: /path/to/crun/venv/bin/crun
```

---

### Issue 2: Python Version Incompatible

**Symptom:**

```
ERROR: This project requires Python 3.11+
```

**Solution:**

```bash
# Check Python version
python3 --version

# Use specific Python version
python3.12 -m venv venv
source venv/bin/activate
pip install -e ".[all]"
```

---

### Issue 3: API Key Not Found

**Symptom:**

```
Error: API key not configured for model
```

**Solution:**

```bash
# Set API key
export OPENAI_API_KEY=sk-your-key

# Or add to .env
echo "OPENAI_API_KEY=sk-your-key" >> .env
source .env

# Verify
echo $OPENAI_API_KEY
```

---

### Issue 4: Port Already in Use

**Symptom:**

```
ERROR: Address already in use 0.0.0.0:8000
```

**Solution:**

```bash
# Find process using port
lsof -ti:8000

# Kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
CRUN_PORT=8001 crun gui
```

---

### Issue 5: Out of Memory

**Symptom:**

```
MemoryError: Unable to allocate memory
```

**Solution:**

```bash
# Reduce worker count
CRUN_AGENTS_MAX_WORKERS=2 crun gui

# Or increase system limits
ulimit -v unlimited
```

---

### Issue 6: Database Connection Failed

**Symptom:**

```
ERROR: Can't connect to database
```

**Solution:**

```bash
# Verify database is running
systemctl status postgresql

# Check credentials in .env
grep CRUN_DB .env

# Test connection manually
psql -h localhost -U crun -d crun -c "SELECT 1"
```

---

## Shutdown Procedure

### Graceful Shutdown

```bash
# If running in foreground (Ctrl+C)
# Press Ctrl+C to stop

# Or send SIGTERM signal
pkill -TERM -f "crun"

# Wait for graceful shutdown
sleep 5

# Verify process stopped
ps aux | grep crun | grep -v grep
```

### Systemd Shutdown

```bash
# Stop service
sudo systemctl stop crun

# Verify stopped
sudo systemctl status crun

# Check logs for shutdown messages
sudo journalctl -u crun -n 10
```

### Force Shutdown

```bash
# If process won't terminate gracefully
pkill -KILL -f "crun"

# Clean up any remaining resources
rm -f .crun/locks/*
```

### Backup Before Shutdown

```bash
# Back up current state
tar -czf crun_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    .crun/cache .crun/logs .crun/*.db
```

---

## Startup Checklist Script

```bash
#!/bin/bash
# startup_checklist.sh - Complete startup verification

set -e

echo "=== CRUN Startup Checklist ==="

# 1. Check resources
echo "1. Checking system resources..."
ulimit -n 10240

# 2. Activate venv
echo "2. Activating virtual environment..."
source venv/bin/activate

# 3. Load environment
echo "3. Loading environment..."
source .env

# 4. Create directories
echo "4. Creating required directories..."
mkdir -p .crun/{logs,cache}

# 5. Database check
echo "5. Checking database..."
if [ "$CRUN_DB_URL" != "" ]; then
    python3 -c "from sqlalchemy import create_engine; create_engine('$CRUN_DB_URL').connect()"
fi

# 6. Health check
echo "6. Running health check..."
crun --version

echo ""
echo "✓ All checks passed!"
echo "Ready to start CRUN"
echo ""
echo "To start, run:"
echo "  crun gui              # GUI mode"
echo "  crun tui              # Terminal UI"
echo "  crun --help           # CLI help"
```

Run the checklist:

```bash
bash startup_checklist.sh
```

---

**Version:** CRUN 3.0.0 | Last Updated: 2026-02-20

---

## Source: scaling-guide.md

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

---

Copied count: 4
