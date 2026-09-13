<DONE>
# System Resources (FD, CPU, Threads, Ports) — Full-Depth Research & Plan

> **Purpose**: Full-depth research and plan for FD (file descriptors), CPU, threads, ports, and other system resources relevant to multi-agent swarms.
> **Status**: Research | **Date**: 2026-02-16
> **Related**: [SMART_ROBUST_STRATEGIES_RESEARCH](./SMART_ROBUST_STRATEGIES_RESEARCH.md), [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md), [load_based_limits.py](../../src/thegent/orchestration/load_based_limits.py)

---

## 1. Executive Summary

Activity Monitor–style metrics (CPU %, memory, FD count, threads, ports) are essential for:

- **ConcurrencyController** gates (FD, memory, load)
- **Prune prioritization** (RSS-aware, FD-aware)
- **`thegent ps` / `thegent observe`** — extend to system process view
- **Backpressure** when FD/CPU/threads approach limits

This document covers: sampling methods (Linux vs macOS), limits (ulimit, sysctl), per-process vs system-wide metrics, and phased implementation.

---

## 2. Resource Taxonomy (Activity Monitor–Style)

From typical macOS Activity Monitor / `top` / `ps` output:

| Column               | Meaning                   | Linux Source                           | macOS Source                                 |
| -------------------- | ------------------------- | -------------------------------------- | -------------------------------------------- |
| **CPU %**            | Process CPU utilization   | `/proc/<pid>/stat` (utime+stime delta) | `top -l 1`, `ps -o %cpu`                     |
| **Memory (RSS)**     | Resident set size         | `/proc/<pid>/status` VmRSS             | `ps -o rss`, `task_info`                     |
| **Memory (Virtual)** | Virtual memory            | `/proc/<pid>/status` VmSize            | `ps -o vsz`                                  |
| **Threads**          | Thread count              | `/proc/<pid>/status` Threads           | `ps -o thcount`, `task_info`                 |
| **FD count**         | Open file descriptors     | `ls /proc/<pid>/fd \| wc -l`           | `lsof -p <pid> \| grep -v " txt " \| wc -l`  |
| **Ports**            | Open sockets/ports        | `ls /proc/<pid>/fd` + `readlink`       | `lsof -p <pid> -i`                           |
| **Compressed**       | Compressed memory (macOS) | N/A                                    | `task_info` (resident_size - phys_footprint) |
| **Time**             | CPU time used             | `/proc/<pid>/stat`                     | `ps -o time`                                 |

---

## 3. File Descriptors (FD)

### 3.1 Limits

| Level                | Linux                    | macOS                           |
| -------------------- | ------------------------ | ------------------------------- |
| **Per-process soft** | `ulimit -n` (often 1024) | `ulimit -n` (often 256 default) |
| **Per-process hard** | `ulimit -Hn`             | `ulimit -Hn`                    |
| **System max**       | `/proc/sys/fs/file-max`  | `sysctl kern.maxfiles`          |
| **Per-process max**  | —                        | `sysctl kern.maxfilesperproc`   |

**macOS defaults** (from research):

- `kern.maxfiles`: 12,288 (system)
- `kern.maxfilesperproc`: 10,240 (per process)
- `ulimit -n`: 256 (shell default; often too low for Node/LSP)

### 3.2 Counting FD Usage

| Platform  | Method                                      | Accuracy                             | Cost                |
| --------- | ------------------------------------------- | ------------------------------------ | ------------------- |
| **Linux** | `len(os.listdir("/proc/<pid>/fd"))`         | Exact                                | Low                 |
| **Linux** | `ls /proc/<pid>/fd 2>/dev/null \| wc -l`    | Exact                                | Low                 |
| **macOS** | `lsof -p <pid> \| grep -v " txt " \| wc -l` | Approx (excludes .txt = loaded libs) | Medium (lsof spawn) |
| **macOS** | `lsof -p <pid> -a -d 0-9999`                | FD num filter                        | Medium              |

**Stack Overflow finding**: On macOS, `lsof -p nnn` includes loaded frameworks (`.txt`); `grep -v " txt "` gets closer to actual FD count. Still not exact; use for relative comparison.

### 3.3 System-Wide FD Usage

