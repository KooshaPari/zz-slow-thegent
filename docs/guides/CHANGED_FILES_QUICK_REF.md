# Changed Files Advanced Filtering - Quick Reference

Phase 1.5 enhancement to `thegent-hooks changed-files` provides advanced filtering, dependency analysis, and impact classification for complex workflows.

## Quick Examples

### Get Code-Impacting Changes Only

```bash
# Excludes documentation, config file changes
thegent-hooks changed-files-impact HEAD~5..HEAD
```

Output: JSON array of file paths that affect code logic

### Filter Python Files in src/

```bash
thegent-hooks changed-files-filter \
  --extension py \
  --directory src

# Output:
# [
#   {"path": "src/main.py", "status": "Modified", "impact": "CodeImpacting"},
#   {"path": "src/utils.py", "status": "Added", "impact": "CodeImpacting"}
# ]
```

### Get All Files Changed in Tests

```bash
thegent-hooks changed-files-filter \
  --directory tests \
  --impact tests

# Output: JSON array of test file changes with metadata
```

### Analyze Dependencies Between Changed Files

```bash
thegent-hooks changed-files-deps HEAD~1..HEAD

# Output:
# {
#   "src/main.py": {
#     "depends_on": ["src/utils.py", "src/config.py"]
#   },
#   "src/utils.py": {
#     "depends_on": ["src/helpers.py"]
#   }
# }
```

### Include Reverse Dependencies (What Depends On Each File)

```bash
thegent-hooks changed-files-deps --dependents

# Output shows both "depends_on" and "depended_by" for each file
```

## Filter Types Reference

### `--extension` / `-e`

Filter by file extension.

```bash
# Get only TypeScript/JavaScript files
thegent-hooks changed-files-filter --extension ts --extension js

# Get only Python files
thegent-hooks changed-files-filter -e py

# Multiple extensions (OR logic)
thegent-hooks changed-files-filter -e py -e rs -e go
```

### `--directory` / `-d`

Filter by directory path.

```bash
# Files in src/
thegent-hooks changed-files-filter --directory src

# Files in tests/
thegent-hooks changed-files-filter -d tests

# Multiple directories (OR logic)
thegent-hooks changed-files-filter -d src -d tests
```

### `--status` / `-s`

Filter by git change status.

```bash
# Only modified files (not new)
thegent-hooks changed-files-filter --status modified

# Only added files
thegent-hooks changed-files-filter --status added

# Deleted files
thegent-hooks changed-files-filter --status deleted

# Untracked files
thegent-hooks changed-files-filter --status untracked

# Combined (OR logic)
thegent-hooks changed-files-filter -s modified -s added
```

### `--impact` / `-i`

Filter by impact classification.

**Impact Types:**

- `code` - Affects source code logic
- `docs` - Documentation only (no code impact)
- `config` - Configuration files
- `tests` - Test files
- `build` - Build/CI files
- `other` - Unclassified

```bash
# Code-impacting changes only
thegent-hooks changed-files-filter --impact code

# Configuration changes
thegent-hooks changed-files-filter -i config

# Multiple impact types (OR logic)
thegent-hooks changed-files-filter -i tests -i build
```

### `--exclude-extension`

Exclude files by extension.

```bash
# Python files, but not __pycache__
thegent-hooks changed-files-filter \
  --extension py \
  --exclude-extension pyc

# All files except Markdown
thegent-hooks changed-files-filter --exclude-extension md
```

### `--exclude-directory`

Exclude files by directory.

```bash
# All files except node_modules
thegent-hooks changed-files-filter --exclude-directory node_modules

# src files except vendor
thegent-hooks changed-files-filter \
  --directory src \
  --exclude-directory src/vendor
```

### `--range` / `-r`

Git revision range (default: `HEAD~1..HEAD`).

```bash
# Last 5 commits
thegent-hooks changed-files-filter -r HEAD~5..HEAD

# Compare branches
thegent-hooks changed-files-filter -r main..feature-branch

# Since tag
thegent-hooks changed-files-filter -r v1.0.0..HEAD
```

## Output Formats

### `changed-files` (Basic)

```json
["src/main.py", "tests/test.py", "README.md"]
```

Simple JSON array of file paths. Same as Phase 1.

### `changed-files-filter` (Detailed)

```json
[
  {
    "path": "src/main.py",
    "status": "Modified",
    "impact": "CodeImpacting"
  },
  {
    "path": "README.md",
    "status": "Added",
    "impact": "DocsOnly"
  },
  {
    "path": "tests/test.py",
    "status": "Modified",
    "impact": "Tests"
  }
]
```

JSON array with full metadata. Useful for agent processing.

### `changed-files-impact` (Code-Only)

```json
["src/main.py", "tests/test.py", "src/utils.py"]
```

JSON array of paths that have code impact. Excludes docs/config/build files.

### `changed-files-deps` (Dependency Graph)

```json
{
  "src/main.py": {
    "depends_on": ["src/utils.py", "src/config.py"]
  },
  "src/utils.py": {
    "depends_on": ["src/helpers.py"]
  }
}
```

Dependency map for changed files. With `--dependents`:

```json
{
  "src/main.py": {
    "depends_on": ["src/utils.py"],
    "depended_by": ["tests/test_main.py", "src/cli.py"]
  }
}
```

## Real-World Use Cases

### CI/CD: Conditional Test Running

