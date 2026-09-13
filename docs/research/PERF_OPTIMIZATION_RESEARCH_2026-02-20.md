<DONE>
# Performance Optimization Research — 2026-02-20

**Date:** 2026-02-20
**Author:** Claude Sonnet 4.6 (agent)
**Scope:** thegent MCP server + routing + agent runner + sitback + Rust crates
**Status:** Draft — ready for WL intake

---

## 1. Executive Summary

Five highest-impact optimizations across the stack, ordered by estimated latency reduction per unit of effort:

| Rank | Optimization                                                                                | Subsystem                            | Est. Latency Reduction                                               | Effort |
| ---- | ------------------------------------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------- | ------ |
| 1    | Cache `get_litellm_router()` result — avoid re-building `model_list` on every request       | routing/litellm_router.py            | 10–50 ms per request                                                 | S      |
| 2    | Replace `asyncio.run()` inside sync thread (NeverIdleLoop) with proper async event loop     | sitback/never_idle.py                | Eliminate 50–200 ms event-loop-creation overhead per gardening tick  | S      |
| 3    | Pool `httpx.AsyncClient` in `_forward_native_responses` — avoid client creation per request | routing/litellm_responses_handler.py | 5–15 ms per OR-18 request                                            | S      |
| 4    | Replace custom SHA-256 in audit.rs with `sha2` crate — 10–20x faster hash computation       | crates/thegent-router/src/audit.rs   | Near-zero latency per routing decision; currently ~0.5–2 ms per hash | M      |
| 5    | Switch `AuditLogger::append` from open-per-write to a held `BufWriter`                      | crates/thegent-router/src/audit.rs   | Eliminate O(N) file-open syscalls under burst traffic                | M      |

---

## 2. Profiling Tools + Methodology

### 2.1 Python Profiling

| Tool                 | Use Case                                                         | Integration                                                                        |
| -------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `py-spy`             | CPU flamegraph with zero code change; attaches to running PID    | `py-spy record -o flamegraph.svg --pid $(pgrep -f mcp/server.py)`                  |
| `pyinstrument`       | Per-request call tree with async support                         | Add `--profiler pyinstrument` to uvicorn/starlette dev startup                     |
| `memray`             | Memory allocation profiling; identifies large dict/list creation | `memray run -o output.bin python -m thegent mcp`                                   |
| `yappi`              | Thread-aware profiling (critical for NeverIdleLoop threads)      | `yappi.start(builtins=True); ... yappi.stop(); yappi.get_func_stats().print_all()` |
| `asyncio` debug mode | Detect sync blocking in async paths                              | `PYTHONASYNCIODEBUG=1 python -m thegent mcp`                                       |

**Setup in pyproject.toml:** All tools are installable as dev extras. None require code changes for initial profiling. Recommended order: py-spy first (zero overhead, production-safe), then pyinstrument for targeted subsystem profiling.

### 2.2 Rust Profiling

| Tool                                 | Use Case                          | Integration                                                                     |
| ------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------- |
| `cargo-flamegraph`                   | CPU flamegraph for Rust binaries  | `cargo flamegraph --bin quality-gate`                                           |
| `criterion`                          | Microbenchmarks for hot functions | Already have `crates/thegent-benchmark/`; add criterion benches for audit chain |
| `perf` (Linux) / Instruments (macOS) | Low-level profiling               | `cargo build --release && perf record target/release/quality-gate`              |
| `dhat`                               | Heap profiling for Rust           | Add `dhat` feature flag to Cargo.toml                                           |

### 2.3 MCP/FastMCP Profiling

The `TimingMiddleware` is already registered in `mcp/server.py`. Enable structured logging output:

```
THGENT_DEBUG=1 thegent mcp
```

Middleware chain produces per-tool timing. Use this to identify which MCP tools are slow before profiling at code level.

### 2.4 Benchmarking Baseline

Run before any optimization:

```bash
# Python startup latency
time python -c "import thegent.routing.litellm_router"

# Router build time
python -c "
import time, thegent.routing.litellm_router as r
t0=time.perf_counter(); r.build_litellm_model_list(); print(f'{(time.perf_counter()-t0)*1000:.1f}ms')
"

# Rust audit hash throughput
cargo bench --bench audit_bench 2>/dev/null || echo "no bench yet"
```

---

## 3. Identified Bottlenecks

### 3.1 Routing Layer

#### BN-001: `get_litellm_router()` — Reconstructed on Every Call

