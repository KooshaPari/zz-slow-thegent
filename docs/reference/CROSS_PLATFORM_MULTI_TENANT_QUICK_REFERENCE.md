# Cross-Platform Multi-Tenant Desktop Automation Quick Reference

**Purpose:** Quick reference for Windows/Linux/macOS support, agent-user isolation, multi-tenant coordination, and desktop automation.

**Date:** 2026-02-16
**Status:** Reference (Polished & Extended)
**Last Updated:** 2026-02-16
**Related:**

- `docs/research/CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md` (Main research)
- `docs/plans/CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN.md` (Implementation plan)
- `docs/research/CROSS_PLATFORM_INTEGRATION_GUIDE.md` (Integration guide)
- `docs/research/CROSS_PLATFORM_PERFORMANCE_BENCHMARKS.md` (Performance SLAs)
- `docs/research/CROSS_PLATFORM_SECURITY_DEEP_DIVE.md` (Security analysis)

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    thegent Desktop Automation System                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
            │   macOS      │ │   Windows   │ │   Linux     │
            │  Provider    │ │  Provider   │ │  Provider   │
            │              │ │             │ │             │
            │ AppleScript  │ │ UI Auto     │ │ AT-SPI      │
            │ Apple Events │ │ (UIA)       │ │ D-Bus       │
            └──────┬───────┘ └──────┬──────┘ └──────┬──────┘
                   │                │                │
                   └────────────────┼────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │   DesktopAutomationProvider    │
                    │        (Abstract Base)         │
                    │  - click()                     │
                    │  - type_text()                 │
                    │  - find_element()              │
                    │  - screenshot()                │
                    └───────────────┬───────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼────────┐      ┌───────────▼──────────┐      ┌─────────▼────────┐
│  Coordinator   │      │  Security Layer      │      │  Observability   │
│  (Multi-Tenant)│      │                      │      │                  │
│                │      │  - Input Validation  │      │  - OTel Traces   │
│  - EditLease   │      │  - App Verification  │      │  - Prometheus    │
│  - Redis Lock  │      │  - Screenshot        │      │  - Run Registry  │
│  - Consensus   │      │    Redaction         │      │                  │
│  - User Activity│     │  - Audit Logging     │      │  - Metrics       │
└───────┬────────┘      └──────────────────────┘      └──────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────────┐
│                    Integration Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Cost Tracking│  │ Rate Limiting│  │ State        │              │
│  │              │  │              │  │ Persistence   │              │
│  │ - Budget     │  │ - TokenBucket│  │ - Checkpoints│              │
│  │ - Aggregator │  │ - RetryBudget│  │ - Continuity │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────────┐
│                         MCP Tools Layer                              │
│  - desktop_automation_click                                          │
│  - desktop_automation_type                                           │
│  - desktop_automation_find                                           │
│  - desktop_automation_screenshot                                     │
│  - desktop_automation_wait_for_user_idle                             │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Decisions

### Agent-User Model: Hybrid (Sub-User + Optional OS Users)

**Default:** Sub-user model (fast, no permissions required)
**Opt-in:** OS user model (true isolation, requires admin/root)

```python
# Configuration
isolation_mode: "subuser" | "osuser" | "docker"
```

### Multi-Tenant Coordination

**Policies:**

- **User Priority:** User always wins over agents
- **FIFO:** First agent wins in agent-agent conflicts
- **Resource Limits:** Per-tenant process limits

**Coordination Mechanisms:**

- File-level: Tenant-aware edit leases
- UI Automation: Desktop automation coordinator + user activity detection
- Process: Tenant-aware concurrency controller

### Desktop Automation: Platform-Specific Providers

| Platform    | Provider                 | Library          | Permission               |
| ----------- | ------------------------ | ---------------- | ------------------------ |
| **macOS**   | AppleScript/Apple Events | `py-applescript` | Accessibility            |
| **Windows** | UI Automation (UIA)      | `pywinauto`      | UIA Access               |
| **Linux**   | AT-SPI                   | `pyatspi`        | AT-SPI (usually default) |

---

## Configuration

