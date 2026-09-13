# CLAUDE.md Governance Files - Creation Summary

**Date**: 2026-02-21
**Status**: COMPLETED
**Scope**: task-tool and morph projects

---

## Overview

Created project-level `CLAUDE.md` governance files for two previously ungoverned Python projects. These files close a critical governance gap and provide AI agents (and human developers) with clear, actionable project standards.

---

## Files Created

### 1. `/Users/kooshapari/temp-PRODVERCEL/485/kush/task-tool/CLAUDE.md`

**Size**: 226 lines (6.1 KB)

**Content**:

- Stack and Defaults table (Python 3.12+, uv, pytest, mypy, ruff)
- Dev environment setup (one-time, build, tests, quality gates)
- Project structure overview
- Configuration management (Pydantic Settings)
- Library-First policy table (httpx, typer, FastMCP, pydantic-settings, etc.)
- Code style constraints (40 LOC max, complexity ≤10, 100 char line length)
- Testing strategy with pytest markers (cli, server, telemetry, integration, client_process)
- Common commands quick reference
- Opinionated quality rules

**Key Details**:

- FastMCP server project for Task Tool platform
- Uses `uv` as package manager
- Requires Python 3.12+ (CPython only)
- Type checking via mypy (strict target)
- Test coverage target: 80%+
- Comprehensive pytest markers for test organization

---

### 2. `/Users/kooshapari/temp-PRODVERCEL/485/kush/morph/CLAUDE.md`

**Size**: 278 lines (7.4 KB)

**Content**:

- Stack and Defaults table (Python 3.11–3.13, uv, pytest, zuban, ruff)
- Dev environment setup
- Project structure overview (hexagonal architecture)
- Configuration management
- Library-First policy table (httpx, FastMCP, Supabase, zuban, etc.)
- Code style constraints
- Testing strategy with integration focus
- Ruff configuration details (comprehensive rule set)
- Common commands quick reference
- Opinionated quality rules with hexagonal architecture emphasis
- Python version support matrix
- MCP and integration notes

**Key Details**:

- MCP server with hexagonal architecture
- Uses `uv` as package manager
- Supports Python 3.11–3.13 (not 3.14 yet)
- Type checking via zuban (high-performance, replaces mypy)
- Async-first design (httpx, aiohttp, asyncio)
- Integrations: Supabase, Pheno SDK, Scholarly
- Document processing (Markdown, DOCX, HTML, PDF)

---

## Governance Alignment

Both CLAUDE.md files:

1. **Reference global policy** (`~/.claude/CLAUDE.md`) for baseline rules
2. **Inherit key policies**:
   - No fallbacks or legacy compatibility
   - Security rules (no process killing)
   - Library-First pattern
   - Fail-fast philosophy

3. **Define project-specific standards**:
   - Language version constraints
   - Tool versions (ruff, mypy/zuban, pytest)
   - Dev setup procedures
   - Quality gates and test strategies
   - Code style limits (max 40 LOC, complexity ≤10)

4. **Follow standard structure**:
   - Stack and Defaults table
   - Dev Environment Setup
   - Project Structure
   - Library Choices with rationale
   - Code Style & Constraints
   - Testing Strategy
   - Common Commands (Quick Ref)
   - Opinionated Quality Rules

---

## Key Differences Between Projects

| Aspect           | task-tool                                                                | morph                 |
| ---------------- | ------------------------------------------------------------------------ | --------------------- |
| **Python**       | 3.12+ (fixed)                                                            | 3.11–3.13 (range)     |
| **Type Checker** | mypy (strict)                                                            | zuban (high-perf)     |
| **Build System** | Hatchling                                                                | Hatchling + hatch-vcs |
| **Architecture** | FastMCP server                                                           | Hexagonal + FastMCP   |
| **Database**     | None noted                                                               | Supabase              |
| **Async**        | AsyncIO (httpx)                                                          | Full async-first      |
| **Test Markers** | 6 markers (cli, server, telemetry, integration, client_process, asyncio) | Standard pytest       |

---

## Standards Enforced

### Both Projects

✓ Line length: 100 (ruff enforced)
✓ Max function: 40 LOC
✓ Max cyclomatic: 10
✓ Type hints required
✓ No fallbacks or legacy compat
✓ Fail-fast, no silent errors
✓ Library-First for generic needs
✓ Test coverage target: 80%+
✓ No TODOs/FIXMEs without tracking
✓ Lint passes before commit

---

## Usage for Agents & Developers

When working on either project, refer to the respective `CLAUDE.md`:

```bash
# task-tool
cat /Users/kooshapari/temp-PRODVERCEL/485/kush/task-tool/CLAUDE.md

# morph
cat /Users/kooshapari/temp-PRODVERCEL/485/kush/morph/CLAUDE.md
```

### Quick Setup (task-tool)

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/task-tool
uv sync --group dev
source .venv/bin/activate
uv run pytest && uv run ruff check --fix task_tool tests && uv run mypy task_tool
```

### Quick Setup (morph)

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/morph
uv sync --group dev
source .venv/bin/activate
uv run pytest && uv run ruff check --fix . && uv run zuban morph
```

---

## Quality Gate Verification

Both files define identical quality gate patterns:

1. **Lint**: `ruff check --fix` (zero violations)
2. **Type check**: `mypy` (task-tool) / `zuban` (morph) with no suppressions
3. **Tests**: `pytest` with 80%+ coverage
4. **Integration**: Run full gate before committing

---

## Future Maintenance

### Triggers for Update

- Python version upgrade (3.13→3.14)
- Tool version change (ruff, mypy, zuban)
- New dependency addition
- Architecture change

### Review Cadence

- Quarterly: Refresh tool versions
- Semi-annually: Audit library choices against new alternatives
- On tool release: Update version constraints

---

## Appendix: File Locations

```
/Users/kooshapari/temp-PRODVERCEL/485/kush/
├── task-tool/
│   ├── CLAUDE.md (NEW)
│   ├── pyproject.toml
│   ├── README.md
│   └── task_tool/ (source)
├── morph/
│   ├── CLAUDE.md (NEW)
│   ├── pyproject.toml
│   ├── README.md
│   └── morph/ (source)
└── thegent/
    ├── CLAUDE.md (reference)
    └── docs/reference/CLAUDE_*.md (global baseline)
```

---

## Governance Gap Closure

**Before**: task-tool and morph had NO project-level governance. Developers/agents lacked:

- Clear library preferences
- Type checking standards
- Test coverage targets
- Code style constraints
- Quality gate procedures

**After**: Both projects now have comprehensive, actionable governance that:

- Aligns with global policy
- Specifies project-specific tool choices
- Enforces code quality standards
- Provides quick-ref commands
- Documents testing strategy

**Status**: ✓ CRITICAL GOVERNANCE GAP CLOSED

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
