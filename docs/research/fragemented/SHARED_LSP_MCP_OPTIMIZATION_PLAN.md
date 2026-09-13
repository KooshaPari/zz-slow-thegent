<DONE>
# Shared LSP/MCP Process Optimization Plan

**Date:** 2026-02-18  
**Priority:** P1  
**Status:** Planning  
**Goal:** Reduce memory usage from 16-32GB (16 sessions × 1-2GB each) to ~2-4GB (1 shared LSP + 1 shared MCP per project)

## Problem Statement

Currently, each thegent session spawns its own LSP/MCP processes:

- **16 active sessions** = 16 × (1-2 GB) = **16-32 GB memory usage**
- Each session independently starts:
  - LSP servers (pyright, typescript-language-server, etc.)
  - MCP servers (context7-mcp, octocode-mcp, etc.)
  - Node.js processes for tooling

**User Request:** Share LSP/MCP processes across sessions:

- **One shared LSP per project** (or system-wide if possible)
- **One shared MCP server per project**
- Only separate when necessary (e.g., different LSP configs)

## Architecture Design

### Current Architecture (Per-Session)

```
Session 1 → LSP Process (1-2GB) + MCP Process (100-500MB)
Session 2 → LSP Process (1-2GB) + MCP Process (100-500MB)
Session 3 → LSP Process (1-2GB) + MCP Process (100-500MB)
...
Session N → LSP Process (1-2GB) + MCP Process (100-500MB)

Total: N × (1-2.5GB) = 16-40GB for 16 sessions
```

### Proposed Architecture (System-Wide Shared - Default)

**Priority: System-wide first, scope down only when necessary**

```
System-Wide (All Projects)
  ├─ Shared LSP Server (1-2GB) ← All sessions from all projects connect
  ├─ Shared MCP Server (100-500MB) ← All sessions from all projects connect
  │
  ├─ Project A Sessions → Connect to system-wide LSP/MCP
  ├─ Project B Sessions → Connect to system-wide LSP/MCP
  ├─ Project C Sessions → Connect to system-wide LSP/MCP
  └─ Project N Sessions → Connect to system-wide LSP/MCP

Total: ~2-2.5GB (shared) + N × (10-50MB per session) = ~2.5-3.5GB for 16 sessions
```

**Scoping Down (Per-Project) - Only When Needed:**

```
Project Root (/Users/kooshapari/temp-PRODVERCEL/485/kush)
  ├─ Shared LSP Server (1-2GB) ← Only this project's sessions
  ├─ Shared MCP Server (100-500MB) ← Only this project's sessions
  │
  └─ Sessions → Connect to project-scoped LSP/MCP

Use when:
- Different LSP/MCP configurations needed per project
- Project isolation required (security/compliance)
- Different language versions needed
- Project-specific MCP servers required
```

## Implementation Strategy

### Phase 1: System-Wide Shared MCP Server (Default)

**Approach:** Use existing process-compose infrastructure

1. **Single System-Wide MCP Server**
   - Start one MCP server via `process-compose` for entire system
   - All sessions from all projects connect to same MCP server
   - Use system-wide lockfile: `~/.cache/thegent/mcp/system.lock`

2. **Session Connection**
   - Sessions check for existing system-wide MCP server (via lockfile/socket)
   - If exists: connect to existing server
   - If not: start new server and register

3. **Lifecycle Management**
   - MCP server stays alive as long as any session is active (any project)
   - Auto-shutdown when last session closes (across all projects)
   - Health checks and auto-restart

4. **Scoping Down (Per-Project) - Only When Needed**
   - Check for project-specific requirements:
     - Different MCP configuration
     - Project isolation needed
     - Different MCP server version
   - If needed: Use project-scoped server: `~/.cache/thegent/mcp/{project_hash}.lock`

**Files to Modify:**

- `thegent/src/thegent/mcp_manage.py` - Add system-wide server detection
- `thegent/src/thegent/agents/cliproxy_manager.py` - Connect to shared server
- Add lockfile mechanism: `~/.cache/thegent/mcp/system.lock` (default)

