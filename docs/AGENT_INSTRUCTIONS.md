# Cross-Project Agent Instructions

This document defines the universal agent rules that apply across all projects in the portfolio (trace, heliosShield, thegent, jobhunter). Each project's `CLAUDE.md` contains project-specific overrides; this document provides the rationale and enforcement details behind every shared rule.

---

## Why These Rules Exist

Every rule here was selected based on observed failure modes in agent-generated code. Each rule has a measurable enforcement mechanism -- no aspirational guidelines, only verifiable constraints.

| Evidence Source | Finding | Rule Category |
|----------------|---------|---------------|
| Hook-backed rules | 3x better adherence than documentation-only | All enforced rules below |
| Decision tables | 1.8x fewer "wrong library" mistakes | Library Preferences |
| Few-shot examples | 2x fewer anti-pattern occurrences | Code Quality examples |
| Verifiable constraints | 2.5x adherence over vague guidelines | Complexity, coverage, security |

---

## 1. Development Philosophy

### 1.1 Extend, Never Duplicate

- NEVER create a v2 file. Refactor the original.
- NEVER create a new class if an existing one can be made generic.
- NEVER create custom implementations when an OSS library exists.
- Before writing ANY new code: search the codebase for existing patterns.

**Why:** Duplicate code is the #1 source of agent-introduced tech debt. Agents tend to create new files rather than understanding and extending existing ones.

### 1.2 Primitives First

- Build generic building blocks before application logic.
- A provider interface + registry is better than N isolated classes.
- Template strings > hardcoded messages. Config-driven > code-driven.

**Why:** Agents that skip abstraction create tightly coupled code that is hard to extend. Registries and interfaces are the foundation of maintainable agent-generated code.

### 1.3 Research Before Implementing

- Check project deps (pyproject.toml, package.json, go.mod) for existing libraries.
- Search PyPI/npm/pkg.go.dev before writing custom code.
- For non-trivial algorithms: check GitHub for 80%+ implementations to fork/adapt.

**Why:** Agents default to writing from scratch. Existing libraries are better tested, documented, and maintained.

---

## 2. Library Preferences (Decision Table)

| Need | Use | NOT | Why |
|------|-----|-----|-----|
| Retry/resilience | tenacity | Custom retry loops | Tenacity handles exponential backoff, jitter, stop conditions |
| HTTP client | httpx | Custom wrappers | Async-native, connection pooling, timeout management |
| Logging | structlog | print() or logging.getLogger | Structured output, context binding, processor pipeline |
| Config | pydantic-settings | Manual env parsing | Type-safe, validation, nested config, env prefix |
| CLI | typer | argparse | Type hints as CLI args, auto-generated help, rich output |
| Validation | pydantic (Python) / zod (TS) | Manual if/else | Schema validation, serialization, error messages |
| Rate limiting | tenacity + asyncio.Semaphore | Custom rate limiter class | Composable, well-tested, no custom state management |

**Enforcement:** The `post-edit-checker.sh` hook scans for anti-pattern imports (argparse, manual os.environ.get patterns) and emits warnings.

---

## 3. Code Quality Non-Negotiables

### Rules

1. **Zero new lint suppressions without inline justification**
   - Acceptable format: suppression directive followed by `--` and a reason
   - Enforced by: `suppression-blocker.sh` (PreToolUse:Write, PreToolUse:Edit)

2. **All code must pass: linter + type checker + tests**
   - Python: `ruff check` + type checker + `pytest`
   - Bash: `shellcheck`
   - TS: `oxlint` + `tsc`
   - Enforced by: `pre-write-validator.sh`, `quality-gate.sh`

3. **Max function: 40 lines. Max cognitive complexity: 15.**
   - Enforced by: `complexity-ratchet.sh` (Stop event)
   - Cyclomatic complexity: <= 10

4. **No placeholder TODOs in committed code**
   - Patterns: "TODO: implement", "TODO: add", "pass with TODO"
   - Enforced by: `post-edit-checker.sh` (AI slop detection)

### Few-Shot Examples

```python
# Bad -- custom retry with sleep
for attempt in range(5):
    try:
        result = httpx.get(url)
        break
    except Exception:
        time.sleep(2**attempt)


# Good -- tenacity decorator
@retry(stop=stop_after_attempt(5), wait=wait_exponential())
def fetch(url: str) -> httpx.Response:
    return httpx.get(url, timeout=10)
```

