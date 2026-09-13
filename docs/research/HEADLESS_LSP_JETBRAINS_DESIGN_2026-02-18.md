<DONE>
# Headless LSP Setup with JetBrains Integration

**Date**: 2026-02-18
**Status**: Design Phase
**Goal**: Full headless LSP infrastructure with JetBrains IDE Ultimate integration

---

## Executive Summary

Design and implement a **comprehensive headless LSP setup** that:
1. Manages multiple LSP servers (Python, TypeScript, Rust, Go, etc.)
2. Integrates JetBrains IDE Ultimate CLI tools (format, inspect, diff, merge)
3. Provides unified LSP interface for agents
4. Supports JetBrains Gateway for headless backend access

**Key Insight**: JetBrains doesn't provide native LSP servers, but we can:
- Use standard LSP servers (pyright, rust-analyzer, etc.)
- Integrate JetBrains CLI tools as complementary services
- Use JetBrains Gateway for headless backend access to full IDE features

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Headless LSP Manager (thegent)                │
│  • LSP Server Registry                                      │
│  • Server Lifecycle Management                              │
│  • Multi-client Support                                     │
│  • JetBrains Integration                                    │
└──────────────────────┬────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ LSP Servers  │ │ JetBrains    │ │ JetBrains    │
│              │ │ CLI Tools     │ │ Gateway      │
│ • pyright    │ │ • format     │ │ (headless    │
│ • rust-analyzer│ │ • inspect   │ │  backend)    │
│ • gopls      │ │ • diff       │ │              │
│ • tsserver   │ │ • merge      │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Component 1: Headless LSP Server Manager

### Purpose

Manage multiple LSP servers in headless mode, providing unified interface for agents.

### Implementation

**File**: `src/thegent/lsp/headless_manager.py`

```python
"""Headless LSP Server Manager - Full-featured LSP infrastructure."""

import asyncio
import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Optional, Dict, List

logger = logging.getLogger(__name__)

# Comprehensive LSP server registry
LSP_SERVERS = {
    "python": {
        "command": "pyright-langserver",
        "args": ["--stdio"],
        "install": "npm install -g pyright",
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
    "typescript": {
        "command": "typescript-language-server",
        "args": ["--stdio"],
        "install": "npm install -g typescript-language-server typescript",
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
    "rust": {
        "command": "rust-analyzer",
        "args": [],
        "install": "rustup component add rust-analyzer",
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
    "go": {
        "command": "gopls",
        "args": ["-mode=stdio"],
        "install": "go install golang.org/x/tools/gopls@latest",
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
    "java": {
        "command": "jdtls",  # Eclipse JDT Language Server
        "args": [],
        "install": "See: https://github.com/eclipse/eclipse.jdt.ls",
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
    "cpp": {
        "command": "clangd",
        "args": [],
        "install": "brew install llvm  # or apt-get install clangd",
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
    "bash": {
        "command": "bash-language-server",
        "args": ["start"],
        "install": "npm install -g bash-language-server",
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
    "yaml": {
        "command": "yaml-language-server",
        "args": ["--stdio"],
        "install": "npm install -g yaml-language-server",
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
    "json": {
        "command": "vscode-json-languageserver",
        "args": ["--stdio"],
        "install": "npm install -g vscode-json-languageserver",
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
}


class HeadlessLSPServer:
    """Manages a single LSP server process."""

    def __init__(self, language: str, config: Dict[str, Any]):
        self.language = language
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.started_at: Optional[float] = None
        self.clients: List[str] = []  # Client IDs

    def start(self) -> bool:
        """Start LSP server process."""
        command = self.config["command"]
        args = self.config.get("args", [])

        # Check if command exists
        import shutil

        cmd_path = shutil.which(command)
        if not cmd_path:
            logger.error(f"LSP server '{command}' not found. Install: {self.config.get('install', 'N/A')}")
            return False

        try:
            self.process = subprocess.Popen(
                [cmd_path] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.pid = self.process.pid
            self.started_at = time.time()
            logger.info(f"Started LSP server: {self.language} (PID: {self.pid})")
            return True
        except Exception as e:
            logger.error(f"Failed to start LSP server {self.language}: {e}")
            return False

    def stop(self) -> None:
        """Stop LSP server process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            self.pid = None

    def is_running(self) -> bool:
        """Check if server is running."""
        if not self.process:
            return False
        return self.process.poll() is None


class HeadlessLSPManager:
    """Manages multiple LSP servers in headless mode."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "thegent" / "lsp")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.servers: Dict[str, HeadlessLSPServer] = {}
        self.lockfile = self.cache_dir / "manager.lock"

    def ensure_server(self, language: str) -> Optional[HeadlessLSPServer]:
        """Ensure LSP server is running for language."""
        # Check if already running
        if language in self.servers:
            server = self.servers[language]
            if server.is_running():
                return server
            else:
                # Clean up dead server
                del self.servers[language]

        # Start new server
        config = LSP_SERVERS.get(language)
        if not config:
            logger.error(f"Unknown language: {language}")
            return None

        server = HeadlessLSPServer(language, config)
        if server.start():
            self.servers[language] = server
            self._save_state()
            return server
        return None

    def stop_server(self, language: str) -> None:
        """Stop LSP server for language."""
        if language in self.servers:
            self.servers[language].stop()
            del self.servers[language]
            self._save_state()

    def stop_all(self) -> None:
        """Stop all LSP servers."""
        for server in self.servers.values():
            server.stop()
        self.servers.clear()
        self._save_state()

    def list_servers(self) -> Dict[str, Dict[str, Any]]:
        """List all running servers."""
        return {
            lang: {
                "pid": server.pid,
                "running": server.is_running(),
                "started_at": server.started_at,
                "clients": len(server.clients),
            }
            for lang, server in self.servers.items()
        }

    def _save_state(self) -> None:
        """Save manager state to lockfile."""
        state = {
            "servers": {
                lang: {
                    "pid": server.pid,
                    "started_at": server.started_at,
                }
                for lang, server in self.servers.items()
            },
            "updated_at": time.time(),
        }
        self.lockfile.write_text(json.dumps(state, indent=2))
```

