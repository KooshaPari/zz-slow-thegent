# thegent Encyclopedia of Technical Specifications

## Master Index

This document indexes all technical specifications, PRDs, and architectural documentation for the thegent platform.

---

## Domain Index

### Core Platform

| Specification         | File                                                         | Status      |
| --------------------- | ------------------------------------------------------------ | ----------- |
| Architecture Overview | [ARCHITECTURE.md](./ARCHITECTURE.md)                         | ✅ Complete |
| Tech Stack            | [TECH_STACK_AUDIT.md](./TECH_STACK_AUDIT.md)                 | ✅ Complete |
| Dependencies          | [THEGENT_DEPENDENCY_AUDIT.md](./THEGENT_DEPENDENCY_AUDIT.md) | ✅ Complete |
| LOC Reduction Plan    | [LOC_REDUCTION_PLAN.md](./LOC_REDUCTION_PLAN.md)             | ✅ Active   |

### Technical Specs (Domain READMEs)

| Domain             | Spec                                                               | Status |
| ------------------ | ------------------------------------------------------------------ | ------ |
| **Agents**         | [specs/agents/README.md](./specs/agents/README.md)                 | ✅     |
| **Routing**        | [specs/routing/README.md](./specs/routing/README.md)               | ✅     |
| **MCP**            | [specs/mcp/README.md](./specs/mcp/README.md)                       | ✅     |
| **Governance**     | [specs/governance/README.md](./specs/governance/README.md)         | ✅     |
| **Orchestration**  | [specs/orchestration/README.md](./specs/orchestration/README.md)   | ✅     |
| **Automation**     | [specs/automation/README.md](./specs/automation/README.md)         | ✅     |
| **Cross-Platform** | [specs/cross_platform/README.md](./specs/cross_platform/README.md) | ✅     |
| **Infrastructure** | [specs/infra/README.md](./specs/infra/README.md)                   | ✅     |
| **Terminal**       | [specs/terminal/README.md](./specs/terminal/README.md)             | ✅     |
| **Memory**         | [specs/memory/README.md](./specs/memory/README.md)                 | ✅     |
| **Planning**       | [specs/planning/README.md](./specs/planning/README.md)             | ✅     |
| **Discovery**      | [specs/discovery/README.md](./specs/discovery/README.md)           | ✅     |
| **Observability**  | [specs/observability/README.md](./specs/observability/README.md)   | ✅     |
| **Security**       | [specs/security/README.md](./specs/security/README.md)             | ✅     |
| **Contracts**      | [specs/contracts/README.md](./specs/contracts/README.md)           | ✅     |
| **Verification**   | [specs/verification/README.md](./specs/verification/README.md)     | ✅     |
| **Cost**           | [specs/cost/README.md](./specs/cost/README.md)                     | ✅     |
| **Skills**         | [specs/skills/README.md](./specs/skills/README.md)                 | ✅     |
| **Mesh**           | [specs/mesh/README.md](./specs/mesh/README.md)                     | ✅     |
| **UI/TUI**         | [specs/ui/README.md](./specs/ui/README.md)                         | ✅     |
| **Protocols**      | [specs/protocols/README.md](./specs/protocols/README.md)           | ✅     |
| **Evals**          | [specs/evals/README.md](./specs/evals/README.md)                   | ✅     |
| **Database**       | [specs/database/README.md](./specs/database/README.md)             | ✅     |
| **Versioning**     | [specs/versioning/README.md](./specs/versioning/README.md)         | ✅     |
| **Documentation**  | [specs/documentation/README.md](./specs/documentation/README.md)   | ✅     |

### Mobile & Desktop Automation

| Specification            | File                                                                   | Status      |
| ------------------------ | ---------------------------------------------------------------------- | ----------- |
| Desktop Agent Cursor PRD | [DESKTOP_AGENT_CURSOR_PLAN.md](./DESKTOP_AGENT_CURSOR_PLAN.md)         | ✅ Complete |
| Mobile Automation PRD    | [THEGENT_MOBILE_AUTOMATION_PRD.md](./THEGENT_MOBILE_AUTOMATION_PRD.md) | ✅ Complete |

