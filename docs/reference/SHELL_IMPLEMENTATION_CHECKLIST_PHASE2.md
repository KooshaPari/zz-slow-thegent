# Shell Implementation Checklist — Phase 2

**Document:** Cross-Platform Shell Strategy Implementation
**Phase:** Phase 2 (Weeks 1-10)
**Last Updated:** 2026-02-19
**Status:** Planning

---

## Phase 2A: Foundation (Weeks 1-2)

### Rust Dispatcher Binary

- [ ] **Design & Architecture ADR**
  - [ ] Document dispatcher responsibility matrix
  - [ ] Define shell detection algorithm
  - [ ] Specify error handling strategy
  - [ ] Review with team
  - **Target:** Day 1

- [ ] **Project Setup**
  - [ ] Create `hooks/hook-dispatcher/` directory
  - [ ] Initialize `Cargo.toml` with dependencies (clap, tempfile, anyhow)
  - [ ] Set up CI for Rust compilation
  - [ ] Add to .gitignore: `target/`, `*.rmeta`
  - **Target:** Day 1

- [ ] **Shell Detection Module**
  - [ ] Implement `src/shell_detector.rs`:
    - [ ] Enum: `Shell { POSIX, PowerShell }`
    - [ ] Fn: `detect_shell() -> Result<Shell>`
    - [ ] Check `THGENT_SHELL` env var
    - [ ] Detect platform (Platform enum)
    - [ ] Try shell executables in order
    - [ ] Unit tests for all platforms
  - [ ] Test on: macOS, Linux (Ubuntu/Alpine), Windows, WSL2
  - **Target:** Day 2

- [ ] **Dispatcher Core**
  - [ ] Implement `src/main.rs`:
    - [ ] Parse CLI args: hook_name, hook_event, context
    - [ ] Call shell detector
    - [ ] Resolve hook file (.sh or .ps1)
    - [ ] Create appropriate runner
    - [ ] Handle timeout (default 30s)
    - [ ] Capture and log stderr
    - [ ] Return exit code
  - [ ] Implement `src/dispatcher.rs`:
    - [ ] `struct PosixRunner`: bash command building
    - [ ] `struct PowerShellRunner`: pwsh command building
    - [ ] Common error handling
  - [ ] Integration tests
  - **Target:** Day 3

- [ ] **Build & Install**
  - [ ] `cargo build --release` works
  - [ ] Binary at `hooks/hook-dispatcher`
  - [ ] Size < 5MB (stripping)
  - [ ] Can be installed to `~/.local/bin`
  - [ ] Update Taskfile: `task build:dispatcher`
  - **Target:** Day 3

**Acceptance Criteria:**

- [ ] Dispatcher detects shell correctly on all platforms
- [ ] Dispatcher resolves hook files (.sh/.ps1)
- [ ] Dispatcher executes hooks with correct environment
- [ ] Error messages are clear and actionable
- [ ] Performance: dispatch overhead < 50ms

---

### POSIX Library (bash_lib.sh)

- [ ] **Module Design**
  - [ ] Document public API (function list)
  - [ ] Document behavior for each function
  - [ ] Specify error semantics
  - **Target:** Day 1

- [ ] **Core Functions**
  - [ ] `log_info()`, `log_warn()`, `log_error()`
    - [ ] Structured output with timestamp
    - [ ] Write to stderr
    - [ ] Test on multiple shells (bash, zsh, sh)
  - [ ] `die()` — log error and exit with code
  - [ ] `get_env()` — safe environment lookup
  - [ ] `normalize_path()` — absolute path resolution
  - [ ] `file_exists()`, `is_dir()`
  - [ ] **Target:** Day 2

- [ ] **Validation Functions**
  - [ ] `validate_changes()` — call Python validator
  - [ ] `check_lint()` — invoke linter
  - [ ] `run_tests()` — invoke test runner
  - [ ] Return proper exit codes
  - [ ] Test with sample files
  - [ ] **Target:** Day 2

- [ ] **File Operations**
  - [ ] `file_changed_since()` — timestamp comparison
  - [ ] `copy_file()`, `remove_file()`
  - [ ] `read_file_line()` — line reader
  - [ ] Error handling for missing files
  - [ ] **Target:** Day 2

- [ ] **Process Management**
  - [ ] `run_with_timeout()` — timeout wrapper
  - [ ] `get_process_pids()` — find processes
  - [ ] `wait_for_process()` — blocking wait
  - [ ] **Target:** Day 3