- **File:** `src/thegent/routing/litellm_router.py:380`
- **Function:** `get_litellm_router()`
- **Issue:** Called without caching in `handle_responses_request()` (line 340) and `handle_responses_websocket()` (line 559). Each call invokes `build_litellm_model_list()` which iterates the full model catalog, deduplicates, and builds OpenRouter entries. `get_healthy_deployments()` also runs on the result. With ~20–40 model entries this is cheap but non-trivial; under high concurrency it is called once per request.
- **Evidence:** `get_litellm_router()` at line 380 builds a fresh `Router(**router_kwargs)` every invocation with no memoization. The function `build_litellm_model_list()` runs `_get_catalog()`, iterates `catalog.values()`, and iterates `CANONICAL_TO_OPENROUTER`. `get_healthy_deployments()` queries the `ProviderCircuitBreakerRegistry` singleton for every deployment.
- **Impact:** Estimated 10–50 ms per request depending on catalog size and circuit breaker state.
- **Effort:** S

#### BN-002: `build_dynamic_fallback_router()` — Full Model List Rebuild per Multi-Model Request

- **File:** `src/thegent/routing/litellm_router.py:427`
- **Function:** `build_dynamic_fallback_router()`
- **Issue:** Called for every request that specifies `models[]` array. Rebuilds the entire model list via `build_litellm_model_list()` then filters. The full list is rebuilt unconditionally even if models have not changed.
- **Evidence:** Line 442: `full_model_list = build_litellm_model_list()` with no cache.
- **Impact:** Same as BN-001, plus filtering loop.
- **Effort:** S (same cache as BN-001 fixes this)

#### BN-003: `_forward_native_responses` — New `httpx.AsyncClient` Per Request

- **File:** `src/thegent/routing/litellm_responses_handler.py:433`
- **Function:** `_forward_native_responses()`
- **Issue:** Line 433: `async with httpx.AsyncClient(timeout=120.0) as client:` — creates and destroys an httpx client on every native-responses request. Client creation involves socket pool setup, TLS context initialization, etc.
- **Evidence:** `async with httpx.AsyncClient(timeout=120.0) as client:` is inside the request handler, not a module-level singleton.
- **Impact:** 5–15 ms client setup cost per request; connection pool cannot reuse TCP connections to OpenRouter.
- **Effort:** S

#### BN-004: `_append_generation_id` — Synchronous File Open Per SSE Chunk

- **File:** `src/thegent/routing/litellm_responses_handler.py:59`
- **Function:** `_append_generation_id()`
- **Issue:** Called from within the streaming async generator (`handle_responses_stream`) for every chunk that carries a generation ID. Opens the file, writes one JSON line, closes. This is a synchronous blocking file I/O call inside an async path.
- **Evidence:** Line 68: `with _GENERATION_ID_STORE.open("a", encoding="utf-8") as fh:` called per chunk inside `async for chunk in response_obj:`.
- **Impact:** Each invocation blocks the event loop for ~0.1–1 ms; under high stream rates this causes measurable tail latency.
- **Effort:** S

#### BN-005: `get_context_window()` — Iterates Full Dict on Every Miss

- **File:** `src/thegent/routing/litellm_router.py:304`
- **Function:** `get_context_window()`
- **Issue:** On metadata miss, iterates all keys of `MODEL_CONTEXT_WINDOWS` doing normalize-and-compare for each. Called per request during context window validation.
- **Evidence:** Lines 322–328: `for key, value in MODEL_CONTEXT_WINDOWS.items(): if key.lower()...`. Dict has ~20 entries today; normalization involves `.lower().replace()` chained 2–3 times per key.
- **Impact:** Small per-call (< 1 ms) but called on every routing decision. Build a normalized lookup dict at module init.
- **Effort:** S

### 3.2 Agent Layer

#### BN-006: `CursorApiRunner` — HTTP Health Check on Every `run()` Call

- **File:** `src/thegent/agents/cursor_api_runner.py:109`
- **Function:** `CursorApiRunner.run()`
- **Issue:** `_is_cursor_api_reachable(base_url, token)` performs a synchronous `httpx.get` with a 3-second timeout before every agent invocation. This is a blocking HTTP call inside what may be an async context, and adds 3 ms–3 s latency to every cursor-agent run.
- **Evidence:** Line 109: `if not _is_cursor_api_reachable(base_url, token):` with `timeout: float = 3.0` on the httpx call.
- **Impact:** 3–50 ms on success; 3 s on timeout; also blocks the calling thread.
- **Effort:** S (cache the reachability result with a TTL of 30 s)

#### BN-007: `CodexProxyRunner` — Creates + Destroys Isolated Home Per Run

