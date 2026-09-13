<DONE>
# Remove Directory Dependencies — Production Installation Optimization

**Date:** 2026-02-17
**Status:** Research Complete, Plan Ready
**Priority:** P1 (DX/AX/UX Optimization)

---

## Executive Summary

**Problem:** thegent currently assumes it's running from the dev repository directory. In production, users install via package managers (pip, nix, etc.) and have a "manage" devkit system. Thegent should work **without** requiring access to the repository directory.

**Current State:**

- `.envrc` uses `$(pwd)` to reference thegent directory
- `.starship.toml` is in thegent directory
- Code searches for `src/thegent` to detect project root
- Scripts assume they're in thegent directory
- Hooks/templates referenced from repo directory

**Goal:** Make thegent work seamlessly for:

1. **Dev mode** (running from repo) — current behavior
2. **Installed mode** (via pip/nix/pkg manager) — new requirement
3. **Manage devkit** — integrate with existing devkit system

---

## 1. Current Directory Dependencies Audit

### 1.1 Environment Files

| File             | Dependency              | Location         | Impact                                  |
| ---------------- | ----------------------- | ---------------- | --------------------------------------- |
| `.envrc`         | `$(pwd)/.starship.toml` | `.envrc:17`      | ⚠️ **High** — Starship config not found |
| `.envrc`         | `$(pwd)/.venv`          | `.envrc:8`       | ⚠️ **Medium** — Dev venv only           |
| `.envrc`         | `$(pwd)/src`            | `.envrc:11`      | ⚠️ **High** — PYTHONPATH for dev        |
| `.starship.toml` | Project root            | `.starship.toml` | ⚠️ **High** — Prompt config             |

### 1.2 Python Code Dependencies

| File                  | Pattern                                       | Line     | Impact                               |
| --------------------- | --------------------------------------------- | -------- | ------------------------------------ |
| `doctor.py`           | `Path.cwd() / "src" / "thegent"`              | 40       | ⚠️ **High** — Assumes repo structure |
| `doctor.py`           | `os.chdir(project_root)`                      | 51       | ⚠️ **High** — Changes CWD            |
| `mcp_manage.py`       | `Path(thegent.__file__).parent.parent.parent` | 88       | ⚠️ **High** — Assumes repo structure |
| `install.py`          | `Path(__file__).parent.parent.parent`         | 1833     | ⚠️ **High** — Assumes repo structure |
| `cliproxy_manager.py` | `Path(thegent.__file__).parent.parent.parent` | 335, 378 | ⚠️ **Medium** — Fork binary lookup   |
| `cliproxy_manager.py` | `parents[3] / "scripts"`                      | 507      | ⚠️ **Medium** — Adapter script       |
| `main.py`             | `parents[2] / "hooks"`                        | 1930     | ⚠️ **High** — Hook watcher           |
| `prompts.py`          | `parent.parent.parent`                        | 592      | ⚠️ **Medium** — Script directory     |

### 1.3 Shell Scripts

| File                           | Dependency                          | Impact                            |
| ------------------------------ | ----------------------------------- | --------------------------------- |
| `scripts/start_proxy.py`       | `Path(__file__).parents[1] / "src"` | ⚠️ **High** — Dev-only            |
| `~/.local/bin/thegent` wrapper | Finds project root                  | ⚠️ **High** — Assumes repo exists |

### 1.4 Configuration Files

| File        | Dependency     | Impact                         |
| ----------- | -------------- | ------------------------------ |
| `flake.nix` | `$(pwd)/src`   | ⚠️ **Medium** — Dev shell only |
| `flake.nix` | `$(pwd)/.venv` | ⚠️ **Medium** — Dev shell only |

---

## 2. Dev vs Installed Detection Strategy

### 2.1 Detection Methods

**Method 1: Check if `thegent.__file__` is in site-packages**

```python
import thegent
from pathlib import Path
import site

pkg_path = Path(thegent.__file__).resolve().parent
site_packages = [Path(p) for p in site.getsitepackages()]

is_installed = any(pkg_path.is_relative_to(sp) for sp in site_packages)
is_dev = not is_installed and (pkg_path.parent.parent / "pyproject.toml").exists()
```

**Method 2: Check for `pyproject.toml` in parent directories**