---

## Component 2: JetBrains CLI Integration

### Purpose

Integrate JetBrains IDE Ultimate CLI tools (format, inspect, diff, merge) as complementary services.

### Implementation

**File**: `src/thegent/lsp/jetbrains_cli.py`

```python
"""JetBrains IDE CLI Integration."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any


class JetBrainsCLI:
    """Wrapper for JetBrains IDE CLI tools."""

    def __init__(self, ide_path: Optional[Path] = None):
        """Initialize JetBrains CLI wrapper.

        Args:
            ide_path: Path to IntelliJ IDEA executable (e.g., /Applications/IntelliJ IDEA.app/Contents/MacOS/idea)
                     If None, tries to find in PATH or common locations.
        """
        self.ide_path = self._find_ide(ide_path)

    def _find_ide(self, provided_path: Optional[Path]) -> Optional[Path]:
        """Find IntelliJ IDEA executable."""
        if provided_path and provided_path.exists():
            return provided_path

        # Check PATH
        idea_cmd = shutil.which("idea")
        if idea_cmd:
            return Path(idea_cmd)

        # Check common macOS locations
        macos_paths = [
            Path("/Applications/IntelliJ IDEA.app/Contents/MacOS/idea"),
            Path.home() / "Applications" / "IntelliJ IDEA.app" / "Contents" / "MacOS" / "idea",
        ]
        for path in macos_paths:
            if path.exists():
                return path

        # Check Linux locations
        linux_paths = [
            Path("/opt/idea/bin/idea.sh"),
            Path.home() / ".local" / "share" / "JetBrains" / "Toolbox" / "scripts" / "idea",
        ]
        for path in linux_paths:
            if path.exists():
                return path

        return None

    def format(self, files: list[Path], project_root: Optional[Path] = None) -> Dict[str, Any]:
        """Format files using IntelliJ IDEA formatter.

        Args:
            files: List of files to format
            project_root: Project root directory (optional)

        Returns:
            Dict with 'success', 'stdout', 'stderr'
        """
        if not self.ide_path:
            return {"success": False, "error": "IntelliJ IDEA not found"}

        cmd = [str(self.ide_path), "format"]
        if project_root:
            cmd.extend(["--project", str(project_root)])
        cmd.extend([str(f) for f in files])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def inspect(self, project_root: Path, profile: Optional[str] = None) -> Dict[str, Any]:
        """Run code inspections using IntelliJ IDEA.

        Args:
            project_root: Project root directory
            profile: Inspection profile name (optional)

        Returns:
            Dict with inspection results
        """
        if not self.ide_path:
            return {"success": False, "error": "IntelliJ IDEA not found"}

        cmd = [str(self.ide_path), "inspect", str(project_root)]
        if profile:
            cmd.extend(["--profile", profile])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def diff(self, file1: Path, file2: Path) -> Dict[str, Any]:
        """Show diff between two files.

        Args:
            file1: First file
            file2: Second file

        Returns:
            Dict with diff output
        """
        if not self.ide_path:
            return {"success": False, "error": "IntelliJ IDEA not found"}

        cmd = [str(self.ide_path), "diff", str(file1), str(file2)]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def merge(self, file1: Path, file2: Path, base: Path, output: Path) -> Dict[str, Any]:
        """Merge two files with base.

        Args:
            file1: First file
            file2: Second file
            base: Base file
            output: Output file

        Returns:
            Dict with merge result
        """
        if not self.ide_path:
            return {"success": False, "error": "IntelliJ IDEA not found"}

        cmd = [
            str(self.ide_path),
            "merge",
            str(file1),
            str(file2),
            str(base),
            str(output),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

## Component 3: JetBrains Gateway Integration

### Purpose

Use JetBrains Gateway for headless backend access to full IDE features.

### Implementation

**File**: `src/thegent/lsp/jetbrains_gateway.py`

```python
"""JetBrains Gateway Integration for Headless Backend."""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any