| Platform  | Method                                                           |
| --------- | ---------------------------------------------------------------- |
| **Linux** | `cat /proc/sys/fs/file-nr` → (allocated, free, max)              |
| **macOS** | No direct sysctl; `lsof \| wc -l` (expensive) or sum per-process |

### 3.4 thegent Current State

`load_based_limits.py`:

- `_get_fd_usage()`: Returns `(used, limit)` for **current process only**.
- Linux: `len(os.listdir("/proc/self/fd"))` — correct.
- macOS: Falls back to `0` for used (no `/proc`); limit from `resource.getrlimit(RLIMIT_NOFILE)`.

**Gap**: On macOS, `fd_used` is 0 → FD gate is effectively disabled for ConcurrencyController.

---

## 4. CPU

### 4.1 Per-Process CPU

| Platform  | Method                                         | Notes                              |
| --------- | ---------------------------------------------- | ---------------------------------- |
| **Linux** | `/proc/<pid>/stat` fields 14+15 (utime, stime) | Jiffies; delta over interval = %   |
| **Linux** | `ps -o %cpu -p <pid>`                          | Instantaneous % (may be 0 if idle) |
| **macOS** | `ps -o %cpu -p <pid>`                          | Same                               |
| **macOS** | `top -l 1 -pid <pid>`                          | Parsing required                   |

**Cumulative CPU time**: `ps -o time -p <pid>` (e.g. `26:24.57` = 26 min 24 sec).

### 4.2 System Load Average

| Platform | Method                            |
| -------- | --------------------------------- |
| **Both** | `os.getloadavg()` → (1m, 5m, 15m) |

**Interpretation**: Load / CPU count = utilization. `load_per_cpu_max` gate in LimitGateConfig uses this.

### 4.3 thegent Current State

- `ResourceSnapshot.load_1m`, `load_5m`, `load_15m` from `os.getloadavg()`.
- `load_per_cpu_max` gate: block when `load_1m / cpu_count >= 1.5`.
- No per-process CPU sampling for prune or `thegent ps`.

---

## 5. Threads

### 5.1 Sampling

| Platform  | Method                                                |
| --------- | ----------------------------------------------------- |
| **Linux** | `cat /proc/<pid>/status \| grep Threads`              |
| **macOS** | `ps -o thcount -p <pid>` (may not exist on all macOS) |
| **macOS** | `ps -o nlwp -p <pid>` (BSD) or `task_info` (API)      |

**Note**: `ps` on macOS varies; `ps -o thcount` might be `-o threads` or similar. Check `ps -L` for thread count.

### 5.2 Relevance

- High thread count → context switching overhead.
- Node.js LSPs often spawn multiple threads.
- Could add thread-based prune: prefer killing processes with >N threads when over threshold.

---

## 6. Ports / Sockets

### 6.1 Sampling

| Platform  | Method                                                 |
| --------- | ------------------------------------------------------ |
| **Linux** | `ls -l /proc/<pid>/fd` → `readlink` for socket:[inode] |
| **Both**  | `lsof -p <pid> -i`                                     |
| **Both**  | `netstat -tulpn` (Linux) or `lsof -i` (macOS)          |

### 6.2 Relevance

- Port exhaustion: 65535 ports; ephemeral range 32768–60999 on typical Linux.
- MCP servers, LSPs, API proxies each use ports.
- Could trigger prune when ephemeral port usage > 80%.

---

## 7. Other Resources

### 7.1 Disk I/O

| Platform  | Method                                           |
| --------- | ------------------------------------------------ |
| **Linux** | `/proc/<pid>/io` (read_bytes, write_bytes)       |
| **macOS** | `iotop` (not native); `fs_usage` (requires root) |

### 7.2 GPU (VRAM)

| Platform   | Method               |
| ---------- | -------------------- |
| **NVIDIA** | `nvidia-smi`         |
| **Apple**  | `ioreg` or Metal API |

### 7.3 Battery

| Platform  | Method                                                |
| --------- | ----------------------------------------------------- |
| **macOS** | `pmset -g batt`; `ioreg -r -d 1 -n AppleSmartBattery` |

---

## 8. Sampling Strategies (Cross-Platform)

