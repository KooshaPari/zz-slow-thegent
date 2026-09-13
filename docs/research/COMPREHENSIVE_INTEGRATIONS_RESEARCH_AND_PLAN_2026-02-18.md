<DONE>
# Comprehensive Integrations Research & Plan: JetBrains, Hooks, MCP, Skills, Shell, OS

**Date**: 2026-02-18
**Status**: Research Complete, Plan Ready
**Scope**: JetBrains plugins, hooks/MCP/skills, zsh/shell, OS-level enhancements for AX/UX/DX

---

## Executive Summary

Comprehensive research and integration plan covering:

1. **JetBrains Plugins**: MCP Server, MCP Language Service Tools, DevoxxGenie, Serena
2. **Hooks/MCP/Skills**: Enhanced hook system, MCP integrations, skills context files
3. **Zsh/Shell Enhancements**: Productivity plugins, optimization, developer experience
4. **OS-Level Enhancements**: macOS automation, system-level productivity tools

**Goal**: Maximize automation, minimize manual configuration, optimize AX/UX/DX across all layers.

---

## Part 1: JetBrains Plugins Research & Integration Plan

### 1.1 Essential JetBrains Plugins for AI/Agent Development

#### ✅ **MCP Server Plugin** (Official JetBrains)

**Plugin ID**: 26071
**URL**: https://plugins.jetbrains.com/plugin/26071-mcp-server
**Status**: ⚠️ Not yet integrated

**Features**:

- 35+ built-in MCP tools for IDE automation
- File and project management
- Debugger integration (breakpoint control)
- Terminal command execution (with safety controls)
- Version control (status, commit search)
- Code analysis and error detection
- Extensible plugin architecture
- Works with all JetBrains IDEs

**Integration Priority**: 🔴 **HIGH** - Official plugin, comprehensive IDE access

**Integration Plan**:

1. Auto-detect plugin installation
2. Connect to plugin's MCP server (default port: varies)
3. Mount as MCP provider in thegent
4. Expose tools via `thegent mcp` namespace

**Auto-Installation**:

- Check if plugin installed via IDE plugin manager API
- Provide installation instructions if missing
- Auto-configure MCP connection when plugin detected

#### ✅ **MCP Language Service Tools Plugin** (Community)

**Plugin ID**: 27888
**URL**: https://plugins.jetbrains.com/plugin/27888-mcp-language-service-tools
**GitHub**: https://github.com/justin1291/mcp-idea-lsp
**Status**: ❌ Not integrated

**Features**:

- Extends MCP Server with LSP capabilities
- Symbol extraction (`get_symbols_in_file`)
- Go-to-definition (`find_symbol_definition`)
- Find references (`find_symbol_references`)
- Hover info (`get_hover_info`)
- Multi-language support (Java, Kotlin, Python, JS/TS, etc.)
- Extensible architecture (easy to add languages)

**Integration Priority**: 🟡 **MEDIUM** - Enhances MCP Server with LSP features

**Integration Plan**:

1. Install after MCP Server plugin
2. Auto-detect language support
3. Expose LSP tools via MCP
4. Prefer over Serena LSP backend when available

#### ✅ **Serena JetBrains Plugin** (Already Planned)

**Plugin ID**: 28946
**URL**: https://plugins.jetbrains.com/plugin/28946-serena
**Status**: ⚠️ Partially integrated (detection only)

**Features**:

- Semantic code retrieval
- Symbol-level code editing
- Leverages JetBrains code analysis
- Supports all JetBrains IDEs

**Integration Priority**: 🔴 **HIGH** - Already partially integrated

**Next Steps**:

1. ✅ Auto-detect plugin (done)
2. ⏳ Auto-install plugin (if marketplace API available)
3. ⏳ Auto-configure MCP connection
4. ⏳ Health monitoring

#### 🔵 **DevoxxGenie Plugin** (MCP Bridge)

