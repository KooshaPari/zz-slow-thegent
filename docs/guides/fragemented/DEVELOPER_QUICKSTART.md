# Developer Quickstart

Quick reference for developers and agents working in the portfolio projects (trace, sharecli, thegent, jobhunter).

---

## Commands

All projects use `task` (go-task). Run these from any project root:

```bash
task lint          # Run all linters
task test          # Run all tests
task format        # Auto-format code
task typecheck     # Run type checkers
task quality       # Full quality check (lint + typecheck + test:cov + security)
task gate          # 9-gate quality system (strictest)
task security      # Security scanning
task complexity    # Complexity check
task test:cov      # Tests with coverage
task --list        # See all available tasks
```

### Backend-specific (Python projects)

```bash
task py:lint           # ruff check
task py:format         # ruff format
task py:typecheck      # ty check
task py:test           # pytest
task py:test:cov       # pytest with coverage
task py:security       # bandit + pip-audit
```

### Frontend-specific (TypeScript projects)

```bash
task ts:lint           # oxlint
task ts:format         # prettier
task ts:typecheck      # tsc --noEmit
task ts:test           # vitest
task ts:build          # production build
```

---

## Common Lint Errors and Fixes

### Python (ruff)

| Error     | Meaning                 | Fix                                                     |
| --------- | ----------------------- | ------------------------------------------------------- |
| `E501`    | Line too long           | Handled by formatter -- run `task format`               |
| `F401`    | Unused import           | Remove the import                                       |
| `F841`    | Unused variable         | Remove or prefix with `_`                               |
| `S101`    | `assert` in production  | Move to test files or use `raise`                       |
| `UP035`   | Deprecated import       | Use the modern import path                              |
| `B008`    | Mutable default arg     | Use `None` default + assign in body                     |
| `ANN001`  | Missing type annotation | Add type hint to parameter                              |
| `C901`    | Too complex             | Break function into smaller pieces (max complexity: 10) |
| `PLR0913` | Too many args           | Use a config dataclass or reduce parameters (max: 6)    |
| `SIM102`  | Collapsible `if`        | Combine with `and`                                      |

### TypeScript (oxlint)

| Error             | Meaning         | Fix                        |
| ----------------- | --------------- | -------------------------- |
| `no-unused-vars`  | Unused variable | Remove or prefix with `_`  |
| `no-explicit-any` | `any` type used | Add proper type annotation |
| `no-console`      | `console.log`   | Use proper logger          |

---

## Adding New Features

### Following Hexagonal Architecture

1. **Define the port** (interface) in `ports/` or `domain/`
2. **Implement the adapter** in `adapters/`
3. **Wire in application layer** via `application/` (use cases)
4. **Expose via API** in `adapters/api/` or routes

### Python backend pattern

```
src/projectname/
  domain/        # Business logic (no external deps)
  ports/         # Abstract interfaces
  adapters/      # Concrete implementations
  application/   # Use cases / orchestration
  config/        # pydantic-settings
```

### TypeScript frontend pattern

```
src/
  features/      # Feature slices (self-contained)
  shared/        # Shared components, hooks, utils
  app/           # App shell, routing
```

---

## Library Preferences

When adding new functionality, prefer these libraries over custom implementations:

| Need          | Python              | TypeScript |
| ------------- | ------------------- | ---------- |
| HTTP client   | httpx               | fetch / ky |
| Validation    | pydantic            | zod        |
| Config        | pydantic-settings   | --         |
| CLI           | typer               | --         |
| Logging       | structlog / loguru  | --         |
| Retry         | tenacity            | --         |
| Testing       | pytest + hypothesis | vitest     |
| Serialization | msgspec             | --         |

---

## Quality Thresholds

| Metric                | Threshold              |
| --------------------- | ---------------------- |
| Test coverage         | >= 80% (90% for trace) |
| Cyclomatic complexity | <= 10 per function     |
| Cognitive complexity  | <= 15 per function     |
| Max function length   | 40 lines               |
| Code duplication      | < 5%                   |
| Line length           | 100 characters         |
| Security findings     | 0 high/critical        |

---

## Project Locations

| Project   | Path         | Description                                   |
| --------- | ------------ | --------------------------------------------- |
| trace     | `trace/`     | Agent-native requirements traceability system |
| sharecli  | `sharecli/`  | Unified CLI for agent harness                 |
| thegent   | `thegent/`   | Agent orchestration + governance MCP server   |
| jobhunter | `jobhunter/` | Full-stack job hunting application            |

---

## Getting Help

- Run `task --list` for available commands
- Check project `CLAUDE.md` for project-specific rules
- Check `docs/guides/MODERNIZATION_IMPLEMENTATION_GUIDE.md` for ecosystem maintenance
- Architecture questions: consult the team lead
