# Design: Mac ↔ PC Compute Offload Architecture

**Document Version:** 1.0
**Change ID:** research-compute-offload
**Date:** 2026-02-18
**Status:** Design
**Phase:** Research & Prototype

---

## 1. Architecture Overview

### 1.1 System Diagram: Remote Shadow Workspace (RSW)

The Distributed Compute Offload architecture is designed as a **Remote Shadow Workspace (RSW)** system. It does not just share states; it creates true, isolated, concurrent execution environments on remote "Worker" nodes (e.g., your Desktop PC).

```text
[ LAPTOP (Client) ]                      [ DESKTOP PC (Worker Node) ]
        │                                            │
        │ 1. Workload Analysis                       │
        ├───────────────────┐                        │
        │                   ▼                        │
        │           [Offload Router]                 │
        │                   │                        │
        │ 2. State Sync (SSE)│ 3. Execution Request  │
        ├───────────────────┼───────────────────────▶│ [Remote Executor]
        │                   │ (JSON Bridge)          │        │
        │                   │                        │        │ 4. Spawn RSW
        │                   │                        │        ▼
        │                   │                        │ [Shadow Workspace]
        │                   │                        │ (git worktree)
        │                   │                        │        │
        │                   │                        │        │ 5. Execute Agent
        │                   │                        │        ▼
        │ 6. Stream Results │                        │ [ isolated process ]
        │◀──────────────────┼────────────────────────┤        │
        │                   │                        │        │
        │ 7. Reconcile      │                        │        │ 8. Cleanup
        │◀──────────────────┴────────────────────────┴────────┘
```

### 1.2 Core Logic: Remote Worktree vs. Shared State

- **Option: Shared OS/States (NO)**: We avoid a simple shared filesystem because it leads to "Index Contention" and state-smashing when both your laptop and desktop try to write to the same `.git` index.
- **Effectively Remote Worktree (YES)**: The `State Synchronization Engine (SSE)` ensures your desktop has the exact delta of your code. The `Remote Executor` then spawns a **True Concurrent Workspace** using `git worktree`.
- **Result**: You can be coding on your laptop while 3 different agents are running heavy tests or builds on your Desktop PC, each in their own isolated filesystem slice.

## 2. Expanded Feature Set (Breadth & Depth)

To "maximally engineer" this system, we are adding the following dimensions:

### 2.1 State Synchronization Engine (SSE) [BREADTH]

- **Git-Delta Sync**: Instead of sending full files, we send uncommitted diffs + current HEAD. Fast, even on high-latency links.
- **Virtual Filesystem Fallback**: If the repo is not Git-managed, we use an `rsync`-like rolling hash sync.
- **Artifact-Aware Sync**: Excludes `node_modules`, `.venv`, and `target/` to minimize network transit.

### 2.2 Remote Shadow Workspace Manager (RSWM) [DEPTH]

- **Isolation Levels**:
  - _Level 1 (Process)_: High speed, uses standard worktree isolation.
  - _Level 2 (Containerized)_: Spawns a Docker container mapped to the worktree for OS-level parity (e.g., running Linux tests from a Mac client).
- **Lifespan Management**: Auto-prunes worktrees after task completion or heartbeat loss.

### 2.3 Cross-Platform Context Bridging (XPCB) [POLISH]

- **Path Translation**: Automatically maps `/Users/koosha/...` (Mac) to `C:\Users\koosha\...` (Windows) during context handoff.
- **Tool Parity**: Leverages `mise` on the remote node to ensure the _exact_ same version of Python/Rust/Node is used as on the client.

### 2.4 Distributed TUI Cockpit (QOL) [POLISH]

- **Unified View**: A laptop dashboard showing:
  - CPU/RAM load on Desktop PC.
  - Active remote tasks and their "time-to-complete" estimates.
  - One-click "Remote Attach" to view live logs.

## 3. Implementation Status (Updated)

