# Maintenance Runbook

Operational procedures for maintaining the portfolio quality ecosystem.

---

## Monthly Checks

### Review Linting Rules

1. Check ruff changelog for new rules that should be enabled
2. Run `ruff check --select ALL . 2>&1 | head -50` in each project to see what new rules catch
3. If a new rule category is valuable, add it to all project `pyproject.toml` files
4. Verify all projects pass: `task gate` in each

### Update Templates

1. Review `thegent/templates/` for staleness
2. Check if any project has diverged from templates (compare `pyproject.toml` settings)
3. Update templates if projects have discovered better patterns
4. Run `task gate` in all projects after template changes

### Dependency Audit

1. Run `pip-audit` in each Python project
2. Run `npm audit` in each TypeScript project
3. Update pinned versions in `pyproject.toml` / `package.json`
4. Re-run tests after updates

---

## Adding New Projects

### Procedure

1. Create project directory with standard structure
2. Copy `pyproject.toml` from `jobhunter/backend/pyproject.toml` as template
3. Customize project name, description, dependencies
4. Set `line-length = 100` in `[tool.ruff]`
5. Create `Taskfile.yml` using `jobhunter/Taskfile.yml` as template
6. Include shared templates from `thegent/templates/`
7. Create `CLAUDE.md` following `jobhunter/CLAUDE.md` pattern
8. Copy `.pre-commit-config.yaml` and `.editorconfig` from existing project
9. Run `task gate` to verify everything passes
10. Update this runbook's project list

### Verification checklist

- [ ] `task lint` passes with zero errors
- [ ] `task typecheck` passes
- [ ] `task test` passes
- [ ] `task format:check` passes
- [ ] `task security` passes
- [ ] `task gate` passes all 9 gates
- [ ] CLAUDE.md has all required sections
- [ ] Line length is 100 in pyproject.toml

---

## Handling Lint Rule Changes

### Adding a new rule across all projects

1. Add rule to `thegent/templates/python/Taskfile.python.yml` or the shared quality config
2. For each project:
   - Add rule to `[tool.ruff.lint] select` in `pyproject.toml`
   - Run `ruff check .` to see violations
   - Fix violations (prefer fixes over ignores)
   - Add per-file-ignores only with inline justification
3. Run `task gate` in each project
4. Update `docs/guides/DEVELOPER_QUICKSTART.md` if the rule affects common patterns

### Removing a rule

1. Remove from all project `pyproject.toml` files
2. Remove any per-file-ignores for that rule
3. Run `task lint` to verify no side effects

---

## Managing Pre-commit Hook Updates

1. Check for new hook versions: `pre-commit autoupdate` in each project
2. Review the diff in `.pre-commit-config.yaml`
3. Run `pre-commit run --all-files` to verify
4. Commit updated config

---

## Security Scanning

### Routine (automated via `task security`)

- `bandit -r src/` -- Python security linting
- `pip-audit` -- dependency vulnerability check
- `npm audit` -- JS dependency vulnerabilities

### Full audit (quarterly or before releases)

1. Run `semgrep --config=p/security-audit src/` in Python projects
2. Run `gitleaks detect` for secret detection
3. Check OWASP dependency-check for deeper analysis
4. Document findings in `docs/reports/`

---

## Coverage Regression Handling

When coverage drops below threshold:

1. Run `pytest --cov=src --cov-report=term-missing` to identify uncovered lines
2. Check git log for recent changes that reduced coverage
3. Write tests for uncovered paths (prioritize: error paths, edge cases, new code)
4. Verify coverage is restored: `task test:cov`
5. If coverage cannot be restored immediately, document the gap and create a follow-up task

### Coverage thresholds

| Project   | Threshold |
| --------- | --------- |
| trace     | 90%       |
| sharecli  | 80%       |
| thegent   | 80%       |
| jobhunter | 80%       |

---

## Complexity Ratchet Management

The complexity ratchet ensures complexity never increases. Baseline auto-tightens.

### When a function exceeds limits

| Metric                | Limit    | Action                                       |
| --------------------- | -------- | -------------------------------------------- |
| Cyclomatic complexity | 10       | Extract helper functions, simplify branching |
| Cognitive complexity  | 15       | Reduce nesting, extract early returns        |
| Function length       | 40 lines | Split into smaller functions                 |
| Max arguments         | 6        | Use config/dataclass parameter object        |

### Adjusting the ratchet

The ratchet should only tighten, never loosen. If a new baseline is needed:

1. Document the justification
2. Update the baseline file
3. Create a follow-up task to reduce complexity back below the old threshold

---

## Dependency Updates and CVE Handling

### Routine updates

1. `uv lock --upgrade` (Python) or `bun update` (TS) in each project
2. Run full test suite after updates
3. Check for breaking changes in changelogs

### CVE response

1. Run `pip-audit` / `npm audit` to identify affected packages
2. Check if the CVE is exploitable in our usage
3. If exploitable: update immediately, run tests, deploy
4. If not exploitable: schedule update within 1 week
5. Document in `docs/reports/` if significant

---

## Decision Matrix

| Situation                             | Action                                                                       |
| ------------------------------------- | ---------------------------------------------------------------------------- |
| Lint rule adds many violations        | Fix incrementally; add per-file-ignores with justification for now           |
| Coverage drops below threshold        | Block merges until coverage is restored                                      |
| Security CVE (high/critical)          | Immediate update + test + deploy                                             |
| Security CVE (low/medium)             | Schedule within 1 week                                                       |
| Template change breaks a project      | Fix the project, not the template (unless template is wrong)                 |
| New tool version has breaking changes | Pin to working version, schedule migration                                   |
| Agent instruction conflict            | Global CLAUDE.md wins; project CLAUDE.md overrides for domain-specific rules |
| Complexity ratchet violation          | Refactor the function; never raise the limit                                 |
