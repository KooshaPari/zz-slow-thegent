# Complete Type Checker Setup Guide

This guide documents the complete type checker setup for Python projects using thegent's dual-approach strategy: fast CI checks and comprehensive IDE support.

## Overview

We use **multiple type checkers** for different purposes:

| Tool                | Purpose          | Speed              | Use Case                     |
| ------------------- | ---------------- | ------------------ | ---------------------------- |
| **Pyright/Pylance** | IDE IntelliSense | Moderate           | Real-time IDE feedback       |
| **ty**              | Fast CI checking | Very Fast (10-50x) | Quick development feedback   |
| **zuban**           | Fast CI checking | Very Fast          | Complementary to ty          |
| **basedpyright**    | Strict checking  | Moderate           | CI/commit strict validation  |
| **mypy**            | Strict checking  | Moderate           | Additional strict validation |

## Architecture: Dual Approach

### IDE (Real-time)

- **Pyright/Pylance** for IntelliSense
- Optimized with aggressive exclusions
- Configuration: `pyrightconfig.json` + `.vscode/settings.json`

### CI/Linting (Batch)

- **Fast path**: `ty` + `zuban` (10-50x faster than Pyright)
- **Strict path**: `basedpyright` + `mypy` (comprehensive checking)

## Setup Instructions

### 1. Install Dependencies

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "ty>=0.0.2",
    "basedpyright>=1.12.0",
    "mypy>=1.9.0",
    "types-pyyaml>=6.0.12.20240311",
]
```

Install:

```bash
uv sync --extra dev
```

### 2. Configure Type Checkers

#### pyproject.toml

Add type checker configurations:

```toml
[tool.ty]
[tool.ty.src]
include = ["src", "tests"]
python-version = "3.12"

[tool.ty.rules]
possibly-unbound-attribute = "error"
possibly-unbound-import = "error"
unresolved-attribute = "error"
unresolved-import = "error"
invalid-type-form = "error"