| Feature                 | Engineering Depth      | Status             |
| :---------------------- | :--------------------- | :----------------- |
| **Bridge Protocol**     | Pydantic V2 + JSON     | Finalized          |
| **SSE (Sync)**          | Git Worktree Over SSH  | **IN DEVELOPMENT** |
| **Remote Executor**     | FastAPI + Streaming    | **IN DEVELOPMENT** |
| **Workload Classifier** | Heuristic AST Analysis | Finalized          |
| **TUI Cockpit**         | Textual (Python)       | Planned            |

### 1.2 Component Responsibilities

| Component               | Responsibility                                    | Location                                 |
| ----------------------- | ------------------------------------------------- | ---------------------------------------- |
| **Compute Catalog**     | Registry of available environments + capabilities | `thegent/offload/compute_catalog.py`     |
| **Capability Resolver** | Probe local env; publish fingerprint              | `thegent/offload/capability_resolver.py` |
| **Workload Classifier** | Analyze task; infer platform requirements         | `thegent/offload/workload_classifier.py` |
| **Offload Router**      | Route to best target based on policy              | `thegent/offload/offload_router.py`      |
| **Bridge Protocol**     | Serialize/deserialize execution context           | `thegent/offload/bridge_protocol.py`     |
| **Remote Executor**     | Listen for offload requests; execute tasks        | `thegent/offload/remote_executor.py`     |
| **Offload Client**      | Initiate remote execution; stream results         | `thegent/offload/offload_client.py`      |

---

## 2. Core Components

### 2.1 Compute Catalog

**Purpose**: Registry of available compute environments and their capabilities.

**Data Structure**:

```python
class Environment(BaseModel):
    """Represents a compute environment (Mac, Linux, Windows)"""

    env_id: str  # "mac-m1-mini", "linux-ubuntu-22.04", "windows-11"
    os: str  # "macos", "linux", "windows"
    arch: str  # "arm64", "x86_64"
    hostname: str  # FQDN or IP
    base_url: str  # "http://192.168.1.100:9000" for remote executor

    # Resource profile
    cpu_cores: int
    memory_gb: float
    storage_gb: float

    # Cost profile ($/minute)
    cost_per_minute: float

    # Capabilities
    capabilities: Set[str]  # {"git", "python-3.12", "node-20", "swift", ...}

    # Network
    network_latency_ms: float  # Approximate RTT
    bandwidth_mbps: float

    # Health
    is_online: bool
    last_health_check: datetime
    availability_percentage: float  # SLA %

    # Metadata
    region: str  # "local", "us-west", "eu-central"
    created_at: datetime
    expires_at: Optional[datetime]  # For temporary nodes


class CapabilityProfile(BaseModel):
    """Capabilities of an environment"""

    languages: Set[str]  # {"python", "node", "rust", "go", "swift"}
    package_managers: Set[str]  # {"pip", "npm", "cargo", "go"}
    runtimes: Set[str]  # {"python-3.12", "node-20", "jvm-21"}
    compilers: Set[str]  # {"gcc", "clang", "rustc", "swiftc"}
    build_tools: Set[str]  # {"make", "cmake", "cargo", "gradle"}
    vcs: Set[str]  # {"git", "hg"}
    container: Set[str]  # {"docker", "podman"}
    databases: Set[str]  # {"postgres", "mysql", "mongodb"}
    cloud_tools: Set[str]  # {"aws-cli", "gcloud", "az"}
    dev_frameworks: Set[str]  # {"xcode", "visual-studio", "vscode"}


class ComputeCatalog(BaseModel):
    """Registry of all available environments"""

    environments: Dict[str, Environment]  # env_id -> Environment

    @classmethod
    def load(cls, path: Path) -> "ComputeCatalog":
        """Load from JSON/YAML file"""
        pass

    def save(self, path: Path):
        """Save to JSON file"""
        pass

    def register_environment(self, env: Environment):
        """Register a new environment"""
        self.environments[env.env_id] = env

    def find_by_hostname(self, hostname: str) -> Optional[Environment]:
        """Find environment by hostname"""
        pass

    def get_online_environments(self) -> List[Environment]:
        """Filter to online environments"""
        return [e for e in self.environments.values() if e.is_online]
```

**File Format** (JSON):