- [ ] **Documentation**
  - [ ] Inline comments for all functions
  - [ ] Example usage for each function
  - [ ] Edge cases documented
  - [ ] **Target:** Day 3

- [ ] **Testing**
  - [ ] Create `tests/shell/bash_lib_test.sh`
  - [ ] Test each function individually
  - [ ] Test on: macOS bash/zsh, Linux bash/zsh, Alpine sh
  - [ ] Test error cases
  - [ ] **Target:** Day 3

**Acceptance Criteria:**

- [ ] bash_lib.sh is 200-300 LOC
- [ ] All public functions documented
- [ ] All functions tested on multiple shells
- [ ] No unquoted variables (shellcheck passes)
- [ ] Works on: bash 3.x+, zsh, sh

---

### PowerShell Library (pwsh_lib.ps1)

- [ ] **Module Design**
  - [ ] Decide: single .ps1 file vs. module structure
  - [ ] Design function naming conventions
  - [ ] Specify parameter style (camelCase vs. PascalCase)
  - [ ] **Target:** Day 1

- [ ] **Module Structure** (if module)
  - [ ] Create `hooks/lib/pwsh_lib/pwsh_lib.psd1` (manifest)
  - [ ] Create `hooks/lib/pwsh_lib/pwsh_lib.psm1` (main module)
  - [ ] Create `hooks/lib/pwsh_lib/public/` directory
  - [ ] Create `hooks/lib/pwsh_lib/private/` directory
  - [ ] **Target:** Day 2

- [ ] **Core Functions**
  - [ ] `Write-Log` — structured logging (equiv. to log_info)
    - [ ] Parameters: -Level, -Message
    - [ ] Output to Write-Verbose or Write-Host
    - [ ] Color-coded output
  - [ ] `Stop-WithError` — error and exit (equiv. to die)
  - [ ] `Get-ConfigValue` — read config
  - [ ] `Normalize-Path` — absolute path resolution
  - [ ] **Target:** Day 2

- [ ] **Validation Functions**
  - [ ] `Invoke-ValidateChanges` — call Python validator
  - [ ] `Invoke-CheckLint` — invoke linter
  - [ ] `Invoke-RunTests` — invoke test runner
  - [ ] Proper error handling
  - [ ] **Target:** Day 2

- [ ] **File Operations**
  - [ ] `Test-FileChangedSince` — timestamp comparison
  - [ ] `Copy-FileItem`, `Remove-FileItem`
  - [ ] `Get-FileContent` — read file
  - [ ] Error handling
  - [ ] **Target:** Day 2

- [ ] **Process Management**
  - [ ] `Invoke-WithTimeout` — timeout wrapper
  - [ ] `Get-ProcessChildren` — find subprocess
  - [ ] `Wait-ForProcess` — blocking wait
  - [ ] **Target:** Day 3

- [ ] **Documentation**
  - [ ] `help` for all functions (PowerShell help spec)
  - [ ] Example usage (Get-Help)
  - [ ] Parameter help text
  - [ ] **Target:** Day 3

- [ ] **Testing**
  - [ ] Create `tests/shell/pwsh_lib_test.ps1`
  - [ ] Test each function individually
  - [ ] Test on: Windows PowerShell 5.1, pwsh 7+
  - [ ] Test error cases
  - [ ] **Target:** Day 3

**Acceptance Criteria:**

- [ ] pwsh_lib.ps1 is 200-300 LOC
- [ ] All functions have PowerShell help
- [ ] All functions tested on pwsh 7+
- [ ] Passes PSScriptAnalyzer (strict rules)
- [ ] Works on: PowerShell 5.1+, pwsh 7+

---

### Python Shell Interface Module

- [ ] **Module Structure**
  - [ ] Create `src/thegent/shell/__init__.py`
  - [ ] Create `src/thegent/shell/detection.py`
  - [ ] Create `src/thegent/shell/environment.py`
  - [ ] Create `src/thegent/shell/executor.py`
  - [ ] Create `src/thegent/shell/adapters/` directory
  - [ ] **Target:** Day 2

- [ ] **ShellType Enum**
  - [ ] `ShellType.BASH`, `.ZSH`, `.SH`, `.POWERSHELL`
  - [ ] Properties: name, path, is_posix, is_windows
  - [ ] **Target:** Day 1