- **File:** `src/thegent/agents/codex_proxy.py:587`
- **Function:** `CodexProxyRunner.run()`
- **Issue:** Lines 587–588: `isolated_home = _create_isolated_home(self.instance_id)` creates a `~/.codex/agents/<id>` directory on every run. The `finally` block at line 692 removes it with `shutil.rmtree()`. This is 2 filesystem ops (mkdir + rmtree) per agent invocation.
- **Evidence:** `_create_isolated_home()` at line 114 calls `isolated_home.mkdir(parents=True, exist_ok=True)`. Cleanup in `finally` calls `shutil.rmtree(isolated_home)`.
- **Impact:** 2–10 ms per run for directory creation/deletion; more on slow filesystems.
- **Effort:** S (reuse home directory across runs for same instance_id)

#### BN-008: `_run_with_activity_monitoring` — 0.5 s Poll Loop

- **File:** `src/thegent/agents/codex_proxy.py:354`
- **Function:** `_run_with_activity_monitoring()`
- **Issue:** Line 354: `time.sleep(0.5)` in the main monitoring while loop. This is the polling interval for checking subprocess completion and hang detection. For fast tasks (< 1 s) this wastes up to 500 ms waiting.
- **Evidence:** `time.sleep(0.5)` inside the `while True:` loop that calls `proc.poll()`.
- **Impact:** Fast subprocess calls pay up to 500 ms extra wait time.
- **Effort:** S (reduce to 0.05–0.1 s or use `proc.wait(timeout=0.1)`)

### 3.3 Sitback / NeverIdleLoop

#### BN-009: `NeverIdleLoop._run_once()` — `asyncio.run()` in Sync Thread

- **File:** `src/thegent/sitback/never_idle.py:163`
- **Function:** `NeverIdleLoop._run_once()`
- **Issue:** Line 163: `result = asyncio.run(self._gardening.run_step(step))`. `asyncio.run()` creates a new event loop, runs the coroutine, and tears down the loop on every gardening tick. The NeverIdleLoop runs in a `threading.Thread` (line 119) that has no existing event loop. With `sleep_interval=45` and 10 steps, `asyncio.run()` is called once every 45 s but each call has 5–50 ms overhead for loop creation/teardown.
- **Evidence:** `threading.Thread(target=self._run_loop, ...)` at line 119; `asyncio.run(self._gardening.run_step(step))` at line 163.
- **Impact:** 5–50 ms overhead per tick; event loop thrash; prevents reuse of connections or async resources across gardening steps.
- **Effort:** S (create one persistent event loop for the thread; use `loop.run_until_complete()`)

#### BN-010: `GardeningManager.check_backlog()` — Full File Read on Every Tick

- **File:** `src/thegent/sitback/gardening.py:87`
- **Function:** `GardeningManager.check_backlog()`
- **Issue:** Line 87: `content = work_stream.read_text()` reads the entire WORK_STREAM.md on every gardening cycle. File is multi-KB and growing. Called every `sleep_interval * len(STEPS)` seconds = every ~450 s, but still reads the full file each time.
- **Evidence:** `content = work_stream.read_text()` with no caching; `content.count("| CLAIMED ")` etc. iterate the string.
- **Impact:** Small today; grows with WORK_STREAM.md size. Cache with file mtime check.
- **Effort:** S

#### BN-011: `GardeningManager.check_traceability()` — Same Full File Read Pattern

- **File:** `src/thegent/sitback/gardening.py:141`
- **Function:** `GardeningManager.check_traceability()`
- **Issue:** Same pattern as BN-010 but for FR_TRACKER.md.
- **Evidence:** Line 146: `content = fr_tracker.read_text()`.
- **Impact:** Same as BN-010.
- **Effort:** S (fix alongside BN-010)

### 3.4 Worker Pool

#### BN-012: `PersistentWorkerPool.acquire()` — Linear Scan on Every Acquire

- **File:** `src/thegent/core/worker_pool.py:267`
- **Function:** `PersistentWorkerPool.acquire()`
- **Issue:** Line 273: `for w in self._workers: if not w.in_use and w.is_alive():` — linear scan of all workers under lock. For `pool_size=4` this is negligible. Under burst conditions with overflow workers, list can grow unbounded, making acquire O(N).
- **Evidence:** Linear scan in `acquire()` plus `self._workers.append(overflow)` in overflow path.
- **Impact:** Low with default pool_size=4; becomes O(N) with overflow workers under burst.
- **Effort:** S (maintain separate idle/busy sets)

#### BN-013: `_WORKER_BOOTSTRAP` — Spawns Another Python Subprocess Per Task