```python
def _is_dev_mode() -> bool:
    """Detect if running from dev repo vs installed package."""
    import thegent

    pkg_path = Path(thegent.__file__).resolve().parent
    # Check if we're in a repo (has pyproject.toml nearby)
    for parent in [pkg_path.parent, pkg_path.parent.parent, pkg_path.parent.parent.parent]:
        if (parent / "pyproject.toml").exists() and (parent / "src" / "thegent").exists():
            return True
    return False
```

**Method 3: Environment variable override**

```python
# Allow explicit override
if os.environ.get("THGENT_MODE") == "dev":
    return True
elif os.environ.get("THGENT_MODE") == "installed":
    return False
# Otherwise auto-detect
```

### 2.2 Recommended Approach

**Hybrid detection:**

1. Check `THGENT_MODE` env var (explicit override)
2. Check if `thegent.__file__` is in site-packages (installed)
3. Check for `pyproject.toml` + `src/thegent` (dev)
4. Fallback: assume installed (safer for production)

---

## 3. User Data Directory Strategy

### 3.1 XDG Base Directory Specification

**Standard locations:**

- **Config:** `~/.config/thegent/` (or `$XDG_CONFIG_HOME/thegent/`)
- **Cache:** `~/.cache/thegent/` (or `$XDG_CACHE_HOME/thegent/`)
- **Data:** `~/.local/share/thegent/` (or `$XDG_DATA_HOME/thegent/`)

**Current usage:**

- `~/.config/thegent/cliproxy-config.yaml` ✅ Already using XDG
- `~/.cache/thegent/sessions/` ✅ Already using XDG
- `~/.cache/thegent/git-shim-cache` ✅ Already using XDG

### 3.2 Project-Specific Files

**For installed thegent:**

- **Hooks:** `~/.config/thegent/hooks/` (installed via `thegent install`)
- **Templates:** `~/.config/thegent/templates/` (installed via `thegent install`)
- **Scripts:** `~/.local/share/thegent/scripts/` (installed via `thegent install`)
- **Starship config:** `~/.config/thegent/.starship.toml` (global) or per-project

**For dev mode:**

- Use repo directories as fallback
- Allow override via `THGENT_HOOKS_DIR`, `THGENT_TEMPLATES_DIR`, etc.

---

## 4. "Manage" Devkit System Research

### 4.1 What is "Manage"?

**Hypothesis:** "manage" is likely:

- A devkit/system management tool
- Possibly related to Factory system (`.factory/` directories)
- May provide hooks, templates, or configuration management
- Could be a wrapper/system for managing dev environments

**Research needed:**

- Search codebase for "manage" references
- Check if there's a `manage` command or tool
- Understand how it integrates with thegent

### 4.2 Integration Points

**Potential integration:**

1. **Hooks:** `manage` may provide hooks that thegent should use
2. **Templates:** `manage` may provide templates
3. **Configuration:** `manage` may manage `.envrc`, `.starship.toml`, etc.
4. **Service management:** `manage` may manage services (MCP, proxy)

---

## 5. Migration Plan

### 5.1 Phase 1: Dev/Installed Detection (Low Risk)

**Goal:** Add detection logic without breaking existing behavior.

**Tasks:**

1. Create `src/thegent/utils.py` with `_is_dev_mode()` function
2. Add `THGENT_MODE` env var support
3. Update `_get_project_root()` functions to use detection
4. Test in both dev and installed modes

**Files:**

- `src/thegent/utils.py` — New utility module
- `src/thegent/mcp_manage.py` — Update `_get_project_root()`
- `src/thegent/doctor.py` — Update project root detection
- `src/thegent/install.py` — Update root detection

**Timeline:** 2-3 hours

**Risk:** Low (backward compatible, dev mode still works)

### 5.2 Phase 2: User Data Directories (Medium Risk)

**Goal:** Move project-specific files to user directories.

**Tasks:**

1. Create `~/.config/thegent/hooks/` directory structure
2. Install hooks to user directory via `thegent install`
3. Update hook resolution to check user dir first, then repo
4. Move `.starship.toml` to `~/.config/thegent/.starship.toml`
5. Update `.envrc` to use user directory

**Files:**

- `src/thegent/install.py` — Install hooks/templates to user dir
- `hooks/hook-dispatcher/src/main.rs` — Update `resolve_hooks_dir()`
- `.envrc` — Use user directory for starship config
- `src/thegent/config.py` — Add hooks_dir, templates_dir settings