- [ ] **Detection Module**
  - [ ] `detect_shell(platform: Platform) -> ShellType`
  - [ ] Check env vars: `THGENT_AGENT_SHELL`, `THGENT_SHELL`
  - [ ] Check config file
  - [ ] Platform-specific logic
  - [ ] Fallback strategy
  - [ ] Unit tests: all platforms
  - [ ] **Target:** Day 2

- [ ] **ShellEnvironment Class**
  - [ ] `__init__(platform=None, prefer_shell=None)`
  - [ ] Properties: shell_type, shell_path, environment
  - [ ] `run_command(cmd, cwd=None, timeout=None, check=True) -> CompletedProcess`
  - [ ] `get_env_var(name: str) -> str | None`
  - [ ] `update_env(key, value)`
  - [ ] Caching: detect shell once per session
  - [ ] **Target:** Day 3

- [ ] **ShellExecutor Class**
  - [ ] `__init__(env: ShellEnvironment | None = None)`
  - [ ] `run_hook(hook_name, *args) -> CompletedProcess`
  - [ ] `run_script(script_path, *args) -> CompletedProcess`
  - [ ] Error handling and logging
  - [ ] **Target:** Day 3

- [ ] **Testing**
  - [ ] `tests/shell/test_shell_detection.py` — parametrized tests
  - [ ] `tests/shell/test_shell_environment.py` — env class
  - [ ] `tests/shell/test_shell_executor.py` — executor
  - [ ] Fixtures: mock platforms, shells, configs
  - [ ] **Target:** Day 3

**Acceptance Criteria:**

- [ ] Shell detection works on all platforms
- [ ] ShellEnvironment properly caches shell detection
- [ ] run_command() executes in correct shell
- [ ] Error messages are clear
- [ ] No performance regression (< 5% slowdown)

---

## Phase 2B: Hook Migration (Weeks 3-4)

### Hook 1: qa-check

- [ ] **Analysis**
  - [ ] [ ] Review current `hooks/qa-check.sh`
  - [ ] [ ] Identify POSIX-specific patterns
  - [ ] [ ] Document PowerShell equivalents
  - [ ] **Target:** Week 3, Day 1

- [ ] **POSIX Version (update)**
  - [ ] [ ] Refactor to use bash_lib.sh
  - [ ] [ ] Replace inline functions with library calls
  - [ ] [ ] Update error handling
  - [ ] [ ] Test on macOS/Linux
  - [ ] **Target:** Week 3, Day 2

- [ ] **PowerShell Version (create)**
  - [ ] [ ] Create `hooks/qa-check.ps1`
  - [ ] [ ] Use pwsh_lib functions
  - [ ] [ ] Replicate exact behavior
  - [ ] [ ] Test on Windows
  - [ ] **Target:** Week 3, Day 3

- [ ] **Integration Testing**
  - [ ] [ ] Test both versions via dispatcher
  - [ ] [ ] Test with sample projects
  - [ ] [ ] Verify exit codes match
  - [ ] **Target:** Week 3, Day 4

- [ ] **Documentation**
  - [ ] [ ] Document changes in hook header
  - [ ] [ ] Update HOOK_DEVELOPMENT guide
  - [ ] **Target:** Week 3, Day 4

**Acceptance Criteria:**

- [ ] Both .sh and .ps1 versions exist
- [ ] Behavior is identical
- [ ] All tests pass on both platforms
- [ ] Dispatcher correctly routes to each

---

### Hook 2: doc-location-guard

- [ ] Analysis & planning
- [ ] POSIX version refactor
- [ ] PowerShell version creation
- [ ] Testing & integration
- [ ] Documentation

**Target:** Week 3, completed by Day 4

---

### Hook 3: change-doc-tracker

- [ ] Analysis & planning
- [ ] POSIX version refactor
- [ ] PowerShell version creation
- [ ] Testing & integration
- [ ] Documentation

**Target:** Week 4, completed by Day 2

---

### Hook 4: complexity-ratchet

- [ ] Analysis & planning
- [ ] POSIX version refactor
- [ ] PowerShell version creation
- [ ] Testing & integration
- [ ] Documentation

**Target:** Week 4, completed by Day 4

---

### Hook 5: security-pipeline

- [ ] Analysis & planning
- [ ] POSIX version refactor
- [ ] PowerShell version creation
- [ ] Testing & integration
- [ ] Documentation

**Target:** Week 4, completed by Day 4

---

### Cross-Hook Testing

