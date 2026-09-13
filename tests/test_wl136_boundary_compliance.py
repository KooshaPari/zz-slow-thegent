"""Tests for WL-136: Import boundary compliance post-refactor.

Validates that the boundary audit script exists, is callable, and finds
no core-to-tooling import violations in the codebase.

# @trace WL-136 B90-W3-C4
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
AUDIT_SCRIPT = ROOT / "scripts" / "audit_boundary_compliance.py"


# @trace WL-136 B90-W3-C4
def test_audit_boundary_compliance_script_exists() -> None:
    """scripts/audit_boundary_compliance.py must exist."""
    assert AUDIT_SCRIPT.exists(), f"audit_boundary_compliance.py not found at {AUDIT_SCRIPT}."


def _load_audit_module():
    """Dynamically load audit_boundary_compliance.py as a module."""
    spec = importlib.util.spec_from_file_location("audit_boundary_compliance", AUDIT_SCRIPT)
    assert spec is not None, "Could not create module spec for audit_boundary_compliance.py"
    assert spec.loader is not None, "Module spec has no loader"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# @trace WL-136 B90-W3-C4
def test_audit_function_returns_list() -> None:
    """audit() from audit_boundary_compliance.py must return a list."""
    mod = _load_audit_module()
    result = mod.audit()
    assert isinstance(result, list), f"audit() returned {type(result).__name__}, expected list."


# @trace WL-136 B90-W3-C4
def test_audit_script_exits_zero_no_violations() -> None:
    """Running audit_boundary_compliance.py must exit 0 (no boundary violations found)."""
    proc = subprocess.run(
        ["python", str(AUDIT_SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"audit_boundary_compliance.py exited {proc.returncode}.\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "PASS" in proc.stdout, f"Expected 'PASS' in output but got: {proc.stdout}"