class JetBrainsGateway:
    """Manages JetBrains Gateway for headless backend access."""

    def __init__(self, gateway_path: Optional[Path] = None):
        """Initialize JetBrains Gateway wrapper.

        Args:
            gateway_path: Path to JetBrains Gateway executable
        """
        self.gateway_path = self._find_gateway(gateway_path)
        self.backend_process: Optional[subprocess.Popen] = None

    def _find_gateway(self, provided_path: Optional[Path]) -> Optional[Path]:
        """Find JetBrains Gateway executable."""
        if provided_path and provided_path.exists():
            return provided_path

        # Check common locations
        macos_paths = [
            Path("/Applications/JetBrains Gateway.app/Contents/MacOS/gateway"),
            Path.home() / "Applications" / "JetBrains Gateway.app" / "Contents" / "MacOS" / "gateway",
        ]
        for path in macos_paths:
            if path.exists():
                return path

        return None

    def start_backend(
        self,
        project_root: Path,
        ide_version: str = "latest",
        ssh_host: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start headless backend IDE.

        Args:
            project_root: Project root directory
            ide_version: IDE version (e.g., "2024.1", "latest")
            ssh_host: SSH host for remote backend (optional, local if None)

        Returns:
            Dict with backend connection info
        """
        if not self.gateway_path:
            return {"success": False, "error": "JetBrains Gateway not found"}

        # For local backend, we can use Gateway CLI
        # For remote, we'd use SSH connection
        # This is a simplified version - full implementation would handle SSH

        cmd = [
            str(self.gateway_path),
            "start",
            "--project",
            str(project_root),
            "--ide",
            ide_version,
        ]

        if ssh_host:
            cmd.extend(["--host", ssh_host])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                # Parse connection info from output
                # Gateway returns connection details
                return {
                    "success": True,
                    "connection_info": result.stdout,
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

## CLI Integration

**File**: `src/thegent/main.py` (additions)

```python
lsp_app = typer.Typer(help="Headless LSP server management")
app.add_typer(lsp_app, name="lsp")


@lsp_app.command("start")
def lsp_start(
    language: str = typer.Argument(..., help="Language (python, typescript, rust, go, etc.)"),
):
    """Start headless LSP server for language."""
    from thegent.lsp.headless_manager import HeadlessLSPManager

    manager = HeadlessLSPManager()
    server = manager.ensure_server(language)

    if server:
        console.print(f"[green]Started LSP server: {language} (PID: {server.pid})[/green]")
    else:
        console.print(f"[red]Failed to start LSP server: {language}[/red]")
        raise typer.Exit(1)


@lsp_app.command("stop")
def lsp_stop(
    language: str = typer.Argument(..., help="Language to stop"),
):
    """Stop LSP server for language."""
    from thegent.lsp.headless_manager import HeadlessLSPManager

    manager = HeadlessLSPManager()
    manager.stop_server(language)
    console.print(f"[green]Stopped LSP server: {language}[/green]")


@lsp_app.command("list")
def lsp_list():
    """List all running LSP servers."""
    from thegent.lsp.headless_manager import HeadlessLSPManager
    from rich.table import Table

    manager = HeadlessLSPManager()
    servers = manager.list_servers()

    table = Table(title="Running LSP Servers")
    table.add_column("Language", style="cyan")
    table.add_column("PID", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Uptime", style="white")

    for lang, info in servers.items():
        status = "✅ Running" if info["running"] else "❌ Stopped"
        uptime = f"{int(time.time() - info['started_at'])}s" if info["started_at"] else "N/A"
        table.add_row(lang, str(info["pid"]), status, uptime)

    console.print(table)


@lsp_app.command("format")
def lsp_format(
    files: list[Path] = typer.Argument(..., help="Files to format"),
    project: Path = typer.Option(None, "--project", "-p", help="Project root"),
):
    """Format files using JetBrains formatter."""
    from thegent.lsp.jetbrains_cli import JetBrainsCLI

    cli = JetBrainsCLI()
    result = cli.format(files, project)

    if result["success"]:
        console.print("[green]Files formatted successfully[/green]")
    else:
        console.print(f"[red]Format failed: {result.get('error', result.get('stderr'))}[/red]")
        raise typer.Exit(1)


@lsp_app.command("inspect")
def lsp_inspect(
    project: Path = typer.Argument(..., help="Project root"),
    profile: str = typer.Option(None, "--profile", "-p", help="Inspection profile"),
):
    """Run code inspections using JetBrains."""
    from thegent.lsp.jetbrains_cli import JetBrainsCLI

    cli = JetBrainsCLI()
    result = cli.inspect(project, profile)

    if result["success"]:
        console.print(result["stdout"])
    else:
        console.print(f"[red]Inspection failed: {result.get('error', result.get('stderr'))}[/red]")
        raise typer.Exit(1)
```

---

## Implementation Plan

### Phase 1: Core LSP Manager (Week 1)
- ✅ Implement `HeadlessLSPManager`
- ✅ Support Python, TypeScript, Rust, Go
- ✅ Process lifecycle management
- ✅ State persistence

### Phase 2: JetBrains CLI Integration (Week 1)
- ✅ Implement `JetBrainsCLI` wrapper
- ✅ Format, inspect, diff, merge commands
- ✅ Auto-detect IDE installation

### Phase 3: Gateway Integration (Week 2)
- ⏳ Implement `JetBrainsGateway` wrapper
- ⏳ Local backend support
- ⏳ SSH remote backend support

### Phase 4: CLI & MCP Integration (Week 2)
- ⏳ Add `thegent lsp` commands
- ⏳ Expose via MCP tools
- ⏳ Documentation

---

## Usage Examples

### Start LSP Server
```bash
# Start Python LSP
thegent lsp start python

# Start TypeScript LSP
thegent lsp start typescript

# List running servers
thegent lsp list
```

### Format Files
```bash
# Format Python files
thegent lsp format src/**/*.py --project /path/to/project

# Format TypeScript files
thegent lsp format src/**/*.ts --project /path/to/project
```

### Run Inspections
```bash
# Run code inspections
thegent lsp inspect /path/to/project --profile "Default"
```

---

## References

- **JetBrains CLI**: https://www.jetbrains.com/help/idea/working-with-the-ide-features-from-command-line.html
- **JetBrains Gateway**: https://www.jetbrains.com/help/idea/remote-development-starting-page.html
- **LSP Specification**: https://microsoft.github.io/language-server-protocol/
