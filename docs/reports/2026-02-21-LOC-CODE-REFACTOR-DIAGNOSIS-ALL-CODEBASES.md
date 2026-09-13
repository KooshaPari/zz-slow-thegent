# LOC / Code / Refactor Diagnosis — All Active Codebases (2026-02-21)

## Scope

Diagnosed active codebases and language surfaces currently used in this workspace:

1. `thegent` (polyglot primary platform)
2. `trace` (secondary shell/js governance repo)

All counts below are from fresh `tokei` runs with generated/build/cache dirs excluded.

## Executive Diagnosis

1. **thegent** is over-accumulated in Python and has multiple monolith hotspots; this is the main refactor risk surface.
2. **Rust** is comparatively healthy in size but has a few oversized files and remaining legacy dependency cleanup.
3. **Zig/Mojo** are still narrow/POC surfaces, not major LOC contributors.
4. **trace** is small but has shell monolith concentration in one quality script.

## Codebase A: thegent

### Language footprint (code lines)

- Python: `272,709`
- Rust: `29,494`
- TypeScript: `15,560`
- JSON: `10,322`
- Shell: `8,652`
- YAML: `4,971`
- TOML: `1,461`
- (others each significantly smaller)

### Refactor pressure by language

#### Python (Critical)

- Files: `1,535`
- Files >500 lines: `158`
- Files >1000 lines: `30`
- Top hotspots:
  - `src/thegent/cli/commands/cli.py` (`6843` code)
  - `src/thegent/cli/commands/impl.py` (`5786` code)
  - `tests/test_e2e_cli.py` (`4855` code)
  - `src/thegent/mcp/server.py` (`4247` code)

Diagnosis:

- Python remains a “catch-all runtime.”
- Core command/router/server surfaces are monolithic.
- Test LOC is large and co-located with runtime concerns.

Refactor direction:

1. Split `cli.py`, `impl.py`, `mcp/server.py` by bounded domains.
2. Move hot-path scanners/parsers/policy checks to Rust backmatter.
3. Separate core runtime test lanes from long-tail integration suites.

#### Rust (High but controlled)

- Files: `137`
- Files >500 lines: `12`
- Files >1000 lines: `3`
- Top hotspots:
  - `crates/thegent-hooks/src/main.rs` (`4109` code)
  - `hooks/hook-dispatcher/src/main.rs` (`2585` code)
  - `crates/thegent-shm/src/lib.rs` (`1025` code)

Diagnosis:

- Rust is sized closer to expected backmatter envelope.
- A few entrypoint files are too large and should be module-split.

Refactor direction:

1. Decompose hook mains into scanner/evaluator/policy/report modules.
2. Remove remaining legacy deps (`lazy_static`) where still present.
3. Keep Rust as primary destination for Python hot-path migration.

#### TypeScript (Low runtime risk)

- Files: `1,366`
- Dominated by docs/api stubs; no >500-line TS hotspots.

Diagnosis:

- TS surface is mostly generated/documentation artifacts, not runtime core.

Refactor direction:

1. Keep generated TS outside core runtime KPIs.
2. Enforce generation-only ownership and avoid manual drift edits.

#### Shell (Moderate risk)

- Files: `93`
- Files >500 lines: `2`
- Top hotspot:
  - `hooks/governance-gates.sh` (`1983` code)

Diagnosis:

- Core governance shell script is too large and operationally fragile.

Refactor direction:

1. Continue migration of shell governance logic to Rust binaries.
2. Keep shell as thin orchestration wrappers only.

#### Zig / Mojo (Early-stage, low LOC)

- Zig: `161` code lines (4 files)
- Mojo: `6` code lines (1 file)

Diagnosis:

- Not a LOC problem; this is a maturity/integration problem.

Refactor direction:

1. Promote Zig via ABI-contract tests before broad use.
2. Promote Mojo only for measured deterministic kernels.

## Codebase B: trace

### Language footprint (code lines)

- YAML: `1,385`
- Shell: `1,236`
- HTML: `1,042`
- JavaScript: `890`
- (small overall footprint; no Python concentration)

### Refactor pressure

- Shell hotspot:
  - `scripts/quality/quality-gate.sh` (`523` code)
  - `scripts/agent-orchestrator.sh` (`350` code)

Diagnosis:

- trace is compact; risk is mostly single-script concentration.

Refactor direction:

1. Split `quality-gate.sh` into composable checks.
2. Keep governance checks declarative/config-driven where possible.

## Cross-Codebase Refactor Priorities

1. **P0** thegent Python monolith decomposition (`cli.py`, `impl.py`, `mcp/server.py`).
2. **P0** Core/runtime boundary definition (`thegent-core`) and non-core extraction.
3. **P1** Rust hook/main file decomposition + legacy dep cleanup.
4. **P1** Shell governance reduction by moving logic to Rust backmatter.
5. **P1** CI lanes: strict fast lane vs deep nightly lane for no-regression refactors.
6. **P2** Zig ABI promotion and Mojo deterministic kernel promotion by benchmark gates.

## Success Targets

1. Reduce core Python code by >=55% from current baseline without behavior regressions.
2. Eliminate all >1000-line files in core runtime path.
3. Keep Rust/Zig/Mojo lanes contract-tested and explicitly scoped.
4. Keep shell scripts thin (<300 lines preferred, wrappers only).

## Repro Commands

```bash
# thegent
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
tokei --sort code --output json \
  --exclude .git --exclude .venv --exclude .venv-cpython --exclude .venv-cpython_314 --exclude .venv-pypy \
  --exclude target --exclude target-maif --exclude node_modules --exclude docs-dist --exclude dist \
  --exclude artifacts --exclude logs --exclude recordings --exclude playwright-report --exclude test-results \
  --exclude src/opentelemetry_backup --exclude .playwright-cli

# trace
cd /Users/kooshapari/kush/trace
tokei --sort code --output json \
  --exclude .git --exclude .venv --exclude node_modules --exclude dist --exclude build \
  --exclude .next --exclude coverage --exclude .pytest_cache --exclude .mypy_cache
```
