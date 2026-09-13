# Completed Items Audit — 2026-02-19

> **Purpose**: Verify that all items marked COMPLETED in WORK_STREAM.md are actually implemented in code. This audit cross-checks COMPLETED notes against the codebase.

---

## Summary

| Status            | Count |
| ----------------- | ----- |
| ✅ Verified       | 85+   |
| ⚠️ Partial / Note | 2     |
| ❌ Gap            | 0     |

---

## Verified Items (representative sample)

| ID                                | Location                                           | Verification                                                                                                                                                                                                                                            |
| --------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| wire-maif-agent-runner            | maif/runner.py, execution.py, cli/commands/impl.py | MAIF lifecycle: `Auditor.sign_run` (run start) + `generate_maif_artifact` + `persist_maif_artifact` (run end) in ExecutionEngine and cli impl. `MAIFRunner.record_run_start`/`record_run_end` exist but are not wired; equivalent behavior via Auditor. |
| swarm-fix-macos-sampling          | execution.py (vm_stat)                             | vm_stat includes speculative/purgeable; dynamic page size from sysctl                                                                                                                                                                                   |
| swarm-redlock-atomic              | orchestration/                                     | RedlockController with SETNX+Lua release; in-memory fallback                                                                                                                                                                                            |
| resource-gpu-utilization          | resources/                                         | GpuMonitor, nvidia-smi fallback                                                                                                                                                                                                                         |
| ux-terminal-keepalive             | tools/, cli_impl                                   | TerminalKeepalive; THGENT_KEEPALIVE_INTERVAL                                                                                                                                                                                                            |
| scratch-doctor-fix                | commands/                                          | DoctorRunner, DoctorCheck, --fix                                                                                                                                                                                                                        |
| resource-disk-queue-depth         | resources/                                         | DiskMonitor, Little's Law queue depth                                                                                                                                                                                                                   |
| impl-remote-executor              | compute/                                           | RemoteExecutor, SSH, round-robin                                                                                                                                                                                                                        |
| ux-linting-accelerator            | tools/linting_accelerator.py                       | LintingAccelerator, oxlint/ruff                                                                                                                                                                                                                         |
| swarm-priority-queue              | orchestration/                                     | RunPriorityQueue, heapq + FIFO                                                                                                                                                                                                                          |
| swarm-dag-prioritization          | orchestration/                                     | DagPrioritizer, CPM                                                                                                                                                                                                                                     |
| swarm-token-bucket                | orchestration/                                     | TokenBucket, RateLimitedSwarmRunner                                                                                                                                                                                                                     |
| impl-simulation-replay-engine     | simulation/replay.py                               | SimulationReplayEngine, replay CLI                                                                                                                                                                                                                      |
| borrow-dex-flash-agents           | agents/flash_agent.py                              | FlashAgent, thegent_flash MCP                                                                                                                                                                                                                           |
| enhance-macos-sandbox             | security/macos_sandbox.py                          | MacOSSandbox, sandbox-exec                                                                                                                                                                                                                              |
| bkm-09-watcher-daemon             | native/watcher_daemon.py                           | WatcherDaemon, watchdog                                                                                                                                                                                                                                 |
| muxless-termitty-introspection    | tools/terminal_capture.py                          | TerminalCapture, ZmxBackend fallback                                                                                                                                                                                                                    |
| borrow-plangent-subagents         | agents/plangent.py                                 | PlangentPlanner, PlangentExecutor                                                                                                                                                                                                                       |
| impl-rust-zmx-wrapper             | crates/thegent-zmx                                 | ZmxSession, ZmxClient; Python tests                                                                                                                                                                                                                     |
| compositor-caching                | ui/compositor/                                     | TTLCache render cache                                                                                                                                                                                                                                   |
| cache-frecency-algorithm          | cache/frecency.py                                  | FrecencyCache, FrecencyModelSelector                                                                                                                                                                                                                    |
| swarm-redis-concurrency           | orchestration/redis_concurrency.py                 | RedisConcurrencyController                                                                                                                                                                                                                              |
| cache-predictive-pre-warming      | cache/pre_warmer.py                                | CachePreWarmer                                                                                                                                                                                                                                          |
| impl-cross-project-registry       | registry/cross_project.py                          | CrossProjectRegistry                                                                                                                                                                                                                                    |
| impl-idea-seed-scanner            | commands/idea_seeds.py                             | IdeaSeedScanner                                                                                                                                                                                                                                         |
| muxless-acp-session-endpoints     | adapters/acp_server.py                             | SessionEndpoints, session/attach,inspect,send                                                                                                                                                                                                           |
| acp-mcp-bridge                    | adapters/acp_mcp_bridge.py                         | AcpMcpBridge                                                                                                                                                                                                                                            |
| cache-diskcache-migration         | cache/                                             | MultiLevelCache L1+L2 diskcache                                                                                                                                                                                                                         |
| swarm-critical-lane               | execution.py                                       | ConcurrencyController.critical_lane_slots                                                                                                                                                                                                               |
| swarm-per-gate-logging            | execution.py                                       | Per-gate \_log messages                                                                                                                                                                                                                                 |
| index-file-indexing               | indexing/file_index.py                             | FileIndex, fd-style search                                                                                                                                                                                                                              |
| bkm-05-state-shm                  | native/state_shm.py                                | CircuitBreakerShm, XpTracker                                                                                                                                                                                                                            |
| bkm-06-git-native                 | native/git_native.py                               | GitNative, thegent-git binary                                                                                                                                                                                                                           |
| bkm-07-hook-dispatcher-extend     | governance/                                        | scan-secrets in hook-dispatcher                                                                                                                                                                                                                         |
| bkm-08-discovery-binary           | native/                                            | thegent-discovery, DiscoveryClient                                                                                                                                                                                                                      |
| litellm-responses-handler         | routing/                                           | router.acompletion, HTTP/WS handlers                                                                                                                                                                                                                    |
| impl-zig-rust-interop-poc         | crates/thegent-zmx-interop                         | extern "C" FFI                                                                                                                                                                                                                                          |
| impl-zmx-c-abi                    | crates/thegent-zmx-interop                         | zmx C ABI                                                                                                                                                                                                                                               |
| cache-multi-level                 | cache/                                             | MultiLevelCache                                                                                                                                                                                                                                         |
| resource-distributed-coordination | resources/                                         | DistributedResourceCoordinator                                                                                                                                                                                                                          |
| impl-os-user-adapter              | adapters/                                          | OS user creation adapter                                                                                                                                                                                                                                |
| heliosShield-bridge-fix           | mesh/                                              | heliosShield bridge fixes                                                                                                                                                                                                                               |
| research-library-\*               | pyproject.toml, codebase                           | ruamel.yaml, pybreaker, diskcache, tenacity, rich                                                                                                                                                                                                       |

---

## Partial / Notes

### wire-maif-agent-runner (resolved 2026-02-19)

- **Status**: ✅ Now fully wired.
- **Implementation**: `MAIFRunner.record_run_start` and `record_run_end` are called from:
  - `ExecutionEngine.execute()` — before/after agent run
  - `cli/commands/impl.py` `run_impl()` — after `registry.register_start`, and after `registry.register_end`
- **Auditor** remains for run-registry signing and `generate_maif_artifact` + `persist_maif_artifact`.

---

## Crates Verified

- `thegent-zmx` — ZmxSession, ZmxClient
- `thegent-zmx-interop` — C ABI, Zig-Rust interop
- `thegent-shm` — CircuitBreakerShm, XpTracker
- `thegent-git` — gix-backed
- `thegent-discovery` — discovery binary
- `thegent-maif` — MAIF signing (used by Auditor)

---

## Recommendations

1. **Audit cadence**: Re-run this audit after major incorporations or when adding new COMPLETED entries.