**Status**: ❌ Not integrated

**Features**:

- Bridge between IDE and MCP ecosystem
- Invoke AI-driven actions from IDE
- Workflow integration

**Integration Priority**: 🟢 **LOW** - Niche use case, Serena covers most needs

### 1.2 Recommended JetBrains Plugins for Developer Experience

#### Productivity Plugins

- **GitToolBox**: Enhanced Git integration
- **Rainbow Brackets**: Visual bracket matching
- **String Manipulation**: String operations
- **Key Promoter X**: Keyboard shortcut learning
- **Presentation Assistant**: Presentation mode

#### Code Quality Plugins

- **SonarLint**: Code quality analysis
- **Checkstyle-IDEA**: Java code style
- **SpotBugs**: Bug detection
- **ArchUnit**: Architecture testing

#### AI/Agent Plugins

- **GitHub Copilot**: AI code completion (if available)
- **Codeium**: AI code completion
- **Tabnine**: AI autocomplete

**Integration Strategy**: Auto-detect and recommend, don't force install

### 1.3 JetBrains Plugin Auto-Installation Plan

**Phase 1: Core MCP Plugins** (Week 1)

1. ✅ MCP Server Plugin detection
2. ✅ MCP Language Service Tools detection
3. ✅ Serena JetBrains Plugin detection (already done)
4. ⏳ Auto-installation via IDE plugin manager API (if available)

**Phase 2: Integration** (Week 2)

1. Connect to MCP Server plugin
2. Mount MCP tools in thegent
3. Expose via `thegent mcp` commands
4. Health monitoring

**Phase 3: Enhancement** (Week 3)

1. Auto-configure plugin settings
2. Plugin health checks
3. Fallback strategies

---

## Part 2: Hooks, MCP, Skills, Context Files Research & Plan

### 2.1 Hooks System Enhancement

**Current State**: Comprehensive hook system with 100+ hooks

**Enhancement Opportunities**:

#### 1. **MCP Hook Integration**

**Opportunity**: Expose hook events via MCP for agent access

**Implementation**:

```python
# src/thegent/hooks/mcp_exporter.py
class HookMCPExporter:
    """Export hook events via MCP."""

    def register_hook_tool(self, hook_name: str):
        """Register hook as MCP tool."""
        # Agents can trigger hooks via MCP
        pass
```

**Benefits**:

- Agents can trigger hooks programmatically
- Hook status visible to agents
- Hook results accessible via MCP

#### 2. **Hook Context Files**

**Opportunity**: Store hook context in structured files for agent access

**Implementation**:

```python
# hooks/context/hook-context.json
{
    "hook_name": "quality-gate",
    "last_run": "2026-02-18T06:00:00Z",
    "status": "passed",
    "results": {...},
    "next_run": "2026-02-18T06:10:00Z",
}
```

**Benefits**:

- Agents can query hook status
- Historical hook data
- Predictive hook execution

#### 3. **Skills Integration with Hooks**

**Opportunity**: Skills can trigger hooks, hooks can inform skills

**Implementation**:

```python
# skills/thegent-skills/hooks-integration.md
## Hook Integration

Skills can:
- Trigger hooks: `thegent hooks trigger quality-gate`
- Query hook status: `thegent hooks status quality-gate`
- Subscribe to hook events: `thegent hooks subscribe quality-gate`
```

### 2.2 MCP Enhancements

#### 1. **MCP Resource: Hook Status**

**Opportunity**: Expose hook status as MCP resource

**Implementation**:

```python
# MCP resource: thegent://hooks/status
{"hooks": [{"name": "quality-gate", "status": "passed", "last_run": "..."}, ...]}
```

#### 2. **MCP Tool: Trigger Hook**

**Opportunity**: Allow agents to trigger hooks via MCP

**Implementation**:

```python
# MCP tool: thegent_trigger_hook
{
    "name": "thegent_trigger_hook",
    "description": "Trigger a thegent hook",
    "inputSchema": {"hook_name": "string", "args": "object"},
}
```

#### 3. **MCP Tool: Query Hook Results**

**Opportunity**: Agents can query hook execution results

**Implementation**:

```python
# MCP tool: thegent_hook_results
{
    "name": "thegent_hook_results",
    "description": "Get hook execution results",
    "inputSchema": {"hook_name": "string", "since": "datetime"},
}
```

### 2.3 Skills System Enhancements

#### 1. **Skills Context Files**

**Current**: Skills defined in `skills/*/SKILL.md`

**Enhancement**: Add structured context files

**Implementation**:

```json
// skills/thegent-skills/context.json
{
  "skill_id": "thegent-skills",
  "version": "1.0.0",
  "capabilities": [
    "agent_orchestration",
    "work_stream_management",
    "hook_integration"
  ],
  "dependencies": ["thegent"],
  "mcp_tools": ["thegent_do_next", "thegent_work_stream_claim"],
  "hooks": ["quality-gate", "spec-verifier"]
}
```

#### 2. **Skills Auto-Discovery**

**Opportunity**: Auto-discover skills from context files

**Implementation**:

```python
# src/thegent/skills/discovery.py
def discover_skills() -> List[Skill]:
    """Auto-discover skills from context files."""
    skills = []
    for skill_dir in Path("skills").iterdir():
        context_file = skill_dir / "context.json"
        if context_file.exists():
            skills.append(Skill.from_context(context_file))
    return skills
```

#### 3. **Skills MCP Integration**

**Opportunity**: Expose skills via MCP

**Implementation**:

```python
# MCP resource: thegent://skills/list
{"skills": [{"id": "thegent-skills", "name": "Thegent Skills", "capabilities": [...], "mcp_tools": [...]}]}
```

### 2.4 Context Files & Instructions

#### 1. **Agent Context Files**

**Opportunity**: Structured context files for agent guidance

**Implementation**:

```yaml
# .thegent/context/agent-context.yaml
agents:
  - name: "code-reviewer"
    capabilities: ["code-review", "security-scan"]
    tools: ["thegent_lsp_format", "thegent_lsp_inspect"]
    hooks: ["quality-gate", "security-pipeline"]
    instructions: |
      Focus on code quality and security.
      Run quality-gate before approving.
```

#### 2. **Project Context Files**

**Opportunity**: Project-specific context for agents

**Implementation**:

```yaml
# .thegent/context/project-context.yaml
project:
  name: "thegent"
  language: "python"
  frameworks: ["typer", "pydantic", "fastapi"]
  lsp_servers: ["python", "typescript"]
  hooks: ["quality-gate", "spec-verifier"]
  skills: ["thegent-skills"]
```

#### 3. **Workflow Context Files**

**Opportunity**: Workflow-specific context

**Implementation**:

```yaml
# .thegent/context/workflow-context.yaml
workflows:
  - name: "code-review"
    steps:
      - hook: "quality-gate"
      - tool: "thegent_lsp_inspect"
      - skill: "code-reviewer"
```

---

## Part 3: Zsh/Shell Enhancements Research & Plan

### 3.1 Essential Zsh Plugins (Already Researched)

**From**: `docs/research/ZSH_STARSHIP_SETUP_GUIDE_2026-02-18.md`

#### Core Plugins (Must-Have)

1. ✅ **zsh-autosuggestions** - History-based autosuggestions
2. ✅ **zsh-syntax-highlighting** - Command syntax highlighting
3. ✅ **fzf-tab** - Fuzzy tab completion
4. ✅ **zsh-completions** - Additional completions
5. ✅ **zsh-history-substring-search** - History search

#### Productivity Plugins