```yaml
# ~/.thegent/config.yaml

isolation:
  mode: "subuser" # subuser | osuser | docker
  osuser_pool_size: 10
  osuser_base_path: "/var/lib/thegent/agents" # Linux/macOS
  # Windows: C:\ProgramData\thegent\agents

multi_tenant:
  user_priority: true
  conflict_resolution: "user_priority" # user_priority | fifo | resource_limits
  user_idle_threshold_seconds: 5.0
  max_user_processes: 5
  max_agent_processes: 10
  max_total_processes: 15

desktop_automation:
  enabled: true
  platforms:
    macos:
      provider: "applescript"
      require_accessibility_permission: true
    windows:
      provider: "uiautomation"
    linux:
      provider: "atspi"
  coordination:
    check_user_activity: true
    wait_for_idle: true
    idle_threshold_seconds: 5.0
```

---

## CLI Usage

```bash
# Run selected agent in default mode
thegent run agent "Task" --agent claude

# Run with OS user isolation (requires admin/root)
thegent run agent "Task" --agent claude --isolation-mode osuser

# Check desktop automation permissions
thegent desktop-automation check-permissions

# Test desktop automation
thegent desktop-automation test-click --selector "button[name='Save']"
```

---

## MCP Tools

```python
# Desktop automation tools (via MCP)
desktop_automation_click(selector: str, wait_timeout: float = 5.0) -> dict
desktop_automation_type(selector: str, text: str, wait_timeout: float = 5.0) -> dict
desktop_automation_find(selector: str, timeout: float = 5.0) -> dict
desktop_automation_screenshot(region: Optional[dict] = None) -> dict
desktop_automation_wait_for_user_idle(idle_seconds: float = 5.0) -> dict
```

---

## Platform Setup

### macOS

**Permissions:**

1. System Preferences > Security & Privacy > Privacy > Accessibility
2. Add Terminal/iTerm/thegent to allowed apps

**Testing:**

```bash
# Test AppleScript
osascript -e 'tell application "System Events" to get name of every process'

# Test Accessibility API
python -c "from thegent.infra.desktop_automation import get_provider; p = get_provider(); print(p.find_element('button[name=\"Save\"]'))"
```

### Windows

**Permissions:**

1. Run as Administrator (for UIA Access)
2. Or grant via Group Policy: `Computer Configuration > Policies > Windows Settings > Security Settings > Local Policies > User Rights Assignment > Access this computer from the network`

**Testing:**

```powershell
# Test UIA (requires pywinauto)
python -c "from pywinauto import Application; app = Application().start('notepad.exe'); print(app.window())"
```

### Linux

**Permissions:**

- AT-SPI usually works by default
- For X11: Ensure X11 display is accessible
- For systemd: Ensure user session is active

**Testing:**

```bash
# Test AT-SPI
python -c "import pyatspi; desktop = pyatspi.Registry.getDesktop(0); print(desktop)"

# Check AT-SPI service
systemctl --user status at-spi-dbus-bus.service
```

---

## Comprehensive Troubleshooting Guide

### Common Issues & Solutions

#### Issue: Permission Denied

**Symptoms:**

- Automation fails with "Permission denied" or "Accessibility permission required"
- Element finding returns None
- Screenshots fail

**Diagnosis:**

```bash
# Check permissions (macOS)
thegent desktop-automation check-permissions

# Check permissions (Windows)
# Run as administrator or check Group Policy

# Check permissions (Linux)
# Usually granted by default
```

**Solutions:**

**macOS:**

1. Open System Preferences
2. Security & Privacy > Accessibility
3. Add thegent to allowed apps
4. Security & Privacy > Screen Recording (for screenshots)
5. Add thegent to allowed apps

**Windows:**

1. Run as administrator, OR
2. Configure Group Policy:
   - Computer Configuration > Policies > Windows Settings > Security Settings > Local Policies > User Rights Assignment
   - Add user to "Access this computer from the network"

**Linux:**

- Usually granted by default
- May need AT-SPI configuration for some desktop environments

#### Issue: Element Not Found

**Symptoms:**

- `find_element()` returns None
- Selector doesn't match
- Element exists but not found