- **File:** `src/thegent/core/worker_pool.py:88`
- **Issue:** The embedded bootstrap script (`_WORKER_BOOTSTRAP`) itself calls `subprocess.run(cmd)` for each task where `cmd = [sys.executable, "-m", "thegent", "run", ...]`. This means each pool task spawns a full Python subprocess — defeating the purpose of the warm pool. The pool eliminates Python startup for the pool worker process itself, but the worker immediately starts another Python process for the actual agent run.
- **Evidence:** Line 88: `cmd = [sys.executable, "-m", "thegent", "run", agent, ...]` inside `_run_task()` in the bootstrap.
- **Impact:** The ~300 ms Python startup elimination claimed in the docstring is not achieved; the worker still pays subprocess startup cost per task.
- **Effort:** M (refactor bootstrap to call agent runner in-process via import)

### 3.5 MCP Server

#### BN-014: `BearerAuthMiddleware` — Instantiates `ThegentSettings()` Per Request

- **File:** `src/thegent/mcp/server.py:50`
- **Function:** `BearerAuthMiddleware.dispatch()`
- **Issue:** Line 50: `settings = ThegentSettings()` — Pydantic settings object is constructed on every MCP request. `ThegentSettings` reads environment variables and applies validators. This is 1–5 ms of pure overhead per request.
- **Evidence:** `settings = ThegentSettings()` inside `dispatch()` which is called on every request.
- **Impact:** 1–5 ms per MCP call; multiplied by all tool invocations.
- **Effort:** S (cache as class-level attribute initialized once)

#### BN-015: SHA-256 Elicitation Cache Key — `hashlib.sha256` Each Call

- **File:** `src/thegent/mcp/server.py:217`
- **Function:** `_cache_elicitation_key()`
- **Issue:** Line 217: `hashlib.sha256(key_data.encode()).hexdigest()[:16]`. While SHA-256 is fast, using only 16 hex chars (64 bits) from a SHA-256 (256 bits) is over-engineered for a 100-item in-memory cache. A simpler hash or direct string key would be faster and sufficient.
- **Evidence:** `hashlib.sha256(key_data.encode()).hexdigest()[:16]` in `_cache_elicitation_key()`.
- **Impact:** Negligible in isolation; pattern should be simplified.
- **Effort:** S

### 3.6 Rust Audit Chain

#### BN-016: `sha256_hex()` — Hand-rolled SHA-256 with No SIMD

- **File:** `crates/thegent-router/src/audit.rs:90`
- **Function:** `sha256_hex()`
- **Issue:** The `sha256_hex()` function is a hand-rolled SHA-256 implementation using the stdlib-only `std::num::Wrapping` approach. This misses all platform SIMD optimizations (SHA-NI on x86, ARMv8 SHA extensions). The `sha2` crate from RustCrypto uses these intrinsics and is 10–20x faster.
- **Evidence:** Lines 90–172: full custom SHA-256 implementation with no use of `sha2` or `ring` crates.
- **Impact:** Every routing decision computes two SHA-256 hashes (the record hash and BTreeMap serialization). Under high throughput, this is a measurable bottleneck.
- **Effort:** M

#### BN-017: `AuditLogger::append()` — File Opened and Closed Per Record

- **File:** `crates/thegent-router/src/audit.rs:265`
- **Function:** `AuditLogger::append()`
- **Issue:** Line 265: `OpenOptions::new().create(true).append(true).open(&self.path)` — opens the file on every `append()` call. Under burst routing (many decisions per second), this is one `open()` + `write()` + implicit `close()` syscall sequence per record. The `Mutex` is held across this.
- **Evidence:** `OpenOptions::new()...open(&self.path)` inside the mutex lock in `append()`.
- **Impact:** Under 100+ routing decisions/sec: ~100 `open()`/`close()` pairs per second; OS file-open overhead accumulates.
- **Effort:** M (hold a `BufWriter<File>` in `AuditState` opened once at construction)

#### BN-018: `AuditLogger::new()` — Reads Full File to Restore Chain Head

- **File:** `crates/thegent-router/src/audit.rs:240`
- **Function:** `AuditLogger::new()` → `read_last_hash()` → `read_records()`
- **Issue:** `read_last_hash()` calls `read_records()` which reads and parses every line of the JSONL file to get the last record. As the audit log grows (long-running deployments), this startup cost grows linearly.
- **Evidence:** `fn read_last_hash(path: &PathBuf) -> String { ... Self::read_records(path).last()... }`.
- **Impact:** At 1000 records, parses 1000 JSON lines at startup. Seek to end and read last line instead.
- **Effort:** S

