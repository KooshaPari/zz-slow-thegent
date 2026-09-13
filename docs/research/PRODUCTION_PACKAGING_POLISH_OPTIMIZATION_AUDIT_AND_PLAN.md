<DONE>
# Production Packaging, Polish & Optimization Audit + Plan
## Cross-Platform Production Readiness (Windows/macOS/Linux)

**Date:** 2026-02-17
**Status:** Comprehensive Cross-Platform Audit Complete, Implementation Plan Ready
**Priority:** P0 (Production Readiness)

---

## Executive Summary

**Goal:** Transform thegent from a dev-focused tool into a **production-ready, shipping-quality cross-platform package** that can be distributed via PyPI, Nix, Homebrew, Windows Installer, Linux packages (deb/rpm), and other package managers with a polished, intuitive user experience across Windows, macOS, and Linux.

**Current State:**
- ✅ Core functionality working (macOS/Linux)
- ⚠️ Windows support partial (WSL2, some native)
- ⚠️ Assumes dev repository directory
- ⚠️ Missing production packaging
- ⚠️ Platform-specific paths inconsistent
- ⚠️ Incomplete error handling
- ⚠️ Limited documentation for end users
- ⚠️ No automated release process
- ⚠️ Missing upgrade/migration paths

**Target State:**
- ✅ Installable via `pip install thegent`, `nix profile install`, `brew install`, `winget install`, `apt install`, `yum install`
- ✅ Works without repository directory on all platforms
- ✅ Platform-aware paths (XDG on Linux, AppData on Windows, Library on macOS)
- ✅ Comprehensive cross-platform error handling with actionable messages
- ✅ Production-grade logging and observability
- ✅ Complete user documentation with platform-specific guides
- ✅ Automated CI/CD releases for all platforms
- ✅ Smooth upgrade experience across platforms

---

## Table of Contents