```json
{
  "environments": {
    "mac-m1-mini": {
      "env_id": "mac-m1-mini",
      "os": "macos",
      "arch": "arm64",
      "hostname": "macs-mini.local",
      "base_url": "http://192.168.1.100:9000",
      "cpu_cores": 8,
      "memory_gb": 24.0,
      "storage_gb": 512.0,
      "cost_per_minute": 0.005,
      "capabilities": ["git", "python-3.12", "node-20", "swift", "rustc"],
      "network_latency_ms": 1.5,
      "bandwidth_mbps": 1000.0,
      "is_online": true,
      "last_health_check": "2026-02-18T10:15:32Z",
      "availability_percentage": 99.5,
      "region": "local",
      "created_at": "2026-02-01T00:00:00Z",
      "expires_at": null
    },
    "linux-ubuntu": {
      "env_id": "linux-ubuntu",
      "os": "linux",
      "arch": "x86_64",
      "hostname": "ubuntu-vm.local",
      "base_url": "http://192.168.1.101:9000",
      "cpu_cores": 16,
      "memory_gb": 32.0,
      "storage_gb": 1024.0,
      "cost_per_minute": 0.003,
      "capabilities": ["git", "python-3.12", "node-20", "rustc", "gcc"],
      "network_latency_ms": 2.0,
      "bandwidth_mbps": 1000.0,
      "is_online": true,
      "last_health_check": "2026-02-18T10:14:12Z",
      "availability_percentage": 98.9,
      "region": "local",
      "created_at": "2026-02-05T00:00:00Z",
      "expires_at": null
    }
  }
}
```

**Persistence**:

- Location: `~/.thegent/compute_catalog.json` (or `${THGENT_COMPUTE_CATALOG_PATH}`)
- Refresh: TTL 5 minutes (or on-demand via `health_check()`)
- Sync: Each environment's remote executor publishes its catalog entry; control plane aggregates

---

### 2.2 Capability Resolver

**Purpose**: Probe local environment; publish capabilities.

**Interface**:

```python
class CapabilityResolver:
    """Probe local machine for capabilities"""

    @staticmethod
    def probe() -> CapabilityProfile:
        """Detect installed tools, languages, runtimes in this environment"""
        profile = CapabilityProfile()

        # Detect languages
        profile.languages.add("python") if _has_python() else None
        profile.languages.add("node") if _has_node() else None
        # ... etc

        # Detect runtimes
        if _has_python():
            profile.runtimes.add(f"python-{_get_python_version()}")

        # Detect build tools
        profile.build_tools.add("make") if _has_make() else None

        return profile

    @staticmethod
    def _has_python() -> bool:
        """Check if Python is available"""
        return shutil.which("python3") is not None

    @staticmethod
    def _get_python_version() -> str:
        """Get Python version"""
        result = subprocess.run(["python3", "--version"], capture_output=True, text=True)
        return result.stdout.strip().split()[-1]  # "3.12.0"


class CapabilityCache:
    """Cache resolved capabilities with TTL"""

    def __init__(self, ttl_seconds: int = 600):  # 10 min default
        self.ttl = ttl_seconds
        self.profile: Optional[CapabilityProfile] = None
        self.cached_at: Optional[datetime] = None

    def get(self) -> CapabilityProfile:
        """Get cached or re-probe if expired"""
        now = datetime.utcnow()
        if self.profile and self.cached_at and (now - self.cached_at).total_seconds() < self.ttl:
            return self.profile

        self.profile = CapabilityResolver.probe()
        self.cached_at = now
        return self.profile
```

**Usage**:

```python
# During remote executor startup
cache = CapabilityCache(ttl_seconds=600)
profile = cache.get()

# Periodically publish to control plane
env_entry = Environment(
    env_id="mac-m1-mini",
    capabilities=profile.all_capabilities,
    # ... other fields
)
catalog.register_environment(env_entry)
```

---

### 2.3 Workload Classifier

**Purpose**: Analyze task/prompt; infer platform requirements.

**Heuristics**:

```python
class WorkloadClassifier:
    """Classify workload by platform suitability"""

    def classify(self, prompt: str, code: Optional[str] = None) -> "Classification":
        """Analyze prompt and code to infer requirements"""

        classification = Classification(
            required_capabilities=set(),
            preferred_os=None,  # None=flexible, "macos", "linux", "windows"
            suitable_environments=[],
            confidence=0.0,
        )

        # Heuristic 1: Language Detection
        for lang in ["python", "node", "rust", "go", "swift", "java", "c++"]:
            if self._mentions_language(prompt, lang) or self._detect_code_language(code) == lang:
                classification.required_capabilities.add(lang)

        # Heuristic 2: Framework Detection
        if "xcode" in prompt.lower() or "swift" in prompt.lower():
            classification.required_capabilities.add("xcode")
            classification.preferred_os = "macos"

        if "visual-studio" in prompt.lower() or ".net" in prompt.lower():
            classification.required_capabilities.add("visual-studio")
            classification.preferred_os = "windows"

        # Heuristic 3: Tool Detection
        if "docker" in prompt.lower():
            classification.required_capabilities.add("docker")

        if "cargo" in prompt.lower():
            classification.required_capabilities.add("cargo")

        # Heuristic 4: OS-Specific Commands
        if "brew install" in prompt.lower():
            classification.preferred_os = "macos"

        if "apt install" in prompt.lower() or "yum install" in prompt.lower():
            classification.preferred_os = "linux"

        if "choco install" in prompt.lower():
            classification.preferred_os = "windows"

        # Compute suitability for each environment in catalog
        catalog = ComputeCatalog.load(CATALOG_PATH)
        for env in catalog.environments.values():
            suitability = self._compute_suitability(env, classification)
            classification.suitable_environments.append((env.env_id, suitability))

        # Confidence: fraction of required capabilities available in best match
        if classification.suitable_environments:
            best_env_id, best_score = max(classification.suitable_environments, key=lambda x: x[1])
            classification.confidence = best_score

        return classification

    def _mentions_language(self, prompt: str, lang: str) -> bool:
        """Check if prompt mentions a language"""
        keywords = {
            "python": ["python", "py3", "django", "flask", "pandas"],
            "node": ["node", "npm", "javascript", "typescript", "express"],
            "rust": ["rust", "cargo", "tokio", "axum"],
            # ... etc
        }
        return any(kw in prompt.lower() for kw in keywords.get(lang, []))

    def _compute_suitability(self, env: Environment, classification: "Classification") -> float:
        """Score environment suitability (0.0-1.0)"""
        if not classification.required_capabilities:
            return 1.0  # Flexible workload; any env is fine

        matched = len(classification.required_capabilities & env.capabilities)
        total = len(classification.required_capabilities)
        base_score = matched / total if total > 0 else 1.0

        # Prefer matching OS if specified
        if classification.preferred_os:
            if env.os == classification.preferred_os:
                base_score *= 1.05  # 5% boost
            else:
                base_score *= 0.5  # 50% penalty

        return min(1.0, base_score)


class Classification(BaseModel):
    required_capabilities: Set[str]
    preferred_os: Optional[str]  # "macos", "linux", "windows", or None
    suitable_environments: List[Tuple[str, float]]  # [(env_id, score), ...]
    confidence: float  # 0.0-1.0
```

---

### 2.4 Offload Router

**Purpose**: Select best target environment; apply routing policies.

**Routing Policies**:

```python
from enum import Enum


class RoutingPolicy(Enum):
    COST_OPTIMAL = "cost_optimal"  # Cheapest
    LATENCY_OPTIMAL = "latency_optimal"  # Fastest
    CAPABILITY_OPTIMAL = "capability_optimal"  # Most capable
    AVAILABILITY_OPTIMAL = "availability_optimal"  # Highest SLA
    PARETO = "pareto"  # Pareto frontier (cost vs latency)


class OffloadRouter:
    """Route workload to best target environment"""

    def __init__(self, policy: RoutingPolicy = RoutingPolicy.COST_OPTIMAL):
        self.policy = policy
        self.catalog = ComputeCatalog.load(CATALOG_PATH)

    def route(self, classification: "Classification") -> Optional["Route"]:
        """Select target environment for this workload"""

        # Filter to suitable environments
        suitable = [
            (env_id, score)
            for env_id, score in classification.suitable_environments
            if score > 0.5  # Min 50% suitability
        ]

        if not suitable:
            return None  # No suitable environment

        # Apply routing policy
        if self.policy == RoutingPolicy.COST_OPTIMAL:
            return self._select_cost_optimal(suitable)
        elif self.policy == RoutingPolicy.LATENCY_OPTIMAL:
            return self._select_latency_optimal(suitable)
        elif self.policy == RoutingPolicy.CAPABILITY_OPTIMAL:
            return self._select_capability_optimal(suitable)
        elif self.policy == RoutingPolicy.AVAILABILITY_OPTIMAL:
            return self._select_availability_optimal(suitable)
        elif self.policy == RoutingPolicy.PARETO:
            return self._select_pareto_optimal(suitable)

        return None

    def _select_cost_optimal(self, suitable: List[Tuple[str, float]]) -> "Route":
        """Select cheapest suitable environment"""
        env_id, _ = min(suitable, key=lambda x: self._cost_score(x[0]))
        env = self.catalog.environments[env_id]
        return Route(
            env_id=env.env_id,
            hostname=env.hostname,
            base_url=env.base_url,
            reason=f"Cost optimal: ${env.cost_per_minute:.4f}/min",
        )

    def _select_latency_optimal(self, suitable: List[Tuple[str, float]]) -> "Route":
        """Select fastest suitable environment"""
        env_id, _ = min(suitable, key=lambda x: self._latency_score(x[0]))
        env = self.catalog.environments[env_id]
        return Route(
            env_id=env.env_id,
            hostname=env.hostname,
            base_url=env.base_url,
            reason=f"Latency optimal: {env.network_latency_ms:.1f}ms RTT",
        )

    def _cost_score(self, env_id: str) -> float:
        """Cost score (lower is better)"""
        env = self.catalog.environments[env_id]
        return env.cost_per_minute

    def _latency_score(self, env_id: str) -> float:
        """Latency score (lower is better)"""
        env = self.catalog.environments[env_id]
        return env.network_latency_ms


class Route(BaseModel):
    env_id: str
    hostname: str
    base_url: str
    reason: str  # Human-readable explanation for routing decision
```

---

### 2.5 Bridge Protocol

**Purpose**: Serialize/deserialize execution context for cross-platform communication.

**Message Format**:

```python
class ExecutionRequest(BaseModel):
    """Request to offload task execution"""

    request_id: str  # UUID
    timestamp: datetime

    # Execution context
    prompt: str
    cwd: str  # Working directory (relative to executor home)
    env_vars: Dict[str, str]  # Environment variables to inject
    timeout_seconds: int  # Execution timeout

    # Origin
    origin_hostname: str
    origin_agent: str  # e.g., "claude-sonnet"
    origin_mode: str  # e.g., "write", "read-only"

    # Policy
    cost_cap_usd: Optional[float] = None
    dry_run: bool = False  # Don't actually execute; validate only

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req-abc123",
                "timestamp": "2026-02-18T10:15:32Z",
                "prompt": "Analyze this Python codebase",
                "cwd": "~/myrepo",
                "env_vars": {"PYTHONPATH": "."},
                "timeout_seconds": 300,
                "origin_hostname": "mac-m1.local",
                "origin_agent": "claude-sonnet",
                "origin_mode": "write",
                "cost_cap_usd": 1.0,
                "dry_run": False,
            }
        }


class ExecutionResponse(BaseModel):
    """Response from remote executor"""

    request_id: str  # Echo request_id
    timestamp: datetime

    # Execution result
    exit_code: int
    stdout: str
    stderr: str

    # Metadata
    execution_time_seconds: float
    executor_hostname: str

    # Cost
    cost_usd: float
    tokens_used: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req-abc123",
                "timestamp": "2026-02-18T10:15:45Z",
                "exit_code": 0,
                "stdout": "Analysis complete: 42 files, 3 major issues found",
                "stderr": "",
                "execution_time_seconds": 12.3,
                "executor_hostname": "linux-ubuntu.local",
                "cost_usd": 0.008,
                "tokens_used": 4200,
            }
        }
```

**HTTP API**:

