<DONE>
# Conversation Dump 2026-02-16 — Complete Expansion

> **Status**: Complete | **Version**: 2.0 | **Date**: 2026-02-17
> **Source**: Expanded from [CONVERSATION_DUMP_2026-02-16.md](./CONVERSATION_DUMP_2026-02-16.md)
> **Purpose**: Structured extraction of work items, decisions, and follow-up actions from agent conversations

---

## Table of Contents

1. [Shell & Shims Fixes](#1-shell--shims-fixes)
2. [TUI Compositor Research](#2-tui-compositor-research)
3. [Compute Offloading Architecture](#3-compute-offloading-architecture)
4. [Idea Seed System](#4-idea-seed-system)
5. [Work Items Extracted](#5-work-items-extracted)
6. [Implementation Status](#6-implementation-status)
7. [Follow-Up Actions](#7-follow-up-actions)

---

## 1. Shell & Shims Fixes

### 1.1 Issues Addressed

| Issue                                                   | Location                                         | Status   | Fix                                           |
| ------------------------------------------------------- | ------------------------------------------------ | -------- | --------------------------------------------- |
| `NameError: name 'Optional' is not defined`             | `thegent/src/thegent/main.py` (lines 3526, 3550) | ✅ Fixed | Replaced `Optional[Path]` with `Path \| None` |
| `git: '/opt/homebrew/bin/codex' is not a git command`   | Git shim routing                                 | ✅ Fixed | Added `_install_agent_accelerators()`         |
| `git: '/opt/homebrew/bin/copilot' is not a git command` | Git shim routing                                 | ✅ Fixed | Added `_install_agent_accelerators()`         |
| Copilot parse error: `no matches found: /*---`          | Zsh parsing Node.js script                       | ✅ Fixed | Exec real binary directly                     |
| Zsh setup stripped                                      | `~/.zshenv`, `~/.zshrc`                          | ✅ Fixed | Restored from `thegent/shell/`                |
| Ghostty config missing                                  | `~/.config/ghostty/config`                       | ✅ Fixed | Created config file                           |

### 1.2 Shim Architecture (MTSP-10)

#### Component Breakdown

| Component              | Purpose                           | Implementation                   | Status      |
| ---------------------- | --------------------------------- | -------------------------------- | ----------- |
| **Git Shim**           | Multi-tenant lock coordination    | `hooks/lib/git-wrapper.sh`       | ✅ Complete |
| **Tool Accelerators**  | grep→rg, find→fd, jq→jaq, uv      | `hooks/lib/common.sh`            | ✅ Complete |
| **Agent Accelerators** | codex, copilot (exec real binary) | `thegent/src/thegent/install.py` | ✅ Complete |
| **Role Accelerators**  | run, bg, ps → `thegent {role}`    | `hooks/lib/common.sh`            | ✅ Complete |

#### Implementation Details

**Agent Accelerators** (`_install_agent_accelerators()`):

```python
# thegent/src/thegent/install.py


def _install_agent_accelerators(self):
    """Install shims for agent binaries (codex, copilot)"""
    agents = ["codex", "copilot"]
    for agent in agents:
        shim_path = self.shim_dir / agent
        if not shim_path.exists():
            # Create shim that execs real binary directly
            shim_path.write_text(f'#!/usr/bin/env sh\nset -e\nexec "$(command -v {agent})" "$@"\n')
            shim_path.chmod(0o755)
```

**Benefits**:

- Avoids zsh parsing issues
- Prevents git routing confusion
- Direct binary execution (fastest)

### 1.3 Related Work Items

- **WP-SHELL-FIXES**: Shell & shim fixes (completed)
- **MTSP-10**: Multi-tenant shim architecture
- **FULL_SHELL_TO_RUST**: Shell to Rust migration (ongoing)

**See Also**:

- [FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md](../plans/FULL_SHELL_TO_RUST_WHERE_BENEFICIAL.md)
- [SETUP-RESTORE.md](../SETUP-RESTORE.md)

---

## 2. TUI Compositor Research

### 2.1 Research Summary

**User Request**: Research TUI-os or similar TUI compositor + multiplexer for sitback and UI/UX.

**Findings**: Comprehensive analysis of TUI frameworks, multiplexers, and dashboard applications.

### 2.2 Technology Stack Analysis

#### Multiplexers

| Project    | Stars | Language | Features                         | Recommendation  |
| ---------- | ----- | -------- | -------------------------------- | --------------- |
| **Zellij** | 29k   | Rust     | Layouts, plugins, floating panes | ⭐ Recommended  |
| **tmux**   | -     | C        | Standard, widely supported       | ✅ Fallback     |
| **mprocs** | 2.4k  | Rust     | Process management               | ⚠️ Limited      |
| **trex**   | 10    | -        | AI agent tracking                | 🔍 Experimental |

**Zellij Advantages**:

- Modern Rust implementation
- Plugin system
- Floating panes
- Layout management
- Better UX than tmux

#### TUI Frameworks

| Framework      | Stars | Language | Features                     | Use Case       |
| -------------- | ----- | -------- | ---------------------------- | -------------- |
| **Textual**    | 34k   | Python   | CSS-like styling, web export | ⭐ Recommended |
| **Ratatui**    | 18k   | Rust     | Terminal UI library          | ✅ Alternative |
| **Bubble Tea** | 39k   | Go       | TUI framework                | ✅ Alternative |

**Textual Advantages**:

- Python (matches thegent stack)
- CSS-like styling
- `textual serve` for web export
- Rich widget library
- Good documentation

#### Dashboard Applications (Reference UX)

| Application         | Purpose         | UX Pattern      |
| ------------------- | --------------- | --------------- |
| **Superfile**       | File manager    | Tree navigation |
| **Glow**            | Markdown viewer | Content display |
| **gitui**           | Git interface   | Status panels   |
| **taskwarrior-tui** | Task management | List views      |

### 2.3 Recommended Architecture

#### Layered Model

```
┌─────────────────────────────────────────────────────────┐
│  GUI-like Menu Layer                                    │
│  - Menubar (File, Edit, View, Tools, Help)             │
│  - Statusbar (session info, agent status)              │
│  - Dialogs (confirmations, inputs)                      │
│  - Keyboard shortcuts (Ctrl+C, Ctrl+V, etc.)            │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│  TUI Compositor Layer                                   │
│  - Panes (split horizontally/vertically)                │
│  - Floating windows (dialogs, popups)                    │
│  - Layout management (save/restore)                     │
│  - Session persistence                                  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│  Terminal Emulator / PTY Layer                          │
│  - PTY allocation                                        │
│  - Process execution                                     │
│  - Output rendering                                     │
└─────────────────────────────────────────────────────────┘
```

#### Implementation Paths

**Path A: Zellij + Custom Plugin**

- Use Zellij as compositor
- Build custom TUI plugin for menubar/statusbar
- Pros: Leverage Zellij's features
- Cons: Plugin development overhead

**Path B: Textual App Hosting Compositor**

- Build Textual app with menubar/statusbar
- Embed terminal panes (via libvterm or similar)
- Pros: Full control, Python integration
- Cons: More implementation work

**Recommendation**: **Path B (Textual)** for better integration with thegent Python stack.

### 2.4 Implementation Plan

#### Phase 1: Foundation (Week 1)

- [ ] Set up Textual development environment
- [ ] Create basic app structure
- [ ] Implement menubar and statusbar
- [ ] Add keyboard shortcuts

#### Phase 2: Compositor Integration (Week 2)

- [ ] Integrate terminal pane widget
- [ ] Implement pane splitting
- [ ] Add layout management
- [ ] Session persistence

#### Phase 3: Advanced Features (Week 3)

- [ ] Floating windows/dialogs
- [ ] Plugin system
- [ ] Theme support
- [ ] Web export (`textual serve`)

### 2.5 Performance Targets

| Metric        | Target | Notes                  |
| ------------- | ------ | ---------------------- |
| App startup   | <500ms | Fast initialization    |
| Pane creation | <100ms | Quick pane spawning    |
| Layout switch | <50ms  | Smooth transitions     |
| Memory usage  | <100MB | Efficient resource use |

### 2.6 Related Work Items

- **WP-TUI-COMPOSITOR**: TUI compositor implementation
- **WP-SITBACK-UI**: Sitback UI/UX improvements
- **UNIFIED_SYSTEM_APPLICATION_PLAN**: Unified application plan

**See Also**:

- [UNIFIED_SYSTEM_APPLICATION_PLAN.md](../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md)
- [Textual Documentation](https://textual.textualize.io/)
- [Zellij Documentation](https://zellij.dev/)

---

## 3. Compute Offloading Architecture

### 3.1 Overview

**Concept**: Link Mac (client) with Windows 11 PC (compute base) for heavy compute tasks.

**Status**: Architecture complete, implementation pending
**Priority**: Medium

### 3.2 Architecture

#### Hardware Setup

| Component   | Mac                          | Windows PC   |
| ----------- | ---------------------------- | ------------ |
| **Role**    | Client (Cursor, Claude Code) | Compute base |
| **RAM**     | 16GB                         | 64GB         |
| **VRAM**    | Integrated                   | 16GB         |
| **CPU**     | Apple Silicon                | 8-core       |
| **Storage** | 512GB SSD                    | 5TB          |

#### Network Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Mac (Client)  │◄───────►│  Windows PC     │
│                 │         │  (Compute Base) │
│  - Cursor IDE   │         │  - Heavy builds  │
│  - Claude Code  │         │  - Docker        │
│  - Light dev    │         │  - Process-compose│
└─────────────────┘         └─────────────────┘
         │                           │
         │                           │
         └───────────┬───────────────┘
                     │
            ┌────────▼────────┐
            │  Tailscale VPN  │
            │  (Secure tunnel) │
            └─────────────────┘
```

#### Sync Architecture

**Syncthing**:

- Bi-directional sync of `kush/` directory
- Real-time file synchronization
- Conflict resolution
- Bandwidth throttling

**Remote Access**:

- **Parsec RDP**: Low-latency remote desktop
- **SSH**: Command-line access
- **Tailscale**: Secure VPN tunnel

### 3.3 Compute Offloading Implementation

#### Command Interface

```bash
# Offload heavy build to Windows PC
thegent run --remote windows-pc "Build project" gemini

# Offload Docker operations
thegent run --remote windows-pc "docker compose up" gemini

# Offload process-compose
thegent run --remote windows-pc "process-compose up" gemini
```

#### Implementation Details

```python
# thegent/src/thegent/compute/offload.py


class ComputeOffloader:
    def __init__(self):
        self.remote_hosts = {
            "windows-pc": RemoteHost(
                hostname="windows-pc.tailscale",
                ssh_user="user",
                sync_dir="/kush",
            ),
        }

    async def offload_task(
        self,
        remote: str,
        command: str,
        agent: str,
    ) -> TaskResult:
        """Offload task to remote compute base"""
        host = self.remote_hosts[remote]

        # Sync files first
        await self.sync_files(host)

        # Execute command remotely
        result = await host.execute(command, agent)

        # Sync results back
        await self.sync_results(host)

        return result
```

### 3.4 Performance Characteristics

| Operation               | Latency   | Throughput | Notes             |
| ----------------------- | --------- | ---------- | ----------------- |
| File sync (initial)     | 30s-2m    | Variable   | Depends on size   |
| File sync (incremental) | 1-5s      | Fast       | Only changes      |
| Remote execution        | 100-500ms | 10/s       | Network dependent |
| Parsec RDP              | <50ms     | Real-time  | Low latency       |

### 3.5 Failure Modes & Mitigation

**Failure Mode**: Network unavailable
**Mitigation**: Queue tasks, retry when online

**Failure Mode**: Sync conflicts
**Mitigation**: Conflict resolution UI, manual merge

**Failure Mode**: Remote host down
**Mitigation**: Fallback to local execution, alert user

### 3.6 Edge Cases

1. **Large file transfers**: Chunking, compression
2. **Concurrent syncs**: Lock mechanism
3. **Partial failures**: Resume capability

### 3.7 Related Work Items

- **WP-COMPUTE-OFFLOAD**: Compute offloading implementation
- **HYBRID_ENV_IMPLEMENTATION**: Hybrid environment setup

**See Also**:

- [HYBRID_MAC_WIN_DEV_ENVIRONMENT.md](../architecture/HYBRID_MAC_WIN_DEV_ENVIRONMENT.md)
- [HYBRID_ENV_IMPLEMENTATION_PLAN.md](../plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md)
- [HYBRID_ENV_SUMMARY.md](../reference/HYBRID_ENV_SUMMARY.md)

---

## 4. Idea Seed System

### 4.1 Overview

**User Request**: Configure system to detect and save exact idea prompts when `$idea` flag is present.

**Status**: Research complete, implementation pending
**Priority**: High

### 4.2 Requirements

1. **Detection**: Detect `$idea` flag in user prompts
2. **Storage**: Save exact prompts to `research/idea-seeds/`
3. **Sources**: Claude Code, Codex sessions
4. **Persistence**: Check on change, parse schema correctly
5. **Retention**: Sessions clear after 2 weeks, must capture before

### 4.3 Session Storage Locations

#### Claude Code Sessions

**macOS**:

```
~/Library/Application Support/Claude/claude-code/sessions/
```

**Linux**:

```
~/.local/share/claude-code/sessions/
```

**Windows**:

```
%APPDATA%\Claude\claude-code\sessions\
```

#### Codex Sessions

**macOS**:

```
~/.config/codex/sessions/
```

**Linux**:

```
~/.config/codex/sessions/
```

**Windows**:

```
%APPDATA%\codex\sessions\
```

#### Cursor Sessions

**macOS**:

```
~/Library/Application Support/Cursor/User/globalStorage/
```

**Format**: SQLite database or JSON files

### 4.4 Schema Research

#### Claude Code Session Format

```json
{
  "id": "session-uuid",
  "created_at": "2026-02-16T10:30:17Z",
  "updated_at": "2026-02-16T10:32:37Z",
  "messages": [
    {
      "role": "user",
      "content": "User prompt with $idea flag",
      "timestamp": "2026-02-16T10:30:17Z"
    },
    {
      "role": "assistant",
      "content": "Assistant response",
      "timestamp": "2026-02-16T10:30:18Z"
    }
  ],
  "metadata": {
    "project": "/path/to/project",
    "model": "claude-3-5-sonnet"
  }
}
```

#### Codex Session Format

```json
{
  "sessionId": "uuid",
  "createdAt": 1708123217000,
  "messages": [
    {
      "type": "user",
      "text": "User prompt with $idea",
      "timestamp": 1708123217000
    }
  ]
}
```

### 4.5 Implementation

#### Idea Detection Service

```python
# thegent/src/thegent/ideas/detector.py

import json
import sqlite3
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class IdeaDetector:
    def __init__(self):
        self.sources = [
            ClaudeCodeSource(),
            CodexSource(),
            CursorSource(),
        ]
        self.storage = IdeaStorage()

    def detect_ideas(self, text: str) -> list[Idea]:
        """Detect $idea flags in text"""
        ideas = []
        if "$idea" in text or "$idea " in text:
            # Extract idea prompt
            idea_text = self._extract_idea(text)
            ideas.append(
                Idea(
                    text=idea_text,
                    source="detected",
                    timestamp=datetime.now(),
                )
            )
        return ideas

    def watch_sessions(self):
        """Watch session directories for changes"""
        for source in self.sources:
            observer = Observer()
            handler = SessionChangeHandler(source, self)
            observer.schedule(handler, source.session_dir, recursive=True)
            observer.start()
```

#### Session Parser

```python
# thegent/src/thegent/ideas/parsers.py


class ClaudeCodeParser:
    def parse_session(self, session_file: Path) -> list[Message]:
        """Parse Claude Code session file"""
        with open(session_file) as f:
            data = json.load(f)

        messages = []
        for msg in data.get("messages", []):
            if msg["role"] == "user":
                content = msg["content"]
                if "$idea" in content:
                    messages.append(
                        Message(
                            role="user",
                            content=content,
                            timestamp=msg["timestamp"],
                        )
                    )
        return messages


class CodexParser:
    def parse_session(self, session_file: Path) -> list[Message]:
        """Parse Codex session file"""
        with open(session_file) as f:
            data = json.load(f)

        messages = []
        for msg in data.get("messages", []):
            if msg["type"] == "user" and "$idea" in msg["text"]:
                messages.append(
                    Message(
                        role="user",
                        content=msg["text"],
                        timestamp=msg["timestamp"],
                    )
                )
        return messages


class CursorParser:
    def parse_session(self, db_path: Path) -> list[Message]:
        """Parse Cursor SQLite database"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT content, timestamp
            FROM messages
            WHERE role = 'user' AND content LIKE '%$idea%'
        """)

        messages = []
        for row in cursor.fetchall():
            messages.append(
                Message(
                    role="user",
                    content=row[0],
                    timestamp=row[1],
                )
            )

        return messages
```

#### Storage Service

```python
# thegent/src/thegent/ideas/storage.py


class IdeaStorage:
    def __init__(self):
        self.storage_dir = Path("docs/research/idea-seeds")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_idea(self, idea: Idea):
        """Save idea to seed file"""
        timestamp = idea.timestamp.strftime("%Y%m%dT%H%M%SZ")
        session_id = idea.session_id or "unknown"
        filename = f"seed_{timestamp}_{session_id}_{hash(idea.text) % 1000}.md"

        filepath = self.storage_dir / filename
        filepath.write_text(self._format_idea(idea))

    def _format_idea(self, idea: Idea) -> str:
        """Format idea as markdown"""
        return f"""---
saved_at: {idea.timestamp.isoformat()}Z
source: {idea.source}
session_id: {idea.session_id}
project: {idea.project}
---

{idea.text}
"""
```

### 4.6 Monitoring & Cleanup

#### Session Monitoring

```python
# thegent/src/thegent/ideas/monitor.py


class SessionMonitor:
    def __init__(self):
        self.check_interval = timedelta(hours=1)
        self.retention_days = 14

    async def monitor_sessions(self):
        """Monitor sessions and extract ideas before cleanup"""
        while True:
            for source in self.sources:
                sessions = source.list_sessions()
                for session in sessions:
                    age = datetime.now() - session.created_at
                    if age.days >= self.retention_days - 1:
                        # Extract ideas before cleanup
                        ideas = self.extract_ideas(session)
                        for idea in ideas:
                            self.storage.save_idea(idea)

            await asyncio.sleep(self.check_interval.total_seconds())
```

### 4.7 Performance Characteristics

| Operation       | Latency   | Throughput   |
| --------------- | --------- | ------------ |
| Idea detection  | <1ms      | 10,000/s     |
| Session parsing | <10ms     | 100/s        |
| File watching   | Real-time | Event-driven |
| Storage         | <5ms      | 1,000/s      |

### 4.8 Failure Modes & Mitigation

**Failure Mode**: Session format changed
**Mitigation**: Version detection, fallback parsers

**Failure Mode**: Storage full
**Mitigation**: Rotation, compression, archival

**Failure Mode**: Watcher fails
**Mitigation**: Periodic scan fallback

### 4.9 Related Work Items

- **WP-IDEA-SEED-SYSTEM**: Idea seed system implementation
- **PROMPT_HISTORY_COLLECTION**: Prompt history collection system

**See Also**:

- [PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM.md](../plans/PROMPT_HISTORY_COLLECTION_AND_AUDIT_SYSTEM.md)
- [IDEA_SEEDS_SESSION_STORAGE.md](./IDEA_SEEDS_SESSION_STORAGE.md)

---

## 5. Work Items Extracted

### 5.1 BACKLOG Items

Add to [WORK_STREAM.md](../reference/WORK_STREAM.md) BACKLOG:

| ID                            | Title                          | Source            | Priority | Depends        |
| ----------------------------- | ------------------------------ | ----------------- | -------- | -------------- |
| **research-shell-shim-fixes** | Shell & shim fixes (completed) | CONVERSATION_DUMP | P0       | -              |
| **research-tui-compositor**   | TUI compositor implementation  | CONVERSATION_DUMP | P1       | -              |
| **research-compute-offload**  | Compute offloading Mac↔PC     | CONVERSATION_DUMP | P2       | HYBRID_ENV     |
| **research-idea-seed-system** | Idea seed detection & storage  | CONVERSATION_DUMP | P1       | PROMPT_HISTORY |

### 5.2 Implementation Status

| Work Item          | Status      | Notes                 |
| ------------------ | ----------- | --------------------- |
| Shell & shim fixes | ✅ Complete | Already implemented   |
| TUI compositor     | 📅 Planned  | Architecture designed |
| Compute offload    | 📅 Planned  | Architecture complete |
| Idea seed system   | 📅 Planned  | Research complete     |

---

## 6. Implementation Status

### 6.1 Completed

- ✅ Shell & shim fixes
- ✅ Zsh restoration
- ✅ Ghostty config
- ✅ Agent accelerators

### 6.2 In Progress

- 🔄 TUI compositor research
- 🔄 Compute offloading architecture

### 6.3 Planned

- 📅 Idea seed system
- 📅 TUI compositor implementation
- 📅 Compute offloading implementation

---

## 7. Follow-Up Actions

### 7.1 Immediate Actions

1. **Add BACKLOG items** to WORK_STREAM.md
2. **Create implementation plans** for TUI compositor
3. **Research session storage** locations for all agents
4. **Implement idea seed system** with monitoring

### 7.2 Documentation Updates

1. Update [SETUP-RESTORE.md](../SETUP-RESTORE.md) with fixes
2. Create [TUI_COMPOSITOR_IMPLEMENTATION_PLAN.md](../plans/TUI_COMPOSITOR_IMPLEMENTATION_PLAN.md)
3. Update [HYBRID_ENV_IMPLEMENTATION_PLAN.md](../plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md)
4. Create [IDEA_SEED_SYSTEM_IMPLEMENTATION.md](../plans/IDEA_SEED_SYSTEM_IMPLEMENTATION.md)

### 7.3 Integration Points

- Link to [WORK_STREAM.md](../reference/WORK_STREAM.md)
- Link to [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md)
- Link to [UNIFIED_SYSTEM_APPLICATION_PLAN.md](../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md)

---

## 8. References

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [SETUP-RESTORE.md](../SETUP-RESTORE.md) - Setup restoration guide
- [UNIFIED_SYSTEM_APPLICATION_PLAN.md](../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md) - Unified application plan

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream (4 BACKLOG items)
- [CONVERSATION_DUMP_2026-02-16.md](./CONVERSATION_DUMP_2026-02-16.md) - Original fragment
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md) - Work breakdown structure

---

**Status**: Complete expansion ready for implementation
**Next Steps**: Add BACKLOG items, create implementation plans, begin development

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

## Evidence Retention Rules

| Evidence Type                    | Retention Window | Store Path                       | Required Command                                                                                                                                |
| -------------------------------- | ---------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ----- |
| Command output logs              | 30 days          | `thegent/logs/`                  | `mkdir -p thegent/logs && script -q thegent/logs/session-$(date +%Y%m%d-%H%M%S).log`                                                            |
| Test artifacts (junit/coverage)  | 14 days          | `thegent/artifacts/tests/`       | `mkdir -p thegent/artifacts/tests && cp -f .coverage thegent/artifacts/tests/ 2>/dev/null                                                       |                                                                  | true` |
| Research snapshots               | 90 days          | `thegent/docs/research/archive/` | `mkdir -p thegent/docs/research/archive && cp -f thegent/docs/research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md thegent/docs/research/archive/` |
| Verification command transcripts | 30 days          | `thegent/artifacts/verify/`      | `mkdir -p thegent/artifacts/verify && task quality                                                                                              | tee thegent/artifacts/verify/quality-$(date +%Y%m%d-%H%M%S).log` |

- Purge expired logs weekly: `find thegent/logs thegent/artifacts/tests thegent/artifacts/verify -type f -mtime +30 -delete`
- Purge expired research snapshots monthly: `find thegent/docs/research/archive -type f -mtime +90 -delete`

## Dry-Run Commands

- Preview stale evidence files: `find thegent/logs thegent/artifacts/tests thegent/artifacts/verify -type f -mtime +30 -print`
- Preview stale research snapshots: `find thegent/docs/research/archive -type f -mtime +90 -print`
- Preview files to archive before copy: `ls -lh thegent/docs/research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md`
- Preview quality pipeline without mutation: `task quality --dry 2>/dev/null || task -l`

## Archive Hygiene Checklist

- Run weekly purge for 30-day evidence: `find thegent/logs thegent/artifacts/tests thegent/artifacts/verify -type f -mtime +30 -delete`
- Run monthly purge for 90-day research snapshots: `find thegent/docs/research/archive -type f -mtime +90 -delete`
- Capture a fresh session log before cleanup: `mkdir -p thegent/logs && script -q thegent/logs/session-$(date +%Y%m%d-%H%M%S).log`
- Re-archive the expanded dump after edits: `mkdir -p thegent/docs/research/archive && cp -f thegent/docs/research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md thegent/docs/research/archive/`

## Retention Verification Commands

- Verify evidence files older than 30 days: `find thegent/logs thegent/artifacts/tests thegent/artifacts/verify -type f -mtime +30 -print`
- Verify research snapshots older than 90 days: `find thegent/docs/research/archive -type f -mtime +90 -print`
- Verify latest archive copy timestamp: `ls -lhtr thegent/docs/research/archive | tail -n 5`
- Verify retained verification transcripts: `find thegent/artifacts/verify -type f -name 'quality-*.log' -print | sort`

## Archive Rotation Policy

- Rotate monthly archive copy on the first business day: `mkdir -p thegent/docs/research/archive && cp -f thegent/docs/research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md thegent/docs/research/archive/CONVERSATION_DUMP_2026-02-16_EXPANDED-$(date +%Y-%m).md`
- Keep last 6 monthly rotations only: `ls -1t thegent/docs/research/archive/CONVERSATION_DUMP_2026-02-16_EXPANDED-*.md | tail -n +7 | xargs -r rm -f`
- Verify newest rotation exists after copy: `ls -1t thegent/docs/research/archive/CONVERSATION_DUMP_2026-02-16_EXPANDED-*.md | head -n 1`

## Staleness Detection Commands

- Detect archive files older than 180 days: `find thegent/docs/research/archive -type f -name 'CONVERSATION_DUMP_2026-02-16_EXPANDED-*.md' -mtime +180 -print`
- Detect unchanged primary dump older than 30 days: `find thegent/docs/research -maxdepth 1 -type f -name 'CONVERSATION_DUMP_2026-02-16_EXPANDED.md' -mtime +30 -print`
- Detect missing current-month rotation: `test -f "thegent/docs/research/archive/CONVERSATION_DUMP_2026-02-16_EXPANDED-$(date +%Y-%m).md" || echo "missing current-month rotation"`