### API References

| Domain       | Path                | Coverage          |
| ------------ | ------------------- | ----------------- |
| MCP Server   | `mcp/server.py`     | Core MCP protocol |
| CLI Commands | `cli/commands/*.py` | All commands      |
| Routing      | `routing/*.py`      | LLM routing       |
| Governance   | `governance/*.py`   | Policy engine     |

---

## Module Domains

### 1. Agent Systems (`agents/`)

- **Purpose**: AI agent execution and management
- **Key Files**:
  - `agents/base.py` - Base agent interface
  - `agents/direct_agents.py` - Direct execution
  - `agents/crew/router.py` - Crew routing
  - `agents/unified_registry.py` - Agent registry
- **Spec**: [agents/README.md](./specs/agents/README.md)

### 2. Routing & LLM Selection (`routing/`)

- **Purpose**: Model routing, cost optimization
- **Key Files**:
  - `routing/task_router.py` - Task-based routing
  - `routing/cost_aware_router.py` - Cost optimization
  - `routing/semantic_cache.py` - Semantic caching
- **Spec**: [routing/README.md](./specs/routing/README.md)

### 3. Mobile Automation (`mobile/`, `automation/`)

- **Purpose**: Mobile device control
- **Key Files**:
  - `automation/mobile.py` - Mobile automation
  - `automation/virtual_desktop.py` - Virtual desktops
  - `automation/macos_desktop.py` - macOS automation
- **Spec**: [automation/README.md](./specs/automation/README.md) (to be created)

### 4. MCP Protocol (`mcp/`)

- **Purpose**: Model Context Protocol server
- **Key Files**:
  - `mcp/server.py` - Main MCP server
  - `mcp/server_tools_*.py` - Tool definitions
  - `mcp/server_resources.py` - Resource handlers
- **Spec**: [mcp/README.md](./specs/mcp/README.md)

### 5. Governance & Security (`governance/`)

- **Purpose**: Policy enforcement, compliance
- **Key Files**:
  - `governance/scanner.py` - Security scanning
  - `governance/signatures.py` - Cryptographic signing
  - `governance/health_score.py` - Health scoring
- **Spec**: [governance/README.md](./specs/governance/README.md)

### 6. Orchestration (`orchestration/`)

- **Purpose**: Task orchestration, execution
- **Key Files**:
  - `orchestration/plan.py` - Execution planning
  - `orchestration/execution/engine.py` - Execution engine
  - `orchestration/state/*.py` - State management
- **Spec**: [orchestration/README.md](./specs/orchestration/README.md)

### 7. Database & Storage

- **Purpose**: Data persistence, caching, state management
- **Key Files**:
  - `native/jsonl_parser.py` - JSONL operations
  - `native/git_native.py` - Git operations
  - `orchestration/state/*.py` - State management
- **Spec**: [database/README.md](./specs/database/README.md)

### 8. Mobile & Terminal

- **Purpose**: Terminal harness, ZMX integration
- **Key Files**:
  - `session/zmx_backend.py` - ZMX session backend
  - `native/zmx_session.py` - Terminal management
- **Spec**: [terminal/README.md](./specs/terminal/README.md)

### 9. Security & Compliance

- **Purpose**: Encryption, secrets, governance
- **Key Files**:
  - `governance/scanner.py` - Security scanning
  - `maif/crypto.py` - Cryptographic operations
- **Spec**: [security/README.md](./specs/security/README.md)

### 7. Mesh & Collaboration (`mesh/`)

- **Purpose**: Multi-agent mesh coordination
- **Key Files**:
  - `mesh/mesh.py` - Mesh coordination
  - `mesh/git.py` - Git operations
  - `mesh/consensus.py` - Consensus

