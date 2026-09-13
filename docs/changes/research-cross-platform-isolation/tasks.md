---
task_id: research-cross-platform-isolation
status: in_progress
---

# Cross-Platform User Isolation Implementation - Tasks & Milestones

**Date**: 2026-02-18
**Total Effort**: 5-6 weeks (phased)
**Total Tasks**: 35+ (across 5 phases)

---

## Phase 1: Sub-User Isolation (Week 1-2)

### 1.1 Infrastructure & Setup

- [ ] **Task 1.1.1**: Create `thegent/isolation/` module directory
  - Add `__init__.py`, `exceptions.py`, `models.py`
  - Define `TenantContext`, `IsolationMode` enums
  - **Acceptance**: Module importable, no dependencies

- [ ] **Task 1.1.2**: Create `thegent/isolation/base_provider.py`
  - Abstract `IsolationProvider` interface
  - Methods: `allocate_tenant()`, `execute_in_context()`, `cleanup_tenant()`
  - **Acceptance**: Interface defined, passes type checker

### 1.2 Sub-User Implementation

- [ ] **Task 1.2.1**: Implement `SubUserIsolationProvider`
  - UID/GID allocation via hash(tenant_id) % 1000
  - Home directory: `/tmp/thegent/{tenant_id}`
  - Environment variable injection: `THEGENT_TENANT_ID`, `THEGENT_AGENT_ID`
  - **Acceptance**: Provider instantiable, tests pass (see 1.3)
  - **LOC**: ~250

- [ ] **Task 1.2.2**: Implement `execute_in_context()`
  - Wrap `subprocess.run()` with tenant context (env vars, cwd)
  - Error handling: timeout, execution errors
  - **Acceptance**: Can execute command in tenant context, env vars set correctly

### 1.3 Unit Tests (Sub-User)

- [ ] **Task 1.3.1**: Basic allocation tests
  - `test_allocate_tenant_creates_context`
  - `test_allocate_tenant_idempotent` (same tenant returns same context)
  - `test_multiple_tenants_different_uids`
  - **Acceptance**: 3/3 tests pass

- [ ] **Task 1.3.2**: Execution tests
  - `test_execute_simple_command`
  - `test_execute_sets_env_vars`
  - `test_execute_timeout`
  - `test_execute_error_handling`
  - **Acceptance**: 4/4 tests pass

- [ ] **Task 1.3.3**: Cleanup tests
  - `test_cleanup_releases_context`
  - `test_cleanup_idempotent`
  - **Acceptance**: 2/2 tests pass

### 1.4 Integration with Agent Executor

- [ ] **Task 1.4.1**: Modify `thegent/core/executor.py`
  - Add `isolation_provider: SubUserIsolationProvider` parameter
  - Pass tenant context to `execute_in_context()` in main execution path
  - **Acceptance**: Executor can use isolation provider without breaking existing logic

### 1.5 Configuration Schema

- [ ] **Task 1.5.1**: Add isolation config to `config.yaml` schema
  - `isolation.mode: "sub-user" | "os-user" | "docker"`
  - `isolation.sub_user.prefix`, `base_uid`, `home_dir_template`
  - **Acceptance**: Config loads and validates

### Phase 1 Completion

- [ ] All tests pass (8+ unit tests)
- [ ] No regressions in existing executor tests
- [ ] Documentation: `design.md` section 2 complete

---

## Phase 2: Edit Lease Manager Enhancement (Week 3)

### 2.1 Lease Manager Refactoring

- [ ] **Task 2.1.1**: Extend existing `EditLeaseManager` with tenant awareness
  - Add `tenant_id` field to `EditLease` dataclass
  - Update `acquire_lease()` signature: `acquire_lease(tenant_id, filepaths, timeout_sec)`
  - **Acceptance**: Existing lease tests still pass, tenant field present

- [ ] **Task 2.1.2**: Implement conflict detection
  - `_check_conflicts(lock_path, current_tenant_id)` method
  - Raise `LeaseConflictError` if different tenant holds lock
  - **Acceptance**: Conflict detection logic correct

### 2.2 Lock File Management

- [ ] **Task 2.2.1**: Implement tenant-aware lock paths
  - Path: `/run/thegent/leases/{tenant_id}/{hash(filepath)}.lock`
  - Create `_get_lock_path()` method
  - Platform-safe: handle Windows paths, long filenames
  - **Acceptance**: Lock paths generated correctly for all platforms