### 8.1 Minimal Overhead (for ConcurrencyController)

| Resource    | Linux                  | macOS                               |
| ----------- | ---------------------- | ----------------------------------- |
| FD (self)   | `/proc/self/fd`        | `resource.getrlimit` only (used=0)  |
| FD (system) | `/proc/sys/fs/file-nr` | `lsof \| wc -l` (expensive) or skip |
| Memory      | `/proc/meminfo`        | `vm_stat`                           |
| Load        | `getloadavg()`         | `getloadavg()`                      |

### 8.2 Per-Process (for Prune / `thegent ps --all`)

| Resource | Linux                                    | macOS                                                 |
| -------- | ---------------------------------------- | ----------------------------------------------------- |
| FD       | `ls /proc/<pid>/fd \| wc -l`             | `lsof -p <pid> \| grep -v " txt " \| wc -l`           |
| RSS      | `cat /proc/<pid>/status \| grep VmRSS`   | `ps -o rss -p <pid>`                                  |
| CPU %    | `ps -o %cpu -p <pid>`                    | `ps -o %cpu -p <pid>`                                 |
| Threads  | `cat /proc/<pid>/status \| grep Threads` | `ps -o thcount -p <pid>` or `ps -M -p <pid> \| wc -l` |

### 8.3 Batch Sampling (Efficient)

For multiple PIDs:

- **Linux**: Single `ps -eo pid,rss,%cpu,nlwp` + `/proc/<pid>/fd` per PID (or batch).
- **macOS**: `ps -eo pid,rss,%cpu` (threads vary by ps); `lsof` per PID is expensive — batch with `lsof -p pid1,pid2,...` or sample top N only.

---

## 9. Implementation Roadmap

### Phase 1: Fix FD on macOS (load_based_limits)

| Task              | Description                                                                              | Effort |
| ----------------- | ---------------------------------------------------------------------------------------- | ------ |
| **macOS fd_used** | Use `lsof -p $$ \| grep -v " txt " \| wc -l` for self, or `resource` module if available | 2–4    |
| **Fallback**      | If lsof too slow, sample every N seconds; cache                                          | 2–4    |

### Phase 2: Per-Process Metrics for Prune

| Task                | Description                                                   | Effort |
| ------------------- | ------------------------------------------------------------- | ------ |
| **RSS-aware prune** | Sort candidates by RSS; kill highest first                    | 6–8    |
| **FD-aware prune**  | When pruning, prefer processes with highest FD (free more FD) | 4–6    |
| **CPU-aware**       | Optional: deprioritize high-CPU (might be active)             | 4–6    |

### Phase 3: `thegent ps --system` or `thegent observe resources`

| Task                      | Description                                                                               | Effort |
| ------------------------- | ----------------------------------------------------------------------------------------- | ------ |
| **System process view**   | `thegent ps --system` or `thegent observe resources` — show top processes by RSS, FD, CPU | 10–15  |
| **Agent-specific filter** | `--agent` filter for node, bun, etc.                                                      | 2–4    |

### Phase 4: Extended Resource Gates

| Task             | Description                                   | Effort |
| ---------------- | --------------------------------------------- | ------ |
| **Thread gate**  | Block when system thread count > threshold    | 6–8    |
| **Port gate**    | Block when ephemeral port usage > 80% (Linux) | 8–12   |
| **Battery gate** | Lower threshold when on battery (macOS)       | 4–6    |

---

## 10. Configuration Schema (Proposed)

```yaml
# Add to config / .env
THGENT_CONCURRENCY_FD_UTILIZATION_MAX=0.75   # Existing
THGENT_CONCURRENCY_LOAD_PER_CPU_MAX=1.5      # Existing
THGENT_CONCURRENCY_MEM_AVAILABLE_MIN_MB=256  # Existing

# New: macOS FD sampling
THGENT_FD_SAMPLE_METHOD=lsof                 # lsof | proc | skip
THGENT_FD_SAMPLE_CACHE_SEC=60                # Cache lsof result (expensive)

# New: Prune prioritization
THGENT_PRUNE_SORT_BY=rss                     # rss | fd | cpu | none
THGENT_PRUNE_SORT_ORDER=desc                 # Kill highest first

# New: System resource view
THGENT_PS_SYSTEM_TOP_N=20                    # Top N processes for --system
THGENT_PS_SYSTEM_COLUMNS=pid,rss,cpu,fd,cmd # Columns for system view
```