**Diagnosis:**

```python
# Enable debug logging
import logging

logging.basicConfig(level=logging.DEBUG)

# Try finding element
element = provider.find_element("button[name='Save']")
if not element:
    # Try alternate selectors
    element = provider.find_element("//button[@name='Save']")  # XPath
    element = provider.find_element("Save")  # Accessibility name
```

**Solutions:**

1. **Wait for element to load:**

   ```python
   element = provider.find_element("button", timeout_ms=10000)  # Wait up to 10s
   ```

2. **Use cached elements:**

   ```python
   # Elements are cached automatically
   element = provider.find_element("button")  # First call: 500ms
   element = provider.find_element("button")  # Cached: 10ms
   ```

3. **Try alternate selectors:**
   - Accessibility name: `"Save"`
   - Role + name: `"button[name='Save']"`
   - XPath: `"//button[@name='Save']"`
   - Coordinates (last resort): `{"x": 100, "y": 200}`

#### Issue: Rate Limit Exceeded

**Symptoms:**

- Automation fails with "Rate limit exceeded"
- Actions throttled
- High automation frequency

**Diagnosis:**

```bash
# Check rate limit status
thegent observe metrics --category automation

# Check token bucket status
thegent automation rate-limit-status
```

**Solutions:**

1. **Reduce automation frequency:**

   ```python
   # Add delays between actions
   time.sleep(0.5)  # 500ms delay
   ```

2. **Increase rate limit:**

   ```yaml
   desktop_automation:
     rate_limits:
       global_actions_per_minute: 200 # Increase from 100
   ```

3. **Use batch operations:**
   ```python
   # Batch multiple clicks
   provider.execute_batch(
       [
           AutomationAction(type="click", selector="button1"),
           AutomationAction(type="click", selector="button2"),
       ]
   )
   ```

#### Issue: Cost Budget Exceeded

**Symptoms:**

- Automation blocked due to budget
- Budget warnings in logs
- High automation costs

**Diagnosis:**

```bash
# Check automation budget
thegent observe cost-status --category automation

# Check budget utilization
thegent govern cost --category automation
```

**Solutions:**

1. **Optimize automation actions:**
   - Use cached elements (reduces find_element cost)
   - Batch operations (reduces overhead)
   - Use incremental screenshots (reduces screenshot cost)

2. **Increase automation budget:**

   ```yaml
   desktop_automation:
     budget_mtd: 20.0 # Increase from 10.0
   ```

3. **Monitor and optimize:**
   ```bash
   # Analyze automation costs
   thegent observe automation-costs --days 7
   ```

#### Issue: User Interruption

**Symptoms:**

- Automation pauses unexpectedly
- "User activity detected" messages
- Automation resumes after delay

**Diagnosis:**

```bash
# Check user activity detection
thegent desktop-automation user-activity-status

# Check automation locks
thegent automation locks
```

**Solutions:**

1. **Adjust idle threshold:**

   ```yaml
   desktop_automation:
     coordination:
       idle_threshold_seconds: 10.0 # Increase from 5.0
   ```

2. **Disable user activity detection (not recommended):**

   ```yaml
   desktop_automation:
     coordination:
       check_user_activity: false # Not recommended
   ```

3. **Use automation locks:**
   ```python
   # Acquire lock to prevent interruption
   if coordinator.acquire_lock(scope, agent_id):
       # Automation protected from interruption
       result = provider.click(element)
   ```

### Debugging Workflow

**Step 1: Enable Debug Logging**

```bash
export THGENT_DEBUG=1
export THGENT_LOG_LEVEL=DEBUG
thegent run agent "automation test" --agent claude --debug
```

**Step 2: Collect Diagnostics**

```bash
# Check automation locks
thegent automation locks

# View recent automation events
thegent observe automation-events --limit 50

# Check performance metrics
thegent observe metrics --category automation

# Check OTel traces
# Query Jaeger/Tempo for automation traces
```

**Step 3: Analyze Logs**