```
POST /v1/offload/execute
Content-Type: application/json
Authorization: Bearer <token>

{
  "request_id": "req-abc123",
  ...
}

---

HTTP/1.1 200 OK
Content-Type: application/json

{
  "request_id": "req-abc123",
  ...
}
```

---

### 2.6 Remote Executor

**Purpose**: Listen for offload requests; execute tasks in sandbox; return results.

**Server Interface**:

```python
class RemoteExecutor:
    """HTTP server for executing offloaded tasks"""

    def __init__(self, host: str = "0.0.0.0", port: int = 9000):
        self.host = host
        self.port = port
        self.app = self._build_app()

    def _build_app(self) -> FastAPI:
        """Build FastAPI app"""
        app = FastAPI(title="RemoteExecutor")

        @app.post("/v1/offload/execute")
        async def execute(request: ExecutionRequest) -> ExecutionResponse:
            """Execute an offloaded task"""
            try:
                # Validate request
                if request.cost_cap_usd is not None:
                    cost = self._estimate_cost(request)
                    if cost > request.cost_cap_usd:
                        raise CostCapExceeded(f"Estimated {cost} > cap {request.cost_cap_usd}")

                # Dry run: validate only
                if request.dry_run:
                    return ExecutionResponse(
                        request_id=request.request_id,
                        timestamp=datetime.utcnow(),
                        exit_code=0,
                        stdout="Dry run OK",
                        stderr="",
                        execution_time_seconds=0.0,
                        executor_hostname=socket.gethostname(),
                        cost_usd=0.0,
                    )

                # Execute in sandbox
                result = await self._execute_in_sandbox(request)

                return ExecutionResponse(
                    request_id=request.request_id,
                    timestamp=datetime.utcnow(),
                    exit_code=result.exit_code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    execution_time_seconds=result.execution_time_seconds,
                    executor_hostname=socket.gethostname(),
                    cost_usd=result.cost_usd,
                    tokens_used=result.tokens_used,
                )

            except Exception as e:
                return ExecutionResponse(
                    request_id=request.request_id,
                    timestamp=datetime.utcnow(),
                    exit_code=1,
                    stdout="",
                    stderr=str(e),
                    execution_time_seconds=0.0,
                    executor_hostname=socket.gethostname(),
                    cost_usd=0.0,
                )

        @app.get("/v1/health")
        async def health() -> dict:
            """Health check"""
            return {"status": "ok", "hostname": socket.gethostname()}

        return app

    async def _execute_in_sandbox(self, request: ExecutionRequest) -> "ExecutionResult":
        """Execute request in isolated sandbox"""
        # For prototype: OS-level process isolation (no containers)
        # Future: Docker/Podman container with security context

        import subprocess
        import time

        start_time = time.time()

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(request.env_vars)

            # Expand cwd
            cwd = os.path.expanduser(request.cwd)

            # Invoke agent (delegate to installed agent, e.g., "claude" CLI)
            result = subprocess.run(
                ["thegent", "run", request.prompt],
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
            )

            execution_time = time.time() - start_time

            return ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time_seconds=execution_time,
                cost_usd=self._compute_cost(execution_time),
                tokens_used=self._estimate_tokens(result.stdout, result.stderr),
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ExecutionResult(
                exit_code=124,  # Timeout exit code
                stdout="",
                stderr="Execution timed out",
                execution_time_seconds=execution_time,
                cost_usd=self._compute_cost(execution_time),
                tokens_used=None,
            )

    def _compute_cost(self, execution_time_seconds: float) -> float:
        """Compute execution cost based on time"""
        # Placeholder: $0.001 per minute
        return (execution_time_seconds / 60.0) * 0.001

    def _estimate_tokens(self, stdout: str, stderr: str) -> int:
        """Estimate token usage from output"""
        # Placeholder: ~4 chars per token
        output = stdout + stderr
        return len(output) // 4

    def run(self):
        """Start the server"""
        import uvicorn

        uvicorn.run(self.app, host=self.host, port=self.port)


class ExecutionResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    execution_time_seconds: float
    cost_usd: float
    tokens_used: Optional[int] = None
```

---

### 2.7 Offload Client

**Purpose**: Initiate remote execution from control plane.

**Interface**:

```python
class OffloadClient:
    """Client for invoking remote executor"""

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.http_client = httpx.AsyncClient()

    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Send execution request to remote executor"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        response = await self.http_client.post(
            f"{self.base_url}/v1/offload/execute",
            json=request.dict(),
            headers=headers,
            timeout=60.0,
        )

        if response.status_code != 200:
            raise OffloadError(f"Execution failed: {response.status_code} {response.text}")

        return ExecutionResponse(**response.json())

    async def health_check(self) -> bool:
        """Check if remote executor is alive"""
        try:
            response = await self.http_client.get(
                f"{self.base_url}/v1/health",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False
```

---

## 3. Integration with thegent

### 3.1 Execution Flow

```
User: thegent run "Analyze Python repo" free
    │
    ├─→ AgentRunner.run()
    │   ├─→ WorkloadClassifier.classify()  # Detect "python"
    │   │   └─→ Classification{required={"python"}, suitable=[...]}
    │   │
    │   ├─→ OffloadRouter.route()  # Select best env
    │   │   └─→ Route{env_id="linux-ubuntu", ...}
    │   │
    │   ├─→ OffloadClient.execute()  # Send to remote
    │   │   ├─→ ExecutionRequest{prompt, cwd, ...}
    │   │   └─→ ExecutionResponse{exit_code, stdout, stderr, ...}
    │   │
    │   └─→ Return normalized result
    │
    └─→ Display output
```

### 3.2 Policy Engine Integration

Offload decisions should respect governance policies:

```python
# In OffloadRouter.route()
def route(self, classification: "Classification") -> Optional["Route"]:
    # ... select candidate environments ...

    # Evaluate against policy
    policy_result = self.policy_engine.evaluate(
        operation_type="OFFLOAD",
        target_env=candidate_env,
        cost_estimate=self._estimate_cost(candidate_env),
        agent_name=self.origin_agent,
    )

    if not policy_result.allow:
        raise OffloadNotAllowed(f"Policy: {policy_result.reason}")

    return route
```

### 3.3 Telemetry & Cost Tracking

Log offload decisions and outcomes:

```python
# In run_registry
def register_offload_decision(self, run_id: str, offload_decision: OffloadDecision):
    """Record offload routing decision"""
    event = {
        "type": "offload_decision",
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "classification": offload_decision.classification.dict(),
        "selected_route": offload_decision.selected_route.dict(),
        "reason": offload_decision.reason,
    }
    self._append_to_registry(event)


def register_offload_completion(self, run_id: str, response: ExecutionResponse):
    """Record offload execution result"""
    event = {
        "type": "offload_completion",
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "exit_code": response.exit_code,
        "execution_time_seconds": response.execution_time_seconds,
        "cost_usd": response.cost_usd,
        "executor_hostname": response.executor_hostname,
    }
    self._append_to_registry(event)
```

---

## 4. Configuration & Deployment

### 4.1 Environment Variables

```bash
# Compute catalog path
export THGENT_COMPUTE_CATALOG_PATH="~/.thegent/compute_catalog.json"

# Offload routing policy
export THGENT_OFFLOAD_POLICY="cost_optimal"  # cost_optimal, latency_optimal, capability_optimal

# Remote executor settings
export THGENT_OFFLOAD_EXECUTOR_HOST="0.0.0.0"
export THGENT_OFFLOAD_EXECUTOR_PORT="9000"
export THGENT_OFFLOAD_EXECUTOR_AUTH_TOKEN="secret-token-here"

# Offload capabilities (enable/disable)
export THGENT_OFFLOAD_ENABLED="true"
export THGENT_OFFLOAD_MAX_COST_CAP_USD="10.0"
```

### 4.2 Setup Instructions

**On each target environment (Mac, Linux, Windows):**

1. Install thegent
2. Start remote executor:
   ```bash
   thegent offload serve --host 0.0.0.0 --port 9000
   ```
3. Publish to shared catalog (manual for prototype):
   ```bash
   # On control plane
   thegent offload register --env-id linux-ubuntu \
     --hostname ubuntu-vm.local \
     --base-url http://192.168.1.101:9000 \
     --cpu-cores 16 --memory-gb 32
   ```

