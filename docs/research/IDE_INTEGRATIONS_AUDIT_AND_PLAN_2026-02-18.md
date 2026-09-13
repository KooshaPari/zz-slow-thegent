<DONE>
# IDE Integrations Audit & Plan: Serena, JetBrains, Ghostty

**Date**: 2026-02-18
**Status**: Research & Planning
**Goal**: Audit existing IDE integrations and plan comprehensive integration strategy

---

## Executive Summary

**Findings**:
1. **Serena (oraios/serena)**: Already integrated via MCP mount; has JetBrains plugin
2. **Serenade (serenadeai/serenade)**: Voice coding tool with JetBrains plugin (different from Serena)
3. **Ghostty**: Terminal emulator with shell integration (not IDE integration)
4. **Other IDE integrations**: Various tools with JetBrains/VSCode/Cursor support

**Recommendation**: Enhance existing Serena integration, add JetBrains plugin support, and leverage Ghostty's terminal capabilities for IDE workflows.

---

## Part 1: Serena Integration Audit

### Current State

**Serena** (`oraios/serena`) is **already integrated** in thegent:

**Location**: `src/thegent/mcp_server.py`
- Mounted at namespace `serena` via MCP proxy
- Enabled via `THGENT_MCP_MOUNT_SERENA=1`
- Uses `uvx --from git+https://github.com/oraios/serena serena start-mcp-server`

**Capabilities**:
- ✅ Semantic code retrieval (find_symbol, find_referencing_symbols)
- ✅ Symbol-level code editing (insert_after_symbol, etc.)
- ✅ LSP-based backend (30+ languages)
- ✅ JetBrains plugin backend (alternative to LSP)

### Serena JetBrains Plugin

**Plugin**: https://plugins.jetbrains.com/plugin/28946-serena

**Features**:
- Leverages JetBrains IDE code analysis
- Supports all JetBrains IDEs (IntelliJ IDEA, PyCharm, WebStorm, etc.)
- More robust than LSP backend
- Requires IDE to be running

**Integration Status**: ⚠️ **Not yet integrated** in thegent

**How It Works**:
1. Install Serena plugin in JetBrains IDE
2. Plugin exposes Serena MCP server
3. Connect thegent to plugin's MCP server
4. Use JetBrains code analysis instead of LSP

### Integration Opportunities

#### 1. **Auto-Detect JetBrains Plugin**

**Opportunity**: Detect if Serena JetBrains plugin is available and prefer it over LSP backend.

**Implementation**:
```python
# src/thegent/lsp/serena_integration.py
def detect_serena_backend() -> str:
    """Detect available Serena backend (JetBrains plugin or LSP)."""
    # Check if JetBrains plugin MCP server is running
    jetbrains_mcp = check_jetbrains_serena_mcp()
    if jetbrains_mcp:
        return "jetbrains"

    # Fallback to LSP
    return "lsp"
```

#### 2. **Unified Serena Configuration**

**Opportunity**: Single configuration for Serena (LSP vs JetBrains plugin).

**Implementation**:
```python
# src/thegent/config.py
serena_backend: Literal["auto", "lsp", "jetbrains"] = Field(
    default="auto", description="Serena backend: auto-detect, LSP, or JetBrains plugin"
)
```

#### 3. **JetBrains Plugin MCP Bridge**

**Opportunity**: Bridge JetBrains plugin MCP server to thegent's MCP server.

**Implementation**:
- Detect plugin MCP server (usually on localhost:port)
- Mount as sub-provider
- Route Serena tools through plugin

---

## Part 2: Serenade Integration (Voice Coding)

### Overview

**Serenade** (`serenadeai/serenade`) is a **voice coding tool** (different from Serena).

**JetBrains Plugin**: https://github.com/serenadeai/intellij

**Features**:
- Voice-to-code transcription
- Natural language commands
- Works with JetBrains IDEs

**Integration Status**: ❌ **Not integrated** in thegent

### Integration Opportunity

**Use Case**: Voice-driven agent workflows

**Implementation**:
```python
# src/thegent/agents/voice_agent.py
class VoiceAgentRunner(AgentRunner):
    """Agent runner that uses Serenade for voice input."""

    def run(self, prompt: str, ...) -> RunResult:
        # Convert voice to text via Serenade
        # Then run normal agent workflow
        pass
```

**Priority**: Low (voice coding is niche use case)

---

## Part 3: Ghostty Terminal Integration

