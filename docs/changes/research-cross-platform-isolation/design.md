# Cross-Platform User Isolation Implementation - Design

**Date**: 2026-02-18
**Status**: Design Phase
**Version**: 1.0

---

## 1. System Architecture

### 1.1 Core Components

```
┌─────────────────────────────────────────────────────────┐
│           Agent Execution Orchestrator                  │
│           (thegent/core/executor.py)                    │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌───────────────┐ ┌──────────────┐ ┌────────────────┐
│IsolationMode  │ │FileCoordinator│ │DesktopAuto    │
│              │ │ (EditLease)   │ │ Coordinator    │
├───────────────┤ │              │ │                │
│ SubUserIso   │ │ • Lease mgmt  │ │ • Activity det │
│ OSUserIso    │ │ • Lock paths  │ │ • Queue sched  │
│ ContainerIso │ │ • Conflict log│ │ • Preemption   │
└───────────────┘ └──────────────┘ └────────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌────────────────┐         ┌──────────────────┐
│Platform         │         │ConcurrencyCtl    │
│Providers        │         │(Per-Tenant)      │
│                 │         │                  │
│ • macOS         │         │ • Limits         │
│ • Linux         │         │ • Escalation Qx  │
│ • Windows       │         │ • Metrics        │
└────────────────┘         └──────────────────┘
```

### 1.2 Core Implementation Files

| File                                             | Purpose                                  | LOC           |
| ------------------------------------------------ | ---------------------------------------- | ------------- |
| `thegent/isolation/sub_user_provider.py`         | Sub-user context allocation & execution  | 300           |
| `thegent/isolation/os_user_provider.py`          | OS user isolation (sudoers + user mgmt)  | 350           |
| `thegent/coordination/edit_lease_manager.py`     | Tenant-aware file locks                  | 250           |
| `thegent/coordination/desktop_coordinator.py`    | Desktop action scheduling & coordination | 400           |
| `thegent/coordination/user_activity_detector.py` | User input/window detection              | 200           |
| `thegent/desktop/macos.py`                       | macOS AppleScript provider               | 200           |
| `thegent/desktop/linux.py`                       | Linux AT-SPI provider                    | 250           |
| `thegent/desktop/windows.py`                     | Windows UI Automation provider           | 250           |
| `thegent/audit/isolation_auditor.py`             | Audit logging & compliance               | 150           |
| **Tests**                                        | Unit, integration, security, performance | 1500+         |
| **Total**                                        |                                          | **3700+ LOC** |

---

## 2. Sub-User Isolation (Lightweight, Default)

### 2.1 Allocation & Context

Process-level isolation without OS-level user creation:

```
┌─────────────────────────────────────────┐
│     thegent Main Process (root-owned)   │
│                                         │
│  ┌──────────────────────────────────┐ │
│  │ Sub-User Context 1 (uid: 1001)  │ │
│  │ • Environment: THEGENT_TENANT_ID │ │
│  │ • HOME: /tmp/thegent/tenant-1    │ │
│  │ • No setuid/setgid (no perms)    │ │
│  └──────────────────────────────────┘ │
│  ┌──────────────────────────────────┐ │
│  │ Sub-User Context 2 (uid: 1002)  │ │
│  │ • Environment: THEGENT_TENANT_ID │ │
│  │ • HOME: /tmp/thegent/tenant-2    │ │
│  └──────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Trade-off**: Fast startup (1ms), no permissions needed, but **no filesystem isolation** (shared `/tmp`, shared home dirs).

### 2.2 Environment Variables (Isolation Marker)

```bash
# Subprocess gets:
THEGENT_TENANT_ID=tenant-abc123
THEGENT_AGENT_ID=agent-456
THEGENT_ISOLATION_MODE=sub-user
HOME=/tmp/thegent/tenant-abc123
USER=thegent-tenant-a
```

Agents read `THEGENT_TENANT_ID` to implement tenant awareness in their own code (e.g., namespace cache keys, log file paths).

---

## 3. OS User Isolation (Strong, Optional)

### 3.1 OS User Setup

Creates distinct OS users with separate home directories:

```bash
# Sudoers config (auto-generated)
thegent-agent-1 ALL=(ALL) NOPASSWD:/usr/bin/thegent
thegent-agent-2 ALL=(ALL) NOPASSWD:/usr/bin/thegent
...