```bash
#!/bin/bash
# Only run tests if code changed

CODE_FILES=$(thegent-hooks changed-files-impact)
if [ -n "$CODE_FILES" ]; then
  echo "Code changes detected, running tests..."
  pytest tests/
else
  echo "Only docs/config changed, skipping tests"
fi
```

### Selective Linting

```bash
#!/bin/bash
# Lint only changed Python files

PYTHON_FILES=$(thegent-hooks changed-files-filter \
  --extension py \
  --exclude-directory __pycache__ \
  | jq -r '.[].path' | paste -sd ' ')

if [ -n "$PYTHON_FILES" ]; then
  ruff check $PYTHON_FILES
  mypy $PYTHON_FILES
fi
```

### Language-Specific Test Triggers

```bash
#!/bin/bash
# Run tests based on changed file types

# Python tests
if thegent-hooks changed-files-filter -e py | jq -e 'length > 0' >/dev/null; then
  pytest tests/unit/
fi

# TypeScript tests
if thegent-hooks changed-files-filter -e ts -e tsx | jq -e 'length > 0' >/dev/null; then
  npm test
fi

# Go tests
if thegent-hooks changed-files-filter -e go | jq -e 'length > 0' >/dev/null; then
  go test ./...
fi
```

### Impact Analysis

```bash
#!/bin/bash
# Show what files are impacted by changes

DEPS=$(thegent-hooks changed-files-deps)
echo "Files changed:"
echo "$DEPS" | jq 'keys[]'
echo ""
echo "All affected files (including dependents):"
thegent-hooks changed-files-deps --dependents | jq 'keys[]'
```

### Skip Flaky Tests for Doc Changes

```bash
#!/bin/bash
# Run full test suite only for code changes

IMPACT=$(thegent-hooks changed-files-filter --impact code)
if [ -z "$IMPACT" ]; then
  # Only docs/config changed, skip flaky integration tests
  pytest tests/unit/ -m "not integration"
else
  # Code changed, run everything
  pytest tests/
fi
```

### Multi-Language Project Build

```bash
#!/bin/bash
# Only build affected languages

PY_CHANGED=$(thegent-hooks changed-files-filter -e py | jq -e 'length > 0')
TS_CHANGED=$(thegent-hooks changed-files-filter -e ts -e tsx | jq -e 'length > 0')
GO_CHANGED=$(thegent-hooks changed-files-filter -e go | jq -e 'length > 0')

[ -n "$PY_CHANGED" ] && echo "Building Python..." && python -m build
[ -n "$TS_CHANGED" ] && echo "Building TypeScript..." && npm run build
[ -n "$GO_CHANGED" ] && echo "Building Go..." && go build ./...
```

### Generate Change Report

```bash
#!/bin/bash
# Generate a detailed change report

FILTER=$(thegent-hooks changed-files-filter)

echo "=== Change Summary ==="
echo "Total changed files: $(echo "$FILTER" | jq 'length')"
echo ""
echo "By Impact Type:"
echo "$FILTER" | jq -r 'group_by(.impact) | map({impact: .[0].impact, count: length}) | .[] | "\(.impact): \(.count)"'
echo ""
echo "By Status:"
echo "$FILTER" | jq -r 'group_by(.status) | map({status: .[0].status, count: length}) | .[] | "\(.status): \(.count)"'
echo ""
echo "Code-impacting changes:"
thegent-hooks changed-files-impact | jq -r '.[]'
```

## Integration with Hooks

The enhanced changed-files detection is used by multiple hooks:

| Hook                  | Usage                                                 |
| --------------------- | ----------------------------------------------------- |
| `pre-write-validator` | Detect impacted domains before file modification      |
| `post-edit-checker`   | Identify changed file categories for selective checks |
| `quality-gate`        | Filter linting based on file type and impact          |
| `suppression-blocker` | Detect suppression changes in code vs config files    |
| `ad-hoc-checks`       | Route checks based on impact classification           |

## Performance Notes

- `git diff --name-status`: ~20ms
- `git ls-files --others`: ~50ms
- Regex import parsing: Per-file analysis (100-500μs per file)
- Dependency graph build: O(n) where n = changed files
- Total for typical change: <500ms for repos with <1000 files

For large monorepos with 10,000+ files:

- Consider caching dependency graphs per commit
- Use `--range` to limit analysis scope
- Filter early to reduce dependency parsing

## Troubleshooting

### No Output / Empty Results

```bash
# Check if in a git repository
git rev-parse --show-toplevel

# Check git status
git status

# Verify range exists
git log HEAD~5..HEAD
```

### Filter Not Matching Expected Files

```bash
# Debug: Show all files with metadata
thegent-hooks changed-files-filter

# Then apply filters incrementally
thegent-hooks changed-files-filter --extension py
thegent-hooks changed-files-filter --extension py --directory src
```

### Dependency Analysis Shows No Dependencies

```bash
# Dependencies are extracted from import statements
# Verify file has proper imports:
grep -E "^(import|from)" src/main.py

# Note: Works for Python, TypeScript, Rust
# Other languages require language-specific analysis
```

## See Also

- `CHANGED_FILES_ENHANCEMENT_PHASE_1_5.md` - Full technical documentation
- `TASK_ROUTING_QUICK_REF.md` - Agent routing based on change types
- `git diff` manual - Git revision range syntax
- `git ls-files` manual - File listing options