- [ ] **Task 2.2.2**: Lock file format & serialization
  - JSON schema: `lease_id`, `tenant_id`, `filepath`, `acquired_at`, `operations`
  - Serialization: `json.dump()` + atomicity
  - **Acceptance**: Lock file readable, schema valid

### 2.3 Unit Tests (Leases)

- [ ] **Task 2.3.1**: Single-tenant lease tests
  - `test_acquire_lease_single_file`
  - `test_acquire_lease_multiple_files`
  - `test_lease_released_on_exit`
  - `test_lease_conflict_same_file_same_tenant` (should succeed)
  - **Acceptance**: 4/4 tests pass

- [ ] **Task 2.3.2**: Multi-tenant conflict tests
  - `test_lease_conflict_different_tenants` (should raise `LeaseConflictError`)
  - `test_concurrent_acquire_conflict` (async conflict)
  - `test_lease_auto_expire_timeout`
  - **Acceptance**: 3/3 tests pass

- [ ] **Task 2.3.3**: Integration tests
  - `test_lease_with_actual_file_operations`
  - `test_lease_cleanup_removes_lock_file`
  - **Acceptance**: 2/2 tests pass

### 2.4 Integration with Agent Executor

- [ ] **Task 2.4.1**: Wire lease manager into executor
  - `async with self.lease_manager.acquire_lease(tenant_id, files):`
  - Ensure leases released after execution
  - **Acceptance**: Executor uses leases, no deadlocks

### Phase 2 Completion

- [ ] All tests pass (9+ lease-specific tests)
- [ ] No regressions in existing file operation tests
- [ ] Documentation: `design.md` section 4 complete

---

## Phase 3: Desktop Automation Coordinator (Weeks 4-5)

### 3.1 Desktop Coordinator Core

- [ ] **Task 3.1.1**: Implement `DesktopAutomationCoordinator` base class
  - Action queueing (asyncio.PriorityQueue)
  - `schedule_action(tenant_id, action_type, target, priority)` method
  - `_execute_action_with_retry()` logic
  - **Acceptance**: Coordinator instantiable, action queue works
  - **LOC**: ~300

- [ ] **Task 3.1.2**: Implement action execution loop
  - Async task management (`_active_actions` dict)
  - Error handling & retry with exponential backoff
  - Metrics recording (success/failure)
  - **Acceptance**: Actions execute, retries work, metrics recorded

### 3.2 User Activity Detection

- [ ] **Task 3.2.1**: Implement `UserActivityDetector` base class
  - `is_user_active()` method
  - Activity threshold: 5 seconds (configurable)
  - Platform detection: macOS/Linux/Windows
  - **Acceptance**: Detector instantiable, platform detection works

- [ ] **Task 3.2.2**: macOS activity detection
  - AppleScript: `osascript -e "tell app System Events ..."`
  - Active window detection
  - **Acceptance**: Can detect active macOS window

- [ ] **Task 3.2.3**: Linux activity detection
  - X11 or AT-SPI (try AT-SPI first)
  - `xdotool getactivewindow` fallback
  - **Acceptance**: Can detect active Linux window

- [ ] **Task 3.2.4**: Windows activity detection
  - ctypes: `GetForegroundWindow()`, `GetWindowText()`
  - **Acceptance**: Can detect active Windows window

### 3.3 Platform-Specific Desktop Providers

#### macOS Provider (3.3.1 - 3.3.4)

- [ ] **Task 3.3.1**: Implement `MacOSDesktopProvider`
  - Base class: `DesktopProvider`
  - Methods: `execute(action)`, `_click()`, `_type_text()`, `_send_hotkey()`
  - **Acceptance**: Provider instantiable
  - **LOC**: ~150

- [ ] **Task 3.3.2**: AppleScript action execution
  - `_click(x, y)`: Position click via AppleScript
  - `_type_text(text)`: Keyboard input
  - `_send_hotkey(keys, modifiers)`: Modifier + key combination
  - **Acceptance**: All three action types execute without error

- [ ] **Task 3.3.3**: AppleScript subprocess management
  - `_run_applescript(script)` helper
  - Error handling: AppleScript failures, timeouts
  - **Acceptance**: Script execution reliable, errors caught

- [ ] **Task 3.3.4**: macOS provider tests
  - `test_macos_click_action`
  - `test_macos_type_action`
  - `test_macos_hotkey_action`
  - Requires manual testing on macOS (can skip in CI initially)
  - **Acceptance**: 3/3 tests pass on macOS

#### Linux Provider (3.3.5 - 3.3.8)

