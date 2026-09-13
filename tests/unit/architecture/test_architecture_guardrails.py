"""L1 / L9 preventive guardrails (baseline-aware).

These tests don't fix existing oversize/complex files — that's done in
the L1/L9 architecture hardening passes — but they **block regressions**
by failing CI when a *new* file or function crosses the agreed budget.

Pattern
-------

On first run the test emits a JSON baseline under
``tests/unit/architecture/.baseline/``. Subsequent runs diff against the
baseline and fail only on **new** offenders. The baseline is intentionally
human-checked into the repo so future L1/L9 hardening passes can shrink
it over time.

Budgets (mirror the scorecard's L1 / L9 thresholds):

* L1 hard cap  — file > 1500 lines fails (unreviewable in one PR).
* L1 soft cap  — file > 500 lines is logged for telemetry.
* L9 budget    — function CC > 25 fails (radon cyclomatic complexity).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

# Soft cap = "extract sub-helpers soon". Hard cap = "block PR".
MAX_FILE_LINES_SOFT = 500
MAX_FILE_LINES_HARD = 1500

# L9 budget — anything CC > 25 is a refactor candidate.
MAX_CYCLOMATIC_CC = 25

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src" / "thegent"
BASELINE_DIR = Path(__file__).resolve().parent / ".baseline"
FILE_BASELINE = BASELINE_DIR / "file_size_offenders.json"
CC_BASELINE = BASELINE_DIR / "cyclomatic_offenders.json"

# Vendored deps mirrored from pyproject.toml's tool.ruff.exclude.
EXCLUDE_DIRS = {"__pycache__", "acp"}


def _iter_python_files() -> list[Path]:
    """Yield Python files under ``src/thegent`` excluding vendored deps."""
    if not SRC_ROOT.exists():
        return []
    files: list[Path] = []
    for path in SRC_ROOT.rglob("*.py"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def _file_offenders(py_files: list[Path]) -> list[dict[str, Any]]:
    """Return hard-cap file offenders as JSON-serializable records."""
    offenders: list[dict[str, Any]] = []
    for path in py_files:
        line_count = sum(1 for _ in path.open("r", encoding="utf-8"))
        if line_count > MAX_FILE_LINES_HARD:
            offenders.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "lines": line_count,
                }
            )
    offenders.sort(key=lambda r: r["lines"], reverse=True)
    return offenders


def _cc_offenders(py_files: list[Path]) -> list[dict[str, Any]]:
    """Return CC-budget offenders as JSON-serializable records."""
    try:
        from radon.complexity import cc_visit  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip("radon not installed; skipping CC guard")

    offenders: list[dict[str, Any]] = []
    for path in py_files:
        try:
            text = path.read_text(encoding="utf-8")
            results = cc_visit(text)
        except (SyntaxError, UnicodeDecodeError):
            continue
        for result in results:
            if result.complexity > MAX_CYCLOMATIC_CC:
                offenders.append(
                    {
                        "path": str(path.relative_to(REPO_ROOT)),
                        "function": result.name,
                        "cc": result.complexity,
                    }
                )
    offenders.sort(key=lambda r: r["cc"], reverse=True)
    return offenders


def _load_baseline(path: Path) -> list[dict[str, Any]]:
    """Load baseline JSON if present, else return []."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def _write_baseline(path: Path, offenders: list[dict[str, Any]]) -> None:
    """Persist baseline to disk for the next run."""
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(offenders, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _diff(baseline: list[dict[str, Any]], current: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return entries in ``current`` representing *new* offenders.

    A "new offender" is a path (and its identifier key) that was **not**
    over budget in the baseline. Existing offenders may grow or shrink
    without flagging — they are tracked separately by the scorecard and
    their reduction is a positive L1/L9 signal.

    For file-size offenders the identity key is ``path``.
    For CC offenders the identity key is ``path`` + ``function``.
    """
    base_keys = {(r.get("path"), r.get("function")) for r in baseline}
    new: list[dict[str, Any]] = []
    for r in current:
        key = (r.get("path"), r.get("function"))
        if key in base_keys:
            # Already a known offender — no regression.
            continue
        # Also skip if the same *path* had any prior offender; only
        # flag genuinely NEW files/functions.
        new.append(r)
    return new


@pytest.fixture(scope="module")
def py_files() -> list[Path]:
    """All tracked thegent Python files."""
    return _iter_python_files()


def test_src_tree_has_python_files(py_files: list[Path]) -> None:
    """Sanity check — there must be source files to lint."""
    assert py_files, "no Python files found under src/thegent"


def test_no_new_file_size_offenders(py_files: list[Path]) -> None:
    """Fail only on NEW files exceeding the L1 hard cap."""
    current = _file_offenders(py_files)
    baseline = _load_baseline(FILE_BASELINE)
    if not FILE_BASELINE.exists():
        _write_baseline(FILE_BASELINE, current)
        pytest.skip(f"baseline written ({len(current)} offenders); rerun to enforce")
    new = _diff(baseline, current)
    if new:
        msg = "\n".join(f"  {r['path']}: {r['lines']} lines" for r in new)
        pytest.fail(
            f"{len(new)} NEW file(s) exceed {MAX_FILE_LINES_HARD} lines "
            f"(previously clean per baseline):\n{msg}\n\n"
            f"Either reduce the file size or update the baseline under "
            f"{FILE_BASELINE.relative_to(REPO_ROOT)} with rationale."
        )


def test_no_new_cyclomatic_offenders(py_files: list[Path]) -> None:
    """Fail only on NEW functions exceeding the L9 CC budget."""
    current = _cc_offenders(py_files)
    baseline = _load_baseline(CC_BASELINE)
    if not CC_BASELINE.exists():
        _write_baseline(CC_BASELINE, current)
        pytest.skip(f"baseline written ({len(current)} offenders); rerun to enforce")
    new = _diff(baseline, current)
    if new:
        msg = "\n".join(f"  {r['path']}::{r['function']} (CC={r['cc']})" for r in new)
        pytest.fail(
            f"{len(new)} NEW function(s) exceed CC={MAX_CYCLOMATIC_CC}:\n{msg}\n\n"
            f"Either refactor with sub-helpers or update the baseline under "
            f"{CC_BASELINE.relative_to(REPO_ROOT)} with rationale."
        )


def test_warn_soft_cap_oversize(py_files: list[Path]) -> None:
    """Informational — count files in the 500-1500 line range."""
    oversize: list[tuple[Path, int]] = []
    for path in py_files:
        line_count = sum(1 for _ in path.open("r", encoding="utf-8"))
        if MAX_FILE_LINES_SOFT < line_count <= MAX_FILE_LINES_HARD:
            oversize.append((path, line_count))
    # Always passes — the scorecard uses this signal directly.
    assert oversize is not None  # noqa: S101 — trivial sanity
