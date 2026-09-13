"""CI architecture guardrails (G-KD-05): boundary checks, contract conformance."""

import subprocess
import sys
from pathlib import Path


def test_check_boundaries_passes() -> None:
    # @trace FR-CFG-006
    """Run scripts/check_boundaries.py; must exit 0."""
    script = Path(__file__).resolve().parent.parent / "scripts" / "check_boundaries.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        cwd=script.parent.parent,
    )
    assert result.returncode == 0, f"Boundary check failed:\n{result.stdout}\n{result.stderr}"


def test_contract_authority_sync() -> None:
    """Verify that docset/contracts/CONTRACT_AUTHORITY.md is in sync with implementation (XK3)."""
    script = Path(__file__).resolve().parent.parent / "scripts" / "verify_contract_authority.py"
    # Ensure src is in PYTHONPATH
    import os

    env = os.environ.copy()
    src_dir = str(Path(__file__).resolve().parent.parent / "src")
    env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

    result = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        cwd=script.parent.parent,
        env=env,
    )
    assert result.returncode == 0, f"Contract authority sync check failed:\n{result.stdout}\n{result.stderr}"