**Timeline:** 4-6 hours

**Risk:** Medium (affects hook resolution, needs testing)

### 5.3 Phase 3: Remove CWD Dependencies (Medium Risk)

**Goal:** Remove all `Path.cwd()` and `$(pwd)` dependencies.

**Tasks:**

1. Update `doctor.py` to not change CWD
2. Update `.envrc` to not use `$(pwd)`
3. Update scripts to use user directories or package paths
4. Remove project root detection from non-dev commands

**Files:**

- `src/thegent/doctor.py` — Remove CWD changes
- `.envrc` — Use user directories
- `scripts/start_proxy.py` — Use package paths
- `flake.nix` — Use user directories

**Timeline:** 3-4 hours

**Risk:** Medium (affects multiple commands)

### 5.4 Phase 4: Manage Devkit Integration (Low Risk)

**Goal:** Integrate with "manage" devkit system.

**Tasks:**

1. Research "manage" devkit system
2. Detect if "manage" is available
3. Use "manage" hooks/templates if available
4. Fallback to thegent defaults if not

**Files:**

- `src/thegent/utils.py` — Add manage detection
- `src/thegent/install.py` — Check for manage integration
- Documentation — Document manage integration

**Timeline:** 2-3 hours (after research)

**Risk:** Low (optional integration, fallback exists)

---

## 6. Implementation Details

### 6.1 Dev/Installed Detection Function

```python
# src/thegent/utils.py
import os
import site
from pathlib import Path
from typing import Optional


def _is_dev_mode() -> bool:
    """Detect if running from dev repo vs installed package.

    Returns:
        True if dev mode (repo), False if installed (site-packages)
    """
    # Explicit override
    mode = os.environ.get("THGENT_MODE", "").lower()
    if mode == "dev":
        return True
    elif mode == "installed":
        return False

    # Auto-detect: check if package is in site-packages
    import thegent

    pkg_path = Path(thegent.__file__).resolve().parent

    # Check site-packages
    site_packages = [Path(p) for p in site.getsitepackages()]
    if any(pkg_path.is_relative_to(sp) for sp in site_packages):
        return False

    # Check for dev repo markers
    for parent in [pkg_path.parent, pkg_path.parent.parent, pkg_path.parent.parent.parent]:
        if (parent / "pyproject.toml").exists() and (parent / "src" / "thegent").exists():
            return True

    # Fallback: assume installed (safer)
    return False


def _get_thegent_root() -> Optional[Path]:
    """Get thegent root directory (dev repo) or None if installed."""
    if not _is_dev_mode():
        return None

    import thegent

    pkg_path = Path(thegent.__file__).resolve().parent
    for parent in [pkg_path.parent, pkg_path.parent.parent, pkg_path.parent.parent.parent]:
        if (parent / "pyproject.toml").exists() and (parent / "src" / "thegent").exists():
            return parent
    return None
```

### 6.2 User Directory Resolution

```python
# src/thegent/config.py additions
from pathlib import Path
import os


def _get_user_config_dir() -> Path:
    """Get user config directory (XDG compliant)."""
    if "XDG_CONFIG_HOME" in os.environ:
        return Path(os.environ["XDG_CONFIG_HOME"]) / "thegent"
    return Path.home() / ".config" / "thegent"


def _get_user_data_dir() -> Path:
    """Get user data directory (XDG compliant)."""
    if "XDG_DATA_HOME" in os.environ:
        return Path(os.environ["XDG_DATA_HOME"]) / "thegent"
    return Path.home() / ".local" / "share" / "thegent"


# Add to ThegentSettings
hooks_dir: Path = Field(
    default_factory=lambda: _get_user_config_dir() / "hooks",
    description="Hooks directory (THGENT_HOOKS_DIR)",
)

templates_dir: Path = Field(
    default_factory=lambda: _get_user_config_dir() / "templates",
    description="Templates directory (THGENT_TEMPLATES_DIR)",
)

scripts_dir: Path = Field(
    default_factory=lambda: _get_user_data_dir() / "scripts",
    description="Scripts directory (THGENT_SCRIPTS_DIR)",
)
```

### 6.3 Hook Resolution Strategy