---

## 11. Activity Monitor Column Mapping

From user's paste (macOS Activity Monitor):

| Column              | Example                     | Interpretation       |
| ------------------- | --------------------------- | -------------------- |
| Name                | node, Terminal, kernel_task | Process name         |
| CPU %               | 105.0, 82.3, 47.9           | CPU utilization      |
| Time                | 26:24.57                    | Cumulative CPU time  |
| Threads             | 22, 606, 21                 | Thread count         |
| PID                 | 3386, 76632, 0              | Process ID           |
| Memory (RSS)        | 1.19 GB, 1.33 GB            | Resident size        |
| Memory (Compressed) | 152.5 MB                    | Compressed (macOS)   |
| FD (?)              | 4,047, 8,115, 766           | Open files / sockets |
| Ports               | 0 bytes, No                 | Port usage           |

**Note**: FD column may be "Open Files and Ports" in Activity Monitor. `lsof -p <pid> | wc -l` approximates.

---

## 12. Cross-References

| Doc                                                                                             | Relevance                                             |
| ----------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| [SMART_ROBUST_STRATEGIES_RESEARCH](./SMART_ROBUST_STRATEGIES_RESEARCH.md)                       | Process lifecycle, LSP multiplexing, prune strategies |
| [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH](./SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md)           | Resource types (§21), disk, network, GPU, battery     |
| [ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH](./ADVANCED_STRATEGIES_AND_RESILIENCE_RESEARCH.md) | Retry, backoff, circuit breaker, bulkhead, fairness   |
| [load_based_limits.py](../../src/thegent/orchestration/load_based_limits.py)                    | Current ResourceSnapshot, gates                       |
| [SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH](./SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md) | Scheduling theory, ResourceSnapshot mapping           |

---

## 13. Bibliography & Sources

