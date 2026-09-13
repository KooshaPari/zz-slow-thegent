# Library Re-Audit + Codebase Atlas (2026-02-21)

## Scope

This report captures:

1. Re-audit of migration status off wasteful custom LOC tooling and legacy package surfaces.
2. Current-state validation after large recent feature growth.
3. A concrete codebase atlas explaining the high Python `tokei` counts.

## Executive Verdict

Status is **partial, not fully complete** for current HEAD.

What remains true:

- Major library-first migration is real (httpx/tenacity, watchfiles/watchdog, cachetools/diskcache, fastjsonschema, etc. in `pyproject.toml`).

What is now stale from older "complete" reports:

- There are still active legacy/debt surfaces and custom LOC enforcement surfaces that need final consolidation.

## Evidence Snapshot

### A) Library-first migration present

- `pyproject.toml` includes modern stack in active deps:
  - `httpx`, `tenacity`, `watchfiles`, `watchdog`, `cachetools`, `diskcache`, `fastjsonschema`, `litellm`.
- This confirms major migration happened and is not only documented.

### B) Remaining legacy/debt/custom surfaces

- Rust legacy crate usage still present:
  - `crates/thegent-hooks/Cargo.toml` still declares `lazy_static = "1.5.0"`.
- Legacy compatibility tasks/aliases still present in task entrypoints:
  - `Taskfile.yml` has `lint:legacy`, `quality:legacy`, and deprecated aliases (`quality:all`, `gate`, `quality_project`).
- Custom file-length enforcement still exists (now Rust/Zig-backed but custom orchestration):
  - `scripts/max-lines-gate.sh`
  - `scripts/max_lines_gate.zig`
  - `crates/thegent-utils/src/bin/max_lines.rs`
- Legacy/fallback paths remain in runtime code (intentional in many places, but still work to review and tighten):
  - `src/thegent/infra/fast_websocket.py`
  - `src/thegent/governance/native_governance_scan.py`
  - `src/thegent/governance/native_secret_scan.py`
  - `src/thegent/infra/multi_runtime_bridge.py`

## Re-Audit Result: Did we fully migrate?

**No, not fully.**

- We completed the high-value core migration.
- We did **not** finish final cleanup/retirement of all legacy/deprecated/custom governance surfaces.

## Codebase Atlas (why Python looks huge)

## Repo-wide (tracked project surface)

- `tokei` total: **986,670 lines**
- Python: **344,933 lines**, **267,846 code lines**
- Markdown: **435,020 lines** (docs-heavy, non-executable)
- Rust: **35,219 lines**, **29,466 code lines**

Interpretation:

- The "~250k Python LOC" number is plausible when reading **code-only** (`267k` code).
- The bigger near-1M total is inflated by markdown/docs and comments/blanks.

## Focused engineering surface (`src tests scripts governance crates hooks shell templates`)

- Total: **401,442 lines**
- Python: **342,661 lines**, **266,186 code lines**
- Rust: **35,219 lines**, **29,466 code lines**

This confirms Python dominates the active engineering surface even after excluding common build/vendor dirs.

## Python hotspot directories (by code lines)

- `tests`: 62,513
- `src/thegent`: 16,037
- `src/thegent/cli/commands`: 14,413
- `scripts`: 9,303
- `src/thegent/governance`: 9,263
- `src/thegent/infra`: 8,780
- `src/thegent/agents`: 7,567
- `src/thegent/routing`: 7,492

## Python hotspot files (by code lines)

- `src/thegent/cli/commands/cli.py`: 6,843
- `src/thegent/cli/commands/impl.py`: 5,786
- `tests/test_e2e_cli.py`: 4,855
- `src/thegent/mcp/server.py`: 4,241
- `src/thegent/execution.py`: 2,165
- `src/thegent/install.py`: 1,899
- `src/thegent/doctor.py`: 1,891

## Why the count feels confusing

- `tokei` reports all lines by default (code + comments + blanks).
- Docs are extremely large and dominate total line volume.
- Tests are large and heavily contribute to Python LOC.
- A few monolithic CLI/server files add major weight.

## Remaining Work (prioritized)

1. Finish legacy package cleanup in Rust hooks

- Replace `lazy_static` with `OnceLock`/`once_cell` strategy consistently and remove remaining legacy crate usage.

2. Consolidate governance task aliases

- Retire deprecated task aliases after parity checks and keep one canonical quality path.

3. Normalize file-length governance into one canonical fast path

- Keep Rust primary implementation; make Zig path explicit optional plugin path; ensure CI gate is single-source.

4. Split oversized Python hotspots

- Start with:
  - `src/thegent/cli/commands/cli.py`
  - `src/thegent/cli/commands/impl.py`
  - `src/thegent/mcp/server.py`
- Target <=500 lines per module via functional decomposition.

5. Re-baseline docs vs code metrics in CI summary

- Publish separate code-only and docs-only metrics in CI outputs to avoid metric confusion.

## Repro Commands

```bash
# Full repo line distribution
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
tokei --sort lines --exclude .git --exclude .venv --exclude .venv-cpython --exclude .venv-cpython_314 --exclude .venv-pypy --exclude .shadow-DEL-18ef --exclude .shadow-DEL-361a --exclude .shadow-DEL-4558 --exclude .shadow-DEL-5a4f --exclude .shadow-DEL-68b2 --exclude .shadow-DEL-7dc3 --exclude .shadow-DEL-7e53 --exclude .shadow-DEL-848e --exclude .shadow-DEL-9455 --exclude .shadow-DEL-9aac --exclude .shadow-DEL-a310 --exclude .shadow-DEL-a420 --exclude .shadow-DEL-a732 --exclude target --exclude node_modules --exclude docs-dist --exclude dist --exclude artifacts --exclude logs --exclude recordings --exclude playwright-report --exclude test-results

# Focused engineering surface
tokei --sort code src tests scripts governance crates hooks shell templates

# Python-only hotspot extraction
tokei --types Python --output json > /tmp/thegent_tokei_python.json
python3 - <<'PY'
import json
from pathlib import Path
from collections import defaultdict
p = Path('/tmp/thegent_tokei_python.json')
data = json.loads(p.read_text())
reports = data['Python']['reports']
bydir = defaultdict(int)
for r in reports:
    bydir[Path(r['name']).parent.as_posix()] += r['stats']['code']
for d, code in sorted(bydir.items(), key=lambda kv: kv[1], reverse=True)[:12]:
    print(d, code)
PY
```

## Decision Log (write-down)

- Prior completion reports are retained as historical milestones.
- Governance going forward must treat them as **time-bound snapshots** and require re-audit after large feature batches.
- Current canonical status for this topic is this report (2026-02-21), not older "complete" labels.
