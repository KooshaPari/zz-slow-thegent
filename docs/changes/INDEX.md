# Python Infrastructure Modernization - Change Proposals Index

**Date:** 2025-10-29  
**Status:** Planning Phase

---

## Overview

This directory contains detailed change proposals for modernizing Python infrastructure across all projects in the kush repository. Each change proposal is a comprehensive, implementation-ready document designed for execution by specialized agents.

---

## Change Proposal Structure

Each change proposal follows this structure:

1. **Header:** Project name, priority, complexity, effort, risk
2. **Current State Analysis:** Strengths and issues
3. **Proposed Changes:** Detailed phase-by-phase changes
4. **Migration Steps:** Step-by-step implementation guide
5. **Rollback Plan:** How to revert if needed
6. **Success Criteria:** Measurable outcomes
7. **Risks & Mitigations:** Identified risks and solutions
8. **Dependencies:** What must be done first
9. **Follow-up Tasks:** Post-implementation work

---

## Tier 1: Production Critical Projects

### 1. atoms-mcp-prod

**File:** `ATOMS_MCP_PROD_INFRASTRUCTURE_MODERNIZATION.md`  
**Priority:** CRITICAL  
**Status:** ✅ Complete  
**Effort:** 40 hours  
**Key Changes:**

- Hybrid .env (Vercel) + YAML (local) configuration
- Pydantic-settings with type-safe config
- Enhanced code quality tools (vulture, cloc)
- Pre-commit hooks

### 2. zen-mcp-server

**File:** `ZEN_MCP_SERVER_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** HIGH
**Status:** ✅ Complete
**Effort:** 30 hours
**Key Changes:**

- Standardize configuration approach
- Clean up legacy files
- Add missing quality tools
- Documentation updates

### 3. router (krouter)

**File:** `ROUTER_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** HIGH
**Status:** ✅ Complete
**Effort:** 50 hours
**Key Changes:**

- Optimize ML/AI dependencies
- YAML configuration for router settings
- Architecture refactoring (hexagonal)
- Performance optimization

---

## Tier 2: SDK/Library Projects

### 4. pheno-sdk

**File:** `PHENO_SDK_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** HIGH
**Status:** ✅ Complete
**Effort:** 50 hours
**Key Changes:**

- Strengthen hexagonal architecture
- Clean public API boundaries
- Comprehensive configuration system
- Enhanced testing infrastructure

### 5. crun

**File:** `CRUN_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** MEDIUM
**Status:** ✅ Complete
**Effort:** 40 hours
**Key Changes:**

- Standardize with other projects
- YAML configuration migration
- Code quality enhancements
- Multi-agent orchestration patterns

### 6. morph

**File:** `MORPH_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** MEDIUM
**Status:** ✅ Complete
**Effort:** 30 hours
**Key Changes:**

- Simplify dependencies
- YAML configuration
- Library replacements (quick wins)
- MCP creation patterns

---

## Tier 3: Tool/Utility Projects

### 7. agentapi/atomsAgent

**File:** `ATOMS_AGENT_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** HIGH
**Status:** ✅ Complete
**Effort:** 20 hours
**Key Changes:**

- Hybrid .env + YAML (like atoms-mcp-prod)
- Code generation patterns
- Vercel deployment optimization

### 8. bloc

**File:** `BLOC_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** LOW
**Status:** ✅ Complete
**Effort:** 10 hours
**Key Changes:**

- Quick modernization
- Simple CLI patterns
- Code analysis tool optimization

### 9. task-tool

**File:** `TASK_TOOL_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** MEDIUM
**Status:** ✅ Complete
**Effort:** 15 hours
**Key Changes:**

- MCP server standardization
- YAML configuration
- Task management patterns

### 10. spec_toolkit

**File:** `SPEC_TOOLKIT_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** LOW
**Status:** ✅ Complete
**Effort:** 20 hours
**Key Changes:**

- Maintain hexagonal architecture
- Specification patterns
- Modern tooling

### 11. usage

**File:** `USAGE_INFRASTRUCTURE_MODERNIZATION.md`
**Priority:** LOW
**Status:** ✅ Complete
**Effort:** 15 hours
**Key Changes:**

- Python side only
- Hybrid project patterns
- Usage tracking optimization

---

## Implementation Order

### Phase 1: Foundation (Week 1) ✅ COMPLETE

1. ✅ Create all change proposals
2. ✅ Create templates and patterns
3. ✅ Setup CI/CD templates

### Phase 2: Tier 1 (Weeks 2-4)

1. **atoms-mcp-prod** (Week 2)
2. **router** (Week 3)
3. **zen-mcp-server** (Week 4)

### Phase 3: Tier 2 (Weeks 5-7)

1. **pheno-sdk** (Weeks 5-6)
2. **crun** (Week 6)
3. **morph** (Week 7)

### Phase 4: Tier 3 (Weeks 8-9)

1. **agentapi/atomsAgent** (Week 8)
2. **task-tool** (Week 8)
3. **bloc** (Week 9)
4. **spec_toolkit** (Week 9)
5. **usage** (Week 9)

### Phase 5: Documentation & Validation (Weeks 10-11)

1. Documentation
2. Knowledge transfer
3. Validation
4. Cleanup

---

## Common Patterns Across Projects

### Pattern 1: Hybrid Configuration (Vercel Projects)

**Projects:** atoms-mcp-prod, agentapi/atomsAgent

```python
@classmethod
def load(cls):
    if os.getenv("VERCEL"):
        return cls()  # Environment variables
    else:
        return cls.from_yaml()  # YAML files