- [ ] [ ] All hooks route correctly via dispatcher
- [ ] [ ] All hooks execute successfully on POSIX
- [ ] [ ] All hooks execute successfully on Windows
- [ ] [ ] Error handling consistent
- [ ] [ ] Performance acceptable (< 200ms per hook)

**Target:** End of Week 4

---

## Phase 2C: Python Interface Integration (Weeks 5-6)

### Migrate fast_subprocess

- [ ] [ ] Update `src/thegent/infra/fast_subprocess.py`
  - [ ] [ ] Import ShellEnvironment
  - [ ] [ ] Use detected shell for command execution
  - [ ] [ ] Pass shell environment to subprocess
  - [ ] [ ] Maintain backward compatibility
- [ ] [ ] Update async execution
- [ ] [ ] Test all platforms
- [ ] [ ] Verify performance (< 5% regression)

**Target:** Week 5, Day 2

---

### Migrate Agent Subprocess Execution

- [ ] [ ] Find all agent subprocess calls
- [ ] [ ] Identify patterns (direct subprocess.run, FastSubprocess)
- [ ] [ ] Update to use ShellEnvironment
- [ ] [ ] Maintain agent isolation
- [ ] [ ] Test agent execution on all platforms

**Target:** Week 5, Day 4

---

### Update Configuration

- [ ] [ ] Add to `src/thegent/config.py`:
  ```yaml
  shell:
    agent_shell: "auto"
    hook_shell: "auto"
    prefer_posix: false
    fallback_shell: "sh"
  ```
- [ ] [ ] CLI flags: `--shell bash`, `--shell pwsh`
- [ ] [ ] Validation: check shell availability
- [ ] [ ] Tests for all config combinations

**Target:** Week 5, Day 2

---

### CLI Updates

- [ ] [ ] `thegent config get shell.agent_shell`
- [ ] [ ] `thegent config set shell.agent_shell bash`
- [ ] [ ] `thegent doctor` report detected shell
- [ ] [ ] `thegent shell-info` show shell details
- [ ] [ ] Tests for all commands

**Target:** Week 6, Day 1

---

### Installer Updates

- [ ] [ ] Update `scripts/install.sh`:
  - [ ] [ ] Detect shell preference
  - [ ] [ ] Set in config
  - [ ] [ ] Build dispatcher if cargo available
- [ ] [ ] Update `scripts/install.ps1`:
  - [ ] [ ] Detect shell preference
  - [ ] [ ] Set in config
  - [ ] [ ] Build dispatcher if cargo available
- [ ] [ ] Test both installers end-to-end

**Target:** Week 6, Day 2

---

### Integration Testing

- [ ] [ ] Test full workflow: install → config → run
- [ ] [ ] Test shell override: env var, config, CLI
- [ ] [ ] Test fallback: unavailable shell → next choice
- [ ] [ ] Test agent execution with various shells
- [ ] [ ] Performance benchmark

**Target:** Week 6, Day 4

---

## Phase 2D: OS-Level Operations (Weeks 7-8)

### Adapter 1: OS User Creation

- [ ] **Design**
  - [ ] Document API: `create_os_user(username, groups=[], shell=None)`
  - [ ] Specify error handling
  - [ ] **Target:** Week 7, Day 1

- [ ] **POSIX Implementation**
  - [ ] Create `src/thegent/shell/adapters/user_creation_posix.py`
  - [ ] Detect: Linux (useradd), macOS (dscl)
  - [ ] Handle permissions (sudo needed?)
  - [ ] Tests
  - [ ] **Target:** Week 7, Day 2

- [ ] **PowerShell Implementation**
  - [ ] Create `src/thegent/shell/adapters/user_creation_windows.ps1`
  - [ ] Use: `New-LocalUser`, `Add-LocalGroupMember`
  - [ ] Handle permissions (admin required?)
  - [ ] Tests
  - [ ] **Target:** Week 7, Day 3

- [ ] **Unified Interface**
  - [ ] Python wrapper: `create_os_user()`
  - [ ] Auto-detect platform and invoke right adapter
  - [ ] Error handling and logging
  - [ ] **Target:** Week 7, Day 4

**Acceptance Criteria:**

- [ ] User creation works on Linux, macOS, Windows
- [ ] Proper error messages for permission issues
- [ ] Idempotent (can call multiple times safely)

---

### Adapter 2: Desktop Automation

- [ ] **Design**
  - [ ] Document API: `notify_desktop(title, message, timeout=5)`
  - [ ] Specify notifications, dialogs, focus management
  - [ ] **Target:** Week 7, Day 1

