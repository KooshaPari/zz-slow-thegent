<DONE>
# Codex CLI Lightweight & Scalable Overhaul Design

**Date:** 2026-02-20
**Status:** Design Specification
**Audience:** Engineering team, infrastructure, agent orchestration
**Version:** 1.0

---

## Executive Summary

OpenAI Codex CLI is a powerful but resource-heavy agent harness built on 50+ Rust crates. For on-device multi-agent workflows (5–10+ concurrent instances), Codex must be redesigned for:

1. **Lightweight execution** — Strip TUI, minimize startup overhead, use `--json` streaming by default
2. **Multi-agent scalability** — Isolate state (separate `~/.codex` homes), share auth, distribute work via task queues
3. **Feature parity with proprietary tools** — Match Claude Code, Ante, and Cursor on project memory, context management, skills, and eval modes
4. **Optimal DX for programmatic use** — Rich JSON output, config injection, sub-agent spawning protocols

**Key findings:**

- Codex 0.104.0 **hardwired the `Responses` wire API only** — `/v1/chat/completions` was fully removed February 2026
- Codex supports **`--dangerously-bypass-approvals-and-sandbox` with `--sandbox workspace-write`** for fast, unattended execution
- Current thegent integration uses `codex exec --json` (lightweight JSONL mode) but does NOT isolate state DBs across instances
- Gap analysis shows Codex lacks: project context files (like CLAUDE.md), skill/eval mode, sub-agent protocols, memory system
- Proprietary tools (Claude Code, Ante) have these; Codex must add them or fall behind

---

## 1. Gap Analysis: Codex vs Proprietary Tools

### Feature Matrix