```python
# hooks/hook-dispatcher/src/main.rs update
fn resolve_hooks_dir() -> PathBuf {
    // 1. HOOKS_DIR env var (explicit override)
    if let Ok(dir) = env::var("HOOKS_DIR") {
        return PathBuf::from(dir);
    }

    // 2. User config directory (installed mode)
    let user_hooks = get_user_config_dir().join("hooks");
    if user_hooks.exists() {
        return user_hooks;
    }

    // 3. Dev repo detection (dev mode)
    if let Ok(exe) = env::current_exe() {
        let mut dir = exe.parent().map(|p| p.to_path_buf());
        for _ in 0..5 {
            if let Some(ref d) = dir {
                if d.join("pretool-dispatcher.sh").exists() {
                    return d.clone();
                }
                dir = d.parent().map(|p| p.to_path_buf());
            } else {
                break;
            }
        }
    }

    // 4. Fallback: ~/.claude/hooks/ (legacy)
    let home = env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    PathBuf::from(format!("{home}/.claude/hooks"))
}
```

### 6.4 Starship Config Strategy

**Option A: Global config (recommended)**

```bash
# ~/.config/thegent/.starship.toml (installed)
# Created by: thegent install --target shell
scan_timeout = 2000
command_timeout = 10000
```

**Option B: Per-project config (dev mode)**

```bash
# .starship.toml (dev repo)
# Only used in dev mode
```

**Option C: Hybrid**

```bash
# .envrc update
if [ -f .starship.toml ]; then
  # Dev mode: use project config
  export STARSHIP_CONFIG="$(pwd)/.starship.toml"
elif [ -f ~/.config/thegent/.starship.toml ]; then
  # Installed mode: use global config
  export STARSHIP_CONFIG="$HOME/.config/thegent/.starship.toml"
fi
```

---

## 7. Package Installation Patterns

### 7.1 Python Package (pip)

**Installation:**

```bash
pip install thegent
# or
pip install -e .  # Dev mode
```

**Package structure:**

```
site-packages/thegent/
├── __init__.py
├── main.py
├── config.py
└── ...
```

**Data files:**

- Use `package_data` in `pyproject.toml` to include hooks/templates
- Install to user directory via `thegent install`

### 7.2 Nix Package

**flake.nix update:**

```nix
{
  packages.default = pkgs.python3Packages.buildPythonPackage {
    # ... existing config ...

    # Include hooks/templates as package data
    postInstall = ''
      mkdir -p $out/share/thegent
      cp -r hooks $out/share/thegent/
      cp -r templates $out/share/thegent/
    '';
  };
}
```

**Usage:**

```bash
nix profile install github:router-for-me/thegent
thegent install  # Installs hooks/templates to ~/.config/thegent/
```

### 7.3 Package Data Strategy

**pyproject.toml:**

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/thegent"]

[tool.hatch.build.targets.wheel.shared-data]
"hooks" = "share/thegent/hooks"
"templates" = "share/thegent/templates"
"scripts" = "share/thegent/scripts"
```

**Access in code:**

```python
import importlib.resources
from pathlib import Path


def _get_package_hooks_dir() -> Path | None:
    """Get hooks directory from installed package."""
    try:
        with importlib.resources.path("thegent", "hooks") as hooks_path:
            return Path(hooks_path)
    except (ModuleNotFoundError, TypeError):
        return None
```

---

## 8. Manage Devkit Integration

### 8.1 Research Needed

**Questions:**

1. What is "manage"? (command, tool, system?)
2. Where does it store hooks/templates?
3. How does it integrate with direnv/nix?
4. Does it provide starship config?

**Investigation:**

- Search codebase for "manage" references
- Check for `manage` command or script
- Check `.factory/` directory structure
- Check if there's a `manage` package or tool

### 8.2 Integration Strategy

**If manage provides hooks:**

```python
def _get_hooks_dir() -> Path:
    """Get hooks directory with manage integration."""
    # 1. Explicit override
    if "THGENT_HOOKS_DIR" in os.environ:
        return Path(os.environ["THGENT_HOOKS_DIR"])

    # 2. Manage devkit (if available)
    manage_hooks = Path.home() / ".manage" / "hooks"
    if manage_hooks.exists():
        return manage_hooks

    # 3. User config (installed)
    user_hooks = _get_user_config_dir() / "hooks"
    if user_hooks.exists():
        return user_hooks

    # 4. Dev repo (dev mode)
    dev_root = _get_thegent_root()
    if dev_root:
        return dev_root / "hooks"

    # 5. Fallback
    return _get_user_config_dir() / "hooks"