| Source                                                                                                                                              | Topic                               |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | --------------- | ------ |
| [Stack Overflow: macOS FD count](https://stackoverflow.com/questions/795236/in-mac-os-x-how-can-i-get-an-accurate-count-of-file-descriptor-usage)   | `lsof -p nnn                        | grep -v " txt " | wc -l` |
| [wilsonmar.github.io: macOS limits](https://wilsonmar.github.io/maximum-limits/)                                                                    | kern.maxfiles, kern.maxfilesperproc |
| [Super User: Too many open files](https://superuser.com/questions/433746/is-there-a-fix-for-the-too-many-open-files-in-system-error-on-os-x-10-7-1) | sysctl kern.maxfiles                |
| [hiltmon.com: ulimit on macOS](https://hiltmon.com/blog/2023/01/01/increasing-file-descriptor-ulimit-on-macos/)                                     | Permanent ulimit change             |

---

## 14. Performance Tuning Guide

### 14.1 System Resource Tuning

#### 14.1.1 File Descriptor Tuning

| Platform  | Location               | Current Default | Recommended | Command                                     |
| --------- | ---------------------- | --------------- | ----------- | ------------------------------------------- |
| **Linux** | `fs.file-max`          | 1627708         | 10000000    | `sysctl -w fs.file-max=10000000`            |
| **Linux** | `ulimit -n`            | 1024            | 65535       | `ulimit -n 65535`                           |
| **macOS** | `kern.maxfiles`        | 12288           | 65535       | `sudo sysctl -w kern.maxfiles=65535`        |
| **macOS** | `kern.maxfilesperproc` | 10240           | 50000       | `sudo sysctl -w kern.maxfilesperproc=50000` |
| **macOS** | `ulimit -n`            | 256             | 65535       | `ulimit -n 65535`                           |

#### 14.1.2 Persistent Tuning (Linux)

```bash
# Add to /etc/sysctl.conf
fs.file-max = 10000000
fs.nr_open = 10000000

# Add to /etc/security/limits.conf
*    soft    nofile    65535
*    hard    nofile    65535
root soft    nofile    65535
root hard    nofile    65535
```

#### 14.1.3 Persistent Tuning (macOS)

```bash
# Add to /etc/sysctl.conf
kern.maxfiles=65535
kern.maxfilesperproc=50000

# Add to ~/.zshrc or ~/.bash_profile
ulimit -n 65535
```

### 14.2 ConcurrencyController Tuning

#### 14.2.1 Gate Thresholds

| Gate                 | Conservative | Balanced | Aggressive |
| -------------------- | ------------ | -------- | ---------- |
| **FD Utilization**   | 0.50         | 0.75     | 0.90       |
| **Load per CPU**     | 1.0          | 1.5      | 2.0        |
| **Memory Available** | 512 MB       | 256 MB   | 128 MB     |
| **Min Slots**        | 2            | 1        | 1          |
| **Max Slots**        | 10           | 20       | 50         |

#### 14.2.2 Hysteresis Settings

| Parameter           | Conservative | Balanced | Aggressive |
| ------------------- | ------------ | -------- | ---------- |
| **Upper Threshold** | 0.70         | 0.80     | 0.90       |
| **Lower Threshold** | 0.30         | 0.40     | 0.50       |
| **Dwell Time**      | 60s          | 30s      | 15s        |

### 14.3 Prune Tuning

#### 14.3.1 Threshold Settings

| Scenario            | Threshold | Cooldown | Trigger        |
| ------------------- | --------- | -------- | -------------- |
| **Memory critical** | 512 MB    | 60s      | Memory only    |
| **Process count**   | 15        | 300s     | Count + Memory |
| **Light usage**     | 20        | 600s     | Periodic only  |
| **Heavy usage**     | 10        | 120s     | All triggers   |

#### 14.3.2 Process Priority for Prune

| Priority  | Process Type      | Reason          |
| --------- | ----------------- | --------------- |
| 1 (First) | cc-status         | High RSS, bloat |
| 2         | Stale MCP servers | Low utility     |
| 3         | Idle LSP servers  | Can restart     |
| 4         | Node/Bun runtimes | May be active   |

### 14.4 Sampling Performance

#### 14.4.1 Sampling Intervals

| Resource            | Sampling      | Cache TTL | Notes              |
| ------------------- | ------------- | --------- | ------------------ |
| **Memory**          | Every acquire | 5s        | Changes frequently |
| **Load avg**        | Every acquire | 5s        | Kernel metric      |
| **FD count**        | Every acquire | 10s       | Expensive on macOS |
| **Per-process RSS** | Every prune   | 30s       | Cached per PID     |
| **Per-process FD**  | Every prune   | 60s       | Very expensive     |

#### 14.4.2 macOS Optimization

```bash
# Use cached values when possible
export THGENT_FD_SAMPLE_CACHE_SEC=60
export THGENT_FD_SAMPLE_METHOD=proc  # Use /proc if available

# For macOS, prefer ps over lsof for speed
export THGENT_PRUNE_SORT_BY=rss  # RSS from ps, faster than lsof
```

### 14.5 Monitoring & Diagnostics

#### 14.5.1 Resource Commands

| Command                               | Purpose                        |
| ------------------------------------- | ------------------------------ | -------------------- | --------- | ---------------------- |
| `thegent ps`                          | List thegent-managed processes |
| `thegent observe resources`           | Show current resource snapshot |
| `cat /proc/self/status                | grep -E 'VmRSS                 | VmSize               | Threads'` | Process memory/threads |
| `ls /proc/self/fd \| wc -l`           | Current process FD count       |
| `ps -eo pid,rss,%cpu,comm --sort=-rss | head -20`                      | Top processes by RSS |

#### 14.5.2 Log Analysis

```bash
# Check prune logs
cat ~/.thegent/sessions/prune.log

# Check resource sampling logs
grep -r "ResourceSnapshot" ~/.thegent/logs/

# Check gate violations
grep -r "gate" ~/.thegent/logs/
```

### 14.6 Troubleshooting Guide

| Symptom                      | Likely Cause           | Solution                              |
| ---------------------------- | ---------------------- | ------------------------------------- |
| Prune never triggers         | Threshold too high     | Lower `THGENT_AUTO_PRUNE_THRESHOLD`   |
| Prune too aggressive         | Cooldown too short     | Increase `THGENT_AUTO_PRUNE_COOLDOWN` |
| FD gate always blocks        | macOS FD count = 0     | Fix macOS FD sampling                 |
| Memory always low            | Too many processes     | Increase prune frequency              |
| ConcurrencyController blocks | Load threshold too low | Increase `load_per_cpu_max`           |

---

## 15. Quick Reference Cards

### 15.1 Resource Sampling Quick Reference

| Metric               | Linux Command                | macOS Command                               |
| -------------------- | ---------------------------- | ------------------------------------------- | ------------------------ | ------------------ |
| **Memory available** | `cat /proc/meminfo           | grep MemAvailable`                          | `vm_stat                 | grep "Pages free"` |
| **Process RSS**      | `cat /proc/<pid>/status      | grep VmRSS`                                 | `ps -o rss -p <pid>`     |
| **FD count**         | `ls /proc/<pid>/fd \| wc -l` | `lsof -p <pid> \| grep -v " txt " \| wc -l` |
| **Thread count**     | `cat /proc/<pid>/status      | grep Threads`                               | `ps -o thcount -p <pid>` |
| **Load average**     | `uptime                      | awk '{print $10}'`                          | `uptime                  | awk '{print $10}'` |
| **CPU %**            | `ps -o %cpu -p <pid>`        | `ps -o %cpu -p <pid>`                       |

### 15.2 ConcurrencyController Configuration

```bash
# Conservative settings (for limited hardware)
export THGENT_CONCURRENCY_FD_UTILIZATION_MAX=0.50
export THGENT_CONCURRENCY_LOAD_PER_CPU_MAX=1.0
export THGENT_CONCURRENCY_MEM_AVAILABLE_MIN_MB=512
export THGENT_HYSTERESIS_UPPER_THRESHOLD=0.70
export THGENT_HYSTERESIS_LOWER_THRESHOLD=0.30
export THGENT_HYSTERESIS_DWELL_TIME_S=60

# Balanced settings (default)
export THGENT_CONCURRENCY_FD_UTILIZATION_MAX=0.75
export THGENT_CONCURRENCY_LOAD_PER_CPU_MAX=1.5
export THGENT_CONCURRENCY_MEM_AVAILABLE_MIN_MB=256
export THGENT_HYSTERESIS_UPPER_THRESHOLD=0.80
export THGENT_HYSTERESIS_LOWER_THRESHOLD=0.40
export THGENT_HYSTERESIS_DWELL_TIME_S=30

# Aggressive settings (powerful hardware)
export THGENT_CONCURRENCY_FD_UTILIZATION_MAX=0.90
export THGENT_CONCURRENCY_LOAD_PER_CPU_MAX=2.0
export THGENT_CONCURRENCY_MEM_AVAILABLE_MIN_MB=128
export THGENT_HYSTERESIS_UPPER_THRESHOLD=0.90
export THGENT_HYSTERESIS_LOWER_THRESHOLD=0.50
export THGENT_HYSTERESIS_DWELL_TIME_S=15
```

---

## EXTENSION_SUMMARY

**Extended on**: 2026-02-17
**Extensions added**: Performance tuning guide (§14), Quick reference cards (§15)

| Section | Added Content                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------ |
| §14.1   | System Resource Tuning (FD limits for Linux/macOS, commands, persistent config)                        |
| §14.2   | ConcurrencyController Tuning (gate thresholds, hysteresis settings - Conservative/Balanced/Aggressive) |
| §14.3   | Prune Tuning (threshold settings, process priority matrix)                                             |
| §14.4   | Sampling Performance (intervals, macOS optimization)                                                   |
| §14.5   | Monitoring & Diagnostics (resource commands, log analysis)                                             |
| §14.6   | Troubleshooting Guide (symptoms, causes, solutions)                                                    |
| §15.1   | Resource Sampling Quick Reference (Linux vs macOS commands)                                            |
| §15.2   | ConcurrencyController Configuration (environment variables for different profiles)                     |

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [SYSTEM_RESOURCES_COMPLETE.md](./SYSTEM_RESOURCES_COMPLETE.md) - Complete guide
- [SWARM_COMPLETE.md](./SWARM_COMPLETE.md) - Swarm guide
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