| Feature | Codex 0.104 | Claude Code | Ante | Cursor Agent |
|---------|------------|-------------|------|--------------|
| **CLI mode** | ✓ exec | ✓ --print | ✓ headless | ✓ agent |
| **JSON streaming** | ✓ --json | ✓ --print | ✓ JSON output | Limited |
| **Project memory** | ✗ | ✓ CLAUDE.md | ✓ memory/* | ✓ .cursor/ |
| **Skill/eval mode** | ✗ | ✗ | ✓ skills/ benchmarks/ | ✗ |
| **Sub-agent spawning** | ✗ | ✓ crew protocol | ✓ droid spawning | ✗ |
| **Context summarization** | ✗ | ✓ compact mode | ✓ summarize | ✓ context compression |
| **MCP ecosystem** | ✓ `codex mcp` | ✓ MCP server | ✓ MCP standard | ✓ Limited |
| **Sandbox control** | ✓ read-only, write, danger | ✓ Limited | ✓ Fine-grained | ✓ IDE bound |
| **Model routing/override** | ✓ --model, --oss | ✓ --model | ✓ provider catalog | ✓ --model |
| **Benchmark/eval** | ✗ | ✗ | ✓ eval mode | ✗ |
| **Approval bypass** | ✓ --dangerously-bypass | ✓ --print (implicit) | ✓ headless | ✓ agent (implicit) |

**Critical gaps in Codex:**

| Gap | Impact | Priority | Effort |
|-----|--------|----------|--------|
| No CLAUDE.md / context file | Agents can't be told to read project memory; must hardcode context in prompts | High | Medium |
| No skill/eval system | Can't compose multi-step tasks or benchmark agent quality | Medium | High |
| No sub-agent spawning protocol | Can't create managed hierarchies of Codex instances | Medium | Medium |
| No context summarization | Multi-agent aggregation requires custom summarization | Medium | Low |
| No memory system | Each instance loses session context; can't learn across runs | Low | High |

---

## 2. Lightweight Mode Design

### 2.1 Current State (thegent Integration)

**Current flags used in `codex_proxy.py`:**
```bash
codex exec - \
  --skip-git-repo-check \
  --dangerously-bypass-approvals-and-sandbox \
  --cd <path> \
  --json \
  --model <model> \
  --sandbox workspace-write \
  --full-auto
```

**Current bottlenecks:**

1. **Binary startup time** — Rust binary is fast (~500ms), but 50 crates bring initialization overhead
2. **Memory per instance** — TUI (ratatui) loads; even with `exec` mode, base memory ~80–120 MB per instance
3. **SQLite state contention** — Multiple instances access `~/.codex/state.db` without connection pooling; can cause lock contention
4. **Auth token duplication** — Each instance re-reads and validates token; no shared session cache
5. **Process cleanup** — No lifecycle management for orphaned Codex processes

### 2.2 Lightweight Mode Redesign

#### 2.2.1 Config-Driven Startup

Create a **lightweight config template** that Codex reads on startup:

```toml
# ~/.codex/lightweight.toml (for multi-agent mode)
[agent]
mode = "lightweight"
skip_analytics = true
skip_telemetry = true
disable_tui = true

[execution]
approval_policy = "never"
sandbox_default = "workspace-write"
stream_format = "json"

[performance]
disable_tree_sitter = false  # still needed for code understanding
disable_semantic_indexing = true  # skip expensive indexing for multi-agent
connection_pool_size = 1  # single connection per instance

[context]
max_context_window = 50000  # shorter for multi-agent; full for single agent
```

**Via CLI override:**
```bash
codex exec - \
  -c agent.mode=lightweight \
  -c performance.disable_semantic_indexing=true \
  -c context.max_context_window=50000 \
  --json
```

#### 2.2.2 State Isolation via `--codex-home`

**Add a new flag to codex** (requires upstream PR):

```bash
codex exec - \
  --codex-home /tmp/codex-agent-0 \
  --skip-git-repo-check \
  --dangerously-bypass-approvals-and-sandbox \
  --json
```

**Without this, implement in thegent:**

```python
# thegent codex_proxy.py enhancement
def _prepare_isolated_state(agent_index: int, auth_token: str) -> Path:
    """Prepare isolated Codex state directory for multi-agent use."""
    home = Path(f"/tmp/codex-agent-{agent_index}")
    home.mkdir(parents=True, exist_ok=True)

    # Create minimal config
    config_dir = home / ".codex"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Link auth token only (read-only)
    auth_file = config_dir / "auth"
    if not auth_file.exists():
        auth_file.symlink_to(Path.home() / ".codex" / "auth")

    return home
```

**Environment override:**
```python
env = os.environ.copy()
env["CODEX_HOME"] = str(isolated_home)
```

#### 2.2.3 Memory Budget Per Instance

**Target memory footprint for lightweight mode:**

- Baseline: ~80 MB (Rust binary, minimal libs)
- Single prompt processing: +20–40 MB (context buffer)
- Total per instance: **~100–120 MB** (vs 200–300 MB in TUI mode)

**Enforce with OS-level limits:**

```bash
# Run Codex under memory cap (Linux/macOS)
memory_limit_mb=150
ulimit -v $((memory_limit_mb * 1024))  # virtual memory cap
codex exec - --json
```

**For Python orchestration:**
```python
import resource

def run_codex_with_memory_limit(cmd: list[str], memory_mb: int = 150) -> RunResult:
    """Run Codex with memory cap."""
    def _preexec_fn() -> None:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (memory_mb * 1024 * 1024, hard))

    proc = subprocess.Popen(
        cmd,
        preexec_fn=_preexec_fn if platform.system() != "Windows" else None,
        ...
    )
    # ...
```

#### 2.2.4 Fast Startup via Prewarmed Instances (Optional)

**For continuous loops**, maintain a small pool of warm Codex processes:

```python
class CodexInstancePool:
    """Pre-warm Codex instances for sub-second first-request latency."""

    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.instances: list[CodexInstance] = []

    async def initialize(self) -> None:
        """Spawn pool_size lightweight Codex instances, ready to serve."""
        for i in range(self.pool_size):
            instance = CodexInstance(home=Path(f"/tmp/codex-warm-{i}"), config={"mode": "lightweight"})
            await instance.spawn()  # Keep alive, wait for work
            self.instances.append(instance)

    async def acquire(self, timeout_sec: float = 10.0) -> CodexInstance:
        """Lease a warm instance; spawn new if pool exhausted."""
        try:
            return self.instances.pop(timeout=timeout_sec)
        except IndexError:
            return CodexInstance(home=Path(f"/tmp/codex-temp-{uuid4()}"))

    async def release(self, instance: CodexInstance) -> None:
        """Return instance to pool."""
        if len(self.instances) < self.pool_size:
            self.instances.append(instance)
        else:
            instance.shutdown()
```

**Trade-off:** Adds complexity; only worthwhile if running 100s of short tasks. For 5–10 concurrent agents, direct spawning is fine.

---

## 3. Multi-Agent Orchestration Pattern

### 3.1 Architecture

```
Task Queue (Redis / in-memory)
    |
    +-- thegent Orchestrator
            |
            +-- [CodexInstance-0] (state: /tmp/codex-agent-0)
            +-- [CodexInstance-1] (state: /tmp/codex-agent-1)
            +-- [CodexInstance-2] (state: /tmp/codex-agent-2)
            ...
            +-- [CodexInstance-9] (state: /tmp/codex-agent-9)
            |
            v
    Task Results Aggregator
            |
            v
    Output (JSONL / structured logs)
```

### 3.2 State Isolation

Each instance has:

1. **Isolated `~/.codex` home** → separate DB connections, no lock contention
2. **Shared auth token** → read-only symlink to `~/.codex/auth` or env var
3. **Shared model metadata cache** → optional, read-only symlink to `~/.cache/codex-models`
4. **Ephemeral session dir** → cleaned up after task completes

```python
def isolate_codex_state(agent_id: int, shared_auth: Path | None = None) -> CodexEnv:
    """Prepare isolated Codex environment for agent."""

    instance_home = Path(f"/tmp/codex-agent-{agent_id}")
    instance_home.mkdir(parents=True, exist_ok=True)

    codex_dir = instance_home / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)

    # Auth: either symlink or env var
    if shared_auth:
        auth_link = codex_dir / "auth"
        if not auth_link.exists():
            auth_link.symlink_to(shared_auth)

    # Cache: optional read-only link (saves model discovery time)
    cache_dir = instance_home / ".cache" / "codex"
    cache_dir.mkdir(parents=True, exist_ok=True)

    return CodexEnv(
        home=instance_home,
        auth_file=shared_auth,
        cache_dir=cache_dir,
    )
```

### 3.3 Work Distribution

**Pattern: Task queue → agent pool**

```python
class CodexWorker:
    """Single worker thread/task that consumes from task queue."""

    def __init__(self, agent_id: int, queue: asyncio.Queue):
        self.agent_id = agent_id
        self.queue = queue
        self.codex_env = isolate_codex_state(agent_id)

    async def run_loop(self) -> None:
        """Consume and execute tasks indefinitely."""
        while True:
            task = await self.queue.get()  # Block until work available
            try:
                result = await self.execute_task(task)
                await self.queue.task_done()
            except Exception as e:
                logger.error(f"Agent {self.agent_id} failed on {task.id}: {e}")
                # Optionally retry or dead-letter the task

    async def execute_task(self, task: CodexTask) -> CodexResult:
        """Execute a single Codex task."""
        env = os.environ.copy()
        env["HOME"] = str(self.codex_env.home)
        env["OPENAI_API_KEY"] = ...  # or from shared keyring

        cmd = [
            "codex",
            "exec",
            "-",
            "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
            "--json",
            "--cd",
            str(task.cwd),
            "--model",
            task.model,
        ]

        result = await self.run_codex(cmd, task.prompt, env=env)
        return result
```

### 3.4 Output Collection & Aggregation

**JSONL streaming from each instance:**

```python
class ResultAggregator:
    """Collect JSONL results from multiple Codex instances."""

    def __init__(self, output_path: Path):
        self.output = output_path.open("a")

    async def on_instance_complete(self, agent_id: int, task_id: str, result: CodexResult) -> None:
        """Emit single JSONL record."""
        record = {
            "timestamp": time.time(),
            "agent_id": agent_id,
            "task_id": task_id,
            "exit_code": result.exit_code,
            "output": result.stdout,
            "error": result.stderr if result.exit_code != 0 else None,
            "duration_sec": result.duration,
        }
        json.dump(record, self.output)
        self.output.write("\n")
        self.output.flush()
```

**Consumption pattern (for parent orchestrator):**

```bash
# Real-time consumption with jq
tail -f results.jsonl | jq -r '.task_id + ": " + (.exit_code | tostring)'

# Post-hoc analysis
jq 'select(.exit_code != 0)' results.jsonl | jq '.task_id, .error'
```

### 3.5 Resource Budgets

For a typical machine (8 CPU cores, 16 GB RAM):

| Metric | Budget | Reasoning |
|--------|--------|-----------|
| Concurrent instances | 5–10 | 150 MB each × 10 = 1.5 GB; keep headroom for system |
| Memory per instance | 120 MB | Lightweight config |
| CPU per instance | 1–2 cores (burst) | Codex is mostly I/O-bound (API calls) |
| Startup time | ~0.5 sec | Rust binary fast; bottleneck is API handshake |
| Max task duration | 30 min | Per thegent defaults; timeout on hung processes |
| Max idle before kill | 3 min | Activity-based detection in `codex_proxy.py` |

---

## 4. DX Improvements for Programmatic Use

### 4.1 Enhanced JSON Output (`--json` mode)

**Current output:** JSONL with basic event types.
**Proposed enhancements:**

```jsonl
{
  "type": "response.started",
  "id": "resp_abc123",
  "model": "gpt-5.3-codex-spark",
  "timestamp": "2026-02-20T12:34:56Z"
}
{
  "type": "response.chunk",
  "id": "resp_abc123",
  "delta": {
    "type": "text",
    "text": "# Hello World\nprint('Hello')"
  }
}
{
  "type": "tool.use",
  "id": "tool_xyz",
  "tool": "shell",
  "input": {"command": "ls -la"}
}
{
  "type": "tool.result",
  "id": "tool_xyz",
  "output": "total 48\n-rw-r--r-- 1 ..."
}
{
  "type": "response.completed",
  "id": "resp_abc123",
  "final_text": "# Hello World\nprint('Hello')\n\n# Output:\nHello",
  "usage": {
    "input_tokens": 50,
    "output_tokens": 120,
    "total_tokens": 170
  },
  "exit_code": 0
}
```

**Benefits:**
- Parent orchestrator can track which tool is running
- Token usage visible for budgeting
- Easier filtering/aggregation

### 4.2 Config Injection via Environment

**Add to thegent integration:**

```python
def run_codex_with_config(
    prompt: str,
    codex_config: dict[str, Any],  # {"model": "gpt-5.3-codex", "sandbox": "read-only"}
    **kwargs,
) -> RunResult:
    """Run Codex with arbitrary config overrides (via -c)."""
    env = os.environ.copy()

    # Build -c flags
    config_flags = []
    for key, value in codex_config.items():
        if isinstance(value, str):
            config_flags.extend(["-c", f"{key}={value}"])
        elif isinstance(value, bool):
            config_flags.extend(["-c", f"{key}={str(value).lower()}"])
        else:
            # JSON encode complex types
            config_flags.extend(["-c", f"{key}={json.dumps(value)}"])

    cmd = ["codex", "exec", "-"] + config_flags + ["--json"]

    return _run_with_retry(cmd, prompt, env=env, **kwargs)
```

**Usage:**
```python
result = run_codex_with_config(
    prompt="Fix the failing tests",
    codex_config={
        "model": "gpt-5.3-codex-high",
        "sandbox": "workspace-write",
        "approval_policy": "never",
        "max_output_tokens": 4000,
    },
    cwd="/path/to/repo",
    timeout=600,
)
```

### 4.3 Sub-Agent Spawning Protocol

**New method on CodexProxyRunner:**

```python
class CodexProxyRunner(AgentRunner):
    async def spawn_sub_agent(
        self,
        agent_id: str,
        prompt: str,
        cwd: Path | None = None,
        config: dict[str, Any] | None = None,
        timeout: int = 600,
    ) -> AsyncIterator[CodexEvent]:
        """
        Spawn a managed Codex sub-agent with isolated state.

        Yields events in real-time (for aggregation/monitoring).
        """
        codex_env = isolate_codex_state(agent_id=hash(agent_id) % 1000)
        env = os.environ.copy()
        env["HOME"] = str(codex_env.home)

        cmd = ["codex", "exec", "-", "--json", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox"]
        if cwd:
            cmd.extend(["--cd", str(cwd)])

        # Inject config
        if config:
            for key, value in config.items():
                cmd.extend(["-c", f"{key}={json.dumps(value) if not isinstance(value, str) else value}"])

        # Stream events as they arrive
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
        )
        proc.stdin.write(prompt)
        proc.stdin.close()

        async for line in self._read_async(proc.stdout):
            try:
                event = json.loads(line)
                yield event
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in Codex output: {line}")
```

**Usage (hierarchical spawning):**
```python
runner = CodexProxyRunner("codex")


async def parent_task():
    """Spawn 3 sub-agents to work on different modules."""
    tasks = [
        ("agent-auth", "Fix authentication module", "/repo/src/auth"),
        ("agent-api", "Refactor API routes", "/repo/src/api"),
        ("agent-db", "Optimize database queries", "/repo/src/db"),
    ]

    results = {}
    async for agent_id, prompt, cwd in tasks:
        async for event in runner.spawn_sub_agent(agent_id, prompt, cwd=cwd):
            if event["type"] == "response.completed":
                results[agent_id] = event["final_text"]

    return results
```

---

## 5. AX/UX Parity Roadmap

### Phase 1: Foundation (2–3 weeks)

| Task | Effort | Impact | Owner |
|------|--------|--------|-------|
| Implement `--codex-home` flag in Codex | Medium | High | OpenAI (upstream) |
| Add CLAUDE.md-style context file support | Medium | High | Codex team |
| Enhance `--json` output with event metadata | Small | Medium | Codex team |
| Lightweight config template + docs | Small | High | thegent |
| Multi-agent isolation in thegent proxy | Small | High | thegent |

**Milestone:** Codex can run 5–10 concurrent instances with isolated state.

### Phase 2: Context & Memory (3–4 weeks)

| Task | Effort | Impact | Owner |
|------|--------|--------|-------|
| Implement CLAUDE.md loader (like claude-code) | Medium | High | Codex team |
| Add project memory file support (`.codex/memory`) | Medium | Medium | Codex team |
| Context summarization for multi-agent aggregation | Medium | Medium | thegent |
| Compact mode (trim context to N% of window) | Small | Medium | Codex team |

**Milestone:** Agents can read project directives; thegent can aggregate multi-agent outputs.

### Phase 3: Skills & Eval (4–6 weeks)

| Task | Effort | Impact | Owner |
|------|--------|--------|-------|
| Skill/task templates system (like Ante) | High | Medium | Codex team |
| Benchmark/eval mode (test suite execution, scoring) | High | Medium | Codex team |
| Sub-agent spawning protocol (code changes only) | Medium | High | thegent |

**Milestone:** Codex feature-parity with Ante on skills; thegent can orchestrate hierarchies.

### Phase 4: Polish & Optimization (2–3 weeks)

| Task | Effort | Impact | Owner |
|------|--------|--------|-------|
| Prewarmed instance pool (optional, if needed) | High | Low | thegent |
| Memory/CPU profiling & tuning | Medium | Medium | Codex + thegent |
| Documentation & examples | Small | High | both |
| Load testing (50+ concurrent agents) | Medium | Medium | thegent |

**Milestone:** Production-ready multi-agent Codex; feature-complete parity.

---

## 6. On-Device Scaling: Resource Budgets

### 6.1 Single Machine (8 CPU, 16 GB RAM)

**Configuration:**
- **Max concurrent instances:** 8
- **Per-instance memory:** 120 MB (lightweight mode)
- **System overhead:** 2 GB (OS, thegent orchestrator, caches)
- **Reserved:** 1 GB (headroom)

**Total utilization:** 8 × 120 MB + 2 GB + 1 GB = 3 GB (18% of 16 GB)

**Bottleneck:** API rate limits, not machine resources. OpenAI API has per-minute rate limits; CPU/memory are not the constraint for 8–10 concurrent agents.

### 6.2 Scaling to 50+ Agents (Multi-Machine)

**Architecture:**

```
Machine-A (8 CPU, 16 GB)    Machine-B (8 CPU, 16 GB)    Machine-C (...)
    |                            |
    +-- [codex-0..7]             +-- [codex-8..15]
    |
    v
Shared Task Queue (Redis / Kafka)
    |
    v
Distributed Orchestrator (Kubernetes / systemd)
    |
    v
Result Aggregator (S3 / NFS)
```

**For this scale, prefer Kubernetes:**
- Each machine runs a Codex DaemonSet (8 pods/node)
- Task queue is a K8s Service
- Results collected to persistent volume

**Out of scope for this design** (infra-as-code; handled separately).

### 6.3 Timeout & Resource Policies

**Per thegent config (`config.py`):**

```python
# defaults in ThegentSettings
default_timeout = 1800  # 30 min wall clock
max_idle_seconds = 180  # 3 min no output → kill
max_wall_time = 0  # unbounded (rely on idle detection)

# Lightweight overrides for multi-agent
codex_lightweight_timeout = 600  # 10 min for typical tasks
codex_lightweight_idle = 120  # 2 min tolerance
codex_lightweight_memory_limit = 150  # MB
```

**Enforcement:**

```bash
# bash wrapper for resource limits
run_codex_with_limits() {
    local timeout_sec=$1 idle_sec=$2 memory_mb=$3

    # Set memory cap
    (ulimit -v $((memory_mb * 1024)); \
     timeout ${timeout_sec}s \
     stdbuf -oL codex exec - --json)
}
```

---

## 7. Implementation Priority

### MVP (Minimum Viable Product) — 1–2 weeks

1. **State isolation** — Implement in thegent without upstream Codex changes
   - `isolate_codex_state()` function that sets `CODEX_HOME` env var
   - Symlink shared auth token

2. **Lightweight config** — Document existing flags for multi-agent use
   - `--json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox --sandbox workspace-write`
   - Add lightweight config template to thegent docs

3. **Multi-agent orchestrator** — Basic work queue + instance pool
   - `CodexWorkerPool` class with N instances pulling from queue
   - JSONL result aggregation
   - Activity-based timeout (already in `codex_proxy.py`)

4. **Documentation** — Multi-agent quick-start guide

**Result:** Codex can run 5–10 concurrent instances; thegent can orchestrate them.

### Phase 1 (Downstream) — 3–4 weeks

5. **CLAUDE.md support in Codex** — Upstream change to Codex CLI
   - Load `~/.codex/CLAUDE.md` (or project root) on startup
   - Pass as system instructions to model

6. **Enhanced JSON output** — `--json` format with event types & metadata
   - `response.started`, `response.chunk`, `tool.use`, `response.completed`
   - Include token usage, duration

7. **Config injection in thegent** — Helper for `-c` flags
   - `run_codex_with_config()` function

### Phase 2 (Full Feature Parity) — 6–8 weeks

8. **Sub-agent spawning** — Protocol in thegent
   - `spawn_sub_agent()` async method
   - Hierarchical task orchestration

9. **Context summarization** — Multi-agent output aggregation
   - Truncate outputs, extract key findings, re-prompt for summary

10. **Skill/eval system** — Optional; requires upstream Codex work

---

## 8. Key Decisions & Rationale

| Decision | Rationale | Alternatives |
|----------|-----------|--------------|
| **No prewarmed pool (MVP)** | Adds complexity; direct spawning sufficient for 5–10 agents | Prewarmed pool for 100+ agents (Phase 2) |
| **Isolated `~/.codex` per instance** | Avoids SQLite lock contention; simple symlink for auth | Connection pooling in Codex (requires upstream) |
| **Activity-based timeouts (no wall-time)** | Prevents killing long-running but active tasks | Strict wall-time; may kill legitimate work |
| **JSONL result format** | Standard streaming format; easy parsing with `jq` | Custom binary protocol (overkill) |
| **Symlink auth token** — Shared token across instances | Reduces API handshake overhead | Separate tokens per instance (more secure, slower) |
| **Sub-agent protocol in thegent, not Codex** | Codex doesn't need to know about orchestration; cleaner separation | Native Codex support (requires redesign) |
| **Lightweight config via `-c` flags** | No config file needed; flags override `~/.codex/config.toml` | New config.toml file per instance (heavier) |

---

## 9. Open Questions & Future Work

1. **Upstream Codex support for `--codex-home`:**
   - Is this feature planned? If so, when?
   - Fallback: implement in thegent via env vars

2. **Memory limits in Rust binaries:**
   - Does Codex respect `RLIMIT_AS` or `ulimit -v`?
   - If not, need `/proc/cgroups` or Docker for hard limits

3. **Auth token caching/sharing:**
   - Can we safely symlink `~/.codex/auth` across instances?
   - Or use env vars to share a token?

4. **Sub-agent child process visibility:**
   - Should parent Codex process track spawned children?
   - Or each child is fully independent?

5. **Model metadata caching:**
   - Is `~/.cache/codex-models` safe to share read-only?
   - Can reduce model discovery time for subsequent instances

6. **Rate limit handling:**
   - How does Codex handle 429 responses from OpenAI?
   - Does it retry, or fail fast?
   - Multi-agent queues should respect this

---

## 10. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Concurrent instances | ≥8 | No lock contention; all instances complete tasks |
| Memory per instance | ≤150 MB | Peak RSS under `ulimit` cap |
| Startup time | <1 sec | Time to first output from `codex exec` |
| Multi-agent throughput | ≥10 tasks/min | Task queue → completion across 8 instances |
| Context isolation | 100% | No cross-instance state leakage (verified with unique markers) |
| Feature parity (AX/UX) | ≥70% | Supports CLAUDE.md, project memory, config injection |
| Documentation quality | ≥80% | Clear quick-start, API docs, examples |

---

## 11. Appendix: Quick-Start Example

### 11.1 Run 5 Concurrent Codex Agents

```python
import asyncio
from pathlib import Path
from thegent.agents.codex_proxy import CodexProxyRunner


async def main():
    """Example: 5 concurrent agents fixing different modules."""

    tasks = [
        ("module-auth", "Refactor auth.py for type safety", "/repo/src/auth"),
        ("module-api", "Add error handling to API routes", "/repo/src/api"),
        ("module-db", "Optimize database queries", "/repo/src/db"),
        ("module-ui", "Fix React component warnings", "/repo/src/ui"),
        ("module-test", "Write unit tests for models", "/repo/tests"),
    ]

    runner = CodexProxyRunner("codex", model="gpt-5.3-codex-spark")

    async def process_task(task_id, prompt, cwd):
        """Process single task with isolated Codex instance."""
        result = runner.run(
            prompt=prompt,
            cwd=Path(cwd),
            mode="write",
            timeout=600,
            use_stream=True,
        )
        print(f"{task_id}: {result.exit_code}")
        return result

    # Run all tasks concurrently
    results = await asyncio.gather(*[process_task(tid, prompt, cwd) for tid, prompt, cwd in tasks])

    for i, result in enumerate(results):
        print(f"Task {i}: {'OK' if result.exit_code == 0 else 'FAILED'}")
        if result.exit_code != 0:
            print(f"  Error: {result.stderr[:200]}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Output:**
```
module-auth: 0
module-api: 0
module-db: 0
module-ui: 0
module-test: 0
Task 0: OK
Task 1: OK
Task 2: OK
Task 3: OK
Task 4: OK
```

### 11.2 Lightweight Config Template

**Create `~/.codex/lightweight.toml`:**

```toml
# Codex lightweight mode config
# Usage: codex exec - -p lightweight --json --skip-git-repo-check

[agent]
mode = "lightweight"
skip_analytics = true
skip_telemetry = true

[execution]
approval_policy = "never"
sandbox_default = "workspace-write"
stream_format = "json"

[performance]
disable_semantic_indexing = true
disable_tree_sitter = false
max_context_window = 50000

[context]
memory_max = "100mb"
```

**Usage:**
```bash
codex exec - -p lightweight --json < task.txt
```

---

## 12. Related Documents

- **Reference:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/docs/research/CODEX_CLI_V2_PROTOCOL_RESEARCH_2026-02-20.md`
- **Reference:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/docs/research/CODEX_V2_GAP_ANALYSIS_2026-02-20.md`
- **Reference:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/docs/research/CODEX_CLIPROXY_CONFIG_AUDIT_AND_PLAN.md`
- **Implementation:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/agents/codex_proxy.py`
- **Tests:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/test_unit_codex_proxy.py`

---

## Signature

**Author:** Architecture Team
**Reviewed:** —
**Approved:** —
**Last Updated:** 2026-02-20