6. ✅ **fast-syntax-highlighting** - Fast syntax highlighting
7. ✅ **git-flow-completion** - Git flow completions
8. ✅ **git-open** - Open Git repos in browser
9. ✅ **zsh-nvm** - Node version manager
10. ✅ **pyenv-zsh-plugin** - Python version manager
11. ✅ **zsh-you-should-use** - Alias suggestions
12. ✅ **zsh-better-npm-completion** - NPM completions

### 3.2 Proposed New Zsh Plugins for thegent

#### 1. **zsh-thegent-integration** ⭐⭐⭐⭐⭐

**Purpose**: Deep thegent integration in shell

**Features**:

- `thegent` command completions
- Agent status in prompt
- Work stream status
- Hook status indicators
- Auto-suggestions from work stream

**Implementation**:

```zsh
# ~/.zsh/plugins/zsh-thegent-integration/thegent-integration.zsh

# Completions
_thegent_completion() {
    local -a commands
    commands=(
        'run:Run agent'
        'bg:Run in background'
        'free:Free agent'
        'plan:Plan commands'
        'lsp:LSP commands'
    )
    _describe 'thegent commands' commands
}
compdef _thegent_completion thegent

# Prompt integration
_thegent_prompt_info() {
    local work_items=$(thegent plan do-next --json 2>/dev/null | jq -r '.items | length')
    if [[ $work_items -gt 0 ]]; then
        echo " [thegent:$work_items]"
    fi
}
```

#### 2. **zsh-agent-status** ⭐⭐⭐⭐

**Purpose**: Show agent status in prompt

**Features**:

- Running agents count
- Background sessions
- Agent health status

**Implementation**:

```zsh
# Show agent status
_agent_status_prompt() {
    local agents=$(thegent ps --format json 2>/dev/null | jq -r '.sessions | length')
    if [[ $agents -gt 0 ]]; then
        echo " [agents:$agents]"
    fi
}
```

#### 3. **zsh-work-stream** ⭐⭐⭐⭐

**Purpose**: Work stream integration

**Features**:

- Show next work item
- Claim work items
- Complete work items
- Work stream shortcuts

**Implementation**:

```zsh
# Aliases
alias wnext='thegent plan do-next'
alias wclaim='thegent plan claim'
alias wcomplete='thegent plan complete'
alias wwait='thegent plan wait-next'
```

### 3.3 Shell Optimization Enhancements

#### 1. **Deferred Plugin Loading** (Already Implemented)

**Status**: ✅ Implemented in `.zshrc`

**Enhancement**: Make it configurable

```zsh
# ~/.zshrc
THEGENT_DEFER_PLUGINS=${THEGENT_DEFER_PLUGINS:-true}
if [[ "$THEGENT_DEFER_PLUGINS" == "true" ]]; then
    # Defer plugin loading
fi
```

#### 2. **Lazy Completions**

**Opportunity**: Load completions on-demand

**Implementation**:

```zsh
# Lazy completion loading
_lazy_completion() {
    local cmd=$1
    if ! command -v "_${cmd}_completion" >/dev/null 2>&1; then
        # Load completion on first use
        source ~/.zsh/completions/${cmd}.zsh
    fi
}
```

#### 3. **Async Plugin Loading**

**Opportunity**: Load plugins asynchronously

**Implementation**:

```zsh
# Async plugin loader
_async_load_plugin() {
    local plugin=$1
    {
        source ~/.zsh/plugins/${plugin}/${plugin}.zsh
    } &!
}
```

### 3.4 Shell Integration with thegent

#### 1. **thegent Shell Functions**

**Opportunity**: Shell functions for common thegent operations

**Implementation**:

```zsh
# ~/.zsh/functions/thegent.zsh

# Quick agent run
tg() {
    local prompt="$1"
    shift
    thegent run "$prompt" "$@"
}

# Quick free agent
tgf() {
    thegent free "$@"
}

# Work stream next
tgw() {
    thegent plan do-next "$@"
}

# LSP start
tglsp() {
    thegent lsp start "$@"
}
```

