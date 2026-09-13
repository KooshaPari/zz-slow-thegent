# Cross-Platform Coordination Through Unified Work Stream — Design

**Status**: Design
**Date**: 2026-02-18
**Baseline**: proposal.md

## 1. Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    Unified Work Stream                        │
│              (docs/reference/WORK_STREAM.md)                  │
│  ┌─────────────┬──────────────┬─────────────────────────────┐ │
│  │   BACKLOG   │   CLAIMED    │      COMPLETED              │ │
│  │  (pending)  │ (in-flight)  │      (done)                 │ │
│  └─────────────┴──────────────┴─────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                            ▲
                ┌───────────┼───────────┐
                │           │           │
    ┌───────────────┐ ┌────────────┐ ┌──────────────┐
    │  File Locking │ │   Agent    │ │ Session      │
    │  + Git Merge  │ │  Registry  │ │  Bridge      │
    └───────────────┘ └────────────┘ └──────────────┘
         (atomic)      (capability)   (continuity)
```

## 2. Core Components

### 1. Platform Registry

**Location**: `thegent/platform/registry.py`

**Data Model**:
```python
@dataclass
class PlatformCapabilities:
    os_type: OSType  # darwin, linux, win32
    arch: str  # x86_64, arm64, aarch64
    python_version: str  # 3.11.2
    tools: Dict[str, ToolCapability]  # {rg: present, version: 14.0}
    env_vars: Dict[str, str]  # PATH, SHELL, etc.
    max_concurrent_processes: int
    available_memory_mb: int
    disk_free_mb: int
    container_runtime: Optional[str]  # docker, podman
    capabilities: Set[str]  # gpu, ssl, network
    last_updated: datetime
    hash: str  # for cache validation
```

**Tool Capability**:
```python
@dataclass
class ToolCapability:
    name: str
    available: bool
    version: Optional[str]
    path: Optional[str]
    fallback: Optional[str]  # alternative tool if unavailable
    min_version: Optional[str]  # minimum required version
```

### 2. Capability Detector

**Location**: `thegent/platform/detector.py`

**Responsibilities**:
- Detect OS, architecture, Python version
- Probe for tools (rg, fd, jq, docker, etc.) via which/where
- Check environment variables, paths
- Measure available memory, disk space
- Detect hardware (GPU, special features)
- Cache results with TTL (default: 1 hour)

**Detection Strategy**:
```python
class CapabilityDetector:
    def detect_platform(self) -> PlatformCapabilities:
        """Comprehensive detection with fallbacks"""
        platform_caps = PlatformCapabilities(
            os_type=self._detect_os(),
            arch=platform.machine(),
            python_version=platform.python_version(),
            tools=self._detect_tools(),  # runs in parallel
            env_vars=self._safe_env_vars(),
            max_concurrent_processes=os.cpu_count() or 4,
            available_memory_mb=self._detect_memory(),
            disk_free_mb=self._detect_disk(),
            container_runtime=self._detect_container(),
            capabilities=self._detect_capabilities(),
            last_updated=datetime.now(),
        )
        platform_caps.hash = hashlib.sha256(json.dumps(asdict(platform_caps), default=str).encode()).hexdigest()
        return platform_caps
```

**Tool Detection**:
- Fast path: Check PATH (avoid spawning subprocess if possible)
- Fallback: Use `which` (Unix) or `where` (Windows)
- Version extraction: Run tool with `--version` flag
- Timeout: 1s per tool (fail gracefully if slow)
- Parallelization: Detect tools concurrently to minimize total time

### 3. Platform Constraints

**Location**: `thegent/platform/constraints.py`

**Agent/Task Declaration**:
```yaml
# In agent definition or task prompt
platforms:
  supported: [darwin, linux]  # exclude windows
  required_tools: [rg, fd, jq]
  min_memory_mb: 512
  requires_container: false
  requires_gpu: false
  requires_network: true

fallback_strategy:
  unavailable_tools:
    rg: grep  # if rg unavailable, use grep instead
    fd: find
    jq: python json module
  degraded_mode: reduced_parallelism  # if memory < threshold