1. [Cross-Platform Architecture](#1-cross-platform-architecture)
2. [Packaging & Distribution](#2-packaging--distribution)
3. [Platform-Specific Paths & Conventions](#3-platform-specific-paths--conventions)
4. [Directory Dependencies Removal](#4-directory-dependencies-removal)
5. [Error Handling & User Feedback](#5-error-handling--user-feedback)
6. [Performance Optimization](#6-performance-optimization)
7. [User Experience Polish](#7-user-experience-polish)
8. [Documentation Completeness](#8-documentation-completeness)
9. [Testing & Quality Assurance](#9-testing--quality-assurance)
10. [CI/CD & Release Automation](#10-cicd--release-automation)
11. [Security & Compliance](#11-security--compliance)
12. [Monitoring & Observability](#12-monitoring--observability)
13. [Migration & Upgrade Paths](#13-migration--upgrade-paths)
14. [Implementation Plan](#14-implementation-plan)

---

## 1. Cross-Platform Architecture

### 1.1 Platform Support Matrix

| Platform | Status | Package Managers | Shell Support | Desktop Automation | Service Management |
|----------|--------|------------------|---------------|-------------------|-------------------|
| **macOS** (10.15+) | ✅ Primary | Homebrew, pip, nix | zsh, bash | AppleScript | launchd |
| **Linux** (Ubuntu 20.04+, Debian 11+, RHEL 8+) | ✅ Primary | apt, yum, pip, nix, snap | bash, zsh | AT-SPI | systemd |
| **Windows** (10/11) | ⚠️ Partial | pip, winget, chocolatey | PowerShell, WSL2 bash | UI Automation | Task Scheduler, NSSM |
| **WSL2** | ✅ Supported | pip, apt (via WSL2) | bash | Via native Windows | systemd (WSL2) |

### 1.2 Platform Detection Strategy

**Implementation:** `src/thegent/platform.py`

```python
"""Cross-platform detection and utilities."""

import os
import platform
import sys
from enum import Enum
from pathlib import Path
from typing import Literal


class Platform(Enum):
    """Supported platforms."""

    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    WSL2 = "wsl2"
    UNKNOWN = "unknown"


def detect_platform() -> Platform:
    """Detect current platform."""
    system = platform.system().lower()

    # WSL2 detection
    if system == "linux":
        if os.path.exists("/proc/version"):
            with open("/proc/version") as f:
                if "microsoft" in f.read().lower() or "wsl" in f.read().lower():
                    return Platform.WSL2
        return Platform.LINUX

    if system == "darwin":
        return Platform.MACOS

    if system == "windows":
        return Platform.WINDOWS

    return Platform.UNKNOWN


def get_platform_name() -> str:
    """Get platform name string."""
    return detect_platform().value


def is_windows() -> bool:
    """Check if running on Windows (native or WSL2)."""
    plat = detect_platform()
    return plat in (Platform.WINDOWS, Platform.WSL2)


def is_unix() -> bool:
    """Check if running on Unix-like system."""
    plat = detect_platform()
    return plat in (Platform.MACOS, Platform.LINUX, Platform.WSL2)
```

### 1.3 Shell Strategy by Platform

| Context | macOS | Linux | Windows (native) | WSL2 |
|---------|-------|-------|------------------|------|
| **Hooks** | bash | bash | WSL2 bash or pwsh | bash |
| **Agent Subprocess** | bash/zsh | bash | pwsh or WSL2 bash | bash |
| **OS Admin** | bash (dscl) | bash (useradd) | pwsh (New-LocalUser) | bash (via WSL2) |
| **Desktop Automation** | AppleScript | Python+AT-SPI | pwsh + UI Automation | Via native Windows |
| **thegent CLI** | Python | Python | Python | Python |

**Implementation:** `src/thegent/infra/shell_detection.py`

```python
from thegent.platform import detect_platform, Platform


def get_preferred_shell(context: Literal["hooks", "agent", "os_admin", "desktop"]) -> str:
    """Get preferred shell for context on current platform."""
    plat = detect_platform()

    if plat == Platform.WINDOWS:
        if context == "os_admin":
            return "pwsh"
        if context == "desktop":
            return "pwsh"
        if context in ("hooks", "agent"):
            # Prefer WSL2 bash if available
            return "wsl-bash" if _wsl_available() else "pwsh"

    return "bash"


def _wsl_available() -> bool:
    """Check if WSL2 is available."""
    try:
        result = subprocess.run(["wsl", "--list", "--quiet"], capture_output=True, timeout=2)
        return result.returncode == 0
    except Exception:
        return False
```

---

## 2. Packaging & Distribution

### 2.1 Current State Audit

| Aspect | macOS | Linux | Windows | Status |
|--------|-------|-------|---------|--------|
| **Python Package (PyPI)** | ⚠️ Partial | ⚠️ Partial | ⚠️ Partial | Missing package data, no release |
| **Nix Package** | ⚠️ Dev-only | ⚠️ Dev-only | ❌ Missing | Only dev shell |
| **Homebrew** | ❌ Missing | ❌ Missing | N/A | No formula |
| **Windows Installer** | N/A | N/A | ❌ Missing | No MSI/EXE |
| **Linux Packages** | N/A | ❌ Missing | N/A | No deb/rpm |
| **Package Data** | ❌ Missing | ❌ Missing | ❌ Missing | Hooks/templates not included |
| **Version Management** | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual | Hardcoded `0.1.0` |
| **Release Process** | ❌ Manual | ❌ Manual | ❌ Manual | No automation |

### 2.2 Python Package (PyPI) — Cross-Platform

**Current `pyproject.toml` Issues:**
- Missing `package_data` for hooks/templates/scripts
- No platform-specific classifiers
- Missing Windows/Linux-specific dependencies
- No binary wheels for Rust extensions

**Required Changes:**

```toml
[project]
name = "thegent"
version = "0.1.0"  # → Dynamic versioning
description = "Agentic orchestration & governance platform"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Koosha Paridehpour", email = "kooshapari@gmail.com" }]
keywords = ["ai", "agent", "mcp", "orchestration", "automation", "cli"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Operating System :: OS Independent",
    "Operating System :: MacOS",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: Microsoft :: Windows :: Windows 10",
    "Operating System :: Microsoft :: Windows :: Windows 11",
    "Operating System :: POSIX",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "httpx>=0.27.0",
    "typer>=0.21.1",
    "rich>=14.3.1",
    "pydantic>=2.12.5",
    "pydantic-settings>=2.12.0",
    "python-dotenv>=1.2.1",
    "tenacity>=9.0.0",
    "pyyaml>=6.0",
    "fastmcp[tasks]>=3.0.0rc1",
    "starlette>=0.36.0",
    "uvicorn>=0.27.0",
    "opentelemetry-api>=1.27.0",
    "opentelemetry-sdk>=1.27.0",
    "litellm>=1.50.0",
    "tomlkit>=0.12.0",
    "cachetools>=5.0.0",
    "orjson>=3.11.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=4.0.0",
    "pytest-xdist>=3.5.0",
    "ruff>=0.3.0",
    "ty>=0.0.2",
    "basedpyright>=1.12.0",
    "pre-commit>=3.6.0",
    "tach>=0.4.0",
    "vulture>=2.11",
    "radon>=6.0",
]
windows = [
    "pywinauto>=0.6.8",  # Windows UI Automation
    "pywin32>=306",      # Windows API access
]
macos = [
    "py-applescript>=1.0.0",  # macOS AppleScript
]
linux = [
    "pyatspi>=2.46.0",  # Linux AT-SPI
]

[project.scripts]
thegent = "thegent.main:app"

[tool.hatch.build.targets.wheel]
packages = ["src/thegent"]
include = [
    "hooks/**/*",
    "templates/**/*",
    "scripts/**/*",
    "shell/**/*",
]

[tool.hatch.build.targets.sdist]
include = [
    "/hooks",
    "/templates",
    "/scripts",
    "/shell",
    "/docs",
]

# Rust extensions (maturin)
[tool.maturin]
features = ["python"]
module-name = "thegent_discovery"
```

**Binary Wheels Strategy:**

For Rust extensions (`thegent-discovery`, `thegent-git`, etc.), build platform-specific wheels:

```yaml
# .github/workflows/build-wheels.yml
name: Build Wheels
on: [push, pull_request]
jobs:
  build-wheels:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.12", "3.13"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - name: Build wheels
        run: |
          pip install maturin
          maturin build --release --out dist
      - uses: actions/upload-artifact@v3
        with:
          name: wheels-${{ matrix.os }}-py${{ matrix.python-version }}
          path: dist/*.whl
```

### 2.3 Nix Package — Cross-Platform

**Current `flake.nix` Issues:**
- Only provides `devShells.default`
- No `packages.default` output
- Missing Rust extensions build
- No cross-platform support

**Required Changes:**

```nix
{
  description = "thegent: Agentic orchestration & governance platform";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay.url = "github:oxalica/rust-overlay";
  };

  outputs = { self, nixpkgs, flake-utils, rust-overlay }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ rust-overlay.overlays.default ];
        };
        python = pkgs.python312;
        pythonPackages = python.pkgs;

        # Build Rust extensions
        rustExtensions = pkgs.buildRustPackage {
          pname = "thegent-rust-extensions";
          version = "0.1.0";
          src = ./.;
          cargoLock = ./Cargo.lock;
          buildInputs = with pkgs; [
            rust-bin.stable.latest.default
            python
          ];
        };

        # Python package
        thegent = pythonPackages.buildPythonPackage {
          pname = "thegent";
          version = "0.1.0";
          src = ./.;
          format = "pyproject";

          buildInputs = with pythonPackages; [
            hatchling
          ];

          propagatedBuildInputs = with pythonPackages; [
            httpx
            typer
            rich
            pydantic
            pydantic-settings
            python-dotenv
            tenacity
            pyyaml
            fastmcp
            starlette
            uvicorn
            opentelemetry-api
            opentelemetry-sdk
            litellm
            tomlkit
            cachetools
            orjson
          ] ++ pkgs.lib.optionals (system == "x86_64-linux" || system == "aarch64-linux") [
            pythonPackages.pyatspi
          ] ++ pkgs.lib.optionals (system == "x86_64-darwin" || system == "aarch64-darwin") [
            pythonPackages.py-applescript
          ];

          postInstall = ''
            # Install hooks/templates to share/thegent
            mkdir -p $out/share/thegent
            cp -r hooks $out/share/thegent/
            cp -r templates $out/share/thegent/
            cp -r scripts $out/share/thegent/

            # Install Rust extensions
            cp -r ${rustExtensions}/lib/* $out/lib/python*/site-packages/
          '';
        };
      in
      {
        packages.default = thegent;
        packages.thegent = thegent;

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            pythonPackages.pip
            pythonPackages.venvShellHook
            uv
            nodejs_20
            nodePackages.npm
            ripgrep
            fd
            jaq
            git
            tmux
            rust-bin.stable.latest.default
          ];

          shellHook = ''
            # Virtualenv setup
            if [ ! -d .venv ]; then
              uv venv
            fi
            source .venv/bin/activate

            # Environment variables
            export PYTHONPATH=$PYTHONPATH:$(pwd)/src
            export PATH=$PATH:$(pwd)/.venv/bin:$HOME/.local/bin

            echo "=== thegent dev environment ==="
            echo "Platform: ${system}"
            echo "Python: $(python --version)"
            echo "Node:   $(node --version)"
            echo "uv:     $(uv --version)"
            echo "==============================="
          '';
        };
      }
    );
}
```

### 2.4 Homebrew Formula (macOS/Linux)

**New File:** `Formula/thegent.rb`

```ruby
class Thegent < Formula
  desc "Agentic orchestration & governance platform"
  homepage "https://github.com/router-for-me/thegent"
  url "https://github.com/router-for-me/thegent/archive/v0.1.0.tar.gz"
  sha256 "..."
  license "MIT"

  depends_on "python@3.12"
  depends_on "rust" => :build

  # Platform-specific dependencies
  on_macos do
    depends_on "python-tk"  # For macOS-specific features
  end

  on_linux do
    depends_on "dbus"       # For Linux AT-SPI
    depends_on "at-spi2-core"
  end

  def install
    # Install Python package
    system "pip3", "install", "--prefix=#{prefix}", "."

    # Install hooks/templates
    system "#{bin}/thegent", "install", "--target", "all", "--force"
  end

  test do
    system "#{bin}/thegent", "--version"
    system "#{bin}/thegent", "doctor"
  end
end
```

### 2.5 Windows Installer (MSI/EXE)

**Tools:**
- **cx_Freeze** — Cross-platform freezing
- **PyInstaller** — Standalone executables
- **Inno Setup** — Windows installer creation
- **NSIS** — Nullsoft Scriptable Install System

**Recommended:** PyInstaller + Inno Setup

**Implementation:** `scripts/build-windows-installer.py`

```python
"""Build Windows installer for thegent."""

import subprocess
import sys
from pathlib import Path


def build_installer():
    """Build Windows MSI/EXE installer."""
    # 1. Build PyInstaller executable
    subprocess.run(
        [
            "pyinstaller",
            "--name=thegent",
            "--onefile",
            "--console",
            "--add-data=hooks;hooks",
            "--add-data=templates;templates",
            "--add-data=scripts;scripts",
            "src/thegent/main.py",
        ],
        check=True,
    )

    # 2. Create Inno Setup installer
    subprocess.run(["iscc", "scripts/thegent-installer.iss"], check=True)


if __name__ == "__main__":
    build_installer()
```

**Inno Setup Script:** `scripts/thegent-installer.iss`

```iss
[Setup]
AppName=thegent
AppVersion=0.1.0
DefaultDirName={autopf}\thegent
DefaultGroupName=thegent
OutputDir=dist
OutputBaseFilename=thegent-setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\thegent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "hooks\*"; DestDir: "{app}\hooks"; Flags: recursesubdirs
Source: "templates\*"; DestDir: "{app}\templates"; Flags: recursesubdirs

[Icons]
Name: "{group}\thegent"; Filename: "{app}\thegent.exe"

[Run]
Filename: "{app}\thegent.exe"; Parameters: "install --target all"; StatusMsg: "Installing hooks and templates..."
```

### 2.6 Linux Packages (deb/rpm)

**Debian/Ubuntu (.deb):**

**File:** `debian/control`

```
Source: thegent
Section: devel
Priority: optional
Maintainer: Koosha Paridehpour <kooshapari@gmail.com>
Build-Depends: debhelper (>= 11), python3-all, python3-setuptools, rustc, cargo
Standards-Version: 4.1.3
Homepage: https://github.com/router-for-me/thegent

Package: thegent
Architecture: all
Depends: ${python3:Depends}, ${misc:Depends}, python3 (>= 3.12)
Description: Agentic orchestration & governance platform
 Thegent is a unified agent orchestration CLI for Factory skills and droids.
```

**Build Script:** `scripts/build-deb.sh`

```bash
#!/bin/bash
set -euo pipefail

# Build .deb package
dpkg-buildpackage -us -uc -b

# Result: ../thegent_0.1.0-1_amd64.deb
```

**RHEL/CentOS (.rpm):**

**File:** `thegent.spec`

```spec
Name:           thegent
Version:        0.1.0
Release:        1%{?dist}
Summary:        Agentic orchestration & governance platform
License:        MIT
URL:            https://github.com/router-for-me/thegent
Source0:        %{name}-%{version}.tar.gz
BuildRequires:  python3-devel python3-setuptools rust cargo
Requires:       python3 >= 3.12

%description
Thegent is a unified agent orchestration CLI for Factory skills and droids.

%prep
%setup -q

%build
python3 setup.py build

%install
python3 setup.py install --skip-build --root %{buildroot}

%files
%{python3_sitelib}/thegent
%{_bindir}/thegent
%{_datadir}/thegent/hooks
%{_datadir}/thegent/templates

%changelog
* Mon Feb 17 2026 Koosha Paridehpour <kooshapari@gmail.com> - 0.1.0-1
- Initial release
```

**Build Script:** `scripts/build-rpm.sh`

```bash
#!/bin/bash
set -euo pipefail

# Build .rpm package
rpmbuild -ba thegent.spec

# Result: ~/rpmbuild/RPMS/x86_64/thegent-0.1.0-1.el8.x86_64.rpm
```

### 2.7 Winget Package (Windows)

**File:** `winget/thegent.yaml`

```yaml
Id: router-for-me.thegent
Version: 0.1.0
Name: thegent
Publisher: Koosha Paridehpour
License: MIT
LicenseUrl: https://github.com/router-for-me/thegent/blob/main/LICENSE
Homepage: https://github.com/router-for-me/thegent
InstallerType: exe
Installers:
  - Architecture: x64
    InstallerUrl: https://github.com/router-for-me/thegent/releases/download/v0.1.0/thegent-setup.exe
    InstallerSha256: ...
```

### 2.8 Snap Package (Linux)

**File:** `snap/snapcraft.yaml`

```yaml
name: thegent
version: '0.1.0'
summary: Agentic orchestration & governance platform
description: |
  Thegent is a unified agent orchestration CLI for Factory skills and droids.

grade: stable
confinement: classic  # Required for hooks/desktop automation

parts:
  thegent:
    plugin: python
    source: .
    python-version: python3
    requirements:
      - requirements.txt

apps:
  thegent:
    command: bin/thegent
    plugs:
      - home
      - network
      - desktop
```

---

## 3. Platform-Specific Paths & Conventions

### 3.1 Path Resolution Strategy

**Implementation:** `src/thegent/platform_paths.py`

```python
"""Platform-specific path resolution."""

import os
import platform
from pathlib import Path
from typing import Optional

from thegent.platform import detect_platform, Platform


def get_config_dir() -> Path:
    """Get platform-specific config directory (XDG/AppData/Library)."""
    plat = detect_platform()

    if plat == Platform.WINDOWS:
        # Windows: %APPDATA%\thegent
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "thegent"
        # Fallback: %USERPROFILE%\AppData\Roaming\thegent
        return Path.home() / "AppData" / "Roaming" / "thegent"

    elif plat == Platform.MACOS:
        # macOS: ~/Library/Application Support/thegent
        return Path.home() / "Library" / "Application Support" / "thegent"

    else:  # Linux, WSL2
        # Linux: XDG_CONFIG_HOME/thegent or ~/.config/thegent
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "thegent"
        return Path.home() / ".config" / "thegent"


def get_cache_dir() -> Path:
    """Get platform-specific cache directory."""
    plat = detect_platform()

    if plat == Platform.WINDOWS:
        # Windows: %LOCALAPPDATA%\thegent\cache
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / "thegent" / "cache"
        return Path.home() / "AppData" / "Local" / "thegent" / "cache"

    elif plat == Platform.MACOS:
        # macOS: ~/Library/Caches/thegent
        return Path.home() / "Library" / "Caches" / "thegent"

    else:  # Linux, WSL2
        # Linux: XDG_CACHE_HOME/thegent or ~/.cache/thegent
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache:
            return Path(xdg_cache) / "thegent"
        return Path.home() / ".cache" / "thegent"


def get_data_dir() -> Path:
    """Get platform-specific data directory."""
    plat = detect_platform()

    if plat == Platform.WINDOWS:
        # Windows: %LOCALAPPDATA%\thegent
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / "thegent"
        return Path.home() / "AppData" / "Local" / "thegent"

    elif plat == Platform.MACOS:
        # macOS: ~/Library/Application Support/thegent/data
        return Path.home() / "Library" / "Application Support" / "thegent" / "data"

    else:  # Linux, WSL2
        # Linux: XDG_DATA_HOME/thegent or ~/.local/share/thegent
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / "thegent"
        return Path.home() / ".local" / "share" / "thegent"


def get_bin_dir() -> Path:
    """Get platform-specific binary directory."""
    plat = detect_platform()

    if plat == Platform.WINDOWS:
        # Windows: %LOCALAPPDATA%\thegent\bin or %USERPROFILE%\.local\bin
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / "thegent" / "bin"
        return Path.home() / ".local" / "bin"

    else:  # macOS, Linux, WSL2
        # Unix: ~/.local/bin
        return Path.home() / ".local" / "bin"


def get_log_dir() -> Path:
    """Get platform-specific log directory."""
    plat = detect_platform()

    if plat == Platform.WINDOWS:
        # Windows: %LOCALAPPDATA%\thegent\logs
        return get_cache_dir().parent / "logs"

    elif plat == Platform.MACOS:
        # macOS: ~/Library/Logs/thegent
        return Path.home() / "Library" / "Logs" / "thegent"

    else:  # Linux, WSL2
        # Linux: ~/.local/share/thegent/logs
        return get_data_dir() / "logs"
```

### 3.2 Path Usage Matrix

| Purpose | macOS | Linux | Windows | WSL2 |
|---------|-------|-------|---------|------|
| **Config** | `~/Library/Application Support/thegent/` | `~/.config/thegent/` | `%APPDATA%\thegent\` | `~/.config/thegent/` |
| **Cache** | `~/Library/Caches/thegent/` | `~/.cache/thegent/` | `%LOCALAPPDATA%\thegent\cache\` | `~/.cache/thegent/` |
| **Data** | `~/Library/Application Support/thegent/data/` | `~/.local/share/thegent/` | `%LOCALAPPDATA%\thegent\` | `~/.local/share/thegent/` |
| **Binaries** | `~/.local/bin/` | `~/.local/bin/` | `%LOCALAPPDATA%\thegent\bin\` | `~/.local/bin/` |
| **Logs** | `~/Library/Logs/thegent/` | `~/.local/share/thegent/logs/` | `%LOCALAPPDATA%\thegent\logs\` | `~/.local/share/thegent/logs/` |
| **Hooks** | `~/.config/thegent/hooks/` | `~/.config/thegent/hooks/` | `%APPDATA%\thegent\hooks\` | `~/.config/thegent/hooks/` |
| **Templates** | `~/.config/thegent/templates/` | `~/.config/thegent/templates/` | `%APPDATA%\thegent\templates\` | `~/.config/thegent/templates/` |

### 3.3 Path Migration

**Migration Script:** `src/thegent/migrate_paths.py`

```python
"""Migrate paths from old locations to platform-specific locations."""

from pathlib import Path
from thegent.platform_paths import get_config_dir, get_cache_dir, get_data_dir


def migrate_paths() -> None:
    """Migrate old paths to platform-specific locations."""
    # Old locations
    old_config = Path.home() / ".thegent"
    old_cache = Path.home() / ".cache" / "thegent"

    # New locations
    new_config = get_config_dir()
    new_cache = get_cache_dir()
    new_data = get_data_dir()

    # Migrate config
    if old_config.exists() and not new_config.exists():
        new_config.mkdir(parents=True, exist_ok=True)
        shutil.copytree(old_config, new_config, dirs_exist_ok=True)
        console.print(f"[green]Migrated config from {old_config} to {new_config}[/green]")

    # Migrate cache
    if old_cache.exists() and not new_cache.exists():
        new_cache.mkdir(parents=True, exist_ok=True)
        shutil.copytree(old_cache, new_cache, dirs_exist_ok=True)
        console.print(f"[green]Migrated cache from {old_cache} to {new_cache}[/green]")
```

---

## 4. Directory Dependencies Removal

### 4.1 Current Dependencies (Cross-Platform Audit)

| File | Dependency | macOS | Linux | Windows | Impact |
|------|-----------|-------|-------|---------|--------|
| `.envrc` | `$(pwd)/.starship.toml` | ⚠️ High | ⚠️ High | ❌ N/A | Starship config not found |
| `.envrc` | `$(pwd)/.venv` | ⚠️ Medium | ⚠️ Medium | ❌ N/A | Dev venv only |
| `.envrc` | `$(pwd)/src` | ⚠️ High | ⚠️ High | ❌ N/A | PYTHONPATH for dev |
| `doctor.py` | `Path.cwd() / "src/thegent"` | ⚠️ High | ⚠️ High | ⚠️ High | Assumes repo structure |
| `mcp_manage.py` | `Path(thegent.__file__).parent.parent.parent` | ⚠️ High | ⚠️ High | ⚠️ High | Assumes repo structure |

### 4.2 Dev/Installed Detection (Cross-Platform)

**Implementation:** `src/thegent/utils.py`

```python
"""Cross-platform utilities."""

import os
import site
import sys
from pathlib import Path
from typing import Optional

from thegent.platform import detect_platform


def _is_dev_mode() -> bool:
    """Detect if running from dev repo vs installed package (cross-platform)."""
    # Explicit override
    mode = os.environ.get("THGENT_MODE", "").lower()
    if mode == "dev":
        return True
    elif mode == "installed":
        return False

    # Auto-detect: check if package is in site-packages
    import thegent

    pkg_path = Path(thegent.__file__).resolve().parent

    # Check site-packages (works on all platforms)
    try:
        site_packages = [Path(p) for p in site.getsitepackages()]
        if sys.platform == "win32":
            # Windows: also check user site-packages
            site_packages.append(Path(site.getusersitepackages()))

        if any(pkg_path.is_relative_to(sp) for sp in site_packages):
            return False
    except Exception:
        pass

    # Check for dev repo markers
    for parent in [pkg_path.parent, pkg_path.parent.parent, pkg_path.parent.parent.parent]:
        if (parent / "pyproject.toml").exists() and (parent / "src" / "thegent").exists():
            return True

    # Fallback: assume installed (safer for production)
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

### 4.3 Package Data Access (Cross-Platform)

**Implementation:** `src/thegent/resources.py`

```python
"""Cross-platform resource access."""

import importlib.resources
from pathlib import Path
from typing import Optional

from thegent.platform_paths import get_config_dir
from thegent.utils import _is_dev_mode, _get_thegent_root


def get_hooks_dir() -> Path:
    """Get hooks directory with cross-platform fallback chain."""
    # 1. Explicit override
    hooks_dir_env = os.environ.get("THGENT_HOOKS_DIR")
    if hooks_dir_env:
        return Path(hooks_dir_env).expanduser().resolve()

    # 2. User config (installed mode)
    user_hooks = get_config_dir() / "hooks"
    if user_hooks.exists():
        return user_hooks

    # 3. Package data (installed mode)
    try:
        with importlib.resources.path("thegent", "hooks") as hooks_path:
            return Path(hooks_path)
    except (ModuleNotFoundError, TypeError, FileNotFoundError):
        pass

    # 4. Dev repo (dev mode)
    dev_root = _get_thegent_root()
    if dev_root:
        dev_hooks = dev_root / "hooks"
        if dev_hooks.exists():
            return dev_hooks

    # 5. Fallback: create user config directory
    user_hooks.mkdir(parents=True, exist_ok=True)
    return user_hooks


def get_templates_dir() -> Path:
    """Get templates directory with cross-platform fallback chain."""
    # Same pattern as get_hooks_dir()
    # ...
```

---

## 5. Error Handling & User Feedback

### 5.1 Cross-Platform Error Messages

**Platform-Specific Error Context:**

```python
from thegent.platform import detect_platform, Platform


class ThegentError(Exception):
    """Base exception with platform-aware remediation."""

    def __init__(
        self,
        message: str,
        remediation: str | None = None,
        exit_code: int = 1,
        platform_hint: dict[str, str] | None = None,
    ):
        self.message = message
        self.remediation = remediation or self._get_platform_remediation(platform_hint)
        self.exit_code = exit_code
        super().__init__(message)

    def _get_platform_remediation(self, hints: dict[str, str] | None) -> str:
        """Get platform-specific remediation hint."""
        if not hints:
            return "See documentation for platform-specific instructions"

        plat = detect_platform()
        return hints.get(plat.value, hints.get("default", "See documentation"))
```

**Platform-Specific Error Examples:**

```python
# Provider not configured
raise ProviderError(
    message="Provider 'anthropic' not configured",
    platform_hint={
        "macos": "Run: thegent cliproxy login anthropic",
        "linux": "Run: thegent cliproxy login anthropic",
        "windows": "Run: thegent cliproxy login anthropic (or: pwsh -Command 'thegent cliproxy login anthropic')",
        "default": "Run: thegent cliproxy login anthropic",
    },
)

# Permission denied
raise PermissionError(
    message="Cannot write to config directory",
    platform_hint={
        "macos": "Check permissions: chmod 755 ~/Library/Application\\ Support/thegent",
        "linux": "Check permissions: chmod 755 ~/.config/thegent",
        "windows": "Run PowerShell as Administrator or check folder permissions",
        "default": "Check directory permissions",
    },
)
```

### 5.2 Platform-Specific Error Remediation

| Error | macOS | Linux | Windows |
|-------|-------|-------|---------|
| **Provider not configured** | `thegent cliproxy login <provider>` | `thegent cliproxy login <provider>` | `thegent cliproxy login <provider>` or `pwsh -Command '...'` |
| **MCP server not reachable** | `thegent serve` | `thegent serve` | `thegent serve` or check firewall |
| **Permission denied** | `chmod 755 ~/Library/Application\ Support/thegent` | `chmod 755 ~/.config/thegent` | Run as Administrator or check folder permissions |
| **Hook not found** | `thegent install --target hooks` | `thegent install --target hooks` | `thegent install --target hooks` |
| **WSL2 not available** | N/A | N/A | Install WSL2: `wsl --install` |
| **PowerShell not found** | N/A | N/A | Install PowerShell: `winget install Microsoft.PowerShell` |

---

## 6. Performance Optimization

### 6.1 Platform-Specific Optimizations

| Optimization | macOS | Linux | Windows | Impact |
|--------------|-------|-------|---------|--------|
| **Git shim caching** | ✅ Fixed | ✅ Fixed | ⚠️ Needs testing | High |
| **Hook resolution** | ⚠️ Multiple fallbacks | ⚠️ Multiple fallbacks | ⚠️ WSL2 detection | Medium |
| **Path resolution** | ⚠️ Library paths | ⚠️ XDG paths | ⚠️ AppData paths | Medium |
| **Startup time** | ⚠️ Lazy imports | ⚠️ Lazy imports | ⚠️ PowerShell startup | Medium |

### 6.2 Windows-Specific Optimizations

**PowerShell Startup:**
- Use `pwsh -NoProfile` for faster startup
- Cache PowerShell module imports
- Use native Windows APIs where possible

**WSL2 Detection:**
- Cache WSL2 availability check
- Prefer native Windows when WSL2 not needed

### 6.3 Cross-Platform Caching

**Unified Cache Strategy:**

```python
from cachetools import TTLCache
from thegent.platform_paths import get_cache_dir

# Platform-agnostic cache
_cache_dir = get_cache_dir()
_cache_dir.mkdir(parents=True, exist_ok=True)

# In-memory cache (all platforms)
_memory_cache: TTLCache[str, Any] = TTLCache(maxsize=128, ttl=300)


# Disk cache (all platforms)
def _get_disk_cache_path(key: str) -> Path:
    """Get disk cache path for key."""
    return _cache_dir / f"{hash(key)}.cache"
```

---

## 7. User Experience Polish

### 7.1 Cross-Platform CLI Completion

**Bash/Zsh (macOS/Linux):**

```bash
# Install completion
eval "$(_THEGENT_COMPLETE=bash_source thegent)"  # Bash
eval "$(_THEGENT_COMPLETE=zsh_source thegent)"   # Zsh

# Add to ~/.bashrc or ~/.zshrc
echo 'eval "$(_THEGENT_COMPLETE=bash_source thegent)"' >> ~/.bashrc
```

**PowerShell (Windows):**

```powershell
# Install completion
Register-ArgumentCompleter -Native -CommandName thegent -ScriptBlock {
    param($commandName, $wordToComplete, $cursorPosition)
    # Completion logic
}

# Add to PowerShell profile
$PROFILE  # Shows profile path
# Add completion script to profile
```

**Fish (Linux/macOS):**

```fish
# Install completion
eval (env _THEGENT_COMPLETE=fish_source thegent)

# Add to ~/.config/fish/config.fish
eval (env _THEGENT_COMPLETE=fish_source thegent) | source
```

### 7.2 Platform-Specific First-Run Experience

**macOS:**
```python
def first_run_wizard_macos() -> None:
    """macOS-specific first-run wizard."""
    console.print("[bold cyan]Welcome to thegent![/bold cyan]")
    console.print("macOS detected. Setting up...")

    # Check Homebrew
    if not shutil.which("brew"):
        console.print("[yellow]Homebrew not found. Install from https://brew.sh[/yellow]")

    # Check Xcode Command Line Tools
    if not Path("/Library/Developer/CommandLineTools").exists():
        console.print("[yellow]Xcode Command Line Tools not installed.[/yellow]")
        console.print("Run: xcode-select --install")

    # Setup continues...
```

**Linux:**
```python
def first_run_wizard_linux() -> None:
    """Linux-specific first-run wizard."""
    console.print("[bold cyan]Welcome to thegent![/bold cyan]")
    console.print("Linux detected. Setting up...")

    # Check package manager
    if shutil.which("apt"):
        console.print("[green]apt detected[/green]")
    elif shutil.which("yum"):
        console.print("[green]yum detected[/green]")
    elif shutil.which("dnf"):
        console.print("[green]dnf detected[/green]")

    # Check XDG directories
    if not os.environ.get("XDG_CONFIG_HOME"):
        console.print("[dim]XDG_CONFIG_HOME not set, using ~/.config[/dim]")

    # Setup continues...
```

**Windows:**
```python
def first_run_wizard_windows() -> None:
    """Windows-specific first-run wizard."""
    console.print("[bold cyan]Welcome to thegent![/bold cyan]")
    console.print("Windows detected. Setting up...")

    # Check PowerShell version
    try:
        result = subprocess.run(["pwsh", "-Command", "$PSVersionTable.PSVersion"], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("[green]PowerShell detected[/green]")
        else:
            console.print("[yellow]PowerShell not found. Install from https://aka.ms/powershell[/yellow]")
    except Exception:
        console.print("[yellow]PowerShell not found[/yellow]")

    # Check WSL2
    try:
        result = subprocess.run(["wsl", "--list", "--quiet"], capture_output=True, timeout=2)
        if result.returncode == 0:
            console.print("[green]WSL2 detected[/green]")
        else:
            console.print("[dim]WSL2 not available (optional)[/dim]")
    except Exception:
        console.print("[dim]WSL2 not available (optional)[/dim]")

    # Setup continues...
```

### 7.3 Platform-Specific Help Text

**Command Help with Platform Hints:**

```python
@app.command()
def run(
    prompt: str = typer.Argument(..., help="Task description"),
    # ...
):
    """
    Run an agent task.

    Examples:
        thegent run "Fix the bug in login.py"
        thegent run "Add tests" --agent codex

    Platform Notes:
        macOS: Uses zsh/bash for agent execution
        Linux: Uses bash for agent execution
        Windows: Uses PowerShell or WSL2 bash (if available)
    """
```

---

## 8. Documentation Completeness

### 8.1 Platform-Specific Documentation

**Required Documentation:**

| Document | macOS | Linux | Windows | Status |
|----------|-------|-------|---------|--------|
| **Installation Guide** | ⚠️ Partial | ⚠️ Partial | ❌ Missing | Need platform-specific guides |
| **Quick Start** | ⚠️ Partial | ⚠️ Partial | ❌ Missing | Need Windows quick start |
| **Troubleshooting** | ⚠️ Partial | ⚠️ Partial | ❌ Missing | Need Windows troubleshooting |
| **Configuration** | ⚠️ Partial | ⚠️ Partial | ❌ Missing | Need Windows config guide |

**Documentation Structure:**

```
docs/
├── user-guide/
│   ├── installation/
│   │   ├── macos.md          # Homebrew, pip, nix
│   │   ├── linux.md          # apt, yum, pip, nix, snap
│   │   ├── windows.md        # pip, winget, chocolatey, MSI
│   │   └── wsl2.md           # WSL2-specific
│   ├── configuration/
│   │   ├── macos.md          # Library paths, launchd
│   │   ├── linux.md          # XDG paths, systemd
│   │   └── windows.md        # AppData paths, Task Scheduler
│   └── troubleshooting/
│       ├── macos.md
│       ├── linux.md
│       └── windows.md
```

### 8.2 Platform-Specific Examples

**macOS Examples:**

```markdown
# macOS Installation

## Homebrew (Recommended)
```bash
brew install thegent
thegent install --target all
```

## pip
```bash
pip3 install thegent
thegent install --target all
```

## Nix
```bash
nix profile install github:router-for-me/thegent
thegent install --target all
```
```

**Linux Examples:**

```markdown
# Linux Installation

## Debian/Ubuntu (apt)
```bash
sudo apt install thegent
thegent install --target all
```

## RHEL/CentOS (yum)
```bash
sudo yum install thegent
thegent install --target all
```

## pip
```bash
pip3 install thegent
thegent install --target all
```
```

**Windows Examples:**

```markdown
# Windows Installation

## pip (Recommended)
```powershell
pip install thegent
thegent install --target all
```

## Winget
```powershell
winget install router-for-me.thegent
thegent install --target all
```

## MSI Installer
1. Download `thegent-setup.exe` from releases
2. Run installer
3. Run `thegent install --target all` in PowerShell
```

---

## 9. Testing & Quality Assurance

### 9.1 Cross-Platform Test Matrix

| Test Type | macOS | Linux | Windows | WSL2 |
|-----------|-------|-------|---------|------|
| **Unit Tests** | ✅ | ✅ | ✅ | ✅ |
| **Integration Tests** | ✅ | ✅ | ⚠️ Partial | ✅ |
| **E2E Tests** | ✅ | ✅ | ⚠️ Partial | ✅ |
| **Packaging Tests** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing |
| **Path Resolution Tests** | ⚠️ Partial | ⚠️ Partial | ❌ Missing | ⚠️ Partial |
| **Shell Detection Tests** | ⚠️ Partial | ⚠️ Partial | ❌ Missing | ⚠️ Partial |

### 9.2 Platform-Specific Test Suites

**Test Structure:**

```
tests/
├── unit/
│   ├── test_platform_detection.py
│   ├── test_platform_paths.py
│   └── test_shell_detection.py
├── integration/
│   ├── test_install_macos.py
│   ├── test_install_linux.py
│   ├── test_install_windows.py
│   └── test_cross_platform_paths.py
└── e2e/
    ├── test_cli_macos.py
    ├── test_cli_linux.py
    └── test_cli_windows.py
```

**Platform Detection Tests:**

```python
# tests/unit/test_platform_detection.py
import pytest
from unittest.mock import patch, mock_open
from thegent.platform import detect_platform, Platform

@pytest.mark.parametrize("system,expected", [
    ("Darwin", Platform.MACOS),
    ("Linux", Platform.LINUX),
    ("Windows", Platform.WINDOWS),
])
def test_platform_detection(system, expected):
    """Test platform detection."""
    with patch("platform.system", return_value=system):
        assert detect_platform() == expected

def test_wsl2_detection():
    """Test WSL2 detection."""
    with patch("platform.system", return_value="Linux"), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="Linux version 5.10.0 Microsoft")):
        assert detect_platform() == Platform.WSL2
```

**Path Resolution Tests:**

```python
# tests/unit/test_platform_paths.py
import pytest
from unittest.mock import patch
from thegent.platform_paths import get_config_dir, get_cache_dir


@pytest.mark.parametrize(
    "platform,appdata,expected",
    [
        ("windows", "C:\\Users\\test\\AppData\\Roaming", "C:\\Users\\test\\AppData\\Roaming\\thegent"),
        ("macos", None, "~/Library/Application Support/thegent"),
        ("linux", None, "~/.config/thegent"),
    ],
)
def test_config_dir_windows(platform, appdata, expected):
    """Test config directory resolution."""
    with (
        patch("thegent.platform.detect_platform", return_value=platform),
        patch.dict("os.environ", {"APPDATA": appdata} if appdata else {}),
    ):
        result = get_config_dir()
        assert str(result) == expected.replace("~", str(Path.home()))
```

### 9.3 CI/CD Test Matrix

**GitHub Actions Matrix:**

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.12", "3.13"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          if [ "${{ matrix.os }}" == "windows-latest" ]; then
            pip install -e ".[windows]"
          elif [ "${{ matrix.os }}" == "macos-latest" ]; then
            pip install -e ".[macos]"
          else
            pip install -e ".[linux]"
          fi
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## 10. CI/CD & Release Automation

### 10.1 Cross-Platform Build Workflows

**Build Matrix:**

```yaml
# .github/workflows/build.yml
name: Build
on:
  push:
    tags:
      - "v*"
jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            python: "3.12"
            wheel: "manylinux2014_x86_64"
          - os: macos-latest
            python: "3.12"
            wheel: "macosx_10_9_x86_64"
          - os: macos-latest
            python: "3.12"
            wheel: "macosx_11_0_arm64"
          - os: windows-latest
            python: "3.12"
            wheel: "win_amd64"
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - name: Build wheel
        run: python -m build --wheel
      - uses: actions/upload-artifact@v3
        with:
          name: wheel-${{ matrix.wheel }}
          path: dist/*.whl
```

### 10.2 Platform-Specific Release Workflows

**macOS/Linux Release:**

```yaml
# .github/workflows/release-unix.yml
name: Release (Unix)
on:
  push:
    tags:
      - "v*"
jobs:
  release-homebrew:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - name: Update Homebrew formula
        run: |
          # Update formula version
          # Submit PR to homebrew-core
```

**Windows Release:**

```yaml
# .github/workflows/release-windows.yml
name: Release (Windows)
on:
  push:
    tags:
      - "v*"
jobs:
  build-installer:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Inno Setup
        run: choco install innosetup -y
      - name: Build installer
        run: python scripts/build-windows-installer.py
      - uses: actions/upload-artifact@v3
        with:
          name: thegent-setup.exe
          path: dist/thegent-setup.exe
```

**Linux Packages:**

```yaml
# .github/workflows/release-linux.yml
name: Release (Linux)
on:
  push:
    tags:
      - "v*"
jobs:
  build-deb:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build .deb
        run: ./scripts/build-deb.sh
      - uses: actions/upload-artifact@v3
        with:
          name: thegent.deb
          path: ../thegent_*.deb

  build-rpm:
    runs-on: centos-stream-8
    steps:
      - uses: actions/checkout@v4
      - name: Build .rpm
        run: ./scripts/build-rpm.sh
      - uses: actions/upload-artifact@v3
        with:
          name: thegent.rpm
          path: ~/rpmbuild/RPMS/x86_64/thegent-*.rpm
```

---

## 11. Security & Compliance

### 11.1 Platform-Specific Security Considerations

| Aspect | macOS | Linux | Windows |
|--------|-------|-------|---------|
| **File Permissions** | Unix permissions (755) | Unix permissions (755) | ACLs, folder permissions |
| **Secret Storage** | Keychain | Keyring | Credential Manager |
| **Service Permissions** | launchd plist | systemd service | Task Scheduler, NSSM |
| **Sandboxing** | App Sandbox | SELinux/AppArmor | Windows Sandbox |

### 11.2 Cross-Platform Secret Management

**Implementation:** `src/thegent/security/secrets.py`

```python
"""Cross-platform secret management."""

from thegent.platform import detect_platform, Platform


def get_secret_storage():
    """Get platform-specific secret storage."""
    plat = detect_platform()

    if plat == Platform.MACOS:
        from thegent.security.macos_secrets import MacOSKeychain

        return MacOSKeychain()

    elif plat == Platform.LINUX:
        from thegent.security.linux_secrets import LinuxKeyring

        return LinuxKeyring()

    elif plat == Platform.WINDOWS:
        from thegent.security.windows_secrets import WindowsCredentialManager

        return WindowsCredentialManager()

    else:
        # Fallback: encrypted file
        from thegent.security.file_secrets import FileSecretStore

        return FileSecretStore()
```

---

## 12. Monitoring & Observability

### 12.1 Platform-Specific Logging

**Log Locations:**

| Platform | Default Log Location | Environment Variable |
|----------|---------------------|---------------------|
| **macOS** | `~/Library/Logs/thegent/thegent.log` | `THGENT_LOG_FILE` |
| **Linux** | `~/.local/share/thegent/logs/thegent.log` | `THGENT_LOG_FILE` |
| **Windows** | `%LOCALAPPDATA%\thegent\logs\thegent.log` | `THGENT_LOG_FILE` |

**Unified Logging:**

```python
from thegent.platform_paths import get_log_dir


def setup_logging(level: str = "INFO") -> None:
    """Setup cross-platform logging."""
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "thegent.log"

    # Configure logging (works on all platforms)
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stderr),
        ],
    )
```

---

## 13. Migration & Upgrade Paths

### 13.1 Cross-Platform Upgrade

**Upgrade Command:**

```python
@app.command()
def upgrade() -> None:
    """Upgrade thegent to latest version (cross-platform)."""
    plat = detect_platform()

    if plat == Platform.MACOS:
        # Check Homebrew
        if shutil.which("brew"):
            console.print("[cyan]Upgrading via Homebrew...[/cyan]")
            subprocess.run(["brew", "upgrade", "thegent"], check=True)
            return

        # Fallback: pip
        console.print("[cyan]Upgrading via pip...[/cyan]")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "thegent"], check=True)

    elif plat == Platform.LINUX:
        # Check package manager
        if shutil.which("apt"):
            console.print("[cyan]Upgrading via apt...[/cyan]")
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "upgrade", "thegent"], check=True)
            return
        elif shutil.which("yum"):
            console.print("[cyan]Upgrading via yum...[/cyan]")
            subprocess.run(["sudo", "yum", "update", "thegent"], check=True)
            return

        # Fallback: pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "thegent"], check=True)

    elif plat == Platform.WINDOWS:
        # Check winget
        if shutil.which("winget"):
            console.print("[cyan]Upgrading via winget...[/cyan]")
            subprocess.run(["winget", "upgrade", "router-for-me.thegent"], check=True)
            return

        # Fallback: pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "thegent"], check=True)

    console.print("[green]Upgrade complete![/green]")
```

---

## 14. Implementation Plan

### 14.1 Phase Breakdown (Cross-Platform)

| Phase | Duration | Effort | Platforms | Risk |
|-------|----------|--------|-----------|------|
| **Phase 1: Platform Detection** | Week 1 | 4-6h | All | Low |
| **Phase 2: Path Resolution** | Week 1 | 6-8h | All | Medium |
| **Phase 3: Directory Dependencies** | Week 1-2 | 8-12h | All | Medium |
| **Phase 4: Packaging (PyPI)** | Week 2 | 8-10h | All | Low |
| **Phase 5: Packaging (Platform-Specific)** | Week 2-3 | 12-16h | macOS/Linux/Windows | Medium |
| **Phase 6: Error Handling** | Week 3 | 10-14h | All | Medium |
| **Phase 7: UX Polish** | Week 3-4 | 8-12h | All | Low |
| **Phase 8: Documentation** | Week 4 | 12-16h | All | Low |
| **Phase 9: Testing** | Week 4-5 | 10-14h | All | Low |
| **Phase 10: CI/CD** | Week 5 | 8-12h | All | Medium |
| **Phase 11: Security** | Week 5 | 6-8h | All | Low |
| **Phase 12: Observability** | Week 5 | 4-6h | All | Low |
| **Total** | **5 weeks** | **104-142h** | **All** | **Medium** |

### 14.2 Platform Priority

**Priority Order:**
1. **macOS** — Primary platform, most users
2. **Linux** — Primary platform, server deployments
3. **Windows** — Secondary platform, WSL2 support
4. **WSL2** — Tertiary platform, bridge to Windows

### 14.3 Success Criteria (Cross-Platform)

| Criterion | macOS | Linux | Windows | WSL2 |
|-----------|-------|-------|---------|------|
| **Installation works** | ✅ | ✅ | ✅ | ✅ |
| **Works without repo** | ✅ | ✅ | ✅ | ✅ |
| **Platform paths correct** | ✅ | ✅ | ✅ | ✅ |
| **Error messages actionable** | ✅ | ✅ | ✅ | ✅ |
| **Documentation complete** | ✅ | ✅ | ✅ | ✅ |
| **Tests passing** | ✅ | ✅ | ✅ | ✅ |
| **CI/CD automated** | ✅ | ✅ | ✅ | ✅ |

---

## 15. Practical Implementation Checklist

### 15.1 Week 1: Foundation

- [ ] **Day 1-2: Platform Detection**
  - [ ] Create `src/thegent/platform.py`
  - [ ] Implement `detect_platform()`
  - [ ] Add platform detection tests
  - [ ] Test on macOS, Linux, Windows, WSL2

- [ ] **Day 3-4: Path Resolution**
  - [ ] Create `src/thegent/platform_paths.py`
  - [ ] Implement platform-specific path functions
  - [ ] Add path resolution tests
  - [ ] Test on all platforms

- [ ] **Day 5: Directory Dependencies**
  - [ ] Create `src/thegent/utils.py` (dev/installed detection)
  - [ ] Create `src/thegent/resources.py` (package data access)
  - [ ] Update all `_get_project_root()` calls
  - [ ] Test in dev and installed modes

### 15.2 Week 2: Packaging

- [ ] **Day 1-2: PyPI Package**
  - [ ] Update `pyproject.toml` with package data
  - [ ] Create `MANIFEST.in`
  - [ ] Test `pip install` on all platforms
  - [ ] Build and test wheels

- [ ] **Day 3-4: Platform-Specific Packages**
  - [ ] Create Homebrew formula
  - [ ] Create Windows installer script
  - [ ] Create Linux package scripts (deb/rpm)
  - [ ] Test installations

- [ ] **Day 5: Nix Package**
  - [ ] Update `flake.nix` with package output
  - [ ] Add Rust extensions build
  - [ ] Test `nix build` and `nix profile install`

### 15.3 Week 3: Polish & Documentation

- [ ] **Day 1-2: Error Handling**
  - [ ] Create exception hierarchy
  - [ ] Add platform-specific remediation hints
  - [ ] Update all error paths
  - [ ] Test error scenarios

- [ ] **Day 3: UX Polish**
  - [ ] Add command completion (bash/zsh/pwsh/fish)
  - [ ] Add progress indicators
  - [ ] Create first-run wizard
  - [ ] Improve help text

- [ ] **Day 4-5: Documentation**
  - [ ] Rewrite README.md
  - [ ] Create platform-specific installation guides
  - [ ] Create platform-specific troubleshooting guides
  - [ ] Generate API docs

### 15.4 Week 4: Testing & CI/CD

- [ ] **Day 1-2: Testing**
  - [ ] Add platform detection tests
  - [ ] Add path resolution tests
  - [ ] Add packaging tests
  - [ ] Increase coverage to 80%+

- [ ] **Day 3-4: CI/CD**
  - [ ] Create test workflow (all platforms)
  - [ ] Create build workflow (all platforms)
  - [ ] Create release workflow
  - [ ] Test release process

- [ ] **Day 5: Security & Observability**
  - [ ] Add dependency scanning
  - [ ] Add SAST scanning
  - [ ] Implement structured logging
  - [ ] Add metrics collection

### 15.5 Week 5: Final Polish & Release

- [ ] **Day 1-2: Final Testing**
  - [ ] Test on all platforms
  - [ ] Test upgrade paths
  - [ ] Test migration scripts
  - [ ] Fix any issues

- [ ] **Day 3: Documentation Review**
  - [ ] Review all documentation
  - [ ] Add missing examples
  - [ ] Fix platform-specific issues

- [ ] **Day 4: Release Preparation**
  - [ ] Version bump
  - [ ] Changelog generation
  - [ ] Release notes
  - [ ] Pre-release testing

- [ ] **Day 5: Release**
  - [ ] Build all packages
  - [ ] Publish to PyPI
  - [ ] Publish to Nix
  - [ ] Create GitHub release
  - [ ] Announce release

---

## 16. Quick Reference: Platform-Specific Commands

### 16.1 Installation Commands

| Platform | Command |
|----------|---------|
| **macOS (Homebrew)** | `brew install thegent` |
| **macOS (pip)** | `pip3 install thegent` |
| **macOS (Nix)** | `nix profile install github:router-for-me/thegent` |
| **Linux (apt)** | `sudo apt install thegent` |
| **Linux (yum)** | `sudo yum install thegent` |
| **Linux (pip)** | `pip3 install thegent` |
| **Linux (Nix)** | `nix profile install github:router-for-me/thegent` |
| **Windows (pip)** | `pip install thegent` |
| **Windows (winget)** | `winget install router-for-me.thegent` |
| **Windows (MSI)** | Download and run `thegent-setup.exe` |

### 16.2 Post-Installation

| Platform | Command |
|----------|---------|
| **All** | `thegent install --target all` |
| **macOS** | `thegent install --target shell` (for zsh) |
| **Linux** | `thegent install --target shell` (for bash/zsh) |
| **Windows** | `thegent install --target shell` (for PowerShell) |

### 16.3 Verification

| Platform | Command |
|----------|---------|
| **All** | `thegent --version` |
| **All** | `thegent doctor` |

---

## 17. Troubleshooting Quick Reference

### 17.1 Common Issues by Platform

| Issue | macOS | Linux | Windows |
|-------|-------|-------|---------|
| **Command not found** | Check `~/.local/bin` in PATH | Check `~/.local/bin` in PATH | Check `%LOCALAPPDATA%\thegent\bin` in PATH |
| **Permission denied** | `chmod 755 ~/Library/Application\ Support/thegent` | `chmod 755 ~/.config/thegent` | Run PowerShell as Administrator |
| **Provider not configured** | `thegent cliproxy login <provider>` | `thegent cliproxy login <provider>` | `thegent cliproxy login <provider>` |
| **MCP server not reachable** | `thegent serve` | `thegent serve` | `thegent serve` (check firewall) |
| **WSL2 not available** | N/A | N/A | `wsl --install` |
| **PowerShell not found** | N/A | N/A | `winget install Microsoft.PowerShell` |

---

## 18. Edge Cases & Gotchas

### 18.1 Platform-Specific Edge Cases

| Platform | Edge Case | Impact | Solution |
|----------|-----------|--------|----------|
| **macOS** | Case-insensitive filesystem | Path collisions | Use case-sensitive checks |
| **macOS** | SIP (System Integrity Protection) | Cannot modify system directories | Use user directories |
| **Linux** | Multiple Python versions | Wrong Python used | Check `python3 --version` |
| **Linux** | SELinux/AppArmor | Permission denied | Configure policies |
| **Windows** | Long paths (>260 chars) | Path too long | Enable long path support |
| **Windows** | Antivirus interference | Slow execution | Add exclusions |
| **WSL2** | Windows/Unix path mixing | Path resolution failures | Use `wslpath` for conversion |

### 18.2 Path Length Handling (Windows)

**Windows Long Path Support:**

```python
# Enable long path support in Windows
import os
import sys

if sys.platform == "win32":
    # Check if long paths enabled
    import winreg

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem")
        long_paths = winreg.QueryValueEx(key, "LongPathsEnabled")[0]
        if not long_paths:
            console.print("[yellow]Long path support not enabled. Enable via Group Policy.[/yellow]")
    except Exception:
        pass
```

### 18.3 Case Sensitivity (macOS)

**macOS Case-Insensitive Filesystem:**

```python
def resolve_case_sensitive_path(path: Path) -> Path:
    """Resolve path with case sensitivity check (macOS)."""
    if not is_macos():
        return path

    # On macOS, check actual case of path components
    resolved = Path("/")
    for part in path.parts[1:]:
        parent = resolved
        # Find matching component (case-insensitive)
        if parent.exists():
            matches = [p for p in parent.iterdir() if p.name.lower() == part.lower()]
            if matches:
                resolved = matches[0]
            else:
                resolved = parent / part
        else:
            resolved = parent / part

    return resolved
```

---

## 19. Real-World Usage Examples

### 19.1 Complete Installation Flow (macOS)

```bash
# 1. Install via Homebrew
brew install thegent

# 2. Post-installation setup
thegent install --target all

# 3. Verify installation
thegent doctor

# 4. Configure providers
thegent cliproxy login anthropic
thegent cliproxy login openai

# 5. Start MCP server
thegent serve

# 6. Verify everything works
thegent list-agents
thegent run "Hello, world!" --agent codex
```

### 19.2 Complete Installation Flow (Linux)

```bash
# 1. Install via apt
sudo apt update
sudo apt install thegent

# 2. Post-installation setup
thegent install --target all

# 3. Verify installation
thegent doctor

# 4. Configure providers
thegent cliproxy login anthropic

# 5. Start MCP server as systemd service
thegent mcp service install
sudo systemctl start thegent-mcp

# 6. Verify everything works
thegent list-agents
```

### 19.3 Complete Installation Flow (Windows)

```powershell
# 1. Install via pip
pip install thegent

# 2. Post-installation setup
thegent install --target all

# 3. Verify installation
thegent doctor

# 4. Configure providers
thegent cliproxy login anthropic

# 5. Start MCP server
thegent serve

# 6. Verify everything works
thegent list-agents
thegent run "Hello, world!" --agent codex
```

---

## 20. Migration Scenarios

### 20.1 Dev to Production Migration

**Scenario:** Developer has been using thegent from dev repo, now wants to install via package manager.

**Steps:**
1. Backup current config: `cp -r ~/.config/thegent ~/.config/thegent.backup`
2. Install via package manager: `pip install thegent` (or brew, etc.)
3. Run migration: `thegent migrate-paths`
4. Verify: `thegent doctor`
5. Remove old dev installation (optional)

### 20.2 Platform Migration

**Scenario:** User migrates from macOS to Linux (or vice versa).

**Steps:**
1. Export config: `thegent config export > thegent-config.json`
2. On new platform, install thegent
3. Import config: `thegent config import < thegent-config.json`
4. Update paths: `thegent migrate-paths`
5. Verify: `thegent doctor`

### 20.3 Version Upgrade Migration

**Scenario:** Upgrading from v0.1.0 to v0.2.0 with breaking changes.

**Steps:**
1. Check current version: `thegent --version`
2. Backup config: `cp -r ~/.config/thegent ~/.config/thegent.v0.1.0`
3. Upgrade: `pip install --upgrade thegent` (or platform-specific)
4. Run migration: `thegent migrate-config --from 0.1.0 --to 0.2.0`
5. Verify: `thegent doctor`

---

## 21. Rollback Procedures

### 21.1 Package Rollback

**PyPI:**
```bash
pip install thegent==0.1.0  # Specific version
```

**Homebrew:**
```bash
brew uninstall thegent
brew install thegent@0.1.0  # If versioned formula exists
```

**Nix:**
```bash
nix profile remove thegent
nix profile install github:router-for-me/thegent/v0.1.0
```

### 21.2 Config Rollback

```bash
# Restore from backup
cp -r ~/.config/thegent.backup ~/.config/thegent

# Or restore specific files
cp ~/.config/thegent.backup/cliproxy-config.yaml ~/.config/thegent/
```

---

## 22. Performance Benchmarks

### 22.1 Platform-Specific Performance Targets

| Operation | macOS Target | Linux Target | Windows Target |
|-----------|--------------|--------------|----------------|
| **Startup time** | < 100ms | < 100ms | < 200ms (PowerShell overhead) |
| **Hook resolution** | < 10ms | < 10ms | < 20ms (WSL2 detection) |
| **Path resolution** | < 5ms | < 5ms | < 10ms (AppData resolution) |
| **Package data access** | < 5ms | < 5ms | < 10ms |

### 22.2 Optimization Checklist

- [ ] Lazy imports implemented
- [ ] Path resolution cached
- [ ] Hook directory cached
- [ ] Platform detection cached
- [ ] Package data access cached

---

## 23. Intuitive Design Principles

### 23.1 User Mental Model

**What users expect:**
1. **Install once, works everywhere** — Same commands on all platforms
2. **Platform-aware defaults** — Uses correct paths automatically
3. **Clear error messages** — Knows what went wrong and how to fix it
4. **Fast startup** — No noticeable delay
5. **Consistent behavior** — Same functionality across platforms

### 23.2 Design Decisions

| Decision | Rationale | Implementation |
|----------|-----------|----------------|
| **Platform detection first** | Need to know platform before any path operations | `detect_platform()` called early |
| **Fallback chains** | Robustness — always have a working path | Multiple fallback levels |
| **Explicit overrides** | User control — can override defaults | Environment variables |
| **Caching everywhere** | Performance — avoid repeated work | Cache platform, paths, hooks |
| **Platform-specific errors** | UX — actionable remediation | Platform-aware error messages |

### 23.3 Intuitive API Design

**Consistent Commands:**
```bash
# Same on all platforms
thegent install --target all
thegent doctor
thegent serve
thegent run "task"
```

**Platform-Aware Behavior:**
```bash
# Automatically uses correct paths
thegent install --target shell  # zsh on macOS, bash on Linux, pwsh on Windows
thegent config show              # Shows platform-specific paths
```

---

## 24. Practical Code Examples

### 24.1 Complete Platform-Aware Config Loading

```python
"""Complete platform-aware configuration loading."""

from pathlib import Path
from thegent.platform_paths import get_config_dir
from thegent.platform import detect_platform


def load_config() -> dict:
    """Load configuration with platform-aware paths."""
    plat = detect_platform()
    config_dir = get_config_dir()
    config_file = config_dir / "config.yaml"

    # Load config
    if config_file.exists():
        import yaml

        with open(config_file) as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    # Set platform-specific defaults
    config.setdefault("platform", plat.value)
    config.setdefault(
        "paths",
        {
            "config": str(config_dir),
            "cache": str(get_cache_dir()),
            "data": str(get_data_dir()),
        },
    )

    return config
```

### 24.2 Complete Cross-Platform Service Installation

```python
"""Cross-platform service installation."""

from thegent.platform import detect_platform, Platform


def install_service() -> bool:
    """Install thegent as system service (platform-aware)."""
    plat = detect_platform()

    if plat == Platform.MACOS:
        return _install_launchd_service()
    elif plat == Platform.LINUX:
        return _install_systemd_service()
    elif plat == Platform.WINDOWS:
        return _install_task_scheduler_service()
    else:
        raise RuntimeError(f"Service installation not supported on {plat.value}")


def _install_launchd_service() -> bool:
    """Install launchd service (macOS)."""
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.thegent.server.plist"
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.thegent.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/thegent</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""
    plist_path.write_text(plist_content)
    subprocess.run(["launchctl", "load", str(plist_path)], check=True)
    return True


def _install_systemd_service() -> bool:
    """Install systemd service (Linux)."""
    service_path = Path("/etc/systemd/system/thegent-mcp.service")
    service_content = """[Unit]
Description=thegent MCP Server
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/thegent serve
Restart=always

[Install]
WantedBy=multi-user.target"""
    # Requires sudo
    subprocess.run(["sudo", "tee", str(service_path)], input=service_content.encode(), check=True)
    subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
    subprocess.run(["sudo", "systemctl", "enable", "thegent-mcp"], check=True)
    return True


def _install_task_scheduler_service() -> bool:
    """Install Task Scheduler service (Windows)."""
    # Use schtasks.exe or Task Scheduler COM API
    import subprocess

    command = ["schtasks", "/Create", "/TN", "thegent-mcp", "/TR", "thegent serve", "/SC", "ONLOGON", "/F"]
    subprocess.run(command, check=True)
    return True
```

---

## 25. Testing Strategy Deep Dive

### 25.1 Platform-Specific Test Scenarios

**macOS Test Scenarios:**
- [ ] Homebrew installation
- [ ] pip installation
- [ ] Nix installation
- [ ] launchd service installation
- [ ] Library paths resolution
- [ ] Case-insensitive filesystem handling
- [ ] SIP restrictions

**Linux Test Scenarios:**
- [ ] apt/yum/dnf installation
- [ ] pip installation
- [ ] Nix installation
- [ ] systemd service installation
- [ ] XDG paths resolution
- [ ] SELinux/AppArmor policies
- [ ] Multiple Python versions

**Windows Test Scenarios:**
- [ ] pip installation
- [ ] winget installation
- [ ] MSI installer
- [ ] Task Scheduler service
- [ ] AppData paths resolution
- [ ] Long path handling
- [ ] WSL2 detection
- [ ] PowerShell vs CMD

### 25.2 Cross-Platform Test Matrix

| Test | macOS | Linux | Windows | WSL2 |
|------|-------|-------|---------|------|
| **Platform detection** | ✅ | ✅ | ✅ | ✅ |
| **Path resolution** | ✅ | ✅ | ✅ | ✅ |
| **Package installation** | ✅ | ✅ | ✅ | ✅ |
| **Service installation** | ✅ | ✅ | ✅ | N/A |
| **Error handling** | ✅ | ✅ | ✅ | ✅ |
| **Shell detection** | ✅ | ✅ | ✅ | ✅ |

---

## 26. Release Checklist (Complete)

### 26.1 Pre-Release (All Platforms)

- [ ] **Code Quality**
  - [ ] All tests passing
  - [ ] Coverage >= 80%
  - [ ] No lint errors
  - [ ] No type errors
  - [ ] No security vulnerabilities

- [ ] **Packaging**
  - [ ] Version bumped
  - [ ] Changelog updated
  - [ ] Release notes written
  - [ ] All packages build successfully

- [ ] **Documentation**
  - [ ] README updated
  - [ ] Installation guides updated
  - [ ] Troubleshooting guides updated
  - [ ] API docs generated

### 26.2 Release Day (All Platforms)

- [ ] **Build Packages**
  - [ ] PyPI wheels (all platforms)
  - [ ] Nix package
  - [ ] Homebrew formula (if applicable)
  - [ ] Windows installer
  - [ ] Linux packages (deb/rpm)

- [ ] **Publish**
  - [ ] PyPI upload
  - [ ] Nix flake update
  - [ ] Homebrew PR (if applicable)
  - [ ] GitHub release
  - [ ] Announcement

### 26.3 Post-Release (All Platforms)

- [ ] **Verification**
  - [ ] Test installation on all platforms
  - [ ] Verify upgrade paths
  - [ ] Monitor error reports
  - [ ] Gather user feedback

---

## 27. Success Metrics

### 27.1 Installation Success Rate

| Platform | Target | Measurement |
|----------|--------|-------------|
| **macOS** | > 95% | Track installation failures |
| **Linux** | > 95% | Track installation failures |
| **Windows** | > 90% | Track installation failures |

### 27.2 User Satisfaction

| Metric | Target | Measurement |
|--------|--------|-------------|
| **First-run success** | > 90% | Track `thegent doctor` passes |
| **Error resolution** | > 80% | Track error remediation success |
| **Documentation helpfulness** | > 85% | User surveys |

### 27.3 Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Startup time** | < 200ms | Measure `thegent --version` |
| **Path resolution** | < 20ms | Measure path function calls |
| **Hook resolution** | < 20ms | Measure hook directory access |

---

## 28. Advanced Implementation Patterns

### 28.1 Dependency Injection for Platform Abstraction

**Pattern:** Use dependency injection to abstract platform-specific implementations.

```python
"""Platform abstraction via dependency injection."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol


class PathResolver(Protocol):
    """Protocol for path resolution."""

    def get_config_dir(self) -> Path: ...
    def get_cache_dir(self) -> Path: ...
    def get_data_dir(self) -> Path: ...


class PlatformPathResolver:
    """Concrete platform-aware path resolver."""

    def __init__(self, platform: str):
        self.platform = platform

    def get_config_dir(self) -> Path:
        """Get config directory based on platform."""
        if self.platform == "windows":
            return Path(os.environ.get("APPDATA", "")) / "thegent"
        elif self.platform == "macos":
            return Path.home() / "Library" / "Application Support" / "thegent"
        else:
            return Path.home() / ".config" / "thegent"

    # ... other methods ...


class ThegentApp:
    """Main application with injected dependencies."""

    def __init__(self, path_resolver: PathResolver):
        self.path_resolver = path_resolver

    def get_config_path(self) -> Path:
        """Get config path using injected resolver."""
        return self.path_resolver.get_config_dir() / "config.yaml"


# Usage
def create_app() -> ThegentApp:
    """Create app with platform-aware resolver."""
    from thegent.platform import detect_platform

    resolver = PlatformPathResolver(detect_platform().value)
    return ThegentApp(resolver)
```

### 28.2 Strategy Pattern for Shell Execution

**Pattern:** Use strategy pattern for platform-specific shell execution.

```python
"""Strategy pattern for shell execution."""

from abc import ABC, abstractmethod
from typing import Optional
import subprocess


class ShellExecutor(ABC):
    """Abstract shell executor."""

    @abstractmethod
    def execute(self, command: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Execute shell command."""
        pass


class BashExecutor(ShellExecutor):
    """Bash executor (macOS/Linux)."""

    def execute(self, command: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        return subprocess.run(["bash", "-c", command], cwd=cwd, capture_output=True, text=True, check=False)


class PowerShellExecutor(ShellExecutor):
    """PowerShell executor (Windows)."""

    def execute(self, command: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["pwsh", "-NoProfile", "-Command", command], cwd=cwd, capture_output=True, text=True, check=False
        )


class WSLBashExecutor(ShellExecutor):
    """WSL2 bash executor (Windows)."""

    def execute(self, command: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        # Convert Windows path to WSL path if needed
        wsl_cwd = self._convert_to_wsl_path(cwd) if cwd else None
        return subprocess.run(["wsl", "bash", "-c", command], cwd=wsl_cwd, capture_output=True, text=True, check=False)

    def _convert_to_wsl_path(self, path: Path) -> str:
        """Convert Windows path to WSL path."""
        result = subprocess.run(["wsl", "wslpath", str(path)], capture_output=True, text=True, check=True)
        return result.stdout.strip()


def get_shell_executor(platform: str, context: str = "agent") -> ShellExecutor:
    """Get appropriate shell executor for platform."""
    if platform == "windows":
        if context == "hooks" and _wsl_available():
            return WSLBashExecutor()
        return PowerShellExecutor()
    return BashExecutor()
```

### 28.3 Factory Pattern for Service Management

**Pattern:** Use factory pattern for platform-specific service management.

```python
"""Factory pattern for service management."""

from abc import ABC, abstractmethod
from pathlib import Path


class ServiceManager(ABC):
    """Abstract service manager."""

    @abstractmethod
    def install(self, service_name: str, command: str) -> bool:
        """Install service."""
        pass

    @abstractmethod
    def start(self, service_name: str) -> bool:
        """Start service."""
        pass

    @abstractmethod
    def stop(self, service_name: str) -> bool:
        """Stop service."""
        pass

    @abstractmethod
    def uninstall(self, service_name: str) -> bool:
        """Uninstall service."""
        pass


class LaunchdServiceManager(ServiceManager):
    """launchd service manager (macOS)."""

    def install(self, service_name: str, command: str) -> bool:
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{service_name}.plist"
        plist_content = self._generate_plist(service_name, command)
        plist_path.write_text(plist_content)
        subprocess.run(["launchctl", "load", str(plist_path)], check=True)
        return True

    def start(self, service_name: str) -> bool:
        subprocess.run(["launchctl", "start", service_name], check=True)
        return True

    def stop(self, service_name: str) -> bool:
        subprocess.run(["launchctl", "stop", service_name], check=True)
        return True

    def uninstall(self, service_name: str) -> bool:
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{service_name}.plist"
        subprocess.run(["launchctl", "unload", str(plist_path)], check=True)
        plist_path.unlink()
        return True

    def _generate_plist(self, service_name: str, command: str) -> str:
        """Generate launchd plist content."""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{service_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/thegent</string>
        <string>{command}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""


class SystemdServiceManager(ServiceManager):
    """systemd service manager (Linux)."""

    def install(self, service_name: str, command: str) -> bool:
        service_path = Path(f"/etc/systemd/system/{service_name}.service")
        service_content = self._generate_service_file(service_name, command)
        subprocess.run(["sudo", "tee", str(service_path)], input=service_content.encode(), check=True)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
        return True

    def start(self, service_name: str) -> bool:
        subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
        return True

    def stop(self, service_name: str) -> bool:
        subprocess.run(["sudo", "systemctl", "stop", service_name], check=True)
        return True

    def uninstall(self, service_name: str) -> bool:
        subprocess.run(["sudo", "systemctl", "stop", service_name], check=False)
        subprocess.run(["sudo", "systemctl", "disable", service_name], check=False)
        service_path = Path(f"/etc/systemd/system/{service_name}.service")
        subprocess.run(["sudo", "rm", str(service_path)], check=True)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        return True

    def _generate_service_file(self, service_name: str, command: str) -> str:
        """Generate systemd service file content."""
        return f"""[Unit]
Description=thegent {service_name}
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/thegent {command}
Restart=always

[Install]
WantedBy=multi-user.target"""


class TaskSchedulerServiceManager(ServiceManager):
    """Task Scheduler service manager (Windows)."""

    def install(self, service_name: str, command: str) -> bool:
        subprocess.run(
            ["schtasks", "/Create", "/TN", service_name, "/TR", f"thegent {command}", "/SC", "ONLOGON", "/F"],
            check=True,
        )
        return True

    def start(self, service_name: str) -> bool:
        subprocess.run(["schtasks", "/Run", "/TN", service_name], check=True)
        return True

    def stop(self, service_name: str) -> bool:
        subprocess.run(["schtasks", "/End", "/TN", service_name], check=True)
        return True

    def uninstall(self, service_name: str) -> bool:
        subprocess.run(["schtasks", "/Delete", "/TN", service_name, "/F"], check=True)
        return True


def get_service_manager(platform: str) -> ServiceManager:
    """Get platform-specific service manager."""
    if platform == "macos":
        return LaunchdServiceManager()
    elif platform == "linux":
        return SystemdServiceManager()
    elif platform == "windows":
        return TaskSchedulerServiceManager()
    else:
        raise ValueError(f"Unsupported platform: {platform}")
```

### 28.4 Observer Pattern for Configuration Changes

**Pattern:** Use observer pattern to react to configuration changes across platforms.

```python
"""Observer pattern for configuration changes."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Callable
import watchdog.observers
import watchdog.events


class ConfigObserver(ABC):
    """Abstract config observer."""

    @abstractmethod
    def on_config_changed(self, config_path: Path) -> None:
        """Called when config changes."""
        pass


class ConfigWatcher:
    """Watch config files for changes."""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.observers: List[ConfigObserver] = []
        self.file_observer = watchdog.observers.Observer()

    def add_observer(self, observer: ConfigObserver) -> None:
        """Add config observer."""
        self.observers.append(observer)

    def start(self) -> None:
        """Start watching config directory."""
        handler = ConfigFileHandler(self.observers)
        self.file_observer.schedule(handler, str(self.config_dir), recursive=False)
        self.file_observer.start()

    def stop(self) -> None:
        """Stop watching."""
        self.file_observer.stop()
        self.file_observer.join()


class ConfigFileHandler(watchdog.events.FileSystemEventHandler):
    """Handle config file changes."""

    def __init__(self, observers: List[ConfigObserver]):
        self.observers = observers

    def on_modified(self, event: watchdog.events.FileSystemEvent) -> None:
        """Handle file modification."""
        if event.is_directory:
            return
        config_path = Path(event.src_path)
        if config_path.suffix in (".yaml", ".yml", ".json", ".toml"):
            for observer in self.observers:
                observer.on_config_changed(config_path)


class ReloadProviderObserver(ConfigObserver):
    """Reload providers when config changes."""

    def on_config_changed(self, config_path: Path) -> None:
        """Reload providers."""
        from thegent.agents.cliproxy_manager import reload_providers

        reload_providers()
        console.print(f"[green]Configuration reloaded: {config_path}[/green]")
```

---

## 29. Advanced Error Handling & Recovery

### 29.1 Retry Logic with Exponential Backoff

**Pattern:** Implement retry logic with platform-aware backoff strategies.

```python
"""Retry logic with exponential backoff."""

import time
import random
from typing import Callable, TypeVar, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
) -> T:
    """Retry function with exponential backoff."""
    attempt = 0
    delay = base_delay

    while attempt < max_attempts:
        try:
            return func()
        except exceptions as e:
            attempt += 1
            if attempt >= max_attempts:
                raise

            # Exponential backoff with jitter
            jitter = random.uniform(0, delay * 0.1)
            sleep_time = min(delay + jitter, max_delay)
            time.sleep(sleep_time)
            delay *= 2

    raise RuntimeError("Retry exhausted")


# Platform-aware retry
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
def fetch_provider_config(provider: str) -> dict:
    """Fetch provider config with retry."""
    # Implementation
    pass
```

### 29.2 Circuit Breaker Pattern

**Pattern:** Implement circuit breaker to prevent cascading failures.

```python
"""Circuit breaker pattern for resilience."""

from enum import Enum
from typing import Callable, TypeVar
import time

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0, expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable[[], T]) -> T:
        """Call function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise RuntimeError("Circuit breaker is OPEN")

        try:
            result = func()
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


# Usage
mcp_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60.0, expected_exception=ConnectionError)


def call_mcp_server(command: str) -> dict:
    """Call MCP server with circuit breaker."""
    return mcp_circuit_breaker.call(lambda: _make_mcp_request(command))
```

### 29.3 Graceful Degradation

**Pattern:** Implement graceful degradation for platform-specific features.

```python
"""Graceful degradation for platform features."""

from typing import Optional, Callable, TypeVar
from functools import wraps

T = TypeVar("T")


def graceful_degradation(fallback_value: T, fallback_message: str = "Feature not available") -> Callable:
    """Decorator for graceful degradation."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (NotImplementedError, RuntimeError) as e:
                console.print(f"[yellow]{fallback_message}: {e}[/yellow]")
                return fallback_value

        return wrapper

    return decorator


@graceful_degradation(fallback_value=False, fallback_message="Desktop automation not available")
def automate_desktop(action: str) -> bool:
    """Automate desktop (platform-specific)."""
    plat = detect_platform()
    if plat == Platform.MACOS:
        return _automate_macos(action)
    elif plat == Platform.WINDOWS:
        return _automate_windows(action)
    elif plat == Platform.LINUX:
        return _automate_linux(action)
    else:
        raise NotImplementedError(f"Desktop automation not supported on {plat.value}")
```

---

## 30. Advanced Caching Strategies

### 30.1 Multi-Level Cache System

**Pattern:** Implement multi-level caching (memory → disk → network).

```python
"""Multi-level cache system."""

from cachetools import TTLCache, LRUCache
from pathlib import Path
import pickle
import hashlib
from typing import Optional, TypeVar

T = TypeVar("T")


class MultiLevelCache:
    """Multi-level cache: memory → disk → network."""

    def __init__(
        self, memory_size: int = 128, memory_ttl: int = 300, disk_dir: Optional[Path] = None, disk_ttl: int = 3600
    ):
        # Level 1: In-memory cache (fastest)
        self.memory_cache: TTLCache[str, T] = TTLCache(maxsize=memory_size, ttl=memory_ttl)

        # Level 2: Disk cache (fast, persistent)
        self.disk_dir = disk_dir or Path.home() / ".cache" / "thegent" / "cache"
        self.disk_dir.mkdir(parents=True, exist_ok=True)
        self.disk_ttl = disk_ttl

    def get(self, key: str) -> Optional[T]:
        """Get value from cache (check all levels)."""
        # Level 1: Memory
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Level 2: Disk
        disk_value = self._get_from_disk(key)
        if disk_value is not None:
            # Promote to memory cache
            self.memory_cache[key] = disk_value
            return disk_value

        return None

    def set(self, key: str, value: T) -> None:
        """Set value in cache (all levels)."""
        # Level 1: Memory
        self.memory_cache[key] = value

        # Level 2: Disk
        self._set_to_disk(key, value)

    def _get_from_disk(self, key: str) -> Optional[T]:
        """Get value from disk cache."""
        cache_file = self.disk_dir / f"{self._hash_key(key)}.cache"
        if not cache_file.exists():
            return None

        # Check TTL
        if cache_file.stat().st_mtime + self.disk_ttl < time.time():
            cache_file.unlink()
            return None

        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def _set_to_disk(self, key: str, value: T) -> None:
        """Set value to disk cache."""
        cache_file = self.disk_dir / f"{self._hash_key(key)}.cache"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(value, f)
        except Exception:
            pass

    def _hash_key(self, key: str) -> str:
        """Hash cache key."""
        return hashlib.sha256(key.encode()).hexdigest()


# Global cache instance
_cache = MultiLevelCache(memory_size=128, memory_ttl=300, disk_dir=get_cache_dir() / "cache", disk_ttl=3600)
```

### 30.2 Cache Invalidation Strategies

**Pattern:** Implement smart cache invalidation.

```python
"""Cache invalidation strategies."""

from typing import Set, Callable
from pathlib import Path


class CacheInvalidator:
    """Smart cache invalidation."""

    def __init__(self):
        self.invalidation_rules: List[Callable[[str], bool]] = []
        self.watched_paths: Set[Path] = set()

    def add_rule(self, rule: Callable[[str], bool]) -> None:
        """Add invalidation rule."""
        self.invalidation_rules.append(rule)

    def invalidate_on_file_change(self, path: Path) -> None:
        """Invalidate cache when file changes."""
        self.watched_paths.add(path)
        # Use watchdog to watch file
        # When file changes, invalidate matching cache entries

    def invalidate(self, key_pattern: str) -> None:
        """Invalidate cache entries matching pattern."""
        keys_to_remove = [
            key for key in _cache.memory_cache.keys() if any(rule(key) for rule in self.invalidation_rules)
        ]
        for key in keys_to_remove:
            _cache.memory_cache.pop(key, None)
            _cache._remove_from_disk(key)


# Usage
invalidator = CacheInvalidator()
invalidator.add_rule(lambda key: key.startswith("provider:"))
invalidator.invalidate_on_file_change(get_config_dir() / "cliproxy-config.yaml")
```

---

## 31. Advanced Logging & Observability

### 31.1 Structured Logging with Context

**Pattern:** Implement structured logging with platform-aware context.

```python
"""Structured logging with context."""

import structlog
import sys
from pathlib import Path
from thegent.platform_paths import get_log_dir
from thegent.platform import detect_platform


def setup_structured_logging(level: str = "INFO") -> None:
    """Setup structured logging with platform-aware configuration."""
    plat = detect_platform()
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    # Platform-specific log file
    log_file = log_dir / f"thegent-{plat.value}.log"

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if plat != "windows" else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add file handler
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logging.getLogger().addHandler(handler)


# Usage
logger = structlog.get_logger()


def run_agent(agent: str, prompt: str) -> dict:
    """Run agent with structured logging."""
    logger.info("agent_started", agent=agent, prompt_length=len(prompt), platform=detect_platform().value)

    try:
        result = _execute_agent(agent, prompt)
        logger.info("agent_completed", agent=agent, result_length=len(str(result)), duration_ms=_get_duration())
        return result
    except Exception as e:
        logger.error(
            "agent_failed", agent=agent, error=str(e), error_type=type(e).__name__, duration_ms=_get_duration()
        )
        raise
```

### 31.2 Distributed Tracing

**Pattern:** Implement distributed tracing for cross-platform operations.

```python
"""Distributed tracing for cross-platform operations."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from thegent.platform import detect_platform


def setup_tracing() -> None:
    """Setup distributed tracing."""
    resource = Resource.create(
        {
            "service.name": "thegent",
            "service.version": __version__,
            "platform": detect_platform().value,
        }
    )

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


tracer = trace.get_tracer(__name__)


def trace_operation(operation_name: str):
    """Decorator for tracing operations."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(operation_name) as span:
                span.set_attribute("platform", detect_platform().value)
                span.set_attribute("function", func.__name__)
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


# Usage
@trace_operation("agent.run")
def run_agent(agent: str, prompt: str) -> dict:
    """Run agent with tracing."""
    # Implementation
    pass
```

---

## 32. Advanced Security Patterns

### 32.1 Secure Secret Storage

**Pattern:** Implement platform-specific secure secret storage.

```python
"""Secure secret storage (platform-specific)."""

from abc import ABC, abstractmethod
from typing import Optional


class SecretStore(ABC):
    """Abstract secret store."""

    @abstractmethod
    def store(self, key: str, value: str) -> None:
        """Store secret."""
        pass

    @abstractmethod
    def retrieve(self, key: str) -> Optional[str]:
        """Retrieve secret."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete secret."""
        pass


class MacOSKeychainStore(SecretStore):
    """macOS Keychain secret store."""

    def store(self, key: str, value: str) -> None:
        subprocess.run(["security", "add-generic-password", "-a", "thegent", "-s", key, "-w", value, "-U"], check=True)

    def retrieve(self, key: str) -> Optional[str]:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-a", "thegent", "-s", key, "-w"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def delete(self, key: str) -> None:
        subprocess.run(["security", "delete-generic-password", "-a", "thegent", "-s", key], check=False)


class LinuxKeyringStore(SecretStore):
    """Linux keyring secret store."""

    def store(self, key: str, value: str) -> None:
        import keyring

        keyring.set_password("thegent", key, value)

    def retrieve(self, key: str) -> Optional[str]:
        import keyring

        try:
            return keyring.get_password("thegent", key)
        except Exception:
            return None

    def delete(self, key: str) -> None:
        import keyring

        try:
            keyring.delete_password("thegent", key)
        except Exception:
            pass


class WindowsCredentialStore(SecretStore):
    """Windows Credential Manager secret store."""

    def store(self, key: str, value: str) -> None:
        import win32cred

        win32cred.CredWrite(
            {
                "Type": win32cred.CRED_TYPE_GENERIC,
                "TargetName": f"thegent:{key}",
                "UserName": "thegent",
                "CredentialBlob": value.encode(),
                "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
            },
            0,
        )

    def retrieve(self, key: str) -> Optional[str]:
        import win32cred

        try:
            cred = win32cred.CredRead(f"thegent:{key}", win32cred.CRED_TYPE_GENERIC, 0)
            return cred["CredentialBlob"].decode()
        except Exception:
            return None

    def delete(self, key: str) -> None:
        import win32cred

        try:
            win32cred.CredDelete(f"thegent:{key}", win32cred.CRED_TYPE_GENERIC, 0)
        except Exception:
            pass


def get_secret_store(platform: str) -> SecretStore:
    """Get platform-specific secret store."""
    if platform == "macos":
        return MacOSKeychainStore()
    elif platform == "linux":
        return LinuxKeyringStore()
    elif platform == "windows":
        return WindowsCredentialStore()
    else:
        raise ValueError(f"Unsupported platform: {platform}")
```

### 32.2 Input Validation & Sanitization

**Pattern:** Implement platform-aware input validation.

```python
"""Input validation and sanitization."""

import re
from pathlib import Path
from thegent.platform import detect_platform


def validate_path(path: str) -> Path:
    """Validate and sanitize path (platform-aware)."""
    plat = detect_platform()

    # Basic validation
    if not path or not path.strip():
        raise ValueError("Path cannot be empty")

    # Platform-specific validation
    if plat == "windows":
        # Windows: Check for invalid characters
        invalid_chars = r'[<>:"|?*]'
        if re.search(invalid_chars, path):
            raise ValueError(f"Path contains invalid characters: {path}")

        # Check for reserved names
        reserved_names = (
            {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
        )
        if Path(path).stem.upper() in reserved_names:
            raise ValueError(f"Path uses reserved name: {path}")
    else:
        # Unix: Check for null bytes
        if "\x00" in path:
            raise ValueError("Path contains null byte")

    # Resolve path
    resolved = Path(path).expanduser().resolve()

    # Check length (Windows has 260 char limit unless long paths enabled)
    if plat == "windows" and len(str(resolved)) > 260:
        raise ValueError(f"Path too long: {len(str(resolved))} characters")

    return resolved


def sanitize_command(command: str) -> str:
    """Sanitize shell command (platform-aware)."""
    plat = detect_platform()

    # Remove null bytes
    command = command.replace("\x00", "")

    # Platform-specific sanitization
    if plat == "windows":
        # Windows: Remove PowerShell injection attempts
        dangerous_patterns = [
            r"`.*`",  # Backtick execution
            r"\$\(.*\)",  # Command substitution
            r";\s*[&|]",  # Command chaining
        ]
        for pattern in dangerous_patterns:
            command = re.sub(pattern, "", command)
    else:
        # Unix: Remove shell injection attempts
        dangerous_patterns = [
            r"`.*`",  # Backtick execution
            r"\$\(.*\)",  # Command substitution
            r";\s*[&|]",  # Command chaining
            r"<\(.*\)",  # Process substitution
        ]
        for pattern in dangerous_patterns:
            command = re.sub(pattern, "", command)

    return command.strip()
```

---

## 33. Advanced Performance Optimization

### 33.1 Lazy Loading with Proxies

**Pattern:** Implement lazy loading for expensive operations.

```python
"""Lazy loading with proxies."""

from typing import TypeVar, Callable, Optional
from functools import wraps

T = TypeVar("T")


class LazyProxy:
    """Lazy loading proxy."""

    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._value: Optional[T] = None
        self._loaded = False

    def __getattr__(self, name: str):
        """Lazy load on attribute access."""
        if not self._loaded:
            self._value = self._factory()
            self._loaded = True
        return getattr(self._value, name)

    def __call__(self, *args, **kwargs):
        """Lazy load on call."""
        if not self._loaded:
            self._value = self._factory()
            self._loaded = True
        return self._value(*args, **kwargs)


# Usage
def _load_heavy_module():
    """Load heavy module."""
    import thegent.agents.heavy_module

    return thegent.agents.heavy_module


heavy_module = LazyProxy(_load_heavy_module)

# Only loads when actually used
heavy_module.some_function()
```

### 33.2 Async Operations for I/O

**Pattern:** Use async operations for I/O-bound tasks.

```python
"""Async operations for I/O-bound tasks."""

import asyncio
from typing import List, TypeVar, Callable
from concurrent.futures import ThreadPoolExecutor

T = TypeVar("T")


class AsyncExecutor:
    """Async executor for I/O operations."""

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def run_async(self, func: Callable[[], T]) -> T:
        """Run function asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func)

    async def run_parallel(self, funcs: List[Callable[[], T]]) -> List[T]:
        """Run multiple functions in parallel."""
        tasks = [self.run_async(func) for func in funcs]
        return await asyncio.gather(*tasks)


# Usage
executor = AsyncExecutor()


async def check_providers(providers: List[str]) -> List[dict]:
    """Check multiple providers in parallel."""
    checks = [lambda p=p: _check_provider(p) for p in providers]
    return await executor.run_parallel(checks)
```

---

## 34. Advanced Testing Patterns

### 34.1 Platform-Specific Test Fixtures

**Pattern:** Create platform-specific test fixtures.

```python
"""Platform-specific test fixtures."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from thegent.platform import detect_platform


@pytest.fixture
def mock_platform(request):
    """Mock platform detection."""
    platform_name = request.param
    with patch("thegent.platform.detect_platform") as mock:
        mock.return_value = Platform(platform_name)
        yield platform_name


@pytest.fixture
def temp_config_dir(tmp_path, mock_platform):
    """Create temporary config directory for platform."""
    if mock_platform == "windows":
        config_dir = tmp_path / "AppData" / "Roaming" / "thegent"
    elif mock_platform == "macos":
        config_dir = tmp_path / "Library" / "Application Support" / "thegent"
    else:
        config_dir = tmp_path / ".config" / "thegent"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.mark.parametrize("mock_platform", ["macos", "linux", "windows"], indirect=True)
def test_path_resolution(mock_platform, temp_config_dir):
    """Test path resolution on all platforms."""
    from thegent.platform_paths import get_config_dir

    assert get_config_dir() == temp_config_dir
```

### 34.2 Integration Test Helpers

**Pattern:** Create helpers for integration testing.

```python
"""Integration test helpers."""

import subprocess
import tempfile
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def isolated_environment():
    """Create isolated test environment."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set environment variables
        env = os.environ.copy()
        env["THGENT_CONFIG_DIR"] = str(Path(tmpdir) / "config")
        env["THGENT_CACHE_DIR"] = str(Path(tmpdir) / "cache")
        env["THGENT_DATA_DIR"] = str(Path(tmpdir) / "data")

        yield env


def run_thegent_command(command: List[str], env: dict = None) -> subprocess.CompletedProcess:
    """Run thegent command in test environment."""
    cmd = ["thegent"] + command
    return subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)


# Usage
def test_install_command():
    """Test install command."""
    with isolated_environment() as env:
        result = run_thegent_command(["install", "--target", "hooks"], env=env)
        assert result.returncode == 0
        assert "hooks installed" in result.stdout
```

---

## 35. Advanced Documentation Patterns

### 35.1 Interactive Documentation

**Pattern:** Create interactive documentation with examples.

```python
"""Interactive documentation generator."""
from pathlib import Path
import subprocess

def generate_interactive_docs():
    """Generate interactive documentation with runnable examples."""
    docs_dir = Path("docs")
    examples_dir = docs_dir / "examples"
    examples_dir.mkdir(exist_ok=True)

    # Generate platform-specific examples
    for platform in ["macos", "linux", "windows"]:
        example_file = examples_dir / f"quickstart-{platform}.md"
        example_content = f"""# Quick Start Guide ({platform.title()})

## Installation

```bash
# Install thegent
{_get_install_command(platform)}

# Verify installation
thegent --version
thegent doctor
```

## First Steps

```bash
# Configure providers
thegent cliproxy login anthropic

# Start MCP server
thegent serve

# Run your first agent
thegent run "Hello, world!" --agent codex
```

## Try It Yourself

All examples in this guide are runnable. Copy and paste into your terminal!
"""
        example_file.write_text(example_content)
```

### 35.2 Platform-Specific Troubleshooting Trees

**Pattern:** Create decision trees for troubleshooting.

```markdown
# Troubleshooting Decision Tree

## Issue: Command not found

### macOS
1. Check PATH: `echo $PATH | grep -q ".local/bin" && echo "OK" || echo "Missing"`
2. Add to PATH: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc`
3. Reload shell: `source ~/.zshrc`

### Linux
1. Check PATH: `echo $PATH | grep -q ".local/bin" && echo "OK" || echo "Missing"`
2. Add to PATH: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc`
3. Reload shell: `source ~/.bashrc`

### Windows
1. Check PATH: `$env:PATH -split ';' | Select-String ".local"`
2. Add to PATH: `[Environment]::SetEnvironmentVariable("Path", "$env:Path;$env:LOCALAPPDATA\thegent\bin", "User")`
3. Restart PowerShell
```

---

## 36. Real-World Integration Scenarios

### 36.1 CI/CD Pipeline Integration

**Scenario:** Integrating thegent into existing CI/CD pipelines across platforms.

**GitHub Actions Example:**

```yaml
# .github/workflows/thegent-ci.yml
name: thegent CI
on: [push, pull_request]

jobs:
  test-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install thegent
        run: |
          pip install thegent
          thegent install --target all
      - name: Run tests
        run: |
          thegent doctor
          thegent run "Run test suite" --agent codex

  test-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install thegent
        run: |
          pip install thegent
          thegent install --target all
      - name: Run tests
        run: |
          thegent doctor
          thegent run "Run test suite" --agent codex

  test-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install thegent
        run: |
          pip install thegent
          thegent install --target all
      - name: Run tests
        shell: pwsh
        run: |
          thegent doctor
          thegent run "Run test suite" --agent codex
```

**GitLab CI Example:**

```yaml
# .gitlab-ci.yml
stages:
  - test

test:macos:
  image: macos:latest
  script:
    - pip install thegent
    - thegent install --target all
    - thegent doctor
    - thegent run "Run test suite" --agent codex

test:linux:
  image: python:3.12
  script:
    - pip install thegent
    - thegent install --target all
    - thegent doctor
    - thegent run "Run test suite" --agent codex

test:windows:
  image: mcr.microsoft.com/windows/servercore:ltsc2022
  script:
    - pip install thegent
    - thegent install --target all
    - thegent doctor
    - thegent run "Run test suite" --agent codex
```

### 36.2 Docker Integration

**Scenario:** Using thegent in Docker containers across platforms.

**Multi-Platform Dockerfile:**

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install thegent
RUN pip install --no-cache-dir thegent

# Install thegent components
RUN thegent install --target all

# Set up environment
ENV PATH="/root/.local/bin:${PATH}"
ENV THGENT_CONFIG_DIR="/root/.config/thegent"
ENV THGENT_CACHE_DIR="/root/.cache/thegent"

# Default command
CMD ["thegent", "serve"]
```

**Docker Compose Example:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  thegent-mcp:
    build: .
    ports:
      - "3847:3847"
    volumes:
      - thegent-config:/root/.config/thegent
      - thegent-cache:/root/.cache/thegent
    environment:
      - THGENT_MODE=installed
    command: thegent serve

volumes:
  thegent-config:
  thegent-cache:
```

### 36.3 Kubernetes Integration

**Scenario:** Deploying thegent in Kubernetes clusters.

**Kubernetes Deployment:**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thegent-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: thegent-mcp
  template:
    metadata:
      labels:
        app: thegent-mcp
    spec:
      containers:
      - name: thegent
        image: thegent:latest
        ports:
        - containerPort: 3847
        env:
        - name: THGENT_MODE
          value: "installed"
        - name: THGENT_CONFIG_DIR
          value: "/config"
        - name: THGENT_CACHE_DIR
          value: "/cache"
        volumeMounts:
        - name: config
          mountPath: /config
        - name: cache
          mountPath: /cache
      volumes:
      - name: config
        persistentVolumeClaim:
          claimName: thegent-config
      - name: cache
        persistentVolumeClaim:
          claimName: thegent-cache
---
apiVersion: v1
kind: Service
metadata:
  name: thegent-mcp
spec:
  selector:
    app: thegent-mcp
  ports:
  - port: 3847
    targetPort: 3847
  type: LoadBalancer
```

---

## 37. Advanced Configuration Management

### 37.1 Hierarchical Configuration

**Pattern:** Implement hierarchical configuration with platform-specific overrides.

```python
"""Hierarchical configuration management."""

from pathlib import Path
import yaml
from typing import Dict, Any
from thegent.platform_paths import get_config_dir
from thegent.platform import detect_platform


class ConfigManager:
    """Hierarchical configuration manager."""

    def __init__(self):
        self.config_dir = get_config_dir()
        self.platform = detect_platform().value
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration with hierarchy."""
        # 1. Default config (package data)
        default_config = self._load_default_config()

        # 2. Platform-specific defaults
        platform_config = self._load_platform_config()

        # 3. User config
        user_config = self._load_user_config()

        # 4. Environment overrides
        env_config = self._load_env_config()

        # Merge (later overrides earlier)
        self._config = {
            **default_config,
            **platform_config,
            **user_config,
            **env_config,
        }

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        try:
            with importlib.resources.path("thegent", "config.default.yaml") as path:
                with open(path) as f:
                    return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _load_platform_config(self) -> Dict[str, Any]:
        """Load platform-specific defaults."""
        platform_config_file = self.config_dir / f"config.{self.platform}.yaml"
        if platform_config_file.exists():
            with open(platform_config_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_user_config(self) -> Dict[str, Any]:
        """Load user configuration."""
        user_config_file = self.config_dir / "config.yaml"
        if user_config_file.exists():
            with open(user_config_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_env_config(self) -> Dict[str, Any]:
        """Load environment variable overrides."""
        config = {}
        for key, value in os.environ.items():
            if key.startswith("THGENT_"):
                # Convert THGENT_SECTION_KEY to nested dict
                parts = key[7:].lower().split("_")
                current = config
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = value
        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split(".")
        current = self._config
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = value

    def save(self) -> None:
        """Save user configuration."""
        user_config_file = self.config_dir / "config.yaml"
        user_config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(user_config_file, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False)
```

### 37.2 Configuration Validation

**Pattern:** Validate configuration with platform-specific rules.

```python
"""Configuration validation."""

from pydantic import BaseModel, Field, field_validator
from thegent.platform import detect_platform


class PlatformConfig(BaseModel):
    """Platform-specific configuration."""

    platform: str = Field(default_factory=lambda: detect_platform().value)

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate platform."""
        valid_platforms = {"macos", "linux", "windows", "wsl2"}
        if v not in valid_platforms:
            raise ValueError(f"Invalid platform: {v}")
        return v


class PathConfig(BaseModel):
    """Path configuration."""

    config_dir: Path
    cache_dir: Path
    data_dir: Path

    @field_validator("config_dir", "cache_dir", "data_dir")
    @classmethod
    def validate_paths(cls, v: Path, info) -> Path:
        """Validate paths."""
        plat = detect_platform()

        # Platform-specific validation
        if plat == "windows":
            # Windows: Check length
            if len(str(v)) > 260:
                raise ValueError(f"Path too long: {v}")
        else:
            # Unix: Check for null bytes
            if "\x00" in str(v):
                raise ValueError("Path contains null byte")

        # Ensure directory exists
        v.mkdir(parents=True, exist_ok=True)
        return v


class ThegentConfig(BaseModel):
    """Complete thegent configuration."""

    platform: PlatformConfig
    paths: PathConfig
    providers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    hooks: Dict[str, bool] = Field(default_factory=dict)

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, v: Dict) -> Dict:
        """Validate providers."""
        # Check for OAuth-only providers
        oauth_only = {"anthropic", "openai", "google"}
        for provider, config in v.items():
            if provider in oauth_only and "api_key" in config:
                raise ValueError(f"{provider} must use OAuth, not API key")
        return v
```

---

## 38. Advanced Monitoring & Alerting

### 38.1 Health Check Endpoints

**Pattern:** Implement health check endpoints for monitoring.

```python
"""Health check endpoints."""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from thegent.platform import detect_platform

app = FastAPI()


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "platform": detect_platform().value, "version": __version__}


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check."""
    checks = {
        "platform": _check_platform(),
        "paths": _check_paths(),
        "providers": _check_providers(),
        "mcp_server": _check_mcp_server(),
    }

    all_healthy = all(check["status"] == "healthy" for check in checks.values())

    return JSONResponse(
        status_code=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "healthy" if all_healthy else "degraded",
            "checks": checks,
            "platform": detect_platform().value,
        },
    )


def _check_platform() -> dict:
    """Check platform detection."""
    try:
        plat = detect_platform()
        return {"status": "healthy", "platform": plat.value, "message": f"Platform detected: {plat.value}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def _check_paths() -> dict:
    """Check path resolution."""
    try:
        from thegent.platform_paths import get_config_dir, get_cache_dir, get_data_dir

        paths = {
            "config": get_config_dir(),
            "cache": get_cache_dir(),
            "data": get_data_dir(),
        }
        # Check if paths are writable
        for name, path in paths.items():
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            if not os.access(path, os.W_OK):
                return {"status": "unhealthy", "error": f"{name} directory not writable: {path}"}
        return {"status": "healthy", "paths": {k: str(v) for k, v in paths.items()}}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 38.2 Metrics Collection

**Pattern:** Collect platform-specific metrics.

```python
"""Metrics collection."""

from prometheus_client import Counter, Histogram, Gauge
from thegent.platform import detect_platform

# Metrics
agent_runs_total = Counter("thegent_agent_runs_total", "Total agent runs", ["agent", "platform", "status"])

agent_duration = Histogram("thegent_agent_duration_seconds", "Agent duration", ["agent", "platform"])

path_resolution_duration = Histogram(
    "thegent_path_resolution_seconds", "Path resolution duration", ["path_type", "platform"]
)

cache_hits = Counter("thegent_cache_hits_total", "Cache hits", ["cache_level", "platform"])

cache_misses = Counter("thegent_cache_misses_total", "Cache misses", ["cache_level", "platform"])


def track_agent_run(agent: str, duration: float, success: bool):
    """Track agent run metrics."""
    plat = detect_platform().value
    status = "success" if success else "failure"
    agent_runs_total.labels(agent=agent, platform=plat, status=status).inc()
    agent_duration.labels(agent=agent, platform=plat).observe(duration)


def track_path_resolution(path_type: str, duration: float):
    """Track path resolution metrics."""
    plat = detect_platform().value
    path_resolution_duration.labels(path_type=path_type, platform=plat).observe(duration)


def track_cache_access(level: str, hit: bool):
    """Track cache access metrics."""
    plat = detect_platform().value
    if hit:
        cache_hits.labels(cache_level=level, platform=plat).inc()
    else:
        cache_misses.labels(cache_level=level, platform=plat).inc()
```

---

## 39. Advanced User Experience Patterns

### 39.1 Progressive Disclosure

**Pattern:** Show information progressively based on user needs.

```python
"""Progressive disclosure in CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_help_basic():
    """Show basic help (for beginners)."""
    console.print(
        Panel(
            "[bold cyan]thegent[/bold cyan] - Agentic orchestration platform\n\n"
            "[green]Quick Start:[/green]\n"
            "  1. thegent doctor          # Check your setup\n"
            "  2. thegent cliproxy login  # Configure providers\n"
            "  3. thegent serve           # Start MCP server\n"
            '  4. thegent run "task"      # Run your first agent\n\n'
            "[dim]For more help: thegent help --advanced[/dim]",
            title="Welcome to thegent",
        )
    )


def show_help_advanced():
    """Show advanced help (for power users)."""
    table = Table(title="Advanced Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Platform", style="yellow")

    commands = [
        ("thegent install --target hooks", "Install hooks", "All"),
        ("thegent mcp service install", "Install as service", "macOS/Linux/Windows"),
        ("thegent config show", "Show configuration", "All"),
        ("thegent config set key value", "Set config value", "All"),
        ("thegent upgrade", "Upgrade thegent", "All"),
    ]

    for cmd, desc, plat in commands:
        table.add_row(cmd, desc, plat)

    console.print(table)
```

### 39.2 Contextual Help

**Pattern:** Provide contextual help based on current state.

```python
"""Contextual help system."""


def get_contextual_help(context: str) -> str:
    """Get contextual help based on current state."""
    plat = detect_platform().value

    if context == "first_run":
        return f"""
[bold cyan]Welcome to thegent![/bold cyan]

Since this is your first run on {plat}, let's set things up:

1. [green]Check your environment:[/green]
   thegent doctor

2. [green]Configure providers:[/green]
   thegent cliproxy login anthropic

3. [green]Start the MCP server:[/green]
   thegent serve

Need help? Run: thegent help
"""

    elif context == "provider_not_configured":
        return f"""
[bold yellow]Provider not configured[/bold yellow]

To configure a provider on {plat}:

  thegent cliproxy login <provider>

Available providers: anthropic, openai, google, moonshot

For more help: thegent cliproxy help
"""

    elif context == "mcp_not_running":
        return f"""
[bold yellow]MCP server not running[/bold yellow]

Start the MCP server:

  thegent serve

Or install as a service ({plat}):

  thegent mcp service install

For more help: thegent serve --help
"""

    return "Run 'thegent help' for more information"
```

---

## 40. Advanced Packaging Scenarios

### 40.1 Custom Package Builds

**Scenario:** Building custom packages for specific environments.

**Script:** `scripts/build-custom-package.sh`

```bash
#!/bin/bash
# Build custom package for specific environment

set -euo pipefail

PLATFORM="${1:-}"
VARIANT="${2:-standard}"

if [ -z "$PLATFORM" ]; then
    echo "Usage: $0 <platform> [variant]"
    echo "Platforms: macos, linux, windows"
    echo "Variants: standard, minimal, full"
    exit 1
fi

case "$PLATFORM" in
    macos)
        echo "Building macOS package (variant: $VARIANT)..."
        python -m build --wheel
        if [ "$VARIANT" == "full" ]; then
            # Include all optional dependencies
            pip install -e ".[dev,all]"
        elif [ "$VARIANT" == "minimal" ]; then
            # Minimal dependencies only
            pip install -e ".[minimal]"
        fi
        ;;
    linux)
        echo "Building Linux package (variant: $VARIANT)..."
        python -m build --wheel
        ;;
    windows)
        echo "Building Windows package (variant: $VARIANT)..."
        python -m build --wheel
        python scripts/build-windows-installer.py
        ;;
esac

echo "✅ Package built successfully!"
```

### 40.2 Package Signing

**Pattern:** Sign packages for security.

```python
"""Package signing."""

import subprocess
from pathlib import Path


def sign_package(package_path: Path, platform: str) -> bool:
    """Sign package for platform."""
    if platform == "macos":
        # macOS: Code signing
        return _sign_macos(package_path)
    elif platform == "windows":
        # Windows: Authenticode signing
        return _sign_windows(package_path)
    elif platform == "linux":
        # Linux: GPG signing
        return _sign_linux(package_path)
    return False


def _sign_macos(package_path: Path) -> bool:
    """Sign macOS package."""
    # Requires Apple Developer certificate
    subprocess.run(
        [
            "codesign",
            "--sign",
            "Developer ID Application: Your Name",
            "--timestamp",
            "--options",
            "runtime",
            str(package_path),
        ],
        check=True,
    )
    return True


def _sign_windows(package_path: Path) -> bool:
    """Sign Windows package."""
    # Requires code signing certificate
    subprocess.run(
        [
            "signtool",
            "sign",
            "/f",
            "certificate.pfx",
            "/p",
            "password",
            "/t",
            "http://timestamp.digicert.com",
            str(package_path),
        ],
        check=True,
    )
    return True


def _sign_linux(package_path: Path) -> bool:
    """Sign Linux package."""
    # GPG signing
    subprocess.run(["gpg", "--armor", "--detach-sign", str(package_path)], check=True)
    return True
```

---

## Conclusion

This comprehensive cross-platform audit and plan provides a complete roadmap for production-ready packaging across Windows, macOS, and Linux. The 12-phase implementation plan covers all aspects from platform detection to final release, with platform-specific considerations throughout.

**Key Priorities:**
1. **Platform Detection & Paths** (Phase 1-2) — Foundation for everything
2. **Packaging** (Phase 4-5) — Enable distribution on all platforms
3. **Error Handling** (Phase 6) — Critical for user experience
4. **Documentation** (Phase 8) — Platform-specific guides essential

**Expected Outcome:**
A production-ready, shipping-quality cross-platform package that can be installed via standard package managers on Windows, macOS, and Linux with a polished, intuitive user experience and comprehensive platform-specific documentation.

**Timeline:** 5 weeks, 104-142 hours total effort

**Risk:** Medium (manageable with phased approach, platform-specific testing, and fallbacks)

---

## 41. Advanced Deployment Scenarios

### 41.1 Air-Gapped Environments

**Scenario:** Deploying thegent in air-gapped (offline) environments.

**Solution:** Offline package distribution with all dependencies.

```python
"""Offline package builder."""

import subprocess
from pathlib import Path


def build_offline_package(output_dir: Path) -> None:
    """Build offline package with all dependencies."""
    # 1. Download all dependencies
    subprocess.run(["pip", "download", "-d", str(output_dir / "wheels"), "-r", "requirements.txt"], check=True)

    # 2. Build thegent wheel
    subprocess.run(["python", "-m", "build", "--wheel", "--outdir", str(output_dir / "wheels")], check=True)

    # 3. Create installation script
    install_script = output_dir / "install-offline.sh"
    install_script.write_text(f"""#!/bin/bash
# Offline installation script
set -euo pipefail

WHEEL_DIR="{output_dir / "wheels"}"

# Install wheels
pip install --no-index --find-links "$WHEEL_DIR" thegent

# Post-installation
thegent install --target all
""")
    install_script.chmod(0o755)
```

### 41.2 Multi-Tenant Deployments

**Scenario:** Deploying thegent in multi-tenant environments (shared servers).

**Solution:** User isolation with separate config directories.

```python
"""Multi-tenant configuration."""

from pathlib import Path
import os


def get_tenant_config_dir(tenant_id: str) -> Path:
    """Get tenant-specific config directory."""
    base_config = get_config_dir()
    tenant_dir = base_config / "tenants" / tenant_id
    tenant_dir.mkdir(parents=True, exist_ok=True)
    return tenant_dir


def get_tenant_cache_dir(tenant_id: str) -> Path:
    """Get tenant-specific cache directory."""
    base_cache = get_cache_dir()
    tenant_dir = base_cache / "tenants" / tenant_id
    tenant_dir.mkdir(parents=True, exist_ok=True)
    return tenant_dir


# Usage
tenant_id = os.environ.get("THGENT_TENANT_ID", "default")
config_dir = get_tenant_config_dir(tenant_id)
cache_dir = get_tenant_cache_dir(tenant_id)
```

### 41.3 High-Availability Deployments

**Scenario:** Deploying thegent in HA environments with load balancing.

**Solution:** Stateless design with shared state backend.

```python
"""High-availability configuration."""

from typing import Optional
import redis


class SharedStateBackend:
    """Shared state backend for HA deployments."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session from shared backend."""
        data = self.redis.get(f"thegent:session:{session_id}")
        if data:
            return json.loads(data)
        return None

    def set_session(self, session_id: str, data: dict) -> None:
        """Set session in shared backend."""
        self.redis.setex(
            f"thegent:session:{session_id}",
            3600,  # TTL: 1 hour
            json.dumps(data),
        )


# Configuration
HA_BACKEND_URL = os.environ.get("THGENT_HA_BACKEND_URL")
if HA_BACKEND_URL:
    shared_backend = SharedStateBackend(HA_BACKEND_URL)
else:
    shared_backend = None
```

---

## 42. Advanced Troubleshooting Patterns

### 42.1 Self-Diagnostic System

**Pattern:** Implement self-diagnostic system for automatic issue detection.

```python
"""Self-diagnostic system."""

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class DiagnosticLevel(Enum):
    """Diagnostic severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DiagnosticResult:
    """Diagnostic check result."""

    name: str
    level: DiagnosticLevel
    message: str
    remediation: str
    platform: str


class DiagnosticSystem:
    """Self-diagnostic system."""

    def __init__(self):
        self.checks: List[Callable[[], DiagnosticResult]] = []
        self._register_checks()

    def _register_checks(self) -> None:
        """Register diagnostic checks."""
        self.checks.extend(
            [
                self._check_platform_detection,
                self._check_path_resolution,
                self._check_permissions,
                self._check_dependencies,
                self._check_network_connectivity,
                self._check_disk_space,
            ]
        )

    def run_diagnostics(self) -> List[DiagnosticResult]:
        """Run all diagnostic checks."""
        results = []
        for check in self.checks:
            try:
                result = check()
                results.append(result)
            except Exception as e:
                results.append(
                    DiagnosticResult(
                        name=check.__name__,
                        level=DiagnosticLevel.ERROR,
                        message=f"Diagnostic check failed: {e}",
                        remediation="Check logs for details",
                        platform=detect_platform().value,
                    )
                )
        return results

    def _check_platform_detection(self) -> DiagnosticResult:
        """Check platform detection."""
        try:
            plat = detect_platform()
            return DiagnosticResult(
                name="platform_detection",
                level=DiagnosticLevel.INFO,
                message=f"Platform detected: {plat.value}",
                remediation="",
                platform=plat.value,
            )
        except Exception as e:
            return DiagnosticResult(
                name="platform_detection",
                level=DiagnosticLevel.CRITICAL,
                message=f"Platform detection failed: {e}",
                remediation="Set THGENT_PLATFORM environment variable",
                platform="unknown",
            )

    def _check_path_resolution(self) -> DiagnosticResult:
        """Check path resolution."""
        try:
            from thegent.platform_paths import get_config_dir, get_cache_dir, get_data_dir

            config_dir = get_config_dir()
            cache_dir = get_cache_dir()
            data_dir = get_data_dir()

            # Check if directories are writable
            for name, path in [("config", config_dir), ("cache", cache_dir), ("data", data_dir)]:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                if not os.access(path, os.W_OK):
                    return DiagnosticResult(
                        name="path_resolution",
                        level=DiagnosticLevel.ERROR,
                        message=f"{name} directory not writable: {path}",
                        remediation=self._get_permission_remediation(name, path),
                        platform=detect_platform().value,
                    )

            return DiagnosticResult(
                name="path_resolution",
                level=DiagnosticLevel.INFO,
                message="All paths resolved and writable",
                remediation="",
                platform=detect_platform().value,
            )
        except Exception as e:
            return DiagnosticResult(
                name="path_resolution",
                level=DiagnosticLevel.ERROR,
                message=f"Path resolution failed: {e}",
                remediation="Check platform detection and environment variables",
                platform=detect_platform().value,
            )

    def _get_permission_remediation(self, name: str, path: Path) -> str:
        """Get platform-specific permission remediation."""
        plat = detect_platform()
        if plat == Platform.MACOS:
            return f"Run: chmod 755 {path}"
        elif plat == Platform.LINUX:
            return f"Run: chmod 755 {path}"
        elif plat == Platform.WINDOWS:
            return "Run PowerShell as Administrator or check folder permissions"
        return f"Check permissions for {path}"

    def _check_permissions(self) -> DiagnosticResult:
        """Check file permissions."""
        # Implementation
        pass

    def _check_dependencies(self) -> DiagnosticResult:
        """Check required dependencies."""
        # Implementation
        pass

    def _check_network_connectivity(self) -> DiagnosticResult:
        """Check network connectivity."""
        # Implementation
        pass

    def _check_disk_space(self) -> DiagnosticResult:
        """Check disk space."""
        # Implementation
        pass


# Usage
diagnostics = DiagnosticSystem()
results = diagnostics.run_diagnostics()
for result in results:
    if result.level in (DiagnosticLevel.ERROR, DiagnosticLevel.CRITICAL):
        console.print(f"[red]{result.name}: {result.message}[/red]")
        console.print(f"[yellow]Remediation: {result.remediation}[/yellow]")
```

### 42.2 Automated Issue Reporting

**Pattern:** Automatically collect diagnostic information for issue reporting.

```python
"""Automated issue reporting."""

import json
from pathlib import Path
from datetime import datetime


def generate_issue_report() -> dict:
    """Generate comprehensive issue report."""
    plat = detect_platform()

    report = {
        "timestamp": datetime.now().isoformat(),
        "platform": {
            "name": plat.value,
            "architecture": get_architecture(),
            "python_version": sys.version,
        },
        "thegent": {
            "version": __version__,
            "config_dir": str(get_config_dir()),
            "cache_dir": str(get_cache_dir()),
            "data_dir": str(get_data_dir()),
        },
        "environment": {
            "path": os.environ.get("PATH", "").split(os.pathsep),
            "python_path": sys.path,
        },
        "diagnostics": [r.__dict__ for r in diagnostics.run_diagnostics()],
        "logs": _collect_recent_logs(),
    }

    return report


def save_issue_report(report: dict, output_path: Path) -> None:
    """Save issue report to file."""
    output_path.write_text(json.dumps(report, indent=2))
    console.print(f"[green]Issue report saved to: {output_path}[/green]")


def _collect_recent_logs() -> List[str]:
    """Collect recent log entries."""
    log_dir = get_log_dir()
    log_file = log_dir / f"thegent-{detect_platform().value}.log"
    if log_file.exists():
        # Read last 100 lines
        lines = log_file.read_text().splitlines()
        return lines[-100:]
    return []
```

---

## 43. Advanced User Onboarding

### 43.1 Interactive Setup Wizard

**Pattern:** Create interactive setup wizard for first-time users.

```python
"""Interactive setup wizard."""

from rich.prompt import Prompt, Confirm
from rich.console import Console
from rich.panel import Panel

console = Console()


def run_setup_wizard() -> None:
    """Run interactive setup wizard."""
    console.print(
        Panel("[bold cyan]Welcome to thegent![/bold cyan]\n\nLet's set up your environment...", title="Setup Wizard")
    )

    # Step 1: Platform detection
    plat = detect_platform()
    console.print(f"[green]✓[/green] Platform detected: {plat.value}")

    # Step 2: Check dependencies
    console.print("\n[cyan]Checking dependencies...[/cyan]")
    missing_deps = _check_dependencies()
    if missing_deps:
        console.print(f"[yellow]Missing dependencies: {', '.join(missing_deps)}[/yellow]")
        if Confirm.ask("Install missing dependencies?"):
            _install_dependencies(missing_deps)

    # Step 3: Configure providers
    console.print("\n[cyan]Configuring providers...[/cyan]")
    providers = Prompt.ask(
        "Which providers would you like to configure? (comma-separated)", default="anthropic,openai"
    ).split(",")

    for provider in providers:
        provider = provider.strip()
        if Confirm.ask(f"Configure {provider}?"):
            subprocess.run(["thegent", "cliproxy", "login", provider], check=True)

    # Step 4: Install components
    console.print("\n[cyan]Installing components...[/cyan]")
    targets = Prompt.ask("Which components to install? (all/hooks/templates/shell)", default="all")
    subprocess.run(["thegent", "install", "--target", targets], check=True)

    # Step 5: Verify setup
    console.print("\n[cyan]Verifying setup...[/cyan]")
    result = subprocess.run(["thegent", "doctor"], capture_output=True, text=True)
    if result.returncode == 0:
        console.print("[green]✓ Setup complete![/green]")
    else:
        console.print("[yellow]⚠ Setup completed with warnings[/yellow]")
        console.print(result.stdout)

    # Step 6: Next steps
    console.print("\n[bold cyan]Next Steps:[/bold cyan]")
    console.print("  1. Start MCP server: [green]thegent serve[/green]")
    console.print('  2. Run your first agent: [green]thegent run "Hello, world!"[/green]')
    console.print("  3. Get help: [green]thegent help[/green]")
```

### 43.2 Guided Tour

**Pattern:** Create guided tour for new users.

```python
"""Guided tour system."""

from typing import List, Dict


class TourStep:
    """Tour step."""

    def __init__(self, title: str, description: str, command: str, expected_output: str = ""):
        self.title = title
        self.description = description
        self.command = command
        self.expected_output = expected_output


def run_guided_tour() -> None:
    """Run guided tour."""
    steps = [
        TourStep(
            title="Check Your Setup",
            description="Verify that thegent is installed correctly",
            command="thegent doctor",
            expected_output="All checks passing",
        ),
        TourStep(
            title="List Available Agents",
            description="See what agents are available",
            command="thegent list-agents",
        ),
        TourStep(
            title="Run Your First Agent",
            description="Execute a simple task",
            command='thegent run "Hello, world!" --agent codex',
        ),
    ]

    console.print("[bold cyan]thegent Guided Tour[/bold cyan]\n")

    for i, step in enumerate(steps, 1):
        console.print(f"\n[bold]Step {i}: {step.title}[/bold]")
        console.print(f"[dim]{step.description}[/dim]")

        if Confirm.ask(f"Run: [green]{step.command}[/green]?"):
            result = subprocess.run(step.command.split(), capture_output=True, text=True)
            console.print(result.stdout)

            if step.expected_output and step.expected_output in result.stdout:
                console.print("[green]✓ Expected output found![/green]")

        if not Confirm.ask("Continue to next step?", default=True):
            break

    console.print("\n[green]Tour complete![/green]")
```

---

## 44. Advanced Performance Monitoring

### 44.1 Performance Profiling

**Pattern:** Implement performance profiling for optimization.

```python
"""Performance profiling."""

import cProfile
import pstats
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def profile_operation(operation_name: str):
    """Profile an operation."""
    profiler = cProfile.Profile()
    profiler.enable()

    try:
        yield
    finally:
        profiler.disable()

        # Save profile
        profile_dir = get_cache_dir() / "profiles"
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profile_dir / f"{operation_name}-{datetime.now().isoformat()}.prof"

        profiler.dump_stats(str(profile_file))

        # Print summary
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumulative")
        stats.print_stats(10)


# Usage
with profile_operation("agent.run"):
    run_agent("codex", "Hello, world!")
```

### 44.2 Resource Usage Tracking

**Pattern:** Track resource usage across platforms.

```python
"""Resource usage tracking."""

import psutil
import time
from typing import Dict


class ResourceTracker:
    """Track resource usage."""

    def __init__(self):
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss

    def get_usage(self) -> Dict[str, float]:
        """Get current resource usage."""
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "duration_seconds": time.time() - self.start_time,
        }

    def log_usage(self, operation: str) -> None:
        """Log resource usage for operation."""
        usage = self.get_usage()
        logger.info("resource_usage", operation=operation, **usage, platform=detect_platform().value)


# Usage
tracker = ResourceTracker()
tracker.log_usage("startup")
# ... operations ...
tracker.log_usage("shutdown")
```

---

## 45. Advanced Configuration Scenarios

### 45.1 Environment-Specific Configuration

**Pattern:** Support different configurations for dev/staging/prod.

```python
"""Environment-specific configuration."""

from enum import Enum


class Environment(Enum):
    """Environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


def get_environment() -> Environment:
    """Detect current environment."""
    env_str = os.environ.get("THGENT_ENV", "development").lower()
    try:
        return Environment(env_str)
    except ValueError:
        return Environment.DEVELOPMENT


def load_environment_config() -> dict:
    """Load environment-specific configuration."""
    env = get_environment()
    config_dir = get_config_dir()

    # Load base config
    base_config = load_config()

    # Load environment-specific overrides
    env_config_file = config_dir / f"config.{env.value}.yaml"
    if env_config_file.exists():
        import yaml

        with open(env_config_file) as f:
            env_config = yaml.safe_load(f) or {}
        base_config.update(env_config)

    return base_config
```

### 45.2 Feature Flags

**Pattern:** Implement feature flags for gradual rollout.

```python
"""Feature flags system."""

from typing import Dict, Optional


class FeatureFlags:
    """Feature flags manager."""

    def __init__(self):
        self.flags: Dict[str, bool] = {}
        self._load_flags()

    def _load_flags(self) -> None:
        """Load feature flags from config."""
        config = load_config()
        self.flags = config.get("feature_flags", {})

        # Override with environment variables
        for key, value in os.environ.items():
            if key.startswith("THGENT_FEATURE_"):
                flag_name = key[15:].lower()
                self.flags[flag_name] = value.lower() in ("true", "1", "yes")

    def is_enabled(self, flag: str, default: bool = False) -> bool:
        """Check if feature flag is enabled."""
        return self.flags.get(flag, default)

    def enable(self, flag: str) -> None:
        """Enable feature flag."""
        self.flags[flag] = True
        self._save_flags()

    def disable(self, flag: str) -> None:
        """Disable feature flag."""
        self.flags[flag] = False
        self._save_flags()

    def _save_flags(self) -> None:
        """Save feature flags to config."""
        config = load_config()
        config["feature_flags"] = self.flags
        save_config(config)


# Usage
flags = FeatureFlags()

if flags.is_enabled("new_ui", default=False):
    use_new_ui()
else:
    use_old_ui()
```

---

## 61. Advanced Quality Assurance Patterns

### 61.1 Automated Quality Gates

**Pattern:** Implement automated quality gates with platform-specific thresholds.

```python
"""Automated quality gates."""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class QualityGate:
    """Quality gate definition."""

    name: str
    threshold: float
    current_value: float
    platform: str
    passed: bool


class QualityGateSystem:
    """Quality gate system."""

    def __init__(self):
        self.gates: List[QualityGate] = []
        self._register_gates()

    def _register_gates(self) -> None:
        """Register quality gates."""
        plat = detect_platform().value

        # Platform-specific thresholds
        thresholds = {
            "macos": {"coverage": 80.0, "performance": 100.0},
            "linux": {"coverage": 80.0, "performance": 100.0},
            "windows": {"coverage": 75.0, "performance": 150.0},  # More lenient
        }

        platform_thresholds = thresholds.get(plat, thresholds["linux"])

        self.gates.extend(
            [
                QualityGate(
                    name="test_coverage",
                    threshold=platform_thresholds["coverage"],
                    current_value=self._get_coverage(),
                    platform=plat,
                    passed=False,
                ),
                QualityGate(
                    name="startup_performance",
                    threshold=platform_thresholds["performance"],
                    current_value=self._get_startup_time(),
                    platform=plat,
                    passed=False,
                ),
            ]
        )

    def check_all_gates(self) -> tuple[bool, List[QualityGate]]:
        """Check all quality gates."""
        for gate in self.gates:
            gate.passed = gate.current_value <= gate.threshold

        all_passed = all(gate.passed for gate in self.gates)
        return all_passed, self.gates

    def _get_coverage(self) -> float:
        """Get test coverage percentage."""
        # Run coverage and parse
        result = subprocess.run(["pytest", "--cov=src", "--cov-report=term"], capture_output=True, text=True)
        # Parse coverage from output
        # ...
        return 85.0  # Placeholder

    def _get_startup_time(self) -> float:
        """Get startup time in milliseconds."""
        import time

        start = time.time()
        subprocess.run(["thegent", "--version"], capture_output=True)
        return (time.time() - start) * 1000


# Usage
quality_gates = QualityGateSystem()
all_passed, gates = quality_gates.check_all_gates()

if not all_passed:
    console.print("[red]Quality gates failed:[/red]")
    for gate in gates:
        if not gate.passed:
            console.print(f"  • {gate.name}: {gate.current_value:.1f} > {gate.threshold:.1f}")
```

### 61.2 Continuous Quality Monitoring

**Pattern:** Monitor quality metrics continuously.

```python
"""Continuous quality monitoring."""

from typing import Dict
import time


class QualityMonitor:
    """Monitor quality metrics."""

    def __init__(self):
        self.metrics_file = get_data_dir() / "quality" / "metrics.jsonl"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record quality metric."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric_name,
            "value": value,
            "tags": tags or {},
            "platform": detect_platform().value,
        }

        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_metric_trend(self, metric_name: str, days: int = 7) -> List[float]:
        """Get metric trend over time."""
        cutoff = datetime.now() - timedelta(days=days)
        values = []

        with open(self.metrics_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry["metric"] == metric_name:
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if entry_time >= cutoff:
                        values.append(entry["value"])

        return values

    def check_regression(self, metric_name: str, threshold: float) -> bool:
        """Check if metric has regressed."""
        trend = self.get_metric_trend(metric_name)
        if len(trend) < 2:
            return False

        recent_avg = sum(trend[-7:]) / len(trend[-7:])
        return recent_avg > threshold


# Usage
monitor = QualityMonitor()

# Record metrics
monitor.record_metric("startup_time_ms", 150.0)
monitor.record_metric("test_coverage", 85.0)

# Check for regressions
if monitor.check_regression("startup_time_ms", 200.0):
    console.print("[yellow]Warning: Startup time has regressed[/yellow]")
```

---

## 62. Advanced Integration Testing

### 62.1 End-to-End Test Scenarios

**Pattern:** Create comprehensive E2E test scenarios.

```python
"""End-to-end test scenarios."""

import pytest
from pathlib import Path


class E2ETestScenarios:
    """E2E test scenarios."""

    @pytest.mark.e2e
    @pytest.mark.parametrize("platform", ["macos", "linux", "windows"])
    def test_complete_installation_flow(self, platform, tmp_path):
        """Test complete installation flow."""
        with mock_platform(platform):
            # 1. Install
            result = run_thegent_command(["install", "--target", "all"])
            assert result.returncode == 0

            # 2. Verify installation
            result = run_thegent_command(["doctor"])
            assert result.returncode == 0

            # 3. Configure provider
            result = run_thegent_command(["cliproxy", "login", "anthropic"])
            assert result.returncode == 0

            # 4. Start MCP server
            result = run_thegent_command(["serve"], background=True)
            assert result.returncode == 0

            # 5. Run agent
            result = run_thegent_command(["run", "Hello, world!"])
            assert result.returncode == 0

    @pytest.mark.e2e
    def test_upgrade_flow(self, tmp_path):
        """Test upgrade flow."""
        # 1. Install old version
        install_version("0.1.0")

        # 2. Create config
        create_test_config()

        # 3. Upgrade
        upgrade_version("0.2.0")

        # 4. Verify config migrated
        assert config_migrated()

        # 5. Verify functionality
        result = run_thegent_command(["doctor"])
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_rollback_flow(self, tmp_path):
        """Test rollback flow."""
        # 1. Install version
        install_version("0.2.0")

        # 2. Create backup
        backup_path = backup_manager.create_backup()

        # 3. Make changes
        modify_config()

        # 4. Rollback
        backup_manager.restore_backup(backup_path)

        # 5. Verify rollback
        assert config_restored()
```

### 62.2 Chaos Engineering Tests

**Pattern:** Implement chaos engineering tests for resilience.

```python
"""Chaos engineering tests."""

import random
import time


class ChaosTests:
    """Chaos engineering tests."""

    def test_network_failure_recovery(self):
        """Test recovery from network failures."""
        # Simulate network failure
        with network_failure():
            # Attempt operation
            try:
                result = fetch_provider_config("anthropic")
                assert False, "Should have failed"
            except ConnectionError:
                pass

        # Verify recovery
        result = fetch_provider_config("anthropic")
        assert result is not None

    def test_disk_failure_recovery(self):
        """Test recovery from disk failures."""
        # Simulate disk full
        with disk_full():
            try:
                save_config(config)
                assert False, "Should have failed"
            except IOError:
                pass

        # Verify recovery
        save_config(config)
        assert config_saved()

    def test_process_crash_recovery(self):
        """Test recovery from process crashes."""
        # Start process
        process = start_mcp_server()

        # Crash process
        process.kill()

        # Verify auto-restart
        time.sleep(2)
        assert mcp_server_running()


@contextmanager
def network_failure():
    """Simulate network failure."""
    # Block network access
    # ...
    yield
    # Restore network


@contextmanager
def disk_full():
    """Simulate disk full."""
    # Fill disk
    # ...
    yield
    # Free disk
```

---

## 63. Advanced User Analytics

### 63.1 Usage Analytics

**Pattern:** Collect usage analytics (privacy-preserving).

```python
"""Usage analytics (privacy-preserving)."""

from typing import Dict
import hashlib


class UsageAnalytics:
    """Usage analytics collector."""

    def __init__(self):
        self.analytics_file = get_data_dir() / "analytics" / "usage.jsonl"
        self.analytics_file.parent.mkdir(parents=True, exist_ok=True)
        self.opt_out = self._check_opt_out()

    def _check_opt_out(self) -> bool:
        """Check if user opted out."""
        return os.environ.get("THGENT_ANALYTICS_OPT_OUT", "false").lower() == "true"

    def track_command(self, command: str, duration: float, success: bool) -> None:
        """Track command usage."""
        if self.opt_out:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "command_hash": self._hash_command(command),
            "duration_ms": duration * 1000,
            "success": success,
            "platform": detect_platform().value,
            "version": __version__,
        }

        # No PII, only aggregated data
        with open(self.analytics_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _hash_command(self, command: str) -> str:
        """Hash command (privacy-preserving)."""
        # Remove arguments, keep only command structure
        parts = command.split()
        if len(parts) > 0:
            base_command = parts[0]
        else:
            base_command = command

        return hashlib.sha256(base_command.encode()).hexdigest()[:8]

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get aggregated usage statistics."""
        stats = {
            "total_commands": 0,
            "success_rate": 0.0,
            "average_duration_ms": 0.0,
            "platform_distribution": {},
            "command_distribution": {},
        }

        if not self.analytics_file.exists():
            return stats

        commands = []
        successes = 0
        durations = []
        platforms = {}
        commands_count = {}

        with open(self.analytics_file) as f:
            for line in f:
                entry = json.loads(line)
                commands.append(entry)
                if entry["success"]:
                    successes += 1
                durations.append(entry["duration_ms"])
                platforms[entry["platform"]] = platforms.get(entry["platform"], 0) + 1
                commands_count[entry["command_hash"]] = commands_count.get(entry["command_hash"], 0) + 1

        if commands:
            stats["total_commands"] = len(commands)
            stats["success_rate"] = successes / len(commands)
            stats["average_duration_ms"] = sum(durations) / len(durations)
            stats["platform_distribution"] = platforms
            stats["command_distribution"] = commands_count

        return stats


# Usage
analytics = UsageAnalytics()

# Track command
start_time = time.time()
try:
    result = run_agent("codex", "Hello")
    analytics.track_command("thegent run", time.time() - start_time, True)
except Exception:
    analytics.track_command("thegent run", time.time() - start_time, False)
```

### 63.2 Performance Benchmarking

**Pattern:** Benchmark performance across platforms.

```python
"""Performance benchmarking."""

from typing import List, Dict
import statistics


class PerformanceBenchmark:
    """Performance benchmark system."""

    def __init__(self):
        self.benchmark_file = get_data_dir() / "benchmarks" / "performance.jsonl"
        self.benchmark_file.parent.mkdir(parents=True, exist_ok=True)

    def benchmark_operation(self, operation_name: str, operation: Callable, iterations: int = 10) -> Dict[str, float]:
        """Benchmark operation."""
        times = []

        for i in range(iterations):
            start = time.time()
            operation()
            duration = time.time() - start
            times.append(duration)

        stats = {
            "operation": operation_name,
            "iterations": iterations,
            "mean_ms": statistics.mean(times) * 1000,
            "median_ms": statistics.median(times) * 1000,
            "min_ms": min(times) * 1000,
            "max_ms": max(times) * 1000,
            "stdev_ms": statistics.stdev(times) * 1000 if len(times) > 1 else 0,
            "platform": detect_platform().value,
            "timestamp": datetime.now().isoformat(),
        }

        # Save benchmark
        with open(self.benchmark_file, "a") as f:
            f.write(json.dumps(stats) + "\n")

        return stats

    def compare_platforms(self, operation_name: str) -> Dict[str, Dict[str, float]]:
        """Compare performance across platforms."""
        platforms = {}

        with open(self.benchmark_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry["operation"] == operation_name:
                    platform = entry["platform"]
                    if platform not in platforms:
                        platforms[platform] = []
                    platforms[platform].append(entry["mean_ms"])

        # Calculate averages
        comparison = {}
        for platform, values in platforms.items():
            comparison[platform] = {
                "mean_ms": statistics.mean(values),
                "median_ms": statistics.median(values),
            }

        return comparison


# Usage
benchmark = PerformanceBenchmark()

# Benchmark path resolution
stats = benchmark.benchmark_operation("path_resolution", lambda: get_config_dir(), iterations=100)

console.print(f"Path resolution: {stats['mean_ms']:.2f}ms (median: {stats['median_ms']:.2f}ms)")
```

---

## 64. Advanced Documentation Automation

### 64.1 Auto-Generated Troubleshooting Guide

**Pattern:** Auto-generate troubleshooting guide from error patterns.

```python
"""Auto-generated troubleshooting guide."""

from pathlib import Path
from typing import Dict, List


class TroubleshootingGuideGenerator:
    """Generate troubleshooting guide from error patterns."""

    def __init__(self):
        self.error_patterns: Dict[str, Dict] = {}
        self._load_error_patterns()

    def _load_error_patterns(self) -> None:
        """Load error patterns from logs and code."""
        # Scan logs for common errors
        log_dir = get_log_dir()
        for log_file in log_dir.glob("*.log"):
            self._extract_errors_from_log(log_file)

        # Scan code for error definitions
        self._extract_errors_from_code()

    def _extract_errors_from_log(self, log_file: Path) -> None:
        """Extract error patterns from log file."""
        # Parse log file for error patterns
        # ...
        pass

    def _extract_errors_from_code(self) -> None:
        """Extract error definitions from code."""
        # Scan source code for exception definitions
        # ...
        pass

    def generate_guide(self) -> str:
        """Generate troubleshooting guide."""
        lines = ["# Troubleshooting Guide", ""]

        # Group by platform
        for platform in ["macos", "linux", "windows"]:
            lines.append(f"## {platform.title()}", "")

            platform_errors = [
                (error, info)
                for error, info in self.error_patterns.items()
                if info.get("platform") == platform or info.get("platform") == "all"
            ]

            for error, info in platform_errors:
                lines.append(f"### {error}", "")
                lines.append(f"**Symptom:** {info.get('symptom', 'Unknown')}", "")
                lines.append(f"**Solution:** {info.get('solution', 'See documentation')}", "")
                lines.append("")

        return "\n".join(lines)
```

### 64.2 Interactive API Explorer

**Pattern:** Create interactive API explorer for documentation.

```python
"""Interactive API explorer."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/api-explorer", response_class=HTMLResponse)
async def api_explorer():
    """Interactive API explorer."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>thegent API Explorer</title>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script>
            SwaggerUIBundle({
                url: "/openapi.json",
                dom_id: "#swagger-ui",
                presets: [SwaggerUIBundle.presets.apis],
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/openapi.json")
async def openapi_spec():
    """OpenAPI specification."""
    from fastapi.openapi.utils import get_openapi

    return get_openapi(
        title="thegent API",
        version=__version__,
        description="thegent API documentation",
        routes=app.routes,
    )
```

---

## 65. Advanced Deployment Automation

### 65.1 Blue-Green Deployment

**Pattern:** Implement blue-green deployment for zero-downtime updates.

```python
"""Blue-green deployment."""

from pathlib import Path
import shutil


class BlueGreenDeployment:
    """Blue-green deployment manager."""

    def __init__(self):
        self.install_dir = get_data_dir() / "installations"
        self.install_dir.mkdir(parents=True, exist_ok=True)
        self.current_version_file = self.install_dir / "current_version"

    def deploy_new_version(self, version: str, package_path: Path) -> bool:
        """Deploy new version (green)."""
        green_dir = self.install_dir / f"green-{version}"

        # Install to green directory
        self._install_to_directory(package_path, green_dir)

        # Verify green installation
        if not self._verify_installation(green_dir):
            shutil.rmtree(green_dir)
            return False

        # Switch to green (atomic)
        self._switch_to_green(version)

        # Cleanup old blue
        self._cleanup_blue()

        return True

    def _switch_to_green(self, version: str) -> None:
        """Switch to green version (atomic)."""
        # Update symlink or PATH
        green_dir = self.install_dir / f"green-{version}"
        bin_dir = get_bin_dir()

        # Create symlink to green
        thegent_symlink = bin_dir / "thegent"
        if thegent_symlink.exists():
            thegent_symlink.unlink()
        thegent_symlink.symlink_to(green_dir / "bin" / "thegent")

        # Update current version
        self.current_version_file.write_text(version)

    def _cleanup_blue(self) -> None:
        """Cleanup old blue installation."""
        current_version = self.current_version_file.read_text().strip()
        blue_dir = self.install_dir / f"blue-{current_version}"
        if blue_dir.exists():
            shutil.rmtree(blue_dir)

    def rollback(self) -> bool:
        """Rollback to previous version."""
        # Switch back to blue
        # ...
        return True
```

### 65.2 Canary Deployment

**Pattern:** Implement canary deployment for gradual rollout.

```python
"""Canary deployment."""

from typing import Dict
import random


class CanaryDeployment:
    """Canary deployment manager."""

    def __init__(self):
        self.canary_percentage = 0.0  # 0-100
        self.canary_version: Optional[str] = None
        self.stable_version: Optional[str] = None

    def set_canary_percentage(self, percentage: float) -> None:
        """Set canary deployment percentage."""
        self.canary_percentage = max(0.0, min(100.0, percentage))

    def deploy_canary(self, version: str) -> None:
        """Deploy canary version."""
        self.canary_version = version

    def should_use_canary(self, user_id: Optional[str] = None) -> bool:
        """Determine if user should use canary version."""
        if not self.canary_version:
            return False

        # Deterministic based on user_id or random
        if user_id:
            hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            user_percentage = (hash_value % 100) + 1
            return user_percentage <= self.canary_percentage
        else:
            return random.random() * 100 <= self.canary_percentage

    def get_version_for_user(self, user_id: Optional[str] = None) -> str:
        """Get version for user (canary or stable)."""
        if self.should_use_canary(user_id):
            return self.canary_version
        return self.stable_version or __version__
```

---

## 66. Advanced Monitoring Dashboards

### 66.1 Real-Time Metrics Dashboard

**Pattern:** Create real-time metrics dashboard with live updates.

```python
"""Real-time metrics dashboard."""

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.graph import Graph
import asyncio


class RealTimeDashboard:
    """Real-time metrics dashboard."""

    def __init__(self):
        self.metrics_history: Dict[str, List[float]] = {}
        self.update_interval = 1.0  # seconds

    def render(self) -> Layout:
        """Render dashboard."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="metrics"),
            Layout(name="graphs", size=15),
            Layout(name="footer", size=3),
        )

        # Header
        layout["header"].update(
            Panel(
                f"[bold cyan]thegent Real-Time Dashboard[/bold cyan] | "
                f"Platform: {detect_platform().value} | "
                f"Uptime: {self._get_uptime()}",
                border_style="cyan",
            )
        )

        # Metrics table
        metrics_table = self._build_metrics_table()
        layout["metrics"].update(Panel(metrics_table, title="Current Metrics"))

        # Graphs
        graphs = self._build_graphs()
        layout["graphs"].update(Panel(graphs, title="Metrics Over Time"))

        # Footer
        layout["footer"].update(Panel("[dim]Press Ctrl+C to exit[/dim]", border_style="dim"))

        return layout

    def _build_metrics_table(self) -> Table:
        """Build metrics table."""
        table = Table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Trend", style="yellow")

        # Get current metrics
        metrics = self._collect_metrics()

        for name, value in metrics.items():
            trend = self._get_trend(name)
            table.add_row(name, f"{value:.2f}", trend)

        return table

    def _build_graphs(self) -> str:
        """Build ASCII graphs."""
        graphs = []

        for metric_name, values in self.metrics_history.items():
            if len(values) > 1:
                graph = Graph()
                for i, value in enumerate(values[-20:]):  # Last 20 values
                    graph.add_series([value])
                graphs.append(f"{metric_name}:\n{graph}")

        return "\n\n".join(graphs) if graphs else "No data yet"

    def _collect_metrics(self) -> Dict[str, float]:
        """Collect current metrics."""
        return {
            "agent_runs": agent_runs_total._value.get(),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "average_duration_ms": self._calculate_average_duration(),
        }

    def _get_trend(self, metric_name: str) -> str:
        """Get trend indicator."""
        values = self.metrics_history.get(metric_name, [])
        if len(values) < 2:
            return "—"

        recent = values[-1]
        previous = values[-2]

        if recent > previous:
            return "↑"
        elif recent < previous:
            return "↓"
        else:
            return "→"

    def run(self) -> None:
        """Run dashboard."""
        with Live(self.render(), refresh_per_second=1) as live:
            while True:
                # Update metrics
                metrics = self._collect_metrics()
                for name, value in metrics.items():
                    if name not in self.metrics_history:
                        self.metrics_history[name] = []
                    self.metrics_history[name].append(value)
                    # Keep only last 100 values
                    if len(self.metrics_history[name]) > 100:
                        self.metrics_history[name] = self.metrics_history[name][-100:]

                live.update(self.render())
                time.sleep(self.update_interval)


# Usage
dashboard = RealTimeDashboard()
dashboard.run()
```

---

## 67. Advanced Error Prevention

### 67.1 Proactive Error Detection

**Pattern:** Detect potential errors before they occur.

```python
"""Proactive error detection."""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class PotentialIssue:
    """Potential issue."""

    severity: str
    category: str
    description: str
    remediation: str


class ProactiveErrorDetector:
    """Detect potential errors proactively."""

    def __init__(self):
        self.checks: List[Callable[[], List[PotentialIssue]]] = []
        self._register_checks()

    def _register_checks(self) -> None:
        """Register proactive checks."""
        self.checks.extend(
            [
                self._check_disk_space,
                self._check_memory_usage,
                self._check_network_connectivity,
                self._check_config_validity,
                self._check_dependency_versions,
            ]
        )

    def detect_issues(self) -> List[PotentialIssue]:
        """Detect potential issues."""
        all_issues = []
        for check in self.checks:
            try:
                issues = check()
                all_issues.extend(issues)
            except Exception as e:
                logger.warning(f"Proactive check failed: {e}")
        return all_issues

    def _check_disk_space(self) -> List[PotentialIssue]:
        """Check disk space."""
        issues = []
        cache_dir = get_cache_dir()
        stat = shutil.disk_usage(cache_dir)
        free_gb = stat.free / (1024**3)

        if free_gb < 1.0:
            issues.append(
                PotentialIssue(
                    severity="high",
                    category="disk_space",
                    description=f"Low disk space: {free_gb:.2f}GB free",
                    remediation="Free up disk space or run: thegent cache cleanup",
                )
            )

        return issues

    def _check_memory_usage(self) -> List[PotentialIssue]:
        """Check memory usage."""
        issues = []
        process = psutil.Process()
        memory_percent = process.memory_percent()

        if memory_percent > 80.0:
            issues.append(
                PotentialIssue(
                    severity="medium",
                    category="memory",
                    description=f"High memory usage: {memory_percent:.1f}%",
                    remediation="Restart thegent or check for memory leaks",
                )
            )

        return issues

    def _check_network_connectivity(self) -> List[PotentialIssue]:
        """Check network connectivity."""
        issues = []
        # Check if MCP server is reachable
        if not _mcp_running():
            issues.append(
                PotentialIssue(
                    severity="medium",
                    category="network",
                    description="MCP server not running",
                    remediation="Run: thegent serve",
                )
            )

        return issues

    def _check_config_validity(self) -> List[PotentialIssue]:
        """Check configuration validity."""
        issues = []
        config = load_config()

        # Check for deprecated settings
        if "api_keys" in config:
            issues.append(
                PotentialIssue(
                    severity="low",
                    category="config",
                    description="Deprecated 'api_keys' setting found",
                    remediation="Migrate to OAuth: thegent cliproxy login <provider>",
                )
            )

        return issues

    def _check_dependency_versions(self) -> List[PotentialIssue]:
        """Check dependency versions."""
        issues = []
        # Check for outdated dependencies
        # ...
        return issues


# Usage
detector = ProactiveErrorDetector()
issues = detector.detect_issues()

for issue in issues:
    if issue.severity == "high":
        console.print(f"[red]⚠ {issue.description}[/red]")
        console.print(f"[yellow]Fix: {issue.remediation}[/yellow]")
```

### 67.2 Predictive Failure Detection

**Pattern:** Predict failures before they occur.

```python
"""Predictive failure detection."""

from typing import Dict, List
import numpy as np
from sklearn.linear_model import LinearRegression


class PredictiveFailureDetector:
    """Predict failures based on patterns."""

    def __init__(self):
        self.metrics_history: Dict[str, List[float]] = {}
        self.failure_thresholds: Dict[str, float] = {
            "memory_usage": 90.0,
            "disk_usage": 95.0,
            "error_rate": 10.0,
        }

    def predict_failure(self, metric_name: str, hours_ahead: int = 1) -> tuple[bool, float]:
        """Predict if failure will occur."""
        values = self.metrics_history.get(metric_name, [])

        if len(values) < 10:
            return False, 0.0

        # Simple linear regression
        X = np.array(range(len(values))).reshape(-1, 1)
        y = np.array(values)

        model = LinearRegression()
        model.fit(X, y)

        # Predict future value
        future_x = len(values) + hours_ahead
        predicted_value = model.predict([[future_x]])[0]

        threshold = self.failure_thresholds.get(metric_name, 100.0)
        will_fail = predicted_value >= threshold

        return will_fail, predicted_value

    def add_metric_value(self, metric_name: str, value: float) -> None:
        """Add metric value to history."""
        if metric_name not in self.metrics_history:
            self.metrics_history[metric_name] = []
        self.metrics_history[metric_name].append(value)

        # Keep only last 1000 values
        if len(self.metrics_history[metric_name]) > 1000:
            self.metrics_history[metric_name] = self.metrics_history[metric_name][-1000:]

        # Check for predicted failure
        will_fail, predicted_value = self.predict_failure(metric_name)
        if will_fail:
            logger.warning(
                f"Predicted failure for {metric_name}: "
                f"predicted {predicted_value:.2f} >= threshold {self.failure_thresholds[metric_name]}"
            )


# Usage
predictor = PredictiveFailureDetector()

# Monitor metrics
while True:
    memory_usage = psutil.virtual_memory().percent
    predictor.add_metric_value("memory_usage", memory_usage)
    time.sleep(60)  # Check every minute
```

---

## 68. Advanced User Personalization

### 68.1 User Preference Learning

**Pattern:** Learn user preferences and adapt behavior.

```python
"""User preference learning."""

from typing import Dict, List
from collections import defaultdict


class UserPreferenceLearner:
    """Learn user preferences."""

    def __init__(self):
        self.preferences_file = get_data_dir() / "preferences" / "learned.json"
        self.preferences_file.parent.mkdir(parents=True, exist_ok=True)
        self.preferences: Dict[str, Any] = {}
        self.usage_patterns: Dict[str, List[str]] = defaultdict(list)
        self._load_preferences()

    def _load_preferences(self) -> None:
        """Load learned preferences."""
        if self.preferences_file.exists():
            with open(self.preferences_file) as f:
                self.preferences = json.load(f)

    def learn_from_usage(self, command: str, context: Dict[str, Any]) -> None:
        """Learn from user usage."""
        # Extract patterns
        agent = context.get("agent", "default")
        time_of_day = datetime.now().hour

        # Track usage patterns
        self.usage_patterns[agent].append(command)

        # Learn preferences
        if agent not in self.preferences:
            self.preferences[agent] = {
                "preferred_agents": [],
                "common_tasks": [],
                "time_preferences": {},
            }

        # Update preferences
        self._update_preferences(agent, command, time_of_day)
        self._save_preferences()

    def _update_preferences(self, agent: str, command: str, time_of_day: int) -> None:
        """Update preferences based on usage."""
        # Analyze patterns
        patterns = self.usage_patterns[agent]

        # Most common tasks
        from collections import Counter

        task_counter = Counter(patterns)
        common_tasks = [task for task, count in task_counter.most_common(5)]

        self.preferences[agent]["common_tasks"] = common_tasks

        # Time preferences
        time_key = "morning" if time_of_day < 12 else "afternoon" if time_of_day < 18 else "evening"
        self.preferences[agent]["time_preferences"][time_key] = (
            self.preferences[agent]["time_preferences"].get(time_key, 0) + 1
        )

    def get_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """Get personalized suggestions."""
        agent = context.get("agent", "default")
        time_of_day = datetime.now().hour

        suggestions = []

        # Suggest common tasks
        if agent in self.preferences:
            common_tasks = self.preferences[agent].get("common_tasks", [])
            suggestions.extend(common_tasks[:3])

        # Suggest based on time
        time_key = "morning" if time_of_day < 12 else "afternoon" if time_of_day < 18 else "evening"
        if agent in self.preferences:
            time_prefs = self.preferences[agent].get("time_preferences", {})
            if time_key in time_prefs and time_prefs[time_key] > 5:
                # User frequently uses this agent at this time
                suggestions.append(f"thegent run --agent {agent}")

        return suggestions

    def _save_preferences(self) -> None:
        """Save learned preferences."""
        with open(self.preferences_file, "w") as f:
            json.dump(self.preferences, f, indent=2)


# Usage
learner = UserPreferenceLearner()

# Learn from usage
learner.learn_from_usage("thegent run 'Fix bug'", {"agent": "codex"})

# Get suggestions
suggestions = learner.get_suggestions({"agent": "codex"})
console.print("[cyan]Suggestions:[/cyan]")
for suggestion in suggestions:
    console.print(f"  • {suggestion}")
```

### 68.2 Adaptive UI/UX

**Pattern:** Adapt UI/UX based on user expertise level.

```python
"""Adaptive UI/UX."""

from enum import Enum
from typing import Dict


class UserExpertise(Enum):
    """User expertise levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AdaptiveUX:
    """Adaptive user experience."""

    def __init__(self):
        self.expertise_file = get_data_dir() / "ux" / "expertise.json"
        self.expertise_file.parent.mkdir(parents=True, exist_ok=True)
        self.expertise_levels: Dict[str, UserExpertise] = {}
        self._load_expertise()

    def _load_expertise(self) -> None:
        """Load user expertise levels."""
        if self.expertise_file.exists():
            with open(self.expertise_file) as f:
                data = json.load(f)
                self.expertise_levels = {k: UserExpertise(v) for k, v in data.items()}

    def detect_expertise(self, command: str) -> UserExpertise:
        """Detect user expertise from command."""
        # Analyze command complexity
        complexity_score = self._calculate_complexity(command)

        if complexity_score < 2:
            return UserExpertise.BEGINNER
        elif complexity_score < 5:
            return UserExpertise.INTERMEDIATE
        elif complexity_score < 8:
            return UserExpertise.ADVANCED
        else:
            return UserExpertise.EXPERT

    def _calculate_complexity(self, command: str) -> int:
        """Calculate command complexity."""
        score = 0

        # Count flags
        score += command.count("--")

        # Count pipes/chains
        score += command.count("|")
        score += command.count("&&")
        score += command.count(";")

        # Count nested structures
        score += command.count("(")
        score += command.count("[")

        return score

    def adapt_output(self, command: str, output: str) -> str:
        """Adapt output based on expertise."""
        expertise = self.detect_expertise(command)

        if expertise == UserExpertise.BEGINNER:
            # Add explanations
            return self._add_explanations(output)
        elif expertise == UserExpertise.INTERMEDIATE:
            # Show standard output
            return output
        elif expertise in (UserExpertise.ADVANCED, UserExpertise.EXPERT):
            # Show concise output
            return self._make_concise(output)

        return output

    def _add_explanations(self, output: str) -> str:
        """Add explanations for beginners."""
        # Add helpful context
        return f"{output}\n\n[dim]Tip: Run 'thegent help' for more information[/dim]"

    def _make_concise(self, output: str) -> str:
        """Make output more concise for experts."""
        # Remove verbose messages
        lines = output.splitlines()
        concise_lines = [line for line in lines if not line.startswith("[dim]")]
        return "\n".join(concise_lines)


# Usage
adaptive_ux = AdaptiveUX()

# Adapt output
command = "thegent run 'Hello'"
output = run_command(command)
adapted_output = adaptive_ux.adapt_output(command, output)
console.print(adapted_output)
```

---

## 69. Advanced Resource Management

### 69.1 Resource Pool Management

**Pattern:** Manage resource pools for efficient resource usage.

```python
"""Resource pool management."""

from typing import TypeVar, Generic
from queue import Queue
import threading

T = TypeVar("T")


class ResourcePool(Generic[T]):
    """Generic resource pool."""

    def __init__(self, factory: Callable[[], T], max_size: int = 10):
        self.factory = factory
        self.max_size = max_size
        self.pool: Queue[T] = Queue(maxsize=max_size)
        self.lock = threading.Lock()
        self.created_count = 0

    def acquire(self) -> T:
        """Acquire resource from pool."""
        try:
            return self.pool.get_nowait()
        except queue.Empty:
            # Create new resource
            with self.lock:
                if self.created_count < self.max_size:
                    resource = self.factory()
                    self.created_count += 1
                    return resource
                else:
                    # Wait for resource to be released
                    return self.pool.get()

    def release(self, resource: T) -> None:
        """Release resource back to pool."""
        self.pool.put(resource)

    def __enter__(self):
        """Context manager entry."""
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release(self)


# Usage
http_client_pool = ResourcePool(factory=lambda: httpx.AsyncClient(), max_size=10)


async def make_request(url: str):
    """Make HTTP request using pool."""
    async with http_client_pool as client:
        return await client.get(url)
```

### 69.2 Resource Cleanup Automation

**Pattern:** Automatically cleanup resources.

```python
"""Resource cleanup automation."""

import atexit
from typing import List, Callable


class ResourceCleanup:
    """Resource cleanup manager."""

    def __init__(self):
        self.cleanup_handlers: List[Callable[[], None]] = []
        atexit.register(self.cleanup_all)

    def register_cleanup(self, handler: Callable[[], None]) -> None:
        """Register cleanup handler."""
        self.cleanup_handlers.append(handler)

    def cleanup_all(self) -> None:
        """Run all cleanup handlers."""
        for handler in reversed(self.cleanup_handlers):
            try:
                handler()
            except Exception as e:
                logger.error(f"Cleanup handler failed: {e}")

    def cleanup_temp_files(self) -> None:
        """Cleanup temporary files."""
        temp_dir = get_temp_dir()
        if temp_dir.exists():
            for file in temp_dir.glob("*"):
                try:
                    if file.is_file():
                        # Check age
                        age = time.time() - file.stat().st_mtime
                        if age > 3600:  # 1 hour
                            file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to cleanup {file}: {e}")

    def cleanup_old_sessions(self) -> None:
        """Cleanup old sessions."""
        sessions_dir = get_data_dir() / "sessions"
        if not sessions_dir.exists():
            return

        cutoff = datetime.now() - timedelta(days=7)

        for session_dir in sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue

            state_file = session_dir / "state.json"
            if state_file.exists():
                mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
                if mtime < cutoff:
                    shutil.rmtree(session_dir)


# Usage
cleanup = ResourceCleanup()
cleanup.register_cleanup(cleanup.cleanup_temp_files)
cleanup.register_cleanup(cleanup.cleanup_old_sessions)
```

---

## 70. Advanced Documentation Features

### 70.1 Video Tutorial Integration

**Pattern:** Integrate video tutorials into documentation.

```markdown
# Installation Guide

## Video Tutorial

<iframe width="560" height="315" src="https://www.youtube.com/embed/VIDEO_ID" frameborder="0" allowfullscreen></iframe>

## Step-by-Step Instructions

### macOS

1. Install via Homebrew:
   ```bash
   brew install thegent
   ```

2. Run post-installation setup:
   ```bash
   thegent install --target all
   ```

[Continue with text instructions...]
```

### 70.2 Interactive Code Playground

**Pattern:** Create interactive code playground in documentation.

```python
"""Interactive code playground."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/playground", response_class=HTMLResponse)
async def code_playground():
    """Interactive code playground."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>thegent Code Playground</title>
        <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
    </head>
    <body>
        <h1>thegent Code Playground</h1>
        <textarea id="code" rows="10" cols="80">
from thegent.platform import detect_platform
print(f"Platform: {detect_platform().value}")
        </textarea>
        <br>
        <button onclick="runCode()">Run</button>
        <pre id="output"></pre>

        <script>
            let pyodide;
            async function main() {
                pyodide = await loadPyodide();
                await pyodide.loadPackage("micropip");
                await pyodide.runPythonAsync(`
                    import micropip
                    await micropip.install("thegent")
                `);
            }
            main();

            function runCode() {
                const code = document.getElementById("code").value;
                try {
                    pyodide.runPython(code);
                    document.getElementById("output").textContent = "Code executed successfully!";
                } catch (e) {
                    document.getElementById("output").textContent = e.toString();
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
```

---

## Conclusion

This comprehensive cross-platform audit and plan provides a complete roadmap for production-ready packaging across Windows, macOS, and Linux. The 12-phase implementation plan covers all aspects from platform detection to final release, with platform-specific considerations throughout.

**Key Priorities:**
1. **Platform Detection & Paths** (Phase 1-2) — Foundation for everything
2. **Packaging** (Phase 4-5) — Enable distribution on all platforms
3. **Error Handling** (Phase 6) — Critical for user experience
4. **Documentation** (Phase 8) — Platform-specific guides essential

**Expected Outcome:**
A production-ready, shipping-quality cross-platform package that can be installed via standard package managers on Windows, macOS, and Linux with a polished, intuitive user experience and comprehensive platform-specific documentation.

**Timeline:** 5 weeks, 104-142 hours total effort

**Risk:** Medium (manageable with phased approach, platform-specific testing, and fallbacks)

---

## 71. Advanced System Integration Patterns

### 71.1 Integration with Existing Devkit Systems

**Pattern:** Integrate with external "manage" devkit systems.

```python
"""Integration with manage devkit system."""

from pathlib import Path
import json
from typing import Optional, Dict


class ManageDevkitIntegration:
    """Integrate with manage devkit system."""

    def __init__(self):
        self.manage_config_path = self._find_manage_config()
        self.manage_config: Dict = {}
        self._load_manage_config()

    def _find_manage_config(self) -> Optional[Path]:
        """Find manage devkit configuration."""
        # Common locations
        possible_paths = [
            Path.home() / ".manage" / "config.yaml",
            Path.home() / ".config" / "manage" / "config.yaml",
            Path("/etc/manage/config.yaml"),
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _load_manage_config(self) -> None:
        """Load manage devkit configuration."""
        if not self.manage_config_path:
            return

        import yaml

        with open(self.manage_config_path) as f:
            self.manage_config = yaml.safe_load(f) or {}

    def integrate_paths(self) -> None:
        """Integrate thegent paths with manage devkit."""
        if "paths" not in self.manage_config:
            self.manage_config["paths"] = {}

        # Share config directory if manage uses similar structure
        if "config_dir" in self.manage_config.get("paths", {}):
            manage_config_dir = Path(self.manage_config["paths"]["config_dir"])
            thegent_config_dir = get_config_dir()

            # Create symlink or merge
            if manage_config_dir.exists():
                # Create shared config structure
                shared_config = manage_config_dir / "thegent"
                shared_config.mkdir(exist_ok=True)

                # Symlink thegent config
                if not (shared_config / "config.yaml").exists():
                    (shared_config / "config.yaml").symlink_to(thegent_config_dir / "config.yaml")

    def integrate_tools(self) -> None:
        """Integrate thegent tools with manage devkit."""
        manage_bin_dir = Path(self.manage_config.get("bin_dir", "~/.manage/bin"))
        manage_bin_dir = manage_bin_dir.expanduser()
        manage_bin_dir.mkdir(parents=True, exist_ok=True)

        # Create thegent symlink in manage bin
        thegent_bin = get_bin_dir() / "thegent"
        manage_thegent = manage_bin_dir / "thegent"

        if thegent_bin.exists() and not manage_thegent.exists():
            manage_thegent.symlink_to(thegent_bin)

    def register_with_manage(self) -> None:
        """Register thegent with manage devkit."""
        if "tools" not in self.manage_config:
            self.manage_config["tools"] = []

        thegent_entry = {
            "name": "thegent",
            "version": __version__,
            "bin_path": str(get_bin_dir() / "thegent"),
            "config_path": str(get_config_dir()),
            "platform": detect_platform().value,
        }

        # Check if already registered
        existing = [t for t in self.manage_config["tools"] if t.get("name") == "thegent"]

        if not existing:
            self.manage_config["tools"].append(thegent_entry)
            self._save_manage_config()

    def _save_manage_config(self) -> None:
        """Save manage devkit configuration."""
        if not self.manage_config_path:
            return

        import yaml

        with open(self.manage_config_path, "w") as f:
            yaml.dump(self.manage_config, f, default_flow_style=False)


# Usage
manage_integration = ManageDevkitIntegration()
manage_integration.integrate_paths()
manage_integration.integrate_tools()
manage_integration.register_with_manage()
```

### 71.2 Integration with WORK_STREAM System

**Pattern:** Integrate with unified work stream system.

```python
"""Integration with WORK_STREAM system."""

from pathlib import Path
import json
from typing import List, Dict
from datetime import datetime


class WorkStreamIntegration:
    """Integrate with WORK_STREAM.md system."""

    def __init__(self):
        self.work_stream_file = Path("docs/reference/WORK_STREAM.md")
        self.work_stream_data: Dict = {}
        self._load_work_stream()

    def _load_work_stream(self) -> None:
        """Load work stream data."""
        if not self.work_stream_file.exists():
            return

        # Parse WORK_STREAM.md
        content = self.work_stream_file.read_text()

        # Extract sections
        self.work_stream_data = {
            "pending": self._extract_section(content, "PENDING"),
            "claimed": self._extract_section(content, "CLAIMED"),
            "completed": self._extract_section(content, "COMPLETED"),
        }

    def _extract_section(self, content: str, section: str) -> List[Dict]:
        """Extract section from WORK_STREAM.md."""
        # Parse markdown table
        # ...
        return []

    def claim_work_item(self, item_id: str, agent_id: str) -> bool:
        """Claim work item from work stream."""
        # Move from PENDING to CLAIMED
        # ...
        return True

    def complete_work_item(self, item_id: str, agent_id: str) -> bool:
        """Complete work item."""
        # Move from CLAIMED to COMPLETED
        # ...
        return True

    def get_next_item(self) -> Optional[Dict]:
        """Get next actionable item from work stream."""
        pending = self.work_stream_data.get("pending", [])
        claimed = self.work_stream_data.get("claimed", [])

        # Filter out claimed items
        available = [item for item in pending if item["id"] not in [c["id"] for c in claimed]]

        if available:
            # Return highest priority
            return sorted(available, key=lambda x: x.get("priority", 0), reverse=True)[0]

        return None
```

### 71.3 Integration with Plan System

**Pattern:** Integrate with PLAN.md and plan status tracking.

```python
"""Integration with plan system."""

from pathlib import Path
import yaml
from typing import List, Dict


class PlanSystemIntegration:
    """Integrate with PLAN.md and plan status."""

    def __init__(self):
        self.plan_file = Path("PLAN.md")
        self.plan_status_file = Path("docs/reference/PLAN_STATUS.md")
        self.plan_data: Dict = {}
        self.plan_status: Dict = {}
        self._load_plan()
        self._load_plan_status()

    def _load_plan(self) -> None:
        """Load PLAN.md."""
        if not self.plan_file.exists():
            return

        content = self.plan_file.read_text()
        # Parse plan structure
        # Extract phases, tasks, dependencies
        # ...

    def _load_plan_status(self) -> None:
        """Load plan status."""
        if not self.plan_status_file.exists():
            return

        content = self.plan_status_file.read_text()
        # Parse status table
        # ...

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status in plan."""
        # Update PLAN_STATUS.md
        # ...
        pass

    def get_tasks_for_phase(self, phase: str) -> List[Dict]:
        """Get tasks for specific phase."""
        # Filter tasks by phase
        # ...
        return []

    def get_blocked_tasks(self) -> List[Dict]:
        """Get tasks blocked by incomplete dependencies."""
        # Find tasks with incomplete dependencies
        # ...
        return []
```

---

## 72. Advanced Cross-System Harmonization

### 72.1 Unified Configuration System

**Pattern:** Harmonize configuration across all systems.

```python
"""Unified configuration system."""

from pathlib import Path
import yaml
from typing import Dict, Any


class UnifiedConfigManager:
    """Unified configuration across systems."""

    def __init__(self):
        self.config_sources = [
            ("thegent", get_config_dir() / "config.yaml"),
            ("manage", Path.home() / ".manage" / "config.yaml"),
            ("workstream", Path("docs/reference/WORK_STREAM.md")),
            ("plan", Path("PLAN.md")),
        ]
        self.unified_config: Dict[str, Any] = {}
        self._load_unified_config()

    def _load_unified_config(self) -> None:
        """Load configuration from all sources."""
        for system_name, config_path in self.config_sources:
            if config_path.exists():
                if config_path.suffix == ".yaml":
                    with open(config_path) as f:
                        config = yaml.safe_load(f) or {}
                elif config_path.suffix == ".md":
                    config = self._parse_markdown_config(config_path)
                else:
                    continue

                self.unified_config[system_name] = config

    def _parse_markdown_config(self, path: Path) -> Dict:
        """Parse configuration from markdown."""
        # Extract configuration from markdown tables
        # ...
        return {}

    def get_unified_setting(self, key: str, system: Optional[str] = None) -> Any:
        """Get setting from unified config."""
        if system:
            return self.unified_config.get(system, {}).get(key)

        # Check all systems (priority order)
        for system_name in ["thegent", "manage", "workstream", "plan"]:
            if system_name in self.unified_config:
                value = self.unified_config[system_name].get(key)
                if value is not None:
                    return value

        return None

    def sync_configs(self) -> None:
        """Synchronize configurations across systems."""
        # Ensure consistency
        # ...
        pass
```

### 72.2 Harmonized Path Strategy

**Pattern:** Harmonize paths across all integrated systems.

```python
"""Harmonized path strategy."""

from typing import Dict
from pathlib import Path


class HarmonizedPathManager:
    """Harmonize paths across systems."""

    def __init__(self):
        self.path_mappings: Dict[str, Dict[str, Path]] = {}
        self._build_path_mappings()

    def _build_path_mappings(self) -> None:
        """Build path mappings for all systems."""
        plat = detect_platform()

        # Base directories
        if plat == Platform.MACOS:
            base_config = Path.home() / "Library" / "Application Support"
            base_cache = Path.home() / "Library" / "Caches"
            base_data = Path.home() / "Library" / "Application Support"
        elif plat == Platform.LINUX:
            base_config = Path.home() / ".config"
            base_cache = Path.home() / ".cache"
            base_data = Path.home() / ".local" / "share"
        else:  # Windows
            base_config = Path(os.environ.get("APPDATA", ""))
            base_cache = Path(os.environ.get("LOCALAPPDATA", "")) / "cache"
            base_data = Path(os.environ.get("LOCALAPPDATA", ""))

        # Harmonized paths
        self.path_mappings = {
            "thegent": {
                "config": base_config / "thegent",
                "cache": base_cache / "thegent",
                "data": base_data / "thegent",
            },
            "manage": {
                "config": base_config / "manage",
                "cache": base_cache / "manage",
                "data": base_data / "manage",
            },
            "workstream": {
                "config": base_config / "workstream",
                "cache": base_cache / "workstream",
                "data": base_data / "workstream",
            },
        }

    def get_harmonized_path(self, system: str, path_type: str) -> Path:
        """Get harmonized path for system."""
        return self.path_mappings.get(system, {}).get(path_type)

    def create_shared_structure(self) -> None:
        """Create shared directory structure."""
        # Create common parent directories
        # ...
        pass
```

---

## 73. Advanced Holistic Design Patterns

### 73.1 System-Wide Consistency

**Pattern:** Ensure consistency across all system components.

```python
"""System-wide consistency."""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ConsistencyRule:
    """Consistency rule definition."""

    component: str
    property: str
    expected_value: Any
    actual_value: Any
    severity: str


class ConsistencyChecker:
    """Check consistency across system."""

    def __init__(self):
        self.rules: List[ConsistencyRule] = []
        self._register_rules()

    def _register_rules(self) -> None:
        """Register consistency rules."""
        # Version consistency
        self.rules.append(
            ConsistencyRule(
                component="package",
                property="version",
                expected_value=__version__,
                actual_value=self._get_package_version(),
                severity="critical",
            )
        )

        # Path consistency
        self.rules.append(
            ConsistencyRule(
                component="paths",
                property="platform",
                expected_value=detect_platform().value,
                actual_value=self._get_path_platform(),
                severity="high",
            )
        )

        # Config consistency
        self.rules.append(
            ConsistencyRule(
                component="config",
                property="providers",
                expected_value="oauth_only",
                actual_value=self._get_provider_auth_method(),
                severity="high",
            )
        )

    def check_all(self) -> List[ConsistencyRule]:
        """Check all consistency rules."""
        violations = []
        for rule in self.rules:
            if rule.expected_value != rule.actual_value:
                violations.append(rule)
        return violations

    def _get_package_version(self) -> str:
        """Get package version."""
        return __version__

    def _get_path_platform(self) -> str:
        """Get platform from paths."""
        # Check if paths match detected platform
        return detect_platform().value

    def _get_provider_auth_method(self) -> str:
        """Get provider authentication method."""
        config = load_config()
        providers = config.get("providers", {})

        # Check if any provider uses API keys (should be OAuth only)
        for provider, provider_config in providers.items():
            if "api_key" in provider_config:
                return "api_key"

        return "oauth_only"


# Usage
consistency = ConsistencyChecker()
violations = consistency.check_all()

if violations:
    console.print("[yellow]Consistency violations detected:[/yellow]")
    for violation in violations:
        console.print(
            f"  • {violation.component}.{violation.property}: "
            f"expected {violation.expected_value}, got {violation.actual_value}"
        )
```

### 73.2 Harmonious API Design

**Pattern:** Design harmonious APIs across all components.

```python
"""Harmonious API design."""

from typing import Protocol, TypeVar
from abc import ABC, abstractmethod

T = TypeVar("T")


class HarmoniousAPI(Protocol):
    """Protocol for harmonious API design."""

    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def delete(self, key: str) -> None: ...
    def list(self) -> List[str]: ...


class ConfigAPI(HarmoniousAPI):
    """Config API following harmonious design."""

    def get(self, key: str) -> Any:
        """Get config value."""
        return config_manager.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set config value."""
        config_manager.set(key, value)

    def delete(self, key: str) -> None:
        """Delete config value."""
        config_manager.delete(key)

    def list(self) -> List[str]:
        """List config keys."""
        return config_manager.list_keys()


class StateAPI(HarmoniousAPI):
    """State API following harmonious design."""

    def get(self, key: str) -> Any:
        """Get state value."""
        return state_manager.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set state value."""
        state_manager.set(key, value)

    def delete(self, key: str) -> None:
        """Delete state value."""
        state_manager.delete(key)

    def list(self) -> List[str]:
        """List state keys."""
        return state_manager.list_keys()


# All APIs follow same pattern - harmonious design
```

---

## 74. Advanced Integration Testing Scenarios

### 74.1 Cross-System Integration Tests

**Pattern:** Test integration between thegent and other systems.

```python
"""Cross-system integration tests."""

import pytest
from pathlib import Path


class CrossSystemIntegrationTests:
    """Test integration with other systems."""

    @pytest.mark.integration
    def test_manage_devkit_integration(self, tmp_path):
        """Test integration with manage devkit."""
        # Setup manage devkit
        manage_config = tmp_path / ".manage" / "config.yaml"
        manage_config.parent.mkdir(parents=True)
        manage_config.write_text("""
paths:
  config_dir: ~/.manage/config
tools: []
""")

        # Integrate thegent
        integration = ManageDevkitIntegration()
        integration.integrate_paths()
        integration.integrate_tools()
        integration.register_with_manage()

        # Verify integration
        assert (tmp_path / ".manage" / "bin" / "thegent").exists()
        assert "thegent" in [t["name"] for t in integration.manage_config.get("tools", [])]

    @pytest.mark.integration
    def test_work_stream_integration(self, tmp_path):
        """Test integration with work stream."""
        # Create work stream
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text("""
## PENDING

| ID | Description | Priority |
|----|-------------|----------|
| WS-001 | Test task | High |
""")

        # Integrate
        integration = WorkStreamIntegration()
        next_item = integration.get_next_item()

        assert next_item is not None
        assert next_item["id"] == "WS-001"

    @pytest.mark.integration
    def test_plan_system_integration(self, tmp_path):
        """Test integration with plan system."""
        # Create plan
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text("""
## Phase 1: Foundation

- [ ] Task 1.1: Setup platform detection
- [ ] Task 1.2: Implement path resolution
""")

        # Integrate
        integration = PlanSystemIntegration()
        tasks = integration.get_tasks_for_phase("Phase 1")

        assert len(tasks) > 0
```

### 74.2 End-to-End System Tests

**Pattern:** Test entire system end-to-end.

```python
"""End-to-end system tests."""

import pytest
from pathlib import Path


@pytest.mark.e2e
def test_complete_system_workflow():
    """Test complete system workflow."""
    # 1. Install thegent
    install_thegent()

    # 2. Integrate with manage devkit
    manage_integration = ManageDevkitIntegration()
    manage_integration.integrate_paths()

    # 3. Integrate with work stream
    work_stream_integration = WorkStreamIntegration()
    work_item = work_stream_integration.get_next_item()

    # 4. Claim work item
    work_stream_integration.claim_work_item(work_item["id"], "test-agent")

    # 5. Execute work
    result = execute_work(work_item)

    # 6. Complete work item
    work_stream_integration.complete_work_item(work_item["id"], "test-agent")

    # 7. Update plan status
    plan_integration = PlanSystemIntegration()
    plan_integration.update_task_status(work_item["task_id"], "completed")

    # Verify everything is consistent
    assert work_item_completed(work_item["id"])
    assert plan_updated(work_item["task_id"])
    assert config_synced()
```

---

## 75. Advanced Documentation Integration

### 75.1 Cross-Reference System

**Pattern:** Create cross-reference system between all documentation.

```python
"""Cross-reference system."""

from pathlib import Path
import re
from typing import Dict, List


class DocumentationCrossReference:
    """Cross-reference system for documentation."""

    def __init__(self):
        self.references: Dict[str, List[str]] = {}
        self._build_reference_index()

    def _build_reference_index(self) -> None:
        """Build cross-reference index."""
        docs_dir = Path("docs")

        for doc_file in docs_dir.rglob("*.md"):
            content = doc_file.read_text()
            relative_path = doc_file.relative_to(docs_dir)

            # Extract references
            references = self._extract_references(content)
            self.references[str(relative_path)] = references

    def _extract_references(self, content: str) -> List[str]:
        """Extract references from content."""
        references = []

        # Markdown links
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        for match in re.finditer(link_pattern, content):
            references.append(match.group(2))

        # Explicit references
        ref_pattern = r"See:\s*([^\s]+)"
        for match in re.finditer(ref_pattern, content):
            references.append(match.group(1))

        return references

    def get_referrers(self, doc_path: str) -> List[str]:
        """Get documents that reference this document."""
        referrers = []
        for doc, refs in self.references.items():
            if doc_path in refs or doc_path in [r.split("#")[0] for r in refs]:
                referrers.append(doc)
        return referrers

    def validate_references(self) -> List[str]:
        """Validate all references."""
        broken_refs = []

        for doc, refs in self.references.items():
            for ref in refs:
                # Resolve reference
                ref_path = self._resolve_reference(ref)
                if not ref_path.exists():
                    broken_refs.append(f"{doc} -> {ref}")

        return broken_refs

    def _resolve_reference(self, ref: str) -> Path:
        """Resolve reference to file path."""
        # Handle different reference formats
        # ...
        return Path("docs") / ref


# Usage
cross_ref = DocumentationCrossReference()

# Get referrers
referrers = cross_ref.get_referrers("PRODUCTION_PACKAGING_POLISH_OPTIMIZATION_AUDIT_AND_PLAN.md")

# Validate references
broken = cross_ref.validate_references()
if broken:
    console.print("[yellow]Broken references:[/yellow]")
    for ref in broken:
        console.print(f"  • {ref}")
```

### 75.2 Documentation Generation Pipeline

**Pattern:** Automated documentation generation pipeline.

```python
"""Documentation generation pipeline."""

from pathlib import Path
import subprocess


class DocumentationPipeline:
    """Documentation generation pipeline."""

    def __init__(self):
        self.docs_dir = Path("docs")
        self.dist_dir = Path("docs-dist")

    def generate_all(self) -> None:
        """Generate all documentation."""
        # 1. Generate API docs
        self.generate_api_docs()

        # 2. Generate platform-specific guides
        self.generate_platform_guides()

        # 3. Generate troubleshooting guides
        self.generate_troubleshooting_guides()

        # 4. Build VitePress site
        self.build_vitepress_site()

        # 5. Validate documentation
        self.validate_documentation()

    def generate_api_docs(self) -> None:
        """Generate API documentation."""
        subprocess.run(["sphinx-build", "-b", "html", "docs/api", "docs-dist/api"], check=True)

    def generate_platform_guides(self) -> None:
        """Generate platform-specific guides."""
        for platform in ["macos", "linux", "windows"]:
            guide_content = self._generate_platform_guide(platform)
            guide_file = self.docs_dir / "user-guide" / "installation" / f"{platform}.md"
            guide_file.write_text(guide_content)

    def generate_troubleshooting_guides(self) -> None:
        """Generate troubleshooting guides."""
        generator = TroubleshootingGuideGenerator()
        guide_content = generator.generate_guide()
        guide_file = self.docs_dir / "user-guide" / "troubleshooting" / "index.md"
        guide_file.write_text(guide_content)

    def build_vitepress_site(self) -> None:
        """Build VitePress documentation site."""
        subprocess.run(["pnpm", "docs:build"], check=True)

    def validate_documentation(self) -> None:
        """Validate documentation."""
        # Check for broken links
        cross_ref = DocumentationCrossReference()
        broken = cross_ref.validate_references()

        if broken:
            raise ValueError(f"Broken references found: {broken}")


# Usage
pipeline = DocumentationPipeline()
pipeline.generate_all()
```

---

## 76. Advanced Harmonious Design Principles

### 76.1 Design Language System

**Pattern:** Establish consistent design language across all components.

```python
"""Design language system."""

from typing import Dict
from dataclasses import dataclass


@dataclass
class DesignToken:
    """Design token definition."""

    name: str
    value: Any
    category: str
    platform: Optional[str] = None


class DesignLanguage:
    """Design language system."""

    def __init__(self):
        self.tokens: Dict[str, DesignToken] = {}
        self._register_tokens()

    def _register_tokens(self) -> None:
        """Register design tokens."""
        # Colors
        self.tokens["color.primary"] = DesignToken(name="color.primary", value="#4CAF50", category="color")
        self.tokens["color.error"] = DesignToken(name="color.error", value="#F44336", category="color")
        self.tokens["color.warning"] = DesignToken(name="color.warning", value="#FF9800", category="color")

        # Spacing
        self.tokens["spacing.unit"] = DesignToken(name="spacing.unit", value=4, category="spacing")

        # Typography
        self.tokens["font.mono"] = DesignToken(
            name="font.mono", value="'Courier New', monospace", category="typography"
        )

        # Platform-specific tokens
        plat = detect_platform()
        if plat == Platform.MACOS:
            self.tokens["font.system"] = DesignToken(
                name="font.system", value="SF Pro", category="typography", platform="macos"
            )
        elif plat == Platform.WINDOWS:
            self.tokens["font.system"] = DesignToken(
                name="font.system", value="Segoe UI", category="typography", platform="windows"
            )
        else:  # Linux
            self.tokens["font.system"] = DesignToken(
                name="font.system", value="Ubuntu", category="typography", platform="linux"
            )

    def get_token(self, name: str, platform: Optional[str] = None) -> Any:
        """Get design token value."""
        token = self.tokens.get(name)
        if not token:
            return None

        # Platform-specific override
        if platform and token.platform and token.platform != platform:
            # Look for platform-specific version
            platform_token_name = f"{name}.{platform}"
            platform_token = self.tokens.get(platform_token_name)
            if platform_token:
                return platform_token.value

        return token.value

    def apply_to_cli(self) -> None:
        """Apply design language to CLI."""
        # Configure Rich console with design tokens
        from rich.console import Console

        console = Console(
            style=self.get_token("color.primary"),
            # Apply other design tokens
        )


# Usage
design_language = DesignLanguage()

# Use tokens
primary_color = design_language.get_token("color.primary")
error_color = design_language.get_token("color.error")
system_font = design_language.get_token("font.system", platform=detect_platform().value)
```

### 76.2 Consistent Naming Conventions

**Pattern:** Enforce consistent naming across all systems.

```python
"""Consistent naming conventions."""

import re
from typing import List


class NamingConvention:
    """Naming convention enforcer."""

    def __init__(self):
        self.conventions = {
            "command": r"^[a-z][a-z0-9-]*$",  # kebab-case
            "config_key": r"^[a-z][a-z0-9_]*$",  # snake_case
            "file": r"^[A-Z][A-Z0-9_]*\.md$",  # UPPER_SNAKE_CASE for docs
            "function": r"^[a-z][a-z0-9_]*$",  # snake_case
            "class": r"^[A-Z][A-Za-z0-9]*$",  # PascalCase
        }

    def validate(self, name: str, convention_type: str) -> bool:
        """Validate name against convention."""
        pattern = self.conventions.get(convention_type)
        if not pattern:
            return True

        return bool(re.match(pattern, name))

    def suggest_name(self, name: str, convention_type: str) -> str:
        """Suggest name following convention."""
        pattern = self.conventions.get(convention_type)
        if not pattern:
            return name

        # Convert to convention
        if convention_type == "command":
            # Convert to kebab-case
            return re.sub(r"_", "-", name.lower())
        elif convention_type == "config_key":
            # Convert to snake_case
            return re.sub(r"-", "_", name.lower())
        elif convention_type == "function":
            # Convert to snake_case
            return re.sub(r"-", "_", name.lower())
        elif convention_type == "class":
            # Convert to PascalCase
            parts = re.split(r"[-_]", name)
            return "".join(p.capitalize() for p in parts)

        return name


# Usage
naming = NamingConvention()

# Validate
assert naming.validate("thegent-install", "command")
assert naming.validate("config_dir", "config_key")
assert naming.validate("get_config_dir", "function")

# Suggest
suggested = naming.suggest_name("thegent_install", "command")
assert suggested == "thegent-install"
```

---

## 77. Advanced Practical Workflows

### 77.1 Complete Development Workflow

**Pattern:** Complete workflow from idea to production.

```python
"""Complete development workflow."""

from typing import List
from dataclasses import dataclass


@dataclass
class WorkflowStep:
    """Workflow step."""

    name: str
    description: str
    command: str
    dependencies: List[str] = None


class DevelopmentWorkflow:
    """Complete development workflow."""

    def __init__(self):
        self.steps: List[WorkflowStep] = []
        self._define_workflow()

    def _define_workflow(self) -> None:
        """Define complete workflow."""
        self.steps = [
            WorkflowStep(name="idea", description="Capture idea", command="thegent workflow idea", dependencies=[]),
            WorkflowStep(
                name="research",
                description="Research and document",
                command="thegent workflow research",
                dependencies=["idea"],
            ),
            WorkflowStep(
                name="plan",
                description="Create implementation plan",
                command="thegent workflow plan",
                dependencies=["research"],
            ),
            WorkflowStep(
                name="implement",
                description="Implement feature",
                command="thegent workflow implement",
                dependencies=["plan"],
            ),
            WorkflowStep(
                name="test",
                description="Test implementation",
                command="thegent workflow test",
                dependencies=["implement"],
            ),
            WorkflowStep(
                name="document",
                description="Update documentation",
                command="thegent workflow document",
                dependencies=["implement"],
            ),
            WorkflowStep(
                name="release",
                description="Release to production",
                command="thegent workflow release",
                dependencies=["test", "document"],
            ),
        ]

    def execute_workflow(self, start_from: Optional[str] = None) -> None:
        """Execute workflow."""
        # Find starting point
        start_index = 0
        if start_from:
            for i, step in enumerate(self.steps):
                if step.name == start_from:
                    start_index = i
                    break

        # Execute steps
        for i in range(start_index, len(self.steps)):
            step = self.steps[i]

            # Check dependencies
            if step.dependencies:
                for dep in step.dependencies:
                    dep_step = next(s for s in self.steps if s.name == dep)
                    if not self._is_completed(dep_step):
                        raise RuntimeError(f"Dependency {dep} not completed")

            # Execute step
            console.print(f"[cyan]Executing: {step.name}[/cyan]")
            console.print(f"[dim]{step.description}[/dim]")

            result = subprocess.run(step.command.split(), check=False)
            if result.returncode != 0:
                raise RuntimeError(f"Workflow step {step.name} failed")

            # Mark as completed
            self._mark_completed(step)

    def _is_completed(self, step: WorkflowStep) -> bool:
        """Check if step is completed."""
        # Check work stream or plan status
        # ...
        return False

    def _mark_completed(self, step: WorkflowStep) -> None:
        """Mark step as completed."""
        # Update work stream or plan status
        # ...
        pass


# Usage
workflow = DevelopmentWorkflow()
workflow.execute_workflow(start_from="idea")
```

### 77.2 Quality Assurance Workflow

**Pattern:** Complete QA workflow.

```python
"""Quality assurance workflow."""

from typing import List


class QAWorkflow:
    """Quality assurance workflow."""

    def __init__(self):
        self.checks: List[Callable[[], bool]] = []
        self._register_checks()

    def _register_checks(self) -> None:
        """Register QA checks."""
        self.checks.extend(
            [
                self._check_lint,
                self._check_types,
                self._check_tests,
                self._check_coverage,
                self._check_security,
                self._check_documentation,
            ]
        )

    def run_all_checks(self) -> tuple[bool, List[str]]:
        """Run all QA checks."""
        failures = []

        for check in self.checks:
            try:
                if not check():
                    failures.append(check.__name__)
            except Exception as e:
                failures.append(f"{check.__name__}: {e}")

        return len(failures) == 0, failures

    def _check_lint(self) -> bool:
        """Check linting."""
        result = subprocess.run(["ruff", "check", "src"], check=False)
        return result.returncode == 0

    def _check_types(self) -> bool:
        """Check types."""
        result = subprocess.run(["basedpyright", "src"], check=False)
        return result.returncode == 0

    def _check_tests(self) -> bool:
        """Check tests."""
        result = subprocess.run(["pytest"], check=False)
        return result.returncode == 0

    def _check_coverage(self) -> bool:
        """Check coverage."""
        result = subprocess.run(["pytest", "--cov=src", "--cov-report=term-missing"], check=False)
        # Parse coverage
        # ...
        return True

    def _check_security(self) -> bool:
        """Check security."""
        # Run security scans
        # ...
        return True

    def _check_documentation(self) -> bool:
        """Check documentation."""
        # Validate documentation
        # ...
        return True


# Usage
qa = QAWorkflow()
all_passed, failures = qa.run_all_checks()

if not all_passed:
    console.print("[red]QA checks failed:[/red]")
    for failure in failures:
        console.print(f"  • {failure}")
    exit(1)
```

---

## 78. Advanced Intuitive Design Patterns

### 78.1 Progressive Complexity

**Pattern:** Expose complexity progressively based on user needs.

```python
"""Progressive complexity."""

from enum import Enum


class ComplexityLevel(Enum):
    """Complexity levels."""

    SIMPLE = "simple"
    STANDARD = "standard"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ProgressiveComplexity:
    """Progressive complexity system."""

    def __init__(self):
        self.user_level = self._detect_user_level()

    def _detect_user_level(self) -> ComplexityLevel:
        """Detect user complexity level."""
        # Analyze command history
        history = CommandHistory()
        recent_commands = history.get_history(limit=50)

        if not recent_commands:
            return ComplexityLevel.SIMPLE

        # Calculate complexity score
        complexity_score = 0
        for entry in recent_commands:
            command = entry["command"]
            complexity_score += self._calculate_command_complexity(command)

        avg_complexity = complexity_score / len(recent_commands)

        if avg_complexity < 2:
            return ComplexityLevel.SIMPLE
        elif avg_complexity < 5:
            return ComplexityLevel.STANDARD
        elif avg_complexity < 8:
            return ComplexityLevel.ADVANCED
        else:
            return ComplexityLevel.EXPERT

    def _calculate_command_complexity(self, command: str) -> int:
        """Calculate command complexity."""
        score = 0
        score += command.count("--")  # Flags
        score += command.count("|")  # Pipes
        score += command.count("&&")  # Chains
        score += len(command.split()) - 1  # Arguments
        return score

    def adapt_command_suggestions(self, partial: str) -> List[str]:
        """Adapt command suggestions based on complexity level."""
        suggester = CommandSuggester()
        suggestions = suggester.suggest(partial)

        # Filter by complexity level
        filtered = []
        for suggestion in suggestions:
            complexity = self._calculate_command_complexity(suggestion)

            if self.user_level == ComplexityLevel.SIMPLE:
                if complexity < 3:
                    filtered.append(suggestion)
            elif self.user_level == ComplexityLevel.STANDARD:
                if complexity < 6:
                    filtered.append(suggestion)
            elif self.user_level == ComplexityLevel.ADVANCED:
                if complexity < 10:
                    filtered.append(suggestion)
            else:  # EXPERT
                filtered.append(suggestion)

        return filtered

    def adapt_output(self, output: str) -> str:
        """Adapt output based on complexity level."""
        if self.user_level == ComplexityLevel.SIMPLE:
            # Add explanations
            return self._add_explanations(output)
        elif self.user_level == ComplexityLevel.STANDARD:
            # Standard output
            return output
        elif self.user_level == ComplexityLevel.ADVANCED:
            # Concise output
            return self._make_concise(output)
        else:  # EXPERT
            # Minimal output
            return self._make_minimal(output)

    def _add_explanations(self, output: str) -> str:
        """Add explanations."""
        return f"{output}\n\n[dim]💡 Tip: Run 'thegent help' for more information[/dim]"

    def _make_concise(self, output: str) -> str:
        """Make concise."""
        lines = output.splitlines()
        return "\n".join(line for line in lines if not line.startswith("[dim]"))

    def _make_minimal(self, output: str) -> str:
        """Make minimal."""
        # Extract only essential information
        # ...
        return output


# Usage
progressive = ProgressiveComplexity()

# Adapt suggestions
suggestions = progressive.adapt_command_suggestions("thegent run")

# Adapt output
output = run_command("thegent doctor")
adapted_output = progressive.adapt_output(output)
console.print(adapted_output)
```

### 78.2 Intuitive Error Messages

**Pattern:** Create intuitive, actionable error messages.

```python
"""Intuitive error messages."""

from typing import Dict, List


class IntuitiveErrorFormatter:
    """Format errors intuitively."""

    def __init__(self):
        self.error_templates: Dict[str, str] = {
            "provider_not_configured": """
[bold red]❌ Provider Not Configured[/bold red]

[cyan]What happened:[/cyan]
The provider '{provider}' is not configured.

[cyan]Why this matters:[/cyan]
You need to configure providers before using agents.

[cyan]How to fix:[/cyan]
[green]thegent cliproxy login {provider}[/green]

[cyan]Need help?[/cyan]
Run: [green]thegent cliproxy help[/green]
""",
            "mcp_not_running": """
[bold red]❌ MCP Server Not Running[/bold red]

[cyan]What happened:[/cyan]
The MCP server is not reachable at {url}.

[cyan]Why this matters:[/cyan]
Agents need the MCP server to function.

[cyan]How to fix:[/cyan]
[green]thegent serve[/green]

Or install as a service:
[green]thegent mcp service install[/green]

[cyan]Need help?[/cyan]
Run: [green]thegent serve --help[/green]
""",
        }

    def format_error(self, error_type: str, **kwargs) -> str:
        """Format error message."""
        template = self.error_templates.get(error_type)
        if not template:
            return f"Error: {error_type}"

        return template.format(**kwargs)

    def format_with_context(self, error: Exception, context: Dict) -> str:
        """Format error with context."""
        # Detect error type
        error_type = type(error).__name__

        # Get platform-specific help
        plat = detect_platform().value

        # Format with context
        if error_type == "ProviderError":
            return self.format_error("provider_not_configured", provider=context.get("provider", "unknown"))
        elif error_type == "ConnectionError":
            return self.format_error("mcp_not_running", url=context.get("url", "http://localhost:3847"))

        # Generic error
        return f"""
[bold red]❌ Error: {error_type}[/bold red]

[cyan]Message:[/cyan]
{str(error)}

[cyan]Platform:[/cyan]
{plat}

[cyan]Need help?[/cyan]
Run: [green]thegent help[/green] or [green]thegent doctor[/green]
"""


# Usage
formatter = IntuitiveErrorFormatter()

try:
    run_agent("codex", "Hello")
except ProviderError as e:
    error_message = formatter.format_with_context(e, {"provider": "anthropic"})
    console.print(error_message)
```

---

## 79. Advanced Practical Examples

### 79.1 Complete Real-World Scenarios

**Scenario 1: New Developer Onboarding**

```python
"""Complete new developer onboarding scenario."""


def onboard_new_developer():
    """Complete onboarding workflow."""
    console.print("[bold cyan]Welcome! Let's get you set up...[/bold cyan]\n")

    # Step 1: Detect platform
    plat = detect_platform()
    console.print(f"[green]✓[/green] Platform: {plat.value}\n")

    # Step 2: Check prerequisites
    console.print("[cyan]Checking prerequisites...[/cyan]")
    missing = check_prerequisites()
    if missing:
        console.print(f"[yellow]Missing: {', '.join(missing)}[/yellow]")
        install_prerequisites(missing)
    console.print("[green]✓[/green] Prerequisites met\n")

    # Step 3: Install thegent
    console.print("[cyan]Installing thegent...[/cyan]")
    install_method = suggest_install_method(plat)
    install_via_method(install_method)
    console.print("[green]✓[/green] Installation complete\n")

    # Step 4: Post-installation
    console.print("[cyan]Running post-installation setup...[/cyan]")
    subprocess.run(["thegent", "install", "--target", "all"], check=True)
    console.print("[green]✓[/green] Setup complete\n")

    # Step 5: Configure providers
    console.print("[cyan]Configuring providers...[/cyan]")
    providers = ["anthropic", "openai"]
    for provider in providers:
        if Confirm.ask(f"Configure {provider}?"):
            subprocess.run(["thegent", "cliproxy", "login", provider], check=True)

    # Step 6: Verify
    console.print("\n[cyan]Verifying installation...[/cyan]")
    result = subprocess.run(["thegent", "doctor"], capture_output=True, text=True)
    if result.returncode == 0:
        console.print("[green]✓[/green] All checks passing!\n")
    else:
        console.print("[yellow]⚠ Some checks failed[/yellow]")
        console.print(result.stdout)

    # Step 7: Guided tour
    if Confirm.ask("\nTake a guided tour?", default=True):
        run_guided_tour()

    console.print("\n[bold green]🎉 Setup complete![/bold green]")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print("  1. Start MCP server: [green]thegent serve[/green]")
    console.print('  2. Run your first agent: [green]thegent run "Hello, world!"[/green]')
    console.print("  3. Explore: [green]thegent help[/green]")
```

**Scenario 2: Production Deployment**

```python
"""Complete production deployment scenario."""


def deploy_to_production(environment: str = "production"):
    """Deploy to production environment."""
    console.print(f"[bold cyan]Deploying to {environment}...[/bold cyan]\n")

    # Step 1: Pre-deployment checks
    console.print("[cyan]Running pre-deployment checks...[/cyan]")
    qa = QAWorkflow()
    all_passed, failures = qa.run_all_checks()
    if not all_passed:
        console.print("[red]Pre-deployment checks failed![/red]")
        for failure in failures:
            console.print(f"  • {failure}")
        raise RuntimeError("Pre-deployment checks failed")
    console.print("[green]✓[/green] All checks passing\n")

    # Step 2: Create backup
    console.print("[cyan]Creating backup...[/cyan]")
    backup_manager = BackupManager()
    backup_path = backup_manager.create_backup(f"pre-{environment}-deploy")
    console.print(f"[green]✓[/green] Backup created: {backup_path}\n")

    # Step 3: Build packages
    console.print("[cyan]Building packages...[/cyan]")
    build_all_packages()
    console.print("[green]✓[/green] Packages built\n")

    # Step 4: Deploy (blue-green)
    console.print("[cyan]Deploying...[/cyan]")
    deployment = BlueGreenDeployment()
    version = get_version()
    package_path = Path(f"dist/thegent-{version}.whl")
    success = deployment.deploy_new_version(version, package_path)
    if not success:
        console.print("[red]Deployment failed![/red]")
        deployment.rollback()
        raise RuntimeError("Deployment failed")
    console.print("[green]✓[/green] Deployment successful\n")

    # Step 5: Verify deployment
    console.print("[cyan]Verifying deployment...[/cyan]")
    verify_deployment()
    console.print("[green]✓[/green] Deployment verified\n")

    # Step 6: Health check
    console.print("[cyan]Running health checks...[/cyan]")
    health_checks = run_health_checks()
    if not all(health_checks.values()):
        console.print("[yellow]⚠ Some health checks failed[/yellow]")
    else:
        console.print("[green]✓[/green] All health checks passing\n")

    console.print(f"[bold green]🎉 Successfully deployed to {environment}![/bold green]")
```

---

## 80. Advanced Integration Checklist

### 80.1 Complete Integration Checklist

**Pre-Integration Checklist:**

- [ ] **Platform Detection**
  - [ ] Platform detection works on all targets
  - [ ] WSL2 detection accurate
  - [ ] Platform-specific paths correct

- [ ] **Path Resolution**
  - [ ] Config directory correct on all platforms
  - [ ] Cache directory correct on all platforms
  - [ ] Data directory correct on all platforms
  - [ ] Paths harmonized with other systems

- [ ] **Package Installation**
  - [ ] PyPI installation works
  - [ ] Nix installation works
  - [ ] Homebrew installation works (macOS)
  - [ ] Windows installer works
  - [ ] Linux packages work (deb/rpm)

- [ ] **System Integration**
  - [ ] Integrates with manage devkit
  - [ ] Integrates with WORK_STREAM
  - [ ] Integrates with PLAN system
  - [ ] Paths harmonized

- [ ] **Configuration**
  - [ ] Hierarchical config works
  - [ ] Platform-specific overrides work
  - [ ] Environment-specific config works
  - [ ] Config validation works

- [ ] **Error Handling**
  - [ ] Platform-specific errors work
  - [ ] Remediation hints accurate
  - [ ] Error recovery works
  - [ ] Error context preserved

- [ ] **Documentation**
  - [ ] Platform-specific guides complete
  - [ ] Troubleshooting guides complete
  - [ ] API docs generated
  - [ ] Cross-references valid

- [ ] **Testing**
  - [ ] Unit tests pass on all platforms
  - [ ] Integration tests pass
  - [ ] E2E tests pass
  - [ ] Cross-system tests pass

- [ ] **Quality**
  - [ ] Lint passes
  - [ ] Types check
  - [ ] Coverage >= 80%
  - [ ] Security scans pass

- [ ] **Release**
  - [ ] All packages build
  - [ ] All packages signed
  - [ ] Release notes complete
  - [ ] Changelog updated

---

## Conclusion

This comprehensive cross-platform audit and plan provides a complete roadmap for production-ready packaging across Windows, macOS, and Linux. The document spans **80 major sections** covering everything from foundational platform detection to advanced integration patterns, harmonious design principles, and complete end-to-end workflows.

### Document Structure

**Foundation (Sections 1-27):**
- Cross-platform architecture and platform detection
- Packaging strategies (PyPI, Nix, Homebrew, Windows Installer, Linux packages)
- Platform-specific paths and conventions
- Directory dependency removal
- Error handling, performance, UX, documentation, testing, CI/CD, security, monitoring, migration

**Advanced Patterns (Sections 28-70):**
- Advanced implementation patterns (DI, Strategy, Factory, Observer)
- Advanced error handling & recovery (Retry, Circuit Breaker, Graceful Degradation)
- Advanced caching strategies (Multi-Level, Invalidation)
- Advanced logging & observability (Structured Logging, Distributed Tracing)
- Advanced security patterns (Secure Secret Storage, Input Validation)
- Advanced performance optimization (Lazy Loading, Async)
- Advanced testing patterns (Platform-Specific Fixtures, Integration Helpers)
- Advanced documentation patterns (Interactive Docs, Troubleshooting Trees)
- Real-world integration scenarios (CI/CD, Docker, Kubernetes)
- Advanced configuration management (Hierarchical, Validation)
- Advanced monitoring & alerting (Health Checks, Metrics)
- Advanced user experience patterns (Progressive Disclosure, Contextual Help)
- Advanced packaging scenarios (Custom Builds, Signing)
- Advanced deployment scenarios (Air-Gapped, Multi-Tenant, HA, Blue-Green, Canary)
- Advanced troubleshooting patterns (Self-Diagnostic, Automated Issue Reporting)
- Advanced user onboarding (Interactive Setup Wizard, Guided Tour)
- Advanced performance monitoring (Profiling, Resource Usage)
- Advanced configuration scenarios (Environment-Specific, Feature Flags)
- Advanced plugin system architecture (Discovery, Lifecycle)
- Advanced state management (Session Persistence, Distributed Sync)
- Advanced networking patterns (Connection Pooling, Rate Limiting)
- Advanced data management (Data Migration, Backup/Recovery)
- Advanced CLI patterns (Interactive Builder, History/Replay)
- Advanced validation & verification (Config Validation, Integrity Verification)
- Advanced error recovery (Auto Recovery, Context Preservation)
- Advanced user feedback systems (Progress Reporting, Interactive Feedback)
- Advanced integration patterns (Webhook, API Gateway)
- Advanced performance tuning (Profiling, Resource Optimization)
- Advanced security hardening (Input Sanitization, Security Audit)
- Advanced monitoring dashboards (Real-Time Status, Metrics Dashboard)
- Advanced workflow automation (Workflow Engine, Task Queue)
- Advanced documentation generation (Auto-Generated API Docs, Interactive Server)
- Advanced user assistance (Intelligent Command Suggestions, Context-Aware Help)
- Advanced quality assurance patterns (Automated Quality Gates, Continuous Monitoring)
- Advanced integration testing (E2E Scenarios, Chaos Engineering)
- Advanced user analytics (Usage Analytics, Performance Benchmarking)
- Advanced documentation automation (Auto-Generated Troubleshooting, Interactive API Explorer)
- Advanced deployment automation (Blue-Green, Canary)
- Advanced monitoring dashboards (Real-Time Metrics with Live Updates)
- Advanced error prevention (Proactive Error Detection, Predictive Failure)
- Advanced user personalization (User Preference Learning, Adaptive UI/UX)
- Advanced resource management (Resource Pool Management, Cleanup Automation)
- Advanced documentation features (Video Tutorial Integration, Interactive Code Playground)

**System Integration & Harmonization (Sections 71-80):**
- Advanced system integration patterns (manage devkit, WORK_STREAM, PLAN system)
- Advanced cross-system harmonization (unified config, harmonized paths)
- Advanced holistic design patterns (consistency, harmonious APIs)
- Advanced integration testing scenarios (cross-system, E2E)
- Advanced documentation integration (cross-reference system, generation pipeline)
- Advanced harmonious design principles (design language system, naming conventions)
- Advanced practical workflows (development workflow, QA workflow)
- Advanced intuitive design patterns (progressive complexity, intuitive error messages)
- Advanced practical examples (complete real-world scenarios)
- Advanced integration checklist (complete pre-integration checklist)

### Key Priorities

1. **Platform Detection & Paths** (Phase 1-2) — Foundation for everything
2. **Packaging** (Phase 4-5) — Enable distribution on all platforms
3. **Error Handling** (Phase 6) — Critical for user experience
4. **Documentation** (Phase 8) — Platform-specific guides essential
5. **System Integration** (Phase 9) — Harmonious integration with existing systems (manage devkit, WORK_STREAM, PLAN system)
6. **Harmonious Design** (Sections 72-73, 76) — Consistent design language and APIs across all components
7. **Advanced Patterns** (Sections 28-70) — Production-grade patterns for scalability, reliability, and maintainability

### Expected Outcome

A production-ready, shipping-quality cross-platform package that can be installed via standard package managers on Windows, macOS, and Linux with:

- **Polished, intuitive user experience** — Progressive complexity, adaptive UI/UX, intelligent command suggestions
- **Comprehensive platform-specific documentation** — Installation guides, troubleshooting trees, interactive API explorer
- **Seamless integration** — Harmonious integration with existing devkit systems (manage), WORK_STREAM, and PLAN system
- **Production-grade patterns** — Advanced error handling, caching, security, monitoring, deployment strategies
- **Complete workflows** — End-to-end development and QA workflows from idea to production
- **Harmonious design** — Consistent design language, naming conventions, and API patterns across all components

### Implementation Approach

**12-Phase Implementation Plan:**
1. Platform Detection & Architecture
2. Path Resolution & Conventions
3. Directory Dependencies Removal
4. Python Packaging (PyPI)
5. Native Package Managers (Nix, Homebrew, Windows Installer, Linux packages)
6. Error Handling & Recovery
7. Performance Optimization
8. User Experience & Documentation
9. Testing & Quality Assurance
10. CI/CD & Release Automation
11. Security & Compliance
12. Migration & Upgrade Paths

**Timeline:** 5 weeks, 104-142 hours total effort

**Risk:** Medium (manageable with phased approach, platform-specific testing, and fallbacks)

### Integration Points

This plan integrates harmoniously with:
- **manage devkit** — Shared paths, tool registration, unified configuration
- **WORK_STREAM.md** — Work item claiming, completion tracking, next item selection
- **PLAN.md / PLAN_STATUS.md** — Task status updates, phase tracking, dependency resolution
- **Existing research & plans** — Cross-referenced with all related documentation

### Next Steps

After completing this comprehensive audit and plan, the next phase will focus on:
1. **Holistic + Harmonious Design** — Ensuring all components work together seamlessly
2. **Full Integration** — Complete integration with existing systems and plans
3. **Implementation** — Begin phased implementation starting with Phase 1 (Platform Detection)

---

---

## 81. Research-Enhanced Implementation Patterns

### 81.1 Dynamic Versioning Implementation

**Research Finding:** PEP 440 and modern build systems support dynamic versioning from git tags.

**Implementation:**

```python
"""Dynamic version management using hatch-vcs."""

# pyproject.toml
[tool.hatch.version]
source = "vcs"  # Automatically get version from git tags
write_to = "src/thegent/_version.py"

# src/thegent/__init__.py
try:
    from thegent._version import __version__
except ImportError:
    # Dev mode fallback
    import subprocess

    try:
        result = subprocess.run(["git", "describe", "--tags", "--always"], capture_output=True, text=True, check=True)
        __version__ = result.stdout.strip()
    except Exception:
        __version__ = "0.1.0-dev"
```

**Alternative: Using setuptools-scm:**

```toml
[build-system]
requires = ["setuptools>=61.0", "setuptools-scm>=8.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools_scm]
write_to = "src/thegent/_version.py"
```

### 81.2 Package Data Access with importlib.resources

**Research Finding:** `importlib.resources` (Python 3.9+) is the standard for accessing bundled files.

**Enhanced Implementation:**

```python
"""Enhanced package data access."""

from importlib import resources
from pathlib import Path
from typing import Optional


def get_hooks_dir() -> Path:
    """Get hooks directory with comprehensive fallback chain.

    Fallback order:
    1. Package data (installed mode)
    2. Dev repository (development mode)
    3. User config directory (create if needed)
    4. Environment variable override
    """
    # 1. Try package data first
    try:
        if resources.is_resource("thegent", "hooks"):
            hooks_pkg = resources.files("thegent") / "hooks"
            if hooks_pkg.is_dir():
                hooks_path = Path(str(hooks_pkg))
                if hooks_path.exists():
                    return hooks_path
    except (ImportError, TypeError, AttributeError):
        pass

    # 2. Fallback to dev repo
    dev_hooks = _find_dev_repo() / "hooks"
    if dev_hooks.exists():
        return dev_hooks

    # 3. Fallback to user config
    user_hooks = get_config_dir() / "hooks"
    user_hooks.mkdir(parents=True, exist_ok=True)

    # 4. Environment variable override
    env_override = os.environ.get("THGENT_HOOKS_DIR")
    if env_override:
        return Path(env_override).expanduser()

    return user_hooks


def _find_dev_repo() -> Path:
    """Find development repository root."""
    current = Path(__file__).resolve()

    # Walk up to find repo root
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "hooks").exists():
            return parent

    # Fallback to current file's parent
    return current.parent.parent.parent
```

### 81.3 Binary Wheel Strategy with maturin

**Research Finding:** Platform-specific wheels with Rust extensions require maturin.

**Implementation:**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling", "maturin>=1.0.0"]
build-backend = "maturin"

[tool.maturin]
features = ["pyo3/extension-module"]
module-name = "thegent._rust"
compatibility = "linux"

# Build wheels for all platforms
# Use cibuildwheel in CI:
# cibuildwheel --platform linux --platform macos --platform windows
```

**CI/CD Integration:**

```yaml
# .github/workflows/build-wheels.yml
name: Build Wheels

on: [push, pull_request]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Build wheel
        run: |
          pip install maturin
          maturin build --release --out dist
```

### 81.4 Homebrew Formula Best Practices

**Research Finding:** Homebrew formulae require specific structure and testing.

**Enhanced Formula:**

```ruby
class Thegent < Formula
  desc "Agentic orchestration & governance platform"
  homepage "https://github.com/router-for-me/thegent"
  url "https://files.pythonhosted.org/packages/.../thegent-0.1.0.tar.gz"
  sha256 "..."
  license "MIT"

  depends_on "python@3.12"
  depends_on "rust" => :build

  # Platform-specific dependencies
  on_macos do
    depends_on "python-tk"
  end

  on_linux do
    depends_on "dbus"
    depends_on "at-spi2-core"
  end

  def install
    # Use pip install with --prefix
    system "pip3", "install", "--prefix=#{prefix}", "--no-deps", "."

    # Install dependencies
    system "pip3", "install", "--prefix=#{prefix}", "-r", "requirements.txt"

    # Install hooks, templates, scripts
    (share/"thegent").install Dir["hooks", "templates", "scripts"]

    # Create symlink
    bin.install_symlink libexec/"bin/thegent"
  end

  test do
    system "#{bin}/thegent", "--version"
    system "#{bin}/thegent", "doctor"
  end
end
```

### 81.5 Nix Flake Best Practices

**Research Finding:** Nix flakes provide reproducible builds across platforms.

**Enhanced Flake:**

```nix
{
  description = "thegent - Agentic orchestration platform";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay.url = "github:oxalica/rust-overlay";
  };

  outputs = { self, nixpkgs, flake-utils, rust-overlay }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ rust-overlay.overlays.default ];
        };

        python = pkgs.python312;

        thegent = python.pkgs.buildPythonPackage {
          pname = "thegent";
          version = "0.1.0";
          src = ./.;

          format = "pyproject";

          propagatedBuildInputs = with python.pkgs; [
            httpx typer rich pydantic
            pydantic-settings python-dotenv
            tenacity pyyaml fastmcp starlette
            uvicorn opentelemetry-api opentelemetry-sdk
            litellm tomlkit cachetools orjson watchdog
          ];

          nativeBuildInputs = with pkgs; [
            rustPlatform.cargoBuildHook
            rustPlatform.rust.cargo
            rustPlatform.rust.rustc
            python.pkgs.setuptools
            python.pkgs.wheel
          ];

          # Install hooks, templates, scripts
          postInstall = ''
            mkdir -p $out/share/thegent
            cp -r hooks $out/share/thegent/
            cp -r templates $out/share/thegent/
            cp -r scripts $out/share/thegent/
          '';

          checkPhase = ''
            ${python.interpreter} -m pytest tests/
          '';
        };
      in
      {
        packages.default = thegent;

        apps.default = {
          type = "app";
          program = "${thegent}/bin/thegent";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            thegent
            python
            pkgs.rustc
            pkgs.cargo
          ];
        };
      }
    );
}
```

### 81.6 Windows Installer Best Practices

**Research Finding:** MSIX is preferred for modern Windows; PyInstaller for standalone executables.

**MSIX Packaging:**

```xml
<!-- Package.appxmanifest -->
<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
  <Identity Name="Thegent"
            Version="0.1.0.0"
            Publisher="CN=Your Name, O=Your Org" />

  <Properties>
    <DisplayName>thegent</DisplayName>
    <PublisherDisplayName>Your Org</PublisherDisplayName>
    <Description>Agentic orchestration & governance platform</Description>
    <Logo>Assets\Logo.png</Logo>
  </Properties>

  <Resources>
    <Resource Language="en-us" />
  </Resources>

  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22621.0" />
  </Dependencies>

  <Applications>
    <Application Id="thegent" Executable="thegent.exe">
      <uap:VisualElements DisplayName="thegent"
                          Description="Agentic orchestration platform"
                          Square150x150Logo="Assets\Square150x150Logo.png"
                          Square44x44Logo="Assets\Square44x44Logo.png"
                          BackgroundColor="transparent" />
    </Application>
  </Applications>
</Package>
```

**PyInstaller Spec:**

```python
# thegent.spec
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["src/thegent/cli.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("hooks", "hooks"),
        ("templates", "templates"),
        ("scripts", "scripts"),
    ],
    hiddenimports=[
        "thegent.platform",
        "thegent.platform_paths",
        "thegent.integration",
        "thegent.design",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="thegent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### 81.7 Auto-Update Mechanism

**Research Finding:** Auto-update patterns vary by package manager; respect user's installation method.

**Implementation:**

```python
"""Auto-update mechanism."""

from packaging import version
import subprocess
from thegent.platform import detect_platform, Platform


class UpdateChecker:
    """Check for available updates."""

    def __init__(self):
        self.platform = detect_platform()
        self.install_method = self._detect_install_method()

    def _detect_install_method(self) -> str:
        """Detect how thegent was installed."""
        # Check for Homebrew
        if self._installed_via_homebrew():
            return "homebrew"

        # Check for Nix
        if self._installed_via_nix():
            return "nix"

        # Check for system package manager
        if self.platform == Platform.LINUX:
            if self._installed_via_apt():
                return "apt"
            elif self._installed_via_yum():
                return "yum"

        if self.platform == Platform.WINDOWS:
            if self._installed_via_winget():
                return "winget"

        # Default to pip
        return "pip"

    def check_for_updates(self) -> Optional[str]:
        """Check for available updates."""
        try:
            current_version = self._get_current_version()
            latest_version = self._get_latest_version()

            if version.parse(latest_version) > version.parse(current_version):
                return latest_version

            return None
        except Exception:
            return None

    def get_update_command(self) -> str:
        """Get update command for current installation method."""
        commands = {
            "homebrew": "brew upgrade thegent",
            "nix": "nix profile upgrade thegent",
            "apt": "sudo apt update && sudo apt upgrade thegent",
            "yum": "sudo yum update thegent",
            "winget": "winget upgrade thegent",
            "pip": "pip install --upgrade thegent",
        }

        return commands.get(self.install_method, "pip install --upgrade thegent")

    def _get_current_version(self) -> str:
        """Get current installed version."""
        from thegent import __version__

        return __version__

    def _get_latest_version(self) -> str:
        """Get latest version from PyPI."""
        import json
        import urllib.request

        url = "https://pypi.org/pypi/thegent/json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            return data["info"]["version"]

    def _installed_via_homebrew(self) -> bool:
        """Check if installed via Homebrew."""
        try:
            result = subprocess.run(["brew", "list", "thegent"], capture_output=True, check=False)
            return result.returncode == 0
        except Exception:
            return False

    def _installed_via_nix(self) -> bool:
        """Check if installed via Nix."""
        nix_store = os.environ.get("NIX_STORE")
        if nix_store:
            try:
                result = subprocess.run(["nix", "profile", "list"], capture_output=True, text=True, check=False)
                return "thegent" in result.stdout
            except Exception:
                pass
        return False

    def _installed_via_apt(self) -> bool:
        """Check if installed via apt."""
        try:
            result = subprocess.run(["dpkg", "-l", "python3-thegent"], capture_output=True, check=False)
            return result.returncode == 0
        except Exception:
            return False

    def _installed_via_yum(self) -> bool:
        """Check if installed via yum."""
        try:
            result = subprocess.run(["rpm", "-q", "python3-thegent"], capture_output=True, check=False)
            return result.returncode == 0
        except Exception:
            return False

    def _installed_via_winget(self) -> bool:
        """Check if installed via winget."""
        try:
            result = subprocess.run(["winget", "list", "thegent"], capture_output=True, check=False)
            return result.returncode == 0
        except Exception:
            return False
```

### 81.8 Code Signing Implementation

**Research Finding:** Code signing required for Windows/macOS distribution.

**macOS Code Signing:**

```python
"""macOS code signing."""

import subprocess
from pathlib import Path


def sign_macos_binary(binary_path: Path, identity: str) -> None:
    """Sign macOS binary."""
    subprocess.run(
        ["codesign", "--sign", identity, "--timestamp", "--options", "runtime", str(binary_path)], check=True
    )


def notarize_macos_package(package_path: Path, apple_id: str, team_id: str, password: str) -> None:
    """Notarize macOS package."""
    subprocess.run(
        [
            "xcrun",
            "notarytool",
            "submit",
            str(package_path),
            "--apple-id",
            apple_id,
            "--team-id",
            team_id,
            "--password",
            password,
            "--wait",
        ],
        check=True,
    )
```

**Windows Code Signing:**

```python
"""Windows code signing."""

import subprocess
from pathlib import Path


def sign_windows_binary(binary_path: Path, cert_path: Path, password: str) -> None:
    """Sign Windows binary."""
    subprocess.run(
        [
            "signtool",
            "sign",
            "/f",
            str(cert_path),
            "/p",
            password,
            "/t",
            "http://timestamp.digicert.com",
            str(binary_path),
        ],
        check=True,
    )
```

### 81.9 First-Run Wizard Implementation

**Research Finding:** First-run wizards improve user onboarding significantly.

**Enhanced Implementation:**

```python
"""Enhanced first-run wizard."""

from rich.prompt import Confirm, Prompt
from rich.console import Console
from thegent.platform import detect_platform
from thegent.integration import ManageDevkitIntegration

console = Console()


def run_first_run_wizard() -> None:
    """Run comprehensive first-run setup wizard."""
    console.print("[bold cyan]Welcome to thegent![/bold cyan]\n")

    # Step 1: Platform detection
    plat = detect_platform()
    console.print(f"[green]✓[/green] Platform: {plat.value}")
    arch = get_architecture()
    console.print(f"[green]✓[/green] Architecture: {arch}\n")

    # Step 2: Prerequisites check
    console.print("[cyan]Checking prerequisites...[/cyan]")
    missing = check_prerequisites()
    if missing:
        console.print(f"[yellow]Missing: {', '.join(missing)}[/yellow]")
        if Confirm.ask("Install missing prerequisites?", default=True):
            install_prerequisites(missing)
    console.print("[green]✓[/green] Prerequisites met\n")

    # Step 3: System integration
    console.print("[cyan]Checking system integrations...[/cyan]")

    # Manage devkit integration
    manage = ManageDevkitIntegration()
    if manage.manage_config_path:
        if Confirm.ask("Integrate with manage devkit?", default=True):
            manage.integrate_paths()
            manage.integrate_tools()
            manage.register_with_manage()
            console.print("[green]✓[/green] Integrated with manage devkit")

    # Step 4: Provider configuration
    console.print("\n[cyan]Configure AI providers:[/cyan]")
    providers = ["anthropic", "openai", "google"]
    configured = []
    for provider in providers:
        if Confirm.ask(f"Configure {provider}?", default=False):
            configure_provider(provider)
            configured.append(provider)

    if configured:
        console.print(f"[green]✓[/green] Configured: {', '.join(configured)}")

    # Step 5: Post-installation
    console.print("\n[cyan]Running post-installation setup...[/cyan]")
    subprocess.run(["thegent", "install", "--target", "all"], check=True)
    console.print("[green]✓[/green] Setup complete\n")

    # Step 6: Verification
    console.print("[cyan]Verifying installation...[/cyan]")
    result = subprocess.run(["thegent", "doctor"], capture_output=True, text=True)
    if result.returncode == 0:
        console.print("[green]✓[/green] All checks passing!\n")
    else:
        console.print("[yellow]⚠ Some checks failed[/yellow]")
        console.print(result.stdout)

    # Step 7: Guided tour
    if Confirm.ask("\nTake a guided tour?", default=True):
        run_guided_tour()

    console.print("\n[bold green]🎉 Setup complete![/bold green]")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print("  1. Start MCP server: [green]thegent serve[/green]")
    console.print('  2. Run your first agent: [green]thegent run "Hello!"[/green]')
    console.print("  3. Explore: [green]thegent help[/green]")
```

---

## 82. Research-Enhanced Packaging Configuration

### 82.1 Enhanced pyproject.toml

**Based on Research Findings:**

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "thegent"
dynamic = ["version"]  # Dynamic from git tags
description = "Agentic orchestration & governance platform"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Koosha Paridehpour", email = "kooshapari@gmail.com" }]
keywords = ["ai", "agent", "mcp", "orchestration", "automation", "cli"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Operating System :: MacOS",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: Microsoft :: Windows :: Windows 10",
    "Operating System :: Microsoft :: Windows :: Windows 11",
    "Operating System :: POSIX",
    "Operating System :: POSIX :: Linux",
]

dependencies = [
    "httpx>=0.27.0",
    "typer>=0.21.1",
    "rich>=14.3.1",
    "pydantic>=2.12.5",
    "pydantic-settings>=2.12.0",
    "python-dotenv>=1.2.1",
    "tenacity>=9.0.0",
    "pyyaml>=6.0",
    "fastmcp[tasks]>=3.0.0rc1",
    "starlette>=0.36.0",
    "uvicorn>=0.27.0",
    "opentelemetry-api>=1.27.0",
    "opentelemetry-sdk>=1.27.0",
    "litellm>=1.50.0",
    "tomlkit>=0.12.0",
    "cachetools>=5.0.0",
    "orjson>=3.11.7",
    "watchdog>=5.0.0",
]

[project.optional-dependencies]
windows = [
    "pywin32>=306",
]
macos = [
    "pyobjc-framework-Cocoa>=10.0",
]
linux = [
    "dbus-python>=1.3.0",
    "python-dbus>=1.3.0",
]

[project.scripts]
thegent = "thegent.main:app"

[tool.hatch.version]
source = "vcs"
write_to = "src/thegent/_version.py"

[tool.hatch.build.targets.wheel]
packages = ["src/thegent"]
include = [
    "hooks/**/*",
    "templates/**/*",
    "scripts/**/*",
]

[tool.hatch.build.targets.sdist]
include = [
    "/hooks",
    "/templates",
    "/scripts",
    "/src",
    "/pyproject.toml",
    "/README.md",
    "/LICENSE",
]
```

### 82.2 MANIFEST.in for Source Distributions

**Research Finding:** MANIFEST.in needed for sdists (not wheels).

```python
# MANIFEST.in
include README.md
include LICENSE
include pyproject.toml
recursive-include hooks *
recursive-include templates *
recursive-include scripts *
recursive-include src *
global-exclude __pycache__
global-exclude *.py[co]
global-exclude .git*
```

---

## 83. Research-Enhanced Release Automation

### 83.1 Complete CI/CD Workflow

**Based on Research Findings:**

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-wheels:
    name: Build wheels on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.12']

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Needed for version detection

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine hatch-vcs

      - name: Build wheel
        run: python -m build --wheel

      - name: Build sdist
        run: python -m build --sdist

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist-${{ matrix.os }}
          path: dist/*

  publish-pypi:
    needs: build-wheels
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')

    steps:
      - uses: actions/checkout@v4

      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: dist
          pattern: dist-*
          merge-multiple: true

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          pip install twine
          twine upload dist/*

  update-homebrew:
    needs: publish-pypi
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')

    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.HOMEBREW_TOKEN }}
          repository: Homebrew/homebrew-core
          path: homebrew-core

      - name: Update Homebrew formula
        run: |
          cd homebrew-core
          # Update formula with new version and SHA256
          # ... (formula update logic)
```

---

## 84. Advanced Research Integration

### 84.1 Deep Research Findings

**Extended Research Document:** See [CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md](CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md) for comprehensive advanced patterns covering **26 major sections** with extensive depth and breadth:

**Core Packaging (Sections 1-6):**
- Modern Python packaging with PEP 517/518 standards
- Package data access with importlib.resources
- Dynamic versioning from git tags
- Native package managers (Homebrew, Nix, Windows Installer, Linux packages)
- User experience patterns (first-run wizards, progress indicators)
- Security fundamentals (code signing, dependency auditing)

**Advanced Packaging Patterns (Section 13):**
- **Namespace Packages (PEP 420)** — Modular distribution strategy for splitting `thegent` into `thegent-core`, `thegent-plugins`, `thegent-integrations`
- **Editable Installs (PEP 660)** — Wheel-based editable installs for development workflow
- **Advanced Build Tools** — PyOxidizer (Rust-based bundler) and Nuitka (Python compiler) for single-file executables

**SBOM & Supply Chain Security (Section 14):**
- **SBOM Standards** — CycloneDX, SPDX (ISO/IEC 5962:2021), Package URL (PURL) for universal package identification
- **SBOM Generation** — Syft, pip-audit integration for automated SBOM creation
- **Supply Chain Security** — SLSA (Supply-chain Levels), cosign signing, OSV-Scanner vulnerability detection
- **Best Practices** — Sign all release artifacts, generate SBOMs for every release, scan dependencies regularly

**Reproducible Builds (Section 15):**
- **Deterministic Builds** — Same source → same binary (bit-for-bit)
- **Python-Specific** — `SOURCE_DATE_EPOCH`, fixed build environment, deterministic file ordering
- **Verification** — diffoscope, reprotest for build reproducibility validation

**Advanced CI/CD Patterns (Section 16):**
- **Matrix Builds** — Comprehensive platform coverage with cibuildwheel
- **Parallel Execution** — Build for all platforms simultaneously
- **Caching Strategies** — pip cache, build dependencies cache
- **Release Automation** — Complete workflow: build → test → sign → publish → update package managers

**Performance Optimization (Section 17):**
- **Wheel Optimization** — Lazy loading, binary size reduction, compression
- **Installation Performance** — Parallel installation, pre-compiled wheels, uv alternative
- **Best Practices** — Provide wheels for all platforms, minimize package size, optimize import paths

**Advanced Testing Strategies (Section 18):**
- **Package Installation Testing** — Test in clean environments, verify resource access
- **Cross-Platform Testing** — Platform-specific tests, wheel compatibility validation
- **Comprehensive Coverage** — Matrix testing across platforms and Python versions

**Advanced Security Frameworks (Section 19):**
- **TUF (The Update Framework)** — Secure content delivery and updates, protection against supply chain attacks
- **in-toto Attestations** — Verifiable claims about software production process
- **DSSE (Dead Simple Signing Envelope)** — Simple, foolproof standard for signing arbitrary data

**Additional Distribution Platforms (Section 20):**
- **Snap Packages** — Linux app distribution via Snap Store with snapcraft.yaml
- **Flatpak** — Cross-distribution Linux application packaging with org.thegent.json
- **AppImage** — Portable Linux application format

**Advanced Package Management Tools (Section 21):**
- **uv** — Ultra-fast Python package manager (10-100x faster than pip), single tool replacing pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv
- **pipx** — Isolated application installation and execution
- **pipenv** — Dependency management with Pipfile and Pipfile.lock

**Developer Experience & Code Quality (Section 22):**
- **Pre-commit Hooks** — Automated code quality checks before commit
- **Ruff** — Ultra-fast linter and formatter (replaces flake8, black, isort)
- **Black** — Uncompromising Python code formatter
- **Mypy** — Static type checker for Python
- **Hypothesis** — Property-based testing framework

**Advanced Performance Optimization (Section 23):**
- **Startup Time** — Lazy imports, deferred CLI loading, module caching
- **Memory Optimization** — __slots__, generators, streaming patterns
- **Binary Size** — Exclude unnecessary files, strip debug symbols, compression

**Advanced CI/CD Patterns Extended (Section 24):**
- **GitOps** — Automated package manager updates
- **Progressive Delivery** — Canary releases, feature flags
- **Advanced Caching** — Dependency caching, Docker layer caching

**Monitoring & Observability (Section 25):**
- **Telemetry** — Structured logging, error reporting, analytics
- **Health Checks** — System diagnostics, actionable error messages
- **Metrics** — Installation tracking, usage analytics, performance monitoring

**Compliance & Legal Considerations (Section 26):**
- **License Compliance** — License detection, attribution, compatibility checking
- **Export Control** — Compliance with international export regulations

**Additional Package Management Tools (Section 27):**
- **Poetry** — Dependency management with pyproject.toml and poetry.lock
- **PDM** — PEP 621 compliant package manager with fast resolver
- **Hatch** — Modern project manager with environment management
- **Conda** — Cross-platform binary package manager

**Windows Package Managers (Section 28):**
- **Chocolatey** — Windows package manager (like apt-get/yum for Windows)
- **Scoop** — Portable app installer for Windows

**Advanced Testing Strategies Extended (Section 29):**
- **Fuzzing** — OSS-Fuzz integration for continuous security testing
- **Mutation Testing** — MutPy for evaluating test quality
- **Chaos Engineering** — Chaos Toolkit for resilience testing

**Advanced Distribution Strategies (Section 30):**
- **Multi-Channel Distribution** — Simultaneous distribution across platforms
- **Staged Rollouts** — Gradual release to minimize risk
- **A/B Testing** — Test new versions with subset of users

**Advanced Error Handling & Recovery (Section 31):**
- **Structured Error Handling** — Consistent error classes with codes
- **Error Recovery** — Automatic recovery from transient failures
- **User-Friendly Messages** — Actionable error messages with suggestions

**Advanced Configuration Management (Section 32):**
- **Hierarchical Configuration** — Multiple sources with precedence
- **Configuration Validation** — Schema-based validation with Pydantic

### 84.2 Implementation Priorities

**Phase 1: Foundation (Sections 1-6)**
- ✅ Platform detection and path resolution (already implemented)
- ✅ Dynamic versioning (integrate hatch-vcs)
- ✅ Package data access (importlib.resources with fallback)
- ✅ Native package managers (Homebrew, Nix, Windows Installer, Linux packages)

**Phase 2: Security & Compliance (Sections 14, 19, 26)**
- 🔄 SBOM generation (CycloneDX, SPDX)
- 🔄 Code signing (cosign integration)
- 🔄 Vulnerability scanning (pip-audit, osv-scanner in CI/CD)
- 🔄 Supply chain security (SLSA attestations)
- 📋 TUF framework for secure updates
- 📋 in-toto attestations for build provenance
- 📋 DSSE signing for artifacts
- 📋 License compliance and export control

**Phase 3: Advanced Patterns (Sections 13, 15-18, 20-21)**
- 📋 Namespace packages (if modular distribution needed)
- 📋 Reproducible builds (SOURCE_DATE_EPOCH, deterministic builds)
- 📋 Advanced CI/CD (matrix builds, parallel execution, caching)
- 📋 Performance optimization (lazy loading, wheel optimization)
- 📋 Comprehensive testing (installation tests, cross-platform validation)
- 📋 Additional distribution platforms (Snap, Flatpak, AppImage)
- 📋 Advanced package management tools (uv, pipx, pipenv integration)

**Phase 4: Developer Experience (Section 22)**
- 📋 Pre-commit hooks for code quality
- 📋 Ruff integration (linting and formatting)
- 📋 Mypy type checking
- 📋 Hypothesis property-based testing
- 📋 Comprehensive type hints

**Phase 5: Performance & Monitoring (Sections 23, 25)**
- 📋 Startup time optimization (lazy imports, deferred loading)
- 📋 Memory optimization (__slots__, generators)
- 📋 Binary size reduction
- 📋 Telemetry and observability
- 📋 Health checks and diagnostics

**Phase 6: Advanced CI/CD (Section 24)**
- 📋 GitOps for package distribution
- 📋 Progressive delivery (canary releases, feature flags)
- 📋 Advanced caching strategies

**Phase 7: Additional Package Managers (Sections 27-28)**
- 📋 Support Poetry, PDM, Hatch for Python projects
- 📋 Conda package support
- 📋 Chocolatey package for Windows
- 📋 Scoop manifest for Windows

**Phase 8: Advanced Testing (Section 29)**
- 📋 OSS-Fuzz integration for fuzzing
- 📋 Mutation testing with MutPy
- 📋 Chaos engineering experiments

**Phase 9: Advanced Distribution (Section 30)**
- 📋 Multi-channel distribution automation
- 📋 Staged rollout mechanisms
- 📋 A/B testing infrastructure

**Phase 10: Error Handling & Configuration (Sections 31-32)**
- 📋 Structured error handling system
- 📋 Error recovery mechanisms
- 📋 User-friendly error messages
- 📋 Hierarchical configuration management
- 📋 Configuration validation with schemas

### 84.3 Key Recommendations

1. **Immediate Actions:**
   - Integrate SBOM generation into release workflow
   - Add code signing with cosign for all artifacts
   - Implement vulnerability scanning in CI/CD
   - Generate reproducible builds with SOURCE_DATE_EPOCH
   - Set up pre-commit hooks with ruff and black
   - Add comprehensive type hints with mypy

2. **Short-Term Enhancements:**
   - Set up advanced CI/CD with cibuildwheel matrix builds
   - Optimize wheel builds for all platforms
   - Implement comprehensive testing matrix
   - Add performance optimizations (lazy loading, size reduction)
   - Support additional distribution platforms (Snap, Flatpak)
   - Integrate uv for faster dependency management
   - Implement TUF for secure updates
   - Add telemetry and health checks

3. **Long-Term Improvements:**
   - Consider namespace packages for modular distribution
   - Evaluate PyOxidizer/Nuitka for single-file executables
   - Implement reproducible build verification
   - Add advanced caching strategies
   - Implement in-toto attestations for all builds
   - Add progressive delivery mechanisms
   - Comprehensive monitoring and observability
   - License compliance automation
   - Support additional package managers (Poetry, PDM, Hatch, Conda)
   - Windows package manager support (Chocolatey, Scoop)
   - Integrate fuzzing with OSS-Fuzz
   - Implement mutation testing
   - Add chaos engineering experiments
   - Multi-channel distribution automation
   - Staged rollout and A/B testing infrastructure
   - Advanced error handling and recovery
   - Hierarchical configuration management

---

## See also

- [CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md](CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md) — **Comprehensive advanced research** on package design, SBOM, supply chain security, reproducible builds, advanced CI/CD, performance optimization, and testing strategies
- [RUNTIME_INFRASTRUCTURE_RESOURCE_LEAKS_AUDIT_AND_PLAN.md](RUNTIME_INFRASTRUCTURE_RESOURCE_LEAKS_AUDIT_AND_PLAN.md) — **Critical runtime infrastructure audit** — Resource leaks, process management, file descriptor exhaustion, and optimization issues
- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
- [REMOVE_DIRECTORY_DEPENDENCIES_AUDIT_AND_PLAN.md](REMOVE_DIRECTORY_DEPENDENCIES_AUDIT_AND_PLAN.md) — original audit
- [CROSS_PLATFORM_RESEARCH_COMPLETE.md](CROSS_PLATFORM_RESEARCH_COMPLETE.md) — cross-platform research
- [CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md](CLIENT_SIDE_PACKAGE_DESIGN_RESEARCH.md) — comprehensive research on package design


---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made
1. Added planning patterns
2. Added implementation roadmap
3. Enhanced cross-references

### Cross-References Added
- WORK_STREAM.md
- Implementation guides

### Practical Additions
- Planning templates
- Roadmap configurations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [REMOVE_DIRECTORY_DEPENDENCIES_AUDIT_AND_PLAN.md](./REMOVE_DIRECTORY_DEPENDENCIES_AUDIT_AND_PLAN.md) - Directory dependencies
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