#### 2. **thegent Prompt Integration**

**Opportunity**: Show thegent status in prompt

**Implementation**:

```zsh
# Starship config: ~/.config/starship.toml
[thegent]
command = "thegent plan do-next --json | jq -r '.items | length'"
format = " [thegent:$output]"
when = "thegent plan do-next --json 2>/dev/null | jq -e '.items | length > 0'"
```

#### 3. **thegent Aliases**

**Opportunity**: Common aliases

**Implementation**:

```zsh
# ~/.zsh/aliases/thegent.zsh
alias tg='thegent'
alias tgr='thegent run'
alias tgb='thegent bg'
alias tgf='thegent free'
alias tgp='thegent plan'
alias tgl='thegent lsp'
alias tgw='thegent plan wait-next'
```

---

## Part 4: OS-Level Enhancements Research & Plan

### 4.1 macOS Productivity Tools

#### 1. **Raycast** ⭐⭐⭐⭐⭐

**Purpose**: macOS productivity launcher

**Features**:

- Quick command execution
- Clipboard history
- Window management
- Extensions

**Integration Opportunity**:

- thegent Raycast extension
- Quick agent invocation
- Work stream access
- LSP server management

**Implementation**:

```javascript
// Raycast extension: thegent
export default function Command() {
  return (
    <List>
      <List.Item title="Run Agent" actions={...} />
      <List.Item title="Work Stream" actions={...} />
      <List.Item title="LSP Servers" actions={...} />
    </List>
  );
}
```

#### 2. **Alfred** ⭐⭐⭐⭐

**Purpose**: macOS productivity launcher (alternative to Raycast)

**Integration**: Similar to Raycast

#### 3. **Hammerspoon** ⭐⭐⭐⭐

**Purpose**: macOS automation

**Features**:

- Window management
- Hotkeys
- System automation
- Lua scripting

**Integration Opportunity**:

- thegent Hammerspoon module
- Agent status monitoring
- Work stream notifications
- LSP server management

**Implementation**:

```lua
-- Hammerspoon module: thegent.lua
local thegent = {}

function thegent.run_agent(prompt)
    hs.execute("thegent run '" .. prompt .. "'")
end

function thegent.show_work_stream()
    hs.execute("thegent plan do-next")
end

return thegent
```

#### 4. **Keyboard Maestro** ⭐⭐⭐

**Purpose**: macOS automation (paid)

**Integration**: Similar to Hammerspoon

### 4.2 macOS System-Level Enhancements

#### 1. **Launch Agents** (launchd)

**Opportunity**: System-level thegent services

**Implementation**:

```xml
<!-- ~/Library/LaunchAgents/com.thegent.server.plist -->
<?xml version="1.0" encoding="UTF-8"?>
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
</plist>
```

#### 2. **Shortcuts App Integration**

**Opportunity**: macOS Shortcuts for thegent

**Implementation**:

- Create Shortcuts for common operations
- Agent invocation shortcuts
- Work stream shortcuts

#### 3. **Menu Bar Integration**

**Opportunity**: Menu bar app for thegent

**Implementation**:

```python
# src/thegent/menubar/app.py
import rumps


class ThegentMenuBar(rumps.App):
    def __init__(self):
        super(ThegentMenuBar, self).__init__("thegent")
        self.menu = ["Work Stream", "LSP Servers", "Agents", None, "Settings", "Quit"]

    @rumps.clicked("Work Stream")
    def work_stream(self, _):
        # Show work stream
        pass
```

### 4.3 Cross-Platform OS Enhancements

#### 1. **System Service Integration**

**Opportunity**: thegent as system service

**Implementation**:

- macOS: launchd
- Linux: systemd
- Windows: NSSM

#### 2. **File Watchers**

**Opportunity**: System-level file watching

**Implementation**:

- macOS: FSEvents
- Linux: inotify
- Windows: ReadDirectoryChangesW