```

**Constraint Matching**:
```python
def matches_constraints(caps: PlatformCapabilities, constraints: PlatformConstraints) -> MatchResult:
    """Check if platform satisfies task constraints"""
    errors = []
    warnings = []

    # Check OS
    if caps.os_type not in constraints.supported:
        errors.append(f"OS {caps.os_type} not supported")

    # Check tools
    for tool in constraints.required_tools:
        if tool not in caps.tools or not caps.tools[tool].available:
            if tool in constraints.fallback_strategy.unavailable_tools:
                warnings.append(f"Tool {tool} unavailable, using fallback")
            else:
                errors.append(f"Required tool {tool} not found")

    # Check memory
    if caps.available_memory_mb < constraints.min_memory_mb:
        if constraints.degraded_mode:
            warnings.append(f"Memory low, degrading to {constraints.degraded_mode}")
        else:
            errors.append(f"Insufficient memory: {caps.available_memory_mb}MB < {constraints.min_memory_mb}MB")

    return MatchResult(
        matches=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        fallback_applied=constraints.fallback_strategy if warnings else None,
    )
```

### 4. Dispatch Logic

**Location**: `thegent/platform/dispatcher.py`

**Dispatch Algorithm**:
```python
class PlatformDispatcher:
    def dispatch(self, task: Task, available_executors: List[ExecutorInfo]) -> DispatchDecision:
        """Select best-fit executor for task"""

        candidates = []

        for executor in available_executors:
            caps = self.registry.get_capabilities(executor.platform_id)
            match = matches_constraints(caps, task.platform_constraints)

            if not match.errors:
                score = self._score_executor(executor, caps, task)
                candidates.append((executor, score, match.warnings))

        if not candidates:
            return DispatchDecision(
                success=False,
                reason="No compatible executor found",
                diagnostics=self._suggest_fixes(task, available_executors),
            )

        # Sort by score: full match > fallback available > degraded
        best_executor, score, warnings = max(candidates, key=lambda x: x[1])

        return DispatchDecision(
            success=True, executor=best_executor, warnings=warnings, fallback_strategy=match.fallback_applied
        )

    def _score_executor(self, executor, caps, task) -> float:
        """Score: 100 = perfect, 50 = fallback, 0 = degraded"""
        score = 100.0

        # Penalize fallbacks
        if executor.has_fallbacks:
            score -= 30

        # Penalize degraded mode
        if executor.in_degraded_mode:
            score -= 40

        # Bonus for excess capacity
        excess_memory = caps.available_memory_mb - task.platform_constraints.min_memory_mb
        if excess_memory > 1024:
            score += 10

        return score
```

### 5. Fallback Strategies

**Unavailable Tool Substitution**:
| Tool | Priority 1 | Priority 2 | Note |
|------|-----------|-----------|------|
| `rg` (ripgrep) | `grep` | N/A | Always available on Unix |
| `fd` | `find` | N/A | Always available on Unix |
| `jq` | `python -m json.tool` | custom parser | JSON manipulation |
| `docker` | `podman` | None | Container management |
| `git` | Fail loudly | N/A | Required; no substitute |

**Degraded Modes**:
- **`reduced_parallelism`**: Reduce concurrent processes if memory < threshold
- **`single_threaded`**: Run serially if CPU-bound constraints tight
- **`readonly`**: Disable write operations in read-only mode
- **`network_offline`**: Disable external calls if network unavailable

**Graceful Handling**:
```python
def execute_with_fallback(task: Task, executor: ExecutorInfo, fallback_strategy: FallbackStrategy) -> ExecutionResult:
    """Execute task with fallback handling"""

    try:
        # Attempt execution with requested tools
        return executor.execute(task)

    except ToolNotFoundError as e:
        tool_name = e.tool
        if tool_name in fallback_strategy.unavailable_tools:
            substitute = fallback_strategy.unavailable_tools[tool_name]
            logging.warning(f"Tool {tool_name} not found, using {substitute}")

            # Inject substitute and retry
            modified_task = task.replace_tool(tool_name, substitute)
            return executor.execute(modified_task)
        else:
            raise

    except InsufficientResourceError as e:
        if fallback_strategy.degraded_mode:
            logging.warning(f"Degrading to {fallback_strategy.degraded_mode}")
            task.degraded_mode = fallback_strategy.degraded_mode
            return executor.execute(task)
        else:
            raise