### Current State

**Ghostty** is a terminal emulator, not an IDE integration tool.

**Shell Integration**: ✅ Available
- Automatic injection for bash, zsh, fish, elvish
- Features: prompt marking, jump_to_prompt, alt+click cursor movement
- Manual setup via `GHOSTTY_RESOURCES_DIR`

**IDE Integration**: ❌ **Not applicable** (Ghostty is a terminal, not an IDE)

### Terminal-Based IDE Workflows

**Opportunity**: Use Ghostty as terminal for IDE workflows.

**Pattern**: Ghostty + Neovim/Helix + agents (as seen in community feedback)

**Integration**:
1. **Terminal Session Management**: Track Ghostty terminal sessions
2. **Agent Terminal Integration**: Run agents in Ghostty terminals
3. **Shell Integration**: Ensure Ghostty shell integration is configured

**Implementation**:
```python
# src/thegent/terminal/ghostty_integration.py
class GhosttyTerminalManager:
    """Manage Ghostty terminal sessions for agents."""

    def spawn_agent_terminal(self, agent_name: str) -> subprocess.Popen:
        """Spawn Ghostty terminal for agent."""
        # Launch Ghostty with agent-specific config
        pass
```

---

## Part 4: Other IDE Integrations Audit

### Tools with IDE Integrations

| Tool | IDE Support | Integration Status |
|------|-------------|-------------------|
| **Serena** | JetBrains, VSCode, Cursor | ✅ Integrated (MCP) |
| **Serenade** | JetBrains, VSCode | ❌ Not integrated |
| **Octocode** | VSCode, Cursor | ✅ Integrated (MCP) |
| **Playwright** | VSCode, Cursor | ✅ Integrated (MCP) |
| **thegent** | Cursor, Claude Code, Codex | ✅ Integrated (MCP) |

### JetBrains-Specific Tools

| Tool | Purpose | Integration |
|------|---------|-------------|
| **IntelliJ IDEA CLI** | Format, inspect, diff, merge | ✅ Integrated (`thegent lsp format`) |
| **JetBrains Gateway** | Remote development | ⏳ Planned |
| **Serena JetBrains Plugin** | Code analysis | ⚠️ Not integrated |

---

## Integration Plan

### Phase 1: Enhance Serena Integration (Week 1)

**Goal**: Add JetBrains plugin support to existing Serena integration.

**Tasks**:
1. **Auto-detect JetBrains plugin**
   - Check if plugin MCP server is running
   - Prefer plugin over LSP backend
   - Fallback to LSP if plugin unavailable

2. **Unified configuration**
   - Add `serena_backend` config option
   - Support `auto`, `lsp`, `jetbrains` modes
   - Update MCP mount logic

3. **Documentation**
   - Guide for installing Serena JetBrains plugin
   - Configuration examples
   - Troubleshooting

**Deliverables**:
- `src/thegent/lsp/serena_integration.py`
- Updated `src/thegent/config.py`
- `docs/guides/SERENA_JETBRAINS_INTEGRATION.md`

### Phase 2: Ghostty Terminal Integration (Week 2)

**Goal**: Integrate Ghostty terminal for agent workflows.

**Tasks**:
1. **Terminal session management**
   - Track Ghostty terminal sessions
   - Spawn agent-specific terminals
   - Manage terminal lifecycle

2. **Shell integration setup**
   - Auto-configure Ghostty shell integration
   - Verify integration is working
   - Provide troubleshooting

3. **Agent terminal workflows**
   - Run agents in Ghostty terminals
   - Support multi-terminal workflows
   - Terminal multiplexing (tmux/Zellij)

**Deliverables**:
- `src/thegent/terminal/ghostty_integration.py`
- `thegent terminal` commands
- `docs/guides/GHOSTTY_INTEGRATION.md`

### Phase 3: Comprehensive IDE Integration (Week 3-4)

**Goal**: Unified IDE integration layer.

**Tasks**:
1. **IDE abstraction layer**
   - Abstract IDE operations (format, inspect, etc.)
   - Support multiple IDEs (JetBrains, VSCode, Cursor)
   - Unified API for agents

2. **IDE detection and configuration**
   - Auto-detect installed IDEs
   - Configure IDE integrations
   - Validate IDE availability

3. **MCP integration**
   - Expose IDE tools via MCP
   - Agent access to IDE features
   - Documentation

