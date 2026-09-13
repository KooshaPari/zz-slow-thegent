<DONE>
# Package Design Research Summary

**Date:** 2026-02-17
**Status:** Research Complete
**Purpose:** Quick reference for package design best practices

---

## Key Findings

### 1. Python Packaging (PEP 517/518/440)

**Standards:**
- Use `pyproject.toml` with `hatchling` or `setuptools` backend
- Dynamic versioning from git tags (`hatch-vcs` or `setuptools-scm`)
- Package data via `importlib.resources` (Python 3.9+)
- Platform-specific optional dependencies

**Tools:**
- `hatchling` — Modern build backend
- `maturin` — Rust-Python interop
- `cibuildwheel` — Cross-platform wheel building
- `twine` — PyPI upload

### 2. Native Package Managers

**Homebrew (macOS/Linux):**
- Formula structure with platform-specific dependencies
- Test blocks required
- Use `depends_on "python@3.12"`

**Nix (Cross-Platform):**
- Flake structure with `buildPythonPackage`
- Install data files to `$out/share/thegent`
- Support multiple systems

**Windows:**
- MSIX preferred for modern Windows
- PyInstaller for standalone executables
- Code signing required

**Linux:**
- Debian packages (deb) with `dh_python3`
- RPM packages with `%{python3_sitelib}`
- Follow FHS

### 3. Update Mechanisms

**Patterns:**
- Check on startup (optional, user-configurable)
- Respect user's package manager
- Provide clear update instructions
- Support opt-out

**Implementation:**
- Detect installation method (Homebrew, Nix, pip, etc.)
- Check PyPI for latest version
- Provide platform-specific update commands

### 4. Code Signing

**macOS:**
- `codesign` for binaries
- `notarytool` for notarization
- Required for Gatekeeper

**Windows:**
- `signtool` for executables
- Timestamp servers for long-term validity

**Linux:**
- GPG signing for packages
- `debsign` for Debian
- `rpm --addsign` for RPM

### 5. User Experience

**First-Run Wizard:**
- Detect platform automatically
- Check prerequisites
- Guide initial configuration
- Provide next steps

**Progress Indicators:**
- Rich progress bars for long operations
- Estimated time remaining
- Allow cancellation

**Error Messages:**
- Actionable remediation steps
- Platform-specific instructions
- Link to documentation

---

## Quick Reference

### Dynamic Versioning

```toml
[tool.hatch.version]
source = "vcs"
write_to = "src/thegent/_version.py"
```

### Package Data Access

```python
from importlib import resources

hooks_pkg = resources.files("thegent") / "hooks"
```

### Platform-Specific Dependencies

```toml
[project.optional-dependencies]
windows = ["pywin32>=306"]
macos = ["pyobjc-framework-Cocoa>=10.0"]
linux = ["dbus-python>=1.3.0"]
```

### Update Detection

```python
from packaging import version

latest = get_latest_version()
current = get_current_version()
if version.parse(latest) > version.parse(current):
    prompt_update(latest)
```

---

## See also

- [CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md](CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md) — Full research document
- [PRODUCTION_PACKAGING_POLISH_OPTIMIZATION_AUDIT_AND_PLAN.md](PRODUCTION_PACKAGING_POLISH_OPTIMIZATION_AUDIT_AND_PLAN.md) — Enhanced plan