#### 3. **Process Management**

**Opportunity**: System-level process management

**Implementation**:

- Process monitoring
- Resource limits
- Auto-restart on crash

---

## Part 5: Comprehensive Integration Plan

### Phase 1: JetBrains Plugins (Week 1-2)

**Goal**: Integrate essential JetBrains plugins

**Tasks**:

1. ✅ Auto-detect MCP Server plugin
2. ⏳ Auto-install MCP Server plugin (if API available)
3. ⏳ Connect to MCP Server plugin MCP server
4. ⏳ Mount MCP tools in thegent
5. ⏳ Auto-detect MCP Language Service Tools plugin
6. ⏳ Integrate LSP tools from plugin
7. ✅ Enhance Serena plugin integration (already done)

**Deliverables**:

- `src/thegent/ide/jetbrains_mcp.py` - MCP Server plugin integration
- `src/thegent/ide/jetbrains_lsp_tools.py` - LSP tools integration
- `docs/guides/JETBRAINS_MCP_INTEGRATION.md` - Integration guide

### Phase 2: Hooks/MCP/Skills Enhancement (Week 3-4)

**Goal**: Enhance hooks, MCP, and skills integration

**Tasks**:

1. ⏳ Expose hooks via MCP
2. ⏳ Create hook context files
3. ⏳ Enhance skills with context files
4. ⏳ Auto-discover skills
5. ⏳ MCP resources for hooks/skills
6. ⏳ Agent context files

**Deliverables**:

- `src/thegent/hooks/mcp_exporter.py` - Hook MCP export
- `src/thegent/skills/discovery.py` - Skills auto-discovery
- `src/thegent/context/` - Context file system
- `docs/guides/HOOKS_MCP_INTEGRATION.md` - Integration guide

### Phase 3: Zsh/Shell Enhancements (Week 5-6)

**Goal**: Optimize shell experience

**Tasks**:

1. ⏳ Create zsh-thegent-integration plugin
2. ⏳ Add thegent shell functions
3. ⏳ Integrate with Starship prompt
4. ⏳ Add thegent aliases
5. ⏳ Optimize plugin loading
6. ⏳ Add async plugin loading

**Deliverables**:

- `shell/plugins/zsh-thegent-integration/` - thegent zsh plugin
- `shell/functions/thegent.zsh` - Shell functions
- `shell/aliases/thegent.zsh` - Aliases
- `docs/guides/SHELL_INTEGRATION.md` - Integration guide

### Phase 4: OS-Level Enhancements (Week 7-8)

**Goal**: System-level integration

**Tasks**:

1. ⏳ Create Raycast extension
2. ⏳ Create Hammerspoon module
3. ⏳ Create launchd service
4. ⏳ Create menu bar app
5. ⏳ System-level file watching
6. ⏳ Process management

**Deliverables**:

- `extensions/raycast/` - Raycast extension
- `extensions/hammerspoon/` - Hammerspoon module
- `extensions/menubar/` - Menu bar app
- `docs/guides/OS_INTEGRATION.md` - Integration guide

---

## Implementation Priority Matrix

| Component                      | Priority  | Effort | Impact | Phase          |
| ------------------------------ | --------- | ------ | ------ | -------------- |
| **MCP Server Plugin**          | 🔴 High   | Medium | High   | Phase 1        |
| **MCP Language Service Tools** | 🟡 Medium | Low    | Medium | Phase 1        |
| **Serena Plugin**              | 🔴 High   | Low    | High   | Phase 1 (done) |
| **Hook MCP Export**            | 🟡 Medium | Medium | Medium | Phase 2        |
| **Skills Context Files**       | 🟡 Medium | Low    | Medium | Phase 2        |
| **zsh-thegent-integration**    | 🟢 Low    | Medium | High   | Phase 3        |
| **Raycast Extension**          | 🟢 Low    | High   | Medium | Phase 4        |
| **Hammerspoon Module**         | 🟢 Low    | Medium | Low    | Phase 4        |