- [ ] **Task 3.3.5**: Implement `LinuxDesktopProvider`
  - Base class: `DesktopProvider`
  - Methods: `execute(action)`, `_click()`, `_type_text()`, `_send_hotkey()`
  - **Acceptance**: Provider instantiable
  - **LOC**: ~150

- [ ] **Task 3.3.6**: AT-SPI action execution
  - Try AT-SPI DBus (preferred)
  - Fallback to `xdotool` for simple actions
  - **Acceptance**: AT-SPI queries work, xdotool fallback available

- [ ] **Task 3.3.7**: xdotool integration
  - `xdotool click`, `type`, `key` for basic actions
  - Error handling: xdotool not installed
  - **Acceptance**: xdotool commands execute correctly

- [ ] **Task 3.3.8**: Linux provider tests
  - `test_linux_click_action`
  - `test_linux_type_action`
  - `test_linux_hotkey_action`
  - Requires manual testing on Linux (can skip in CI initially)
  - **Acceptance**: 3/3 tests pass on Linux

#### Windows Provider (3.3.9 - 3.3.12)

- [ ] **Task 3.3.9**: Implement `WindowsDesktopProvider`
  - Base class: `DesktopProvider`
  - Methods: `execute(action)`, `_click()`, `_type_text()`, `_send_hotkey()`
  - **Acceptance**: Provider instantiable
  - **LOC**: ~150

- [ ] **Task 3.3.10**: Windows UI Automation (pywinauto)
  - `pywinauto` library for element finding & interaction
  - Click by position or element selector
  - **Acceptance**: Can create pywinauto app/element objects

- [ ] **Task 3.3.11**: Windows keyboard input
  - `pywinauto.keyboard` for type & hotkey
  - Alt/Ctrl/Shift modifiers
  - **Acceptance**: Keyboard input works

- [ ] **Task 3.3.12**: Windows provider tests
  - `test_windows_click_action`
  - `test_windows_type_action`
  - `test_windows_hotkey_action`
  - Requires manual testing on Windows
  - **Acceptance**: 3/3 tests pass on Windows

### 3.4 Desktop Coordinator Integration

- [ ] **Task 3.4.1**: Wire coordinator into executor
  - `async with self.desktop_coordinator.schedule_action(tenant_id, action_type, target):`
  - Ensure user activity detection pauses actions
  - **Acceptance**: Executor uses coordinator without deadlocks

- [ ] **Task 3.4.2**: Action queue scheduling
  - Priority queue ordering (higher priority first)
  - Per-tenant FIFO for same priority
  - Action delay between agent actions (100ms configurable)
  - **Acceptance**: Actions scheduled in correct order, delays applied

### 3.5 Coordinator Unit Tests

- [ ] **Task 3.5.1**: Coordinator core tests
  - `test_schedule_action_queues`
  - `test_execute_action_success`
  - `test_execute_action_retry_exponential_backoff`
  - `test_metrics_recorded`
  - **Acceptance**: 4/4 tests pass

- [ ] **Task 3.5.2**: Concurrency tests
  - `test_concurrent_actions_different_tenants`
  - `test_concurrent_actions_same_tenant_ordered`
  - **Acceptance**: 2/2 tests pass

- [ ] **Task 3.5.3**: User activity tests
  - `test_user_activity_detected_pauses_action`
  - `test_action_resumes_after_user_inactive`
  - **Acceptance**: 2/2 tests pass

### Phase 3 Completion

- [ ] All platform providers implemented (macOS, Linux, Windows)
- [ ] All tests pass (15+ desktop-related tests)
- [ ] No regressions in existing executor tests
- [ ] Documentation: `design.md` sections 5-6 complete

---

## Phase 4: OS User Isolation (Week 6)

### 4.1 OS User Provider Implementation

- [ ] **Task 4.1.1**: Implement `OSUserIsolationProvider`
  - Base class: `IsolationProvider`
  - Methods: `allocate_tenant()`, `execute_in_context()`, `cleanup_tenant()`
  - **Acceptance**: Provider instantiable
  - **LOC**: ~300

- [ ] **Task 4.1.2**: OS user creation logic
  - `create_os_user(username, uid)` method
  - Platform-specific: `useradd` (Linux), `dscl` (macOS), `net user` (Windows)
  - Home directory setup
  - **Acceptance**: Users created correctly with proper directories

