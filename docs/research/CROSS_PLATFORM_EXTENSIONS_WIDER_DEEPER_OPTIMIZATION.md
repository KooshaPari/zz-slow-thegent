<DONE>
# Cross-Platform Extensions: Wider, Deeper, Polish & Optimization

**Purpose:** Extend cross-platform plans with wider scope, deeper implementation detail, UX polish, and optimization. No repolish—add net-new coverage.

**Date:** 2026-02-16
**Status:** Research
**Extends:** CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md, CROSS_PLATFORM_ADVANCED_PATTERNS.md, CROSS_PLATFORM_PERFORMANCE_BENCHMARKS.md

---

## 1. Wider Scope

### 1.1 Additional Platforms & Environments

| Platform / Env                   | Current                             | Extension                                                                                                                      |
| -------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **WSL2**                         | Shell strategy; hooks via bash      | Full WSL2 provider: path translation (`/mnt/c/` ↔ `C:\`), Windows automation via `wsl.exe` bridge, `wslpath` for path mapping |
| **FreeBSD**                      | Not covered                         | Document as unsupported; add `platform == "freebsd"` detection; defer desktop automation                                       |
| **Container (Docker)**           | `isolation_mode=docker` placeholder | Headless mode; no desktop automation; `--headless` flag; Xvfb for Linux CI                                                     |
| **CI/CD (GitHub Actions, etc.)** | Not covered                         | Headless agent mode; `THGENT_HEADLESS=1`; skip hooks that require TTY; mock user activity                                      |
| **RDP / Remote Desktop**         | Windows Session awareness           | RDP session detection; `SessionId`; avoid automation in disconnected sessions                                                  |
| **VM / Cloud Desktop**           | Not covered                         | Document: same as native; latency considerations for remote MCP                                                                |

### 1.2 Edge Cases & Configurations

| Edge Case             | Current                      | Extension                                                                                        |
| --------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------ |
| **Multi-monitor**     | Single-screen assumptions    | `screenshot(region)` with monitor index; `get_monitors()`; coordinate clicks by monitor          |
| **High-DPI / Retina** | May break coordinate mapping | Scale factor detection; `device_pixel_ratio`; coordinate scaling in providers                    |
| **Mixed DPI**         | Not covered                  | Per-monitor scale; document coordinate system                                                    |
| **Wayland (Linux)**   | X11 assumed                  | Wayland: different capture APIs; `wlr-screencopy`, `pipewire`; document limitations              |
| **Headless Linux**    | Not covered                  | Xvfb; `DISPLAY=:99`; `xvfb-run` wrapper for CI                                                   |
| **Locked screen**     | Not covered                  | Detect lock; deny automation or queue; `CGSessionLockState` (macOS), `LockWorkStation` (Windows) |
| **Sleep / Hibernate** | Not covered                  | Detect sleep; fail fast with clear error; optional wake-on-LAN for remote                        |

### 1.3 Use Cases Beyond Desktop

| Use Case                | Current     | Extension                                                                      |
| ----------------------- | ----------- | ------------------------------------------------------------------------------ |
| **Headless agent (CI)** | Not covered | `thegent run --headless`; skip desktop automation; mock `UserActivityDetector` |
| **Scheduled runs**      | Not covered | cron/systemd timer; ensure no user activity check when headless                |
| **Batch processing**    | Not covered | `thegent run --batch` for non-interactive; no TTY prompts                      |
| **Remote + headless**   | Remote only | `thegent run --remote HOST --headless`; Windows PC runs headless agent         |

---

## 2. Deeper Implementation

### 2.1 Failure Modes & Error Taxonomy

| Failure Class  | Examples                              | Handling                                      |
| -------------- | ------------------------------------- | --------------------------------------------- |
| **Transient**  | Network blip, element not yet visible | Retry with backoff (tenacity)                 |
| **Permission** | Accessibility denied, UAC             | Fail fast; clear message; link to setup guide |
| **State**      | App closed, window moved              | Re-find element; invalidate cache             |
| **Resource**   | OOM, disk full                        | Circuit breaker; escalate                     |
| **Platform**   | API deprecated, unsupported OS        | Version check; graceful degradation           |
| **User**       | User interrupted, lock screen         | Release lock; queue or abort                  |

**Error Code Schema:**

```
THGENT-E001: Permission denied (accessibility)
THGENT-E002: Element not found (selector, timeout)
THGENT-E003: Remote host unreachable
THGENT-E004: Resource limit exceeded
THGENT-E005: Platform unsupported
THGENT-E006: User interrupted
...
```

### 2.2 Retry & Fallback Chains

| Layer                  | Retry                              | Fallback                                                 |
| ---------------------- | ---------------------------------- | -------------------------------------------------------- |
| **Desktop automation** | 3x with 0.5s backoff for transient | AppleScript → Apple Events (macOS); UIA → MSAA (Windows) |
| **Remote SSH**         | 2x with 2s backoff                 | Fail with clear message; suggest `ssh HOST` test         |
| **Element find**       | 2x with 1s (element may appear)    | Broader selector; screenshot + vision fallback (future)  |
| **Screenshot**         | 1 retry (capture can fail once)    | Region fallback; lower resolution                        |
| **User activity**      | No retry (user state)              | Config: `skip_user_check` for headless                   |

### 2.3 Circuit Breaker Integration

- **Desktop provider:** Open after 5 consecutive failures; 60s cooldown
- **Remote host:** Open after 3 connection failures; 120s cooldown
- **Use tenacity + pybreaker** (or custom thin wrapper); no custom retry loops

### 2.4 Security Hardening

| Area                  | Current                       | Extension                                           |
| --------------------- | ----------------------------- | --------------------------------------------------- |
| **Remote hosts**      | `remote_hosts.yaml` plaintext | Optional: encrypt at rest; `thegent remote decrypt` |
| **Agent credentials** | Per-agent env                 | Never log; redact in traces                         |
| **Audit**             | Run registry                  | Add `audit.jsonl` for automation actions; immutable |
| **Sandbox**           | Sub-user, OS user             | Document: OS user preferred for untrusted agents    |

---

## 3. Polish (UX, Diagnostics, Runbooks)

### 3.1 Error Messages & Diagnostics

| Scenario               | Current             | Extension                                                                                         |
| ---------------------- | ------------------- | ------------------------------------------------------------------------------------------------- |
| **Permission denied**  | Generic             | "Accessibility permission required. See: docs/guides/ACCESSIBILITY_SETUP.md"                      |
| **Element not found**  | "Element not found" | "Element 'button#submit' not found after 5s. App may have changed. Try: thegent diagnose element" |
| **Remote unreachable** | SSH error           | "Cannot reach windows-pc. Run: ssh windows-pc echo ok"                                            |
| **Hook failure**       | Exit code           | "Hook qa-lint failed (exit 1). Check: ~/.thegent/logs/hooks/qa-lint.log"                          |

### 3.2 Diagnostic Commands

```bash
thegent diagnose permissions   # Check accessibility, UIA, AT-SPI
thegent diagnose remote HOST   # SSH, path mapping, thegent version on remote
thegent diagnose element SEL   # Try find; report tree snippet
thegent diagnose shell         # Report get_preferred_shell() for all contexts
```

### 3.3 Troubleshooting Runbooks

| Doc                                                 | Content                                        |
| --------------------------------------------------- | ---------------------------------------------- |
| `docs/guides/TROUBLESHOOTING_DESKTOP_AUTOMATION.md` | Permission setup per platform; common failures |
| `docs/guides/TROUBLESHOOTING_REMOTE.md`             | SSH, path mapping, firewall                    |
| `docs/guides/TROUBLESHOOTING_HOOKS.md`              | Shell, WSL2, pwsh fallback                     |
| `docs/reference/ERROR_CODES.md`                     | THGENT-E001..E099 with causes and fixes        |

### 3.4 Structured Logging & Observability

| Area           | Extension                                                                   |
| -------------- | --------------------------------------------------------------------------- |
| **Trace ID**   | `trace_id` in all log lines; propagate to remote                            |
| **Structured** | JSON logs: `{"trace_id":"...","event":"automation_click","selector":"..."}` |
| **OTel**       | Spans for: automation action, remote call, hook execution                   |
| **Metrics**    | `thegent_automation_duration_seconds`, `thegent_remote_errors_total`        |

---

## 4. Optimization

### 4.1 Connection & Resource Pooling

| Resource             | Current                         | Extension                                                   |
| -------------------- | ------------------------------- | ----------------------------------------------------------- |
| **SSH**              | New connection per `run_remote` | Connection pool per host; reuse for `ps`, `logs`, `stop`    |
| **Desktop provider** | Lazy init                       | Warm-up on first use; optional `thegent warmup`             |
| **Element cache**    | Per-action                      | Extend TTL; event-based invalidation on window focus change |

### 4.2 Batching & Pipelining

| Operation                | Current            | Extension                                                             |
| ------------------------ | ------------------ | --------------------------------------------------------------------- |
| **Remote `ps` + `logs`** | Separate SSH calls | Batch: `ssh HOST "thegent ps; thegent logs ID"` when both needed      |
| **Element finds**        | One at a time      | Batch find for known selectors; parallel where independent            |
| **Screenshots**          | Full or region     | Incremental (diff) when supported; document in Performance Benchmarks |

### 4.3 Lazy Init & Warm-up

```python
# Optional warm-up to reduce first-action latency
def warmup_desktop_provider():
    """Pre-initialize desktop provider."""
    provider = get_provider()
    provider.screenshot(region={"width": 1, "height": 1})  # Minimal
```

- **CLI:** `thegent warmup` — init provider, test permissions
- **Config:** `warmup_on_start: bool` for sitback / long-running

### 4.4 Memory & Storage Tuning

| Area                  | Extension                                                         |
| --------------------- | ----------------------------------------------------------------- |
| **Screenshot buffer** | Limit in-memory screenshots; stream to disk for large             |
| **Run registry**      | Rotate old entries; `run_registry_max_entries: 1000`              |
| **Cache size**        | `element_cache_max_entries: 100`, `element_cache_ttl_seconds: 30` |

---

## 5. Consolidated Task Additions

### 5.1 Phase 8: Polish, Optimization & Extensions (New)

| ID    | Task                                                                 | Effort | Depends    |
| ----- | -------------------------------------------------------------------- | ------ | ---------- |
| P8.1  | Error code schema (THGENT-E001..) + structured errors                | 6-8    | P5.1       |
| P8.2  | `thegent diagnose` subcommands (permissions, remote, element, shell) | 8-12   | P5.1, P6.2 |
| P8.3  | Troubleshooting runbooks (desktop, remote, hooks, error codes)       | 6-8    | P8.1       |
| P8.4  | Circuit breaker for desktop provider + remote (tenacity/pybreaker)   | 6-8    | P3.5, P6.2 |
| P8.5  | Retry/fallback chains (automation, remote, element find)             | 8-10   | P8.4       |
| P8.6  | SSH connection pooling for remote                                    | 4-6    | P6.2       |
| P8.7  | `thegent warmup` + `warmup_on_start` config                          | 4-6    | P3.5       |
| P8.8  | OTel spans + trace_id propagation                                    | 6-8    | P5.1       |
| P8.9  | Headless mode (`--headless`, `THGENT_HEADLESS`)                      | 6-8    | P1.5, P2.2 |
| P8.10 | Edge cases: multi-monitor, high-DPI, locked screen detection         | 8-12   | P3.5       |
| P8.11 | WSL2 path translation + Windows automation bridge                    | 6-8    | P1.7, P3.3 |

### 5.2 Documents to Create

| Document                                            | Purpose                           |
| --------------------------------------------------- | --------------------------------- |
| `docs/reference/ERROR_CODES.md`                     | THGENT-E001.. with causes, fixes  |
| `docs/guides/TROUBLESHOOTING_DESKTOP_AUTOMATION.md` | Permission setup, common failures |
| `docs/guides/TROUBLESHOOTING_REMOTE.md`             | SSH, path mapping                 |
| `docs/guides/TROUBLESHOOTING_HOOKS.md`              | Shell, WSL2, pwsh                 |
| `docs/guides/HEADLESS_AND_CI.md`                    | Headless mode, CI/CD usage        |

### 5.3 Updates to Existing Docs

| Document                                        | Update                                     |
| ----------------------------------------------- | ------------------------------------------ |
| CROSS_PLATFORM_PERFORMANCE_BENCHMARKS           | Add connection pooling, warm-up, batch SSH |
| CROSS_PLATFORM_ADVANCED_PATTERNS                | Add error taxonomy, diagnostic patterns    |
| CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN | Add Phase 8                                |
| CROSS_PLATFORM_MASTER_INDEX                     | Add this doc, new guides                   |

---

## 6. References

- [CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md](./CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md)
- [CROSS_PLATFORM_ADVANCED_PATTERNS.md](./CROSS_PLATFORM_ADVANCED_PATTERNS.md)
- [CROSS_PLATFORM_PERFORMANCE_BENCHMARKS.md](./CROSS_PLATFORM_PERFORMANCE_BENCHMARKS.md)
- [CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN.md](../plans/CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN.md)
- [LIBRARY_FIRST_AUDIT_AND_PLAN.md](./LIBRARY_FIRST_AUDIT_AND_PLAN.md)

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md](./CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md) - Consolidated guide
- [CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md](./CROSS_PLATFORM_GAPS_AND_EXTENSIONS_RESEARCH.md) - Gaps research
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