# Home directories
/home/thegent-agent-1/.config    (isolated config)
/home/thegent-agent-1/.local     (isolated cache)
/home/thegent-agent-2/.config    (isolated config)
```

**Trade-off**: Strong isolation (true OS-level), but requires admin setup and ~50ms overhead per action.

### 3.2 User Creation Helper

```bash
# Auto-create users and sudoers config
thegent isolation setup-os-user --num-users 5 --base-user thegent-prod
```

---

## 4. File-Level Coordination

### 4.1 Lease File Structure

```
/run/thegent/leases/
├── tenant-abc123/
│   ├── a1b2c3d4e5f6g7h8.lock    (file: /path/to/file.py)
│   └── x9y8z7w6v5u4t3s2.lock    (file: /path/to/config.yaml)
└── tenant-def456/
    └── m1n2o3p4q5r6s7t8.lock    (file: /path/to/file.py)
```

**Lock File Format** (JSON):

```json
{
  "lease_id": "tenant-abc123:file.py:1708345234567890123",
  "tenant_id": "tenant-abc123",
  "agent_id": "agent-xyz789",
  "filepath": "/path/to/file.py",
  "acquired_at": "2026-02-18T10:30:45.123Z",
  "operations": ["read", "write"]
}
```

### 4.2 Conflict Detection Logic

```python
# Pseudocode: acquire_lease(filepath, tenant_id)
lock_path = "/run/thegent/leases/{tenant_id}/{hash(filepath)}.lock"

if lock_path exists:
    read existing_lease from lock_path
    if existing_lease.tenant_id != tenant_id:
        # CONFLICT: Different tenant holds lock
        raise LeaseConflictError(existing_lease.tenant_id)

# Write new lease
write lock_path with current lease_data
return lease
```

---

## 5. Desktop Automation Coordinator

### 5.1 Action Scheduling & Queueing

```
┌──────────────────────────────────────────┐
│   Desktop Automation Coordinator         │
├──────────────────────────────────────────┤
│                                          │
│  ┌─ Action Queue (Priority) ─────────┐  │
│  │ (tenant, action, priority)        │  │
│  │ Scheduled: agent-1: click (p=0)   │  │
│  │ Queued:    agent-2: type (p=0)    │  │
│  │ Queued:    agent-1: hotkey (p=0)  │  │
│  └──────────────────────────────────┘  │
│                                          │
│  ┌─ User Activity Monitor ────────────┐ │
│  │ IsUserActive: false                │ │
│  │ LastUserAction: 15s ago            │ │
│  │ ActiveWindow: "Code"               │ │
│  └──────────────────────────────────┘ │
│                                          │
│  ┌─ Platform Provider (macOS) ──────┐  │
│  │ execute(action) → AppleScript    │  │
│  └──────────────────────────────────┘ │
│                                          │
└──────────────────────────────────────────┘
```

### 5.2 Scheduling Policy

1. **Check user activity**: If user active, defer action by 5 seconds
2. **Queue by tenant & priority**: FIFO within priority level
3. **Execute with delays**: 100ms between agent actions (reduce UI thrashing)
4. **Retry on failure**: Exponential backoff (0.5s, 1s, 2s, 4s)

---

## 6. User Activity Detection

### 6.1 Platform Detection Logic

**macOS**:

```
osascript: "tell app System Events name of (first app process whose frontmost is true)"
→ Returns active app name (e.g., "Code", "Terminal")
```

**Linux**:

```
x11: XGetInputFocus() → Active window
OR AT-SPI: dbus query active window accessible object
```

**Windows**:

```
ctypes: GetForegroundWindow() → Active window hwnd
→ GetWindowText(hwnd) → Window title
```

### 6.2 Activity Threshold

User is considered "active" if any input/window change in last **5 seconds** (configurable).

---

## 7. Configuration Reference

```yaml
# ~/.thegent/config.yaml