- [ ] **Task 4.1.3**: Sudoers configuration
  - Generate sudoers entries: `thegent-agent-N ALL=(ALL) NOPASSWD:/usr/bin/thegent`
  - Use `visudo` validation or direct file write (careful!)
  - macOS: Use `doas` instead of sudo (or configure sudo)
  - **Acceptance**: Sudoers entries correct, no syntax errors

- [ ] **Task 4.1.4**: Execution in OS user context
  - `sudo -u thegent-agent-N /usr/bin/thegent <command>`
  - Error handling: user doesn't exist, permission denied
  - **Acceptance**: Command executes as OS user

### 4.2 Helper CLI Command

- [ ] **Task 4.2.1**: Implement `thegent isolation setup-os-user` command
  - Arguments: `--num-users N`, `--base-user PREFIX`, `--group GROUP`
  - Creates N OS users with sequential numbering
  - Generates sudoers config
  - **Acceptance**: Command creates N users, sudoers configured

- [ ] **Task 4.2.2**: Implement `thegent isolation cleanup-os-user` command
  - Remove created OS users and sudoers entries
  - Safe deletion (confirm prompt)
  - **Acceptance**: Users deleted, sudoers entries removed

### 4.3 Unit Tests (OS User)

- [ ] **Task 4.3.1**: User creation tests (may be platform-specific)
  - `test_create_os_user` (platform detection)
  - `test_user_home_directory_created`
  - `test_execute_as_os_user` (requires actual user)
  - **Note**: These tests may be skipped on non-target platforms
  - **Acceptance**: 2-3 tests pass (or skipped gracefully)

- [ ] **Task 4.3.2**: Sudoers generation tests
  - `test_sudoers_entry_format` (syntax validation)
  - `test_visudo_validation` (if using visudo)
  - **Acceptance**: 2/2 tests pass

### 4.4 Integration Tests

- [ ] **Task 4.4.1**: End-to-end OS user isolation
  - Create OS user, execute command, verify isolation
  - Multiple users, verify separation
  - Cleanup users
  - **Note**: Requires admin, may be manual test
  - **Acceptance**: Manual test passes

### Phase 4 Completion

- [ ] OS user isolation fully functional
- [ ] Helper CLI commands work
- [ ] Tests pass (where possible; some platform-specific)
- [ ] Documentation: `design.md` section 3 complete

---

## Phase 5: Integration & Hardening (Weeks 7-8)

### 5.1 Audit Logging

- [ ] **Task 5.1.1**: Implement `IsolationAuditor`
  - Log events: `isolation_create`, `lease_acquire`, `action_execute`
  - JSONL format: `/var/log/thegent/tenant-{id}.jsonl`
  - Fields: timestamp, event_type, tenant_id, agent_id, resource, operation, result
  - **Acceptance**: Auditor logs events, JSONL readable
  - **LOC**: ~100

- [ ] **Task 5.1.2**: Integration into executor
  - Wire auditor into all isolation/coordination operations
  - Log successful and failed operations
  - **Acceptance**: Audit log populated with events

### 5.2 Concurrency Controller

- [ ] **Task 5.2.1**: Implement per-tenant concurrency limits
  - Config: `coordination.concurrency.per_tenant_max: 3`
  - Semaphore per tenant
  - User actions bypass limit (always allowed)
  - **Acceptance**: Concurrency limits enforced

- [ ] **Task 5.2.2**: Escalation queue for backpressure
  - Queue actions when limit exceeded
  - Log escalations
  - **Acceptance**: Queue works, no silent failures

### 5.3 Performance Benchmarking

- [ ] **Task 5.3.1**: Latency benchmarks
  - Sub-user allocation: measure <1ms
  - Lease acquire: measure <50ms
  - Desktop action: measure <200ms
  - User activity check: measure <50ms
  - **Acceptance**: Actual measurements match targets (within 10%)

- [ ] **Task 5.3.2**: Success rate measurement
  - Run 1000+ operations, measure success rate
  - Target: >95% for all operations
  - **Acceptance**: Success rates meet targets

### 5.4 Security Tests

- [ ] **Task 5.4.1**: Cross-tenant file access prevention
  - Attempt to read file locked by other tenant
  - Expect `LeaseConflictError`
  - **Acceptance**: Test passes (cross-tenant access blocked)

- [ ] **Task 5.4.2**: Capability matrix validation
  - Define per-tenant capabilities: `["exec", "file_read", "file_write"]`
  - Attempt operation outside capabilities
  - Expect error (capability denied)
  - **Acceptance**: Capability matrix enforced

- [ ] **Task 5.4.3**: Audit log verification
  - Verify all sensitive operations logged
  - No blind spots in audit trail
  - **Acceptance**: Audit log complete