```python
# Bad -- manual env parsing with silent fallback
db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")


# Good -- pydantic-settings with type safety
class Settings(BaseSettings):
    database_url: str = "sqlite:///local.db"
    model_config = SettingsConfigDict(env_prefix="APP_")
```

```bash
# Bad -- hardcoded paths
LOG_DIR="/tmp/app/logs"

# Good -- env var with default
LOG_DIR="${APP_LOG_DIR:-/tmp/app/logs}"
```

---

## 4. Verifiable Constraints

| Metric | Threshold | Enforcement | Command |
|--------|-----------|-------------|---------|
| Test coverage | >= 80% | pytest cov-fail-under | `pytest --cov-fail-under=80` |
| Cyclomatic complexity | <= 10 | complexity-ratchet hook | Hook auto-runs on Stop |
| Cognitive complexity | <= 15 | complexity-ratchet hook | Hook auto-runs on Stop |
| Code duplication | < 5% | jscpd threshold | `jscpd --threshold 5` |
| Security findings | 0 high/critical | security-pipeline hook | bandit + gitleaks on Stop |
| Dead code | 0 unused imports | quality-gate hook | ruff F401 / oxlint |

---

## 5. How Enforcement Works

### Hook Pipeline

The enforcement system operates through lifecycle hooks that fire at specific events:

| Event | What Fires | What It Checks |
|-------|-----------|----------------|
| PreToolUse:Write | suppression-blocker, pre-write-validator, doc-location-guard | New suppressions, syntax, doc placement |
| PreToolUse:Edit | suppression-blocker, pre-write-validator | New suppressions, syntax |
| PostToolUse:Write/Edit | post-edit-checker, change-doc-tracker | AI slop, complexity, doc updates |
| Stop | quality-gate, complexity-ratchet, security-pipeline, spec-verifier | Full quality audit |

### Verification Flow

```
Code Change --> PreToolUse hooks (block bad changes)
           --> PostToolUse hooks (warn on patterns)
           --> Stop event (full audit: lint + security + coverage + traceability)
           --> Verdict: VERIFIED or GAPS
```

### What Happens on Failure

- **PreToolUse hooks**: Block the write/edit. Agent must fix before proceeding.
- **PostToolUse hooks**: Advisory warnings. Agent should address but is not blocked.
- **Stop hooks**: Advisory report. Quality findings are logged for next session.

---

## 6. Cross-Project Consistency

### Shared Patterns

All projects share these patterns:
- **Provider registry** for extensible services (not hardcoded switch statements)
- **Port/adapter boundaries** (hexagonal architecture) for external dependencies
- **Config-driven behavior** via pydantic-settings (not env var parsing)
- **Taskfile.yml** as build system (not Makefile)
- **Process-compose** for service orchestration where applicable

### Project-Specific Overrides

| Project | Stack | Build | Package Manager | Extra Tools |
|---------|-------|-------|-----------------|-------------|
| trace | Bash + Python | Taskfile | uv | shellcheck, shfmt |
| heliosShield | Multi-language | Taskfile | uv + bun | shellcheck |
| thegent | Python (MCP) | Taskfile | uv | tach, FastMCP |
| jobhunter | Python + TypeScript | Taskfile | uv + bun | process-compose |

### Where to Find Domain Rules

| Project | CLAUDE.md | Deep-Dive Guide |
|---------|-----------|----------------|
| trace | `trace/CLAUDE.md` | Bash scripting toolkit, orchestration patterns |
| heliosShield | `heliosShield/CLAUDE.md` | `docs/guides/AGENT_INSTRUCTIONS_heliosShield.md` |
| thegent | `thegent/CLAUDE.md` | `docs/guides/AGENT_INSTRUCTIONS_THEGENT.md` |
| jobhunter | `jobhunter/CLAUDE.md` | `docs/guides/AGENT_INSTRUCTIONS_JOBHUNTER.md` |

---

## See also

- [WORK_STREAM.md](reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](plans/00-MASTER-INDEX.md) — plan index
- [CLAUDE_CORE_GUIDELINES.md](reference/CLAUDE_CORE_GUIDELINES.md) — core guidelines
