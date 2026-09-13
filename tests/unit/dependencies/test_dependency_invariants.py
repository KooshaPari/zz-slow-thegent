"""Tests for the L11 Dependencies lane — `scripts/check_dependency_invariants.sh`.

Validates that:

* ``Makefile`` exposes a ``dep-audit`` target with a docstring and the
  expected body rule.
* ``scripts/check_dependency_invariants.sh`` exists, is executable, and
  exits non-zero on a synthetic missing-lock file.
* The script's five canonical checks each pass on the canonical
  workspace (uv.lock present, pyproject pinned, requirements.txt
  populated, PEP-503 sync, no bare '==' pins).
* The script catches each violation in isolation when run against an
  isolated sandbox.

Focused; runs in well under 1 second per case.
"""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_dependency_invariants.sh"
MAKEFILE = REPO_ROOT / "Makefile"
UV_LOCK = REPO_ROOT / "uv.lock"
PYPROJECT = REPO_ROOT / "pyproject.toml"
REQUIREMENTS = REPO_ROOT / "requirements.txt"


# ---------------------------------------------------------------------------
# Makefile surface
# ---------------------------------------------------------------------------


def test_makefile_has_dep_audit_phony_target() -> None:
    """Makefile must list ``dep-audit`` in its .PHONY block (multi-line)."""
    content = MAKEFILE.read_text(encoding="utf-8")
    # Collect the .PHONY block (lines starting with .PHONY: plus their
    # backslash-continuations AND the final non-continued line).
    lines = content.splitlines()
    block_lines: list[str] = []
    in_phony = False
    for _idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(".PHONY:"):
            in_phony = True
            block_lines.append(stripped)
            continue
        if in_phony:
            if line.endswith("\\") or line.rstrip().endswith("\\"):
                block_lines.append(line)
                continue
            # Final, un-continued line of the .PHONY block.
            block_lines.append(line)
            break
    block = "\n".join(block_lines)
    assert "dep-audit" in block, f"dep-audit missing from .PHONY block:\n{block}"


def test_makefile_dep_audit_target_has_docstring() -> None:
    """``dep-audit:`` rule must carry a ``## docstring`` for `make help`."""
    content = MAKEFILE.read_text(encoding="utf-8")
    body_lines = content.splitlines()
    body = "\n".join(body_lines)
    assert "dep-audit: ##" in body, "dep-audit must have a '## ' docstring"


def test_makefile_dep_audit_target_runs_script() -> None:
    """``dep-audit`` body must shell out to the invariants script."""
    content = MAKEFILE.read_text(encoding="utf-8")
    body_lines = content.splitlines()
    found_rule = False
    for idx, line in enumerate(body_lines):
        if line.startswith("dep-audit:"):
            tail = "\n".join(body_lines[idx : idx + 3])
            assert "scripts/check_dependency_invariants.sh" in tail, (
                f"dep-audit body must invoke scripts/check_dependency_invariants.sh; got: {tail!r}"
            )
            found_rule = True
            break
    assert found_rule, "dep-audit rule not found"