### Phase 2: System-Wide Shared LSP Server (Default)

**Approach:** LSP servers support multiple clients via Language Server Protocol

1. **Single System-Wide LSP Server**
   - Start one LSP server for entire system
   - LSP servers support multiple clients (standard LSP feature)
   - Use system-wide workspace or multi-root workspace support

2. **Client Connection**
   - Sessions from all projects connect as LSP clients to shared server
   - Each session maintains its own client connection
   - LSP server handles multiple concurrent requests from different projects

3. **LSP Server Types:**
   - **pyright**: Supports multiple clients (via stdio/HTTP)
   - **typescript-language-server**: Supports multiple clients
   - **Other LSPs**: Check multi-client support

4. **Scoping Down (Per-Project) - Only When Needed**
   - Check for project-specific requirements:
     - Different language versions (Python 3.11 vs 3.12)
     - Different LSP configuration
     - Project isolation needed
   - If needed: Use project-scoped server: `~/.cache/thegent/lsp/{project_hash}.lock`

**Files to Modify:**

- `thegent/src/thegent/agents/cliproxy_manager.py` - LSP client connection
- Add LSP server manager: `thegent/src/thegent/lsp_manager.py`
- Add lockfile mechanism: `~/.cache/thegent/lsp/system.lock` (default)

### Phase 3: Scoping Logic

**Key:** System-wide by default, scope down only when necessary

```python
import hashlib
from pathlib import Path
from typing import Optional


def get_server_scope(project_root: Optional[Path] = None) -> tuple[str, Path]:
    """
    Determine server scope (system-wide or project-scoped).

    Returns:
        (scope_type, lockfile_path)
        scope_type: 'system' or 'project'
    """
    # Default: system-wide
    system_lockfile = Path.home() / ".cache" / "thegent" / "mcp" / "system.lock"

    # Check if project-specific requirements exist
    if project_root:
        # Check for project-specific config
        project_config = project_root / ".thegent" / "isolate_servers"
        if project_config.exists():
            # Project requires isolation
            project_key = hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()[:16]
            project_lockfile = Path.home() / ".cache" / "thegent" / "mcp" / f"{project_key}.lock"
            return ("project", project_lockfile)

    # Default: system-wide
    return ("system", system_lockfile)
```

**Benefits:**

- Different projects get separate servers (isolation)
- Same project shares server (efficiency)
- System-wide option available (single server for all)

## Implementation Details

### Shared MCP Server Manager (System-Wide First)

```python
# thegent/src/thegent/shared_mcp_manager.py

from pathlib import Path
import hashlib
import json
import time
import os
from typing import Optional, Tuple


def get_server_scope(project_root: Optional[Path] = None) -> Tuple[str, Path]:
    """
    Determine server scope (system-wide or project-scoped).
    Default: system-wide. Scope down only if project requires isolation.

    Returns:
        (scope_type, lockfile_path)
    """
    cache_dir = Path.home() / ".cache" / "thegent" / "mcp"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Default: system-wide
    system_lockfile = cache_dir / "system.lock"

    # Check if project requires isolation
    if project_root:
        project_config = project_root / ".thegent" / "isolate_servers"
        if project_config.exists():
            # Project requires isolation - scope down
            project_key = hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()[:16]
            project_lockfile = cache_dir / f"{project_key}.lock"
            return ("project", project_lockfile)

    # Default: system-wide
    return ("system", system_lockfile)


def ensure_shared_mcp_server(project_root: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
    """
    Ensure shared MCP server is running (system-wide by default).
    Returns: (is_new_server, server_url_or_error)
    """
    scope_type, lockfile = get_server_scope(project_root)

    # Check if server already running
    if lockfile.exists():
        try:
            with open(lockfile, "r") as f:
                data = json.load(f)
                pid = data.get("pid")
                port = data.get("port", 3847)

                # Check if process still alive
                try:
                    os.kill(pid, 0)  # Check if process exists
                    return False, f"http://127.0.0.1:{port}/mcp"
                except OSError:
                    # Process dead, remove stale lockfile
                    lockfile.unlink()
        except Exception:
            lockfile.unlink()

    # Start new server (system-wide)
    from thegent.mcp_manage import mcp_up

    success, message = mcp_up()
    if not success:
        return False, message

    # Create lockfile
    import subprocess

    # Get process-compose PID
    # (Implementation depends on how mcp_up works)

    lockfile.write_text(
        json.dumps(
            {
                "pid": os.getpid(),  # Or actual server PID
                "port": 3847,
                "scope": scope_type,
                "project_root": str(project_root) if project_root else None,
                "started_at": time.time(),
            }
        )
    )

    return True, f"http://127.0.0.1:3847/mcp"
```