```bash
# Check run registry
cat .thegent/sessions/*/run_registry.jsonl | grep automation | jq '.'

# Check audit logs
cat .thegent/sessions/*/automation_audit_*.jsonl | jq '.'

# Check error logs
cat .thegent/sessions/*/automation_errors.log
```

**Step 4: Review Traces**

- Open OTel trace viewer (Jaeger/Tempo)
- Filter by `automation.action`, `automation.platform`
- Look for latency spikes, errors, failures
- Analyze span attributes for context

### Performance Troubleshooting

**Slow Element Finding:**

- **Cause:** Deep accessibility tree, inefficient selector
- **Fix:** Use cached elements, optimize selector, use coordinates

**High Screenshot Latency:**

- **Cause:** Large screen resolution, full screenshot
- **Fix:** Use incremental screenshots, capture regions only

**High CPU Usage:**

- **Cause:** Frequent screenshots, inefficient tree traversal
- **Fix:** Cache elements, reduce screenshot frequency, optimize algorithms

### Security Troubleshooting

**Input Injection Attempts:**

- **Symptoms:** Validation errors, security warnings
- **Fix:** Review selector/text input, ensure validation enabled

**Permission Denial:**

- **Symptoms:** Permission errors, access denied
- **Fix:** Grant permissions, verify app trust, check privileges

**Screenshot Leakage:**

- **Symptoms:** Security warnings, audit alerts
- **Fix:** Enable screenshot redaction, encrypt screenshots

---

## Troubleshooting

### Issue: "Permission denied" when creating OS user

**Solution:** Run with admin/root privileges, or use sub-user mode (default).

### Issue: Desktop automation fails with "Accessibility permission denied"

**Solution:**

- macOS: Grant Accessibility permission in System Preferences
- Windows: Run as Administrator or grant UIA Access
- Linux: Ensure AT-SPI service is running

### Issue: Agent conflicts with user input

**Solution:**

- Enable user activity detection: `check_user_activity: true`
- Increase idle threshold: `idle_threshold_seconds: 10.0`
- Use coordination locks: Agents wait for user idle

### Issue: Too many processes spawned

**Solution:**

- Adjust limits: `max_user_processes`, `max_agent_processes`, `max_total_processes`
- Use concurrency controller: `thegent run --max-processes 5`

---

## Implementation Status

| Phase                             | Status     | Deliverable                                                     |
| --------------------------------- | ---------- | --------------------------------------------------------------- |
| **P1: User Isolation**            | ⏳ Planned | SystemUser abstraction, OS user creation, AgentUserPool         |
| **P2: Multi-Tenant Coordination** | ⏳ Planned | Tenant-aware leases, user activity detection, conflict resolver |
| **P3: Desktop Automation**        | ⏳ Planned | Platform providers (macOS/Windows/Linux)                        |
| **P4: MCP Integration**           | ⏳ Planned | MCP tools + resources                                           |
| **P5: Testing & Polish**          | ⏳ Planned | Cross-platform tests, documentation                             |

**Legend:** ⏳ Planned | 🚧 In Progress | ✓ Done

---

## Key Files

```
src/thegent/infra/
  ├── user_isolation.py          # SystemUser abstraction
  ├── os_user_manager.py         # OS user creation (macOS/Linux/Windows)
  ├── user_pool.py               # AgentUserPool
  ├── user_activity.py           # User activity detection
  ├── desktop_coordinator.py     # Desktop automation coordination
  ├── conflict_resolver.py       # Conflict resolution policies
  └── desktop_automation/
      ├── base.py                # DesktopAutomationProvider abstract
      ├── macos.py               # macOS provider (AppleScript)
      ├── windows.py             # Windows provider (UIA)
      └── linux.py               # Linux provider (AT-SPI)

src/thegent/mcp_server.py        # MCP tools registration
```

---

## References

- **Research:** `docs/research/CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md`
- **Plan:** `docs/plans/CROSS_PLATFORM_MULTI_TENANT_IMPLEMENTATION_PLAN.md`
- **Sandboxing:** `docs/governance/SANDBOXING_DESIGN.md`
- **Process Optimization:** `docs/research/SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md`

---

**Last Updated:** 2026-02-16

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