**Deliverables**:
- `src/thegent/ide/integration.py`
- `src/thegent/ide/jetbrains.py`
- `src/thegent/ide/vscode.py`
- `docs/guides/IDE_INTEGRATIONS.md`

---

## Implementation Details

### 1. Serena JetBrains Plugin Detection

**File**: `src/thegent/lsp/serena_integration.py`

```python
"""Serena integration with JetBrains plugin support."""

import socket
from typing import Optional, Literal
from thegent.config import ThegentSettings


def detect_serena_backend() -> Literal["lsp", "jetbrains"]:
    """Detect available Serena backend."""
    settings = ThegentSettings()

    if settings.serena_backend == "lsp":
        return "lsp"
    elif settings.serena_backend == "jetbrains":
        return "jetbrains"

    # Auto-detect: Check if JetBrains plugin MCP server is running
    # Default port: 8765 (configurable)
    jetbrains_port = settings.serena_jetbrains_port or 8765

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", jetbrains_port))
        sock.close()

        if result == 0:
            return "jetbrains"
    except Exception:
        pass

    # Fallback to LSP
    return "lsp"


def get_serena_mcp_config() -> dict:
    """Get Serena MCP configuration based on detected backend."""
    backend = detect_serena_backend()

    if backend == "jetbrains":
        # Connect to JetBrains plugin MCP server
        return {
            "command": "mcp-client",
            "args": ["--url", f"http://localhost:{settings.serena_jetbrains_port}"],
        }
    else:
        # Use LSP backend (existing)
        return {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/oraios/serena",
                "serena",
                "start-mcp-server",
                "--context",
                "ide",
            ],
        }
```

### 2. Ghostty Terminal Manager

**File**: `src/thegent/terminal/ghostty_integration.py`

```python
"""Ghostty terminal integration for agent workflows."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional


class GhosttyTerminalManager:
    """Manage Ghostty terminal sessions for agents."""

    def __init__(self):
        self.ghostty_path = self._find_ghostty()

    def _find_ghostty(self) -> Optional[Path]:
        """Find Ghostty executable."""
        # Check PATH
        ghostty_cmd = shutil.which("ghostty")
        if ghostty_cmd:
            return Path(ghostty_cmd)

        # Check macOS app bundle
        macos_paths = [
            Path("/Applications/Ghostty.app/Contents/MacOS/ghostty"),
            Path.home() / "Applications" / "Ghostty.app" / "Contents" / "MacOS" / "ghostty",
        ]
        for path in macos_paths:
            if path.exists():
                return path

        return None

    def spawn_agent_terminal(self, agent_name: str, cwd: Optional[Path] = None) -> subprocess.Popen:
        """Spawn Ghostty terminal for agent."""
        if not self.ghostty_path:
            raise RuntimeError("Ghostty not found")

        # Launch Ghostty with agent-specific config
        cmd = [
            str(self.ghostty_path),
            "--title",
            f"thegent-{agent_name}",
            "--cwd",
            str(cwd) if cwd else str(Path.cwd()),
        ]

        return subprocess.Popen(cmd)

    def ensure_shell_integration(self) -> bool:
        """Ensure Ghostty shell integration is configured."""
        # Check if GHOSTTY_RESOURCES_DIR is set
        # Verify shell integration scripts exist
        # Provide setup instructions if missing
        pass
```

### 3. IDE Abstraction Layer

**File**: `src/thegent/ide/integration.py`

```python
"""Unified IDE integration abstraction."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class IDEIntegration(ABC):
    """Abstract base class for IDE integrations."""

    @abstractmethod
    def format_files(self, files: List[Path], project_root: Optional[Path] = None) -> dict:
        """Format files."""
        pass

    @abstractmethod
    def inspect_project(self, project_root: Path, profile: Optional[str] = None) -> dict:
        """Run code inspections."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if IDE is available."""
        pass


class JetBrainsIntegration(IDEIntegration):
    """JetBrains IDE integration."""

    def __init__(self):
        from thegent.lsp.jetbrains_cli import JetBrainsCLI

        self.cli = JetBrainsCLI()

    def format_files(self, files: List[Path], project_root: Optional[Path] = None) -> dict:
        return self.cli.format(files, project_root)

    def inspect_project(self, project_root: Path, profile: Optional[str] = None) -> dict:
        return self.cli.inspect(project_root, profile)

    def is_available(self) -> bool:
        return self.cli.ide_path is not None


class VSCodeIntegration(IDEIntegration):
    """VSCode integration (future)."""

    def format_files(self, files: List[Path], project_root: Optional[Path] = None) -> dict:
        # Use VSCode CLI
        pass

    def inspect_project(self, project_root: Path, profile: Optional[str] = None) -> dict:
        # Use VSCode extensions
        pass

    def is_available(self) -> bool:
        # Check if code CLI is available
        pass


def get_ide_integration() -> Optional[IDEIntegration]:
    """Get available IDE integration."""
    # Try JetBrains first
    jetbrains = JetBrainsIntegration()
    if jetbrains.is_available():
        return jetbrains

    # Try VSCode
    vscode = VSCodeIntegration()
    if vscode.is_available():
        return vscode

    return None
```