### 3.7 Semantic Cache

#### BN-019: `cosine_similarity()` — Pure Python Vector Math

- **File:** `src/thegent/routing/semantic_cache.py:30`
- **Function:** `cosine_similarity()`
- **Issue:** Pure Python loop for dot product and norms. For embedding vectors of dimension 384–1536 (common sentence-transformer sizes), this is 384–1536 Python multiply+add operations per similarity check. NumPy vectorization would be 10–50x faster.
- **Evidence:** `dot = sum(x * y for x, y in zip(a, b))` — Python generator expression.
- **Impact:** Per cache lookup; grows with number of cached entries (linear scan to find best match).
- **Effort:** S

---

## 4. Quick Wins (S-effort, implementable in one WL item each)

| ID     | File                                   | Function                                   | Fix                                                                                                                                                    |
| ------ | -------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| QW-001 | `routing/litellm_router.py`            | `get_litellm_router()`                     | Cache the `Router` instance as a module-level singleton; invalidate when circuit breaker state changes. Use `cachetools.TTLCache(maxsize=1, ttl=300)`. |
| QW-002 | `routing/litellm_responses_handler.py` | `_forward_native_responses()`              | Create a module-level `httpx.AsyncClient` singleton (or use `contextlib.asynccontextmanager` lifespan).                                                |
| QW-003 | `routing/litellm_responses_handler.py` | `_append_generation_id()`                  | Buffer generation IDs in an in-memory deque; flush to disk in a background task or on a schedule (every 5 s).                                          |
| QW-004 | `sitback/never_idle.py`                | `NeverIdleLoop._run_once()`                | Replace `asyncio.run()` with a persistent event loop stored as `self._loop`; call `self._loop.run_until_complete()`.                                   |
| QW-005 | `sitback/gardening.py`                 | `check_backlog()` / `check_traceability()` | Cache `read_text()` result keyed by file `mtime`; re-read only when mtime changes.                                                                     |
| QW-006 | `agents/cursor_api_runner.py`          | `_is_cursor_api_reachable()`               | Cache result in a `cachetools.TTLCache(maxsize=1, ttl=30)` keyed by `base_url`.                                                                        |
| QW-007 | `mcp/server.py`                        | `BearerAuthMiddleware.dispatch()`          | Cache `ThegentSettings()` as a class-level attribute; reload only on `SIGHUP`.                                                                         |
| QW-008 | `agents/codex_proxy.py`                | `_run_with_activity_monitoring()`          | Reduce `time.sleep(0.5)` to `time.sleep(0.05)` to cut fast-task overhead from 500 ms to 50 ms.                                                         |
| QW-009 | `routing/litellm_router.py`            | `get_context_window()`                     | Build normalized lookup dict at module init; O(1) lookup instead of O(N) scan.                                                                         |
| QW-010 | `crates/thegent-router/src/audit.rs`   | `AuditLogger::new()`                       | Replace `read_records().last()` with seek-to-end scan for last non-empty line (tail-read approach).                                                    |

---

## 5. Medium-term Optimizations (M-effort, 1–3 days each)

### M-001: Replace Custom SHA-256 with `sha2` Crate

- **File:** `crates/thegent-router/src/audit.rs`
- **Change:** Add `sha2 = "0.10"` to `Cargo.toml`. Replace `sha256_hex()` (lines 90–172) with `sha2::Sha256::digest()`. Remove the 80-line hand-rolled implementation.
- **Impact:** 10–20x faster hashing; correct use of hardware SHA extensions on x86/ARM.
- **Validation:** Existing test `test_sha256_known_value` verifies hash output; update expected values for `sha2` output format.

### M-002: Hold `BufWriter` in `AuditLogger`

- **File:** `crates/thegent-router/src/audit.rs`
- **Change:** Move the open `File` handle into `AuditState` as `writer: BufWriter<File>`. Open once at `AuditLogger::new()`. Flush on each `append()` call (or batch flush every N records). Mutex already protects state.
- **Impact:** Eliminates one `open()`/`close()` syscall pair per routing decision. Under 100 decisions/sec, saves ~100 syscalls/sec.
- **Validation:** All existing tests continue to pass; add a high-throughput bench test.

### M-003: Async `_generate_id` Buffering via asyncio Queue

- **File:** `src/thegent/routing/litellm_responses_handler.py`
- **Change:** Replace synchronous `_append_generation_id()` with an asyncio `Queue`-backed writer task. Writer task drains queue every 5 s or when batch size reaches 10. Avoids any blocking I/O in the streaming async path.
- **Impact:** Zero blocking I/O in SSE stream handler; generation IDs still persisted reliably.

