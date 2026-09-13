# Changelog

All notable changes to **thegent** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Multi-language support (English, Chinese Simplified/Traditional, Persian, Pinglish)
- Agent governance framework with persona definitions
- MCP (Model Context Protocol) server integration
- Hook system for lifecycle events (pre/post tool execution)
- Quality gates for code validation

### Changed

- Migrated from atoms_mcp_server to zen_mcp_server architecture
- Hexagonal architecture split for better modularity

### Known Issues

- GitHub Pages asset path configuration needs manual base URL setting

---

## [2026.02] - 2026-02

### Infrastructure Modernization

#### ATOMS Agent Infrastructure

- **Status**: Completed
- **Files**: `changes/ATOMS_AGENT_INFRASTRUCTURE_MODERNIZATION.md`
- Modernized agent infrastructure from atoms to production-ready state

#### ATOMS MCP Production Infrastructure

- **Status**: Completed
- **Files**: `changes/ATOMS_MCP_PROD_INFRASTRUCTURE_MODERNIZATION.md`
- MCP server production deployment and operations

#### BLOC Infrastructure

- **Status**: Completed
- **Files**: `changes/BLOC_INFRASTRUCTURE_MODERNIZATION.md`
- Infrastructure modernization for BLOC component

#### CRUN Infrastructure

- **Status**: Completed
- **Files**: `changes/CRUN_INFRASTRUCTURE_MODERNIZATION.md`
- Container runtime infrastructure improvements

#### MORPH Infrastructure

- **Status**: Completed
- **Files**: `changes/MORPH_INFRASTRUCTURE_MODERNIZATION.md`
- Morph component infrastructure

#### PHENO SDK Infrastructure

- **Status**: Completed
- **Files**: `changes/PHENO_SDK_INFRASTRUCTURE_MODERNIZATION.md`
- Phenotype SDK integration and infrastructure

#### Router Infrastructure

- **Status**: Completed
- **Files**: `changes/ROUTER_INFRASTRUCTURE_MODERNIZATION.md`
- Router component modernization

#### SPEC Toolkit Infrastructure

- **Status**: Completed
- **Files**: `changes/SPEC_TOOLKIT_INFRASTRUCTURE_MODERNIZATION.md`
- Specification toolkit infrastructure

#### Task Tool Infrastructure

- **Status**: Completed
- **Files**: `changes/TASK_TOOL_INFRASTRUCTURE_MODERNIZATION.md`
- Task tool infrastructure

#### Usage Infrastructure

- **Status**: Completed
- **Files**: `changes/USAGE_INFRASTRUCTURE_MODERNIZATION.md`
- Usage tracking infrastructure

#### Zen MCP Server

- **Status**: Completed
- **Files**: `changes/ZEN_MCP_SERVER_INFRASTRUCTURE_MODERNIZATION.md`
- Zen MCP server production infrastructure

---

### Research Tracks

| Track                    | Status      | Documentation                                |
| ------------------------ | ----------- | -------------------------------------------- |
| Hook Rust Phase 1        | ✅ Complete | `changes/research-hook-rust-phase1/`         |
| Hook Rust Phase 2        | ✅ Complete | `changes/research-hook-rust-phase2/`         |
| Cross-platform Isolation | ✅ Complete | `changes/research-cross-platform-isolation/` |
| Cross-platform Shell     | ✅ Complete | `changes/research-cross-platform-shell/`     |
| Compute Offload          | ✅ Complete | `changes/research-compute-offload/`          |
| Economic Governance      | ✅ Complete | `changes/research-economic-governance/`      |
| Idea Seed System         | ✅ Complete | `changes/research-idea-seed-system/`         |
| Library Cache            | ✅ Complete | `changes/research-library-cache/`            |
| Library Retry            | ✅ Complete | `changes/research-library-retry/`            |
| MAIF Artifacts           | ✅ Complete | `changes/research-maif-artifacts/`           |
| Pareto Routing           | ✅ Complete | `changes/research-pareto-routing/`           |
| Simulation Replay        | ✅ Complete | `changes/research-simulation-replay/`        |
| Supermemory Integration  | ✅ Complete | `changes/research-supermemory-integration/`  |
| TUI Compositor           | ✅ Complete | `changes/research-tui-compositor/`           |

---

### Wave 70 Execution (2026-02-22)

| Lane   | Status      | Items                             |
| ------ | ----------- | --------------------------------- |
| Lane 1 | ✅ Complete | Quality system audit, 2026 models |
| Lane 2 | ✅ Complete | CLI examples, feature parity      |
| Lane 3 | ✅ Complete | Documentation updates             |
| Lane 4 | ✅ Complete | Router improvements               |
| Lane 5 | ✅ Complete | Integration work                  |
| Lane 6 | ✅ Complete | Infrastructure fixes              |
| Lane 7 | ✅ Complete | Testing and validation            |

**Details**: `reports/2026-02-22-worklog-wave70-master.md`

---

### OpenRouter Integration

- WebSocket Authorization header fix
- Provider type registration
- LiteLLM router configuration
- Model ID mappings
- SSE keep-alive parsing

**Source**: `docs/plans/2026-02-20-OPENROUTER-FULL-INTEGRATION-PLAN.md`

---

### Quality Gate Improvements

- Disk capacity management (bounded scans)
- JSCPD configuration with ignore globs
- File-size and runtime caps for gitleaks
- Max attempts and prompt char limits

**Source**: `docs/plans/2026-02-20-QUALITY-RUN-RESOURCE-AUDIT-AND-OPTIMIZATION-PLAN.md`

---

## Historical Changes

See `changes/archive/` for older change logs.

---

## Upgrade Notes

### From 2025.x to 2026.x

1. **New Dependencies**: Ensure `zen-mcp-server` is installed
2. **Configuration**: Review `config/` for new schema
3. **Database**: Run migrations for quality system changes
4. **CLI**: Updated command structure - run `thegent --help`

### Breaking Changes

- `thegent run` now requires explicit `--sandbox` flag
- Quality gates are enforced by default
- MCP server requires authentication

---

## Credits

Thanks to all contributors and the AI agents who participated in Wave 70 execution.

---

_Last updated: 2026-02-23_
_This changelog is automatically generated from `changes/` and `reports/` directories._