---

## Configuration Updates

### New Config Options

**File**: `src/thegent/config.py`

```python
class ThegentSettings(BaseSettings):
    # ... existing config ...

    # Serena backend selection
    serena_backend: Literal["auto", "lsp", "jetbrains"] = Field(
        default="auto", description="Serena backend: auto-detect, LSP, or JetBrains plugin"
    )

    # Serena JetBrains plugin port
    serena_jetbrains_port: int = Field(default=8765, description="Port for Serena JetBrains plugin MCP server")

    # Ghostty integration
    ghostty_enabled: bool = Field(default=True, description="Enable Ghostty terminal integration")

    # IDE integration
    ide_integration_enabled: bool = Field(default=True, description="Enable IDE integration (format, inspect, etc.)")
```

---

## CLI Commands

### New Commands

**File**: `src/thegent/main.py`

```python
@lsp_app.command("serena-backend")
def lsp_serena_backend() -> None:
    """Show detected Serena backend (LSP or JetBrains plugin)."""
    from thegent.lsp.serena_integration import detect_serena_backend

    backend = detect_serena_backend()
    console.print(f"[green]Serena backend:[/green] {backend}")


@lsp_app.command("serena-jetbrains-setup")
def lsp_serena_jetbrains_setup() -> None:
    """Guide for setting up Serena JetBrains plugin."""
    console.print("[bold]Serena JetBrains Plugin Setup[/bold]")
    console.print("1. Install plugin: https://plugins.jetbrains.com/plugin/28946-serena")
    console.print("2. Enable plugin in JetBrains IDE")
    console.print("3. Configure MCP server port (default: 8765)")
    console.print("4. Run: thegent lsp serena-backend")


terminal_app = typer.Typer(help="Terminal session management")
app.add_typer(terminal_app, name="terminal")


@terminal_app.command("ghostty-check")
def terminal_ghostty_check() -> None:
    """Check Ghostty installation and shell integration."""
    from thegent.terminal.ghostty_integration import GhosttyTerminalManager

    manager = GhosttyTerminalManager()
    if manager.ghostty_path:
        console.print(f"[green]Ghostty found:[/green] {manager.ghostty_path}")
        if manager.ensure_shell_integration():
            console.print("[green]Shell integration:[/green] ✅ Configured")
        else:
            console.print("[yellow]Shell integration:[/yellow] ⚠️ Not configured")
    else:
        console.print("[red]Ghostty not found[/red]")
```

---

## Success Metrics

### Phase 1 (Serena Enhancement)
- ✅ Auto-detect JetBrains plugin
- ✅ Prefer plugin over LSP when available
- ✅ Configuration documented

### Phase 2 (Ghostty Integration)
- ✅ Terminal session management
- ✅ Shell integration auto-setup
- ✅ Agent terminal workflows

### Phase 3 (IDE Integration)
- ✅ Unified IDE abstraction
- ✅ Multiple IDE support
- ✅ MCP exposure

---

## References

- **Serena**: https://github.com/oraios/serena
- **Serena JetBrains Plugin**: https://plugins.jetbrains.com/plugin/28946-serena
- **Serenade**: https://github.com/serenadeai/serenade
- **Ghostty**: https://ghostty.org
- **Ghostty Shell Integration**: https://ghostty.org/docs/features/shell-integration

---

## Related Documents

- `docs/research/HEADLESS_LSP_JETBRAINS_DESIGN_2026-02-18.md` - Headless LSP design
- `docs/research/GSH_ANALYSIS_2026-02-18.md` - gsh analysis
- `docs/guides/GHOSTTY_SETUP_GUIDE_2026-02-18.md` - Ghostty setup guide