- [ ] **macOS Implementation**
  - [ ] AppleScript via osascript
  - [ ] Notifications, dialogs, focus
  - [ ] Tests
  - [ ] **Target:** Week 7, Day 3

- [ ] **Windows Implementation**
  - [ ] PowerShell Toast notifications
  - [ ] Windows Forms dialogs
  - [ ] Window focus with SetForegroundWindow
  - [ ] Tests
  - [ ] **Target:** Week 8, Day 1

- [ ] **Linux Implementation (optional)**
  - [ ] D-Bus notifications (GNOME/KDE)
  - [ ] Fallback to terminal
  - [ ] Tests
  - [ ] **Target:** Week 8, Day 2

- [ ] **Unified Interface**
  - [ ] Python wrapper: `notify_desktop()`
  - [ ] Platform-aware implementation selection
  - [ ] Graceful degradation if not available
  - [ ] **Target:** Week 8, Day 2

---

### Adapter 3: Process Monitoring

- [ ] **Design**
  - [ ] Document API: `get_process_info(pid)`, `find_processes(name)`
  - [ ] Return: PID, parent PID, memory, CPU, status
  - [ ] **Target:** Week 8, Day 1

- [ ] **POSIX Implementation** (see existing code)
  - [ ] Use /proc on Linux, ps on macOS
  - [ ] `get_process_info()`, `find_processes()`
  - [ ] **Target:** Week 8, Day 2

- [ ] **PowerShell Implementation**
  - [ ] Use `Get-Process` cmdlet
  - [ ] `Get-ProcessInfo()`, `Find-Processes()`
  - [ ] Convert .NET objects to dict/JSON
  - [ ] **Target:** Week 8, Day 3

- [ ] **Unified Interface**
  - [ ] Python wrapper: `get_process_info()`, `find_processes()`
  - [ ] Platform-aware selection
  - [ ] Consistent return types
  - [ ] **Target:** Week 8, Day 4

---

### Adapter 4: File Watcher (optional)

- [ ] **Design** (if time permits)
  - [ ] Document API: `watch_files(paths, callback, pattern=None)`
  - [ ] Specify callback signature: `callback(event_type, path)`
  - [ ] **Target:** Week 8, Day 2

- [ ] **POSIX**: inotify or watchdog library
- [ ] **Windows**: FileSystemWatcher
- [ ] **Unified interface**

---

## Phase 2E: Documentation & Rollout (Weeks 9-10)

### Documentation

- [ ] **SHELL_STRATEGY.md**
  - [ ] Overview of dual-shell architecture
  - [ ] Shell selection logic
  - [ ] Configuration guide
  - [ ] Troubleshooting
  - [ ] **Target:** Week 9, Day 1

- [ ] **HOOK_DEVELOPMENT.md**
  - [ ] How to write cross-platform hooks
  - [ ] POSIX patterns
  - [ ] PowerShell patterns
  - [ ] Library function reference
  - [ ] Examples
  - [ ] **Target:** Week 9, Day 2

- [ ] **POSIX_PWSH_COMPARISON.md**
  - [ ] Detailed feature comparison
  - [ ] Path handling, env vars, quoting
  - [ ] Error handling differences
  - [ ] Performance characteristics
  - [ ] **Target:** Week 9, Day 3

- [ ] **CROSS_PLATFORM_TROUBLESHOOTING.md**
  - [ ] Common issues by platform
  - [ ] Shell not found → fallback
  - [ ] Permission issues → solutions
  - [ ] Path issues → normalization
  - [ ] WSL2 interop → wslpath
  - [ ] **Target:** Week 9, Day 4

- [ ] **README.md Updates**
  - [ ] Add Windows support section
  - [ ] Link to shell strategy docs
  - [ ] Quick start for each platform
  - [ ] **Target:** Week 9, Day 4

- [ ] **API Documentation**
  - [ ] ShellEnvironment API docs
  - [ ] ShellExecutor API docs
  - [ ] Adapter interfaces
  - [ ] Auto-generated (docstrings)
  - [ ] **Target:** Week 10, Day 1

---

### Testing & QA

- [ ] **Test Suite Expansion**
  - [ ] All shell tests on CI matrix:
    - [ ] macOS (bash, zsh)
    - [ ] Ubuntu (bash, sh)
    - [ ] Alpine (sh)
    - [ ] Windows (pwsh, WSL2 bash)
  - [ ] **Target:** Week 9, Day 2