```

### Pattern 2: Standard YAML Configuration

**Projects:** All others

```yaml
# config.yml
app:
  name: "project-name"
  debug: false

# secrets.yml
api_keys:
  openai: "sk-..."
```

### Pattern 3: Hexagonal Architecture

**Projects:** pheno-sdk, spec_toolkit, router

```
project/
├── domain/          # Business logic
├── application/     # Use cases
├── adapters/        # External integrations
└── infrastructure/  # Framework code
```

### Pattern 4: MCP Server Patterns

**Projects:** atoms-mcp-prod, zen-mcp-server, task-tool, morph

- FastMCP integration
- Tool registration
- Resource management
- Prompt handling

---

## Quick Wins Library Replacements

### Common Across Projects

1. **Custom logging → structlog/loguru**
2. **Custom config → pydantic-settings**
3. **Custom validation → pydantic**
4. **Custom retry → tenacity**
5. **Custom caching → cachetools/aiocache**
6. **Custom CLI → typer**
7. **Custom serialization → msgspec**

### Project-Specific

- **router:** Custom ML routing → routellm integration
- **pheno-sdk:** Custom infrastructure → standardized adapters
- **crun:** Custom orchestration → langgraph patterns

---

## Templates & Reusable Components

### 1. Standard pyproject.toml Template

**File:** `templates/pyproject.toml.template`

- Build system (hatch)
- Dependencies structure
- Tool configurations (ruff, mypy, pytest)
- UV configuration

### 2. Pydantic Settings Template

**File:** `templates/settings.py.template`

- Base settings class
- YAML loading
- Environment variable support
- Secrets handling

### 3. Pre-commit Hooks Template

**File:** `templates/.pre-commit-config.yaml`

- Ruff linting/formatting
- Standard hooks
- Bandit security

### 4. GitHub Actions Template

**File:** `templates/.github/workflows/ci.yml`

- UV setup
- Test running
- Code quality checks
- Coverage reporting

---

## Metrics & Success Criteria

### Per-Project Metrics

- [ ] No requirements.txt files
- [ ] No .env files (except Vercel projects)
- [ ] uv.lock present and working
- [ ] Ruff passing
- [ ] Tests passing
- [ ] Coverage > 70%
- [ ] Type coverage > 60%
- [ ] Bandit passing
- [ ] Vulture < 5% dead code

### Global Metrics

- [ ] All 11 projects modernized
- [ ] Consistent patterns across projects
- [ ] Documentation complete
- [ ] Team trained
- [ ] CI/CD updated

---

## Agent Handoff Instructions

### For Implementation Agents

Each change proposal is designed for independent execution. To implement:

1. **Read the change proposal** thoroughly
2. **Follow the migration steps** exactly as written
3. **Test at each phase** before proceeding
4. **Document any deviations** from the plan
5. **Update the change proposal** if you discover issues
6. **Mark success criteria** as you complete them
7. **Create a summary report** when done

### For Review Agents

When reviewing implementations:

1. **Check success criteria** are all met
2. **Verify tests pass** and coverage is adequate
3. **Review code quality** metrics
4. **Test configuration loading** in different environments
5. **Validate documentation** is updated
6. **Approve or request changes**

---

## Status Tracking

| Project        | Change Proposal | Implementation | Testing | Documentation | Status |
| -------------- | --------------- | -------------- | ------- | ------------- | ------ |
| atoms-mcp-prod | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| zen-mcp-server | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| router         | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| pheno-sdk      | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| crun           | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| morph          | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| atomsAgent     | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| bloc           | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| task-tool      | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| spec_toolkit   | ✅              | ⏳             | ⏳      | ⏳            | Ready  |
| usage          | ✅              | ⏳             | ⏳      | ⏳            | Ready  |

Legend: ✅ Complete | ⏳ Pending | 🚧 In Progress | ❌ Blocked

---

## Next Steps

1. ✅ Create master plan
2. ✅ Create WBS
3. ✅ Create atoms-mcp-prod change proposal
4. ✅ Create remaining change proposals
5. ✅ Create templates
6. ⏳ Begin implementation (Week 2)

---

## Contact & Support

For questions or issues with change proposals:

- Review the master plan: `PYTHON_INFRASTRUCTURE_MODERNIZATION_MASTER_PLAN.md`
- Review the WBS: `PYTHON_INFRASTRUCTURE_WBS.md`
- Check templates in `templates/` directory
- Consult work-prompts in `zen-mcp-server/work-prompts/`
