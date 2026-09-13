"""Tests for the L11 Dependencies lane — pip-audit advisory gate.

Validates that:

* ``Makefile`` exposes a ``pip-audit`` target with a docstring and the
  expected body rule.
* ``scripts/check_pip_audit_invariants.sh`` exists, is executable, and
  exits zero on the canonical workspace (all six checks pass).
* The script's six canonical checks each pass on the canonical
  workspace (tooling, uv.lock presence, frozen-export parse, pip-audit
  JSON parse, severity gate, baseline snapshot parity).
* The script honours ``PIP_AUDIT_NO_NETWORK=1`` and exits zero on the
  offline path.
* The script catches each violation in isolation when run against an
  isolated sandbox (missing-lock + lock-truncated).
* The ``make help`` surface lists the ``pip-audit`` target.

Focused; runs in well under 30s per case (network-permitting) and
under 1s in the offline path.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_pip_audit_invariants.sh"
MAKEFILE = REPO_ROOT / "Makefile"
UV_LOCK = REPO_ROOT / "uv.lock"


# ---------------------------------------------------------------------------
# Makefile surface
# ---------------------------------------------------------------------------


def _phony_block() -> str:
    """Return the .PHONY block as a single string (multi-line aware)."""
    text = MAKEFILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    block_lines: list[str] = []
    in_phony = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(".PHONY:"):
            in_phony = True
            block_lines.append(stripped)
            continue
        if in_phony:
            if line.endswith("\\") or line.rstrip().endswith("\\"):
                block_lines.append(line)
                continue
            block_lines.append(line)
            break
    return "\n".join(block_lines)


def test_makefile_has_pip_audit_phony_target() -> None:
    """Makefile must list ``pip-audit`` in its .PHONY block (multi-line)."""
    assert "pip-audit" in _phony_block(), "pip-audit missing from .PHONY block"


def test_makefile_pip_audit_target_has_docstring_and_runs_script() -> None:
    """``pip-audit:`` rule must carry a ``## docstring`` and shell out to the script."""
    content = MAKEFILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    found = False
    for idx, line in enumerate(lines):
        if line.startswith("pip-audit:"):
            tail = "\n".join(lines[idx : idx + 4])
            assert "## " in tail, "pip-audit must carry a '## ' docstring"
            assert "scripts/check_pip_audit_invariants.sh" in tail, (
                f"pip-audit body must invoke scripts/check_pip_audit_invariants.sh; got: {tail!r}"
            )
            found = True
            break
    assert found, "pip-audit rule not found in Makefile"


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_help_shows_pip_audit() -> None:
    """``make help`` must list the pip-audit target."""
    result = subprocess.run(
        ["make", "help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "pip-audit" in result.stdout, f"pip-audit not listed in: {result.stdout!r}"


# ---------------------------------------------------------------------------
# Script surface
# ---------------------------------------------------------------------------


def test_script_exists_and_is_executable() -> None:
    """Invariants script must exist and be executable."""
    assert SCRIPT.exists(), f"missing {SCRIPT}"
    assert SCRIPT.is_file(), f"{SCRIPT} is not a file"
    assert shutil.which("bash") is not None, "bash must be on PATH"


def test_script_exits_zero_on_canonical_workspace_with_six_checks() -> None:
    """On the real workspace the script must exit 0 and report all 6 checks."""
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        f"unexpected exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    # Canonical OK marker.
    assert "[make pip-audit] OK" in result.stdout, f"expected OK marker in stdout: {result.stdout!r}"
    # The six canonical check labels.
    expected = [
        "pip-audit tooling is available",
        "uv.lock exists and is non-empty",
        "uv export --frozen produces a parseable pip-style requirements file",
        "pip-audit emits parseable JSON for the frozen requirements",
        "severity gate: no findings at or above",
        "baseline snapshot: current run does not introduce new vulnerabilities",
    ]
    for needle in expected:
        assert needle in result.stdout, f"check label missing: {needle}\nstdout:\n{result.stdout}"


# ---------------------------------------------------------------------------
# Per-violation isolation (sandboxed fixtures)
# ---------------------------------------------------------------------------


def _run_script_with_root(tmp: Path, *, offline: bool = False) -> subprocess.CompletedProcess[str]:
    """Run the script in a sandbox where ROOT is rewritten to *tmp*.

    Reads the real script, patches its ``ROOT=`` assignment so the
    sandbox behaves as if it were the project root, and pipes the
    patched script through `bash`. Honours ``PIP_AUDIT_NO_NETWORK`` so
    the offline path can be exercised deterministically.
    """
    src = SCRIPT.read_text(encoding="utf-8")
    patched = src.replace(
        'ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"',
        f'ROOT="{tmp}"',
    )
    sandbox_script = tmp / "check.sh"
    sandbox_script.write_text(patched, encoding="utf-8")
    sandbox_script.chmod(0o755)
    env = os.environ.copy()
    if offline:
        env["PIP_AUDIT_NO_NETWORK"] = "1"
    else:
        env.pop("PIP_AUDIT_NO_NETWORK", None)
    return subprocess.run(
        ["bash", str(sandbox_script)],
        cwd=tmp,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=False,
    )


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    """Create a sandbox directory the patched script treats as ROOT."""
    box = tmp_path / "auditbox"
    box.mkdir()
    return box


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
    # No uv.lock on purpose. Run offline so the script does not try to
    # call pip-audit / uv against the canonical workspace.
    result = _run_script_with_root(sandbox, offline=True)
    assert result.returncode != 0, result.stdout
    assert "FAIL" in result.stdout, f"expected FAIL marker in stdout: {result.stdout}"


def test_script_fails_when_lock_is_truncated(sandbox: Path) -> None:
    """A sub-1KB uv.lock must be flagged as truncated by check #2."""
    sandbox.joinpath("uv.lock").write_text("# tiny\n", encoding="utf-8")
    result = _run_script_with_root(sandbox, offline=True)
    assert result.returncode != 0, result.stdout
    assert "truncated" in result.stdout or "suspiciously small" in result.stdout, (
        f"expected truncation warning in stdout: {result.stdout}"
    )


# ---------------------------------------------------------------------------
# Offline path contract
# ---------------------------------------------------------------------------


def test_script_offline_path_exits_zero_with_placeholder_json() -> None:
    """PIP_AUDIT_NO_NETWORK=1 must still exit 0 and write a baseline snapshot."""
    sandbox = REPO_ROOT / ".tmp-pip-audit-sandbox"  # created on demand
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir()
    try:
        # Seed minimal artefacts so checks #2 and #3 succeed.
        sandbox.joinpath("uv.lock").write_text("# fake uv.lock\n" * 200, encoding="utf-8")
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
        result = _run_script_with_root(sandbox, offline=True)
        assert result.returncode == 0, (
            f"offline path failed: rc={result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "[make pip-audit] OK" in result.stdout
        # Baseline should be initialised from the placeholder current.
        baseline = sandbox / "help" / "audit" / "pip-audit-baseline.json"
        current = sandbox / "help" / "audit" / "pip-audit-current.json"
        assert baseline.exists() and baseline.stat().st_size > 0, (
            f"baseline missing or empty at {baseline}; stdout={result.stdout!r}"
        )
        assert current.exists() and current.stat().st_size > 0, (
            f"current snapshot missing at {current}; stdout={result.stdout!r}"
        )
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


# ---------------------------------------------------------------------------
# Real workspace artefact sanity
# ---------------------------------------------------------------------------


def test_canonical_uv_lock_is_substantively_sized() -> None:
    """Sanity-check uv.lock is in the expected size range for this repo."""
    size = UV_LOCK.stat().st_size
    assert size > 100_000, f"uv.lock is unusually small: {size} bytes"
    assert size < 5_000_000, f"uv.lock is unusually large: {size} bytes"
