# Python Infrastructure Modernization - Change Proposals

This directory contains detailed change proposals for modernizing Python infrastructure across all projects in the kush repository.

---

## What Are Change Proposals?

Change proposals are comprehensive, implementation-ready documents that provide:
- **Current state analysis** - What exists today
- **Proposed changes** - What needs to change
- **Migration steps** - How to implement the changes
- **Rollback plan** - How to revert if needed
- **Success criteria** - How to know when done
- **Risks & mitigations** - What could go wrong and how to handle it

Each change proposal is designed to be executed by specialized implementation agents who follow instructions well but may not be strong at architecture or planning.

---

## Directory Structure

```
changes/
├── README.md                                          # This file
├── INDEX.md                                           # Index of all change proposals
├── ATOMS_MCP_PROD_INFRASTRUCTURE_MODERNIZATION.md    # atoms-mcp-prod (✅ Complete)
├── ROUTER_INFRASTRUCTURE_MODERNIZATION.md            # router (✅ Complete)
├── ZEN_MCP_SERVER_INFRASTRUCTURE_MODERNIZATION.md    # zen-mcp-server (📝 To create)
├── PHENO_SDK_INFRASTRUCTURE_MODERNIZATION.md         # pheno-sdk (📝 To create)
├── CRUN_INFRASTRUCTURE_MODERNIZATION.md              # crun (📝 To create)
├── MORPH_INFRASTRUCTURE_MODERNIZATION.md             # morph (📝 To create)
├── ATOMS_AGENT_INFRASTRUCTURE_MODERNIZATION.md       # atomsAgent (📝 To create)
├── BLOC_INFRASTRUCTURE_MODERNIZATION.md              # bloc (📝 To create)
├── TASK_TOOL_INFRASTRUCTURE_MODERNIZATION.md         # task-tool (📝 To create)
├── SPEC_TOOLKIT_INFRASTRUCTURE_MODERNIZATION.md      # spec_toolkit (📝 To create)
└── USAGE_INFRASTRUCTURE_MODERNIZATION.md             # usage (📝 To create)
```

---

## How to Use These Change Proposals

### For Implementation Agents

1. **Read the change proposal** for your assigned project
2. **Follow the migration steps** exactly as written
3. **Test at each phase** before proceeding to the next
4. **Document deviations** if you need to change the plan
5. **Update the change proposal** if you discover issues
6. **Mark success criteria** as you complete them
7. **Create a summary report** when done

### For Review Agents

1. **Check success criteria** are all met
2. **Verify tests pass** and coverage is adequate
3. **Review code quality** metrics
4. **Test configuration loading** in different environments
5. **Validate documentation** is updated
6. **Approve or request changes**

### For Project Managers

1. **Track progress** using the status table in INDEX.md
2. **Assign work** based on priority and dependencies
3. **Monitor risks** especially for high-risk projects
4. **Coordinate** between projects with dependencies
5. **Review** completed work before moving to next tier

---

## Change Proposal Template

Each change proposal follows this structure:

```markdown
# Change Proposal: [Project Name] Infrastructure Modernization

**Project:** [project-name]
**Priority:** [CRITICAL|HIGH|MEDIUM|LOW]
**Complexity:** [HIGH|MEDIUM|LOW]
**Estimated Effort:** [X hours]
**Risk Level:** [HIGH|MEDIUM|LOW]

## Current State Analysis
### Strengths
### Issues

## Proposed Changes
### Phase 1: [Name] (X hours)
### Phase 2: [Name] (X hours)
### Phase 3: [Name] (X hours)
### Phase 4: [Name] (X hours)

## Migration Steps
### Step 1: [Name]
### Step 2: [Name]
...

## Rollback Plan
## Success Criteria
## Risks & Mitigations
## Dependencies
## Follow-up Tasks
```

---

## Implementation Priority

### Tier 1: Production Critical (Weeks 2-4)
1. **atoms-mcp-prod** (Week 2) - ✅ Change proposal complete
2. **router** (Week 3) - ✅ Change proposal complete
3. **zen-mcp-server** (Week 4) - 📝 To create