- [ ] **Integration Tests**
  - [ ] Full workflow: install → config → hook execution
  - [ ] All critical hooks on all platforms
  - [ ] Agent subprocess execution
  - [ ] **Target:** Week 9, Day 3

- [ ] **Performance Testing**
  - [ ] Benchmark dispatcher (vs. direct bash)
  - [ ] Benchmark hook execution
  - [ ] Memory usage
  - [ ] Startup time
  - [ ] **Target:** Week 9, Day 4

- [ ] **Cross-Platform Testing**
  - [ ] WSL2 integration
  - [ ] Windows + bash (MinGW, Git Bash)
  - [ ] Hybrid environments
  - [ ] **Target:** Week 10, Day 1

- [ ] **User Acceptance Testing**
  - [ ] Beta users on each platform
  - [ ] Collect feedback
  - [ ] Fix regressions
  - [ ] **Target:** Week 10, Day 2

---

### Migration & Rollout

- [ ] **Feature Flag**
  - [ ] Add `THGENT_DUAL_SHELL_ENABLED` env var
  - [ ] Gradual rollout: 10% → 50% → 100%
  - [ ] Monitoring: errors, performance
  - [ ] **Target:** Week 10, Day 1

- [ ] **Rollback Plan**
  - [ ] Document how to revert
  - [ ] Keep old bash-only code paths available
  - [ ] Quick disable via env var
  - [ ] **Target:** Week 9, Day 4

- [ ] **Release Notes**
  - [ ] What's new
  - [ ] Breaking changes (none expected)
  - [ ] Configuration guide
  - [ ] Known issues
  - [ ] **Target:** Week 10, Day 2

- [ ] **Announcement**
  - [ ] Blog post / changelog
  - [ ] Highlight Windows support
  - [ ] Mention performance improvements
  - [ ] **Target:** Week 10, Day 3

---

### Final Validation

- [ ] [ ] Code review: all Phase 2 code
- [ ] [ ] Documentation review
- [ ] [ ] Security audit (if needed)
- [ ] [ ] Performance validated
- [ ] [ ] All tests green
- [ ] [ ] Production deploy readiness

**Target:** Week 10, Day 4

---

## Success Criteria

- [ ] All Phase 2A acceptance criteria met
- [ ] All Phase 2B acceptance criteria met
- [ ] All Phase 2C acceptance criteria met
- [ ] All Phase 2D acceptance criteria met (or deferrable)
- [ ] Documentation complete and reviewed
- [ ] Test coverage > 90% (shell-related code)
- [ ] Performance: < 5% regression in critical paths
- [ ] Cross-platform: works on macOS, Linux, Windows
- [ ] Backward compatible: no breaking changes

---

## Risk & Contingency

### High Risk: Windows Integration

**Risk:** PowerShell library development, deployment complexity

**Mitigation:**

- Early spike (Week 1) to validate PowerShell module approach
- Windows developer on team from Week 3
- Extended testing (Week 9-10)

**Contingency:**

- If pwsh library too complex, fall back to single .ps1 file
- Defer OS-level adapters (Phase 2D) if time pressure

### Medium Risk: Performance Regression

**Risk:** Dispatcher overhead, environment setup

**Mitigation:**

- Benchmark prototype (end of Week 1)
- Caching shell detection
- Profile hook execution

**Contingency:**

- Optimize dispatcher further (compile flags, caching)
- Fallback to direct bash for POSIX if needed

### Medium Risk: Library API Mismatch

**Risk:** bash_lib.sh and pwsh_lib.ps1 behavior divergence

**Mitigation:**

- Detailed API specs (Week 1)
- Pair programming on libraries
- Comprehensive test coverage

**Contingency:**

- API compatibility tests: run same test on both shells
- Regular code review checkpoints

---

## Team & Resources

**Recommended Team:**

- 1 Rust engineer (dispatcher, adapters)
- 1 PowerShell engineer (pwsh library, testing)
- 1 Python engineer (integration, config)
- 1 QA engineer (testing, documentation)

**Effort:** ~7 weeks @ 4 FTE = ~28 person-weeks

**Alternatives:**

- 1 fullstack engineer: 3 months
- 2 engineers (POSIX + PowerShell split): 10-12 weeks

---

**Prepared for:** Phase 2 Implementation Planning
**Next Review Date:** End of Phase 2A (Week 2)
**Escalation Path:** Blocked by unavailable shell? Escalate to tech lead for workaround.
