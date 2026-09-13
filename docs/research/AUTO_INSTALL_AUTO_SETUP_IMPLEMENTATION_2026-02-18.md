<DONE>
# Auto-Install & Auto-Setup Implementation Summary

**Date**: 2026-02-18
**Status**: Complete
**Philosophy**: Instructions as last resort; auto-install/auto-configure everything possible

---

## Implementation Philosophy

**Core Principle**: Minimize human interaction. Auto-install, auto-configure, auto-detect. Only show instructions when automation isn't possible.

**Key Behaviors**:

1. **Auto-install missing dependencies** (LSP servers, tools)
2. **Auto-detect configurations** (JetBrains IDE, Serena backend, Ghostty)
3. **Auto-setup integrations** (shell integration, plugin detection)
4. **Instructions only as last resort** (when automation fails or requires user action)

---

## What Was Implemented

### 1. Auto-Install LSP Servers (`src/thegent/lsp/auto_install.py`)

**Features**:

- ✅ Auto-install missing LSP servers (Python, TypeScript, Rust, Go, etc.)
- ✅ Check if already installed before installing
- ✅ Platform-specific install commands (macOS, Linux)
- ✅ Silent installation (no prompts)

**Usage**:

```python
# Auto-install if missing
ensure_lsp_server_installed("python", auto_install=True)

# Install all servers
auto_install_all_lsp_servers(auto_confirm=True)
```

**Integration**: Called automatically when starting LSP servers if missing.

### 2. Auto-Setup IDE Integrations (`src/thegent/ide/auto_setup.py`)

**Features**:

- ✅ Auto-detect JetBrains IDE installation
- ✅ Auto-detect Serena JetBrains plugin
- ✅ Auto-detect Ghostty shell integration
- ✅ Unified auto-setup for all integrations

**Usage**:

```python
# Auto-setup all integrations
results = auto_setup_all()

# Individual setup
auto_setup_jetbrains_integration()
auto_setup_serena_jetbrains_plugin()
auto_setup_ghostty_shell_integration()
```

### 3. Auto-Init on Startup (`src/thegent/ide/auto_init.py`)

**Features**:

- ✅ Runs automatically when thegent MCP server starts
- ✅ Initializes all IDE integrations
- ✅ Ensures LSP servers are ready
- ✅ Non-blocking (failures are logged but don't stop startup)

**Integration**: Called in `thegent_lifespan()` function in `mcp_server.py`.

### 4. Enhanced LSP Manager

**Updates**:

- ✅ Auto-install LSP servers when starting if missing
- ✅ Respects `THGENT_LSP_AUTO_INSTALL` config
- ✅ Falls back to instructions only if auto-install fails

### 5. New CLI Commands

**Added**:

- ✅ `thegent lsp auto-setup` - Auto-setup all integrations
- ✅ `thegent lsp start` - Auto-installs missing servers by default
- ✅ `thegent lsp serena-backend` - Auto-detects backend
- ✅ `thegent lsp serena-jetbrains-setup` - Auto-detects and guides if needed

---

## Configuration

### New Config Options

**File**: `src/thegent/config.py`

```python
# Auto-install LSP servers
lsp_auto_install: bool = True  # THGENT_LSP_AUTO_INSTALL

# IDE integration
ide_integration_enabled: bool = True  # THGENT_IDE_INTEGRATION_ENABLED
ghostty_enabled: bool = True  # THGENT_GHOSTTY_ENABLED

# Serena backend
serena_backend: Literal["auto", "lsp", "jetbrains"] = "auto"  # THGENT_SERENA_BACKEND
serena_jetbrains_port: int = 8765  # THGENT_SERENA_JETBRAINS_PORT
```

---

## Auto-Installation Flow

### LSP Server Startup

```
User: thegent lsp start python
  ↓
Check if pyright-langserver exists
  ↓
Not found? → Auto-install (npm install -g pyright)
  ↓
Installation succeeds? → Start server
  ↓
Installation fails? → Show error + manual install instructions (last resort)
```

### IDE Integration Startup

```
thegent serve (MCP server starts)
  ↓
auto_init_on_startup() runs
  ↓
Auto-detect JetBrains IDE
Auto-detect Serena backend
Auto-detect Ghostty integration
  ↓
Log results (success/failure)
  ↓
Continue startup (non-blocking)
```

---

## Supported Auto-Installations

### LSP Servers

| Language   | Install Command                                                | Platform          |
| ---------- | -------------------------------------------------------------- | ----------------- |
| Python     | `npm install -g pyright`                                       | All               |
| TypeScript | `npm install -g typescript-language-server typescript`         | All               |
| Rust       | `rustup component add rust-analyzer`                           | All               |
| Go         | `go install golang.org/x/tools/gopls@latest`                   | All               |
| C++        | `brew install llvm` (macOS) / `apt-get install clangd` (Linux) | Platform-specific |
| Bash       | `npm install -g bash-language-server`                          | All               |
| YAML       | `npm install -g yaml-language-server`                          | All               |
| JSON       | `npm install -g vscode-json-languageserver`                    | All               |

### IDE Integrations

| Integration               | Auto-Detection             | Auto-Configuration             |
| ------------------------- | -------------------------- | ------------------------------ |
| JetBrains IDE             | ✅ PATH + common locations | ✅ CLI access                  |
| Serena JetBrains Plugin   | ✅ Port check (8765)       | ✅ Backend selection           |
| Ghostty Shell Integration | ✅ `GHOSTTY_RESOURCES_DIR` | ⚠️ Manual setup (instructions) |

---

## When Instructions Are Shown

**Instructions are only shown when**:

1. Auto-installation fails (network error, permission denied, etc.)
2. User action required (install JetBrains plugin manually)
3. Configuration requires user input (API keys, auth tokens)

**Examples**:

- ✅ **Auto-install succeeds**: No output, server starts
- ⚠️ **Auto-install fails**: Error message + manual install command
- ⚠️ **Plugin not detected**: Setup guide with steps
- ⚠️ **Auth required**: OAuth flow or API key prompt

---

## Usage Examples

### Auto-Setup Everything

```bash
# Auto-setup all IDE integrations and install LSP servers
thegent lsp auto-setup

# Output:
# ┌─────────────────────────────────────────┐
# │         Setup Status                    │
# ├──────────────────┬──────────┬──────────┤
# │ Integration      │ Status   │ Details  │
# ├──────────────────┼──────────┼──────────┤
# │ JetBrains IDE    │ ✅ Config│ CLI OK   │
# │ Serena Plugin    │ ✅ Config│ jetbrains │
# │ Ghostty          │ ✅ Config│ Active   │
# │ LSP Servers      │ ✅ 8/9   │ 8 ready  │
# └──────────────────┴──────────┴──────────┘
```

### Start LSP Server (Auto-Installs)

```bash
# Auto-installs pyright if missing, then starts server
thegent lsp start python

# Output (if missing):
# Installing Python LSP (pyright)...
# ✅ Successfully installed Python LSP (pyright)
# ✅ Started LSP server: python (PID: 1234)
```

### Check Serena Backend (Auto-Detects)

```bash
# Auto-detects backend (LSP or JetBrains plugin)
thegent lsp serena-backend

# Output:
# ✅ Serena backend: jetbrains
# JetBrains plugin port: 8765
```

---

## Implementation Details

### Auto-Install Logic

**File**: `src/thegent/lsp/auto_install.py`

```python
def ensure_lsp_server_installed(language: str, auto_install: bool = True) -> bool:
    """Ensure LSP server is installed, auto-installing if needed."""
    # 1. Check if already installed
    if check_command_available(check_cmd):
        return True

    # 2. Auto-install if enabled
    if auto_install:
        return auto_install_lsp_server(language, auto_confirm=True)

    # 3. Return False (will show instructions)
    return False
```

### Auto-Init Hook

**File**: `src/thegent/mcp_server.py`

```python
@lifespan
async def thegent_lifespan(mcp_app: FastMCP):
    # ... other startup ...

    # Auto-initialize IDE integrations
    try:
        auto_init_on_startup()
        _log.info("IDE integrations auto-initialized")
    except Exception as e:
        _log.debug("IDE auto-init failed (non-critical): %s", e)
```

---

## Benefits

### 1. **Zero-Config Experience**

- New users: Run `thegent lsp start python` → Works immediately
- Missing dependencies: Auto-installed silently
- No manual setup required

### 2. **Proactive Setup**

- Startup auto-initializes integrations
- LSP servers auto-install when needed
- Backend auto-detection (Serena)

### 3. **Instructions as Last Resort**

- Only shown when automation fails
- Clear, actionable steps
- Minimal user intervention

---

## Future Enhancements

### 1. **Auto-Install JetBrains Plugin**

- Detect plugin marketplace API
- Auto-install via CLI (if possible)
- Currently: Manual install (instructions)

### 2. **Auto-Configure Ghostty**

- Auto-add shell integration to `.zshrc`
- Backup existing config
- Verify integration works

### 3. **Auto-Auth Flows**

- OAuth auto-redirect
- Token refresh automation
- Minimize auth prompts

---

## Files Created/Modified

### New Files

- `src/thegent/lsp/auto_install.py` - Auto-installation logic
- `src/thegent/ide/auto_setup.py` - Auto-setup for IDE integrations
- `src/thegent/ide/auto_init.py` - Startup initialization
- `src/thegent/ide/__init__.py` - IDE module exports

### Modified Files

- `src/thegent/lsp/headless_manager.py` - Auto-install integration
- `src/thegent/config.py` - New config options
- `src/thegent/mcp_server.py` - Auto-init hook
- `src/thegent/main.py` - New CLI commands

---

## Testing

### Test Auto-Install

```bash
# Remove pyright
npm uninstall -g pyright

# Start Python LSP (should auto-install)
thegent lsp start python

# Verify installation
which pyright-langserver
```

### Test Auto-Setup

```bash
# Run auto-setup
thegent lsp auto-setup

# Verify all integrations detected
thegent lsp serena-backend
```

---

## References

- **Design**: `docs/research/IDE_INTEGRATIONS_AUDIT_AND_PLAN_2026-02-18.md`
- **Summary**: `docs/research/IDE_INTEGRATIONS_SUMMARY_2026-02-18.md`
- **Headless LSP**: `docs/research/HEADLESS_LSP_JETBRAINS_DESIGN_2026-02-18.md`