---

## Auto-Installation & Auto-Configuration Strategy

### JetBrains Plugins

1. **Detection**: Check plugin installation via IDE API
2. **Installation**: Use IDE plugin manager API (if available)
3. **Configuration**: Auto-configure MCP connection
4. **Verification**: Health check plugin MCP server

### Zsh Plugins

1. **Detection**: Check plugin installation
2. **Installation**: `git clone` to `~/.zsh/plugins/`
3. **Configuration**: Add to `.zshrc` automatically
4. **Verification**: Test plugin loading

### OS Tools

1. **Detection**: Check tool installation
2. **Installation**: `brew install` or download
3. **Configuration**: Auto-configure extensions
4. **Verification**: Test integration

---

## Configuration Files

### New Config Options

```python
# src/thegent/config.py
class ThegentSettings(BaseSettings):
    # JetBrains MCP Plugin
    jetbrains_mcp_enabled: bool = Field(default=True, description="Enable JetBrains MCP Server plugin integration")
    jetbrains_mcp_port: int = Field(default=8765, description="JetBrains MCP Server plugin port")

    # MCP Language Service Tools
    jetbrains_lsp_tools_enabled: bool = Field(default=True, description="Enable MCP Language Service Tools plugin")

    # Shell Integration
    shell_integration_enabled: bool = Field(
        default=True, description="Enable shell integration (zsh functions, aliases)"
    )
    shell_prompt_integration: bool = Field(default=True, description="Show thegent status in prompt")

    # OS Integration
    os_integration_enabled: bool = Field(default=True, description="Enable OS-level integrations (Raycast, etc.)")
```

---

## Success Metrics

### Phase 1 (JetBrains Plugins)

- ✅ MCP Server plugin detected and connected
- ✅ 35+ MCP tools available via thegent
- ✅ MCP Language Service Tools integrated
- ✅ Serena plugin fully integrated

### Phase 2 (Hooks/MCP/Skills)

- ✅ Hooks exposed via MCP
- ✅ Skills auto-discovered
- ✅ Context files system operational
- ✅ Agent context files working

### Phase 3 (Shell Enhancements)

- ✅ zsh-thegent-integration plugin installed
- ✅ Shell functions available
- ✅ Prompt integration working
- ✅ Startup time < 80ms

### Phase 4 (OS Enhancements)

- ✅ Raycast extension available
- ✅ Hammerspoon module working
- ✅ Menu bar app functional
- ✅ System service running

---

## References

### JetBrains Plugins

- **MCP Server**: https://plugins.jetbrains.com/plugin/26071-mcp-server
- **MCP Language Service Tools**: https://plugins.jetbrains.com/plugin/27888-mcp-language-service-tools
- **GitHub**: https://github.com/justin1291/mcp-idea-lsp
- **MCPlane**: https://www.mcplane.com/mcp_servers/mcpplugin

### Serena

- **GitHub**: https://github.com/oraios/serena
- **JetBrains Plugin**: https://plugins.jetbrains.com/plugin/28946-serena

### Shell

- **Zsh Guide**: `docs/research/ZSH_STARSHIP_SETUP_GUIDE_2026-02-18.md`
- **Shell Config**: `docs/research/SHELL_CONFIG_AUDIT_AND_CONSOLIDATION_PLAN.md`

### OS Tools

- **Raycast**: https://www.raycast.com
- **Hammerspoon**: https://www.hammerspoon.org
- **Keyboard Maestro**: https://www.keyboardmaestro.com

---

## Next Steps

1. ✅ Research complete
2. ⏳ Review plan with user
3. ⏳ Prioritize phases
4. ⏳ Begin Phase 1 implementation
5. ⏳ Iterate based on feedback

---

**Document Status**: Research Complete, Plan Ready for Implementation