### 5.5 Documentation & Examples

- [ ] **Task 5.5.1**: Deployment guide
  - Sub-user mode setup (no special steps)
  - OS user mode setup (sudoers, user creation)
  - Docker mode (future)
  - **Acceptance**: Guide clear, no ambiguities

- [ ] **Task 5.5.2**: Troubleshooting guide
  - Common errors: "lease conflict", "desktop action timeout", "user creation failed"
  - Solutions for each
  - **Acceptance**: Guide covers main issues

- [ ] **Task 5.5.3**: Configuration reference
  - All config options documented
  - Examples for dev/prod/enterprise
  - **Acceptance**: Reference complete

- [ ] **Task 5.5.4**: Example: Multi-tenant agent execution
  - Code snippet: spawn 3 agents, each in own tenant context
  - Show audit log output
  - **Acceptance**: Example runs without error

### 5.6 Regression Testing

- [ ] **Task 5.6.1**: Existing test suite
  - Run full thegent test suite
  - No regressions from isolation changes
  - **Acceptance**: All existing tests pass

- [ ] **Task 5.6.2**: Backward compatibility
  - Existing agents without isolation changes work
  - No forced adoption of new APIs
  - **Acceptance**: Legacy code unaffected

### 5.7 Code Quality

- [ ] **Task 5.7.1**: Lint & type checking
  - `ruff check` passes (all files)
  - `mypy` passes (Python type checker)
  - **Acceptance**: Zero lint/type errors

- [ ] **Task 5.7.2**: Code review readiness
  - Comments & docstrings complete
  - Architecture decisions documented
  - **Acceptance**: Code ready for peer review

### Phase 5 Completion

- [ ] All integration complete
- [ ] All tests pass (50+ total tests across all phases)
- [ ] Benchmarks meet SLAs
- [ ] Security tests pass
- [ ] Documentation complete
- [ ] No regressions
- [ ] Ready for release

---

## Summary: Task Checklist

| Phase                            | Tasks              | Status | Est. Week     |
| -------------------------------- | ------------------ | ------ | ------------- |
| Phase 1: Sub-User Isolation      | 1.1-1.5 (5 tasks)  | TBD    | 1-2           |
| Phase 2: Edit Lease Manager      | 2.1-2.4 (4 tasks)  | TBD    | 3             |
| Phase 3: Desktop Coordinator     | 3.1-3.5 (12 tasks) | TBD    | 4-5           |
| Phase 4: OS User Isolation       | 4.1-4.4 (4 tasks)  | TBD    | 6             |
| Phase 5: Integration & Hardening | 5.1-5.7 (7 tasks)  | TBD    | 7-8           |
| **TOTAL**                        | **32+ tasks**      |        | **5-6 weeks** |

---

## Success Criteria (Phase 5 Exit)

### Functional

- [ ] Sub-user isolation working (default mode)
- [ ] OS user isolation working (opt-in mode)
- [ ] Edit leases prevent multi-tenant conflicts
- [ ] Desktop automation coordinator prevents UI collisions
- [ ] User activity detection pauses agent actions
- [ ] Per-tenant concurrency limits enforced

### Non-Functional

- [ ] Latency budgets met (p95 targets)
- [ ] Success rates >95% for all operations
- [ ] No regressions in existing tests
- [ ] Backward compatible (existing agents work)

### Security & Compliance

- [ ] Cross-tenant file access blocked
- [ ] Capability matrix enforced
- [ ] Audit log complete & tamper-evident
- [ ] Security tests pass

### Documentation

- [ ] Proposal, design, tasks documents complete
- [ ] Deployment guide written
- [ ] Troubleshooting guide written
- [ ] Code examples provided
- [ ] Inline comments & docstrings present

---

## Acceptance Criteria (Per Task)

Each task has **explicit acceptance criteria** above. Example:

```
Task 1.2.1: Implement SubUserIsolationProvider
  Acceptance:
    - Provider instantiable
    - UID/GID allocated per tenant (hash-based)
    - Environment variables set in subprocess
    - Tests: test_allocate_tenant, test_execute_in_context (4+ unit tests)
    - Code: ~250 LOC, no external dependencies
    - Status: Ready for Phase 1 completion review
```

---

## References

- **Proposal**: `proposal.md`
- **Design**: `design.md`
- **Research**: `docs/research/CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md`
- **Work Stream**: `docs/reference/WORK_STREAM.md` (item: `research-cross-platform-isolation`)