### Tier 2: SDK/Libraries (Weeks 5-7)
4. **pheno-sdk** (Weeks 5-6) - 📝 To create
5. **crun** (Week 6) - 📝 To create
6. **morph** (Week 7) - 📝 To create

### Tier 3: Tools/Utilities (Weeks 8-9)
7. **atomsAgent** (Week 8) - 📝 To create
8. **task-tool** (Week 8) - 📝 To create
9. **bloc** (Week 9) - 📝 To create
10. **spec_toolkit** (Week 9) - 📝 To create
11. **usage** (Week 9) - 📝 To create

---

## Common Patterns

### Pattern 1: Hybrid Configuration (Vercel Projects)
Used by: atoms-mcp-prod, atomsAgent

```python
@classmethod
def load(cls):
    if os.getenv("VERCEL"):
        return cls()  # Environment variables
    else:
        return cls.from_yaml()  # YAML files
```

### Pattern 2: Standard YAML Configuration
Used by: All other projects

```yaml
# config.yml (non-sensitive, git-tracked)
app:
  name: "my-app"
  debug: false

# secrets.yml (sensitive, git-ignored)
api_keys:
  openai: "sk-..."
```

### Pattern 3: Hexagonal Architecture
Used by: pheno-sdk, spec_toolkit, router

```
project/
├── domain/          # Business logic
├── application/     # Use cases
├── adapters/        # External integrations
└── infrastructure/  # Framework code
```

---

## Quick Reference

### Standard Tools
- **uv** - Package manager
- **ruff** - Linter and formatter
- **hatch** - Build system
- **pydantic-settings** - Configuration
- **bandit** - Security scanner
- **vulture** - Dead code detector
- **mypy/zuban** - Type checker

### Standard Files
- `pyproject.toml` - Project configuration
- `uv.lock` - Dependency lock file
- `config.yml` - Non-sensitive configuration
- `secrets.yml` - Sensitive configuration (git-ignored)
- `secrets.yml.example` - Template for secrets
- `.pre-commit-config.yaml` - Pre-commit hooks

### Standard Commands
```bash
# Setup
uv venv
uv pip install -e ".[dev]"
uv lock

# Quality
ruff check --fix .
ruff format .
bandit -r .
vulture .

# Testing
pytest
pytest --cov=.
```

---

## Status Tracking

See `INDEX.md` for the current status of all change proposals and implementations.

---

## Creating New Change Proposals

When creating a new change proposal:

1. **Copy the template** from an existing change proposal
2. **Analyze the project** thoroughly
3. **Identify current state** (strengths and issues)
4. **Plan phases** (Foundation, Configuration, Quality, Architecture)
5. **Estimate effort** realistically
6. **Identify risks** and mitigation strategies
7. **Define success criteria** clearly
8. **Write migration steps** in detail
9. **Plan rollback** strategy
10. **Review and refine**

---

## Getting Help

### Documentation
- Master plan: `../PYTHON_INFRASTRUCTURE_MODERNIZATION_MASTER_PLAN.md`
- WBS: `../PYTHON_INFRASTRUCTURE_WBS.md`
- Summary: `../PYTHON_INFRASTRUCTURE_SUMMARY.md`
- Quick start: `../QUICK_START_IMPLEMENTATION_GUIDE.md`

### Architecture Patterns
- Hexagonal architecture: `../zen-mcp-server/work-prompts/python-patterns-guide.md`
- TDD patterns: `../zen-mcp-server/work-prompts/tdd-architecture-prompts.md`

### Examples
- Completed change proposals in this directory
- Existing modern projects: zen-mcp-server, crun

---

## Contributing

When updating change proposals:

1. **Document changes** clearly
2. **Update status** in INDEX.md
3. **Maintain structure** of the template
4. **Keep it detailed** - implementers need specifics
5. **Test your changes** before committing

---

## Questions?

If you have questions about:
- **Overall strategy** - See the master plan
- **Specific project** - See that project's change proposal
- **Implementation** - See the quick start guide
- **Architecture** - See work-prompts in zen-mcp-server

---

## License

These change proposals are part of the kush repository and follow the same license.

