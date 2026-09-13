# Portfolio Modernization Implementation Guide

Guide for agents maintaining and extending the cross-project quality modernization ecosystem.

---

## 1. Taskfile Targets

Every project uses `task` (go-task) with shared templates from `thegent/templates/`. Available targets:

| Target              | What it does                                                          |
| ------------------- | --------------------------------------------------------------------- |
| `task lint`         | Run all linters (ruff for Python, oxlint for TS, shellcheck for Bash) |
| `task test`         | Run all test suites                                                   |
| `task format`       | Auto-format all source files                                          |
| `task typecheck`    | Run type checkers (ty for Python, tsc for TS)                         |
| `task quality`      | Run lint + typecheck + test:cov + security                            |
| `task gate`         | Run full 9-gate quality system                                        |
| `task security`     | Run security scanners (bandit, pip-audit, npm audit)                  |
| `task complexity`   | Check cyclomatic/cognitive complexity                                 |
| `task format:check` | Check formatting without modifying files                              |
| `task test:cov`     | Run tests with coverage reporting                                     |

Run `task --list` in any project for the full target list.

---

## 2. Adding New Projects to the Ecosystem

### Step-by-step

1. **Create project Taskfile.yml** in the project root. Use `jobhunter/Taskfile.yml` as the reference template.

2. **Include shared templates** from thegent:

   ```yaml
   includes:
     py:
       taskfile: ../thegent/templates/python/Taskfile.python.yml
       optional: true
       vars:
         PYTHON_SRC: "src"
         PYTHON_TESTS: "tests"
     quality:
       taskfile: ../thegent/templates/shared/Taskfile.quality.yml
       optional: true
   ```

3. **Copy quality config** from templates into the project:
   - `pyproject.toml` -- use `jobhunter/backend/pyproject.toml` as the canonical template
   - `.pre-commit-config.yaml` -- copy from any existing project
   - `.editorconfig` -- copy from any existing project

4. **Set ruff line-length to 100** in `[tool.ruff]` section of `pyproject.toml`.

5. **Create CLAUDE.md** with agent instructions following the pattern in `jobhunter/CLAUDE.md`:
   - Development Philosophy section
   - Library Preferences table
   - Code Quality Non-Negotiables
   - Verifiable Constraints table
   - Domain-specific patterns

6. **Verify** by running `task gate` in the new project.

---

## 3. The 9-Gate Quality System

The gate system runs sequentially. Each gate must pass before the next runs.

| Gate | Check                    | Tool                                       |
| ---- | ------------------------ | ------------------------------------------ |
| 1    | Formatting               | `ruff format --check` / `prettier --check` |
| 2    | Linting                  | `ruff check` / `oxlint` / `shellcheck`     |
| 3    | Type checking            | `ty check` / `tsc --noEmit`                |
| 4    | Unit tests               | `pytest -m unit` / `vitest`                |
| 5    | Integration tests        | `pytest -m integration`                    |
| 6    | Coverage threshold       | `pytest --cov --cov-fail-under=80`         |
| 7    | Security scanning        | `bandit` / `pip-audit` / `npm audit`       |
| 8    | Complexity check         | `radon` / cyclomatic + cognitive limits    |
| 9    | Architecture enforcement | `import-linter` / `tach check`             |

### Extending the gate system

To add a new gate:

1. Edit `thegent/templates/shared/Taskfile.quality.yml`
2. Add a new task following the naming pattern `gate:NN:name`
3. Add it to the `gate` task's dependency list
4. Update this guide with the new gate description

---

## 4. Adding New Linting Rules

### Ruff (Python)

1. Add the rule code to `[tool.ruff.lint] select` in `pyproject.toml`
2. Run `ruff check .` to see new violations
3. Fix violations or add targeted per-file-ignores with justification
4. Coordinate: update all four project `pyproject.toml` files for consistency

### Oxlint (TypeScript)

1. Edit `.oxlintrc.json` or add rules to the oxlint config
2. Run `oxlint .` to check new violations
3. Fix or add targeted ignores

### golangci-lint (Go)

1. Edit `.golangci.yml` in the Go project root
2. Add the linter to the `enable` list
3. Run `golangci-lint run` to verify

### Cross-project coordination

When adding rules that affect multiple projects, update all projects in a single pass. Use the parent-level docs as the source of truth for which rules are standard.

---

## 5. Hexagonal Architecture via import-linter

Architecture boundaries are enforced via `import-linter` (Python) or `tach` (Python).

### Configuration

In `pyproject.toml`:

```toml
[tool.importlinter]
root_packages = ["mypackage"]

[[tool.importlinter.contracts]]
name = "Core layered architecture"
type = "layers"
layers = [
    "config",
    "db",
    "models",
    "repositories",
    "services",
    "api",
]
containers = ["mypackage"]
```

### Adding new layers

1. Add the layer name to the `layers` list in the correct position (lower = inner)
2. Create the corresponding package directory
3. Run `lint-imports` to verify no violations
4. Update forbidden-module contracts if the new layer has special restrictions

### Forbidden imports

Use `type = "forbidden"` contracts to prevent outer layers from reaching into inner layers directly:

```toml
[[tool.importlinter.contracts]]
name = "API must not access DB directly"
type = "forbidden"
source_modules = ["mypackage.api"]
forbidden_modules = ["mypackage.db", "mypackage.repositories"]
```

---

## 6. Common Agent Instruction Patterns

All project CLAUDE.md files share a common structure:

1. **Project header** -- project name, brief description
2. **Build system** -- how to run tasks
3. **Development Philosophy** -- extend-never-duplicate, primitives-first, research-first
4. **Library Preferences** -- decision table (Use / NOT columns)
5. **Code Quality Non-Negotiables** -- lint, type check, test requirements
6. **Verifiable Constraints** -- metrics table with thresholds and enforcement mechanisms
7. **Architecture Pattern** -- project-specific directory layout
8. **Domain-specific rules** -- where to add new functionality

When creating a new project CLAUDE.md, copy the structure from `jobhunter/CLAUDE.md` and customize the domain-specific sections.

---

## 7. Template Customization

Templates live in `thegent/templates/`:

```
templates/
  python/           # Python-specific Taskfile + config templates
  typescript/       # TypeScript-specific Taskfile + config templates
  bash/             # Bash/shell Taskfile + config templates
  shared/           # Cross-language quality gate Taskfile
```

### Customizing for a project

- Templates are included via Taskfile `includes` with variable overrides
- Override `PYTHON_SRC`, `PYTHON_TESTS`, `TS_SRC`, etc. in the project Taskfile
- For project-specific rules, add to the project's own `pyproject.toml` rather than modifying templates
- Templates define the baseline; projects extend

### Updating templates

1. Edit the template in `thegent/templates/`
2. All projects that include the template pick up changes automatically
3. Run `task gate` in each project to verify no regressions