### Shared LSP Server Manager (System-Wide First)

```python
# thegent/src/thegent/shared_lsp_manager.py

from pathlib import Path
import hashlib
import json
import subprocess
import os
from typing import Optional, Dict, Tuple

LSP_SERVERS = {
    "python": {
        "command": "pyright-langserver",
        "args": ["--stdio"],
        "supports_multi_client": True,
        "supports_multi_root": True,  # Can handle multiple project roots
    },
    "typescript": {
        "command": "typescript-language-server",
        "args": ["--stdio"],
        "supports_multi_client": True,
        "supports_multi_root": True,
    },
}


def get_lsp_server_scope(project_root: Optional[Path] = None, language: str = "python") -> Tuple[str, Path]:
    """
    Determine LSP server scope (system-wide or project-scoped).
    Default: system-wide. Scope down only if project requires isolation.

    Returns:
        (scope_type, lockfile_path)
    """
    cache_dir = Path.home() / ".cache" / "thegent" / "lsp"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Default: system-wide
    system_lockfile = cache_dir / "system" / f"{language}.lock"
    system_lockfile.parent.mkdir(parents=True, exist_ok=True)

    # Check if project requires isolation
    if project_root:
        # Check for project-specific requirements
        project_config = project_root / ".thegent" / "isolate_servers"
        if project_config.exists():
            # Check if language version differs
            # (e.g., Python 3.11 vs 3.12 might need separate servers)
            # For now, scope down if isolation requested
            project_key = hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()[:16]
            project_lockfile = cache_dir / project_key / f"{language}.lock"
            project_lockfile.parent.mkdir(parents=True, exist_ok=True)
            return ("project", project_lockfile)

    # Default: system-wide
    return ("system", system_lockfile)


def ensure_shared_lsp_server(project_root: Optional[Path] = None, language: str = "python") -> Optional[str]:
    """
    Ensure shared LSP server is running (system-wide by default).
    Returns: stdio pipe path or socket path or None
    """
    scope_type, lockfile = get_lsp_server_scope(project_root, language)
    socket_path = lockfile.parent / f"{language}.sock"  # Unix domain socket

    # Check if server already running
    if lockfile.exists() and socket_path.exists():
        try:
            with open(lockfile, "r") as f:
                data = json.load(f)
                pid = data.get("pid")

                try:
                    os.kill(pid, 0)  # Check if process exists
                    return str(socket_path)
                except OSError:
                    # Process dead, remove stale files
                    lockfile.unlink()
                    socket_path.unlink(missing_ok=True)
        except Exception:
            lockfile.unlink(missing_ok=True)

    # Start new LSP server (system-wide)
    lsp_config = LSP_SERVERS.get(language)
    if not lsp_config:
        return None

    # Start server with Unix domain socket for multi-client support
    # (Implementation depends on LSP server capabilities)
    # System-wide server can handle multiple project roots

    return str(socket_path)
```

## Configuration Options

### Environment Variables