```

---

## Data Structures

### PlatformConstraints (YAML/JSON)
```json
{
  "platforms": {
    "supported": ["darwin", "linux"],
    "required_tools": ["rg", "fd"],
    "min_memory_mb": 512,
    "requires_container": false,
    "requires_gpu": false,
    "requires_network": false,
    "architecture": ["x86_64", "arm64"]
  },
  "fallback_strategy": {
    "unavailable_tools": {
      "rg": "grep",
      "fd": "find"
    },
    "degraded_mode": "reduced_parallelism"
  },
  "execution_hints": {
    "prefer_local": true,
    "max_retries": 3
  }
}
```

---

## Integration Points

### 1. CLI Commands
```bash
# Show platform capabilities
thegent platform detect

# Show registry (cached)
thegent platform registry

# Refresh capabilities
thegent platform detect --refresh

# Validate task constraints
thegent platform validate-task <task-id>

# Dispatch simulation (dry-run)
thegent platform dispatch-sim <task> --executors <executor-list>
```

### 2. MCP Tools
- `thegent://platform/detect` — Get current platform capabilities
- `thegent://platform/registry` — Access capability cache
- `thegent://platform/constraints` — Declare task constraints

### 3. Agent Declarative API
```python
# In agent skill or task
from thegent.platform import PlatformConstraint, fallback


@PlatformConstraint(
    supported_platforms=["darwin", "linux"],
    required_tools=["rg", "fd"],
    min_memory_mb=512,
    fallbacks={"rg": "grep", "fd": "find"},
)
def my_agent_task():
    pass
```

---

## Error Handling & Diagnostics

**Diagnostic Output**:
```
DISPATCH FAILED: Cannot find compatible executor for task "audit-security"

Constraints:
  • Supported platforms: darwin, linux
  • Required tools: semgrep, gosec
  • Min memory: 2048 MB

Available executors:
  1. macOS (darwin/x86_64) – MATCH, but semgrep not found (fallback available)
  2. Linux (linux/x86_64) – FAILED: gosec not found (no fallback)
  3. Windows (win32/x86_64) – FAILED: platform not supported

Suggestions:
  • Install semgrep on macOS (brew install semgrep)
  • Install gosec on Linux (apt-get install gosec)
  • Remove Windows from execution pool, or declare windows support
```

---

## Testing Strategy

### Unit Tests
- Platform detection on mocked environments
- Constraint matching algorithm with edge cases
- Dispatch scoring and selection logic
- Fallback strategy application

### Integration Tests
- Multi-platform CI matrix (macOS, Linux, Windows)
- Real tool detection (rg, fd, docker, etc.)
- End-to-end dispatch with actual executors

### Scenario Tests
- All tools available → perfect dispatch
- One tool missing → fallback applied, task succeeds
- Multiple tools missing → degraded mode or failure
- Memory exhausted → degraded or failure
- Network unavailable → offline mode or failure

---

## Rollout Plan

### Phase 1: Core (Week 1)
- [ ] Implement capability detector
- [ ] Build platform registry (in-memory + disk cache)
- [ ] Add constraint matching and fallback logic

### Phase 2: Integration (Week 2)
- [ ] Wire dispatch into `thegent run` and `thegent bg`
- [ ] Add CLI commands (`thegent platform *`)
- [ ] Expose MCP tools

### Phase 3: Verification (Week 3)
- [ ] Multi-platform CI matrix setup
- [ ] Documentation and agent guide
- [ ] Knowledge transfer and backlog closure

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Detection overhead (slow startup) | Medium | Low | Cache with TTL; lazy detection on first use |
| False negatives (tool detected but broken) | Low | Medium | Version validation; smoke tests on dispatch |
| Platform-specific quirks | Medium | Medium | Comprehensive test matrix; community feedback |
| Configuration complexity | Medium | Low | Sensible defaults; decorator API |

---

## Success Metrics

- [ ] Dispatch decision made in <100ms (p95)
- [ ] Zero manual platform workarounds in CI/CD
- [ ] 100% of agents declare platform constraints
- [ ] 95%+ dispatch success rate on multi-platform matrix
- [ ] Fallback strategies cover 80%+ of common tool unavailability scenarios