### 8. Persistence & Storage

- **Database**: `db_utils/`, `storage/`
- **Cache**: `cache/`, `redis/`
- **Files**: `native/jsonl_parser.py`, `native/git_native.py`

### 9. Observability (`observability/`, `telemetry/`)

- **Purpose**: Monitoring, tracing
- **Key Files**:
  - `observability/otel.py` - OpenTelemetry
  - `audit/*.py` - Audit logging

### 10. Terminal & UI (`terminal/`, `tui/`, `compositor/`)

- **Purpose**: Terminal and UI rendering
- **Key Files**:
  - `terminal_cli.py` - CLI terminal
  - `tui/*.py` - TUI components
  - `compositor/*.py` - Terminal compositor

---

## API Reference by Domain

### Core APIs

| API                | Purpose           | Path                                |
| ------------------ | ----------------- | ----------------------------------- |
| Session Management | Session lifecycle | `session/manager.py`                |
| Task Execution     | Run tasks         | `orchestration/execution/engine.py` |
| Agent Registry     | Agent lookup      | `agents/registry.py`                |
| Tool Registry      | Tool discovery    | `mcp/server_tool_loader.py`         |

### Mobile APIs

| API                | Purpose             | Path                            |
| ------------------ | ------------------- | ------------------------------- |
| Device Control     | Launch/interact     | `automation/mobile.py`          |
| Desktop Automation | OS-level automation | `automation/macos_desktop.py`   |
| Virtual Desktops   | VM management       | `automation/virtual_desktop.py` |

### Governance APIs

| API           | Purpose                | Path                        |
| ------------- | ---------------------- | --------------------------- |
| Security Scan | Vulnerability scanning | `governance/scanner.py`     |
| Compliance    | Policy checking        | `governance/compliance.py`  |
| Attestation   | Provenance             | `governance/attestation.py` |

---

## Data Models

### Core Entities

| Entity  | Schema                    | Storage  |
| ------- | ------------------------- | -------- |
| Agent   | `agents/models.py`        | Registry |
| Session | `session/models.py`       | State    |
| Task    | `orchestration/models.py` | Queue    |
| Tool    | `mcp/tool_schema.py`      | Registry |
| Policy  | `governance/policy.py`    | Files    |

---

## Integration Points

### External Services

| Service       | Integration  | Path                          |
| ------------- | ------------ | ----------------------------- |
| LLM Providers | Multiple     | `routing/`                    |
| Git           | Native + CLI | `native/git_native.py`        |
| Claude Code   | Protocol     | `agents/codex_proxy.py`       |
| Cursor        | API          | `agents/cursor_api_runner.py` |

---

## Configuration

### Settings

| Config      | Location               | Purpose         |
| ----------- | ---------------------- | --------------- |
| Core        | `config.py`            | Main settings   |
| Environment | Environment vars       | Runtime         |
| Policies    | `governance/policies/` | Policy files    |
| Contracts   | `contracts/`           | ABI definitions |

---

## Testing

| Test Type   | Location             | Coverage     |
| ----------- | -------------------- | ------------ |
| Unit        | `tests/unit/`        | Core modules |
| Integration | `tests/integration/` | Cross-module |
| E2E         | `tests/e2e/`         | Full flows   |
| Performance | `bench/`             | Benchmarks   |

---

## Documentation

| Doc           | Location                | Purpose     |
| ------------- | ----------------------- | ----------- |
| API Reference | Generated               | MCP tools   |
| CLI Help      | Inline                  | Commands    |
| Architecture  | This index              | Overview    |
| Migration     | `LOC_REDUCTION_PLAN.md` | Python→Rust |

---

## Version

- **Last Updated**: 2026-02-22
- **Macro Version**: 2.1.0 (SemVer)
- **Micro Version**: sess_xxx.001.017
- **Status**: Living document