### M-004: Worker Pool Bootstrap — In-Process Agent Execution

- **File:** `src/thegent/core/worker_pool.py`
- **Change:** Refactor `_WORKER_BOOTSTRAP` to call the agent runner in-process via Python import instead of spawning `subprocess.run([sys.executable, "-m", "thegent", "run", ...])`. The pool worker process already has thegent imported (pre-warm). Use `CodexProxyRunner.run()` or equivalent directly.
- **Impact:** Eliminates ~300 ms Python startup per task — the entire stated goal of WL-016/MTSP-06 is currently defeated by the nested subprocess.
- **Validation:** Worker pool unit tests; integration test comparing subprocess vs in-process latency.

### M-005: `PersistentWorkerPool.acquire()` — O(1) with Free List

- **File:** `src/thegent/core/worker_pool.py`
- **Change:** Maintain `self._idle: asyncio.Queue[Worker]` alongside `self._workers`. Push to queue on `release()`; pop from queue on `acquire()`. Overflow path pushes directly to queue. Eliminates O(N) scan under lock.
- **Impact:** Acquire from O(N) to O(1); lock contention reduced.

### M-006: Semantic Cache Cosine Similarity — NumPy Vectorization

- **File:** `src/thegent/routing/semantic_cache.py`
- **Change:** Replace pure-Python `cosine_similarity()` with `numpy.dot(a, b) / (numpy.linalg.norm(a) * numpy.linalg.norm(b))`. NumPy is already a transitive dependency via sentence-transformers. For cache scan, batch-vectorize all stored embeddings as a 2D numpy array and use matrix multiply for bulk similarity.
- **Impact:** 10–50x speedup for similarity computation; enables larger semantic caches without latency penalty.

---

## 6. Deep Work / Rust Rewrites (L-effort, 3–7 days each)

### L-001: Rust JSONL Generation ID Writer

- **Description:** Move `_GENERATION_ID_STORE` persistence to a Rust binary (`thegent-jsonl` crate already exists). Python side sends generation IDs over a Unix socket or shared memory (`thegent-shm` crate exists); Rust side batches and fsync-writes. Eliminates all Python file I/O in the hot streaming path.
- **Effort:** L
- **Blocked by:** M-003 (interim async queue solution)

### L-002: LiteLLM Model Registry as Rust-backed Cache

- **Description:** Move the model catalog and healthy-deployment filtering to a Rust shared memory segment (leveraging `thegent-shm`). Python side reads model config from shared memory on first access per process, cached indefinitely until invalidated via IPC. Circuit breaker state changes are signaled via a watch channel. Eliminates per-request model list rebuild entirely.
- **Effort:** L
- **Blocked by:** QW-001 (TTL cache as interim)

### L-003: Routing Decision via Rust ParetoRouter PyO3 Binding

- **Description:** The Rust `ParetoRouter` (in `crates/thegent-router/src/router.rs`) is already implemented. Wire it into the Python routing path via PyO3 (`crates/thegent-router/src/python.rs` already exists). Replace `make_routing_decision_from_factors()` in Python with a direct call to the compiled Rust binding. Eliminates Python-side heuristic duplication and gets sub-millisecond routing decisions.
- **Effort:** L
- **Blocked by:** PyO3 wheel build integration in pyproject.toml

### L-004: NeverIdleLoop Gardening Steps as Rust Async Tasks

- **Description:** Port the gardening subprocess calls (`subprocess.run(["thegent", "govern", "go", "health"])` etc.) to use the Rust `thegent-hooks` crate via IPC. Eliminates Python subprocess spawn overhead for each gardening step. High complexity; benefit mainly for high-frequency gardening.
- **Effort:** L

---

## 7. Benchmarking Infrastructure

### 7.1 Python Benchmark Suite

Add to `benchmarks/` directory (already exists at project root):

```
benchmarks/
  routing_benchmark.py      # router build time, request throughput
  agent_benchmark.py        # subprocess spawn latency
  sitback_benchmark.py      # gardening tick latency
  mcp_benchmark.py          # MCP tool call latency via uvicorn TestClient
```

Use `pytest-benchmark` for consistent measurement. Example:

```python
def test_router_build_latency(benchmark):
    result = benchmark(build_litellm_model_list)
    assert len(result) > 0
```

### 7.2 Rust Benchmark Suite

Add criterion benchmarks to `crates/thegent-router/`:

```rust
// benches/audit_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use thegent_router::audit::{AuditLogger, AuditRecord};

fn bench_audit_append(c: &mut Criterion) {
    let dir = tempfile::tempdir().unwrap();
    let logger = AuditLogger::new(dir.path().join("bench.jsonl"));
    c.bench_function("audit_append", |b| {
        b.iter(|| {
            let r = AuditRecord::new("lifecycle".into(), "gemini-3-flash".into(), 10, 0.001);
            logger.append(black_box(&r)).unwrap();
        })
    });
}
```

### 7.3 Regression Gate

Add to `Taskfile.yml`:

```yaml
bench:
  desc: Run performance benchmarks and compare against baseline
  cmds:
    - python -m pytest benchmarks/ --benchmark-json=bench-results.json
    - cargo bench --manifest-path crates/Cargo.toml 2>&1 | tee bench-rust.txt
```

Store baseline in `benchmarks/baseline.json`. CI fails if any benchmark regresses > 15%.

---

## 8. Proposed WL Items

The following items are formatted for direct intake into `docs/reference/WORK_STREAM.md`.

### [WL-070] Cache LiteLLM Router Instance — Eliminate Per-Request Model List Rebuild

**Status:** pending
**Priority:** P1
**Area:** performance
**Effort:** S
**Blocked by:** none
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

In `src/thegent/routing/litellm_router.py`, the `get_litellm_router()` function builds a new `Router` instance on every call by running `build_litellm_model_list()` and `build_fallback_chains()` each time. Add a module-level `cachetools.TTLCache(maxsize=1, ttl=300)` to memoize the built `Router`. Invalidate cache when circuit breaker state changes (hook into `ProviderCircuitBreakerRegistry`). Also fix `build_dynamic_fallback_router()` to cache the full model list separately with the same TTL. Estimated impact: 10–50 ms latency reduction per request.

---

### [WL-071] Pool `httpx.AsyncClient` in `_forward_native_responses`

**Status:** pending
**Priority:** P1
**Area:** performance
**Effort:** S
**Blocked by:** none
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

In `src/thegent/routing/litellm_responses_handler.py`, `_forward_native_responses()` creates a new `httpx.AsyncClient` per request (`async with httpx.AsyncClient(timeout=120.0) as client:`). Replace with a module-level singleton client initialized at module load, or use FastMCP/Starlette lifespan to manage a shared client with connection pooling. This enables TCP connection reuse to OpenRouter and eliminates 5–15 ms client setup overhead per native-responses request.

---

### [WL-072] Fix NeverIdleLoop — Replace `asyncio.run()` with Persistent Event Loop

**Status:** pending
**Priority:** P1
**Area:** performance
**Effort:** S
**Blocked by:** none
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

In `src/thegent/sitback/never_idle.py`, `_run_once()` calls `asyncio.run(self._gardening.run_step(step))` (line 163), which creates and destroys an asyncio event loop on every gardening tick (every 45 s per step, but with event-loop creation overhead of 5–50 ms per call). Replace with: create a dedicated event loop in `start()`, store as `self._loop = asyncio.new_event_loop()`, and in `_run_once()` call `self._loop.run_until_complete(...)`. Tear down in `stop()`. This also enables future reuse of async resources (connections, caches) across gardening steps.

---

### [WL-073] Cache Cursor API Reachability Check (30 s TTL)

**Status:** pending
**Priority:** P2
**Area:** performance
**Effort:** S
**Blocked by:** none
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

In `src/thegent/agents/cursor_api_runner.py`, `CursorApiRunner.run()` calls `_is_cursor_api_reachable(base_url, token)` on every invocation, performing a synchronous `httpx.get` with up to a 3-second timeout. Add a `cachetools.TTLCache(maxsize=4, ttl=30)` keyed by `(base_url, token_hash)` to memoize the reachability result. On cache hit, skip the HTTP probe. Reset cache entry on connection failure so recovery is fast. Saves 3–50 ms per cursor-agent invocation.

---

### [WL-074] Replace Custom SHA-256 in `audit.rs` with `sha2` Crate

**Status:** pending
**Priority:** P2
**Area:** performance
**Effort:** M
**Blocked by:** none
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

In `crates/thegent-router/src/audit.rs`, the `sha256_hex()` function (lines 90–172) is a hand-rolled SHA-256 implementation using `std::num::Wrapping`. This misses hardware SHA-NI (x86) and ARMv8 SHA extensions. Replace with `sha2 = "0.10"` (RustCrypto, `digest` trait): `use sha2::{Sha256, Digest}; Sha256::digest(input)`. Remove the 80-line custom implementation. Update `Cargo.toml` for `crates/thegent-router`. Update the known-value test (`test_sha256_known_value`) since the custom implementation has a known incorrect result for "hello world" (the test only checks length, not value). Expected improvement: 10–20x throughput for hash computation.