isolation:
  # Mode: "sub-user" (default), "os-user", "docker"
  mode: "sub-user"

  # Sub-user configuration
  sub_user:
    prefix: "thegent" # thegent-tenant-abc123
    base_uid: 1000 # UID offset start
    home_dir_template: "/tmp/thegent/{tenant_id}"

  # OS user configuration (if mode: "os-user")
  os_user:
    prefix: "thegent-agent-" # thegent-agent-1, etc.
    base_home: "/home"
    sudo_nopasswd: true

coordination:
  # File-level coordination
  file_locks:
    enabled: true
    lock_dir: "/run/thegent/leases"
    lease_timeout_sec: 300

  # Desktop automation coordination
  desktop:
    enabled: true
    activity_threshold_sec: 5
    action_delay_ms: 100
    action_queue_max: 100
    retry_count: 3

  # Process concurrency
  concurrency:
    per_tenant_max: 3
    user_priority: true
    agent_fifo: true

# Platform-specific providers
platform:
  macos:
    desktop_provider: "applescript" # or "accessibility"
  linux:
    desktop_provider: "at-spi" # or "x11"
  windows:
    desktop_provider: "uiautomation"

audit:
  enabled: true
  log_dir: "/var/log/thegent"
  retention_days: 90
```

---

## 8. Performance Characteristics

### 8.1 Latency Budget (p95)

| Operation              | Latency | Budget | Notes                       |
| ---------------------- | ------- | ------ | --------------------------- |
| Sub-user allocation    | <1ms    | 5ms    | Hash-based UID assignment   |
| Lease acquire          | <50ms   | 100ms  | File write + conflict check |
| Desktop action execute | <200ms  | 500ms  | Platform provider call      |
| User activity check    | <50ms   | 100ms  | Window manager query        |

### 8.2 Success Rate Target

- **Lease acquisition**: >95% (conflict rare in well-behaved agents)
- **Desktop action execution**: >95% (retry handles transients)
- **Overall isolation**: >99% (no cross-tenant data leaks)

---

## 9. Testing Checklist

### Phase 1: Sub-User Isolation

- [ ] Allocate tenant, verify UID/GID set
- [ ] Execute command in context, verify env vars
- [ ] Multiple tenants execute concurrently without interference
- [ ] Cleanup releases resources

### Phase 2: Edit Lease Manager

- [ ] Single tenant acquires & releases lease
- [ ] Conflict detected when different tenant tries to acquire same file
- [ ] Multiple files acquired in batch
- [ ] Lease timeout auto-expires

### Phase 3: Desktop Coordinator

- [ ] macOS: click, type, hotkey actions work
- [ ] Linux: AT-SPI actions work
- [ ] Windows: UI Automation actions work
- [ ] User activity detection pauses agent actions
- [ ] Action retry succeeds after transient failure
- [ ] Concurrent actions queued correctly (no UI collision)

### Phase 4: OS User Isolation

- [ ] Users created with correct UIDs/home dirs
- [ ] Sudoers config generated correctly
- [ ] OS user execution works (and isolation verified)
- [ ] Cleanup removes users

### Phase 5: Integration & Security

- [ ] Multiple concurrent agents with different isolation modes
- [ ] Audit log captures all events
- [ ] Cross-tenant file access prevented (security test)
- [ ] Capability matrix enforced

---

## 10. Rollback & Safety

### 10.1 Backward Compatibility

- **No breaking changes**: Existing agents work without modification
- **Sub-user default**: No extra permissions required
- **Opt-in OS user**: User enables explicitly

### 10.2 Rollback Strategy

1. **Phase 1-2**: Safe (file-based coordination, no process changes)
2. **Phase 3**: Gradual (desktop actions can be disabled per-tenant)
3. **Phase 4**: Safe (OS users remain on system, can be cleaned up manually)

---

## References

- **Proposal**: `proposal.md` (scope, decisions, roadmap)
- **Tasks**: `tasks.md` (detailed milestones and acceptance criteria)
- **Research**: `docs/research/CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md` (background)