[tool.basedpyright]
include = ["src", "tests"]
typeCheckingMode = "strict"
pythonVersion = "3.12"
reportMissingTypeStubs = false
reportMissingImports = true
reportUnusedImport = true
reportUnusedClass = true
reportUnusedFunction = true
reportUnusedVariable = true

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = ["tests.*", "scripts.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
```

#### pyrightconfig.json (IDE)

Copy from template:

```bash
cp thegent/templates/quality/pyrightconfig.json ./pyrightconfig.json
```

#### basedpyrightconfig.json (Optional)

For strict checking configuration:

```bash
cp thegent/templates/quality/basedpyrightconfig.json ./basedpyrightconfig.json
```

### 3. Configure IDE Settings

Copy VS Code/Cursor settings:

```bash
cp -r thegent/templates/ide/.vscode ./my-project/.vscode
```

Ensure Pylance is enabled:

```json
{
  "python.languageServer": "Pylance"
}
```

### 4. Setup Taskfile Tasks

Add to `Taskfile.yml`:

```yaml
lint:type:
  desc: "Fast static type checking (ty + zuban)"
  cmds:
    - uv run ty check src/
    - uv run zuban check src/ --disable-error-code call-overload --disable-error-code unreachable --disable-error-code assignment --disable-error-code var-annotated --disable-error-code override --disable-error-code return-value --disable-error-code arg-type --disable-error-code union-attr --disable-error-code dict-item --disable-error-code misc --disable-error-code no-redef --disable-error-code call-arg --disable-error-code operator

lint:strict:
  desc: "Strict type checking (basedpyright + mypy) - recommended for CI/commit"
  cmds:
    - uv run basedpyright src/
    - uv run mypy src/
```

### 5. Setup Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: ty
        name: Fast Type Check (ty)
        entry: uv run ty check src/
        language: system
        pass_filenames: false
        types: [python]

      - id: basedpyright
        name: Strict Type Check (basedpyright)
        entry: uv run basedpyright src/
        language: system
        pass_filenames: false
        types: [python]
```

## Usage Workflows

### Development (IDE)

- **Real-time**: Pylance provides IntelliSense as you type
- **Performance**: Optimized with `pyrightconfig.json` exclusions
- **No action needed**: Works automatically

### Pre-commit

- **Fast**: `ty` check (quick feedback)
- **Strict**: `basedpyright` check (comprehensive)

### CI Fast Path

```bash
task lint:type
```

- Runs: `ty` + `zuban`
- Speed: 10-50x faster than Pyright
- Use: Quick feedback during development

### CI Strict Path

```bash
task lint:strict
```

- Runs: `basedpyright` + `mypy`
- Speed: Moderate (comprehensive checking)
- Use: Before commits, CI pipelines

## Configuration Files Reference

### pyproject.toml Sections

| Section               | Purpose                    | Tools        |
| --------------------- | -------------------------- | ------------ |
| `[tool.ty]`           | Fast type checker config   | ty           |
| `[tool.basedpyright]` | Strict type checker config | basedpyright |
| `[tool.mypy]`         | Additional strict checking | mypy         |

### Standalone Config Files

| File                      | Purpose                    | Tool            |
| ------------------------- | -------------------------- | --------------- |
| `pyrightconfig.json`      | IDE IntelliSense           | Pyright/Pylance |
| `basedpyrightconfig.json` | Strict checking (optional) | basedpyright    |
| `.vscode/settings.json`   | IDE settings               | VS Code/Cursor  |

### Zuban Configuration

Zuban uses command-line flags (no config file):

```bash
zuban check src/ \
  --disable-error-code call-overload \
  --disable-error-code unreachable \
  # ... (see templates/quality/zuban-config.md)
```

## Performance Comparison

| Checker      | Speed                | Use Case           |
| ------------ | -------------------- | ------------------ |
| ty           | ⚡⚡⚡⚡⚡ Very Fast | Fast CI feedback   |
| zuban        | ⚡⚡⚡⚡⚡ Very Fast | Fast CI feedback   |
| Pyright      | ⚡⚡⚡ Moderate      | IDE IntelliSense   |
| basedpyright | ⚡⚡⚡ Moderate      | Strict CI checking |
| mypy         | ⚡⚡⚡ Moderate      | Strict CI checking |

## Troubleshooting

### IDE IntelliSense Slow

1. Verify `pyrightconfig.json` exists with aggressive exclusions
2. Check `.vscode/settings.json` has file watcher exclusions
3. Ensure Pylance is enabled (not Jedi)
4. Consider opening subdirectory instead of parent directory

### CI Checks Too Slow

1. Use `task lint:type` (ty + zuban) for fast feedback
2. Use `task lint:strict` (basedpyright + mypy) only for commits/CI
3. Verify exclusions in configs match your project structure

### Type Checking Inconsistencies

- **Expected**: Different checkers may report different errors
- **Solution**: Use strict checkers (basedpyright + mypy) for final validation
- **Fast checkers** (ty + zuban) prioritize speed over completeness

## Template Files

All configurations are available as templates:

- `templates/quality/pyrightconfig.json` - IDE config
- `templates/quality/basedpyrightconfig.json` - Strict checking config
- `templates/quality/ty-config.toml` - ty config template
- `templates/quality/zuban-config.md` - zuban usage guide
- `templates/python/pyproject.template.toml` - Complete pyproject.toml template
- `templates/ide/.vscode/settings.json` - IDE settings

## Best Practices

1. **IDE**: Use Pyright/Pylance (optimized with exclusions)
2. **Fast CI**: Use ty + zuban (10-50x faster)
3. **Strict CI**: Use basedpyright + mypy (comprehensive)
4. **Pre-commit**: Use ty + basedpyright (fast + strict)
5. **Keep configs separate**: IDE optimized for IntelliSense, CI optimized for speed/strictness

## Related Documentation

- [Python IDE Performance Setup](PYTHON_IDE_PERFORMANCE_SETUP.md)
- [Type Checker Migration Analysis](../../research/TYPE_CHECKER_MIGRATION_ANALYSIS.md)
- [Quality Assurance Guide](../QUALITY_ASSURANCE.md)