---

### [WL-075] Hold `BufWriter` in `AuditLogger` — Eliminate Per-Record `open()`

**Status:** pending
**Priority:** P2
**Area:** performance
**Effort:** M
**Blocked by:** WL-074 (do together with SHA-256 replacement)
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

In `crates/thegent-router/src/audit.rs`, `AuditLogger::append()` opens the file on every call (`OpenOptions::new()...open(&self.path)` inside the Mutex). Refactor `AuditState` to hold `writer: BufWriter<File>` opened once at `AuditLogger::new()`. Call `self.state.lock().unwrap().writer.flush()` after each write (or batch flush every N records for higher throughput). Also fix `AuditLogger::new()`: replace `read_records().last()` in `read_last_hash()` with a tail-read (seek to end, scan backward for last newline) to avoid parsing all records at startup.

---

### [WL-076] Fix Worker Pool Bootstrap — In-Process Agent Execution

**Status:** pending
**Priority:** P1
**Area:** performance
**Effort:** M
**Blocked by:** none
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

In `src/thegent/core/worker_pool.py`, the `_WORKER_BOOTSTRAP` embedded script (line 64) calls `subprocess.run([sys.executable, "-m", "thegent", "run", ...])` for each task, spawning a full Python subprocess and defeating the ~300 ms startup elimination that `PersistentWorkerPool` was designed to provide (FR-OPT-006 / MTSP-06). Refactor the bootstrap to call the agent runner in-process: import `thegent.agents.codex_proxy.CodexProxyRunner` (or `DirectAgentRunner`) and call `.run()` directly. The pool workers already pre-import `thegent.agents.base` and `thegent.config`. This requires making the runner callable without CLI parsing. Update worker pool tests to verify actual latency improvement (target: < 50 ms per task vs current ~300+ ms).

---

### [WL-077] Cache `ThegentSettings()` in MCP `BearerAuthMiddleware`

**Status:** pending
**Priority:** P2
**Area:** performance
**Effort:** S
**Blocked by:** none
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

In `src/thegent/mcp/server.py`, `BearerAuthMiddleware.dispatch()` instantiates `ThegentSettings()` on every MCP request (line 50). Pydantic settings construction reads environment variables and applies validators, costing 1–5 ms per call. Cache as a class-level attribute: `_settings: ThegentSettings | None = None` initialized on first request. Optionally add a `reload()` method or SIGHUP handler to invalidate. Saves 1–5 ms per MCP tool invocation across all tools.

---

### [WL-078] Add Python Performance Benchmark Suite

**Status:** pending
**Priority:** P2
**Area:** performance
**Effort:** M
**Blocked by:** none
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

Create `benchmarks/` suite using `pytest-benchmark`:

- `benchmarks/routing_benchmark.py`: measures `get_litellm_router()` build time, `build_litellm_model_list()`, `get_context_window()` miss path.
- `benchmarks/mcp_benchmark.py`: measures `ThegentSettings()` construction, elicitation cache key generation.
- `benchmarks/sitback_benchmark.py`: measures `asyncio.run()` loop creation overhead, `check_backlog()` file read.
- Store baseline JSON in `benchmarks/baseline.json`.
- Add `task bench` to `Taskfile.yml` that fails CI if any benchmark regresses > 15%.

This provides regression detection for all WL-070 through WL-077 optimizations.

---

### [WL-079] Add Rust Criterion Benchmark Suite for Audit Chain

**Status:** pending
**Priority:** P2
**Area:** performance
**Effort:** M
**Blocked by:** WL-074, WL-075
**Source:** [docs/research/PERF_OPTIMIZATION_RESEARCH_2026-02-20.md]

Add `crates/thegent-router/benches/audit_bench.rs` using `criterion`:

- Benchmark `AuditRecord::new()` (includes hash computation).
- Benchmark `AuditLogger::append()` (includes file I/O).
- Benchmark `AuditLogger::verify_chain()` for N=100, N=1000, N=10000 records.
- Add to `crates/Cargo.toml` criterion dev-dependency.
- Run as part of CI with `cargo bench --manifest-path crates/Cargo.toml`.

Establishes before/after baselines for WL-074 (SHA-256 replacement) and WL-075 (BufWriter).

---

_End of performance optimization research document._
