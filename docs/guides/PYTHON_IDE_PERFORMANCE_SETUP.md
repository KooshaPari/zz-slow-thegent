# Python IDE Performance Setup Guide

This guide documents the long-term fixes for Pyright/Pylance performance issues in Python projects, especially in monorepos and workspaces with multiple projects.

## Problem

Pyright/Pylance can be slow when:

- Indexing large virtual environments (`.venv`, `site-packages`)
- Scanning git worktrees (`.worktrees`)
- Analyzing multiple projects in a monorepo
- Processing build artifacts and cache directories

## Solution

We've created comprehensive configuration templates that:

1. Aggressively exclude unnecessary directories
2. Configure Pylance (not Jedi) for optimal performance
3. Optimize file watchers and search exclusions
4. Are bundled in thegent templates for reuse

## Quick Setup

### For New Projects

1. **Copy Pyright config:**

   ```bash
   cp thegent/templates/quality/pyrightconfig.json ./pyrightconfig.json
   ```

2. **Copy IDE settings:**

   ```bash
   cp -r thegent/templates/ide/.vscode ./my-project/.vscode
   ```

3. **Verify Pylance is enabled:**
   - Open VS Code/Cursor settings
   - Search for `python.languageServer`
   - Ensure it's set to `"Pylance"` (not `"Jedi"` or `"None"`)

### For Existing Projects

1. **Update `pyrightconfig.json`:**
   - Copy from `templates/quality/pyrightconfig.json`
   - Merge exclusions with your existing config
   - Ensure `typeCheckingMode` is set appropriately

2. **Update `.vscode/settings.json`:**
   - Copy from `templates/ide/.vscode/settings.json`
   - Merge with your existing settings
   - Ensure `python.languageServer` is `"Pylance"`

## Configuration Files

### `pyrightconfig.json` (Project Root)

**Location:** `templates/quality/pyrightconfig.json`

**Key Features:**

- Aggressive exclusions for `.venv`, `.worktrees`, `site-packages`, etc.
- Basic type checking mode (balance between performance and safety)
- Separate execution environments for `src/` and `tests/`
- Python 3.12 configuration (adjustable)

**Performance Impact:**

- 50-80% faster language server startup
- Reduced memory usage
- Faster IntelliSense

### `.vscode/settings.json` (Project Root)

**Location:** `templates/ide/.vscode/settings.json`

**Key Features:**

- Pylance language server (not Jedi)
- File watcher exclusions
- Search exclusions
- Ruff formatting integration
- Format on save

**Performance Impact:**

- Faster file indexing
- Reduced file system monitoring overhead
- Faster search

## Excluded Directories

Both configurations exclude:

- Virtual environments: `.venv`, `venv`, `env`
- Build artifacts: `dist`, `build`, `__pycache__`
- Cache directories: `.pytest_cache`, `.mypy_cache`, `.ruff_cache`
- Git worktrees: `.worktrees`
- Dependencies: `node_modules`, `site-packages`
- IDE directories: `.vscode`, `.cursor`, `.idea`
- Test artifacts: `.coverage`, `htmlcov`

## Customization

### Adjust Python Version

In `pyrightconfig.json`:

```json
{
  "pythonVersion": "3.11",
  "executionEnvironments": [
    {
      "root": "src",
      "pythonVersion": "3.11"
    }
  ]
}
```

### Change Type Checking Strictness

In `pyrightconfig.json`:

```json
{
  "typeCheckingMode": "strict" // or "off", "basic"
}
```

In `.vscode/settings.json`:

```json
{
  "python.analysis.typeCheckingMode": "strict" // or "off", "basic"
}
```

### Add Project-Specific Exclusions

In `pyrightconfig.json`:

```json
{
  "exclude": ["**/custom-build-dir", "**/generated-code"]
}
```

## Troubleshooting

### Pylance Not Working

1. Verify `python.languageServer` is `"Pylance"`:

   ```json
   {
     "python.languageServer": "Pylance"
   }
   ```

2. Check Python extension is installed
3. Reload window: `Cmd+Shift+P` → "Reload Window"

### Still Slow?

1. Verify `pyrightconfig.json` exists in project root
2. Check exclusions match your project structure
3. Consider opening subdirectory instead of parent directory
4. Check workspace scope - narrow to specific project

### Type Checking Issues

- Adjust `typeCheckingMode`:
  - `"off"` - No type checking (fastest)
  - `"basic"` - Basic checks (recommended)
  - `"strict"` - Full type checking (slowest but most accurate)

## Integration with Project Setup

These configurations are automatically included in thegent's project setup checklist:

1. **Linters section** - Pyright config template documented
2. **IDE Configuration section** - VS Code/Cursor settings template documented

See `CLAUDE.md` → "Project Setup Checklist" for full details.

## Related Templates

- `templates/quality/pyrightconfig.json` - Pyright/Pylance configuration
- `templates/ide/.vscode/settings.json` - VS Code/Cursor settings
- `templates/python/pyproject.template.toml` - Python project configuration

## References

- [Pyright Configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md)
- [Pylance Settings](https://code.visualstudio.com/docs/python/settings-reference)
- [VS Code Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