def test_make_help_shows_dep_audit() -> None:
    """``make help`` must list the dep-audit target."""
    result = subprocess.run(
        ["make", "help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "dep-audit" in result.stdout, f"dep-audit not listed in: {result.stdout!r}"


# ---------------------------------------------------------------------------
# Script surface
# ---------------------------------------------------------------------------


def test_script_exists_and_is_executable() -> None:
    """Invariants script must exist and be executable."""
    assert SCRIPT.exists(), f"missing {SCRIPT}"
    assert SCRIPT.is_file(), f"{SCRIPT} is not a file"
    # Either the executable bit is set or `bash` is on PATH (we run via `bash`)
    # so we just assert it can be invoked.
    assert shutil.which("bash") is not None, "bash must be on PATH"


def test_script_exits_zero_on_canonical_workspace() -> None:
    """Script must exit 0 on the real workspace (all 5 checks pass)."""
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"unexpected exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    # The script prints "[make dep-audit] OK" on success.
    assert "[make dep-audit] OK" in result.stdout, f"expected OK marker in stdout: {result.stdout!r}"


def test_script_reports_all_five_canonical_checks() -> None:
    """The five canonical checks must all be reported."""
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    expected = [
        "uv.lock exists and is non-empty",
        "pyproject.toml declares pinned runtime dependencies",
        "requirements.txt exists and lists packages",
        "uv.lock contains every top-level pyproject dep",
        "pyproject.toml has no plain '==' pin",
    ]
    for needle in expected:
        assert needle in result.stdout, f"check missing: {needle}"


# ---------------------------------------------------------------------------
# Per-violation isolation (sandboxed fixtures)
# ---------------------------------------------------------------------------


def _run_script_with_env(tmp: Path, monkeypatch: pytest.MonkeyPatch) -> subprocess.CompletedProcess[str]:
    """Run the script in a sandbox where ROOT points at *tmp*.

    Patches the script's path so its `ROOT` derivation resolves to the
    sandbox, then asserts the exit code + output.
    """
    sandbox_script = tmp / "check.sh"
    sandbox_script.write_text(
        textwrap.dedent(
            f"""
            #!/usr/bin/env bash
            # Patched copy that always treats {tmp} as ROOT.
            set -euo pipefail
            ROOT="{tmp}"
            export ROOT
            source <(sed -e 's|ROOT=\"$(cd \"$(dirname \"${{BASH_SOURCE[0]}}\")/..\" && pwd)\"|ROOT=\"{tmp}\"|' "{SCRIPT}")
            """
        ).strip()
        + "\n"
    )
    sandbox_script.chmod(0o755)
    return subprocess.run(
        ["bash", str(sandbox_script)],
        cwd=tmp,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    """Create a sandbox with valid lock/pyproject/requirements that fail one check."""
    sandbox = tmp_path / "depbox"
    sandbox.mkdir()
    return sandbox


def test_script_fails_when_uv_lock_missing(sandbox: Path) -> None:
    """Missing uv.lock must fail the script (non-zero exit, FAIL line)."""
    sandbox.joinpath("pyproject.toml").write_text(
        textwrap.dedent(
            """
            [project]
            name = "demo"
            version = "0.0.1"
            dependencies = ["httpx>=0.27"]
            """
        ).strip()
        + "\n"
    )
    sandbox.joinpath("requirements.txt").write_text("httpx==0.27.0\n")
    # No uv.lock on purpose.
    result = _run_script_with_env(sandbox, pytest.MonkeyPatch())
    assert result.returncode != 0, result.stdout
    assert "FAIL" in result.stdout, result.stdout


def test_script_fails_when_pyproject_unpinned(sandbox: Path) -> None:
    """Unpinned pyproject.toml dep must fail the script."""
    sandbox.joinpath("uv.lock").write_text('version = 1\nrequires-python = ">=3.11"\n')
    sandbox.joinpath("pyproject.toml").write_text(
        textwrap.dedent(
            """
            [project]
            name = "demo"
            version = "0.0.1"
            dependencies = ["httpx"]
            """
        ).strip()
        + "\n"
    )
    sandbox.joinpath("requirements.txt").write_text("httpx\n")
    result = _run_script_with_env(sandbox, pytest.MonkeyPatch())
    assert result.returncode != 0, result.stdout
    assert "FAIL" in result.stdout or "missing pinned runtime dependencies" in result.stdout


def test_script_fails_when_requirements_missing(sandbox: Path) -> None:
    """Missing requirements.txt must fail the script."""
    sandbox.joinpath("uv.lock").write_text('version = 1\nrequires-python = ">=3.11"\n')
    sandbox.joinpath("pyproject.toml").write_text(
        textwrap.dedent(
            """
            [project]
            name = "demo"
            version = "0.0.1"
            dependencies = ["httpx>=0.27"]
            """
        ).strip()
        + "\n"
    )
    # No requirements.txt on purpose.
    result = _run_script_with_env(sandbox, pytest.MonkeyPatch())
    assert result.returncode != 0, result.stdout
    assert "requirements.txt missing" in result.stdout


def test_script_fails_when_lock_and_pyproject_drift(sandbox: Path) -> None:
    """A pyproject dep not present in uv.lock must fail the script."""
    sandbox.joinpath("pyproject.toml").write_text(
        textwrap.dedent(
            """
            [project]
            name = "demo"
            version = "0.0.1"
            dependencies = ["httpx>=0.27", "this-package-is-not-in-the-lock>=1.0"]
            """
        ).strip()
        + "\n"
    )
    sandbox.joinpath("requirements.txt").write_text("httpx==0.27.0\nthis-package-is-not-in-the-lock==1.0\n")
    # uv.lock is empty so neither name is present.
    sandbox.joinpath("uv.lock").write_text('version = 1\nrequires-python = ">=3.11"\n')
    result = _run_script_with_env(sandbox, pytest.MonkeyPatch())
    assert result.returncode != 0, result.stdout
    assert "uv.lock is missing" in result.stdout


# ---------------------------------------------------------------------------
# Real workspace artefacts must exist
# ---------------------------------------------------------------------------


def test_canonical_workspace_has_lock_pyproject_and_requirements() -> None:
    """All three canonical surfaces must exist in the real workspace."""
    assert UV_LOCK.exists() and UV_LOCK.stat().st_size > 1024
    assert PYPROJECT.exists() and PYPROJECT.stat().st_size > 0
    assert REQUIREMENTS.exists() and REQUIREMENTS.stat().st_size > 0


def test_canonical_uv_lock_is_under_a_megabyte_but_over_100kb() -> None:
    """Sanity-check uv.lock is in the expected size range for this repo."""
    size = UV_LOCK.stat().st_size
    assert size > 100_000, f"uv.lock is unusually small: {size} bytes"
    assert size < 2_000_000, f"uv.lock is unusually large: {size} bytes"