---

## 5. Testing Strategy

### 5.1 Unit Tests

- `test_compute_catalog.py`: Load/save, register, query
- `test_capability_resolver.py`: Probe mock environment, cache TTL
- `test_workload_classifier.py`: Classify Python, Node, Rust, Swift workloads
- `test_offload_router.py`: Route with different policies (cost, latency)
- `test_bridge_protocol.py`: Serialize/deserialize execution requests/responses

### 5.2 Integration Tests

- `test_offload_end_to_end.py`: Full flow (classify → route → execute → return)
  - Test case 1: Python analysis on Linux
  - Test case 2: Swift build on Mac (should fail on Linux)
  - Test case 3: Cost routing selects cheapest

### 5.3 Mock Strategy

- Mock `ComputeCatalog` with 3 test environments
- Mock `OffloadClient` to return canned responses
- Real subprocess execution in integration tests

---

## 6. Security Considerations

### 6.1 Authentication

**Prototype**: Pre-shared bearer tokens (simple, not production-grade)

```bash
# Client sends token
curl -H "Authorization: Bearer secret-token" \
  http://executor:9000/v1/offload/execute
```

**Future**: mTLS certificates, OAuth, JWT

### 6.2 Isolation

**Prototype**: OS-level process isolation (separate user, working directory)

**Future**: Docker/Podman containers with restricted capabilities

### 6.3 Input Validation

- Validate `cwd` is within allowed directories (prevent path traversal)
- Validate `env_vars` keys/values (prevent injection)
- Reject overly long prompts (prevent DoS)

### 6.4 Network

- Assume LAN/VPN only (no internet-scale security)
- Implement timeout (5s) for health checks
- Log all requests (audit trail)

---

## 7. Error Handling & Fallback

### 7.1 Failure Modes

| Scenario                         | Handling                               |
| -------------------------------- | -------------------------------------- |
| Remote executor offline          | Fall back to local execution           |
| Network timeout                  | Retry with backoff; fall back to local |
| Cost cap exceeded                | Reject offload; run locally            |
| Workload unsuitable for all envs | Run locally with warning               |
| Executor policy rejects request  | Fall back to local                     |

### 7.2 Fallback Flow

```python
def run_with_offload_fallback(self, prompt: str) -> RunResult:
    """Try offload; fall back to local execution"""
    try:
        classification = self.classifier.classify(prompt)
        route = self.router.route(classification)
        if not route:
            raise NoSuitableEnvironment("No suitable offload target")

        client = OffloadClient(route.base_url, self.auth_token)
        response = await client.execute(ExecutionRequest(...))

        return self._adapt_response(response)

    except (OffloadNotAllowed, OffloadError, NoSuitableEnvironment, TimeoutError) as e:
        logger.warning(f"Offload failed: {e}; falling back to local execution")
        return self._execute_locally(prompt)
```

---

## 8. Decision Log

### Decision 1: HTTP vs gRPC

**Chosen**: HTTP (prototype only)

**Rationale**:

- Simpler to implement and debug
- Built-in tooling (curl, Postman)
- Stateless; easier to load balance
- JSON serialization widely understood

**Trade-off**: gRPC would be more efficient (binary + streaming), but complexity not justified for prototype.

---

### Decision 2: JSON vs Protocol Buffers

**Chosen**: JSON + Pydantic

**Rationale**:

- Self-documenting
- Pydantic provides validation + serialization
- Human-readable logs

---

### Decision 3: Centralized vs Distributed Catalog

**Chosen**: File-based catalog with periodic sync (hybrid)

**Rationale**:

- Simple for prototype (single JSON file)
- Avoid external service dependency
- Future: Gossip protocol or git-based sync

---

### Decision 4: Local vs Container Isolation

**Chosen**: OS-level process isolation (local execution)

**Rationale**:

- Simpler to prototype
- Sufficient for LAN environments
- Future: Docker containers for stronger isolation

---

## 9. References & Appendices

### A. Example Workload Classifications

See proposal.md Appendix A

### B. Compute Catalog Example

See Section 2.1

### C. Bridge Protocol Schema

See Section 2.5

---

**End of Design Document**