```

---

## 9. Benefits

### 9.1 Developer Experience

- ✅ **Works out of box** — No repo directory needed
- ✅ **Clean installation** — Standard package manager workflow
- ✅ **Manage integration** — Works with existing devkit
- ✅ **Backward compatible** — Dev mode still works

### 9.2 Agent Experience

- ✅ **No CWD assumptions** — Works from any directory
- ✅ **Consistent behavior** — Same in dev and production
- ✅ **Fast startup** — No directory traversal overhead

### 9.3 User Experience

- ✅ **Standard locations** — XDG-compliant directories
- ✅ **Easy updates** — Package manager handles updates
- ✅ **Isolated config** — Per-user configuration

---

## 10. Risks and Mitigation

### 10.1 Risks

| Risk                         | Severity | Mitigation                                    |
| ---------------------------- | -------- | --------------------------------------------- |
| **Breaking dev workflow**    | High     | Keep dev mode detection, test thoroughly      |
| **Hook resolution failures** | Medium   | Multiple fallback paths, clear error messages |
| **Config migration**         | Low      | Provide migration script                      |
| **Manage integration**       | Low      | Optional, fallback exists                     |

### 10.2 Migration Strategy

1. **Phase 1:** Add detection (no behavior change)
2. **Phase 2:** Install to user dirs (parallel to repo)
3. **Phase 3:** Prefer user dirs (dev mode fallback)
4. **Phase 4:** Remove repo dependencies (dev mode optional)

---

## 11. Timeline and Effort

| Phase       | Tasks                     | Effort | Risk   | Priority |
| ----------- | ------------------------- | ------ | ------ | -------- |
| **Phase 1** | Dev/installed detection   | 2-3h   | Low    | P1       |
| **Phase 2** | User data directories     | 4-6h   | Medium | P1       |
| **Phase 3** | Remove CWD dependencies   | 3-4h   | Medium | P1       |
| **Phase 4** | Manage devkit integration | 2-3h   | Low    | P2       |

**Total Effort:** 11-16 hours
**Total Risk:** Low-Medium (with fallbacks)

---

## 12. Recommendations

### 12.1 Immediate Actions

1. ✅ **Add dev/installed detection** (Phase 1) — Foundation for all changes
2. ✅ **Research "manage" devkit** — Understand integration points
3. ✅ **Create user directory structure** — Standard locations

### 12.2 Short-term (1-2 weeks)

1. ✅ **Install hooks/templates to user dirs** (Phase 2)
2. ✅ **Update hook resolution** — Check user dirs first
3. ✅ **Test in installed mode** — Verify production workflow

### 12.3 Long-term (1-2 months)

1. ✅ **Remove all CWD dependencies** (Phase 3)
2. ✅ **Integrate with manage** (Phase 4)
3. ✅ **Package for distribution** — PyPI, Nix, etc.

---

## 13. References

### 13.1 Project Documentation

- `src/thegent/config.py` — Current config structure
- `src/thegent/install.py` — Installation logic
- `hooks/hook-dispatcher/src/main.rs` — Hook resolution
- `.envrc` — Environment setup

### 13.2 External Resources

- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
- [Python importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html)
- [Python Packaging Guide](https://packaging.python.org/)
- [Nix Flakes](https://nixos.wiki/wiki/Flakes)

---

## 14. Conclusion

**Current State:** thegent assumes it's running from the dev repository directory, making it unsuitable for production installations.

**Goal:** Make thegent work seamlessly in both dev and installed modes, with integration for "manage" devkit system.

**Approach:**

1. Detect dev vs installed mode
2. Use user directories for installed mode
3. Remove CWD dependencies
4. Integrate with manage devkit

**Expected Benefits:**

- ✅ Works out of box for production users
- ✅ Clean package manager installation
- ✅ Manage devkit integration
- ✅ Backward compatible with dev mode

**Risk:** Low-Medium (with fallbacks and gradual migration)

**Effort:** 11-16 hours total

**Priority:** P1 (DX/AX/UX Optimization)

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
- [PRODUCTION_PACKAGING_POLISH_OPTIMIZATION_AUDIT_AND_PLAN.md](./PRODUCTION_PACKAGING_POLISH_OPTIMIZATION_AUDIT_AND_PLAN.md) - Packaging plan
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
