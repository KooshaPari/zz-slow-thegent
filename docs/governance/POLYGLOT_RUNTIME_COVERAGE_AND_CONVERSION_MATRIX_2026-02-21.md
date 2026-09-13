# Polyglot Runtime Coverage and Conversion Matrix (2026-02-21)

Status: Active governance baseline for language/runtime selection, test matrix, and refactor/conversion decisions.

## Scope

This policy standardizes:

1. test/runtime coverage expectations,
2. frontmatter/backmatter defaults,
3. when to keep/refactor/convert projects across Python, Rust, Zig, Go, and Mojo.

## Runtime and Coverage Matrix

| Language | Primary Runtime                | Required Matrix                                           | Fallback                                                        | Gate Policy                                                                        |
| -------- | ------------------------------ | --------------------------------------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Python   | `uv` + CPython 3.14            | CPython 3.14 + PyPy 3.11                                  | CPython 3.13 only when dependency/tooling blocks primary matrix | Must pass primary runtime + at least one alternate runtime in CI                   |
| Rust     | stable toolchain               | `cargo test`, `clippy -D warnings`, `fmt --check`         | nightly only for explicitly gated features                      | Stable must remain green; nightly may be non-blocking unless feature requires it   |
| Zig      | pinned Zig stable              | `zig test`, build in release-safe mode                    | next Zig as preview lane                                        | Stable lane blocking; preview lane advisory                                        |
| Go       | latest two supported Go minors | `go test ./...`, `go vet`, race lane for critical pkgs    | previous minor as compatibility lane                            | Latest lane blocking; compatibility lane soft-block until green for release branch |
| Mojo     | pinned Mojo version            | smoke + integration tests against Python interop boundary | Python/Rust reference implementation for parity checks          | Mojo lane can start advisory; becomes blocking once parity SLO achieved            |

## Frontmatter and Backmatter Defaults

### Frontmatter (required in governance/spec docs)

Use:

```yaml
---
title: <Doc Title>
date: YYYY-MM-DD
status: draft|active|deprecated
owner: <team-or-project>
tags: [governance, polyglot, testing]
---
```

### Backmatter (required in decision-heavy docs)

Append:

1. Decision record summary (what changed, why),
2. validation commands run,
3. open risks and follow-up owners,
4. review cadence/date.

## Conversion and Refactor Decision Matrix

| Condition                                                | Keep Current Stack | Refactor in Place                        | Convert Language                                            |
| -------------------------------------------------------- | ------------------ | ---------------------------------------- | ----------------------------------------------------------- |
| Team/runtime maturity high, perf acceptable              | Yes                | Optional cleanup only                    | No                                                          |
| Perf pain in hot path, architecture otherwise healthy    | No                 | Yes: isolate hotspots and optimize       | Convert hotspot module only                                 |
| Tooling/governance friction high but domain logic stable | No                 | Yes: improve build/test ergonomics first | Convert only if friction persists after 2 governance cycles |
| Ecosystem/library mismatch blocks core roadmap           | No                 | Temporary adapters only                  | Yes: convert to language with strong library support        |
| Operational latency/cost SLO repeatedly missed           | No                 | First profile + tune                     | Convert critical path after failed tuning attempts          |

## Conversion Triggers (must meet at least two)

1. Two consecutive release cycles miss SLOs after optimization.
2. Required libraries/security updates unavailable in current stack.
3. Runtime stability incidents exceed governance threshold.
4. Developer throughput materially below baseline due toolchain constraints.

## Mandatory Pre-Conversion Checklist

1. Measure baseline: throughput, latency, memory, CI duration.
2. Define API/ABI boundaries and parity tests.
3. Implement side-by-side validation harness.
4. Plan phased cutover with rollback.
5. Update governance docs, templates, and `CLAUDE.md`.

## Python-Specific Standard (requested baseline)

Default matrix:

1. `uv` + CPython 3.14 (primary),
2. PyPy 3.11 (secondary),
3. CPython 3.13 (fallback compatibility lane).

Failure policy:

1. Primary lane failure is blocking.
2. Secondary failure is blocking on release branches, advisory on feature branches.
3. Fallback lane is required when dependency constraints force downgrade.

## Instruction Architecture Normalization Policy

1. Canonical filename is `CLAUDE.md`.
2. Any `calude.md` typo file must be merged into canonical `CLAUDE.md` and removed.
3. Global vs project split is mandatory:
   - Global `CLAUDE.md` is index + guardrails.
   - Project `CLAUDE.md` is overlay + local execution specifics.
4. If `CLAUDE.md` exceeds ~20k tokens, split into docset:
   - keep `CLAUDE.md` as concise policy index,
   - move long detail to `docs/reference/CLAUDE_CORE_GUIDELINES.md` and related docs,
   - maintain a doc map section with explicit links.
5. Required instruction doc map references:
   - `docs/reference/CLAUDE_CORE_GUIDELINES.md`
   - `docs/reference/CLAUDE_THEGENT_RUNTIME_APPENDIX.md`
   - `docs/governance/GOVERNANCE_SUMMARY.md`
   - `docs/reference/WORK_STREAM.md`

## Validation Commands

```bash
# python lanes
uv run pytest
uv run -p 3.14 pytest
uv run -p pypy3.11 pytest
uv run -p 3.13 pytest  # compatibility fallback lane

# rust
cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test

# go
go test ./... && go vet ./...

# zig
zig test ./...
```