```bash
# Enable shared LSP/MCP servers (default: true)
THGENT_SHARED_LSP=1
THGENT_SHARED_MCP=1

# Server scope (default: system-wide)
THGENT_SHARED_SCOPE=system  # "system" (default) or "project"

# LSP server timeout (seconds)
THGENT_LSP_TIMEOUT=300

# MCP server timeout (seconds)
THGENT_MCP_TIMEOUT=300

# Force project isolation (overrides default system-wide)
THGENT_FORCE_PROJECT_ISOLATION=0  # Set to 1 to force per-project servers
```

### Config File

```yaml
# ~/.config/thegent/config.yaml
shared_servers:
  enabled: true
  scope: "system" # "system" (default) or "project"
  lsp:
    enabled: true
    timeout: 300
    system_wide: true # Default: true
  mcp:
    enabled: true
    timeout: 300
    system_wide: true # Default: true
```

### Project-Level Override

To force project isolation for a specific project, create:

```bash
# .thegent/isolate_servers
# This file forces project-scoped servers for this project
# Reasons: Different config, isolation needed, etc.
```

**When to Use Project Isolation:**

- Different language versions (Python 3.11 vs 3.12)
- Different LSP/MCP configurations
- Security/compliance isolation requirements
- Project-specific MCP servers needed

## Migration Path

### Step 1: Add Shared Server Detection (Non-Breaking)

- Add shared server detection alongside existing per-session spawning
- Default: Use shared if available, fallback to per-session
- No breaking changes

### Step 2: Make Shared Default (Opt-Out)

- Default to shared servers
- Add `--no-shared` flag for per-session spawning
- Update documentation

### Step 3: Remove Per-Session Spawning (Future)

- Remove per-session spawning code
- Shared servers become only option
- Simplify codebase

## Testing Strategy

1. **Unit Tests**
   - Test shared server detection
   - Test lockfile management
   - Test multi-client connection

2. **Integration Tests**
   - Test multiple sessions connecting to shared server
   - Test server lifecycle (start/stop)
   - Test project isolation

3. **Performance Tests**
   - Measure memory usage reduction
   - Measure startup time impact
   - Measure request latency

## Expected Benefits

### Memory Reduction

- **Before:** 16 sessions × 1.5GB = **24GB**
- **After:** 2GB (shared) + 16 × 20MB = **2.3GB**
- **Savings:** ~**90% reduction** (21.7GB saved)

### Startup Time

- **Before:** Each session starts LSP/MCP (~5-10s)
- **After:** First session starts server (~5-10s), others connect (~0.1s)
- **Savings:** ~**90% faster** for subsequent sessions

### Resource Efficiency

- Fewer processes to manage
- Better CPU utilization
- Lower system overhead

## Risks & Mitigations

### Risk 1: Server Crash Affects All Sessions

**Mitigation:**

- Health checks and auto-restart
- Graceful degradation to per-session fallback
- Session-level error handling

### Risk 2: LSP Server Doesn't Support Multi-Client

**Mitigation:**

- Check LSP server capabilities
- Fallback to per-session for unsupported servers
- Document limitations

### Risk 3: Project Isolation Issues

**Mitigation:**

- Use project root hash as isolation key
- Verify workspace root matches
- Add project validation

## Implementation Priority

1. **P0:** System-Wide Shared MCP Server (easier, high impact, default)
2. **P1:** System-Wide Shared LSP Server (more complex, higher impact, default)
3. **P2:** Project-scoped fallback (only when isolation needed)

## Next Steps

1. ✅ **Research:** Document current architecture
2. ⏭️ **Design:** Finalize shared server architecture
3. ⏭️ **Implement:** Phase 1 - Shared MCP Server
4. ⏭️ **Test:** Verify memory reduction
5. ⏭️ **Implement:** Phase 2 - Shared LSP Server
6. ⏭️ **Optimize:** Fine-tune based on usage

## References

- LSP Specification: https://microsoft.github.io/language-server-protocol/
- MCP Specification: https://modelcontextprotocol.io/
- Process Management: `thegent/src/thegent/mcp_manage.py`
- Prune Utils: `thegent/src/thegent/prune_utils.py`
