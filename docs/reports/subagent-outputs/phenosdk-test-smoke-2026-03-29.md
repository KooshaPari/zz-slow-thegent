# phenoSDK — tests, lint, and local smoke (subagent report)

**Worktree:** `/Users/kooshapari/CodeProjects/Phenotype/repos/worktrees/phenoSDK/main`  
**Date:** 2026-03-29

## 1. Config files (presence)

| File             | Present | Notes                                                              |
| ---------------- | ------- | ------------------------------------------------------------------ |
| `pyproject.toml` | Yes     | Root package `pheno-sdk`; Ruff extends `ruff.toml`; pytest options |
| `setup.cfg`      | No      | —                                                                  |
| `tox.ini`        | No      | —                                                                  |
| `Makefile`       | Yes     | Includes `makefiles/quality.mk`, `testing.mk`, `ci.mk`, `deps.mk`  |
| `Taskfile.yml`   | No      | —                                                                  |

### 1.1 `pyproject.toml` — exact tool settings

**Ruff**

```toml
[tool.ruff]
extend = "ruff.toml"
```

**Pytest**

```toml
[tool.pytest.ini_options]
addopts = "-q"
testpaths = ["test"]
```

**Dev dependencies (excerpt):** optional extra `[project.optional-dependencies] dev` includes `pytest>=8.3.3`, `pytest-asyncio`, `pytest-cov`, `pytest-mock`, `hypothesis`, `ruff>=0.6.3`, etc. Install with `pip install -e ".[dev]"` (or equivalent).

**Note:** `Makefile` `install-dev` uses `pip install -e ".[dev,test]"`; there is no `test` optional dependency group in root `pyproject.toml` — use `.[dev]` for tooling.

### 1.2 `ruff.toml` (referenced by pyproject)

- `target-version = "py311"`
- Large `[lint]` rule `select` list (E, F, I, W, C4, SIM, RET, PL, RUF, PIE, PGH, UP, PYI, S, B, …)
- `extend-exclude` includes `src`, `tests`, `test`, `examples`, `scripts`, `tools`, vendored trees, `.venv`, etc.

### 1.3 `Makefile` / included makefiles — intended commands

From `makefiles/quality.mk`:

| Target         | Command(s)                                                                                            |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| `lint`         | `ruff check . --statistics`                                                                           |
| `lint-fix`     | `ruff check . --fix`                                                                                  |
| `format`       | `ruff format .` then `black .`, `isort . --profile black`, `docformatter --in-place --recursive src/` |
| `format-check` | `black --check .`, `isort --check-only . --profile black`, `docformatter --check --recursive src/`    |
| `type-check`   | `mypy src/ --explicit-package-bases \|\| true`                                                        |

From `makefiles/testing.mk`:

| Target         | Command(s)                                                           |
| -------------- | -------------------------------------------------------------------- |
| `test`         | `pytest -q`                                                          |
| `test-verbose` | `pytest -v`                                                          |
| `test-quick`   | `pytest -x --ff`                                                     |
| `test-cov`     | `pytest --cov=src/pheno --cov-report=term-missing --cov-report=html` |

From `makefiles/ci.mk`:

| Target      | Command(s)                                                             |
| ----------- | ---------------------------------------------------------------------- |
| `ci-lint`   | `ruff check . --statistics`                                            |
| `ci-format` | `black --check .`; `isort --check-only . --profile black`              |
| `ci-test`   | `pytest --cov=src/pheno --cov-report=term-missing --cov-report=xml -v` |
| `ci-all`    | `ci-install` then `ci-check` then `ci-test`                            |

**Makefile variable caveat:** `makefiles/common.mk` defines `RUFF ?= ruff`, `PYTEST ?= pytest`, etc., but the root `Makefile` does **not** include `common.mk`. A dry-run of `make -n lint` expands to `check . --statistics` (missing `ruff`). To use Make targets as written, either include `makefiles/common.mk` from the root `Makefile` or invoke with explicit variables, e.g. `make RUFF=ruff PYTEST=pytest lint test`.

Top-level `Makefile` also defines `dev: format lint test` (format + lint + test).

---

## 2. GitHub Actions (first three workflows by filename)

Sorted basename order under `.github/workflows/` (excluding `.cicd-backups/`).

### 2.1 `analytics-dashboard.yml`

- **Workflow name:** Quality Analytics Dashboard
- **Sample job:** `data-collection` — display name `1. Quality Metrics Data Collection`
- **Relevant steps:** Python 3.13; `pip install pydantic requests pandas numpy matplotlib seaborn plotly dash` (analytics stack); repository metrics collection — **not** the primary pytest/ruff gate for SDK code.

### 2.2 `architecture-fitness-2.yml`

- **Workflow name:** Architecture Fitness
- **Job:** `fitness` — **Architecture Guardrails**
- **Env:** `PYTEST_ADDOPTS: "-p no:cov -p no:pytest_benchmark"`
- **Commands (examples):**
  - `pip install pytest pytest-asyncio`
  - `scripts/install_pheno_sdk.sh --upgrade --no-deps` (SSH / secrets)
  - `pytest tests/architecture/test_import_boundaries.py -v --tb=short`
  - `pytest tests/architecture/test_file_sizes.py -v --tb=short -s`
  - `pytest tests/architecture/test_dependency_direction.py -v --tb=short`
  - (further steps continue for naming, etc.)

### 2.3 `architecture-fitness.yml`

- **Workflow name:** Architecture Fitness Compliance
- **Jobs / names:**
  - `file-size-validation` — File Size Enforcement (500 LOC limit): `pip install radon`; `python scripts/checks/check_file_size.py --max-lines 500 $(find src/ -name "*.py")`
  - `import-boundary-validation` — Import Boundary Validation: `python scripts/checks/validate_kit_boundaries.py $(find src/pheno/ -name "*.py")`
  - `dependency-direction-validation` — Dependency Direction Checks: `pip install pylint`; `python scripts/architectural_pattern_validator.py --dependency-direction`
  - `naming-convention-validation` — Naming Convention Enforcement: (file continues)

---

## 3. Recommended local smoke (single sequence)

From repo root (`worktrees/phenoSDK/main`), after a dev install:

```bash
cd /Users/kooshapari/CodeProjects/Phenotype/repos/worktrees/phenoSDK/main
python -m pip install -e ".[dev]"
ruff check . --statistics
pytest -q
```

**Optional stricter alignment with `make ci-check` + coverage (still direct commands):**

```bash
ruff check . --statistics && black --check . && isort --check-only . --profile black && pytest --cov=src/pheno --cov-report=term-missing -q
```

**If you prefer Make** (workaround for missing `common.mk` include):

```bash
make RUFF=ruff PYTEST=pytest lint test
```

Pytest discovers tests under `test/` per `pyproject.toml` `testpaths`.
